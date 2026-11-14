"""Prepare/check an opt-in required-path probe offline. No paid runner or API access."""
import argparse
from copy import deepcopy
import json
import hashlib
from pathlib import Path

from .design.inputs import verify_sources, unique
from .design.judge import load_packet, safe_output, write_json
from .design.rubric import digest, ROOT

VERSION = 'required_path_probe_v1_prepared_only'
ADDENDUM = ROOT / 'docs/evaluation/required_path_clarification_draft_v1.md'


def prompt_addendum():
    text = ADDENDUM.read_text()
    return text.split('## Proposed prompt addendum\n\n', 1)[1].split('\n## Interpretation and limits', 1)[0].strip()


def prepare(packet_paths, out):
    out = safe_output(out)
    if out.exists():
        raise ValueError('Use a fresh probe directory')
    if len(packet_paths) != 4:
        raise ValueError('Exactly four frozen source cases required')
    requests, originals, rows, identities = [], [], [], set()
    for path in packet_paths:
        manifest, cases, frozen = load_packet(path)
        if len(cases) != 1 or len(frozen) != 1 or not manifest['source_bound_evidence_experimental']:
            raise ValueError('Use one-task, one-judgment, evidence-reference primary packets')
        row = cases[0]
        key = row['payload']['case_key']
        if key in identities:
            raise ValueError('Duplicate probe case')
        identities.add(key)
        original = frozen[0]
        api = deepcopy(original['api_request'])
        if len(api['input']) != 2 or api['input'][0]['role'] != 'system':
            raise ValueError('Unexpected original request layout')
        api['input'][0]['content'] += '\n\nREQUIRED-PATH CLARIFICATION (DEVELOPMENT PROBE)\n' + prompt_addendum()
        requests.append({'request_id': 'required_path_' + key + '_r00', 'case_key': key,
                         'input_sha256': row['input_sha256'], 'api_request': api,
                         'request_sha256': digest(api)})
        originals.append({'packet': str(path), 'manifest': manifest, 'request': original})
        rows.append(row)
    manifest = {'version': VERSION, 'probe_implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'status': 'prepared_not_run_requires_new_api_authorization',
                'api_calls': 0, 'proposed_call_cap': 4, 'baseline_repeats': 1, 'proposed_repeats': 1,
                'probe_prompt_version': 'design_prompt_v1.4_required_path_probe',
                'addendum_sha256': digest(prompt_addendum()), 'document_sha256': digest(ADDENDUM.read_text()),
                'inventory_sha256': digest(rows), 'requests_sha256': digest(requests),
                'originals_sha256': digest(originals), 'published_scores_changed': False,
                'inputs_and_schema_unchanged': True, 'system_prompt_only_change': True,
                'independent_validation': False, 'full_rerun_authorized': False}
    out.mkdir(parents=True)
    for name, value in [('manifest.json', manifest), ('requests.json', requests),
                        ('inventory_PRIVATE_COMPARISON.json', rows), ('originals.json', originals)]:
        write_json(out / name, value)
    return check(out)


def check(packet):
    packet = Path(packet)
    manifest, requests, rows, originals = [json.loads((packet / name).read_text()) for name in
        ('manifest.json', 'requests.json', 'inventory_PRIVATE_COMPARISON.json', 'originals.json')]
    expected = {'version': VERSION, 'probe_implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'api_calls': 0, 'proposed_call_cap': 4,
                'addendum_sha256': digest(prompt_addendum()), 'document_sha256': digest(ADDENDUM.read_text()),
                'inventory_sha256': digest(rows), 'requests_sha256': digest(requests),
                'originals_sha256': digest(originals)}
    if any(manifest.get(k) != v for k, v in expected.items()) or not len(requests)==len(rows)==len(originals)==4:
        raise ValueError('Probe fingerprints or bounded scope changed')
    unique(rows)
    if len({r['request_id'] for r in requests}) != 4:
        raise ValueError('Duplicate probe request IDs')
    verify_sources(rows)
    for request, row, saved in zip(requests, rows, originals):
        current_manifest, current_rows, current_requests = load_packet(saved['packet'])
        if saved['manifest'] != current_manifest or [row] != current_rows or [saved['request']] != current_requests:
            raise ValueError('Original packet changed')
        original = saved['request']
        candidate = deepcopy(request['api_request'])
        suffix = '\n\nREQUIRED-PATH CLARIFICATION (DEVELOPMENT PROBE)\n' + prompt_addendum()
        if not candidate['input'][0]['content'].endswith(suffix):
            raise ValueError('Probe instruction differs')
        candidate['input'][0]['content'] = candidate['input'][0]['content'][:-len(suffix)]
        if (candidate != original['api_request'] or digest(request['api_request']) != request['request_sha256'] or
            request['case_key'] != row['payload']['case_key'] or request['input_sha256'] != row['input_sha256']):
            raise ValueError('Probe changes more than the system addendum or task binding')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--packet', type=Path, action='append', required=True)
    p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('check')
    p.add_argument('--packet', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.packet, args.out) if args.command=='prepare' else check(args.packet), indent=2))


if __name__ == '__main__':
    main()
