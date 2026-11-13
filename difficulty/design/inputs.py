"""Static adapters: never import supplied test cases or initialize agents/tools."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml

from .rubric import INPUT_VERSION, ROOT, digest

ADAPTER_VERSION = "design_adapters_v1"
HIDDEN = {"difficulty", "difficulty_label", "difficulty_reasoning", "difficulty_tag",
          "class_name", "test_case_id", "score", "reward", "passed", "trial"}
TERMINALS = {"SUCCESS", "FAILED", "CANCELLED", "HUMAN_IN_THE_LOOP"}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value, identifiers=()):
    """Hide explicit labels/identities, preserving meaningful scenario constraints."""
    if isinstance(value, dict):
        return {k: clean(v, identifiers) for k, v in value.items()
                if k.lower() not in HIDDEN and not k.lower().startswith("difficulty_")}
    if isinstance(value, list):
        return [clean(v, identifiers) for v in value]
    if isinstance(value, str):
        for identifier in sorted(identifiers, key=len, reverse=True):
            value = value.replace(identifier, "[case]")
        return re.sub(r"(?i)\b(?:difficulty|complexity)[ _-]*(?:label|tag|level|rating)?\s*[:=]\s*(?:easy|medium|hard)\b", "[withheld annotation]", value)
    return value


def literals(node):
    result = {}
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    try:
                        result[target.id] = ast.literal_eval(item.value)
                    except (ValueError, TypeError, SyntaxError):
                        pass
    return result


def tool_definitions(value):
    result = {}
    def walk(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("name"), str) and any(k in obj for k in ("signature", "args", "returns")):
                if obj["name"] in result:
                    raise ValueError("Duplicate tool definition: " + obj["name"])
                result[obj["name"]] = obj
            else:
                for child in obj.values():
                    walk(child)
        elif isinstance(obj, list):
            for child in obj:
                walk(child)
    walk(value)
    return result


class CaseBuilder:
    def __init__(self, dataset, domain, task_id, workflow_id, root, identifiers=()):
        self.root = Path(root).resolve()
        self.identifiers = identifiers
        self.row = {"dataset": dataset, "domain": domain, "task_id": task_id,
                    "workflow_id": workflow_id, "source_root": str(self.root),
                    "sources": {}, "source_quality_flags": [], "preflight_errors": [],
                    "comparison_only": {}, "provenance": {}}
        self.payload = {"version": INPUT_VERSION, "case_key": digest([dataset, domain, task_id])[:24],
                        "source_catalog": [], "units": [], "source_notes": []}

    def add(self, source_id, value, path, locator, kind="context"):
        path = Path(path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Source escaped adapter root")
        text = json.dumps(clean(value, self.identifiers), ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else clean(value, self.identifiers)
        self.payload["source_catalog"].append({"source_id": source_id, "text": text, "kind": kind})
        relative = str(path.relative_to(self.root))
        self.row["sources"][source_id] = {"path": relative, "locator": locator, "sha256": file_hash(path)}
        return source_id

    def unit(self, unit_id, source_id, kind):
        self.payload["units"].append({"unit_id": unit_id, "source_ids": [source_id], "kind": kind})

    def finish(self):
        self.row["payload"] = self.payload
        self.row["input_sha256"] = digest(self.payload)
        validate_case(self.row)
        return self.row


def validate_case(row):
    payload = row["payload"]
    if payload.get("version") != INPUT_VERSION or row["input_sha256"] != digest(payload):
        raise ValueError("Unsupported input contract or changed input fingerprint")
    ids = [s["source_id"] for s in payload["source_catalog"]]
    units = [u["unit_id"] for u in payload["units"]]
    if not ids or len(ids) != len(set(ids)) or len(units) != len(set(units)):
        raise ValueError("Missing or duplicate sources/units")
    if set(row["sources"]) != set(ids):
        raise ValueError("Source pointers must cover every visible source")
    if any(not u["source_ids"] or not set(u["source_ids"]).issubset(ids) for u in payload["units"]):
        raise ValueError("Unit source is missing")
    if not units:
        raise ValueError("No assessable task requirements")


def synthetic_cases(data_dir=ROOT / "data"):
    rows = []
    root = Path(data_dir)
    for jp in sorted(root.glob("*/test_cases.json")):
        pp, yp = jp.with_suffix(".py"), jp.with_name("agent_definition.yaml")
        classes = [(n, literals(n)) for n in ast.parse(pp.read_text()).body
                   if isinstance(n, ast.ClassDef) and n.name.startswith("TestCase")]
        ids = [v.get("test_case_id") for _, v in classes]
        if any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)):
            raise ValueError("Missing or duplicate canonical Python case IDs")
        agent = yaml.safe_load(yp.read_text())["agent"]
        workflows = agent["workflows"]
        if len({w["id"] for w in workflows}) != len(workflows):
            raise ValueError("Duplicate workflow IDs")
        definitions = tool_definitions(agent.get("tools", {}))
        mapped = set()
        for wi, group in enumerate(json.loads(jp.read_text())["workflows"]):
            for ci, case in enumerate(group["test_cases"]):
                token = re.search(r"W\d+_TC\d+$", case["test_case_id"])
                candidates = [(n, v) for n, v in classes if v["test_case_id"] == case["test_case_id"] or
                              (token and v["test_case_id"].endswith(token.group()))]
                if len(candidates) != 1:
                    raise ValueError("Ambiguous JSON/Python task mapping")
                node, values = candidates[0]
                canonical = values["test_case_id"]
                if canonical in mapped:
                    raise ValueError("Duplicate JSON case mapping")
                mapped.add(canonical)
                wid = re.match(r"W\d+", values.get("workflow", ""))
                matches = [(i, w) for i, w in enumerate(workflows) if wid and w["id"] == wid.group()]
                if len(matches) != 1:
                    raise ValueError("Missing or ambiguous selected workflow")
                yi, workflow = matches[0]
                json_workflow = re.match(r"W\d+", group["workflow"])
                if not json_workflow or json_workflow.group() != workflow["id"]:
                    raise ValueError("JSON/Python workflow conflict")
                b = CaseBuilder("synthetic", jp.parent.name, canonical, workflow["id"], root,
                                [canonical, case["test_case_id"], node.name])
                b.row["comparison_only"] = {"class_tag": node.name.rsplit("_", 1)[-1],
                                              "declared_label": values.get("difficulty"),
                                              "difficulty_reasoning": values.get("difficulty_reasoning")}
                base = f"#/workflows/{wi}/test_cases/{ci}"
                for field in ("title", "rationale", "input_conditions", "representative_input", "success_path_differences", "expected_success_outcome"):
                    if field in case:
                        b.add("case_" + field, case[field], jp, base + "/" + field, "scenario")
                b.add("python_input", values.get("input_data", {}), pp, f"class at line {node.lineno}/input_data", "scenario")
                if values.get("input_data") != case.get("representative_input"):
                    b.row["source_quality_flags"].append("python_json_scenario_difference")
                calls = values.get("expected_tool_calls")
                if calls is None:
                    # Some references contain expressions: retain static call text, never evaluate it.
                    assignment = next((s for s in node.body if isinstance(s, ast.Assign) and
                                       any(isinstance(t, ast.Name) and t.id == "expected_tool_calls" for t in s.targets)), None)
                    calls = ast.get_source_segment(pp.read_text(), assignment.value) if assignment else None
                    b.row["source_quality_flags"].append("reference_has_nonliteral_expressions")
                b.add("reference_calls", calls, pp, f"class at line {node.lineno}/expected_tool_calls", "intended_reference_not_execution")
                b.add("workflow_context", {k: workflow.get(k) for k in ("name", "purpose", "trigger_conditions")}, yp, f"#/agent/workflows/{yi}")
                for si, step in enumerate(workflow.get("steps", [])):
                    sid = f"step_{si+1:03}"
                    b.add(sid, step, yp, f"#/agent/workflows/{yi}/steps/{si}", "workflow_step")
                    b.unit(sid, sid, "workflow_step")
                for mi, milestone in enumerate(case.get("milestones", [])):
                    sid = f"milestone_{mi+1:03}"
                    b.add(sid, milestone, jp, base + f"/milestones/{mi}", "requirement")
                    b.unit(sid, sid, "milestone_not_extra_action")
                exits = workflow.get("exit_conditions")
                b.add("exit_conditions", exits, yp, f"#/agent/workflows/{yi}/exit_conditions", "completion_requirements")
                b.add("global_plan", agent.get("action_plan", {}), yp, "#/agent/action_plan", "global_requirements")
                b.unit("global_requirements", "global_plan", "global_requirements_not_extra_steps")
                b.add("agent_goal", agent.get("goal", ""), yp, "#/agent/goal")
                used = {name for step in workflow.get("steps", []) for name in step.get("tools_used", [])}
                if isinstance(calls, list):
                    used |= {c["name"] for c in calls}
                elif isinstance(calls, str):
                    # Only top-level call names; nested customer {name: ...} is not a tool.
                    call_ast = ast.parse(calls, mode="eval").body
                    if isinstance(call_ast, ast.List):
                        for call in call_ast.elts:
                            if isinstance(call, ast.Dict):
                                for key, value in zip(call.keys, call.values):
                                    if isinstance(key, ast.Constant) and key.value == "name":
                                        used.add(ast.literal_eval(value))
                missing = sorted(used - set(definitions))
                if missing:
                    b.row["preflight_errors"].append("missing_tool_definitions:" + ",".join(missing))
                if not definitions:
                    b.row["preflight_errors"].append("empty_tool_catalog")
                # Include available choices, not only the answer/reference tool sequence.
                b.add("tool_contracts", definitions, yp, "#/agent/tools", "tool_contracts")
                if not exits or not case.get("milestones") or not case.get("expected_success_outcome"):
                    b.row["preflight_errors"].append("missing_completion_design")
                b.payload["source_notes"] = ["Milestones and reference calls are intended design evidence, not live execution or an authoritative minimal ordered path.",
                                             *b.row["source_quality_flags"], *b.row["preflight_errors"]]
                rows.append(b.finish())
        if mapped != set(ids):
            raise ValueError("Unmapped Python test cases")
    return unique(rows)


def static_tools(path):
    """Extract decorated public contracts, including inheritance, without importing code."""
    result = {}
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                isinstance(d, ast.Call) and ast.unparse(d.func).endswith("is_tool") for d in node.decorator_list):
            if node.name in result:
                raise ValueError("Duplicate native tool contract")
            result[node.name] = {"signature": node.name + "(" + ast.unparse(node.args) + ")",
                                 "returns": ast.unparse(node.returns) if node.returns else None,
                                 "documentation": ast.get_docstring(node) or "",
                                 "decorators": [ast.unparse(d) for d in node.decorator_list]}
    return result


def tau_cases(tau_dir=ROOT / "tau2-bench", domains=("airline", "retail", "telecom"), split="base"):
    root = Path(tau_dir)
    try:
        revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unavailable; exact file hashes retained"
    rows = []
    for domain in domains:
        folder = root / "data/tau2/domains" / domain
        tp, sp = folder / "tasks.json", folder / "split_tasks.json"
        policies = [folder / name for name in (("main_policy.md", "tech_support_manual.md")
                                               if domain == "telecom" else ("policy.md",))]
        task_list = json.loads(tp.read_text())
        byid = {t["id"]: (i, t) for i, t in enumerate(task_list)}
        if len(byid) != len(task_list):
            raise ValueError("Duplicate native task IDs")
        ids = json.loads(sp.read_text())[split]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate IDs in native split")
        contracts, files = {}, []
        for name in ("tools.py", "user_tools.py"):
            path = root / "src/tau2/domains" / domain / name
            if path.exists():
                actor = "user" if name == "user_tools.py" else "assistant"
                contracts[actor] = static_tools(path)
                files.append((path, actor))
        for tid in ids:
            index, task = byid[tid]
            b = CaseBuilder("tau2", domain, tid, None, root)
            b.row["provenance"] = {"benchmark": "tau2-bench", "revision": revision,
                                    "split": split, "split_sha256": file_hash(sp)}
            base = f"#/{index}"
            b.add("scenario", task.get("user_scenario"), tp, base + "/user_scenario", "scenario")
            b.unit("task_requirements", "scenario", "task_requirements")
            b.add("initial_state", task.get("initial_state"), tp, base + "/initial_state", "scenario")
            for pi, policy in enumerate(policies):
                b.add("policy_" + str(pi+1), policy.read_text(), policy, "whole document", "global_requirements")
            b.add("task_design_notes", task.get("description"), tp, base + "/description")
            criteria = task.get("evaluation_criteria") or {}
            endpoint = {k: criteria.get(k) for k in ("actions", "communicate_info", "nl_assertions")}
            b.add("completion_design", endpoint, tp, base + "/evaluation_criteria", "completion_requirements")
            for i, action in enumerate(criteria.get("actions") or []):
                sid = f"reference_{i+1:03}"
                b.add(sid, action, tp, base + f"/evaluation_criteria/actions/{i}", "intended_reference_not_execution")
                b.unit(sid, sid, "reference_action_not_workflow_step")
                actor = action.get("requestor") or "assistant"
                if action["name"] not in contracts.get(actor, {}):
                    b.row["preflight_errors"].append("missing_tool_definition:" + actor + ":" + action["name"])
            for path, actor in files:
                b.add("tools_" + actor, contracts[actor], path, "@is_tool method signatures/docstrings", "tool_contracts")
            # Complex argument types and native state definitions matter to design burden.
            for name in ("data_model.py", "user_data_model.py"):
                path = root / "src/tau2/domains" / domain / name
                if path.exists():
                    b.add("types_" + name[:-3], path.read_text(), path, "whole source; types only", "type_definitions")
            if not task.get("user_scenario") or not any(endpoint.values()):
                b.row["preflight_errors"].append("missing_task_or_completion_requirements")
            b.payload["source_notes"] = ["Native task has no synthetic YAML workflow or milestone list. Do not invent them. Reference actions and completion requirements describe intended design, not observed execution.",
                                          "Full database records are not supplied. Mark unscorable if the case cannot be assessed without them; do not silently treat omitted state as easy.", *b.row["preflight_errors"]]
            rows.append(b.finish())
    return unique(rows)


def unique(rows):
    keys = [(r["dataset"], r["domain"], r["task_id"]) for r in rows]
    if not rows or len(keys) != len(set(keys)) or len({r["payload"]["case_key"] for r in rows}) != len(rows):
        raise ValueError("Empty inventory or duplicate task identity")
    return rows


def verify_sources(rows):
    for row in rows:
        validate_case(row)
        root = Path(row["source_root"]).resolve()
        for source in row["sources"].values():
            path = (root / source["path"]).resolve()
            if not path.is_relative_to(root) or file_hash(path) != source["sha256"]:
                raise ValueError("Changed or escaped source: " + source["path"])


def inventory_summary(rows):
    return {"adapter_version": ADAPTER_VERSION, "n_tasks": len(rows),
            "datasets": dict(Counter(r["dataset"] for r in rows)),
            "domains": dict(Counter(r["dataset"] + "/" + r["domain"] for r in rows)),
            "preflight_blocked": sum(bool(r["preflight_errors"]) for r in rows),
            "source_flagged": sum(bool(r["source_quality_flags"]) for r in rows),
            "api_calls": 0}
