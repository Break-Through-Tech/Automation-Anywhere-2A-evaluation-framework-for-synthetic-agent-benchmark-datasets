"""Offline preparation/analysis by default; paid pilot requires --authorize-paid-api."""
import argparse
import json
from pathlib import Path

from .calibration import compare_variants, control_cases, pilot_cases, reliability
from .crosscheck import compare
from .inputs import ROOT, inventory_summary, synthetic_cases, tau_cases, unique
from .judge import load_packet, prepare_packet, run_packet, safe_output, write_json
from .reporting import aggregate, write_report


def prepare_inventory(dataset):
    if dataset == "controls":
        return control_cases()
    return unique((synthetic_cases() if dataset in {"synthetic", "both"} else []) +
                  (tau_cases() if dataset in {"tau2", "both"} else []))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("inventory", help="Static extraction; no API")
    inventory.add_argument("--dataset", choices=["synthetic", "tau2", "both", "controls"], default="both")
    inventory.add_argument("--out", type=Path, required=True)
    prepare = commands.add_parser("prepare", help="Freeze judge requests; no API")
    prepare.add_argument("--inventory", type=Path, required=True)
    prepare.add_argument("--selection", choices=["pilot", "all"], default="pilot")
    prepare.add_argument("--model", required=True)
    prepare.add_argument("--repeats", type=int, default=1)
    prepare.add_argument("--reasoning-effort", choices=["low", "medium", "high"])
    prepare.add_argument("--max-output-tokens", type=int, default=10000)
    prepare.add_argument("--source-bound-evidence", action="store_true",
                         help="Experimental source/excerpt enum schema; API compatibility not established")
    prepare.add_argument("--out", type=Path, required=True)
    check = commands.add_parser("check", help="Verify a frozen packet offline")
    check.add_argument("--packet", type=Path, required=True)
    run = commands.add_parser("run", help="Explicitly authorized paid pilot only")
    run.add_argument("--packet", type=Path, required=True)
    run.add_argument("--authorize-paid-api", action="store_true")
    run.add_argument("--max-calls", type=int, default=3)
    report = commands.add_parser("report", help="Aggregate saved results; no API")
    report.add_argument("--inventory", type=Path, required=True)
    report.add_argument("--packet", type=Path, action="append", default=[])
    report.add_argument("--features", type=Path)
    report.add_argument("--out", type=Path, required=True)
    calibrate = commands.add_parser("calibrate", help="Compare prespecified saved source-control pairs; no API")
    calibrate.add_argument("--baseline-report", type=Path, required=True)
    calibrate.add_argument("--variant-report", type=Path, required=True)
    calibrate.add_argument("--pairs", type=Path, required=True, help="JSON list of case keys and source_review_rationale")
    calibrate.add_argument("--kind", choices=["perturbation", "controlled_complexity"], required=True)
    calibrate.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "inventory":
        rows = prepare_inventory(args.dataset)
        out = safe_output(args.out)
        if out.exists():
            raise ValueError("Use a fresh inventory directory")
        out.mkdir(parents=True)
        write_json(out / "inventory.json", rows)
        result = inventory_summary(rows)
        write_json(out / "preflight.json", result)
    elif args.command == "prepare":
        rows = json.loads(args.inventory.read_text())
        if args.selection == "pilot":
            rows = pilot_cases(rows)
        result = prepare_packet(rows, args.out, args.model, args.repeats, args.max_output_tokens, args.reasoning_effort,
                                source_bound_evidence=args.source_bound_evidence)
    elif args.command == "check":
        result = load_packet(args.packet)[0]
    elif args.command == "run":
        # Never load .env or access an API key during preparation/reporting.
        result = run_packet(args.packet, authorize_paid=args.authorize_paid_api, max_calls=args.max_calls)
    elif args.command == "calibrate":
        result = compare_variants(json.loads(args.baseline_report.read_text()), json.loads(args.variant_report.read_text()),
                                  json.loads(args.pairs.read_text()), args.kind)
        out = safe_output(args.out)
        if out.exists():
            raise ValueError("Use a fresh calibration output")
        out.mkdir(parents=True)
        write_json(out / "paired_checks.json", result)
    else:
        rows = json.loads(args.inventory.read_text())
        result = aggregate(rows, args.packet)
        write_report(result, args.out)
        write_json(args.out / "reliability.json", reliability(result))
        features = json.loads(args.features.read_text()) if args.features else None
        write_json(args.out / "crosschecks.json", compare(result, rows, features))
        result = {"datasets": result["datasets"], "api_calls": 0}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
