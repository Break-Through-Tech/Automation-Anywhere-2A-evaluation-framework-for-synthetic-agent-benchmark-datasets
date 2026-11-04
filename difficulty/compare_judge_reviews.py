"""Compare recorded human judgments with model outputs; never fabricate human labels."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

if __package__:
    from .llm_judge import _parse_judgment
else:
    from llm_judge import _parse_judgment


def identity(row):
    return row['domain'], row['task_id'], str(row['trial'])


def pointer_value(transcript, locator):
    if not locator.startswith('#/'):
        raise ValueError('Review evidence locators must start with #/ relative to the transcript')
    value = transcript
    try:
        for token in locator[2:].split('/'):
            token = token.replace('~1', '/').replace('~0', '~')
            value = value[int(token)] if isinstance(value, list) else value[token]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise ValueError(f'Evidence locator does not resolve: {locator}') from exc
    return value


def check_evidence(judgment, transcript):
    for claim in [dict(evidence=judgment['task_evidence']), *judgment['milestones']]:
        for evidence in claim['evidence']:
            value = pointer_value(transcript, evidence['locator'])
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            if evidence['excerpt'] not in text:
                raise ValueError('Evidence excerpt is not present at its stated locator')


def compare_reviews(human_path, packet_path, judgments_path=None):
    human = json.loads(Path(human_path).read_text())
    packet = json.loads(Path(packet_path).read_text())
    packet_hash = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if (human['packet_sha256'] != packet_hash or human['rubric_sha256'] != packet['rubric_sha256']
            or human['rubric_version'] != packet['rubric_version']):
        raise ValueError('Human review packet or rubric fingerprint does not match')
    cases = {identity(c): c for c in packet['cases']}
    reviews = human['reviews']
    if len({identity(r) for r in reviews}) != len(reviews) or {identity(r) for r in reviews} != set(cases):
        raise ValueError('Human review identities must exactly match the packet without duplicates')
    pending = [r['review_id'] for r in reviews if not r.get('reviewer') or r.get('task_judgment') is None
               or not r.get('task_rationale') or any(
                   m.get('judgment') is None or m.get('applicable') is None or m.get('material') is None
                   or not m.get('rationale') or not m.get('applicability_basis') for m in r.get('milestones', []))]
    base = {'rubric_version': packet['rubric_version'], 'rubric_sha256': packet['rubric_sha256'],
            'scope': 'purposive development sample; not held-out judge validation',
            'expected_reviews': len(cases), 'independent_review_not_verified_by_software': True}
    if pending:
        return {**base, 'status': 'awaiting_human_review', 'pending_review_ids': pending,
                'agreement_metrics_computed': False}
    parsed_human = {}
    for row in reviews:
        parsed = _parse_judgment(json.dumps(row), cases[identity(row)]['reference']['milestones'])
        check_evidence(parsed, cases[identity(row)]['transcript'])
        parsed_human[identity(row)] = parsed
    if judgments_path is None:
        return {**base, 'status': 'awaiting_judge_results', 'agreement_metrics_computed': False}
    with Path(judgments_path).open(newline='') as handle:
        results = list(csv.DictReader(handle))
    if len({identity(r) for r in results}) != len(results) or {identity(r) for r in results} != set(cases):
        raise ValueError('Judge result identities must exactly match the review packet')
    task_pairs, milestone_pairs, unassessed = [], [], []
    for row in results:
        if row.get('rubric_sha256') != packet['rubric_sha256'] or row.get('rubric_version') != packet['rubric_version']:
            raise ValueError('Judge results and human reviews must use the same rubric version and hash')
        if row['status'] != 'valid':
            unassessed.append(cases[identity(row)]['review_id']); continue
        judgment = {'task_judgment': row['task_judgment'], 'task_rationale': row['rationale'],
                    'task_evidence': json.loads(row['evidence_json']),
                    'task_contradictions': json.loads(row['contradictions_json']),
                    'milestones': json.loads(row['milestones_json'])}
        parsed = _parse_judgment(json.dumps(judgment), cases[identity(row)]['reference']['milestones'])
        check_evidence(parsed, cases[identity(row)]['transcript'])
        reference = parsed_human[identity(row)]
        task_pairs.append((reference['task_judgment'], parsed['task_judgment']))
        milestone_pairs.extend((h['judgment'], j['judgment']) for h, j in zip(reference['milestones'], parsed['milestones']))
    def metrics(pairs):
        counts = Counter(pairs)
        return {'n_compared': len(pairs), 'n_agree': sum(a == b for a, b in pairs),
                'agreement': sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
                'confusion_counts': [{'human': a, 'judge': b, 'count': n} for (a, b), n in sorted(counts.items())]}
    return {**base, 'status': 'development_comparison_complete', 'agreement_metrics_computed': bool(task_pairs),
            'unassessed_judge_review_ids': unassessed,
            'task_comparison': metrics(task_pairs), 'milestone_comparison': metrics(milestone_pairs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--human', required=True, type=Path)
    parser.add_argument('--packet', required=True, type=Path)
    parser.add_argument('--judgments', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = compare_reviews(args.human, args.packet, args.judgments)
    if args.out.resolve() in {p.resolve() for p in (args.human, args.packet, args.judgments) if p}:
        parser.error('Comparison output cannot replace its input files')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
