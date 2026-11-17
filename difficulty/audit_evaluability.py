"""Offline source-consistency triage; never assign task outcomes or modify data."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re

from difficulty.llm_judge import DATA_DIR, REPO, load_synthetic_cases
from difficulty.saved_trials import file_hash
from difficulty.structural_features import SYSTEM_TOOLS, extract


def literal_return(classes, class_name, method_name, seen=None):
    """Resolve a local inherited method; inspect a single literal return, never call it."""
    seen = set() if seen is None else seen
    if class_name in seen or class_name not in classes:
        return None
    seen.add(class_name)
    node = classes[class_name]
    method = next((n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == method_name), None)
    if method is None:
        for base in node.bases:
            if isinstance(base, ast.Name):
                result = literal_return(classes, base.id, method_name, seen)
                if result is not None:
                    return result
        return None
    returns = [n for n in ast.walk(method) if isinstance(n, ast.Return)]
    if len(returns) != 1:
        return None
    try:
        value = ast.literal_eval(returns[0].value)
    except (ValueError, TypeError):
        return None
    if not isinstance(value, dict):
        return None
    return {'value': value, 'method_line': method.lineno, 'return_line': returns[0].lineno,
            'scope': 'candidate output only if execution reaches this return; no tool execution performed'}


def subset_matches(expected, observed):
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(k in observed and subset_matches(v, observed[k])
                                                  for k, v in expected.items())
    return type(expected) is type(observed) and expected == observed


def compare_fields(milestones, outputs):
    findings = []
    for milestone in milestones:
        for field, expected in milestone.get('expected_state', {}).items():
            matches = [(name, record) for name, record in outputs.items() if field in record['value']]
            record = {'milestone_step': milestone['step'], 'reference_field': field,
                      'reference_value': expected}
            if len(matches) == 1:
                name, source = matches[0]
                record.update(tool=name, candidate_value=source['value'][field],
                              source_method_line=source['method_line'], source_return_line=source['return_line'],
                              finding='literal_subset_match' if subset_matches(expected, source['value'][field])
                              else 'literal_difference_requires_review')
            else:
                record.update(finding='ambiguous_tool_mapping' if matches else 'no_exact_static_field_mapping',
                              candidate_tools=[name for name, _ in matches])
            findings.append(record)
    return findings


def audit():
    features = extract()
    cases = load_synthetic_cases()
    replay_path = REPO / 'results/rubric_review/v1/reference_replay.json'
    replays = {(r['domain'], r['task_id']): r for r in json.loads(replay_path.read_text())}
    historical = json.loads((REPO / 'results/baseline/v2_synthetic_full/manifest.json').read_text())
    trees = {}; rows = []
    import yaml
    for feature in features['tasks']:
        domain, task_id = feature['domain'], feature['task_id']
        path = DATA_DIR / domain / 'test_cases.py'
        yaml_path = path.with_name('agent_definition.yaml')
        for source in (path, yaml_path):
            if file_hash(source) != historical['sources'][str(source.relative_to(REPO))]:
                raise ValueError('Supplied source changed since baseline: ' + str(source))
        if domain not in trees:
            trees[domain] = {n.name: n for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef)}
        reference = cases[(domain, task_id)]
        names = set(reference['expected_tool_calls']) - SYSTEM_TOOLS
        outputs = {name: found for name in sorted(names)
                   if (found := literal_return(trees[domain], feature['class_name'], name)) is not None}
        fields = compare_fields(reference['milestones'], outputs)
        agent = yaml.safe_load(yaml_path.read_text())['agent']
        workflow = next(w for w in agent['workflows'] if w['id'] == feature['workflow_id'])
        endpoint_flags = []
        for step in workflow['steps']:
            used = step.get('tools_used', [])
            if used and set(used) <= SYSTEM_TOOLS and re.search(
                r'\b(approv\w*|clos\w*|creat\w*|updat\w*|send\w*|notif\w*|block\w*|process\w*)\b',
                step['description'], re.I):
                endpoint_flags.append({'step': step['step'], 'description': step['description'],
                                       'tools_used': used, 'finding': 'system_tool_only_business_endpoint_requires_contract_review'})
        replay = replays[(domain, task_id)]
        differences = [f for f in fields if f['finding'] == 'literal_difference_requires_review']
        flags = []
        if replay['errors']: flags.append('historical_reference_execution_errors')
        if differences: flags.append('reference_literal_output_differences')
        if endpoint_flags: flags.append('system_tool_only_business_endpoint')
        if feature['expected_tools_not_listed_in_workflow']: flags.append('reference_tools_not_listed_in_workflow')
        rows.append({'domain': domain, 'task_id': task_id, 'title': reference['title'],
                     'workflow_id': feature['workflow_id'], 'source_file': str(path.relative_to(REPO)),
                     'class_line': feature['sources']['python_class_line'], 'review_flags': flags,
                     'expected_domain_tool_count': len(names), 'static_literal_tools_resolved': sorted(outputs),
                     'static_tools_unresolved': sorted(names - outputs.keys()),
                     'field_findings': fields, 'endpoint_findings': endpoint_flags,
                     'historical_reference_errors': replay['errors'],
                     'new_task_judgment': None, 'difficulty_eligibility': 'not_assigned_by_source_audit'})
    return {'audit_version': 'evaluability_source_triage_v0.1', 'network_calls': 0,
            'new_tool_executions': 0, 'new_outcome_labels': False, 'tasks': rows,
            'task_count': len(rows), 'domain_count': len({r['domain'] for r in rows}),
            'tasks_by_review_flag': dict(Counter(f for row in rows for f in row['review_flags'])),
            'field_finding_counts': dict(Counter(f['finding'] for row in rows for f in row['field_findings'])),
            'source_hashes': features['source_sha256'], 'historical_replay_sha256': file_hash(replay_path),
            'limitations': ['Literal differences are triage findings, not automatically material blockers.',
                            'Generated IDs, ordering, units, aliases, or broader task semantics can explain a difference.',
                            'Only exact top-level milestone output keys with unique static tool mapping are compared.',
                            'Conditional/dynamic/multiple-return methods are not fully analyzed; no static match does not prove missing capability.',
                            'A literal return may be unreachable for supplied arguments; preserved historical execution errors must be inspected.',
                            'No unflagged task is certified valid; no flagged task is declared impossible.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=REPO / 'results/evaluability/source_v1')
    args = parser.parse_args()
    out = args.out.resolve()
    protected = [DATA_DIR, REPO / 'results/baseline', REPO / 'results/framework', REPO / 'results/rubric_review']
    if out == REPO or any(out == p or out.is_relative_to(p) or p.is_relative_to(out) for p in protected):
        parser.error('Audit output must not overlap supplied data or historical evidence')
    target = out / 'source_audit.json'
    if target.exists(): parser.error('Audit already exists; choose a new output directory')
    result = audit();out.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:result[k] for k in ('task_count','domain_count','tasks_by_review_flag','field_finding_counts')},indent=2))


if __name__ == '__main__':
    main()
