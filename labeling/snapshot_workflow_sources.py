"""Save the tau2 metadata needed for workflow labeling from a pinned checkout.

python labeling/snapshot_workflow_sources.py --tau2-root path/to/tau2-bench
The normal label build uses the saved snapshot and does not need a checkout.
"""

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVISION = "dd8757d4c8791dad7b3cdaf02a105a3d5f9d86bd"
DESTINATION = ROOT / "labeling/workflow_sources/tau2"
POLICIES = [
    "LICENSE",
    "src/tau2/agent/llm_agent.py",
    "data/tau2/domains/retail/policy.md",
    "data/tau2/domains/airline/policy.md",
    "data/tau2/domains/telecom/main_policy.md",
    "data/tau2/domains/telecom/tech_support_manual.md",
    "data/tau2/domains/telecom/tech_support_workflow.md",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(source, destination=DESTINATION):
    # A downloaded source bundle must match the saved pinned file hashes.
    existing = destination / "manifest.json"
    expected = json.loads(existing.read_text())["original_files"] if existing.exists() else None
    if expected is None:
        revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        if revision != REVISION:
            raise ValueError(f"Expected tau2 revision {REVISION}, found {revision}")
    tasks = [json.loads(line) for line in (ROOT / "data/processed/tasks.jsonl").read_text().splitlines()]
    metadata, conditions, originals, copies = [], {}, {}, {}

    def read(path):
        data = (source / path).read_bytes()
        if expected is not None and digest(data) != expected[path]["sha256"]:
            raise ValueError(f"{path}: source differs from the pinned snapshot")
        originals[path] = {"sha256": digest(data), "url":
                           f"https://github.com/sierra-research/tau2-bench/blob/{REVISION}/{path}"}
        return data

    for domain in ("airline", "retail", "telecom"):
        path = f"data/tau2/domains/{domain}/tasks.json"
        raw = {t["id"]: t for t in json.loads(read(path))}
        split = json.loads(read(f"data/tau2/domains/{domain}/split_tasks.json"))["base"]
        selected = [t for t in tasks if t["dataset"] == "tau2" and t["domain"] == domain]
        if set(split) != {t["task_id"] for t in selected}:
            raise ValueError(f"{domain}: base split does not match the committed tasks")
        for task in selected:
            original = raw[task["task_id"]]
            instructions = original["user_scenario"]["instructions"]
            actions = [{"name": a["name"], "arguments": a.get("arguments") or {},
                        "requestor": a.get("requestor") or "assistant"}
                       for a in original["evaluation_criteria"].get("actions") or []]
            if task["description"] != instructions["reason_for_call"].strip() or task["actions"] != actions:
                raise ValueError(f"{domain}:{task['task_id']}: source differs from committed task")
            metadata.append({"domain": domain, "task_id": task["task_id"],
                             "description": original["description"],
                             "instructions": instructions, "actions": actions,
                             "source": originals[path]["url"]})

    for name in ("service_issues", "mobile_data_issues", "mms_issues"):
        path = f"src/tau2/domains/telecom/tasks/{name}.py"
        data = read(path)
        for node in ast.walk(ast.parse(data)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "BaseTask"):
                continue
            values = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords
                      if kw.arg in ("name", "description")}
            conditions[values["name"]] = {"description": values["description"],
                                          "source": originals[path]["url"] + f"#L{node.lineno}"}

    for path in POLICIES:
        copies[path] = read(path)
    metadata.sort(key=lambda t: (t["domain"], t["task_id"]))
    generated = {
        "tasks.jsonl": "".join(json.dumps(t, ensure_ascii=False, sort_keys=True) + "\n" for t in metadata).encode(),
        "conditions.json": (json.dumps(conditions, indent=2, sort_keys=True) + "\n").encode(),
    }
    generated.update({"policy/" + path: data for path, data in copies.items()})
    manifest = {"repository": "sierra-research/tau2-bench", "revision": REVISION,
                "split": "base", "task_count": len(metadata), "original_files": originals,
                "snapshot_sha256": {path: digest(data) for path, data in generated.items()}}
    destination.mkdir(parents=True, exist_ok=True)
    for path, data in generated.items():
        output = destination / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Saved metadata for {len(metadata)} tau2 tasks to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau2-root", type=Path, required=True)
    args = parser.parse_args()
    snapshot(args.tau2_root)
