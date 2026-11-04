#!/usr/bin/env python3
"""Run the fixed v2 ReAct baseline on the supplied synthetic mock tools.

python baseline/run_synthetic_baseline.py --num-tasks 2 --num-trials 1
python baseline/run_synthetic_baseline.py --full --run-id v2_synthetic_full
python baseline/run_synthetic_baseline.py --full --run-id v2_synthetic_full --resume

Uses the exact saved v2 ReAct prompt template and its model/decoding settings.
The synthetic evaluator is a trajectory/structured-outcome proxy, not a tau2
database evaluator. Invalid references and API errors have no numeric reward.
"""
import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import json
import os
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI, APIError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from baseline.compute_difficulty import run as compute_empirical
from baseline.synthetic_environment import (
    END_TOOLS, TOOL_LOCK, evaluate_trajectory, execute, load_cases, reference_preflight, tools_for,
)

ACTION_RE = re.compile(r"Action:\s*(\{.*\})", re.DOTALL)
STOP_TOKENS = ("###STOP###", "###TRANSFER###", "###OUT-OF-SCOPE###")
EVALUATOR_VERSION = "synthetic_reference_v2_schema_compat"
CONFIG = ROOT / "baseline/baseline_config.yaml"
PROMPT = ROOT / "results/baseline/v2_full/prompt.txt"
USER_GUIDELINES = ROOT / "baseline/synthetic_user_guidelines.md"
COLUMNS = ["domain", "task_id", "trial", "seed", "reward", "passed", "termination_reason",
           "evaluation_status", "steps", "duration_s", "agent_calls", "user_calls",
           "agent_prompt_tokens", "agent_completion_tokens", "user_prompt_tokens", "user_completion_tokens",
           "agent_cost", "user_cost", "trace_file"]


def parse_action(text):
    """Same parser as baseline/react_agent.py; tested against that implementation."""
    match = ACTION_RE.search(text or "")
    if not match:
        return None
    raw = match.group(1).strip()
    for end in range(len(raw), 0, -1):
        if raw[end - 1] != "}":
            continue
        try:
            action = json.loads(raw[:end])
        except json.JSONDecodeError:
            continue
        if isinstance(action, dict) and isinstance(action.get("name"), str):
            if not isinstance(action.get("arguments"), dict):
                action["arguments"] = {}
            return action
    return None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(message):
    with TOOL_LOCK:
        print(message, flush=True)


class CompletionClient:
    def __init__(self, config):
        load_dotenv(ROOT / ".env")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                             base_url=os.getenv("BASE_URL") or os.getenv("OPENAI_BASE_URL"),
                             timeout=90, max_retries=2)
        self.config = config

    def complete(self, messages, side):
        model = self.config["model" if side == "agent" else "user_model"]
        decoding = self.config["decoding" if side == "agent" else "user_decoding"]
        # Do not pass a sampling seed: tau2's v2 generate() does not pass one.
        response = self.client.chat.completions.create(model=model, messages=messages, **decoding)
        choice = response.choices[0]
        usage = response.usage.model_dump() if response.usage else {}
        return choice.message.content or "", {
            "side": side, "request_id": response.id, "model": response.model,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "usage": usage, "finish_reason": choice.finish_reason,
        }


def trial(domain, case, number, seed, config, client, reference_issues, write_tools):
    start = time.perf_counter()
    instance = case()
    tools, schemas = tools_for(instance)
    definition = yaml.safe_load((ROOT / "data" / domain / "agent_definition.yaml").read_text())["agent"]
    policy = yaml.safe_dump({k: definition[k] for k in ("role", "goal", "action_plan")}, sort_keys=False)
    prompt = PROMPT.read_text().replace("{domain_policy}", policy).replace("{tools}", json.dumps(schemas, indent=2))
    agent_history = [{"role": "system", "content": prompt}]
    # The simulated customer knows only the narrative and supplied input, never
    # expected_tool_calls, milestones, expected outputs, or tool implementation.
    scenario = json.dumps({"title": case.title, "description": case.description,
                           "input_data": case.input_data}, ensure_ascii=False)
    user_prompt = USER_GUIDELINES.read_text().replace("<PERSONA_GUIDELINES>", "") + "\n\n<scenario>\n" + scenario + "\n</scenario>"
    user_history = [{"role": "system", "content": user_prompt},
                    {"role": "user", "content": "Hi! How can I help you today?"}]
    events, calls, conversation = [], [], []
    reason, steps, infrastructure_error = "max_steps", 0, None

    def complete(history, side):
        text, info = client.complete(history, side)
        calls.append(info)
        return text

    try:
        user_text = complete(user_history, "user")
        user_history.append({"role": "assistant", "content": user_text})
        agent_history.append({"role": "user", "content": "User: " + user_text})
        conversation.append({"role": "user", "content": user_text})
        while steps < config["max_steps"]:
            if any(token in user_text for token in STOP_TOKENS):
                reason = "user_stop"
                break
            text = complete(agent_history, "agent")
            steps += 1
            agent_history.append({"role": "assistant", "content": text or "(empty)"})
            conversation.append({"role": "assistant", "content": text})
            action = parse_action(text)
            if action is not None and action["name"] != "respond":
                event = execute(tools, action)
                events.append(event)
                steps += 1
                prefix = "Tool error: " if event["error"] else "Tool output: "
                agent_history.append({"role": "user", "content": prefix + json.dumps(event["output"])})
                if action["name"] in END_TOOLS and not event["error"]:
                    reason = "workflow_terminal"
                    break
            else:
                content = text if action is None else str(action["arguments"].get("content", "")) or text
                if steps >= config["max_steps"]:
                    break
                user_history.append({"role": "user", "content": content})
                user_text = complete(user_history, "user")
                user_history.append({"role": "assistant", "content": user_text})
                agent_history.append({"role": "user", "content": "User: " + user_text})
                conversation.append({"role": "user", "content": user_text})
                steps += 1
    except APIError as exc:
        infrastructure_error = {"type": type(exc).__name__, "status_code": getattr(exc, "status_code", None),
                                "code": getattr(exc, "code", None)}
        # Do not serialize SDK exceptions: they can include request headers.
        reason = "api_error"
    evaluation = evaluate_trajectory(case, events, write_tools, reference_issues)
    if infrastructure_error:
        evaluation = {"reward": None, "status": "infrastructure_error", "error": infrastructure_error}
    reward = evaluation["reward"]
    row = dict(domain=domain, task_id=case.test_case_id, trial=number, seed=seed,
               reward=reward, passed=int(reward == 1), termination_reason=reason,
               evaluation_status=evaluation["status"], steps=steps,
               duration_s=round(time.perf_counter() - start, 4), agent_cost=None, user_cost=None)
    for side in ("agent", "user"):
        side_calls = [c for c in calls if c["side"] == side]
        row[f"{side}_calls"] = len(side_calls)
        for kind in ("prompt", "completion"):
            row[f"{side}_{kind}_tokens"] = sum(c["usage"].get(f"{kind}_tokens", 0) for c in side_calls)
    trace = {"domain": domain, "task_id": case.test_case_id, "trial": number, "seed": seed,
             "agent_prompt": prompt, "user_prompt": user_prompt, "conversation": conversation,
             "tool_events": events, "api_calls": calls, "evaluation": evaluation}
    return row, trace


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full", action="store_true", help="Run all 64 synthetic tasks")
    ap.add_argument("--num-tasks", type=int, default=2)
    ap.add_argument("--num-trials", type=int)
    ap.add_argument("--run-id", default="v2_synthetic_full")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--preflight-only", action="store_true", help="Check fixtures; make no API calls")
    args = ap.parse_args()
    if Path(args.run_id).name != args.run_id:
        ap.error("run-id must be a directory name")
    config = yaml.safe_load(CONFIG.read_text())
    n = args.num_trials if args.num_trials is not None else config["num_trials"]
    if n < 1 or args.num_tasks < 1:
        ap.error("Task and trial counts must be positive")
    cases = load_cases()
    if not args.full:
        cases = cases[:args.num_tasks]
    issues = {(d, cls.test_case_id): reference_preflight(cls) for d, cls in cases}
    out = ROOT / "results/baseline" / args.run_id
    report = [{"domain": d, "task_id": cls.test_case_id, "issues": issues[(d, cls.test_case_id)]}
              for d, cls in cases if issues[(d, cls.test_case_id)]]
    emit(f"Preflight: {len(cases)} tasks; {len(report)} have invalid references")
    if args.preflight_only:
        print(json.dumps(report, indent=2))
        return 0
    sources = [CONFIG, PROMPT, USER_GUIDELINES, Path(__file__), ROOT / "baseline/synthetic_environment.py",
               ROOT / "difficulty/synthetic_tool_labels.csv"]
    for d in sorted({d for d, _ in cases}):
        sources.extend([ROOT / "data" / d / "test_cases.py", ROOT / "data" / d / "agent_definition.yaml"])
    fingerprint = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    rng = random.Random(config["seed"])
    planned = [(d, cls, i, rng.randint(0, 1_000_000)) for d, cls in cases for i in range(n)]
    manifest = {"baseline_version": config["baseline_version"], "config": config,
                "adapter": EVALUATOR_VERSION, "dataset": "synthetic", "run_id": args.run_id,
                "task_count": len(cases), "num_trials": n, "planned_trials": len(planned),
                "sources": fingerprint, "openai_version": metadata.version("openai"),
                "limitations": ["Trajectory/structured-outcome oracle differs from tau2 database evaluation.",
                                 "Expected calls/structured inputs are exact; descriptive text may be paraphrased.",
                                 "Invalid reference tasks and infrastructure failures have no numeric reward.",
                                 "Costs are unavailable from this endpoint; actual token usage is recorded.",
                                 "HUMAN_IN_THE_LOOP returns a fixed acknowledgement."],
                "started_utc": datetime.now(timezone.utc).isoformat()}
    rows = []
    if out.exists():
        if not args.resume:
            ap.error(f"{out} exists; choose a new run-id or use --resume")
        previous = json.loads((out / "manifest.json").read_text())
        if any(previous[k] != manifest[k] for k in ("config", "sources", "planned_trials", "task_count")):
            ap.error("Cannot resume: configuration, sources, or trial plan changed")
        manifest = previous
        if (out / "trials.csv").exists():
            with (out / "trials.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "reference_preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "prompt.txt").write_text(PROMPT.read_text())
    (out / "user_guidelines.txt").write_text(USER_GUIDELINES.read_text())
    seen = {(r["domain"], r["task_id"], int(r["trial"])) for r in rows}
    if len(seen) != len(rows):
        ap.error("Duplicate existing trial identities")
    write_tools = set()
    with (ROOT / "difficulty/synthetic_tool_labels.csv").open(newline="") as handle:
        write_tools = {r["tool"] for r in csv.DictReader(handle) if r["label"] == "write"}
    client = CompletionClient(config)
    jobs = [job for job in planned if (job[0], job[1].test_case_id, job[2]) not in seen]
    emit(f"Running {len(jobs)} new trials on {config['model']}; concurrency={config['max_concurrency']}")
    def work(job):
        d, cls, i, seed = job
        return trial(d, cls, i, seed, config, client, issues[(d, cls.test_case_id)], write_tools)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_concurrency"]) as pool:
        futures = [pool.submit(work, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            row, trace = future.result()
            relative = Path("traces") / row["domain"] / f"{row['task_id']}_trial{row['trial']}.json.gz"
            path = out / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(json.dumps(trace, ensure_ascii=False).encode(), mtime=0))
            row["trace_file"] = str(relative)
            rows.append(row)
            rows.sort(key=lambda r: (r["domain"], r["task_id"], int(r["trial"])))
            temporary = out / "trials.csv.tmp"
            with temporary.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            temporary.replace(out / "trials.csv")
            emit(f"[{len(rows)}/{len(planned)}] {row['domain']}/{row['task_id']} trial={row['trial']} "
                 f"{row['evaluation_status']} ({row['duration_s']:.1f}s)")
    summary = compute_empirical([out / "trials.csv"], out / "difficulty")
    manifest["completed_trials"] = len(rows)
    manifest["evaluation_status_counts"] = dict(Counter(r["evaluation_status"] for r in rows))
    manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    emit(json.dumps(manifest["evaluation_status_counts"], indent=2))
    emit(f"Saved trials, traces, and empirical scores in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
