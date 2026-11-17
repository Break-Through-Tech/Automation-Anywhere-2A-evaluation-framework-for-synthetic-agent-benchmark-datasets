"""Offline sensitivity trials for a relative coverage-and-challenge index."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

VERSION = 'relative_coverage_challenge_trials_v1'
TRIALS = [('zayd',.7),('ronnit',.6),('divya',.5),('sana',.4),('mila',.3)]


def finite(value, low, high):
    if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError('Nonfinite or out-of-range score')
    return value


def normalize_id(row):
    task_id=row['task_id']
    if row['dataset']=='tau2':
        prefix=row['agent_category']+':'
        if not task_id.startswith(prefix):raise ValueError('Native coverage task ID lacks domain prefix')
        task_id=task_id[len(prefix):]
    return row['dataset'],row['agent_category'],task_id


def prepare_inputs(labels, catalog, difficulty):
    if difficulty.get('release_protocol')!='designed_difficulty_v1.1_required_path':
        raise ValueError('Use the finalized clarified difficulty release')
    covered={normalize_id(row) for row in labels}
    scored={(t['dataset'],t['domain'],t['task_id']) for t in difficulty['tasks']}
    if len(covered)!=len(labels) or len(scored)!=len(difficulty['tasks']) or covered!=scored:
        raise ValueError('Duplicate or mismatched coverage/difficulty task inventory')
    if any(t['status']!='scored' for t in difficulty['tasks']):raise ValueError('Incomplete difficulty input')
    categories=defaultdict(set)
    for row in catalog:
        key=(row['dataset'],row['agent_category']);wf=row['workflow_key']
        if wf in categories[key]:raise ValueError('Duplicate catalog workflow')
        categories[key].add(wf)
    groups=defaultdict(list)
    for row in labels:groups[row['dataset'],row['agent_category']].append(row)
    if set(categories)!=set(groups):raise ValueError('Catalog/group mismatch')
    summaries=[]
    for key,rows in sorted(groups.items()):
        counts=Counter()
        for row in rows:
            labels_for_task=set(filter(None,row['workflow_keys'].split('|')))
            if not labels_for_task or not labels_for_task<=categories[key]:raise ValueError('Missing or unknown workflow label')
            counts.update(labels_for_task)
        k=len(categories[key]);n=sum(counts.values())
        if k<2 or n==0:raise ValueError('Undefined group entropy; do not impute a zero')
        entropy=-sum((v/n)*math.log(v/n) for v in counts.values())/math.log(k)
        summaries.append({'dataset':key[0],'group':key[1],'tasks':len(rows),
            'declared':k,'represented':len(counts),'catalog_coverage':len(counts)/k,
            'entropy':entropy,'singleton_workflows':sum(v==1 for v in counts.values())})
    result={}
    for dataset in sorted({key[0] for key in groups}):
        gs=[r for r in summaries if r['dataset']==dataset]
        tasks=[t for t in difficulty['tasks'] if t['dataset']==dataset]
        d=mean(finite(t['score'],0,100) for t in tasks)/100
        represented=sum(g['represented'] for g in gs);declared=sum(g['declared'] for g in gs)
        catalog_score=represented/declared;entropy=mean(g['entropy'] for g in gs)
        result[dataset]={'n_tasks':len(tasks),'n_groups':len(gs),'represented':represented,'declared':declared,
            'catalog_coverage':catalog_score,'mean_group_entropy':entropy,'coverage':.5*catalog_score+.5*entropy,
            'difficulty_normalized':d,'difficulty_0_100':100*d,'singleton_workflows':sum(g['singleton_workflows'] for g in gs)}
    return {'version':VERSION,'datasets':result,'groups':summaries,
        'interpretation':'Exploratory within-declared-scope coverage-and-challenge index; not validated universal dataset quality.',
        'coverage_rule':'C = 0.5 * (sum represented workflows / sum declared workflows) + 0.5 * unweighted mean group entropy',
        'difficulty_rule':'D = equal-task mean finalized difficulty / 100; original repeat means already applied',
        'telecom_conditions':'Separate diagnostic; not double-counted as another group',
        'vendi':'Separate diagnostic; not blended into the primary index',
        'source_catalogs_comparable':False,'higher_difficulty':'Positive for this challenge-oriented design convention; not a quality theorem',
        'api_calls':0}


def trial(inputs, coverage_weight):
    w=finite(coverage_weight,0,1)
    return [{'dataset':ds,'coverage_weight':w,'difficulty_weight':1-w,
        'coverage':v['coverage'],'difficulty_normalized':v['difficulty_normalized'],
        'coverage_contribution_0_100':100*w*v['coverage'],
        'difficulty_contribution_0_100':100*(1-w)*v['difficulty_normalized'],
        'combined_index_0_100':100*(w*v['coverage']+(1-w)*v['difficulty_normalized'])}
        for ds,v in inputs['datasets'].items()]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('labels','catalog','difficulty','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--coverage-weight',type=float)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Choose a fresh output directory')
    inputs=prepare_inputs(list(csv.DictReader(a.labels.open())),list(csv.DictReader(a.catalog.open())),json.loads(a.difficulty.read_text()))
    weights=TRIALS if a.coverage_weight is None else [('selected',a.coverage_weight)]
    rows=[{'trial':name,**r} for name,w in weights for r in trial(inputs,w)]
    a.out.mkdir(parents=True)
    (a.out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    (a.out/'trials.json').write_text(json.dumps({'status':'exploratory_candidates_not_final_selected_weights','rows':rows},indent=2)+'\n')
    with (a.out/'trials.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (a.out/'provenance.json').write_text(json.dumps({'api_calls':0,'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (a.labels,a.catalog,a.difficulty)},'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    print(json.dumps({'status':'exploratory_trials_only','datasets':inputs['datasets'],'trial_count':len(weights),'api_calls':0},indent=2))


if __name__=='__main__':main()
