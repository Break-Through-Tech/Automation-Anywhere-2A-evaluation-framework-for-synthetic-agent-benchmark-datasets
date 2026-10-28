#!/usr/bin/env python3
"""Retry only synthetic infrastructure failures; preserve every original error trace.

python baseline/retry_synthetic_errors.py --run-dir results/baseline/v2_synthetic_full
"""
import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from baseline import run_synthetic_baseline as runner
from baseline.synthetic_environment import load_cases, reference_preflight


def retry(run_dir):
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest["sources"].items():
        if runner.digest(ROOT / name) != expected:
            raise ValueError(f"Refusing retry with changed source: {name}")
    with (run_dir / "trials.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    failed = [r for r in rows if r["evaluation_status"] == "infrastructure_error"]
    if not failed:
        runner.emit("No infrastructure errors to retry")
        return
    round_number = len(manifest.get("retry_rounds", [])) + 1
    archive = run_dir / "retries" / f"round{round_number:03d}"
    archive.mkdir(parents=True)
    shutil.copy2(run_dir / "trials.csv", archive / "trials_before.csv")
    for row in failed:
        destination = archive / row["trace_file"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_dir / row["trace_file"], destination)
    info = {"round": round_number, "trials_retried": len(failed),
            "original_errors": str(archive.relative_to(run_dir)),
            "source_sha256": runner.digest(Path(__file__)),
            "started_utc": datetime.now(timezone.utc).isoformat()}
    manifest.setdefault("retry_rounds", []).append(info)
    manifest["completed_trials"] = len(rows) - len(failed)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    cases = {(d, c.test_case_id): c for d, c in load_cases()}
    with (ROOT / "difficulty/synthetic_tool_labels.csv").open(newline="") as handle:
        writes = {r["tool"] for r in csv.DictReader(handle) if r["label"] == "write"}
    client = runner.CompletionClient(manifest["config"])
    indices = {(r["domain"], r["task_id"], int(r["trial"])): i for i, r in enumerate(rows)}
    def work(row):
        case = cases[(row["domain"], row["task_id"])]
        return runner.trial(row["domain"], case, int(row["trial"]), int(row["seed"]),
                            manifest["config"], client, reference_preflight(case), writes)
    with concurrent.futures.ThreadPoolExecutor(max_workers=manifest["config"]["max_concurrency"]) as pool:
        futures = [pool.submit(work, row) for row in failed]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row, trace = future.result()
            index = indices[(row["domain"], row["task_id"], int(row["trial"]))]
            row["trace_file"] = rows[index]["trace_file"]
            path = run_dir / row["trace_file"]
            path.write_bytes(gzip.compress(json.dumps(trace, ensure_ascii=False).encode(), mtime=0))
            rows[index] = row
            temporary = run_dir / "trials.csv.tmp"
            with temporary.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=runner.COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            temporary.replace(run_dir / "trials.csv")
            runner.emit(f"Retry {completed}/{len(failed)}: {row['task_id']} "
                        f"trial={row['trial']} {row['evaluation_status']}")
    runner.compute_empirical([run_dir / "trials.csv"], run_dir / "difficulty")
    info["completed_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["completed_trials"] = len(rows)
    manifest["evaluation_status_counts"] = dict(Counter(r["evaluation_status"] for r in rows))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    runner.emit(json.dumps(manifest["evaluation_status_counts"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=ROOT / "results/baseline/v2_synthetic_full")
    retry(parser.parse_args().run_dir)
