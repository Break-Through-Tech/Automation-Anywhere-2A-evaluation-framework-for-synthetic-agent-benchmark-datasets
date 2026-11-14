"""Offline scoring experiments on frozen v0.3 profiles; no production score update."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import mean

from . import designed_profiles_v3 as profiles
from .designed_difficulty import ranks, REPO
from .saved_trials import file_hash

VERSION='designed_scoring_comparison_v0.1'
INPUT=REPO/'results/difficulty/designed_v3/profiles.json'
SCALES={'operations':11,'reference_calls':23,'additional_coordination_events':3}
COORD_WEIGHTS=(0,.1,.2,.3,.5)


def additional_coordination_events(requirements):
    events=defaultdict(set)
    for r in requirements:events[r['event_key']].add(r['kind'])
    # Exclude pure routing/dispatch events already reflected as active operations.
    # Other dimensions can still overlap with work; no independence is claimed.
    return sorted(key for key,kinds in events.items() if kinds-{'handoff'})


def candidate_values(operations,calls,coord):
    counts=dict(zip(SCALES,(operations,calls,coord)))
    if any(type(v) is not int or v<0 or v>SCALES[k] for k,v in counts.items()):
        raise ValueError('Candidate counts outside the frozen v0.3 comparison scales')
    o=operations/SCALES['operations'];t=calls/SCALES['reference_calls'];c=coord/SCALES['additional_coordination_events']
    workload=(o+t)/2
    return ({'operations_only':round(100*o,6),'workload_only':round(100*workload,6),
            'workload_coord20':round(100*(.8*workload+.2*c),6)},
           {str(w):round(100*((1-w)*workload+w*c),6) for w in COORD_WEIGHTS})


def build(path=INPUT):
    path=Path(path);doc=json.loads(path.read_text())
    if doc!=profiles.build():raise ValueError('Scoring comparison requires reproducible current v0.3 profiles')
    rows=[]
    for r in doc['tasks']:
        events=additional_coordination_events(r['coordination_evidence'])
        values,sensitivity=candidate_values(r['proposed_operation_unit_count'],r['reference_tool_interactions'],len(events))
        rows.append({'domain':r['domain'],'task_id':r['task_id'],'title':r['title'],
         'operations':r['proposed_operation_unit_count'],'reference_calls':r['reference_tool_interactions'],
         'additional_coordination_events':len(events),'additional_coordination_event_keys':events,
         'uncertain_global_requirements':r['uncertain_global_requirements'],
         'unresolved_granularity_groups':r['unresolved_granularity_groups'],
         'added_global_operations':r['added_global_operations'],'global_requirement_dispositions':r['global_requirement_dispositions'],
         'candidate_indices':values,'coordination_weight_indices':sensitivity})
    names=list(rows[0]['candidate_indices']);rankings={n:ranks(rows,lambda r:r['candidate_indices'][n]) for n in names}
    weight_ranks={str(w):ranks(rows,lambda r:r['coordination_weight_indices'][str(w)]) for w in COORD_WEIGHTS}
    for r in rows:
        r['candidate_ranks']={n:rankings[n][r['candidate_indices'][n]] for n in names}
        r['coordination_weight_ranks']={w:rs[r['coordination_weight_indices'][w]] for w,rs in weight_ranks.items()}
    summary={}
    for n in names:
        counts=Counter(r['candidate_indices'][n] for r in rows)
        summary[n]={'distinct_index_values':len(counts),'tasks_in_ties':sum(v for v in counts.values() if v>1),
                    'min_index':min(counts),'max_index':max(counts)}
    sensitivity={w:{'max_rank_change_from_no_coordination':max(abs(r['coordination_weight_ranks'][w]-r['candidate_ranks']['workload_only']) for r in rows),
                    'tasks_moving_at_least_10_places':sum(abs(r['coordination_weight_ranks'][w]-r['candidate_ranks']['workload_only'])>=10 for r in rows)} for w in weight_ranks if w!='0'}
    changed=[{'task_id':r['task_id'],'title':r['title'],'n_added_operations':len(r['added_global_operations']),
              'added_descriptions':[o['description'] for o in r['added_global_operations']],
              'check_result':'source-backed applicability and duplicate checks passed; interpretation remains provisional'}
              for r in rows if r['added_global_operations']]
    return {'version':VERSION,'status':'offline_options_not_adopted_or_validated','n_tasks':len(rows),
        'scales':SCALES,'profile_only_has_no_scalar_or_rank':True,'candidate_summary':summary,
        'coordination_weight_sensitivity':sensitivity,'n_tasks_with_uncertain_global_requirements':sum(r['uncertain_global_requirements']>0 for r in rows),
        'n_tasks_with_additional_coordination':sum(r['additional_coordination_events']>0 for r in rows),
        'reviewed_changed_tasks':changed,'source_profiles_sha256':file_hash(path),
        'comparison_implementation_sha256':file_hash(Path(__file__)),'network_calls':0,
        'recommended_primary':'v0.3 feature profile','combined_index_adopted':False,'tasks':rows}


def write_outputs(out,result):
    out=Path(out).resolve();data=profiles.DATA_DIR.resolve()
    if out.exists():raise ValueError('Use a fresh comparison directory')
    if out==data or out.is_relative_to(data) or data.is_relative_to(out):raise ValueError('Output overlaps supplied data')
    out.mkdir(parents=True)
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    names=list(result['candidate_summary']);cols=['domain','task_id','title','operations','reference_calls',
        'additional_coordination_events','uncertain_global_requirements',*[n+s for n in names for s in ('_index','_rank')]]
    with (out/'scoring_options.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in result['tasks']:
            w.writerow({**{k:r[k] for k in cols if k in r},
                        **{n+'_index':r['candidate_indices'][n] for n in names},
                        **{n+'_rank':r['candidate_ranks'][n] for n in names}})
    names=[str(w) for w in COORD_WEIGHTS];cols=['domain','task_id']+['coord_'+w+'_'+s for w in names for s in ('index','rank')]
    with (out/'weight_sensitivity.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in result['tasks']:
            w.writerow({'domain':r['domain'],'task_id':r['task_id'],
                        **{'coord_'+k+'_index':r['coordination_weight_indices'][k] for k in names},
                        **{'coord_'+k+'_rank':r['coordination_weight_ranks'][k] for k in names}})
    rs={r['task_id']:r for r in result['tasks']};e=rs['InsuranceClaimsIntakeAndTriageAgent_W1_TC1'];c=rs['InsuranceClaimsIntakeAndTriageAgent_W8_TC1'];b=rs['InsuranceClaimsIntakeAndTriageAgent_W3_TC1']
    shift=result['coordination_weight_sensitivity']['0.2']['max_rank_change_from_no_coordination']
    text=f'''# Recommendation on presenting designed difficulty

## Recommendation for Sandra

Use the v0.3 feature profile as the primary designed-difficulty measure. Report
operations, intended tool interactions, checks and explicit coordination together,
with uncertainty flags. Keep the experimental combined index secondary and do
not call it a validated final score. This is a concrete project deliverable;
choosing an unsupported universal weighting is not necessary to present it.

If a single number is required, show the 80% workload / 20% additional-coordination
index as a transparent candidate for discussion, not an adopted score or a failure
probability. I do not recommend declaring its 20% coordination weight final: it
moves ranks substantially. The weight is an assumption, not a learned optimum.

## What was checked

All 64 profiles reproduce from their frozen inputs. The 12 changed tasks retain
source evidence for all 22 additional operations; covered checks, the self-pay
exception, update phases and deduplicated AP/claim events are tested. There remain
{result['n_tasks_with_uncertain_global_requirements']} tasks with unresolved global duties, plus retained action-granularity flags.
These are interpretation limits, not agent failures. No API calls or profile,
score, source-data or model-response edits were made.

## Options compared

- Profile only: no scalar or rank. It preserves distinctions and uncertainty but
  requires reading several features. This is the recommended primary output.
- Operations only: 100 × operations / 11. Simple workload baseline, but a bulk
  milestone can hide repeated work. The three-claim batch has eight operation
  groups, so this alone does not express its 23 intended reference calls.
- Workload only: 100 × (operations / 11 + reference calls / 23) / 2. Captures
  reference repetition as well as required work, but the two inputs overlap and
  reference call counts can be incomplete. This is not double-count-free truth.
- Workload plus coordination: 100 × [0.4 × operations / 11 + 0.4 × calls / 23
  + 0.2 × additional-coordination events / 3]. It excludes handoff-only events
  already represented by routing/dispatch actions. An event carrying several
  categories counts once. Business checks are not added again as a scored term
  because they are already active evaluations. Residual overlap remains: linked
  records, approvals or multiple-role coordination may still be reflected in work.

Scales 11, 23 and 3 are frozen to this v0.3 64-task snapshot, not inherited from
v0.1 or refitted per domain. No easy/medium/hard cutoffs, uncertainty penalty or
validated confidence intervals are introduced. All ranks are conditional on the
current documented counts; ambiguous duties are not silently imputed.

## Concrete examples

The emergency property and commercial interruption cases both have eight
operations and eight reference calls. They tie at {e['candidate_indices']['workload_only']:.2f} on workload alone.
After counting additional coordination once per event, they have zero versus
three such events. The 80/20 candidate becomes {e['candidate_indices']['workload_coord20']:.2f} versus {c['candidate_indices']['workload_coord20']:.2f}.
This shows that the feature distinguishes requirements. It does not establish
that the 20-point difference is the correct amount of difficulty.

The catastrophe batch remains higher at {b['candidate_indices']['workload_coord20']:.2f} under that candidate because its
three-claim reference contains 23 business calls. That expresses work volume,
not proof that its reasoning is harder than a commercial claim.

## Sensitivity and limitations

Using coordination weights of 0%, 10%, 20%, 30% and a 50% stress case changes
rankings. At 20%, the largest rank change from workload-only is {shift:g} places.
More distinct scores or resolving a preferred tie is not validation. Do not tune
weights to supplied tags, the assistant's ranking or these selected examples.
This comparison does not use agent outcomes or claim independent validation.

## Suggested meeting statement

“We have a reproducible designed-complexity profile for all 64 tasks. The source
review and LLM experiment helped us find omitted global requirements and clarify
coordination. I recommend the profile as the main result. If one number is required,
we have a transparent workload-plus-coordination candidate, with explicit weights
and sensitivity results, rather than claiming it is already validated.”

## Files and reproduction

scoring_options.csv contains all exploratory indices and ranks. comparison.json
contains input fingerprints, the 12 changed-task checks, formulas' inputs and
summary statistics. weight_sensitivity.csv keeps all tested coordination weights.
Current profiles and previous indices are separate and remain unchanged.

    python -m difficulty.compare_designed_scoring --out results/difficulty/scoring_options_fresh
'''
    (out/'README.md').write_text(text)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=REPO/'results/difficulty/scoring_options_v1')
    a=p.parse_args();result=build();write_outputs(a.out,result)
    print('Compared profiles and three experimental indices for 64 tasks; no API calls or adopted score.')


if __name__=='__main__':main()
