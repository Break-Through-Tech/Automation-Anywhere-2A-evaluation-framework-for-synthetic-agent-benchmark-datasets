"""Freeze/check a staged paired development study offline; no API runner or credentials."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import shutil

from .design.inputs import unique, verify_sources
from .design.judge import load_packet, read_result, safe_output, write_json
from .design.rubric import ROOT, digest
from .required_path_probe import prompt_addendum

VERSION = 'required_path_calibration_v1_prepared_only'
PLAN = ROOT / 'docs/evaluation/required_path_calibration_plan_v1.md'
THRESHOLDS = {'max_repeat_range':10,'max_mean_repeat_range':5,
              'min_authored_complexity_gap':10,'non_target_mean_shift_review_threshold':10}


def clarified(api):
    api = deepcopy(api)
    api['input'][0]['content'] += '\n\nREQUIRED-PATH CLARIFICATION (DEVELOPMENT PROBE)\n' + prompt_addendum()
    return api


def source_record(item):
    manifest, rows, requests = load_packet(item['packet'])
    request = next(q for q in requests if q['request_id'] == item['request_id'])
    row = next(r for r in rows if r['payload']['case_key'] == request['case_key'])
    result = read_result(item['packet'], request, row)
    if not result or result['status'] != 'validated' or result['judgment']['status'] != 'scored':
        raise ValueError('A cached original judgment must be validated and scored')
    return {'manifest': manifest, 'request': request, 'row': row, 'result': result}


def prepare(selection, out):
    out = safe_output(out)
    if out.exists():
        raise ValueError('Use a fresh study directory')
    items = selection['cases']
    if len(items) != 6 or len({i['role'] for i in items}) != 6:
        raise ValueError('Exactly six distinct study roles required')
    sources = [source_record(i) for i in items]
    rows = [s['row'] for s in sources]
    unique(rows)
    if {r['task_id'] for r in rows if r['dataset'] == 'validation_fixture'} != {'C01', 'C02'}:
        raise ValueError('Both authored controls are required')
    guard = selection['cached_clarified']
    cache_requests = json.loads((Path(guard['packet'])/'requests.json').read_text())
    cq = next(q for q in cache_requests if q['request_id'] == guard['request_id'])
    cache_rows = json.loads((Path(guard['packet'])/'inventory_PRIVATE_COMPARISON.json').read_text())
    cr = next(r for r in cache_rows if r['payload']['case_key'] == cq['case_key'])
    cached = read_result(guard['packet'], cq, cr)
    if not cached or cached['status'] != 'validated' or cached['judgment']['status'] != 'scored':
        raise ValueError('Cached clarified judgment is not usable')
    if cr not in rows:
        raise ValueError('Clarified cache is outside the selected cohort')
    config_keys = ('model', 'reasoning', 'max_output_tokens', 'store')
    configs = [{k:s['request']['api_request'].get(k) for k in config_keys} for s in sources]
    if any(c != configs[0] for c in configs):
        raise ValueError('Study mixes model configurations')
    requests, bindings = [], []
    for item, source in zip(items, sources):
        row, original = source['row'], source['request']
        for arm in ('original', 'clarified'):
            api = original['api_request'] if arm == 'original' else clarified(original['api_request'])
            for repeat in range(3):
                q = {'request_id': f"pathcal_{arm}_{original['case_key']}_r{repeat:02}",
                     'case_key': original['case_key'], 'role': item['role'], 'arm': arm, 'repeat': repeat,
                     'input_sha256': row['input_sha256'], 'api_request': deepcopy(api), 'request_sha256': digest(api)}
                requests.append(q)
                if repeat == 0 and arm == 'original':
                    bindings.append({'request_id':q['request_id'], 'source_packet':item['packet'],
                                     'source_request_id':item['request_id']})
                if repeat == 0 and arm == 'clarified' and cq['case_key'] == q['case_key']:
                    if cq['api_request'] != api or cr != row:
                        raise ValueError('Cached clarification is not an exact request/input match')
                    bindings.append({'request_id':q['request_id'], 'source_packet':guard['packet'],
                                     'source_request_id':guard['request_id']})
    cached_ids = {b['request_id'] for b in bindings}
    phase1 = [q['request_id'] for q in requests if q['arm']=='clarified' and q['repeat']==0 and q['request_id'] not in cached_ids]
    phase2 = [q['request_id'] for q in requests if q['repeat']>0]
    random.Random(20261113).shuffle(phase2)
    if (len(requests), len(bindings), len(phase1), len(phase2)) != (36, 7, 5, 24):
        raise ValueError('Expected 36 judgments, seven exact caches and 29 new requests')
    manifest = {'version':VERSION, 'status':'prepared_not_run_requires_new_api_authorization',
                'api_calls':0, 'proposed_new_call_cap':29, 'total_planned_judgments':36,
                'cached_judgments':7, 'phase1_new_calls':5, 'phase2_new_calls':24,
                'phase2_requires_phase1_review':True, 'repeats_per_case_per_arm':3,
                'model_config':configs[0], 'thresholds':THRESHOLDS,
                'plan_sha256':digest(PLAN.read_text()), 'addendum_sha256':digest(prompt_addendum()),
                'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'requests_sha256':digest(requests),'inventory_sha256':digest(rows),
                'selection_sha256':digest(selection),'bindings_sha256':digest(bindings),
                'phase1':phase1,'phase2_interleaved_order':phase2,
                'scores_changed':False,'independent_validation':False,'full_rerun_authorized':False}
    out.mkdir(parents=True)
    for name, value in [('manifest.json',manifest),('requests.json',requests),('inventory_PRIVATE_COMPARISON.json',rows),
                        ('selection.json',selection),('cache_bindings.json',bindings)]:
        write_json(out/name,value)
    for name in ('raw','results'):
        (out/name).mkdir()
    lookup = {q['request_id']:q for q in requests}
    bykey = {r['payload']['case_key']:r for r in rows}
    response_ids = set()
    for binding in bindings:
        q = lookup[binding['request_id']]
        src = Path(binding['source_packet']); rid = binding['source_request_id']
        result = json.loads((src/'results'/(rid+'.json')).read_text())
        if result['response_id'] in response_ids:
            raise ValueError('A cached response is being counted twice')
        response_ids.add(result['response_id'])
        result['offline_cache_binding'] = binding | {'new_api_calls':0}
        shutil.copy2(src/'raw'/(rid+'.json'), out/'raw'/(q['request_id']+'.json'))
        write_json(out/'results'/(q['request_id']+'.json'),result)
        read_result(out,q,bykey[q['case_key']])
    return check(out)


def check(out):
    out=Path(out)
    m,qs,rows,selection,bindings=[json.loads((out/name).read_text()) for name in
        ('manifest.json','requests.json','inventory_PRIVATE_COMPARISON.json','selection.json','cache_bindings.json')]
    expected={'version':VERSION,'api_calls':0,'proposed_new_call_cap':29,'total_planned_judgments':36,
              'cached_judgments':7,'phase1_new_calls':5,'phase2_new_calls':24,
              'thresholds':THRESHOLDS,'phase2_requires_phase1_review':True,
              'scores_changed':False,'full_rerun_authorized':False,
              'plan_sha256':digest(PLAN.read_text()),'addendum_sha256':digest(prompt_addendum()),
              'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'requests_sha256':digest(qs),'inventory_sha256':digest(rows),
              'selection_sha256':digest(selection),'bindings_sha256':digest(bindings)}
    if any(m.get(k)!=v for k,v in expected.items()) or len(qs)!=36 or len(bindings)!=7:
        raise ValueError('Study fingerprints or bounded scope changed')
    unique(rows);verify_sources(rows)
    sources={s['request']['case_key']:s for s in map(source_record,selection['cases'])}
    if len(sources)!=6 or set(sources)!={r['payload']['case_key'] for r in rows}:
        raise ValueError('Selected cohort changed')
    if {r['payload']['case_key']:r for r in rows} != {k:s['row'] for k,s in sources.items()}:
        raise ValueError('Frozen inventory differs from source records')
    seen=set(); conditions=set()
    for q in qs:
        if q['request_id'] in seen or q['arm'] not in {'original','clarified'} or (type(q['repeat']) is not int or q['repeat'] not in range(3)):
            raise ValueError('Duplicate request or invalid arm/repeat')
        seen.add(q['request_id']); conditions.add((q['case_key'],q['arm'],q['repeat']));source=sources[q['case_key']]
        expected_api=source['request']['api_request']
        if q['arm']=='clarified':expected_api=clarified(expected_api)
        if q['api_request']!=expected_api or q['request_sha256']!=digest(expected_api) or q['input_sha256']!=source['row']['input_sha256']:
            raise ValueError('Only the frozen prompt addendum may differ between arms')
    if len(conditions)!=36:
        raise ValueError('Each case/arm/repeat must occur once')
    cached_ids={b['request_id'] for b in bindings}
    phase1=[q['request_id'] for q in qs if q['arm']=='clarified' and q['repeat']==0 and q['request_id'] not in cached_ids]
    phase2=[q['request_id'] for q in qs if q['repeat']>0];random.Random(20261113).shuffle(phase2)
    if m['phase1']!=phase1 or m['phase2_interleaved_order']!=phase2 or len(phase1)!=5 or len(phase2)!=24:
        raise ValueError('Frozen scheduling order changed')
    if set(m['phase1'])|set(m['phase2_interleaved_order'])|{b['request_id'] for b in bindings} != seen:
        raise ValueError('Scheduling coverage differs from requests')
    lookup={q['request_id']:q for q in qs}
    if any(lookup[b['request_id']]['repeat']!=0 for b in bindings) or sum(lookup[b['request_id']]['arm']=='original' for b in bindings)!=6:
        raise ValueError('Only six original first judgments and one clarified first judgment may be cached')
    cached_response_ids=set()
    for b in bindings:
        q=next(q for q in qs if q['request_id']==b['request_id'])
        result=read_result(out,q,sources[q['case_key']]['row'])
        if not result or result['status']!='validated' or result['judgment']['status']!='scored':
            raise ValueError('Cached result missing or unusable')
        if result['response_id'] in cached_response_ids:
            raise ValueError('Duplicate cached response')
        cached_response_ids.add(result['response_id'])
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    prepare_p=sub.add_parser('prepare');prepare_p.add_argument('--selection',type=Path,required=True);prepare_p.add_argument('--out',type=Path,required=True)
    check_p=sub.add_parser('check');check_p.add_argument('--packet',type=Path,required=True);a=p.parse_args()
    result=prepare(json.loads(a.selection.read_text()),a.out) if a.command=='prepare' else check(a.packet)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
