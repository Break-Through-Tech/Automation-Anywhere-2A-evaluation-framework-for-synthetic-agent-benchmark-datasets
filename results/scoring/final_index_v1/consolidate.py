"""Offline consolidation of five documented reviews; no model calls."""
import csv,io,json,math
from pathlib import Path
p=Path(__file__).parent
trials=json.loads((p/'trials.json').read_text())['rows'];sources=json.loads((p/'review_sources.json').read_text())
for name in ('zayd','ronnit','divya'):
    observed=list(csv.DictReader(io.StringIO(sources[name]['csv']['content'])))
    for r in observed:
        expected=next(t for t in trials if t['trial']==name and t['dataset']==r['dataset'])
        for key in ('coverage_weight','difficulty_weight','coverage','difficulty_normalized','coverage_contribution_0_100','difficulty_contribution_0_100','combined_index_0_100'):
            assert math.isclose(float(r[key]),expected[key],abs_tol=1e-12), (name,key)
for r in trials:assert math.isclose(r['combined_index_0_100'],r['coverage_contribution_0_100']+r['difficulty_contribution_0_100'],abs_tol=1e-12)
assert '73.43' in sources['sana'][0]['body'] and '76.57' in sources['sana'][0]['body']
assert '73.46' in sources['mila'][0]['body'] and '71.01' in sources['mila'][0]['body']
selected=[dict(r,trial='selected_50_50') for r in trials if r['coverage_weight']==.5]
(p/'scores.json').write_text(json.dumps({'version':'relative_coverage_challenge_index_v1','status':'selected_project_reporting_convention_not_advisor_approved','coverage_weight':.5,'difficulty_weight':.5,'coverage_internal_weights':{'catalog_completeness':.5,'mean_group_entropy':.5},'difficulty_internal_weights':.2,'formula':'100 * (0.5 C + 0.5 D)','independent_validity_established':False,'api_calls':0,'rows':selected},indent=2)+'\n')
with (p/'scores.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
(p/'verification.json').write_text(json.dumps({'status':'passed','review_count':5,'csvs_checked_against_recalculation':['zayd','ronnit','divya'],'comment_scores_checked_at_display_precision':['sana','mila'],'sana_raw_trial_csv_supplied':False,'all_contribution_sums_match':True,'api_calls':0,'zayd_pr':83,'zayd_pr_merged':False,'weights_selected_by':'Mila delegated operational choice to assistant; this is not reviewer consensus or Sandra approval'},indent=2)+'\n')
print('All five reviews consolidated; exact CSV checks passed; selected 50/50 scores saved.')
