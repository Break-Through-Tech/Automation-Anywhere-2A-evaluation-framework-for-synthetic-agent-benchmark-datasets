"""Bounded clarified-protocol execution and offline reporting, preserving the v19 core."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
import json
from pathlib import Path
from statistics import mean

from .design import judge
from .design.evidence_choices import request_payload
from .design.inputs import file_hash, unique, verify_sources
from .design.reporting import distribution, write_report
from .design.rubric import DIMENSIONS, digest, response_schema, system_prompt
from .required_path_calibration import clarified

VERSION = 'designed_difficulty_v1.1_required_path'


def load(packet, check_sources=True):
    packet = Path(packet)
    m, qs, rows, bindings = [json.loads((packet/name).read_text()) for name in
        ('manifest.json', 'requests.json', 'inventory_PRIVATE_COMPARISON.json', 'cache_bindings.json')]
    if (digest(qs) != m['requests_sha256'] or digest(rows) != m['inventory_sha256'] or
            digest(bindings) != m['bindings_sha256'] or len(qs) != m['n_requests'] or
            len(rows) != m['n_tasks'] or len(bindings) != m['cached_requests'] or
            len(qs)-len(bindings) != m['proposed_new_call_cap']):
        raise ValueError('Frozen full-run packet changed')
    unique(rows)
    if check_sources:
        verify_sources(rows)
    bykey = {r['payload']['case_key']: r for r in rows}
    seen, repeats, configs = set(), defaultdict(set), set()
    expected_prompt = clarified({'input': [{'content': system_prompt(True)}]})['input'][0]['content']
    for q in qs:
        key, rid, repeat = q['case_key'], q['request_id'], q['repeat']
        if key not in bykey or rid in seen or type(repeat) is not int or repeat < 0 or repeat in repeats[key]:
            raise ValueError('Unknown case or duplicate request/repeat')
        if Path(rid).name != rid or '/' in rid or '\\' in rid:
            raise ValueError('Unsafe request identifier')
        seen.add(rid); repeats[key].add(repeat)
        row, api = bykey[key], q['api_request']
        expected = request_payload(row, True)
        if (q['input_sha256'] != row['input_sha256'] or digest(api) != q['request_sha256'] or
            len(api['input']) != 2 or api['input'][0] != {'role': 'system', 'content': expected_prompt} or
            api['input'][1]['role'] != 'user' or json.loads(api['input'][1]['content']) != expected or
            api['text']['format']['schema'] != response_schema([u['unit_id'] for u in row['payload']['units']], row['payload']['source_catalog'])):
            raise ValueError('Prompt, input, evidence schema or request fingerprint changed')
        configs.add(digest({k: api.get(k) for k in ('model','reasoning','max_output_tokens','store')}))
    if set(repeats) != set(bykey) or any(v != set(range(len(v))) for v in repeats.values()) or len(configs) != 1:
        raise ValueError('Missing task/repeat or mixed generation configurations')
    if (len({b['request_id'] for b in bindings}) != len(bindings) or
            len({b['response_id'] for b in bindings}) != len(bindings) or
            not {b['request_id'] for b in bindings} <= seen):
        raise ValueError('Duplicate or unknown cache binding')
    return m, qs, rows, bindings


def bind_caches(packet):
    packet = Path(packet)
    m, qs, rows, bindings = load(packet)
    qmap = {q['request_id']:q for q in qs}; bykey = {r['payload']['case_key']:r for r in rows}
    for name in ('raw','results','intents'):
        (packet/name).mkdir(exist_ok=True)
    for b in bindings:
        q = qmap[b['request_id']]; src = Path(b['source_packet'])
        original = next(x for x in json.loads((src/'requests.json').read_text()) if x['request_id']==b['source_request_id'])
        if original['api_request'] != q['api_request'] or original.get('repeat',0) != q['repeat']:
            raise ValueError('Cache request/repeat differs')
        row = bykey[q['case_key']]
        r = judge.read_result(src, original, row)
        if not r or r['status'] != 'validated' or r['judgment']['status'] != 'scored' or r['response_id'] != b['response_id']:
            raise ValueError('Unusable cache')
        target = packet/'results'/(q['request_id']+'.json')
        if not target.exists():
            raw = json.loads((src/'raw'/(original['request_id']+'.json')).read_text())
            judge.write_json(packet/'raw'/(q['request_id']+'.json'), raw)
            r = deepcopy(r); r['offline_cache_binding'] = b | {'new_api_calls':0}
            judge.write_json(target, r)
        judge.read_result(packet,q,row)
    return m


def one_response(packet, q, row, client):
    """One wire call only; retain raw/error data and use the unchanged core validator."""
    rid = q['request_id']
    result = {'validator_version':judge.VALIDATOR_VERSION, 'release_protocol':VERSION,
        'request_sha256':q['request_sha256'], 'input_sha256':row['input_sha256'],
        'requested_model':q['api_request']['model'], 'started_at':judge.utc_now()}
    try:
        response = client.responses.create(**q['api_request'])
        raw = response.model_dump(mode='json')
        judge.write_json(packet/'raw'/(rid+'.json'), raw)
        result.update(returned_model=raw.get('model'), response_id=raw.get('id'), usage=raw.get('usage'),
            decoding_metadata={k:raw.get(k) for k in ('temperature','top_p','reasoning','max_output_tokens')})
        try:
            if raw.get('status') != 'completed':
                raise ValueError('Incomplete response')
            wire = json.loads(response.output_text)
            judge.Draft202012Validator(q['api_request']['text']['format']['schema']).validate(wire)
            result['model_judgment'] = wire
            value, arithmetic = judge.canonical_judgment(wire,row)
            judge.validate_judgment(value,row)
            if raw.get('model') != q['api_request']['model']:
                raise ValueError('Unexpected returned model; diagnose before continuing')
            result.update(status='validated',judgment=value,score_arithmetic=arithmetic,
                request_binding=judge.request_binding(wire,row),evidence_diagnostics=judge.evidence_diagnostics(value,row))
        except Exception as exc:
            result.update(status='format_error',error=str(exc))
    except Exception as exc:
        raw = judge.safe_api_error(exc)
        result.update(status='api_error',error=type(exc).__name__)
    raw_path = packet/'raw'/(rid+'.json')
    if not raw_path.exists():
        judge.write_json(raw_path,raw)
    result.update(raw_sha256=file_hash(raw_path),finished_at=judge.utc_now())
    judge.write_json(packet/'results'/(rid+'.json'),result)
    judge.read_result(packet,q,row)
    return result


def run(packet, max_calls, *, authorize_paid=False, concurrency=1, client=None):
    if not authorize_paid:
        raise PermissionError('Explicit paid authorization required')
    if type(max_calls) is not int or max_calls < 1 or concurrency not in (1,2,3):
        raise ValueError('Positive call limit and 1–3 concurrent requests required')
    packet = Path(packet); m, qs, rows, bindings = load(packet)
    log = packet/'execution_log.jsonl'
    if log.exists() and json.loads(log.read_text().splitlines()[-1])['stop_reason'] != 'call_limit_or_complete':
        raise ValueError('Previous stop gate requires documented diagnosis before continuing')
    if any(r['preflight_errors'] for r in rows):
        raise ValueError('Source preflight errors require review before paid execution')
    bykey = {r['payload']['case_key']:r for r in rows}
    for name in ('raw','results','intents'):
        (packet/name).mkdir(exist_ok=True)
    cached = {b['request_id'] for b in bindings}
    previous = {q['request_id']:judge.read_result(packet,q,bykey[q['case_key']]) for q in qs}
    if any(not previous[rid] for rid in cached):
        raise ValueError('Bind all validated caches before paid execution')
    if any(r and (r['status']!='validated' or r['judgment']['status']!='scored') for r in previous.values()):
        raise ValueError('Prior error/unscorable result needs diagnosis; no automatic retry')
    intents = {p.stem for p in (packet/'intents').glob('*.json')}
    if not intents <= {q['request_id'] for q in qs}-cached or any(not previous.get(rid) for rid in intents):
        raise ValueError('Unknown or unresolved spending intent; no automatic replay')
    allowance = min(max_calls,m['proposed_new_call_cap']-len(intents))
    pending = iter([q for q in qs if previous[q['request_id']] is None])
    if client is None:
        import os
        from dotenv import dotenv_values
        from openai import OpenAI
        key = os.environ.get('OPENAI_API_KEY') or dotenv_values('.env')['OPENAI_API_KEY']
        client = OpenAI(api_key=key,max_retries=0,timeout=180)
    calls, completed, stopped = 0, 0, None
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        active = {}
        while True:
            while not stopped and len(active)<concurrency and calls<allowance:
                q = next(pending,None)
                if q is None: break
                judge.write_json(packet/'intents'/(q['request_id']+'.json'),{
                    'authorization':'User approved up to 341 new calls with documented uncertainty',
                    'overall_new_call_cap':m['proposed_new_call_cap'],'request_sha256':q['request_sha256'],'at':judge.utc_now()})
                active[pool.submit(one_response,packet,q,bykey[q['case_key']],client)] = q
                calls += 1
            if not active: break
            done,_ = wait(active,return_when=FIRST_COMPLETED)
            for future in done:
                q = active.pop(future); r = future.result(); completed += 1
                status = r['judgment']['status'] if r['status']=='validated' else r['status']
                record = {'request_id':q['request_id'],'case_key':q['case_key'],'status':status,
                    'score':r.get('judgment',{}).get('overall_score'),'new_calls_dispatched':len(intents)+calls,
                    'new_calls_completed_this_invocation':completed,'at':judge.utc_now()}
                with (packet/'progress.jsonl').open('a') as f: f.write(json.dumps(record)+'\n')
                print(json.dumps(record),flush=True)
                if status!='scored': stopped='unusable_response_requires_diagnosis'
                old = [v['judgment']['overall_score'] for v in previous.values() if v and v['status']=='validated' and v['judgment']['case_key']==q['case_key'] and v['judgment']['status']=='scored']
                if status=='scored' and old and max(old+[record['score']])-min(old+[record['score']])>10:
                    stopped='repeat_range_above_10_requires_review'
                previous[q['request_id']] = r
    summary = {'new_calls_this_invocation':calls,'new_calls_total':len(intents)+calls,
        'stop_reason':stopped or 'call_limit_or_complete','remaining_requests':sum(v is None for v in previous.values())}
    with (packet/'execution_log.jsonl').open('a') as f:f.write(json.dumps(summary)+'\n')
    return summary


def report(packet):
    packet = Path(packet); m, qs, rows, _ = load(packet)
    grouped = defaultdict(list); saved_models = set()
    for q in qs:
        grouped[q['case_key']].append(q)
    tasks, response_ids = [], set()
    for row in rows:
        requests = grouped[row['payload']['case_key']]
        results = [judge.read_result(packet,q,row) for q in requests]
        for r in results:
            if r and r['status']=='validated':
                if r['response_id'] in response_ids:raise ValueError('Duplicate saved response')
                response_ids.add(r['response_id'])
        status, reason, score, dimensions = 'pending','Planned judgment missing',None,None
        if row['preflight_errors']:
            status,reason='source_preflight_blocked','; '.join(row['preflight_errors'])
        elif any(r and r['status']!='validated' for r in results):status,reason='judge_error','Planned response failed validation'
        elif any(r and r['judgment']['status']=='unscorable' for r in results):status,reason='unscorable','Source design cannot support a defensible score'
        elif all(results):
            status,reason='scored','All planned repeat judgments usable'
            score=mean(r['judgment']['overall_score'] for r in results)
            dimensions={k:mean(r['judgment']['dimensions'][k]['level'] for r in results) for k in DIMENSIONS}
        saved_models.update(r['returned_model'] for r in results if r and r['status']=='validated')
        tasks.append({k:row[k] for k in ('dataset','domain','task_id','workflow_id','input_sha256')} | {
            'case_key':row['payload']['case_key'],'status':status,'reason':reason,'score':score,'dimensions':dimensions,
            'n_planned_judgments':len(requests),'n_saved_judgments':sum(r is not None for r in results),
            'repeat_score_range':max(r['judgment']['overall_score'] for r in results)-min(r['judgment']['overall_score'] for r in results) if status=='scored' else None,
            'source_quality_flags':row['source_quality_flags'],
            'judge_source_quality_flags':[v for r in results if r and r['status']=='validated' for v in r['judgment']['source_quality_flags']],
            'judge_uncertainties':[v for r in results if r and r['status']=='validated' for v in r['judgment']['uncertainties']]})
    if len(saved_models)>1:raise ValueError('Mixed returned models')
    datasets={d:distribution([t for t in tasks if t['dataset']==d]) for d in sorted({t['dataset'] for t in tasks})}
    domains={d+'/'+n:distribution([t for t in tasks if t['dataset']==d and t['domain']==n]) for d in datasets for n in sorted({t['domain'] for t in tasks if t['dataset']==d})}
    return {'metric':'llm_source_only_designed_difficulty','release_protocol':VERSION,'rubric_version':'design_numeric_v1.0_provisional',
        'prompt_version':'design_prompt_v1.4_required_path_probe','scale':[0,100],
        'task_weighting':'equal_weight_after_mean_of_all_planned_usable_repeats','datasets':datasets,'domains':domains,'tasks':tasks,
        'packet_manifest_sha256':digest(m),'returned_models':sorted(saved_models),'independent_validation':False,
        'limitations':['Interpretive anchored index; practical repeatability is not independent accuracy.',
            'Multiple sufficient paths and source conflicts remain explicit.',
            'Higher designed difficulty does not establish higher dataset quality.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('check','bind-caches','run','report'));p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--max-calls',type=int,default=0);p.add_argument('--authorize-paid',action='store_true');p.add_argument('--concurrency',type=int,default=1);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.action=='check': value=load(a.packet)[0]
    elif a.action=='bind-caches':value=bind_caches(a.packet)
    elif a.action=='run':value=run(a.packet,a.max_calls,authorize_paid=a.authorize_paid,concurrency=a.concurrency)
    else:
        value=report(a.packet)
        if not a.out:raise ValueError('--out required for report')
        write_report(value,a.out)
        value={k:v for k,v in value.items() if k!='tasks'}
    print(json.dumps(value,indent=2))


if __name__=='__main__':main()
