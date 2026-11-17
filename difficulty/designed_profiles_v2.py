"""Richer source-bound designed complexity profiles; no new scalar or model calls."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from . import designed_difficulty as baseline
from .saved_trials import file_hash

VERSION = 'designed_profiles_v0.2_provisional'
ANNOTATIONS = baseline.REPO/'difficulty/designed_annotations_v2.json'
KINDS = {'linked_records','approval','handoff','multi_party','external_response','multi_channel'}


def build(annotations_path=ANNOTATIONS):
    previous = baseline.build()
    raw = json.loads(Path(annotations_path).read_text())
    if raw.get('version') != 'designed_annotations_v0.2' or raw.get('source_sha256') != previous['source_sha256']:
        raise ValueError('Unsupported annotations or stale source fingerprints')
    saved = baseline.REPO/'results/difficulty/designed_v1/scores.json'
    if file_hash(saved) != raw['baseline_scores_sha256'] or json.loads(saved.read_text()) != previous:
        raise ValueError('Baseline must remain unchanged and reproducible')
    keys = [(r['domain'],r['task_id']) for r in raw['tasks']]
    expected = {(r['domain'],r['task_id']):r for r in previous['tasks']}
    if len(keys)!=len(set(keys)) or set(keys)!=set(expected):
        raise ValueError('Exactly one annotation per canonical task is required')
    rows=[]
    for item in raw['tasks']:
        old=expected[(item['domain'],item['task_id'])]
        if len(item['milestones']) != len(old['milestone_evidence']):
            raise ValueError('Milestone coverage differs from source')
        ms=[]; sources={}
        for m, source in zip(item['milestones'],old['milestone_evidence']):
            if (m['step'],m['expected_description'],m['role'],m['business_check_group']) != (source['step'],source['expected_description'],source['role'],source['business_check']):
                raise ValueError('Annotation identity, role or source text drifted')
            units=m['operation_units']
            if not isinstance(units,list) or any(not isinstance(u,str) or not u.strip() for u in units) or len({u.casefold() for u in units})!=len(units):
                raise ValueError('Operation units must be nonempty distinct descriptions')
            active=m['role']=='active_action_group'
            if active != bool(units):
                raise ValueError('Only active milestones can contain operation units')
            if type(m['unresolved_granularity']) is not bool:
                raise ValueError('Granularity uncertainty must be explicit')
            if m['split_status'] not in {'explicit_distinct_operations','conservative_group_retained','not_agent_action'}:
                raise ValueError('Unsupported split status')
            if (m['split_status']=='explicit_distinct_operations') != (len(units)>1):
                raise ValueError('Split status and number of units disagree')
            ev={'source':source['source'],'locator':source['locator'],'excerpt':source['expected_description']}
            sources[(ev['source'],ev['locator'])]=ev['excerpt']
            ms.append({**m,'evidence':ev})
        requirements=item['coordination_requirements'];ids=set()
        for req in requirements:
            if req['kind'] not in KINDS or req['id'] in ids or not req['description'].strip():
                raise ValueError('Unsupported or duplicated coordination requirement')
            ids.add(req['id'])
            if not req['evidence']:
                raise ValueError('Coordination requires source evidence')
            for ev in req['evidence']:
                value=sources.get((ev['source'],ev['locator']))
                if value is None or not ev['excerpt'] or ev['excerpt'] not in value:
                    raise ValueError('Coordination source citation is invalid')
        calls=Counter(n for n in old['reference_tool_sequence'] if n not in {'SUCCESS','FAILED','CANCELLED','HUMAN_IN_THE_LOOP'})
        repeated={name:n for name,n in sorted(calls.items()) if n>1}
        counts=Counter(r['kind'] for r in requirements)
        rows.append({'domain':item['domain'],'task_id':item['task_id'],'title':old['title'],
            'status':VERSION,'proposed_operation_unit_count':sum(len(m['operation_units']) for m in ms),
            'v1_action_groups':old['action_groups'],'reference_tool_interactions':old['reference_tool_interactions'],
            'business_check_groups':old['business_check_groups'],
            'additional_reference_calls_from_repetition':sum(n-1 for n in repeated.values()),
            'repeated_reference_tools':repeated,
            **{kind+'_requirements':counts[kind] for kind in sorted(KINDS)},
            'unresolved_granularity_groups':sum(m['unresolved_granularity'] for m in ms),
            'explicit_wait_groups':old['excluded_wait_groups'],
            'v1_score_reference_only':old['score'],'v2_combined_score':None,
            'exact_atomic_actions':None,'exact_independent_decisions':None,
            'milestones':ms,'coordination_evidence':requirements,'sources':old['sources'],
            'flags':['assistant_interpretation_not_independent_validation',
                     'conservative_units_not_exhaustive_atomic_actions',
                     'coordination_dimensions_overlap_do_not_sum_as_score',
                     'source_feasibility_not_scored']})
    return {'version':VERSION,'status':'complete_provisional_profiles_no_new_scalar',
            'task_count':len(rows),'domain_count':len({r['domain'] for r in rows}),
            'network_calls':0,'agent_runs':0,'paid_llm_reviews':0,'independent_validation':False,
            'source_sha256':raw['source_sha256'],'baseline_scores_sha256':raw['baseline_scores_sha256'],
            'annotations_sha256':file_hash(annotations_path),'implementation_sha256':file_hash(Path(__file__)),
            'tasks':rows}


def write_outputs(out,doc):
    out=Path(out).resolve();source=baseline.DATA_DIR.resolve()
    if out==source or out.is_relative_to(source) or source.is_relative_to(out):raise ValueError('Output overlaps supplied data')
    if out.exists():raise ValueError('Use a fresh output directory')
    out.mkdir(parents=True)
    (out/'profiles.json').write_text(json.dumps(doc,indent=2)+'\n')
    cols=['domain','task_id','title','proposed_operation_unit_count','v1_action_groups',
          'reference_tool_interactions','business_check_groups','additional_reference_calls_from_repetition',
          *[k+'_requirements' for k in sorted(KINDS)],'unresolved_granularity_groups','v1_score_reference_only']
    with (out/'profiles.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:r[k] for k in cols} for r in doc['tasks'])
    summary={'n_tasks':doc['task_count'],'n_tasks_with_explicit_operation_splits':sum(r['proposed_operation_unit_count']>r['v1_action_groups'] for r in doc['tasks']),
             'n_tasks_with_documented_coordination':sum(bool(r['coordination_evidence']) for r in doc['tasks']),
             'n_tasks_with_unresolved_granularity':sum(r['unresolved_granularity_groups']>0 for r in doc['tasks']),
             'combined_score':None,'independent_validation':False}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    byid={r['task_id']:r for r in doc['tasks']}
    examples=[('InsuranceClaimsIntakeAndTriageAgent_W1_TC1','Emergency property'),('InsuranceClaimsIntakeAndTriageAgent_W8_TC1','Commercial interruption'),('HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1','Insurance-update recovery')]
    text='''# Designed complexity profiles version 0.2

## What changed

All 64 tasks now include proposed operational units, repetition and source-backed
coordination requirements. Original v0.1 scores remain unchanged. There is no new
weighted scalar: adding weights before agreeing on overlapping features would
hide the uncertainty identified in the audit.

## How to read the profiles

Start with title and proposed_operation_unit_count. This is a conservative
assistant interpretation, not a minimum execution length or
an exact atomic action count. Only clearly distinct active operations are split;
noun lists, fields, audiences, prepared/assembled wording and opaque bundled work
are not automatically separate actions. Passive responses, waiting and completion
signals remain outside active units. Unresolved groups are explicitly counted.

Then read reference_tool_interactions and additional_reference_calls_from_repetition.
Repeated calls come from the supplied intended reference, not agent execution.
The coordination columns count documented requirements, not people or difficulty
points. They include approvals, handoffs, linked records, multiple parties,
external responses and multiple communication channels. One source requirement
can appear in more than one dimension; do not add these columns into a score.
Zero means no requirement annotated under these rules, not proof of no coordination.

## Examples that the old counts hid
'''
    for tid,title in examples:
        r=byid[tid]
        text+=f"\n- {title}: {r['v1_action_groups']} old action groups; {r['proposed_operation_unit_count']} proposed operation units; {r['linked_records_requirements']} linked-record, {r['multi_party_requirements']} multi-party and {r['handoff_requirements']} handoff requirements.\n"
    text+='''
The commercial and emergency claim examples can now be distinguished by their
coordination profile, rather than by changing weights on identical old counts.
That is better feature coverage, not proof that one has a particular true score.
All counts remain provisional assistant annotations with exact source excerpts.

## Complementary LLM review

A separate source-only reviewer can propose operational units, business checks,
coordination and uncertainties without seeing our counts, score, supplied difficulty
tag or earlier ranking. We compare the proposals and inspect disagreements.
It does not judge whether an agent succeeded. It is neither human validation nor
an automatic authority that overwrites the profile or supplies scoring weights.
Three blinded-to-our-features requests are prepared offline under
results/difficulty/design_review_v1. No paid LLM review has been run.

Full definitions: docs/evaluation/designed_profiles_v0.2.md.

    python -m difficulty.designed_profiles_v2 --out results/difficulty/designed_v2_fresh
'''
    (out/'README.md').write_text(text)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=baseline.REPO/'results/difficulty/designed_v2')
    a=p.parse_args();doc=build();write_outputs(a.out,doc)
    print(f"Prepared {doc['task_count']} richer profiles; original scores unchanged; no API calls.")


if __name__=='__main__':main()
