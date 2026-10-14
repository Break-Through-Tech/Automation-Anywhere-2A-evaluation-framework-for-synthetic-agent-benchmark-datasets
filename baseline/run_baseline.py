#!/usr/bin/env python3
"""Run the fixed baseline agent on tau-bench tasks and save pass/fail per trial.

Outputs (in results/baseline/<run_id>/):
  manifest.json  everything needed to reproduce the run (model, params, seed, commits, hashes)
  trials.csv     one row per task x trial, with whether it passed

SAFE BY DEFAULT: runs only --num-tasks tasks (default 2). Pass --full for all tasks.
Check budget/call limits with Sandra before using --full.

Usage:
  python baseline/run_baseline.py --dry-run                  # print commands only
  python baseline/run_baseline.py --domains airline          # 2 tasks, 1 domain
  python baseline/run_baseline.py --num-tasks 10 --num-trials 1   # pilot-sized run
  python baseline/run_baseline.py --full                     # everything (costly)
"""
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "baseline_config.yaml"
RESULTS_ROOT = HERE.parent / "results" / "baseline"

# tau2 CLI flags this script relies on. Verified at startup against `tau2 run --help`
# because flag names can differ between tau2-bench versions.
FLAGS_USED = [
    "--domain", "--agent", "--agent-llm", "--agent-llm-args", "--user-llm",
    "--user-llm-args", "--num-trials", "--num-tasks", "--max-steps", "--seed",
    "--save-to",
]
# Files holding the agent's prompt text; hashed into the manifest so the prompt is pinned.
PROMPT_SOURCE_FILES = ["src/tau2/agent/llm_agent.py"]


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_quiet(cmd, cwd=None):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return None


def pkg_version(name):
    try:
        return metadata.version(name)
    except Exception:
        return None


def build_command(cfg, domain, num_tasks, save_to):
    cmd = [
        *cfg["tau2_cmd"], "run",
        "--domain", domain,
        "--agent", cfg["agent"],
        "--agent-llm", cfg["model"],
        "--agent-llm-args", json.dumps(cfg["decoding"]),
        "--user-llm", cfg["user_model"],
        "--user-llm-args", json.dumps(cfg["user_decoding"]),
        "--num-trials", str(cfg["num_trials"]),
        "--max-steps", str(cfg["max_steps"]),
        "--seed", str(cfg["seed"]),
        "--save-to", save_to,
    ]
    if num_tasks is not None:
        cmd += ["--num-tasks", str(num_tasks)]
    return cmd


def find_results(tau2_repo, save_to):
    """tau2 saves each run as data/simulations/<save_to>/results.json."""
    direct = tau2_repo / "data" / "simulations" / save_to / "results.json"
    if direct.exists():
        return direct
    data_dir = tau2_repo / "data"
    matches = list(data_dir.glob(f"**/{save_to}*/results.json")) + list(data_dir.glob(f"**/{save_to}*.json"))
    if not matches:
        raise FileNotFoundError(
            f"No results found for {save_to} under {data_dir}. "
            "Look in data/simulations/ and check tau2's output."
        )
    return max(matches, key=lambda p: p.stat().st_mtime)


def parse_results(path, domain):
    """Flatten a tau2 simulations file into one row per task x trial.

    ASSUMPTION: each item in data["simulations"] has task_id, trial, and
    reward_info.reward (1.0 = pass). Verify against a real file from your pilot run.
    """
    data = json.loads(Path(path).read_text())
    sims = data.get("simulations", [])
    if not sims:
        raise ValueError(f"No 'simulations' in {path}. Top-level keys: {list(data)}")
    rows = []
    for s in sims:
        reward = (s.get("reward_info") or {}).get("reward")
        rows.append({
            "domain": domain,
            "task_id": s.get("task_id"),
            "trial": s.get("trial"),
            "seed": s.get("seed"),
            "reward": reward,
            "passed": int(reward is not None and reward >= 0.999),
            "termination_reason": s.get("termination_reason"),
            "duration_s": s.get("duration"),
            "agent_cost": s.get("agent_cost"),
            "user_cost": s.get("user_cost"),
        })
    return rows


def write_trials_csv(out_dir, rows):
    with open(out_dir / "trials.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--domains", nargs="+", help="override domains from config")
    ap.add_argument("--num-tasks", type=int, default=2, help="tasks per domain (default 2)")
    ap.add_argument("--num-trials", type=int, help="override num_trials from config")
    ap.add_argument("--full", action="store_true", help="run ALL tasks (costly)")
    ap.add_argument("--run-id", help="name for this run (default: <version>_<timestamp>)")
    ap.add_argument("--parse-results", metavar="PATH",
                    help="don't run anything; convert an existing tau2 results.json (or its folder)\n"
                         "into trials.csv. Use --domains to label the domain (e.g. --domains airline)")
    ap.add_argument("--dry-run", action="store_true", help="print commands, run nothing")
    args = ap.parse_args()

    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    if args.parse_results:
        path = Path(args.parse_results)
        if path.is_dir():
            path = path / "results.json"
        domain = (args.domains or ["unknown"])[0]
        rows = parse_results(path, domain)
        out_dir = RESULTS_ROOT / (args.run_id or f"parsed_{path.parent.name}")
        out_dir.mkdir(parents=True, exist_ok=True)
        write_trials_csv(out_dir, rows)
        (out_dir / "manifest.json").write_text(json.dumps(
            {"parsed_from": str(path), "domain": domain, "baseline_version": cfg["baseline_version"],
             "config": cfg, "config_sha256": sha256_file(CONFIG_PATH)}, indent=2))
        print(f"Saved {len(rows)} trials to {out_dir}/trials.csv "
              f"({sum(r['passed'] for r in rows)} passed)")
        return
    if args.num_trials:
        cfg["num_trials"] = args.num_trials
    domains = args.domains or cfg["domains"]
    num_tasks = None if args.full else args.num_tasks

    tau2_repo = (HERE / cfg["tau2_repo"]).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = args.run_id or f"{cfg['baseline_version']}_{stamp}"
    out_dir = RESULTS_ROOT / run_id

    # Preflight: confirm tau2 exists and supports the flags we use.
    help_text = run_quiet([*cfg["tau2_cmd"], "run", "--help"], cwd=tau2_repo) or ""
    if not help_text:
        msg = f"Could not run `{' '.join(cfg['tau2_cmd'])} run --help` in {tau2_repo}. Is uv installed, did `uv sync` finish, and is tau2_repo correct?"
        if args.dry_run:
            print("WARNING:", msg)
        else:
            sys.exit(msg)
    else:
        missing = [f for f in FLAGS_USED if f not in help_text]
        if missing:
            sys.exit(f"tau2 doesn't list these flags: {missing}. Edit FLAGS_USED/build_command to match `tau2 run --help`.")

    manifest = {
        "run_id": run_id,
        "started_utc": stamp,
        "baseline_version": cfg["baseline_version"],
        "config": cfg,
        "domains": domains,
        "num_tasks_per_domain": "all" if args.full else num_tasks,
        "tau2_git_commit": run_quiet(["git", "rev-parse", "HEAD"], cwd=tau2_repo),
        "prompt_source_sha256": {
            f: sha256_file(tau2_repo / f) for f in PROMPT_SOURCE_FILES if (tau2_repo / f).exists()
        },
        "config_sha256": sha256_file(CONFIG_PATH),
        "versions": {"python": platform.python_version(), "litellm": pkg_version("litellm")},
        "commands": [],
        "result_files": [],
    }

    all_rows = []
    for domain in domains:
        save_to = f"{run_id}_{domain}"
        cmd = build_command(cfg, domain, num_tasks, save_to)
        manifest["commands"].append(" ".join(cmd))
        print(f"\n[{domain}] {' '.join(cmd)}")
        if args.dry_run:
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))  # record survives a crash
        subprocess.run(cmd, cwd=tau2_repo, check=True)
        result_file = find_results(tau2_repo, save_to)
        manifest["result_files"].append(str(result_file))
        all_rows += parse_results(result_file, domain)

    if args.dry_run:
        print("\nDry run only. Nothing was run.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    write_trials_csv(out_dir, all_rows)

    print(f"\nSaved {len(all_rows)} trials to {out_dir}/trials.csv")
    for d in domains:
        rs = [r for r in all_rows if r["domain"] == d]
        if rs:
            print(f"  {d}: {sum(r['passed'] for r in rs)}/{len(rs)} trials passed")


if __name__ == "__main__":
    main()
