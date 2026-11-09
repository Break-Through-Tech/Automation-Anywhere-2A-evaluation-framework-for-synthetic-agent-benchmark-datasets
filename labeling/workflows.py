"""Build workflow labels for the committed coverage dataset. No model calls.

Run from the repo root: python labeling/workflows.py
"""

import argparse
import ast
import csv
import hashlib
import json
import re
import platform
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "coverage/labels/workflows"
STATUS_MARKERS = {"SUCCESS", "FAILED", "CANCELLED"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def record_hash(record):
    return sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode())


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_csv(path):
    with path.open(newline="") as source:
        return list(csv.DictReader(source))


def index_unique(rows, key, description):
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result:
            raise ValueError(f"Duplicate {description}: {identity}")
        result[identity] = row
    return result


def workflow_id(value):
    match = re.match(r"^\s*(W\d+)(?:\b|_)", value or "")
    if not match:
        raise ValueError(f"Invalid synthetic workflow ID: {value!r}")
    return match.group(1)


def parse_cases(path):
    # Read class attributes without importing agent code or initializing an LLM.
    cases = []
    for node in ast.parse(path.read_text()).body:
        if not isinstance(node, ast.ClassDef) or not node.name.startswith("TestCase"):
            continue
        attributes = {s.targets[0].id: s.value for s in node.body
                      if isinstance(s, ast.Assign) and len(s.targets) == 1
                      and isinstance(s.targets[0], ast.Name)}
        values = {name: ast.literal_eval(attributes[name])
                  for name in ("test_case_id", "title", "workflow")}
        calls = attributes["expected_tool_calls"]
        if not isinstance(calls, ast.List):
            raise ValueError(f"{path}:{node.lineno}: expected a literal tool-call list")
        tools = []
        for call in calls.elts:
            if not isinstance(call, ast.Dict):
                raise ValueError(f"{path}:{node.lineno}: unsupported tool-call format")
            for key, value in zip(call.keys, call.values):
                if isinstance(key, ast.Constant) and key.value == "name":
                    tools.append(ast.literal_eval(value))
        values.update(line=node.lineno, tools=tools)
        cases.append(values)
    return index_unique(cases, lambda c: c["test_case_id"], str(path))


def telecom_labels(task_id, families, conditions):
    match = re.fullmatch(r"\[([^]]+)\](.*?)\[PERSONA:([^]]+)\]", task_id)
    if not match:
        raise ValueError(f"Unrecognized telecom task ID: {task_id}")
    family, raw_conditions, persona = match.groups()
    parts = raw_conditions.split("|") if raw_conditions else []
    if family not in families or set(parts) - set(conditions):
        raise ValueError(f"Unknown telecom family or condition: {task_id}")
    if len(parts) != len(set(parts)):
        raise ValueError(f"Repeated telecom condition: {task_id}")
    return family, sorted(parts), persona


def match_json_case(case, json_cases):
    # Agent folders are already separate. Prefixes differ between Python and JSON.
    match = re.search(r"W\d+_TC\d+$", case["test_case_id"])
    if not match:
        raise ValueError(f"Unknown synthetic case ID: {case['test_case_id']}")
    suffix = "_" + match.group()
    candidates = [(wf, c) for wf, c in json_cases if c.get("test_case_id", "").endswith(suffix)]
    if len(candidates) != 1:
        raise ValueError(f"{case['test_case_id']}: expected one JSON case, found {len(candidates)}")
    workflow, candidate = candidates[0]
    if candidate["title"] != case["title"] or workflow_id(workflow) != workflow_id(case["workflow"]):
        raise ValueError(f"{case['test_case_id']}: Python/JSON title or workflow mismatch")
    return candidate


def build(root=ROOT):
    inputs = {}

    def source(relative):
        path = root / relative
        inputs[str(relative)] = sha256(path.read_bytes())
        return path

    rules = json.loads(source("labeling/workflow_rules.json").read_text())
    snapshot = root / "labeling/workflow_sources/tau2"
    manifest = json.loads(source("labeling/workflow_sources/tau2/manifest.json").read_text())
    for name, expected in manifest["snapshot_sha256"].items():
        path = source(str((snapshot / name).relative_to(root)))
        if sha256(path.read_bytes()) != expected:
            raise ValueError(f"Changed tau2 source snapshot: {name}")
    metadata = index_unique(read_jsonl(snapshot / "tasks.jsonl"),
                            lambda t: (t["domain"], t["task_id"]), "tau2 metadata")
    conditions = json.loads((snapshot / "conditions.json").read_text())
    mapping = index_unique(read_csv(source("labeling/workflow_task_map.csv")),
                           lambda t: t["task_id"], "curated workflow mapping")
    tasks = read_jsonl(source("data/processed/tasks.jsonl"))
    index_unique(tasks, lambda t: (t["dataset"], t["domain"], t["task_id"]), "processed task")
    legacy = []
    for dataset in ("tau2", "synthetic"):
        legacy.extend(read_csv(source(f"coverage/labels/labels_{dataset}.csv")))
    legacy = index_unique(legacy, lambda r: (r["dataset"], r["task_id"]), "legacy label")
    expected_ids = {(t["dataset"], f"{t['domain']}:{t['task_id']}" if t["dataset"] == "tau2"
                     else t["task_id"]) for t in tasks}
    if expected_ids != set(legacy):
        raise ValueError("Task IDs and legacy label IDs differ; align the input datasets first")
    if set(metadata) != {(t["domain"], t["task_id"]) for t in tasks if t["dataset"] == "tau2"}:
        raise ValueError("Tau2 metadata does not match the committed split")
    if set(mapping) != {f"{domain}:{task_id}" for domain, task_id in metadata if domain != "telecom"}:
        raise ValueError("Curated workflow mapping does not cover exactly the airline/retail tasks")

    catalog, synthetic = {}, {}

    def add_family(dataset, domain, agent, family, name, definition, origin, scope, reference):
        key = f"{dataset}:{agent}:{family}"
        if key in catalog:
            raise ValueError(f"Duplicate workflow definition: {key}")
        catalog[key] = {"dataset": dataset, "domain": domain, "agent_category": agent,
                        "workflow_key": key, "workflow_name": name, "definition": definition,
                        "origin": origin, "scope": scope, "definition_source": reference}

    for domain, families in rules["families"].items():
        policy = manifest["original_files"][f"data/tau2/domains/{domain}/policy.md"]["url"]
        for family, definition in families.items():
            scope = "unsupported_request" if family in rules["unsupported_families"][domain] else "policy_bounded_request"
            add_family("tau2", domain, domain, family, family.replace("_", " "), definition,
                       "team_label_from_policy_and_tasks", scope, policy)
    telecom_policy = manifest["original_files"]["data/tau2/domains/telecom/tech_support_workflow.md"]["url"]
    for family, name in rules["telecom_families"].items():
        add_family("tau2", "telecom", "telecom", family, name, name,
                   "source_task_manager", "technical_support_base_split", telecom_policy)

    agents = sorted({t["domain"] for t in tasks if t["dataset"] == "synthetic"})
    for agent in agents:
        definition_path = source(f"data/{agent}/agent_definition.yaml")
        definition = yaml.safe_load(definition_path.read_text())["agent"]
        cases = parse_cases(source(f"data/{agent}/test_cases.py"))
        if set(cases) != {t["task_id"] for t in tasks if t["dataset"] == "synthetic" and t["domain"] == agent}:
            raise ValueError(f"{agent}: Python cases and committed tasks differ")
        json_path = source(f"data/{agent}/test_cases.json")
        json_cases = [(w["workflow"], c) for w in json.loads(json_path.read_text())["workflows"]
                      for c in w["test_cases"]]
        synthetic[agent] = {"cases": cases, "json_cases": json_cases}
        for number, workflow in enumerate(definition["workflows"]):
            add_family("synthetic", agent.split("_")[0], agent, workflow["id"], workflow["name"],
                       workflow.get("purpose", workflow["name"]), "source_workflow_id",
                       "declared_agent_workflow", f"data/{agent}/agent_definition.yaml#/agent/workflows/{number}")

    labels, evidence = [], []
    for task in sorted(tasks, key=lambda t: (t["dataset"], t["domain"], t["task_id"])):
        dataset, agent, original_id = task["dataset"], task["domain"], task["task_id"]
        task_id = f"{agent}:{original_id}" if dataset == "tau2" else original_id
        old = legacy[(dataset, task_id)]
        expected_domain = agent if dataset == "tau2" else agent.split("_")[0]
        if old["domain"] != expected_domain:
            raise ValueError(f"{task_id}: domain disagrees with legacy labels")
        factors, persona, notes, case_conditions, json_reference = [], "", [], [], ""
        if dataset == "tau2":
            meta = metadata[(agent, original_id)]
            if meta["instructions"]["reason_for_call"].strip() != task["description"] or meta["actions"] != task["actions"]:
                raise ValueError(f"{task_id}: task text or reference actions changed")
            goal = meta["instructions"]["reason_for_call"].strip()
            purpose = meta["description"].get("purpose") or ""
            reference = meta["source"] + " (id=" + original_id + ")"
            if agent == "telecom":
                family, factors, persona = telecom_labels(original_id, rules["telecom_families"], conditions)
                families, method = [family], "source_task_id_and_generator"
            else:
                entry = mapping[task_id]
                if entry["source_sha256"] != record_hash(meta):
                    raise ValueError(f"{task_id}: source changed; review the curated label")
                families = entry["workflow_families"].split("|")
                method = "curated_from_goal_instructions_and_policy"
                if entry["note"]:
                    notes.append(entry["note"])
        else:
            case = synthetic[agent]["cases"][original_id]
            if case["workflow"] != task["meta"]["workflow"] or case["title"] != task["meta"]["title"]:
                raise ValueError(f"{task_id}: workflow/title differs from committed task")
            expected_tools = [name for name in case["tools"] if name not in STATUS_MARKERS]
            if expected_tools != [a["name"] for a in task["actions"]]:
                raise ValueError(f"{task_id}: reference tool sequence changed")
            families, method = [workflow_id(case["workflow"])], "source_workflow_id_and_agent_definition"
            goal, purpose = case["title"], task["description"]
            reference = f"data/{agent}/test_cases.py:L{case['line']}"
            json_case = match_json_case(case, synthetic[agent]["json_cases"])
            json_reference = f"data/{agent}/test_cases.json (test_case_id={json_case['test_case_id']})"
            case_conditions = json_case.get("input_conditions", [])

        keys = sorted(f"{dataset}:{agent}:{family}" for family in families)
        if len(keys) != len(set(keys)) or set(keys) - set(catalog):
            raise ValueError(f"{task_id}: duplicate or undefined workflow labels")
        assistant_tools = sorted({a["name"] for a in task["actions"] if a["requestor"] == "assistant"})
        user_tools = sorted({a["name"] for a in task["actions"] if a["requestor"] == "user"})
        labels.append({"dataset": dataset, "domain": old["domain"], "agent_category": agent,
                       "task_id": task_id, "source_task_id": original_id,
                       "legacy_task_type": old["task_type"], "workflow_keys": "|".join(keys),
                       "telecom_conditions": "|".join(factors), "persona": persona,
                       "reference_assistant_tools": "|".join(assistant_tools),
                       "reference_user_tools": "|".join(user_tools), "label_method": method,
                       "goal": goal, "notes": " ".join(notes)})
        evidence.append({"dataset": dataset, "task_id": task_id, "task_source": reference,
                         "agent_policy_source": (f"data/{agent}/agent_definition.yaml#/agent" if dataset == "synthetic"
                                                 else manifest["original_files"][f"data/tau2/domains/{agent}/" +
                                                      ("main_policy.md" if agent == "telecom" else "policy.md")]["url"]),
                         "source_purpose": purpose, "workflow_keys": keys,
                         "definition_sources": [catalog[key]["definition_source"] for key in keys],
                         "telecom_condition_sources": {f: conditions[f] for f in factors},
                         "synthetic_json_source": json_reference,
                         "synthetic_input_conditions": case_conditions,
                         "notes": notes})

    totals = Counter((r["dataset"], r["agent_category"]) for r in labels)
    counts = Counter(key for r in labels for key in r["workflow_keys"].split("|"))
    for key, definition in catalog.items():
        definition["task_count"] = counts[key]
        definition["n_agent_tasks"] = totals[(definition["dataset"], definition["agent_category"])]
    provenance = {"schema_version": rules["schema_version"], "tau2_revision": manifest["revision"],
                  "python_version": platform.python_version(), "pyyaml_version": yaml.__version__,
                  "code_sha256": {"labeling/workflows.py": sha256(Path(__file__).read_bytes())},
                  "tau2_split": manifest["split"], "task_counts": dict(Counter(r["dataset"] for r in labels)),
                  "input_sha256": dict(sorted(inputs.items())),
                  "checks": ["unique task identities", "legacy labels match selected tasks",
                             "pinned tau2 metadata and snapshot hashes", "curated map source hashes",
                             "synthetic Python/JSON workflow agreement", "workflow IDs exist in agent definitions",
                             "known telecom condition IDs", "reference tools match selected dataset"],
                  "review_note": "Source extraction and rule checks; no independent human-label accuracy claim.",
                  "downstream_scoring_status": "not_run"}
    return labels, list(catalog.values()), evidence, provenance


def write_csv(path, rows):
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_results(output, labels, catalog, evidence, provenance):
    # These are label counts for review, not new coverage scores.
    counts = [{"dataset": c["dataset"], "domain": c["domain"], "agent_category": c["agent_category"],
               "attribute": "workflow", "label": c["workflow_key"], "task_count": c["task_count"],
               "n_tasks": c["n_agent_tasks"]} for c in catalog]
    telecom = [r for r in labels if r["agent_category"] == "telecom"]
    factors = Counter(f for r in telecom for f in r["telecom_conditions"].split("|") if f)
    counts.extend({"dataset": "tau2", "domain": "telecom", "agent_category": "telecom",
                   "attribute": "telecom_condition", "label": factor, "task_count": count,
                   "n_tasks": len(telecom)} for factor, count in sorted(factors.items()))
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "workflow_labels.csv", labels)
    write_csv(output / "workflow_catalog.csv", catalog)
    write_csv(output / "workflow_counts.csv", counts)
    (output / "workflow_evidence.jsonl").write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in evidence))
    provenance["output_sha256"] = {p.name: sha256(p.read_bytes()) for p in sorted(output.iterdir())
                                   if p.name in {"workflow_labels.csv", "workflow_catalog.csv",
                                                 "workflow_counts.csv", "workflow_evidence.jsonl"}}
    (output / "checks.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(labels)} task labels and {len(catalog)} workflow definitions to {output}")
    print(f"Telecom: {len(telecom)} tasks, {len(factors)} condition labels")
    missing = [c for c in catalog if c["dataset"] == "synthetic" and c["task_count"] == 0]
    print(f"Synthetic: {len(missing)} declared workflows have no selected Python test cases")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    labels, catalog, evidence, provenance = build()
    if args.output_dir.resolve() in {ROOT / "coverage", ROOT / "coverage/labels"}:
        parser.error("Use a separate output directory for workflow labels")
    write_results(args.output_dir, labels, catalog, evidence, provenance)


if __name__ == "__main__":
    main()
