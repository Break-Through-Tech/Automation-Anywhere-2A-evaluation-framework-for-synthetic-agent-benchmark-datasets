"""Read original baseline evidence without changing rewards or losing tool results."""
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_transcript(transcript):
    if not isinstance(transcript, dict):
        raise ValueError('Baseline transcript must contain conversation and tool_events')
    for field in ('conversation', 'tool_events'):
        if not isinstance(transcript.get(field), list):
            raise ValueError(f'Baseline trace requires a {field} list')
    for message in transcript['conversation']:
        if not isinstance(message, dict) or not isinstance(message.get('role'), str) or 'content' not in message:
            raise ValueError('Malformed baseline conversation message')
    for event in transcript['tool_events']:
        if (not isinstance(event, dict) or not isinstance(event.get('name'), str)
                or not isinstance(event.get('arguments'), dict)
                or not isinstance(event.get('error'), bool) or 'output' not in event):
            raise ValueError('Malformed baseline tool event; inputs, output, and error are required')


def load_baseline_trials(csv_path):
    """CSV identities point at immutable .json.gz traces within the same run directory.

    Old invalid_reference labels remain provenance, not new judge exclusions.
    Only an actual infrastructure-error attempt is marked with a top-level error.
    """
    csv_path = Path(csv_path).resolve()
    root = csv_path.parent
    csv_hash = file_hash(csv_path)
    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        required = {'domain', 'task_id', 'trial', 'trace_file'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'Baseline CSV requires columns {sorted(required)}')
        records = list(reader)
    if not records:
        raise ValueError('No baseline trial rows found')
    rows, seen = [], set()
    for record in records:
        if not record['domain'] or not record['task_id']:
            raise ValueError('Baseline trial is missing domain or task_id')
        try:
            number = int(record['trial'])
        except (ValueError, TypeError) as exc:
            raise ValueError('Baseline trial must be a nonnegative integer') from exc
        if number < 0:
            raise ValueError('Baseline trial must be a nonnegative integer')
        identity = (record['domain'], record['task_id'], number)
        if identity in seen:
            raise ValueError(f'Duplicate baseline task/trial identity: {identity}')
        seen.add(identity)
        if not record['trace_file']:
            raise ValueError(f'Missing trace_file for {identity}')
        path = (root / record['trace_file']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Baseline trace must be inside its saved run directory')
        if not path.is_file():
            raise ValueError(f'Missing saved trace for {identity}: {path}')
        try:
            raw = path.read_bytes()
            trace = json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
        except (OSError, EOFError, ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f'Unreadable saved trace for {identity}: {path}') from exc
        if not isinstance(trace, dict) or type(trace.get('trial')) is not int or (
                trace.get('domain'), trace.get('task_id'), trace.get('trial')) != identity:
            raise ValueError(f'Trace identity does not match baseline CSV: {identity}')
        transcript = {key: trace.get(key) for key in ('conversation', 'tool_events')}
        validate_transcript(transcript)
        evaluation = trace.get('evaluation')
        if not isinstance(evaluation, dict):
            raise ValueError(f'Missing saved evaluation provenance for {identity}')
        if (record.get('evaluation_status') and
                record['evaluation_status'] != evaluation.get('status')):
            raise ValueError(f'Saved evaluation status disagrees with CSV: {identity}')
        if 'reward' in record and record['reward'] != (
                '' if evaluation.get('reward') is None else str(evaluation['reward'])):
            raise ValueError(f'Saved reward disagrees with CSV: {identity}')
        row = {'domain': identity[0], 'task_id': identity[1], 'trial': number,
               'transcript': transcript,
               'source': {'format': 'baseline_csv_trace_v1', 'csv_file': str(csv_path),
                          'csv_sha256': csv_hash, 'trace_file': str(path),
                          'trace_sha256': hashlib.sha256(raw).hexdigest(),
                          'original_evaluation': evaluation,
                          'termination_reason': record.get('termination_reason')}}
        # Retain the original scenario without sending the simulator's instructions.
        prompt = trace.get('user_prompt', '')
        if not isinstance(prompt, str):
            raise ValueError(f'Invalid user prompt in saved trace: {identity}')
        match = re.search(r'<scenario>\s*(.*?)\s*</scenario>', prompt, re.DOTALL)
        if match:
            row['scenario'] = json.loads(match.group(1))
            if not isinstance(row['scenario'], dict):
                raise ValueError(f'Invalid scenario object in saved trace: {identity}')
        if evaluation.get('status') == 'infrastructure_error':
            row['error'] = evaluation.get('error') or 'Recorded baseline infrastructure error'
        rows.append(row)
    if file_hash(csv_path) != csv_hash:
        raise ValueError('Baseline CSV changed during loading')
    manifest_path = root / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('completed_trials') is not None and manifest['completed_trials'] != len(rows):
            raise ValueError('CSV attempt count differs from the saved manifest')
        complete = manifest.get('planned_trials') == len(rows)
        if complete and manifest.get('num_trials') is not None:
            expected = set(range(manifest['num_trials']))
            tasks = {(r['domain'], r['task_id']) for r in rows}
            if (manifest.get('task_count') is not None and manifest['task_count'] != len(tasks)):
                raise ValueError('CSV task count differs from the saved manifest')
            for domain, task_id in tasks:
                if {r['trial'] for r in rows if (r['domain'], r['task_id']) == (domain, task_id)} != expected:
                    raise ValueError(f'Missing or unexpected trial slots for {domain}/{task_id}')
        for row in rows:
            row['source']['manifest_file'] = str(manifest_path)
            row['source']['manifest_sha256'] = file_hash(manifest_path)
    return rows
