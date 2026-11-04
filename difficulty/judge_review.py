"""Offline audits and blind review packets for original saved attempts."""
import hashlib
import json
from collections import Counter
from pathlib import Path

if __package__:
    from .saved_trials import file_hash
else:
    from saved_trials import file_hash


def identity(row):
    return (row['domain'], row['task_id'], str(row.get('trial', '')))


def select_trials(resolved, path, cases):
    selection = json.loads(Path(path).read_text())
    if not isinstance(selection, list) or not selection:
        raise ValueError('Selection must be a nonempty JSON list')
    available = {identity(row): (row, key, task) for row, key, task in resolved}
    selected, seen = [], set()
    for entry in selection:
        task = cases.get((entry['domain'], entry['task_id']))
        if task is None:
            raise ValueError('Unknown selected task')
        item_id = (entry['domain'], task['test_case_id'], str(entry['trial']))
        if item_id in seen:
            raise ValueError('Duplicate selection identity')
        if item_id not in available:
            raise ValueError(f'Selected attempt is missing: {item_id}')
        seen.add(item_id)
        row, key, reference = available[item_id]
        selected.append(({**row, 'review_id': entry.get('review_id', f'R{len(selected)+1:02d}')}, key, reference))
    return selected


def audit_inputs(all_resolved, selected, data_dir, rubric_path, selection):
    rows = [row for row, _, _ in all_resolved]
    sources = {}
    for row in rows:
        source = row.get('source', {})
        for key in ('csv', 'trace', 'manifest', 'jsonl'):
            if f'{key}_file' in source:
                path, expected = source[f'{key}_file'], source[f'{key}_sha256']
                if file_hash(path) != expected:
                    raise ValueError(f'Input changed during validation: {path}')
                sources[path] = expected
    reference_files = {str(p.resolve()): file_hash(p) for p in Path(data_dir).glob('*/test_cases.*')
                       if p.suffix in ('.json', '.py')}
    reference_files.update({str(p.resolve()): file_hash(p) for p in Path(data_dir).glob('*/agent_definition.yaml')})
    task_counts = Counter((r['domain'], r['task_id']) for r in rows)
    return {
        'status': 'offline_input_validation_only', 'network_calls': 0,
        'new_outcome_scores_assigned': False,
        'attempts_loaded': len(rows), 'tasks_loaded': len(task_counts),
        'categories_loaded': len({r['domain'] for r in rows}),
        'attempts_per_task_distribution': dict(Counter(task_counts.values())),
        'selected_attempts': len(selected),
        'selected_tasks': len({(r['domain'], r['task_id']) for r, _, _ in selected}),
        'selected_categories': len({r['domain'] for r, _, _ in selected}),
        'recorded_infrastructure_error_attempts': sum(bool(r.get('error')) for r in rows),
        'original_status_counts_for_provenance_only': dict(Counter(
            r.get('source', {}).get('original_evaluation', {}).get('status', 'not_recorded') for r in rows)),
        'invalid_reference_is_not_automatically_excluded': True,
        'source_hashes': sources, 'reference_hashes': reference_files,
        'implementation_hashes': {name: file_hash(Path(__file__).with_name(name))
                                  for name in ('llm_judge.py', 'saved_trials.py', 'judge_review.py', 'compare_judge_reviews.py')},
        'rubric_sha256': file_hash(rubric_path),
        'selection_sha256': file_hash(selection) if selection else None,
        'evidence_format': 'conversation and tool_events copied without modifying their contents; no original scores are sent as evidence',
    }


def write_review_packet(out, selected, rubric, rubric_hash):
    """Never overwrite a reviewer packet or completed human labels."""
    paths = [out / 'review_packet.json', out / 'human_reviews.json', out / 'REVIEW.md']
    if any(p.exists() for p in paths):
        raise ValueError('Review packet already exists; choose a new output directory to preserve human labels')
    materials, forms = [], []
    for row, _, task in selected:
        review_id = row.get('review_id', f'R{len(materials)+1:02d}')
        if any(m['review_id'] == review_id for m in materials):
            raise ValueError('Duplicate review_id')
        source = {k: v for k, v in row.get('source', {}).items()
                  if k not in ('original_evaluation', 'termination_reason')}
        materials.append({'review_id': review_id, 'domain': row['domain'],
                          'task_id': row['task_id'], 'trial': row.get('trial', ''),
                          'reference': task, 'transcript': row.get('transcript', row.get('messages')),
                          'source': source})
        forms.append({'review_id': review_id, 'domain': row['domain'], 'task_id': row['task_id'],
                      'trial': row.get('trial', ''), 'reviewer': None,
                      'task_judgment': None, 'task_rationale': '', 'task_evidence': [],
                      'task_contradictions': [],
                      'milestones': [{'step': m['step'], 'applicable': None, 'material': None,
                                      'applicability_basis': '', 'judgment': None, 'rationale': '',
                                      'evidence': [], 'contradictions': []} for m in task['milestones']]})
    packet = {'rubric_version': rubric[1], 'rubric_status': rubric[2],
              'rubric_sha256': rubric_hash, 'rubric_text': rubric[0],
              'status': 'awaiting_independent_human_review', 'cases': materials}
    canonical = json.dumps(packet, sort_keys=True, ensure_ascii=False).encode()
    packet_hash = hashlib.sha256(canonical).hexdigest()
    human = {'rubric_version': rubric[1], 'rubric_sha256': rubric_hash,
             'packet_sha256': packet_hash, 'reviews': forms}
    out.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(json.dumps(packet, indent=2, ensure_ascii=False) + '\n')
    paths[1].write_text(json.dumps(human, indent=2, ensure_ascii=False) + '\n')
    paths[2].write_text('''# Independent review of original synthetic attempts

Reviewer: you (or a teammate you choose). All human judgments are blank until
entered by the reviewer. This packet contains no old grader labels or LLM judge
answers. It is a purposive development sample, not a held-out validation set.

1. Open review_packet.json. Read the draft rubric and one case at a time.
   Each case includes its intended outcome, milestones, scenario inputs,
   conversation, and executed tool events with arguments, results, and errors.
2. Fill the matching entry in human_reviews.json. Enter your name, task judgment
   (met, unmet, or unverifiable), rationale, contradictions, and milestone checks.
   Decide applicability/materiality with reasons. Unresolved policy or reference
   conflicts can make a judgment unverifiable; do not invent missing facts.
3. For met/unmet judgments, give evidence with a JSON-pointer locator and a short
   exact excerpt. Example: {"locator":"#/tool_events/0/output/status",
   "excerpt":"verified"}. Conversation evidence uses #/conversation/INDEX/content.
   These locators are relative to that case's transcript object.
4. Keep justified escalation separate from completion of the requested outcome.
   Do not infer success from a SUCCESS call or the simulated user's stop marker.
5. Save the form before looking at any model judgments. Run the comparison
   command documented in difficulty/README.md after model results are available.

If you prefer reviewing in chat, provide the review ID, judgment, supporting
observations, and unresolved questions. The assistant can transcribe your actual
judgments into the form; it must not invent human labels or sign off for you.

The historical attempts and source annotations are unchanged. New judgments
remain exploratory while the rubric is a draft. Full independent calibration,
including held-out examples, remains issue #48.
''')
