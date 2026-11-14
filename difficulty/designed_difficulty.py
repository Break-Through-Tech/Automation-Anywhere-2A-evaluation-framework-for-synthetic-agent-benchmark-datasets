"""Reproducible provisional designed-complexity index; no API or agent execution."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import mean

from .llm_judge import DATA_DIR, REPO, load_synthetic_cases
from .saved_trials import file_hash
from .structural_features import extract

VERSION = 'designed_difficulty_v0.1_provisional'
ANNOTATIONS = REPO / 'difficulty/designed_annotations_v1.json'
COMPONENTS = ('action_groups', 'reference_tool_interactions', 'business_check_groups')
# Fixed to the original 64-task snapshot, not refitted per domain or future batch.
SCALES = dict(zip(COMPONENTS, (9, 23, 4)))
WEIGHTS = dict.fromkeys(COMPONENTS, 1 / 3)
VARIANTS = {'equal': (1/3, 1/3, 1/3), 'action_heavy': (.5, .25, .25),
            'tool_heavy': (.25, .5, .25), 'without_checks': (.5, .5, 0)}
ROLES = {'active_action_group', 'terminal_signal', 'external_response_or_approval', 'wait_condition'}
FRAMEWORK_COLUMNS = ('score', 'status', 'action_groups', 'reference_tool_interactions',
                     'business_check_groups', 'rank_easy_first', 'uncertainty_flags')


def score_counts(counts, weights=WEIGHTS):
    if set(counts) != set(COMPONENTS) or set(weights) != set(COMPONENTS):
        raise ValueError('All and only the three versioned components are required')
    if any(type(counts[k]) is not int or not 0 <= counts[k] <= SCALES[k] for k in COMPONENTS):
        raise ValueError('Counts must be nonnegative integers within the frozen reference scales')
    if any(not isinstance(weights[k], (int, float)) or not 0 <= weights[k] <= 1 for k in COMPONENTS) or abs(sum(weights.values())-1) > 1e-9:
        raise ValueError('Weights must be nonnegative and sum to one')
    normalized = {k: counts[k]/SCALES[k] for k in COMPONENTS}
    contributions = {k: 100*weights[k]*normalized[k] for k in COMPONENTS}
    return round(sum(contributions.values()), 6), normalized, contributions


def validate_annotations(document, features, cases):
    if document.get('version') != 'designed_annotations_v0.1':
        raise ValueError('Unsupported annotation version')
    if document.get('source_sha256') != features['source_sha256']:
        raise ValueError('Annotation source fingerprints are stale or incomplete')
    entries = document['tasks']; keys = [(r['domain'], r['task_id']) for r in entries]
    expected = {(r['domain'], r['task_id']) for r in features['tasks']}
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError('Annotations must cover canonical tasks exactly once')
    for row in entries:
        ref = cases[(row['domain'], row['task_id'])]
        milestones = ref['milestones']; annotations = row['milestones']
        if [m['step'] for m in annotations] != [m['step'] for m in milestones]:
            raise ValueError('Milestone annotation coverage/order differs from source')
        for a, m in zip(annotations, milestones):
            if a['expected_description'] != m['description']:
                raise ValueError('Annotation excerpt differs from source')
            if a['role'] not in ROLES or type(a['business_check']) is not bool:
                raise ValueError('Invalid milestone role or business-check flag')
            if a['business_check'] and (a['role'] != 'active_action_group' or not a['business_check_basis']):
                raise ValueError('Business checks require an active group and an explicit basis')
    return dict(zip(keys, entries))


def source_pointers(data_dir, cases):
    result = {}
    for path in sorted(Path(data_dir).glob('*/test_cases.json')):
        domain = path.parent.name
        def walk(value, pointer=''):
            if isinstance(value, dict):
                if 'test_case_id' in value and 'milestones' in value:
                    key = (domain, cases[(domain, value['test_case_id'])]['test_case_id'])
                    if key in result:
                        raise ValueError('Duplicate source JSON task mapping')
                    result[key] = (str(path.relative_to(data_dir)), pointer)
                for k, v in value.items():
                    walk(v, pointer+'/'+str(k).replace('~', '~0').replace('/', '~1'))
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    walk(v, pointer+'/'+str(i))
        walk(json.loads(path.read_text()))
    return result


def ranks(rows, value):
    values = sorted(value(r) for r in rows)
    # Average rank for ties; 1 is easiest, larger ranks are harder.
    return {v: (values.index(v)+1 + len(values)-values[::-1].index(v))/2 for v in set(values)}


def build(data_dir=DATA_DIR, annotations_path=ANNOTATIONS):
    features = extract(data_dir); cases = load_synthetic_cases(data_dir)
    annotations = json.loads(Path(annotations_path).read_text())
    annotated = validate_annotations(annotations, features, cases)
    pointers = source_pointers(data_dir, cases); rows = []
    for f in features['tasks']:
        key = (f['domain'], f['task_id']); a = annotated[key]; ref = cases[key]
        source, pointer = pointers[key]; evidence = []
        for i, m in enumerate(a['milestones']):
            evidence.append({**m, 'source': source,
                             'locator': '#'+pointer+f'/milestones/{i}/description'})
        counts = {'action_groups': sum(m['role']=='active_action_group' for m in evidence),
                  'reference_tool_interactions': f['reference_domain_tool_call_count'],
                  'business_check_groups': sum(m['business_check'] for m in evidence)}
        score, normalized, contributions = score_counts(counts)
        flags = ['provisional_not_independently_validated', 'reference_path_assumed_intended',
                 'checks_are_not_independent_decisions', 'runtime_feasibility_not_scored',
                 'component_overlap_possible']
        if any(any(token in m['expected_description'].lower() for token in (' and ', ', ', ';', 'batch', 'linked', 'multiple', 'all '))
               for m in evidence if m['role']=='active_action_group'):
            flags.append('milestone_groups_may_bundle_multiple_actions_or_entities')
        if any(' if ' in m['expected_description'].lower() for m in evidence):
            flags.append('conditional_milestone_applicability_requires_interpretation')
        if f['expected_tools_not_listed_in_workflow']:
            flags.append('reference_tools_not_listed_in_shared_workflow')
        rows.append({'domain': f['domain'], 'task_id': f['task_id'], 'title': ref['title'],
            'workflow_id': f['workflow_id'], 'supplied_tag_comparison_only': f['class_difficulty_tag'],
            'status': VERSION, **counts, 'score': score, 'normalized_components': normalized,
            'weighted_points': contributions, 'shared_workflow_steps_comparison_only': f['workflow_step_count'],
            'excluded_terminal_groups': sum(m['role']=='terminal_signal' for m in evidence),
            'excluded_external_groups': sum(m['role']=='external_response_or_approval' for m in evidence),
            'excluded_wait_groups': sum(m['role']=='wait_condition' for m in evidence),
            'exact_atomic_action_count': None, 'exact_independent_decision_count': None,
            'review_type': a['review_type'], 'uncertainty_flags': flags, 'milestone_evidence': evidence,
            'reference_tool_sequence': f['reference_tool_sequence'],
            'sources': {**f['sources'], 'json_case_pointer': '#'+pointer},
            'score_variants': {name: score_counts(counts, dict(zip(COMPONENTS, w)))[0]
                               for name, w in VARIANTS.items()}})
    rank_sets = {name: ranks(rows, lambda r: r['score_variants'][name]) for name in VARIANTS}
    for row in rows:
        row['variant_ranks'] = {name: rank_sets[name][row['score_variants'][name]] for name in VARIANTS}
        row['rank_easy_first'] = row['variant_ranks']['equal']
        row['max_rank_change_under_alternative_weights'] = max(abs(x-row['rank_easy_first']) for x in row['variant_ranks'].values())
    return {'version': VERSION, 'status': 'complete_provisional_measure_not_validated',
            'network_calls': 0, 'agent_runs': 0, 'human_reviews_claimed': 0,
            'task_count': len(rows), 'domain_count': len({r['domain'] for r in rows}),
            'weights': WEIGHTS, 'normalization_scales': SCALES,
            'normalization_reference': 'Original 64 synthetic tasks; fixed v0.1 maxima, not per-domain fits',
            'source_sha256': features['source_sha256'], 'annotations_sha256': file_hash(annotations_path),
            'implementation_sha256': file_hash(Path(__file__)), 'tasks': rows}


def load_scores_for_framework(path, tasks, data_dir=DATA_DIR):
    doc = json.loads(Path(path).read_text())
    expected = {(r['domain'], r['task_id']) for r in tasks if r['dataset']=='synthetic'}
    keys = [(r['domain'], r['task_id']) for r in doc['tasks']]
    if doc.get('version') != VERSION or len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('Designed scores must match canonical synthetic framework tasks exactly once')
    if doc.get('task_count') != len(keys) or doc.get('weights') != WEIGHTS or doc.get('normalization_scales') != SCALES:
        raise ValueError('Designed score metadata differs from the versioned method')
    required = {f'{domain}/{name}' for domain, _ in expected
                for name in ('test_cases.py', 'test_cases.json', 'agent_definition.yaml')}
    if set(doc.get('source_sha256', {})) != required:
        raise ValueError('Designed scores must fingerprint every supplied source')
    root = Path(data_dir).resolve(); sources = []
    for name, digest in doc['source_sha256'].items():
        p = (root/name).resolve()
        if not p.is_relative_to(root) or file_hash(p) != digest:
            raise ValueError('Designed score source changed or escaped data root')
        sources.append(p)
    # Recompute the full source-backed artifact: rejects altered scores and annotations.
    if doc != build(data_dir):
        raise ValueError('Designed score artifact differs from the current reproducible method')
    return doc, dict(zip(keys, doc['tasks'])), sources+[ANNOTATIONS, Path(__file__)]


def write_outputs(out, document):
    out = Path(out).resolve(); source = DATA_DIR.resolve()
    if out == source or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('Output must not overlap supplied data')
    if out.exists():
        raise ValueError('Use a fresh output directory; existing results are never overwritten')
    out.mkdir(parents=True)
    (out/'scores.json').write_text(json.dumps(document, indent=2)+'\n')
    columns = ['domain', 'task_id', 'title', 'status', 'score', 'rank_easy_first', *COMPONENTS,
               'supplied_tag_comparison_only', 'shared_workflow_steps_comparison_only',
               'excluded_terminal_groups', 'excluded_external_groups', 'excluded_wait_groups',
               'max_rank_change_under_alternative_weights', 'uncertainty_flags']
    with (out/'scores.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns); writer.writeheader()
        for row in document['tasks']:
            writer.writerow({k: '|'.join(row[k]) if isinstance(row[k], list) else row[k] for k in columns})
    rows = document['tasks']
    def describe(subset):
        return {'n_tasks': len(subset), 'mean_score': round(mean(r['score'] for r in subset),6),
                'min_score': min(r['score'] for r in subset), 'max_score': max(r['score'] for r in subset)}
    summary = {'method_version': VERSION, 'status': document['status'], 'all': describe(rows),
        'domains': {d: describe([r for r in rows if r['domain']==d]) for d in sorted({r['domain'] for r in rows})},
        'labels_descriptive_only_not_validation': {t: describe([r for r in rows if r['supplied_tag_comparison_only']==t])
                                                   for t in sorted({r['supplied_tag_comparison_only'] for r in rows})},
        'weight_sensitivity': {'variants': VARIANTS,
            'max_rank_change': max(r['max_rank_change_under_alternative_weights'] for r in rows)},
        'score_is_not_failure_probability': True, 'no_independent_validation': True}
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    with (out/'weight_sensitivity.csv').open('w', newline='') as f:
        cols=['domain','task_id']+[f'{n}_{suffix}' for n in VARIANTS for suffix in ('score','rank')]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in rows:
            w.writerow({'domain':r['domain'],'task_id':r['task_id'],
                        **{f'{n}_score':r['score_variants'][n] for n in VARIANTS},
                        **{f'{n}_rank':r['variant_ranks'][n] for n in VARIANTS}})
    top = sorted(rows, key=lambda r: (-r['score'], r['domain'], r['task_id']))[:3]
    bottom = sorted(rows, key=lambda r: (r['score'], r['domain'], r['task_id']))[:3]
    text = f'''# Provisional designed difficulty for all 64 synthetic tasks

All {len(rows)} tasks across {document['domain_count']} domains have a reproducible
0–100 complexity index and source-backed component counts. Higher means more
complex under this baseline. This is not a probability, success rate, validated
measurement or a comparison scale with tau2-bench. No agent or API runs were used.

## Start here

Open scores.csv for the 64 results. Read the three component counts before the
combined score. scores.json contains every source excerpt, annotation and flag.
The supplied easy/medium/hard labels are comparison columns, never score inputs.

Formula: score = 100 / 3 × (active task milestone groups / 9 + expected business
tool interactions / 23 + business-check groups / 4). Scales are frozen to this
64-task snapshot. Equal weights are provisional. Changing the task set or counting
rules requires a new version, not silently fitting new scales.

An action group is one active task milestone, excluding terminal signals, passive
responses/approvals and waiting. A milestone may bundle multiple operations, so
this is not an exact atomic action count. A business-check group is an explicitly
annotated evaluative milestone, not a verified independent decision or branch.
Calls come from the intended reference, not observed execution; repeated calls
count again and system signals are excluded. No extra penalty is added for bad
references, missing inputs or environmental defects. A score does not certify
that a task is runnable or that its reference is correct.

Highest three under this method:
'''
    text += ''.join(f"- {r['task_id']}: {r['score']:.2f}\n" for r in top)
    text += '\nLowest three under this method:\n'+''.join(f"- {r['task_id']}: {r['score']:.2f}\n" for r in bottom)
    text += f'''
## Limits and next use

The method can tie tasks with different semantic complexity, including the easy
and hard insurance examples with identical component counts. The features overlap;
more tool calls may also mean more actions or checks. weight_sensitivity.csv shows
alternative weights, not validation. The largest rank shift is
{summary['weight_sensitivity']['max_rank_change']:.1f} places across the tested alternatives.
Do not tune weights just to reproduce supplied labels or the assistant's six-task
ranking. Those are not independent validation targets. Exact atomic actions and
independent decisions remain unknown. All annotations are assistant interpretations.

The usable first version is complete; approval and independent validation are not
claimed. Review feature definitions with Sandra before describing scores as final.

Reproduce into a fresh directory:

    python -m difficulty.designed_difficulty --out results/difficulty/designed_fresh

Method: docs/evaluation/designed_difficulty_v0.1.md
Annotations: difficulty/designed_annotations_v1.json
'''
    (out/'README.md').write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=REPO/'results/difficulty/designed_v1')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Use a fresh output directory to preserve existing results')
    document = build(); write_outputs(args.out, document)
    print(f"Scored {document['task_count']} tasks; provisional designed complexity; no API calls. Output: {args.out}")


if __name__ == '__main__':
    main()
