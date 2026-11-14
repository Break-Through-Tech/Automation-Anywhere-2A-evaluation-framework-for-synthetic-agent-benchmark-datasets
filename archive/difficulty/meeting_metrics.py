"""Build source-derived difficulty profiles and a provenance-preserving outcome log.

No agent or judge calls. Historical outcomes are never reclassified as new-policy
judgments. Runtime difficulty is supplementary and requires explicit eligibility.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import mean, median

from .llm_judge import REPO, load_synthetic_cases, load_trials, resolve_trials
from .saved_trials import file_hash
from .structural_features import extract

METHOD_VERSION = 'difficulty_lab_v0.3_proposed'
OUTCOMES = {'pass', 'fail', 'unverifiable'}
MAPPING = {'met': 'pass', 'unmet': 'fail', 'unverifiable': 'unverifiable'}
FIELDS = ('workflow_step_count', 'reference_domain_tool_call_count',
          'reference_unique_domain_tool_count', 'reference_milestone_count',
          'workflow_decision_cue_step_count')


def runtime_summary(rows):
    """Allow an observed fail with a blocker, but never count it as difficulty.

    Missing assessments have outcome None and a separate lifecycle status. They
    must not be relabeled unverifiable, which is itself an assessment.
    """
    seen = set()
    by_task = defaultdict(list)
    versions = set()
    for row in rows:
        key = (row['domain'], row['task_id'], row['trial'])
        if key in seen:
            raise ValueError('Duplicate task/trial identity')
        seen.add(key)
        outcome, eligible = row.get('outcome'), row.get('execution_eligible')
        if outcome is not None and outcome not in OUTCOMES:
            raise ValueError('Unknown outcome')
        if type(eligible) is not bool:
            raise ValueError('Explicit boolean eligibility is required')
        if eligible and (outcome not in {'pass', 'fail'} or row.get('environment_blocked')
                         or row.get('environment_unresolved')):
            raise ValueError('Blocked, unresolved and unverifiable attempts cannot enter difficulty')
        if not eligible and not row.get('exclusion_reason'):
            raise ValueError('Excluded attempts require a reason')
        if outcome is not None:
            if not row.get('source_policy'):
                raise ValueError('Assessed outcomes require policy provenance')
            versions.add(row['source_policy'])
        by_task[key[:2]].append(row)
    if len(versions) > 1:
        raise ValueError('Different assessment policies must be summarized separately')
    result = []
    for (domain, task), trials in sorted(by_task.items()):
        assessed = [r for r in trials if r.get('outcome') is not None]
        eligible = [r for r in trials if r['execution_eligible']]
        passed = sum(r['outcome'] == 'pass' for r in eligible)
        result.append({'domain': domain, 'task_id': task, 'n_planned': len(trials),
                       'n_assessed': len(assessed), 'n_unassessed': len(trials)-len(assessed),
                       'n_pass_logged': sum(r.get('outcome') == 'pass' for r in trials),
                       'n_fail_logged': sum(r.get('outcome') == 'fail' for r in trials),
                       'n_unverifiable_logged': sum(r.get('outcome') == 'unverifiable' for r in trials),
                       'n_eligible': len(eligible), 'n_excluded_assessed': len(assessed)-len(eligible),
                       'execution_difficulty': 1-passed/len(eligible) if eligible else None})
    return result


def describe(rows):
    return {'n_tasks': len(rows),
            'supplied_label_counts': dict(sorted(Counter(r['class_difficulty_tag'] or 'missing' for r in rows).items())),
            'features': {field: {'minimum': min(r[field] for r in rows),
                                  'median': median(r[field] for r in rows),
                                  'mean': mean(r[field] for r in rows),
                                  'maximum': max(r[field] for r in rows)} for field in FIELDS},
            'n_unknown_exact_path_counts': sum(r['task_path_step_count'] is None for r in rows),
            'n_unknown_exact_decision_counts': sum(r['task_decision_point_count'] is None for r in rows)}


def build():
    feature_document = extract()
    paths = [REPO/'results/baseline/v2_synthetic_full/trials.csv',
             REPO/'results/judge_review/v4/blocked_and_unverifiable.json',
             REPO/'results/judge_review/v4/run_summary.json',
             REPO/'results/judge_review/v1/sample/human_reviews.json']
    before = {str(p.relative_to(REPO)): file_hash(p) for p in paths}
    resolved = resolve_trials(load_trials([paths[0]]), load_synthetic_cases())
    legacy = json.loads(paths[1].read_text())
    source_policy = json.loads(paths[2].read_text())['policy_version']
    if source_policy != 'provisional_outcome_v0.2' or any(r['model_judgment'] != 'unverifiable' for r in legacy):
        raise ValueError('This historical ledger source changed; review eligibility before rebuilding')
    by_key = {(r['domain'], r['task_id'], r['trial']): r for r in legacy}
    if len(by_key) != len(legacy):
        raise ValueError('Duplicate saved judge assessments')
    known = {(r['domain'],r['task_id'],r['trial']) for r,_,_ in resolved}
    if not set(by_key).issubset(known):
        raise ValueError('Assessment identity not found in original attempts')
    ledger = []
    for row, _, _ in resolved:
        key = row['domain'], row['task_id'], row['trial']
        assessment = by_key.get(key)
        item = {'domain': key[0], 'task_id': key[1], 'trial': key[2],
                'assessment_status': 'saved_development_assessment' if assessment else 'not_assessed',
                'outcome': MAPPING[assessment['model_judgment']] if assessment else None,
                'source_policy': source_policy if assessment else None,
                'source_review_id': assessment['review_id'] if assessment else None,
                'source_outcome': assessment['model_judgment'] if assessment else None,
                'execution_eligible': False,
                'environment_blocked': bool(assessment and assessment['environment_assessment']['status'] == 'supported_blocker'
                                            and assessment['environment_assessment']['prevents_required_execution']),
                'environment_unresolved': bool(assessment and assessment['environment_assessment']['status'] == 'suspected_blocker'),
                'exclusion_reason': ('Historical unverifiable development assessment; judge context was incomplete and final policy validation is pending.' if assessment
                                     else 'No outcome assessment under the selected policy; historical oracle reward is not substituted.'),
                'assessment_source': str(paths[1].relative_to(REPO)) if assessment else None,
                'historical_reference_evaluation': row['source']['original_evaluation'],
                'trace_file': str(Path(row['source']['trace_file']).relative_to(REPO)),
                'trace_sha256': row['source']['trace_sha256']}
        ledger.append(item)
    task_runtime = runtime_summary(ledger)
    features = feature_document['tasks']
    domains = sorted({r['domain'] for r in features})
    tag_groups = sorted({r['class_difficulty_tag'] for r in features})
    summary = {'method_version': METHOD_VERSION, 'status': 'source_metrics_complete_runtime_not_validated',
               'scope': 'difficulty only; outcomes are inputs and diagnostics, not a separate correctness metric',
               'primary_result': 'designed_difficulty_profile', 'combined_weighted_score': None,
               'new_api_calls': 0, 'new_mock_executions': 0,
               'overall': describe(features),
               'by_domain': {d: describe([r for r in features if r['domain']==d]) for d in domains},
               'by_supplied_label': {tag: describe([r for r in features if r['class_difficulty_tag']==tag]) for tag in tag_groups},
               'execution': {'assessment_policy': source_policy, 'policy_status': 'historical exploratory, not adjudicated under new guidance',
                             'n_original_trials': len(ledger), 'n_assessed': len(legacy),
                             'n_unassessed': len(ledger)-len(legacy),
                             'logged_outcomes': dict(Counter(r['outcome'] for r in ledger if r['outcome'])),
                             'n_eligible': sum(r['execution_eligible'] for r in ledger),
                             'execution_difficulty': None, 'reason': 'No eligible validated attempts in this development assessment source.'},
               'limitations': ['Shared workflow counts are not exact scenario paths.',
                               'Decision wording cues are not exact decisions.',
                               'Supplied labels are designed annotations, not ground truth.',
                               'Only three hard labels; within-domain/label comparisons may be sparse.',
                               'Historical 16-attempt sample is purposive and lacked complete judge context.',
                               'No new-policy outcome labels, benchmark correctness metric, or combined difficulty weights were invented.'],
               'source_hashes': {**before, **{str(Path('data')/p): h for p,h in feature_document['source_sha256'].items()}}}
    for p in paths:
        if file_hash(p) != before[str(p.relative_to(REPO))]:
            raise ValueError('Source changed during report')
    return summary, features, ledger, task_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    target = args.out.resolve()
    data = (REPO/'data').resolve()
    if target == data or target.is_relative_to(data) or data.is_relative_to(target):
        parser.error('Output overlaps supplied data')
    if target.exists():
        parser.error('Use a fresh output directory')
    summary, features, ledger, task_runtime = build()
    target.mkdir(parents=True)
    for name, value in [('summary.json',summary), ('designed_profiles.json',features),
                        ('attempt_outcomes.json',ledger), ('execution_by_task.json',task_runtime)]:
        (target/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    for name, values in [('designed_profiles.csv', [{k:r[k] for k in ('domain','task_id','class_difficulty_tag','declared_difficulty','workflow_id',*FIELDS,'task_path_step_count','task_decision_point_count')} for r in features]),
                         ('execution_by_task.csv',task_runtime)]:
        with (target/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    print(f'Wrote {len(features)} profiles and {len(ledger)} trial slots; no API calls. {target}')


if __name__ == '__main__':
    main()
