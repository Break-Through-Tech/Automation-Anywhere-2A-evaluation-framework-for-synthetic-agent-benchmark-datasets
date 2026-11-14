import csv,json,math,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from statistics import fmean
root=Path('results/scoring/weekend_weight_trials_v1/inputs')
out=Path('results/scoring/mila_weight_review_v1')
read=lambda p:list(csv.DictReader(p.open()))
labels=read(root/'workflow_labels.csv');catalog=read(root/'workflow_catalog.csv')
published=read(root/'workflow_coverage_scores.csv')
tasks=json.loads(Path('results/difficulty/designed_final_v27/task_scores.json').read_text())['tasks']
label_ids={(r['dataset'],r['agent_category'],r['task_id'].removeprefix(r['agent_category']+':') if r['dataset']=='tau2' else r['task_id']) for r in labels}
task_ids={(t['dataset'],t['domain'],t['task_id']) for t in tasks}
assert len(label_ids)==len(labels)==len(task_ids)==len(tasks)==342 and label_ids==task_ids
cats=defaultdict(set); counts=defaultdict(Counter)
for r in catalog:cats[r['dataset'],r['agent_category']].add(r['workflow_key'])
for r in labels:counts[r['dataset'],r['agent_category']].update(set(r['workflow_keys'].split('|')))
groups={}
for key,ks in cats.items():
    freq=counts[key];assert set(freq)<=ks
    n=sum(freq.values());h=-math.fsum((v/n)*math.log(v/n) for v in freq.values())/math.log(len(ks))
    row=next(r for r in published if (r['dataset'],r['group'])==key and r['attribute']=='workflow')
    assert math.isclose(len(freq)/len(ks),float(row['catalog_coverage']),abs_tol=0.00005)
    assert math.isclose(h,float(row['normalized_entropy']),abs_tol=0.00005)
    groups[key]=(len(freq),len(ks),h)
cli={r['dataset']:r for r in json.loads((out/'trials.json').read_text())['rows']}
rows=[]
for ds in ('tau2','synthetic'):
    gs=[v for k,v in groups.items() if k[0]==ds]
    a=sum(g[0] for g in gs)/sum(g[1] for g in gs);e=fmean(g[2] for g in gs)
    c=(a+e)/2;d=fmean(t['score'] for t in tasks if t['dataset']==ds)/100
    cp=30*c;dp=70*d;q=cp+dp;base=50*c+50*d
    assert math.isclose(q,cli[ds]['combined_index_0_100'],abs_tol=1e-12)
    assert math.isclose(cp,cli[ds]['coverage_contribution_0_100'],abs_tol=1e-12)
    assert math.isclose(dp,cli[ds]['difficulty_contribution_0_100'],abs_tol=1e-12)
    assert min(100*c,100*d)<=q<=max(100*c,100*d)
    rows.append(dict(dataset=ds,coverage_0_100=100*c,difficulty_0_100=100*d,coverage_contribution=cp,difficulty_contribution=dp,index_30_70=q,index_50_50=base,change_from_50_50=q-base))
gap=rows[0]['index_30_70']-rows[1]['index_30_70'];oldgap=rows[0]['index_50_50']-rows[1]['index_50_50']
assert rows[0]['coverage_0_100']>rows[1]['coverage_0_100'] and rows[0]['difficulty_0_100']>rows[1]['difficulty_0_100']
with (out/'comparison.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
verification=dict(status='passed',review_type='assistant_completed_on_Mila_request_not_independent_human_validation',api_calls=0,matched_task_ids=342,coverage_groups_checked=10,independent_math='Recomputed directly from CSV labels/catalog and saved task scores without importing shared calculator.',contributions_and_bounds='passed',gap_30_70=gap,gap_50_50=oldgap,gap_change=gap-oldgap,ordering='tau2 > synthetic for every convex Coverage/Difficulty weighting, because both components are greater',final_weights_selected=False,rows=rows)
(out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(verification,indent=2))
