#!/usr/bin/env python3
"""
Load tau2-bench and the synthetic dataset into one task format so the same
metric code runs on both.

Every task is a dict:
    dataset      "tau2" or "synthetic"
    domain       e.g. "retail", "banking_fraud_monitoring"
    task_id      unique within (dataset, domain)
    description  short natural-language statement of the task (for embeddings)
    actions      ground-truth tool calls in order: [{"name", "arguments", "requestor"}]
                 requestor is "assistant" or "user" (only telecom has user actions)
    meta         dataset-specific extras (workflow / difficulty label / title, or reward_basis)

Usage:
    from loaders import load_tasks
    tasks = load_tasks()                      # both datasets
    tasks = load_tasks(datasets=["synthetic"])

    python data/loaders.py                    # writes data/processed/tasks.jsonl
"""

import importlib.util
import json
import sys
import types
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
REPO_DIR = DATA_DIR.parent
# Same location baseline/baseline_config.yaml uses (tau2_repo: ../tau2-bench from baseline/)
TAU2_DIR = REPO_DIR / "tau2-bench"

TAU2_DOMAINS = ["retail", "airline", "telecom"]
SYNTHETIC_DOMAINS = [
    "banking_accounts_deposits",
    "banking_customer_onboarding",
    "banking_fraud_monitoring",
    "healthcare_patient_onboarding",
    "healthcare_prior_authorization",
    "insurance_claims_intake",
    "manufacturing_purchase_to_pay",
]
# Terminal status signals in the synthetic data; tau2 has no equivalent, so they are not actions.
# HUMAN_IN_THE_LOOP is kept: it is the counterpart of tau2's transfer_to_human_agents.
STATUS_TOOLS = {"SUCCESS", "FAILED", "CANCELLED"}


def load_tau2(domains=TAU2_DOMAINS, tau2_dir=TAU2_DIR, split="base"):
    """Load tau2-bench tasks. "base" is the split `tau2 run` uses by default."""
    domains_dir = Path(tau2_dir) / "data" / "tau2" / "domains"
    if not domains_dir.exists():
        raise FileNotFoundError(
            f"{domains_dir} not found. Clone it from the repo root:\n"
            "  git clone https://github.com/sierra-research/tau2-bench.git"
        )

    tasks = []
    for domain in domains:
        by_id = {t["id"]: t for t in json.loads((domains_dir / domain / "tasks.json").read_text())}
        ids = json.loads((domains_dir / domain / "split_tasks.json").read_text())[split]
        for task_id in ids:
            t = by_id[task_id]
            criteria = t.get("evaluation_criteria") or {}
            tasks.append({
                "dataset": "tau2",
                "domain": domain,
                "task_id": task_id,
                "description": t["user_scenario"]["instructions"]["reason_for_call"].strip(),
                "actions": [
                    {
                        "name": a["name"],
                        "arguments": a.get("arguments") or {},
                        "requestor": a.get("requestor") or "assistant",
                    }
                    for a in criteria.get("actions") or []
                ],
                "meta": {"reward_basis": criteria.get("reward_basis")},
            })
    return tasks


def _test_case_classes(path):
    """Import a test_cases.py and return its TestCase* classes.

    The real system_tools_base builds a ChatOpenAI client on import (needs langchain + an
    API key), so a stub base class stands in while loading. Only class attributes are read.
    """
    stubbed = "system_tools_base" not in sys.modules
    if stubbed:
        stub = types.ModuleType("system_tools_base")
        stub.SystemToolsBaseClass = object
        sys.modules["system_tools_base"] = stub
    try:
        spec = importlib.util.spec_from_file_location(f"_synthetic_{path.parent.name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if stubbed:
            del sys.modules["system_tools_base"]
    # vars() keeps definition order
    return [c for name, c in vars(module).items() if name.startswith("TestCase") and isinstance(c, type)]


def load_synthetic(domains=SYNTHETIC_DOMAINS, data_dir=DATA_DIR):
    """Load the Automation Anywhere synthetic test cases from data/<domain>/test_cases.py."""
    tasks = []
    for domain in domains:
        for cls in _test_case_classes(Path(data_dir) / domain / "test_cases.py"):
            tasks.append({
                "dataset": "synthetic",
                "domain": domain,
                "task_id": cls.test_case_id,
                # docstring = title + rationale, the closest match to tau2's reason_for_call
                "description": " ".join((cls.__doc__ or "").split()),
                "actions": [
                    {"name": c["name"], "arguments": c.get("tool_inputs") or {}, "requestor": "assistant"}
                    for c in cls.expected_tool_calls
                    if c["name"] not in STATUS_TOOLS
                ],
                "meta": {
                    "workflow": getattr(cls, "workflow", None),
                    "title": getattr(cls, "title", None),
                    # class names end in _easy / _medium / _hard
                    "difficulty_label": cls.__name__.rsplit("_", 1)[-1],
                },
            })
    return tasks


def load_tasks(datasets=("tau2", "synthetic")):
    """Load the requested datasets in the unified format."""
    loaders = {"tau2": load_tau2, "synthetic": load_synthetic}
    return [task for name in datasets for task in loaders[name]()]


if __name__ == "__main__":
    tasks = load_tasks()

    # self-check: shape is identical across datasets and ids are unique
    keys = {"dataset", "domain", "task_id", "description", "actions", "meta"}
    assert all(set(t) == keys for t in tasks)
    assert all(t["description"] for t in tasks)  # actions may be [] (tau2 refusal tasks)
    ids = [(t["dataset"], t["domain"], t["task_id"]) for t in tasks]
    assert len(ids) == len(set(ids)), "duplicate task ids"

    out = DATA_DIR / "processed" / "tasks.jsonl"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")

    counts = {}
    for t in tasks:
        counts[(t["dataset"], t["domain"])] = counts.get((t["dataset"], t["domain"]), 0) + 1
    for (dataset, domain), n in sorted(counts.items()):
        print(f"{dataset:10} {domain:32} {n:4}")
    print(f"Wrote {len(tasks)} tasks to {out}")
