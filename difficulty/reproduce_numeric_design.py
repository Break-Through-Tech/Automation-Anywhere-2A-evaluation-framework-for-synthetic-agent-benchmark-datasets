"""Reproduce the published v19 design comparison offline; never call a model.

Run from the repository root:
  python -m difficulty.reproduce_numeric_design --out .cache/replayed_design_v19
Requires the exact source/code revision recorded in the published audit.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from .design.inputs import verify_sources
from .design.judge import load_packet, safe_output, write_json
from .design.reporting import aggregate, write_report
from .design.rubric import ROOT, digest


def reproduce(output, report_dir=ROOT / 'results/difficulty/tau2_final_v19'):
    output = safe_output(output)
    if output.exists():
        raise ValueError('Choose a fresh output directory')
    manifest = json.loads((report_dir / 'audit/run_manifest.json').read_text())
    archive = report_dir / 'audit/frozen_packets.jsonl.gz'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Archive fingerprint differs from published audit')
    output.mkdir(parents=True)
    native_packets, synthetic_packets, rows, bindings = [], [], [], []
    with gzip.open(archive, 'rt') as handle:
        for line in handle:
            record = json.loads(line)
            original = Path(record['original_path'])
            category = original.parent.name
            if original.name == 'controls':
                category = 'controls'
            if category not in {'native', 'synthetic_bound', 'calibration_synthetic', 'controls'}:
                raise ValueError('Unknown archived packet category')
            packet = output / 'packets' / category / original.name
            packet.mkdir(parents=True)
            for name, value in record['files'].items():
                rel = Path(name)
                if rel.is_absolute() or '..' in rel.parts or rel.suffix not in {'.json', '.jsonl'}:
                    raise ValueError('Unsafe archived output path')
                target = packet / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('x') as dest:
                    dest.write(value)
            inventory_path = packet / 'inventory_PRIVATE_COMPARISON.json'
            inventory = json.loads(inventory_path.read_text())
            frozen = json.loads((packet / 'manifest.json').read_text())
            old_hash = digest(inventory)
            for row in inventory:
                row['source_root'] = str(ROOT / 'tau2-bench' if row['dataset'] == 'tau2' else ROOT / 'data' if row['dataset'] == 'synthetic' else ROOT)
            verify_sources(inventory)
            # Relocate paths only. Payloads, requests, raw outputs and scores stay fixed.
            inventory_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n')
            frozen['inventory_sha256'] = digest(inventory)
            (packet / 'manifest.json').write_text(json.dumps(frozen, indent=2) + '\n')
            bindings.append({'original_packet': str(original), 'relocated_packet': str(packet),
                             'original_inventory_sha256': old_hash,
                             'relocated_inventory_sha256': digest(inventory), 'new_api_calls': 0})
            load_packet(packet)
            if category in {'native', 'synthetic_bound'}:
                rows.extend(inventory)
                (native_packets if category == 'native' else synthetic_packets).append(packet)
    result = aggregate(rows, native_packets + synthetic_packets)
    expected = json.loads((report_dir / 'comparison.json').read_text())
    for key in ['datasets', 'domains', 'workflows', 'tasks', 'protocol_fingerprints', 'returned_models']:
        actual, original = result[key], expected[key]
        if key == 'tasks':
            actual = {row['case_key']: row for row in actual}
            original = {row['case_key']: row for row in original}
        if actual != original:
            raise ValueError('Offline reproduction differs in ' + key)
    write_report(result, output / 'report')
    write_json(output / 'relocation_audit.json', bindings)
    write_json(output / 'verification.json', {'status': 'exact_scores_and_summaries_match',
               'api_calls': 0, 'tasks': len(rows), 'datasets': result['datasets']})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = reproduce(args.out)
    for dataset, value in result['datasets'].items():
        print(f"{dataset}: {value['mean']:.6f}/100; {value['n_scored']}/{value['n_total']} scored; zero API calls")


if __name__ == '__main__':
    main()
