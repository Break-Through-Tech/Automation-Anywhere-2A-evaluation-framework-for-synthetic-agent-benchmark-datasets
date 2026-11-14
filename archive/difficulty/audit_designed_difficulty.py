"""Audit the frozen v0.1 designed index without changing scores or calling models."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean
from scipy.stats import spearmanr

from . import designed_difficulty as designed
from .saved_trials import file_hash

SCORES = designed.REPO/'results/difficulty/designed_v1/scores.json'


def profile_groups(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in designed.COMPONENTS)].append(row)
    return [{'counts': dict(zip(designed.COMPONENTS, key)), 'n_tasks': len(group),
             'task_ids': [r['task_id'] for r in group],
             'domains': sorted({r['domain'] for r in group}),
             'supplied_tags_comparison_only': sorted({r['supplied_tag_comparison_only'] for r in group})}
            for key, group in sorted(groups.items())]


def sensitivity(rows):
    result = {}
    for name in designed.VARIANTS:
        if name == 'equal':
            continue
        changes = [abs(r['variant_ranks'][name]-r['rank_easy_first']) for r in rows]
        result[name] = {'comparison_type': 'component_removal' if name=='without_checks' else 'weight_change',
                        'max_absolute_rank_change': max(changes),
                        'mean_absolute_rank_change': mean(changes),
                        'tasks_moving_at_least_10_places': sum(x>=10 for x in changes)}
    return result


def audit_document(document):
    rows = document['tasks']; groups = profile_groups(rows)
    ordered = sorted(rows, key=lambda r: r['score'])
    correlations = []
    for i, a in enumerate(designed.COMPONENTS):
        for b in designed.COMPONENTS[i+1:]:
            correlations.append({'first': a, 'second': b,
                'spearman_rho': float(spearmanr([r[a] for r in rows],[r[b] for r in rows]).statistic),
                'interpretation': 'Descriptive feature overlap; not outcome validation or independent-task inference.'})
    top_boundary = ordered[-5]['score']; bottom_boundary = ordered[4]['score']
    review_ids = {
        'InsuranceClaimsIntakeAndTriageAgent_W3_TC1': ('highest',
            'Three claims and two emergency dispatches explain the 23 reference business calls. High volume is supported by the intended reference, not proof of hardest reasoning.'),
        'BankingCustomerOnboardingAgent_BankOnboard_W7_TC1': ('near_highest',
            'Address mismatch recovery includes two extraction and two communication calls. Four evaluative milestone groups contribute a full 33.33 points; their independence is not established.'),
        'DigitalAccountOpeningAgent_W1_TC2': ('high_tied_profile',
            'Identity, AML, tier and funding verification give four check groups. Six account tasks share (8,8,4), including a multi-owner business task; depth and entity multiplicity are not resolved.'),
        'ManufacturingPurchaseToPayAutomationAgent_P2P_W5_TC1': ('lowest',
            'A short duplicate-invoice branch has two active milestone groups and two business calls. Rejection is the intended endpoint. Notification is bundled into a milestone and terminal result; a short reference does not establish that notification is fully implemented.'),
        'HealthcarePA_W8_TC1': ('near_lowest',
            'The approved status path has three milestones and one lookup call, not all five shared workflow steps. Missing reference_id is a separate feasibility concern and is not a complexity penalty.'),
        'InsuranceClaimsIntakeAndTriageAgent_W1_TC1': ('semantic_tie',
            'Emergency property intake has profile (8,8,3). It ties the commercial-interruption task despite different required entities and specialist coordination.'),
        'InsuranceClaimsIntakeAndTriageAgent_W8_TC1': ('semantic_tie',
            'The milestones require property and business-interruption coverage, linked claims, large-loss and BI specialists, and accountant/engineer dispatch. Grouped counts collapse those requirements to the same (8,8,3) profile as ordinary emergency property intake.'),
        'HealthcareOnboarding_W5_TC1': ('largest_component_removal_mover',
            'Six active groups and six reference calls, but no annotated check group. Rank moves from 6 to 26.5 only when checks are removed; ordinary weight changes move it from 6 to 7. Zero annotated checks is not proof of zero reasoning.'),
        'ManufacturingPurchaseToPayAutomationAgent_P2P_W4_TC1': ('largest_weight_change_mover',
            'Partial receipt and a backorder lead to partial and final payments. Rank moves from 8 to 18 with action-heavy weights; the four-call reference includes two payment calls. This supports a dependency/repetition feature discussion, not a proven correct rank.')}
    examples = []
    for row in rows:
        if row['task_id'] in review_ids:
            category, interpretation = review_ids[row['task_id']]
            examples.append({**row, 'audit_category': category, 'assistant_interpretation': interpretation})
    ties = [g for g in groups if g['n_tasks']>1]
    return {'audit_version': 'designed_difficulty_audit_v0.1', 'score_method': document['version'],
        'status': 'offline_internal_review_not_independent_validation', 'n_tasks': len(rows),
        'n_distinct_component_profiles': len(groups), 'n_tied_profile_groups': len(ties),
        'n_tasks_in_tied_profiles': sum(g['n_tasks'] for g in ties),
        'profile_groups': groups, 'weight_sensitivity': sensitivity(rows),
        'points_for_one_more_unit': {k: 100*designed.WEIGHTS[k]/designed.SCALES[k] for k in designed.COMPONENTS},
        'component_correlations': correlations,
        'top_band_with_boundary_ties': [r['task_id'] for r in sorted(rows,key=lambda r:(-r['score'],r['task_id'])) if r['score']>=top_boundary],
        'bottom_band_with_boundary_ties': [r['task_id'] for r in ordered if r['score']<=bottom_boundary],
        'reviewed_examples': examples,
        'recommendation': 'Retain v0.1 as an exploratory baseline, lead with its component profile, and revise requirement granularity and explicit coordination/dependencies before promoting a scalar to the final metric. Weight tuning alone cannot separate identical profiles.',
        'no_api_calls': True, 'scores_changed': False, 'validation_claimed': False}


def write_audit(scores_path, out):
    scores_path=Path(scores_path);out=Path(out).resolve()
    if out.exists():
        raise ValueError('Use a fresh audit directory; existing results are not overwritten')
    source=designed.DATA_DIR.resolve()
    if out==source or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('Audit output must not overlap supplied sources')
    document=json.loads(scores_path.read_text())
    if document!=designed.build():
        raise ValueError('Audit requires the exact reproducible current v0.1 scores')
    result=audit_document(document)
    result['inputs']={'scores_sha256':file_hash(scores_path), 'annotations_sha256':file_hash(designed.ANNOTATIONS),
                     'method_sha256':file_hash(Path(designed.__file__)), 'audit_implementation_sha256':file_hash(Path(__file__))}
    out.mkdir(parents=True)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    text=f'''# Audit of the provisional designed difficulty index

## Recommendation for Sandra

Keep v0.1 as an exploratory baseline and show the three component counts first.
Do not present its scalar ranking as a validated final difficulty measure.
The code reproduces the intended formula; the main problems are feature coverage
and annotation granularity. Weights alone cannot distinguish tasks with identical
component counts. No baseline scores or supplied data were changed in this audit.

## What looks reasonable

The highest index, 87.96, belongs to a catastrophe batch with three claims and
23 reference business calls, including two emergency dispatches. This explains
its placement as high-volume work; it does not prove hardest reasoning.
The lowest index, 18.64, belongs to duplicate-invoice rejection, a short intended
branch. Approved-authorization status lookup is also near the bottom at 20.89.
These placements are plausible from source scope, not independently established.
The notification obligations in the low-scoring examples may still be bundled
or weakly expressed by their reference tool sequences.

## What needs revision

1. **Limited resolution.** There are {result['n_distinct_component_profiles']} distinct three-component profiles across
   {result['n_tasks']} tasks. {result['n_tasks_in_tied_profiles']} tasks belong to {result['n_tied_profile_groups']} repeated-profile groups. Some ties are
   sensible, but others hide meaningful differences. The emergency property and
   complex commercial-interruption examples both score 66.22 from (8,8,3), even
   though commercial interruption requires linked claims and several specialist
   roles. Any weights applied to those same counts will leave them tied.
2. **Source grouping affects scores.** One milestone can bundle multiple actions,
   entities or checks. An action group is not an atomic action, and a check group
   is not an independently resolved decision. Standardize these units before
   adding more decimal places or adjusting weights.
3. **Feature overlap.** Descriptive Spearman associations are {result['component_correlations'][0]['spearman_rho']:.2f} between action
   groups and calls, {result['component_correlations'][1]['spearman_rho']:.2f} between action groups and checks, and {result['component_correlations'][2]['spearman_rho']:.2f} between calls
   and checks. This suggests overlapping signals; it does not prove any feature
   invalid. Tasks share workflows, so these are not independent inferential tests.
4. **Normalization matters.** One extra action group adds {result['points_for_one_more_unit']['action_groups']:.2f} points, one extra
   reference call adds {result['points_for_one_more_unit']['reference_tool_interactions']:.2f}, and one extra check group adds {result['points_for_one_more_unit']['business_check_groups']:.2f}. Equal component
   weights do not mean equal per-item influence. Twenty-three calls is the batch
   maximum, so eight calls contribute only 11.59 of a possible 33.33 points.

## Weight sensitivity with the comparisons kept separate

Moving weights from equal thirds to action-heavy (.50/.25/.25) changes a task's
rank by at most {result['weight_sensitivity']['action_heavy']['max_absolute_rank_change']:g} places; {result['weight_sensitivity']['action_heavy']['tasks_moving_at_least_10_places']} task moves at least 10. Tool-heavy
(.25/.50/.25) changes ranks by at most {result['weight_sensitivity']['tool_heavy']['max_absolute_rank_change']:g} places.

Removing checks entirely (.50/.50/0) is a component-removal experiment, not a
small weight adjustment. It changes a task's rank by as much as {result['weight_sensitivity']['without_checks']['max_absolute_rank_change']:g} places;
{result['weight_sensitivity']['without_checks']['tasks_moving_at_least_10_places']} tasks move at least 10. Self-pay onboarding moves from rank 6 to 26.5 in
that experiment, but only to rank 7 under the two ordinary weight variants.
Ranks are average ranks for ties, with 1 easiest and 64 hardest. Rank changes
measure sensitivity, not which ordering is correct.

## What to do next

- Preserve v0.1 and its evidence as the baseline; do not silently overwrite it.
- Make profiles primary in the meeting and the composite index secondary.
- In a new version, define actions at a consistent granularity and separately
  describe required repetitions, linked entities, approvals and coordination.
  Keep these features descriptive until their aggregation is justified.
- Do not tune weights to copy supplied easy/medium/hard tags or the assistant's
  earlier ranking. Neither is independent validation. Do not treat an apparent
  label mismatch as proof that the task, annotation or score is wrong.

Suggested meeting statement: “We have a reproducible 64-task baseline. The audit
shows it measures work volume better than it distinguishes all forms of task
complexity. I recommend leading with the feature profile and refining action
units and coordination before declaring a final single score.”

## Source-backed reviewed examples
'''
    for e in examples_sorted(result['reviewed_examples']):
        text+=f"\n### {e['title']}\n\nTask: `{e['task_id']}`. Score {e['score']:.2f}; profile ({e['action_groups']},{e['reference_tool_interactions']},{e['business_check_groups']}).\n\n{e['assistant_interpretation']}\n\nSource: `data/{e['sources']['python_file']}:{e['sources']['python_class_line']}`; `data/{e['sources']['json_file']}` at `{e['sources']['json_case_pointer']}`. Exact milestone excerpts and pointers are in audit.json.\n"
    text+='''
## Checks and reproducibility

The audit verifies the saved artifact against a fresh offline build, including
source hashes. All statistics come from the original 64 records; supplied tags
are comparison context only. Source inspection is the assistant's interpretation,
not a human review, task rerun, completion judgment or independent validation.
Top-band selection retains ties at the fifth-place boundary rather than picking
an arbitrary five tasks. Original scores and outcome judgments remain unchanged.

    python -m difficulty.audit_designed_difficulty --out results/difficulty/designed_audit_fresh
'''
    (out/'README.md').write_text(text)
    return result


def examples_sorted(examples):
    return sorted(examples,key=lambda r:(-r['score'],r['task_id']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scores',type=Path,default=SCORES)
    parser.add_argument('--out',type=Path,default=designed.REPO/'results/difficulty/designed_audit_v1')
    args=parser.parse_args();result=write_audit(args.scores,args.out)
    print(f"Audited {result['n_tasks']} tasks. Scores unchanged; no API calls. Output: {args.out}")


if __name__=='__main__':main()
