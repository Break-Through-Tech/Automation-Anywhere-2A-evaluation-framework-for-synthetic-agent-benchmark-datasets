"""Extract proposed synthetic complexity signals without executing supplied cases."""
import argparse
import ast
import json
from pathlib import Path
import re

import yaml

if __package__:
    from .llm_judge import DATA_DIR, REPO, _literal_assignment, load_synthetic_cases
    from .saved_trials import file_hash
else:
    from llm_judge import DATA_DIR, REPO, _literal_assignment, load_synthetic_cases
    from saved_trials import file_hash

VERSION = 'structural_features_v0.1_proposed'
SYSTEM_TOOLS = {'SUCCESS', 'FAILED', 'CANCELLED', 'HUMAN_IN_THE_LOOP'}
FRAMEWORK_COLUMNS = (
    'class_difficulty_tag', 'declared_difficulty', 'workflow_id', 'workflow_step_count',
    'reference_domain_tool_call_count', 'reference_unique_domain_tool_count',
    'reference_system_tool_call_count', 'reference_milestone_count',
    'workflow_decision_cue_step_count', 'task_path_step_count',
    'task_decision_point_count', 'review_status',
)
# Count matching steps, not words, branches, or actual runtime decisions.
DECISION_CUES = re.compile(
    r'\b(if|unless|otherwise|whether|depending|based on|approve|approval|reject|rejection|escalate|escalation)\b',
    re.IGNORECASE,
)


def workflow_features(workflow):
    steps = workflow.get('steps', [])
    if not isinstance(steps, list) or not all(isinstance(s, dict) for s in steps):
        raise ValueError('Workflow steps must be a list of objects')
    tools = []
    cues = []
    for index, step in enumerate(steps):
        names = step.get('tools_used', [])
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            raise ValueError('tools_used must be a list of names')
        tools.extend(names)
        description = step.get('description', '')
        matches = sorted({m.group().lower() for m in DECISION_CUES.finditer(description)})
        if matches:
            cues.append({'step_index': index, 'step': step.get('step'),
                         'matched_cues': matches, 'description': description})
    return {'workflow_step_count': len(steps),
            'workflow_domain_tool_mentions': sum(n not in SYSTEM_TOOLS for n in tools),
            'workflow_system_tool_mentions': sum(n in SYSTEM_TOOLS for n in tools),
            'workflow_decision_cue_step_count': len(cues),
            'workflow_decision_cue_evidence': cues,
            'workflow_tool_names': tools}


def extract(data_dir=DATA_DIR):
    cases = load_synthetic_cases(data_dir)
    rows, hashes = [], {}
    for python_path in sorted(Path(data_dir).glob('*/test_cases.py')):
        domain = python_path.parent.name
        if not python_path.with_name('test_cases.json').exists():
            continue
        yaml_path = python_path.with_name('agent_definition.yaml')
        agent = yaml.safe_load(yaml_path.read_text())['agent']
        workflows = agent['workflows']
        by_workflow = {}
        for index, workflow in enumerate(workflows):
            if workflow['id'] in by_workflow:
                raise ValueError(f'Duplicate workflow ID in {yaml_path}')
            by_workflow[workflow['id']] = (index, workflow)
        for source in [python_path, yaml_path, python_path.with_name('test_cases.json')]:
            hashes[str(source.relative_to(data_dir))] = file_hash(source)
        tree = ast.parse(python_path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not node.name.startswith('TestCase'):
                continue
            task_id = _literal_assignment(node, 'test_case_id')
            reference = cases[(domain, task_id)]
            raw_workflow = _literal_assignment(node, 'workflow')
            match = re.match(r'^(W\d+)(?:\s|$)', raw_workflow or '')
            if not match or match.group(1) not in by_workflow:
                raise ValueError(f'Unknown workflow for {domain}/{task_id}: {raw_workflow}')
            workflow_id = match.group(1)
            workflow_index, workflow = by_workflow[workflow_id]
            features = workflow_features(workflow)
            names = reference['expected_tool_calls']
            tag = node.name.rsplit('_', 1)[-1]
            tag = tag if tag in {'easy', 'medium', 'hard'} else None
            declared = _literal_assignment(node, 'difficulty')
            unlisted = sorted(set(names) - set(features['workflow_tool_names']) - SYSTEM_TOOLS)
            flags = ['workflow_counts_are_not_task_path_counts', 'decision_cues_require_review']
            if tag is None:
                flags.append('missing_class_difficulty_tag')
            if tag != declared:
                flags.append('class_tag_disagrees_with_difficulty_field')
            if unlisted:
                flags.append('expected_tools_not_listed_in_workflow')
            rows.append({
                'domain': domain, 'task_id': task_id, 'title': reference['title'],
                'class_name': node.name, 'class_difficulty_tag': tag,
                'declared_difficulty': declared, 'workflow_id': workflow_id,
                'workflow_name': workflow.get('name'),
                **features,
                'reference_milestone_count': len(reference['milestones']),
                'reference_domain_tool_call_count': sum(n not in SYSTEM_TOOLS for n in names),
                'reference_unique_domain_tool_count': len(set(names) - SYSTEM_TOOLS),
                'reference_system_tool_call_count': sum(n in SYSTEM_TOOLS for n in names),
                'reference_tool_sequence': names, 'expected_tools_not_listed_in_workflow': unlisted,
                'task_path_step_count': None, 'task_decision_point_count': None,
                'review_status': 'proposed_unreviewed', 'review_flags': flags,
                'sources': {'python_file': str(python_path.relative_to(data_dir)),
                            'python_class_line': node.lineno,
                            'yaml_file': str(yaml_path.relative_to(data_dir)),
                            'yaml_workflow_pointer': f'#/agent/workflows/{workflow_index}',
                            'json_file': str(python_path.with_name('test_cases.json').relative_to(data_dir)),
                            'canonical_task_id': task_id},
            })
    identities = {(r['domain'], r['task_id']) for r in rows}
    expected = {(d, r['test_case_id']) for (d, _), r in cases.items()}
    if len(identities) != len(rows) or identities != expected:
        raise ValueError('Extracted tasks must match all canonical source task IDs exactly once')
    return {'feature_version': VERSION, 'status': 'proposed_unreviewed',
            'network_calls': 0, 'combined_difficulty_score': None,
            'source_root': str(Path(data_dir).resolve()), 'source_sha256': hashes,
            'task_count': len(rows), 'domain_count': len({r['domain'] for r in rows}),
            'tasks': rows}


def review_sample(features):
    """One task per domain, prioritizing source discrepancies, with blank human fields."""
    selected = []
    for domain in sorted({r['domain'] for r in features['tasks']}):
        candidates = [r for r in features['tasks'] if r['domain'] == domain]
        row = sorted(candidates, key=lambda r: (-len(r['review_flags']), r['task_id']))[0]
        selected.append({'features': row, 'reviewer': None,
                         'counts_and_tag_verified': None, 'notes': '',
                         'proposed_task_path_step_count': None,
                         'proposed_task_decision_point_count': None})
    return {'feature_version': VERSION, 'scope': 'one development example per domain; not exhaustive review',
            'reviews': selected}


def load_for_framework(path, tasks, data_dir=DATA_DIR):
    """Require an exact identity join and unchanged supplied sources before attaching features."""
    document = json.loads(Path(path).read_text())
    if document.get('feature_version') != VERSION or document.get('combined_difficulty_score') is not None:
        raise ValueError('Unsupported feature version or unexpected combined difficulty score')
    rows = document['tasks']
    expected = {(t['domain'], t['task_id']) for t in tasks if t['dataset'] == 'synthetic'}
    keys = [(r['domain'], r['task_id']) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != expected or document.get('task_count') != len(rows):
        raise ValueError('Structural features must match synthetic framework tasks exactly once')
    required_sources = {f'{domain}/{name}' for domain, _ in expected
                        for name in ('test_cases.py', 'test_cases.json', 'agent_definition.yaml')}
    if set(document.get('source_sha256', {})) != required_sources:
        raise ValueError('Structural features must fingerprint every supplied source file')
    source_paths = []
    root = Path(data_dir).resolve()
    for name, expected_hash in document['source_sha256'].items():
        source = (root / name).resolve()
        if not source.is_relative_to(root) or file_hash(source) != expected_hash:
            raise ValueError(f'Structural feature source changed or escaped data root: {name}')
        source_paths.append(source)
    for row in rows:
        for field in FRAMEWORK_COLUMNS:
            if field not in row:
                raise ValueError(f'Structural feature is missing {field}')
        for field in ('workflow_step_count', 'reference_domain_tool_call_count',
                      'reference_unique_domain_tool_count', 'reference_system_tool_call_count',
                      'reference_milestone_count', 'workflow_decision_cue_step_count'):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError(f'Structural feature {field} must be a nonnegative integer')
    return document, dict(zip(keys, rows)), source_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=REPO / 'results/difficulty/structural_v1')
    args = parser.parse_args()
    out = args.out.resolve()
    source = DATA_DIR.resolve()
    if out == source or out.is_relative_to(source) or source.is_relative_to(out):
        parser.error('Output must not overlap the supplied dataset')
    targets = [out / 'task_features.json', out / 'review_sample.json']
    if any(p.exists() for p in targets):
        parser.error('Outputs already exist; use a new directory to preserve human review')
    features = extract()
    out.mkdir(parents=True, exist_ok=True)
    for path, content in zip(targets, [features, review_sample(features)]):
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n')
    print(f"Extracted {features['task_count']} tasks across {features['domain_count']} domains; no API calls. Output: {out}")


if __name__ == '__main__':
    main()
