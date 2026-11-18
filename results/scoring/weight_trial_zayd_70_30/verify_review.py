"""Independent check of the 70/30 trial (#78); does not import the shared calculator.

Run from the repository root: python results/scoring/weight_trial_zayd_70_30/verify_review.py
"""
import csv, io, json, math, subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).parent
SNAP = Path('results/scoring/weekend_weight_trials_v1')
W, TOL = 0.70, 1e-12
rows = lambda p: list(csv.DictReader(open(p, newline='')))
labels, catalog = rows(SNAP / 'inputs/workflow_labels.csv'), rows(SNAP / 'inputs/workflow_catalog.csv')
diff = json.load(open('results/difficulty/designed_final_v27/task_scores.json'))

# Snapshots must match main's coverage sources by parsed content (bytes may differ in trailing lines).
for snap, src in [('workflow_labels.csv', 'coverage/labels/workflows/workflow_labels.csv'),
                  ('workflow_catalog.csv', 'coverage/labels/workflows/workflow_catalog.csv'),
                  ('workflow_coverage_scores.csv', 'results/coverage/workflow/workflow_coverage_scores.csv')]:
    main = subprocess.run(['git', 'show', f'origin/main:{src}'], capture_output=True, text=True, check=True).stdout
    assert list(csv.DictReader(io.StringIO(main))) == rows(SNAP / 'inputs' / snap), snap

# Coverage: A pooled represented/declared, E unweighted mean normalized entropy per group.
declared = defaultdict(set)
for r in catalog: declared[r['dataset'], r['agent_category']].add(r['workflow_key'])
counts = defaultdict(Counter)
for r in labels: counts[r['dataset'], r['agent_category']].update(filter(None, r['workflow_keys'].split('|')))
published = {(r['dataset'], r['group']): r for r in rows(SNAP / 'inputs/workflow_coverage_scores.csv') if r['attribute'] == 'workflow'}
assert set(published) == set(declared) == set(counts)
groups = {}
for key, c in counts.items():
    assert set(c) <= declared[key]
    n, k = sum(c.values()), len(declared[key])
    groups[key] = (len(c), k, -sum(v / n * math.log(v / n) for v in c.values()) / math.log(k))
    assert round(len(c) / k, 4) == float(published[key]['catalog_coverage']), key
    assert abs(groups[key][2] - float(published[key]['normalized_entropy'])) <= 5e-5, key

# Difficulty: FINAL v1.1, all tasks scored, task IDs identical to coverage inventory.
assert diff['release_protocol'] == 'designed_difficulty_v1.1_required_path'
assert all(t['status'] == 'scored' for t in diff['tasks'])
# Five internal dimensions at 20% each: score = 5 x sum of the five 0-4 ratings.
assert all(len(t['dimensions']) == 5 and abs(t['score'] - 5 * sum(t['dimensions'].values())) < TOL for t in diff['tasks'])
strip = lambda r: r['task_id'][len(r['agent_category']) + 1:] if r['dataset'] == 'tau2' else r['task_id']
assert sorted((r['dataset'], strip(r)) for r in labels) == sorted((t['dataset'], t['task_id']) for t in diff['tasks'])
assert len(labels) == 342

ours = {r['dataset']: r for r in rows(HERE / 'trials.csv')}
cand = {r['dataset']: r for r in rows(SNAP / 'trials.csv')}
out = {}
for ds in ('tau2', 'synthetic'):
    g = [v for k, v in groups.items() if k[0] == ds]
    A = sum(x[0] for x in g) / sum(x[1] for x in g)
    E = mean(x[2] for x in g)
    C = 0.5 * A + 0.5 * E
    raw = mean(t['score'] for t in diff['tasks'] if t['dataset'] == ds)
    assert raw == diff['datasets'][ds]['mean'] == {'tau2': 64.15467625899281, 'synthetic': 63.75}[ds]  # not old 65.35/64.30
    D = raw / 100
    q = lambda w: 100 * (w * C + (1 - w) * D)
    r = ours[ds]
    cc, dc, tot = (float(r[f]) for f in ('coverage_contribution_0_100', 'difficulty_contribution_0_100', 'combined_index_0_100'))
    assert abs(cc - 100 * W * C) < TOL and abs(dc - 100 * (1 - W) * D) < TOL and abs(tot - q(W)) < TOL
    assert abs(tot - (cc + dc)) < TOL  # score = Coverage contribution + Difficulty contribution
    assert min(C, D) * 100 <= tot <= max(C, D) * 100
    for c in ('zayd', 'divya'):  # prepared 70/30 candidate and 50/50 baseline
        row = next(x for x in rows(SNAP / 'trials.csv') if x['trial'] == c and x['dataset'] == ds)
        assert abs(float(row['combined_index_0_100']) - q(float(row['coverage_weight']))) < TOL
    out[ds] = {'A': A, 'E': E, 'C': C, 'D': D, 'q_70_30': q(W), 'q_50_50': q(0.5), 'change': q(W) - q(0.5)}

gap = lambda k: out['tau2'][k] - out['synthetic'][k]
out['gap'] = {'50_50': gap('q_50_50'), '70_30': gap('q_70_30'), 'change': gap('q_70_30') - gap('q_50_50'),
              'ordering_changed': (gap('q_50_50') > 0) != (gap('q_70_30') > 0)}
print(json.dumps(out, indent=2))
