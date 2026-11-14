"""Validate authored native complexity profiles offline, without inventing missing counts."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

from .design.inputs import unique, verify_sources
from .design.rubric import digest

VERSION = 'native_semantic_profiles_v1'
KINDS = {'approval', 'handoff', 'linked_records', 'multi_party', 'external_response', 'multi_channel'}


def validate_items(items, catalog, source_map, kind):
    if not isinstance(items, list):
        raise ValueError('Profile items must be lists')
    keys = set()
    for item in items:
        key = item.get('key')
        if not isinstance(key, str) or not key.strip() or key in keys:
            raise ValueError('Missing or duplicate event/operation key')
        keys.add(key)
        if not item.get('description') or not item.get('rationale') or not item.get('evidence'):
            raise ValueError('Description, rationale and source evidence required')
        if kind == 'operation' and type(item.get('business_check')) is not bool:
            raise ValueError('Business-check flag must be boolean')
        if kind == 'coordination':
            tags = item.get('categories')
            if not isinstance(tags, list) or not tags or len(set(tags)) != len(tags) or not set(tags) <= KINDS:
                raise ValueError('Invalid coordination categories')
        for ev in item['evidence']:
            sid, excerpt = ev.get('source_id'), ev.get('excerpt')
            if sid not in catalog or sid not in source_map or not isinstance(excerpt, str) or not excerpt.strip() or excerpt not in catalog[sid]:
                raise ValueError('Evidence does not match frozen source')


def analyze(inventory, annotations, score_report):
    unique(inventory)
    verify_sources(inventory)
    native = {r['payload']['case_key']: r for r in inventory if r['dataset'] == 'tau2'}
    scores = {t['case_key']: t for t in score_report['tasks'] if t['dataset'] == 'tau2'}
    if len(scores) != sum(t['dataset'] == 'tau2' for t in score_report['tasks']):
        raise ValueError('Duplicate native score task')
    if set(scores) != set(native):
        raise ValueError('Complete native score/input coverage required')
    authored = {}
    for profile in annotations['tasks']:
        key = profile['case_key']
        if key in authored or key not in native:
            raise ValueError('Duplicate or unknown annotation case')
        row = native[key]
        if profile['input_sha256'] != row['input_sha256']:
            raise ValueError('Annotation/input fingerprint mismatch')
        catalog = {s['source_id']: s['text'] for s in row['payload']['source_catalog']}
        for name, kind in [('operations', 'operation'), ('coordination_events', 'coordination')]:
            validate_items(profile[name], catalog, row['sources'], kind)
        if not profile['operations']:
            raise ValueError('Authored profile requires documented operations')
        if profile.get('status') not in {'provisional_complete', 'unresolved_path'}:
            raise ValueError('Invalid authored profile status')
        if not profile.get('scope_rationale') or not profile.get('excluded_work') or not isinstance(profile.get('uncertainties'), list):
            raise ValueError('Scope, exclusions and uncertainty record required')
        if profile['status'] == 'unresolved_path' and not profile['uncertainties']:
            raise ValueError('Unresolved path needs an explanation')
        authored[key] = profile
    tasks = []
    for key, row in native.items():
        score = scores[key]
        if score['input_sha256'] != row['input_sha256'] or (score['domain'], score['task_id']) != (row['domain'], row['task_id']):
            raise ValueError('Score/input identity mismatch')
        p = authored.get(key)
        counts = None if not p else {'proposed_operation_unit_count': len(p['operations']),
            'business_check_groups': sum(o['business_check'] for o in p['operations']),
            'distinct_coordination_events': len(p['coordination_events'])}
        complete = bool(p and p['status'] == 'provisional_complete')
        tasks.append({'case_key': key, 'domain': row['domain'], 'task_id': row['task_id'],
            'input_sha256': row['input_sha256'], 'score': score['score'],
            'status': p['status'] if p else 'not_authored',
            'features': counts if complete else {k: None for k in ('proposed_operation_unit_count', 'business_check_groups', 'distinct_coordination_events')},
            'documented_partial_counts': counts if p and not complete else None,
            'annotation': p,
            'source_bindings': row['sources'] if p else None})
    return {'version': VERSION, 'api_calls': 0, 'agent_runs': 0, 'scores_changed': False,
        'independent_validation': False, 'annotation_sha256': digest(annotations),
        'score_report_sha256': digest(score_report), 'coverage': dict(Counter(t['status'] for t in tasks)),
        'task_count': len(tasks), 'tasks': tasks,
        'correlations': None, 'correlation_reason': 'Small selected development sample; no representative association claim.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('inventory', 'annotations', 'scores', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    text = gzip.decompress(a.inventory.read_bytes()).decode() if a.inventory.suffix == '.gz' else a.inventory.read_text()
    result = analyze(json.loads(text), json.loads(a.annotations.read_text()), json.loads(a.scores.read_text()))
    from .design.judge import safe_output, write_json
    out = safe_output(a.out)
    if out.exists():
        raise ValueError('Use a fresh output file')
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, result)
    print(json.dumps({'coverage': result['coverage'], 'task_count': result['task_count'], 'api_calls': 0}))


if __name__ == '__main__':
    main()
