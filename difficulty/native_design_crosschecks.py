"""Offline shared reference diagnostics; no model calls or score changes."""
import argparse
import ast
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

from .design.crosscheck import association
from .design.inputs import verify_sources, unique
from .design.rubric import digest, ROOT

VERSION = 'reference_design_crosschecks_v1'
RULES = ROOT / 'docs/evaluation/native_design_crosschecks_v1.md'
TERMINALS = {'SUCCESS', 'FAILED', 'CANCELLED', 'HUMAN_IN_THE_LOOP'}
FEATURES = ('reference_tool_interactions', 'distinct_reference_tool_names',
            'repeated_reference_calls', 'reference_argument_leaves')
SEMANTIC = ('proposed_operation_unit_count', 'business_check_groups',
            'distinct_coordination_events')


def leaves(value):
    if isinstance(value, dict):
        return sum(leaves(v) for v in value.values())
    if isinstance(value, list):
        return sum(leaves(v) for v in value)
    return 1


def reference_list(text):
    """Read JSON or Python list syntax without importing/executing source code."""
    try:
        return json.loads(text), 'json'
    except ValueError:
        node = ast.parse(text, mode='eval').body
    if not isinstance(node, ast.List):
        raise ValueError('Python reference expression is not a list')
    values = []
    for entry in node.elts:
        if not isinstance(entry, ast.Dict):
            raise ValueError('Python reference entry is not a dictionary')
        fields = {ast.literal_eval(k): v for k, v in zip(entry.keys, entry.values)}
        name = ast.literal_eval(fields['name'])
        if 'tool_inputs' not in fields:
            raise ValueError('Missing reference arguments')
        try:
            arguments = ast.literal_eval(fields['tool_inputs'])
            unresolved = False
        except (ValueError, TypeError):
            arguments, unresolved = None, True
        values.append({'name': name, 'tool_inputs': arguments,
                       '_unresolved_arguments': unresolved})
    return values, 'static_python_expression'


def reference_features(row):
    catalog = {s['source_id']: s for s in row['payload']['source_catalog']}
    if row['dataset'] == 'synthetic':
        sid = 'reference_calls'
        values, representation = reference_list(catalog[sid]['text'])
        arguments_key = 'tool_inputs'
        missing = False
        suffix = ''
    elif row['dataset'] == 'tau2':
        sid = 'completion_design'
        endpoint = json.loads(catalog[sid]['text'])
        values = endpoint.get('actions') or []
        representation = 'json'
        arguments_key = 'arguments'
        missing = not any(endpoint.values())
        suffix = '/actions'
        unit_values = [json.loads(s['text']) for s in row['payload']['source_catalog']
                       if s['source_id'].startswith('reference_')]
        if unit_values != values:
            raise ValueError('Reference unit list differs from original completion design')
    else:
        raise ValueError('Unsupported dataset')
    if not isinstance(values, list):
        raise ValueError('Reference design must be a list')
    source = row['sources'][sid]
    calls, excluded, evidence = [], [], []
    for index, call in enumerate(values):
        if not isinstance(call, dict) or not isinstance(call.get('name'), str) or not call['name']:
            raise ValueError('Malformed reference call')
        citation = {**source, 'locator': source['locator'] + suffix + '/' + str(index)}
        if call['name'] in TERMINALS:
            excluded.append({'name': call['name'], 'reason': 'terminal_signal', 'source': citation})
        else:
            if not call.get('_unresolved_arguments') and (arguments_key not in call or not isinstance(call[arguments_key], dict)):
                raise ValueError('Missing or malformed reference arguments')
            calls.append(call)
            evidence.append({'name': call['name'], 'source': citation})
    names = Counter(c['name'] for c in calls)
    features = dict(zip(FEATURES, (len(calls), len(names), len(calls)-len(names),
                                  None if any(c.get('_unresolved_arguments') for c in calls) else sum(leaves(c[arguments_key]) for c in calls))))
    if missing:
        features = {k: None for k in FEATURES}
    return {'features': features, 'reference_status': 'unavailable' if missing else 'documented_list',
            'missing_reason': 'No explicit reference actions or completion references' if missing else None,
            'reference_representation': representation,
            'argument_feature_missing_reason': 'Unresolved Python argument expression; no source code executed' if any(c.get('_unresolved_arguments') for c in calls) else None,
            'reference_source': {**source, 'locator': source['locator'] + suffix},
            'counted_calls': evidence, 'excluded_terminal_signals': excluded}


def analyze(score_report, inventory):
    unique(inventory)
    verify_sources(inventory)
    bykey = {r['payload']['case_key']: r for r in inventory}
    if len(score_report['tasks']) != len(inventory):
        raise ValueError('Complete score/inventory coverage required')
    tasks, seen = [], set()
    for score in score_report['tasks']:
        key = score['case_key']
        if key in seen or key not in bykey:
            raise ValueError('Duplicate or unknown score task')
        seen.add(key)
        row = bykey[key]
        if (score['input_sha256'] != row['input_sha256'] or
            (score['dataset'], score['domain'], score['task_id']) !=
                (row['dataset'], row['domain'], row['task_id'])):
            raise ValueError('Score/input identity mismatch')
        tasks.append({k: score[k] for k in ('dataset', 'domain', 'task_id', 'case_key',
                     'input_sha256', 'status', 'score')} | reference_features(row))
    groups = defaultdict(list)
    for task in tasks:
        groups[task['dataset']].append(task)
        groups[task['dataset']+'/'+task['domain']].append(task)
    summaries = {}
    examples = []
    for name, values in sorted(groups.items()):
        summaries[name] = {'n_total': len(values), 'n_scored': sum(v['status']=='scored' for v in values),
            'n_missing_reference': sum(v['reference_status']=='unavailable' for v in values),
            'associations': {k: association([(v['features'][k], v['score']) for v in values
                if v['status']=='scored' and v['features'][k] is not None]) for k in FEATURES}}
        if '/' not in name:
            continue
        same_count = defaultdict(list)
        for v in values:
            n = v['features']['reference_tool_interactions']
            if n is not None and v['status']=='scored':
                same_count[n].append(v)
        candidates = []
        for n, cohort in same_count.items():
            low = min(cohort, key=lambda v: (v['score'], v['task_id']))
            high = max(cohort, key=lambda v: (v['score'], v['task_id']))
            if high['score'] > low['score']:
                candidates.append({'domain': name, 'reference_calls': n,
                    'score_gap': high['score']-low['score'], 'low': low, 'high': high})
        if candidates:
            examples.append(max(candidates, key=lambda x:(x['score_gap'], -x['reference_calls'])))
    return {'version': VERSION, 'rules_sha256': digest(RULES.read_text()),
            'score_report_sha256': digest(score_report), 'inventory_sha256': digest(inventory),
            'api_calls': 0, 'scores_changed': False, 'groups': summaries, 'tasks': tasks,
            'same_reference_count_examples': examples,
            'selection_note': 'Post-hoc illustrative maximum score-gap pair per domain within equal reference count; not held-out validation.',
            'native_semantic_features': {k: {'status':'unavailable',
                'reason':'Requires source-bound native semantic annotations; not inferred from call counts'} for k in SEMANTIC},
            'native_tags': {'status':'unavailable', 'reason':'No comparable supplied task difficulty tags'},
            'independent_validation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scores', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    from .design.judge import safe_output, write_json
    out = safe_output(args.out)
    if out.exists():
        raise ValueError('Use a fresh output directory')
    result = analyze(json.loads(args.scores.read_text()), json.loads(args.inventory.read_text()))
    out.mkdir(parents=True)
    write_json(out/'crosschecks.json', result)
    with (out/'task_features.csv').open('w', newline='') as handle:
        fields = ['dataset','domain','task_id','score','reference_status',*FEATURES]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({**{k:v[k] for k in fields[:5]}, **v['features']} for v in result['tasks'])
    lines = ['# Shared reference-design cross-checks', '',
        'All 342 saved task scores are unchanged. Zero API calls. These exact source observables are supporting diagnostics, not the difficulty formula.', '',
        '## Native findings', '']
    for name in ['tau2','tau2/airline','tau2/retail','tau2/telecom','synthetic']:
        g=result['groups'][name]; a=g['associations']['reference_tool_interactions']
        rho='undefined' if a['rho'] is None else f"{a['rho']:.3f}"
        lines.append(f"- **{name}**: reference-call/score Spearman rho {rho}, paired n={a['n']}; missing references {g['n_missing_reference']}/{g['n_total']}.")
    lines += ['', 'Reference lists vary in completeness; zero listed calls does not mean no work. Native retail 57 remains unavailable for these reference features. Repeated calls, distinct tool names and argument leaves are separately reported, with sample sizes and ties.', '',
        'See the [frozen definitions](../../../docs/evaluation/native_design_crosschecks_v1.md). P-values are exploratory, task variants are clustered, and shared evidence prevents independent-validation claims.', '',
        '## Remaining scope', '',
        '#50 and parent #71 remain open. Native operations, business checks and coordination need source-bound semantic annotations under the existing counting rules. Tool counts, actor counts and environment assertions are not substitutes. Native difficulty tags remain unavailable. The original synthetic profiles and tag comparisons remain separate and unchanged.', '',
        'Equal-count example pairs in crosschecks.json were selected after scoring for illustration, not as independent validation. Their source-backed explanations are supplied in examples.md.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result['groups'],indent=2))


if __name__ == '__main__':
    main()
