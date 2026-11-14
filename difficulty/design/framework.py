"""Framework entry point for source-only scoring, without coverage-model downloads."""
import json

from .inputs import verify_sources
from .reporting import aggregate, write_report


def evaluate(args):
    if not args.design_inventory:
        raise ValueError("source-only mode requires --design-inventory")
    if getattr(args, "synthetic_designed_scores", None) or getattr(args, "synthetic_structural_features", None):
        raise ValueError("Source-only mode does not mix historical structural indices/features into its score")
    rows = json.loads(args.design_inventory.read_text())
    verify_sources(rows)
    report = aggregate(rows, args.design_packet or [])
    write_report(report, args.output_dir)
    for dataset, result in report["datasets"].items():
        print(f"{dataset}: numeric designed difficulty={result['mean']} ({result['mean_label']}), scored={result['n_scored']}/{result['n_total']}")
    return report
