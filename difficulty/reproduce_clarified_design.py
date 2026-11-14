"""Restore and reproduce a published clarified score archive without API access."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

from .clarified_framework import build_report
from .design.judge import safe_output
from .design.rubric import ROOT, digest

ROOT_FILES = {'manifest.json','requests.json','inventory_PRIVATE_COMPARISON.json',
              'cache_bindings.json','authorization_v27.json','execution_log.jsonl','progress.jsonl'}


def restore(archive, output, expected_hash):
    archive = Path(archive); output = safe_output(output)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_hash:
        raise ValueError('Archive hash differs from published audit')
    if output.exists():
        raise ValueError('Choose a fresh restore directory')
    with tarfile.open(archive,'r:gz') as handle:
        members = handle.getmembers(); seen = set()
        for member in members:
            p = Path(member.name)
            allowed = member.name in ROOT_FILES or (len(p.parts)==2 and p.parts[0] in {'raw','results','intents'} and p.suffix=='.json')
            if (not allowed or not member.isfile() or p.is_absolute() or '..' in p.parts or
                    member.name in seen or '\\' in member.name):
                raise ValueError('Unsafe, duplicate or unexpected archive member')
            seen.add(member.name)
        if not {'manifest.json','requests.json','inventory_PRIVATE_COMPARISON.json','cache_bindings.json'} <= seen:
            raise ValueError('Incomplete score archive')
        output.mkdir(parents=True)
        for member in members:
            target=output/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as dest:dest.write(handle.extractfile(member).read())
    return output


def reproduce(report_dir, output):
    report_dir=Path(report_dir)
    audit=json.loads((report_dir/'audit/run_manifest.json').read_text())
    packet=restore(report_dir/'audit/frozen_packet.tar.gz',output,audit['archive_sha256'])
    # Only local filesystem roots are relocated. Payloads, wire requests, evidence,
    # ratings and raw responses remain identical to the frozen observations.
    path=packet/'inventory_PRIVATE_COMPARISON.json';rows=json.loads(path.read_text())
    old=digest(rows)
    for row in rows:
        row['source_root']=str(ROOT/('tau2-bench' if row['dataset']=='tau2' else 'data'))
    path.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    mp=packet/'manifest.json';m=json.loads(mp.read_text());m['inventory_sha256']=digest(rows)
    mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
    result=build_report(packet);expected=json.loads((report_dir/'task_scores.json').read_text())
    for key in ('metric','release_protocol','rubric_version','prompt_version','scale','task_weighting','datasets','domains','workflows','weights','formula','calibration_status','tasks','returned_models','limitations'):
        a,b=result[key],expected[key]
        if key=='tasks':a,b=({r['case_key']:r for r in value} for value in (a,b))
        if a!=b:raise ValueError('Offline replay differs: '+key)
    check={'status':'exact_task_scores_and_summaries_match','api_calls':0,'task_count':len(rows),
        'original_inventory_sha256':old,'relocated_inventory_sha256':digest(rows)}
    (packet/'offline_replay_verification.json').write_text(json.dumps(check,indent=2)+'\n')
    return check


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(reproduce(a.report_dir,a.out),indent=2))


if __name__=='__main__':main()
