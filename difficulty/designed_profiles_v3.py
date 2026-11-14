"""Apply source-bound global-rule scope and coordination conventions offline."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import yaml

from . import designed_profiles_v2 as v2
from .designed_difficulty import REPO, DATA_DIR
from .judge_evidence import pointer_value
from .saved_trials import file_hash

VERSION='designed_profiles_v0.3_scope_clarified'
ANNOTATIONS=REPO/'difficulty/designed_scope_annotations_v3.json'
RULES=REPO/'docs/evaluation/design_counting_rulebook_v0.2.md'
DISPOSITIONS={'covered','added','not_applicable','conditional_not_selected','uncertain','constraint_only'}


def check_source_evidence(evidence,cache=None):
    cache={} if cache is None else cache
    if not isinstance(evidence,list) or not evidence:raise ValueError('Source evidence is required')
    for ev in evidence:
        p=(DATA_DIR/ev['source']).resolve()
        if not p.is_relative_to(DATA_DIR.resolve()):raise ValueError('Evidence source escaped data root')
        if p.suffix not in {'.json','.yaml'}:raise ValueError('Unsupported evidence source type')
        if p not in cache:cache[p]=json.loads(p.read_text()) if p.suffix=='.json' else yaml.safe_load(p.read_text())
        value=pointer_value(cache[p],ev['locator']);text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
        if not isinstance(ev['excerpt'],str) or not ev['excerpt'].strip() or ev['excerpt'] not in text:
            raise ValueError('Source excerpt does not match its locator')


def coordination_profile(task_id,requirements,cache=None):
    result={};excluded=[]
    for req in requirements:
        check_source_evidence(req['evidence'],cache);text=' '.join(e['excerpt'] for e in req['evidence'])
        if req['kind']=='external_response' and not (re.search(r'\b(patient|provider|guardian)\b',text,re.I) and re.search(r'\b(responds?|supplies|supplied|returned)\b',text,re.I)):
            excluded.append({'requirement':req,'reason':'Ordinary tool returns or an outbound request alone do not establish an additional human/asynchronous response.'});continue
        if req['kind']=='linked_records' and not re.search(r'\b(link|linked|linking|merge|merged|merging|sync|synchronize|synchronization)\b',text,re.I):
            excluded.append({'requirement':req,'reason':'Routine ID arguments alone do not establish explicit linking/merging/synchronization.'});continue
        event=req['id']
        if task_id=='ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1' and req['id'] in {'approval:ap','handoff:milestone_2'}:event='ap_review'
        if task_id=='InsuranceClaimsIntakeAndTriageAgent_W8_TC1':
            if req['id']=='multi_party:claim_assignment_roles':event='handoff:milestone_6'
            if req['id']=='multi_party:expert_roles':event='handoff:milestone_7'
        key=(event,req['kind'])
        if key not in result:result[key]={**req,'event_key':event,'evidence':list(req['evidence'])}
        else:
            for ev in req['evidence']:
                if ev not in result[key]['evidence']:result[key]['evidence'].append(ev)
    return list(result.values()),excluded


def build(annotations_path=ANNOTATIONS):
    source_cache={}
    previous=v2.build();stored=REPO/'results/difficulty/designed_v2/profiles.json'
    if json.loads(stored.read_text())!=previous:raise ValueError('Stored v0.2 profiles do not reproduce')
    raw=json.loads(Path(annotations_path).read_text())
    if raw.get('version')!='designed_scope_annotations_v0.3' or raw.get('source_sha256')!=previous['source_sha256'] or raw.get('v2_profiles_sha256')!=file_hash(stored):
        raise ValueError('Scope annotations have stale source/profile fingerprints')
    if raw.get('rulebook_version')!='design_counting_rules_v0.2_scope_clarified' or raw.get('rulebook_sha256')!=file_hash(RULES):
        raise ValueError('Scope annotations and counting rulebook differ')
    prior={(r['domain'],r['task_id']):r for r in previous['tasks']};keys=[(r['domain'],r['task_id']) for r in raw['tasks']]
    if len(keys)!=len(set(keys)) or set(keys)!=set(prior):raise ValueError('Scope annotations must cover all tasks exactly once')
    rows=[]
    for item in raw['tasks']:
        old=prior[(item['domain'],item['task_id'])]
        agent=yaml.safe_load((DATA_DIR/old['sources']['yaml_file']).read_text())['agent'];guides=agent['action_plan'].get('guidelines',[])
        entries=item['global_requirements'];ops=item['added_operations'];opkeys=[op['key'] for op in ops]
        if len(opkeys)!=len(set(opkeys)):raise ValueError('Duplicate global operation')
        if len({e['key'] for e in entries})!=len(entries) or {e['guideline_index'] for e in entries}!=set(range(len(guides))):raise ValueError('Every global guideline needs a unique obligation disposition')
        referenced=[];steps={m['step'] for m in old['milestones']}
        for e in entries:
            if e['disposition'] not in DISPOSITIONS or not e['rationale'].strip():raise ValueError('Invalid global requirement disposition')
            check_source_evidence(e['evidence'],source_cache);g=e['guideline_index']
            required={'source':old['sources']['yaml_file'],'locator':'#/agent/action_plan/guidelines/'+str(g),'excerpt':guides[g]}
            if required not in e['evidence']:raise ValueError('Global obligation must cite its exact guideline')
            if e['disposition']=='covered' and (not e['covered_milestone_steps'] or not set(e['covered_milestone_steps']).issubset(steps)):raise ValueError('Covered requirement needs existing milestone support')
            if (e['disposition']=='added')!=bool(e['added_operation_keys']):raise ValueError('Added operations and disposition disagree')
            referenced.extend(e['added_operation_keys'])
        if len(referenced)!=len(set(referenced)) or set(referenced)!=set(opkeys):raise ValueError('Global operations must be referenced exactly once')
        for op in ops:
            if not op['description'].strip() or type(op['business_check']) is not bool or not op['phase_basis'].strip():raise ValueError('Added operation needs a description, phase and check classification')
            check_source_evidence(op['evidence'],source_cache)
            parent=next(e for e in entries if op['key'] in e['added_operation_keys'])
            if not all(ev in op['evidence'] for ev in parent['evidence']):raise ValueError('Added operation lost its applicability evidence')
            if not any(ev['source']==old['sources']['json_file'] and ev['locator'].startswith(old['sources']['json_case_pointer']+'/') for ev in op['evidence']):raise ValueError('Global operation needs task-specific phase evidence')
        coord,excluded=coordination_profile(item['task_id'],old['coordination_evidence'],source_cache);counts=Counter(e['kind'] for e in coord)
        rows.append({**old,'status':VERSION,'v2_operation_unit_count':old['proposed_operation_unit_count'],
            'v2_business_check_groups':old['business_check_groups'],
            'proposed_operation_unit_count':old['proposed_operation_unit_count']+len(ops),
            'business_check_groups':old['business_check_groups']+sum(op['business_check'] for op in ops),
            'added_global_operation_count':len(ops),'added_global_operations':ops,
            'global_requirement_dispositions':entries,'uncertain_global_requirements':sum(e['disposition']=='uncertain' for e in entries),
            'policy_constraints_not_counted':sum(e['disposition']=='constraint_only' for e in entries),
            'coordination_evidence':coord,'excluded_coordination_candidates':excluded,
            'distinct_coordination_events':len({e['event_key'] for e in coord}),
            **{k+'_requirements':counts[k] for k in sorted(v2.KINDS)},'v3_combined_score':None,
            'flags':old['flags']+['applicable_global_rules_reviewed','uncertain_global_duties_not_imputed','coordination_categories_not_additive']})
    if any(file_hash(DATA_DIR/name)!=h for name,h in previous['source_sha256'].items()):
        raise ValueError('Supplied source changed during profile construction')
    return {'version':VERSION,'status':'provisional_profiles_not_independent_validation','task_count':len(rows),
        'domain_count':len({r['domain'] for r in rows}),'network_calls':0,'agent_runs':0,'new_llm_reviews':0,
        'rulebook_version':'design_counting_rules_v0.2_scope_clarified','rulebook_sha256':file_hash(RULES),
        'source_sha256':previous['source_sha256'],'v2_profiles_sha256':file_hash(stored),
        'annotations_sha256':file_hash(annotations_path),'implementation_sha256':file_hash(Path(__file__)),
        'combined_score':None,'tasks':rows}


def write_outputs(out,doc):
    out=Path(out).resolve();data=DATA_DIR.resolve()
    if out==data or out.is_relative_to(data) or data.is_relative_to(out):raise ValueError('Output overlaps supplied data')
    if out.exists():raise ValueError('Use a fresh output directory')
    out.mkdir(parents=True)
    (out/'profiles.json').write_text(json.dumps(doc,indent=2)+'\n')
    rows=doc['tasks'];cols=['domain','task_id','title','proposed_operation_unit_count','business_check_groups',
         'reference_tool_interactions','added_global_operation_count','uncertain_global_requirements',
         'distinct_coordination_events',*[k+'_requirements' for k in sorted(v2.KINDS)],'v1_score_reference_only']
    with (out/'profiles.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:r[k] for k in cols} for r in rows)
    cols=['domain','task_id','title','v2_operation_unit_count','proposed_operation_unit_count','added_global_operation_count',
          'v2_business_check_groups','business_check_groups','uncertain_global_requirements']
    with (out/'changes.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:r[k] for k in cols} for r in rows)
    dispositions=Counter(e['disposition'] for r in rows for e in r['global_requirement_dispositions'])
    summary={'n_tasks':len(rows),'n_domains':doc['domain_count'],
       'tasks_with_added_global_operations':sum(r['added_global_operation_count']>0 for r in rows),
       'added_operations':sum(r['added_global_operation_count'] for r in rows),
       'global_obligation_dispositions':dict(sorted(dispositions.items())),
       'tasks_with_uncertain_global_obligations':sum(r['uncertain_global_requirements']>0 for r in rows),
       'combined_score':None,'new_api_calls':0,'prior_versions_unchanged':True}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    c=next(r for r in rows if r['task_id']=='HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1')
    text=f'''# Designed complexity profiles version 0.3

## Start here

All 64 tasks have been reviewed against their global guidelines as well as their
milestones. {summary['tasks_with_added_global_operations']} tasks gain {summary['added_operations']} explicit operations/checks in total.
Original sources, v0.1 scores, v0.2 profiles and model responses are preserved.
No API calls or agent runs were made. This remains a provisional interpretation,
not a validated final score; there is no new combined number.

Open changes.csv to see before/after counts. profiles.csv gives the current
profiles. profiles.json retains exact evidence and a disposition for every global
guideline: covered, added, not applicable, conditional branch not selected,
uncertain, or constraint only. Covered rules are not counted a second time.

## The insurance update example

Operations increase from {c['v2_operation_unit_count']} to {c['proposed_operation_unit_count']}; checks increase from {c['v2_business_check_groups']} to {c['business_check_groups']}.
The added work is initial field validation, validation after the update, and
duplicate detection. Access logging stays an uncertain infrastructure/compliance
obligation, not an invented fourth agent operation. One patient response is
coordination; ordinary payer API returns are not extra response events. Passing
patient/provider IDs for normal booking does not add a linked-record obligation.

## Consistent treatment across domains

Banking and fraud prerequisites already covered by identity, screening and risk
operations are not added again. The risk tool already returns a recommended action;
its result selecting a route does not automatically create another check.
Missing explicit global work is included in two PA paths and early-payment
eligibility. Whether a global duty is relevant, already covered or ambiguous is
recorded per task. Unsupported infrastructure steps, unused branches and missing
environmental material are not converted into complexity penalties.

Explicit linking/merging/synchronization requirements are retained; routine ID
arguments alone are insufficient. External responses mean additional human or
asynchronous dependencies, not ordinary synchronous tool results. Shared event
keys avoid counting one AP review twice when tagged as approval and handoff.
Category counts overlap and must not be summed into a difficulty score.

## What remains uncertain

Some guidelines leave authority checks, human escalation or audit/logging actor
boundaries unclear. These stay visible without invented operations. Source
applicability and operation granularity remain assistant interpretations. Exact
atomic actions and independent decisions remain unknown. No new weights, cutoff
labels or independent-validation claim are introduced.

Rules: docs/evaluation/design_counting_rulebook_v0.2.md.

    python -m difficulty.designed_profiles_v3 --out results/difficulty/designed_v3_fresh
'''
    (out/'README.md').write_text(text)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=REPO/'results/difficulty/designed_v3')
    args=p.parse_args();doc=build();write_outputs(args.out,doc)
    print(f"Updated {doc['task_count']} profiles offline; prior versions unchanged.")


if __name__=='__main__':main()
