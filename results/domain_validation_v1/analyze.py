"""Issue #66: offline descriptive checks of Ronnit's domain profiles."""
import csv,json,math,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean,median
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
read=lambda p:list(csv.DictReader(Path(p).open()))
inputs=ROOT/'results/scoring/weekend_weight_trials_v1/inputs'
labels=read(inputs/'workflow_labels.csv');catalog=read(inputs/'workflow_catalog.csv')
scores=json.loads((ROOT/'results/difficulty/designed_final_v27/task_scores.json').read_text())['tasks']
upstream=read(OUT/'issue65_snapshot/domain_profiles.csv')
keys=lambda r:(r['dataset'],r['agent_category'],r['task_id'].removeprefix(r['agent_category']+':') if r['dataset']=='tau2' else r['task_id'])
assert {keys(r) for r in labels}=={(t['dataset'],t['domain'],t['task_id']) for t in scores} and len(labels)==len(scores)==342
cats=defaultdict(set);rows=defaultdict(list);groups={};workflow_rows=[]
for r in catalog:cats[r['dataset'],r['agent_category']].add(r['workflow_key'])
for r in labels:rows[r['dataset'],r['agent_category']].append(r)
for key,ls in sorted(rows.items()):
    freq=Counter(w for r in ls for w in set(r['workflow_keys'].split('|')));assert set(freq)<=cats[key]
    total=sum(freq.values());ent=-sum(v/total*math.log(v/total) for v in freq.values())/math.log(len(cats[key]))
    a=len(freq)/len(cats[key]);c=(a+ent)/2;ts=[t for t in scores if (t['dataset'],t['domain'])==key];d=mean(t['score'] for t in ts)
    expected=next(r for r in upstream if (r['dataset'],r['domain'])==key)
    for name,value in [('workflow_completeness',a),('workflow_entropy',ent),('coverage',c),('difficulty_mean',d),('composite_50_50',50*c+.5*d)]:assert math.isclose(float(expected[name]),value,abs_tol=1e-10),(key,name)
    assert int(expected['n_tasks'])==len(ts)==len(ls)
    groups['/'.join(key)]={'n':len(ts),'workflow_memberships':total,'tasks_with_multiple_workflows':sum(len(set(t['workflow_keys'].split('|')))>1 for t in ls),'completeness':a,'entropy':ent,'coverage':c,'difficulty':d,'composite':50*c+.5*d,'dimension_means':{k:mean(t['dimensions'][k] for t in ts) for k in ts[0]['dimensions']},'min':min(t['score'] for t in ts),'max':max(t['score'] for t in ts),'median':median(t['score'] for t in ts)}
    for w in sorted(cats[key]):
        selected={keys(r) for r in ls if w in r['workflow_keys'].split('|')};st=[t['score'] for t in ts if (t['dataset'],t['domain'],t['task_id']) in selected]
        workflow_rows.append({'dataset':key[0],'domain':key[1],'workflow':w,'tasks':len(st),'difficulty_mean':mean(st) if st else None})
a=groups['tau2/airline'];r=groups['tau2/retail'];delta_d=r['difficulty']-a['difficulty'];delta_c=100*(r['coverage']-a['coverage'])
weights=[{'coverage_weight':w,'airline':100*w*a['coverage']+(1-w)*a['difficulty'],'retail':100*w*r['coverage']+(1-w)*r['difficulty'],'retail_minus_airline':w*delta_c+(1-w)*delta_d} for w in (.3,.4,.5,.6,.7)]
tau=[t for t in scores if t['dataset']=='tau2'];air=[t['score'] for t in tau if t['domain']=='airline'];ret=[t['score'] for t in tau if t['domain']=='retail']
loo=[mean(ret)-mean([v for j,v in enumerate(air) if i!=j]) for i in range(len(air))]+[mean([v for j,v in enumerate(ret) if i!=j])-mean(air) for i in range(len(ret))]
paired=sum((x>y)+.5*(x==y) for x in ret for y in air)/(len(ret)*len(air))
contrib=[{'dimension':k,'retail_minus_airline_level':r['dimension_means'][k]-a['dimension_means'][k],'difficulty_point_difference':5*(r['dimension_means'][k]-a['dimension_means'][k])} for k in a['dimension_means']]
assert math.isclose(sum(v['difficulty_point_difference'] for v in contrib),delta_d,abs_tol=1e-12)
assert min(loo)>0
full=json.loads((ROOT/'results/scoring/final_index_v1/scores.json').read_text())['rows']
aggregations={}
for ds in ('tau2','synthetic'):
    ts=[t for t in scores if t['dataset']==ds];gs=[g for k,g in groups.items() if k.startswith(ds+'/')]
    weighted_d=sum(g['n']*g['difficulty'] for g in gs)/len(ts);assert math.isclose(weighted_d,mean(t['score'] for t in ts),abs_tol=1e-12)
    aggregations[ds]={'equal_task_difficulty':weighted_d,'task_weighted_domain_composites':sum(g['n']*g['composite'] for g in gs)/len(ts),'published_dataset_composite':next(v['combined_index_0_100'] for v in full if v['dataset']==ds),'note':'Domain composite averages are not the dataset formula: dataset entropy averages groups, and completeness pools workflow counts.'}
policies={}
for d in ('airline','retail'):
    p=ROOT/f'tau2-bench/data/tau2/domains/{d}/policy.md';lines=p.read_text().splitlines();ix=[139,143,147,149] if d=='airline' else [12,16,130,132,134,136]
    ix += [i for i,line in enumerate(lines,1) if 'only be called once per order' in line]
    policies[d]={'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'excerpts':[{'line':i,'text':lines[i-1]} for i in ix if i<=len(lines)]}
evidence=json.loads((ROOT/'results/difficulty/designed_final_v27/audit/judgment_evidence.json').read_text());examples=[]
for d in ('airline','retail'):
    t=next(t for t in scores if t['dataset']=='tau2' and t['domain']==d and t['task_id']=='0');es=[e for e in evidence if e['dataset']=='tau2' and e['domain']==d and e['task_id']=='0']
    examples.append({'domain':d,'task_id':'0','score':t['score'],'dimensions':t['dimensions'],'n_judgments':len(es),'repeat_range':t['repeat_score_range'],'case_key':t['case_key'],'rationale':es[0]['result']['judgment']['score_rationale'],'endpoint':es[0]['result']['judgment']['intended_endpoint'],'interpretation':'Illustrative post-scoring examples, not an independent validation sample.'})
summary={'status':'descriptive_consistency_check_completed_not_independent_validity','api_calls':0,'matched_tasks':342,'checked_upstream_domains':10,'groups':groups,'retail_minus_airline':{'difficulty_points':delta_d,'coverage_points':delta_c,'composite_points_at_50_50':.5*(delta_c+delta_d),'equalizing_coverage_weight':delta_d/(delta_d-delta_c),'dimension_contributions':contrib,'leave_one_task_out_difficulty_gap_range':[min(loo),max(loo)],'pairwise_retail_higher_with_half_ties':paired,'pairwise_count':len(ret)*len(air),'airline_single_5_point_rating_counterfactual_composite':a['composite']+2.5/len(air),'counterfactual_modifies_saved_scores':False},'weight_sensitivity':weights,'aggregations':aggregations,'limitations':['Shared sources and same judge; no independent gold difficulty or causal effect.','Task variants/workflows are dependent; no task-level IID p-values or confidence intervals claimed.','Task counts 50/114/114 and distinct own-catalog definitions.','Most tasks have one judgment; domain uncertainty is not estimated by the few development repeats.','Higher designed difficulty and higher composite are not proven higher benchmark quality.']}
for name,doc in [('findings.json',summary),('examples.json',examples),('policy_evidence.json',policies)]: (OUT/name).write_text(json.dumps(doc,indent=2)+'\n')
for name,data in [('weight_sensitivity.csv',weights),('workflow_profiles.csv',workflow_rows),('dimension_contributions.csv',contrib)]:
    with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
files=[inputs/'workflow_labels.csv',inputs/'workflow_catalog.csv',ROOT/'results/difficulty/designed_final_v27/task_scores.json',ROOT/'results/difficulty/designed_final_v27/audit/judgment_evidence.json',OUT/'issue65_snapshot/domain_profiles.csv']
upstream_provenance=json.loads((OUT/'issue65_snapshot/provenance.json').read_text())
for path,h in upstream_provenance['inputs'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
(OUT/'verification.json').write_text(json.dumps({'status':'passed','upstream_profile_groups_checked':10,'upstream_input_hashes_checked':len(upstream_provenance['inputs']),'exact_task_identity_join':342,'dimension_gap_decomposition':'exact','weighted_domain_difficulty_reconstructs_dataset_means':True,'api_calls':0,'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['retail_minus_airline','aggregations']},indent=2))
