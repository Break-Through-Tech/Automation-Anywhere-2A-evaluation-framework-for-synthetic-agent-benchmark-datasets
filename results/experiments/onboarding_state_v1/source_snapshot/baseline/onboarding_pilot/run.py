"""Run the isolated six-scenario stateful onboarding pilot (24 baseline trials).

python -m baseline.onboarding_pilot.run --validate-only
python -m baseline.onboarding_pilot.run --limit-trials 2
python -m baseline.onboarding_pilot.run --resume
python -m baseline.onboarding_pilot.run --regrade
"""
import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import json
import random
import time
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import yaml
from openai import APIError

from baseline import run_synthetic_baseline as protocol
from baseline.onboarding_pilot.environment import OnboardingEnvironment
from baseline.onboarding_pilot.grader import grade_state
from baseline.onboarding_pilot.validation import CASES, load_fixtures, validate_pilot
from baseline.synthetic_environment import END_TOOLS, execute, tools_for

ROOT = protocol.ROOT
HERE = Path(__file__).resolve().parent
DATASET_VERSION = "onboarding_state_pilot_v1"
EVALUATOR_VERSION = "onboarding_business_outcomes_v1"
POLICY = HERE / "policy.md"
COLUMNS = ["dataset", "domain", "task_id", "source_task_id", "trial", "seed", "reward", "passed",
           "evaluation_status", "termination_reason", "steps", "duration_s", "agent_calls", "user_calls",
           "agent_prompt_tokens", "agent_completion_tokens", "user_prompt_tokens", "user_completion_tokens",
           "failed_checks", "trace_file"]


def run_trial(fixture, number, seed, config, client):
    start = time.perf_counter()
    env = OnboardingEnvironment(fixture)
    tools, schemas = tools_for(env)
    prompt = protocol.PROMPT.read_text().replace("{domain_policy}", POLICY.read_text()).replace("{tools}", json.dumps(schemas, indent=2))
    greeting = "Hi! How can I help you today?"
    agent = [{"role": "system", "content": prompt},
             {"role": "assistant", "content": "Action:\n" + json.dumps({"name": "respond", "arguments": {"content": greeting}})}]
    # Fixtures, risk outcomes, grading checks, and validation plans are NOT
    # included in either model's prompt. Facts are retrieved through tools.
    scenario = {"title": fixture["title"], "description": fixture["description"],
                "input_data": fixture["application"]}
    user_prompt = protocol.USER_GUIDELINES.read_text() + "\n\n<scenario>\n" + json.dumps(scenario) + "\n</scenario>"
    user = [{"role": "system", "content": user_prompt}, {"role": "user", "content": greeting}]
    events, calls, conversation = [], [], []
    steps, reason, error = 0, "max_steps", None
    def complete(history, side):
        text, info = client.complete(history, side)
        calls.append(info)
        return text
    try:
        user_text = complete(user, "user")
        user.append({"role": "assistant", "content": user_text})
        agent.append({"role": "user", "content": "User: " + user_text})
        conversation.append({"role": "user", "content": user_text})
        while steps < config["max_steps"]:
            if any(token in user_text for token in protocol.STOP_TOKENS):
                reason = "user_stop"
                break
            text = complete(agent, "agent")
            steps += 1
            agent.append({"role": "assistant", "content": text or "(empty)"})
            conversation.append({"role": "assistant", "content": text})
            action = protocol.parse_action(text)
            if action is not None and action["name"] != "respond":
                if steps >= config["max_steps"]:
                    break
                event = execute(tools, action)
                events.append(event)
                steps += 1
                prefix = "Tool error: " if event["error"] else "Tool output: "
                agent.append({"role": "user", "content": prefix + json.dumps(event["output"])})
                if action["name"] in END_TOOLS and not event["error"]:
                    reason = "workflow_terminal"
                    break
            else:
                if steps >= config["max_steps"]:
                    break
                content = text if action is None else str(action["arguments"].get("content", "")) or text
                user.append({"role": "user", "content": content})
                user_text = complete(user, "user")
                user.append({"role": "assistant", "content": user_text})
                agent.append({"role": "user", "content": "User: " + user_text})
                conversation.append({"role": "user", "content": user_text})
                steps += 1
    except APIError as exc:
        error = {"type": type(exc).__name__, "status_code": getattr(exc, "status_code", None), "code": getattr(exc, "code", None)}
        reason = "api_error"
    state = env._snapshot()
    grade = grade_state(fixture, state)
    if error:
        grade = {"reward": None, "checks": grade["checks"], "failed_checks": grade["failed_checks"], "api_error": error}
    status = "infrastructure_error" if error else "passed_outcome" if grade["reward"] == 1 else "failed_outcome"
    row = {"dataset": DATASET_VERSION, "domain": "banking_customer_onboarding",
           "task_id": f"{DATASET_VERSION}::{fixture['task_id']}", "source_task_id": fixture["task_id"],
           "trial": number, "seed": seed, "reward": grade["reward"], "passed": int(grade["reward"] == 1),
           "evaluation_status": status, "termination_reason": reason, "steps": steps,
           "duration_s": round(time.perf_counter() - start, 4), "failed_checks": "|".join(grade["failed_checks"])}
    for side in ("agent", "user"):
        selected = [c for c in calls if c["side"] == side]
        row[f"{side}_calls"] = len(selected)
        for kind in ("prompt", "completion"):
            row[f"{side}_{kind}_tokens"] = sum(c["usage"].get(f"{kind}_tokens", 0) for c in selected)
    trace = {"dataset_version": DATASET_VERSION, "evaluator_version": EVALUATOR_VERSION,
             "source_task_id": fixture["task_id"], "trial": number, "seed": seed,
             "agent_prompt": prompt, "user_prompt": user_prompt, "conversation": conversation,
             "tool_events": events, "api_calls": calls, "final_state": state, "evaluation": grade}
    return row, trace


def write_csv(path, rows, columns):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def score_saved(out, data, rows):
    per_task = []
    for fixture in data["cases"]:
        selected = [r for r in rows if r["source_task_id"] == fixture["task_id"]]
        valid = [r for r in selected if r["reward"] not in (None, "", "None")]
        passed = sum(int(r["passed"]) for r in valid)
        per_task.append({"dataset_version": DATASET_VERSION, "source_task_id": fixture["task_id"],
                         "n_trials": len(selected), "n_valid": len(valid), "c_passed": passed,
                         "difficulty": 1 - passed / len(valid) if valid else None})
    write_csv(out / "empirical_difficulty.csv", per_task, list(per_task[0]))
    scored = [r["difficulty"] for r in per_task if r["difficulty"] is not None]
    summary = {"dataset_version": DATASET_VERSION, "evaluator_version": EVALUATOR_VERSION,
               "status": "complete" if len(rows) == 24 and all(r["n_valid"] == 4 for r in per_task) else "incomplete",
               "tasks": 6, "planned_trials": 24, "recorded_trials": len(rows),
               "tasks_scored": len(scored), "passed_trials": sum(int(r["passed"]) for r in rows if r["reward"] not in (None, "", "None")),
               "status_counts": dict(Counter(r["evaluation_status"] for r in rows)),
               "mean_empirical_difficulty": sum(scored) / len(scored) if scored else None,
               "scope": "Six revised controlled onboarding scenarios; not original synthetic benchmark scores.",
               "limitations": ["Pilot uses independent state assertions inspired by tau2, not tau2's evaluator implementation.",
                               "Fixtures and simulated services were revised; original traces cannot be regraded as these tasks.",
                               "AML results and follow-up uploads are simulated fixture services; free-text message meaning is not graded.",
                               "Team review of business rules and broader negative scenarios is needed before scaling."]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/pilots/onboarding_state_v1")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--limit-trials", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--regrade", action="store_true", help="Verify stored rewards from final states; make no API calls")
    args = parser.parse_args()
    validation = validate_pilot()
    data = load_fixtures()
    if args.validate_only:
        print(f"PASS: {len(validation)} known-valid workflows across six scenarios; no API calls")
        return 0
    if args.limit_trials is not None and args.limit_trials < 1:
        parser.error("limit-trials must be positive")
    out = args.output_dir
    config = yaml.safe_load(protocol.CONFIG.read_text())
    files = [CASES, POLICY, HERE / "environment.py", HERE / "grader.py", HERE / "validation.py", Path(__file__),
             protocol.CONFIG, protocol.PROMPT, protocol.USER_GUIDELINES,
             ROOT / "baseline/run_synthetic_baseline.py", ROOT / "baseline/synthetic_environment.py"]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest = {"dataset_version": DATASET_VERSION, "evaluator_version": EVALUATOR_VERSION,
                "baseline_config": config, "sources": hashes, "planned_trials": 24,
                "packages": {name: metadata.version(name) for name in ("openai", "pydantic", "PyYAML")},
                "started_utc": datetime.now(timezone.utc).isoformat()}
    rows = []
    if out.exists():
        if not (args.resume or args.regrade):
            parser.error("Output exists; use --resume, --regrade, or a new output directory")
        previous = json.loads((out / "manifest.json").read_text())
        if previous["sources"] != hashes or previous["baseline_config"] != config:
            parser.error("Pilot sources/configuration changed; use a new version/output directory")
        manifest = previous
        with (out / "trials.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif args.resume or args.regrade:
        parser.error("No saved pilot exists")
    out.mkdir(parents=True, exist_ok=True)
    if args.regrade:
        fixtures = {f["task_id"]: f for f in data["cases"]}
        for row in rows:
            trace = json.loads(gzip.decompress((out / row["trace_file"]).read_bytes()))
            if row["evaluation_status"] == "infrastructure_error":
                continue
            grade = grade_state(fixtures[row["source_task_id"]], trace["final_state"])
            if grade != trace["evaluation"] or str(grade["reward"]) != str(row["reward"]):
                raise ValueError("Stored state and recorded reward disagree")
        (out / "regrade_verification.json").write_text(json.dumps({"trials_verified": len(rows), "rewards_identical": True}, indent=2) + "\n")
        print(f"PASS: reproduced rewards for {len(rows)} saved trials without API calls")
        return 0
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    (out / "policy.md").write_text(POLICY.read_text())
    seen = {(r["source_task_id"], int(r["trial"])) for r in rows}
    if len(seen) != len(rows):
        raise ValueError("Duplicate pilot trial identities")
    rng = random.Random(config["seed"])
    planned = [(f, i, rng.randint(0, 1_000_000)) for i in range(4) for f in data["cases"]]
    jobs = [j for j in planned if (j[0]["task_id"], j[1]) not in seen]
    if args.limit_trials:
        jobs = jobs[:args.limit_trials]
    protocol.emit(f"Stateful pilot: {len(jobs)} new trials; {len(rows)}/24 saved; model={config['model']}")
    client = protocol.CompletionClient(config)
    def work(job):
        return run_trial(job[0], job[1], job[2], config, client)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_concurrency"]) as pool:
        for future in concurrent.futures.as_completed([pool.submit(work, job) for job in jobs]):
            row, trace = future.result()
            relative = Path("traces") / f"{row['source_task_id']}_trial{row['trial']}.json.gz"
            path = out / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(json.dumps(trace).encode(), mtime=0))
            row["trace_file"] = str(relative)
            rows.append(row)
            rows.sort(key=lambda r: (r["source_task_id"], int(r["trial"])))
            write_csv(out / "trials.csv", rows, COLUMNS)
            protocol.emit(f"[{len(rows)}/24] {row['source_task_id']} trial={row['trial']} {row['evaluation_status']}")
    summary = score_saved(out, data, rows)
    manifest["completed_trials"] = len(rows)
    manifest["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    protocol.emit(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
