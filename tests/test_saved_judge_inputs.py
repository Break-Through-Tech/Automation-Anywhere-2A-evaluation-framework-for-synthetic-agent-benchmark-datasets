import contextlib
import csv
import gzip
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from difficulty import llm_judge
from difficulty.saved_trials import load_baseline_trials
from difficulty.judge_review import write_review_packet
from difficulty.compare_judge_reviews import compare_reviews

ROOT = Path(__file__).resolve().parents[1]


def fixture_run(root, status='failed_reference'):
    trace = {'domain': 'sample', 'task_id': 'Task_W1_TC1', 'trial': 0,
             'conversation': [{'role': 'user', 'content': 'Please complete the task.'}],
             'tool_events': [{'name': 'operation', 'arguments': {'value': 7},
                              'output': {'status': 'done'}, 'error': False}],
             'user_prompt': '<scenario>{"input_data":{"value":7}}</scenario>',
             'evaluation': {'status': status, 'reward': None if status != 'failed_reference' else 0}}
    (root / 'trace.json.gz').write_bytes(gzip.compress(json.dumps(trace).encode()))
    columns = ['domain', 'task_id', 'trial', 'trace_file', 'evaluation_status', 'reward']
    with (root / 'trials.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns); writer.writeheader()
        writer.writerow({'domain': trace['domain'], 'task_id': trace['task_id'], 'trial': 0,
                         'trace_file': 'trace.json.gz', 'evaluation_status': status,
                         'reward': trace['evaluation']['reward']})
    return trace


class SavedJudgeInputTests(unittest.TestCase):
    def test_all_256_attempts_preserve_original_conversations_and_tool_events(self):
        path = ROOT / 'results/baseline/v2_synthetic_full/trials.csv'
        rows = llm_judge.load_trials([path])
        resolved = llm_judge.resolve_trials(rows, llm_judge.load_synthetic_cases())
        self.assertEqual(len(resolved), 256)
        self.assertEqual(len({(r['domain'], r['task_id']) for r in rows}), 64)
        invalid_refs = [r for r in rows if r['source']['original_evaluation']['status'] == 'invalid_reference']
        self.assertEqual(len(invalid_refs), 68)
        self.assertTrue(all('error' not in r for r in invalid_refs))
        for row in rows:
            trace = json.loads(gzip.decompress(Path(row['source']['trace_file']).read_bytes()))
            self.assertEqual(row['transcript']['conversation'], trace['conversation'])
            self.assertEqual(row['transcript']['tool_events'], trace['tool_events'])
            self.assertNotIn('evaluation', row['transcript'])

    def test_call_errors_are_evidence_not_automatic_infrastructure_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); trace = fixture_run(root, 'invalid_reference')
            trace['tool_events'][0].update(error=True, output={'error': 'ValueError', 'message': 'invalid input'})
            (root / 'trace.json.gz').write_bytes(gzip.compress(json.dumps(trace).encode()))
            row = load_baseline_trials(root / 'trials.csv')[0]
            self.assertTrue(row['transcript']['tool_events'][0]['error'])
            self.assertNotIn('error', row)
            self.assertEqual(row['scenario']['input_data']['value'], 7)

    def test_actual_infrastructure_error_remains_unscored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fixture_run(root, 'infrastructure_error')
            self.assertTrue(load_baseline_trials(root / 'trials.csv')[0]['error'])

    def test_corrupt_or_mismatched_or_incomplete_traces_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); original = fixture_run(root)
            variants = [dict(original, task_id='wrong'), dict(original, tool_events=[{'name': 'operation'}])]
            for variant in variants:
                (root / 'trace.json.gz').write_bytes(gzip.compress(json.dumps(variant).encode()))
                with self.assertRaises(ValueError): load_baseline_trials(root / 'trials.csv')
            (root / 'trace.json.gz').write_bytes(b'not gzip')
            with self.assertRaises(ValueError): load_baseline_trials(root / 'trials.csv')
            fixture_run(root)
            (root / 'trace.json.gz').unlink()
            with self.assertRaisesRegex(ValueError, 'Missing saved trace'):
                load_baseline_trials(root / 'trials.csv')

    def test_duplicate_rows_and_manifest_count_mismatch_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fixture_run(root)
            path = root / 'trials.csv'; lines = path.read_text().splitlines()
            path.write_text('\n'.join([*lines, lines[-1]]) + '\n')
            with self.assertRaisesRegex(ValueError, 'Duplicate baseline'):
                load_baseline_trials(path)
            fixture_run(root)
            (root / 'manifest.json').write_text('{"completed_trials":2}')
            with self.assertRaisesRegex(ValueError, 'count differs'):
                load_baseline_trials(path)

    def test_trace_paths_cannot_escape_saved_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fixture_run(root)
            path = root / 'trials.csv'
            path.write_text(path.read_text().replace('trace.json.gz', '../outside.json.gz'))
            with self.assertRaisesRegex(ValueError, 'inside its saved run'):
                load_baseline_trials(path)

    def test_dry_run_needs_no_credentials_and_never_calls_judge(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True), \
                patch.object(llm_judge, 'load_dotenv'), \
                patch.object(llm_judge, 'judge_trials', side_effect=AssertionError('No paid calls')):
            with contextlib.redirect_stdout(io.StringIO()):
                result = llm_judge.main(['--trials', str(ROOT / 'results/baseline/v2_synthetic_full'),
                                        '--dry-run', '--out', directory])
            self.assertEqual(result, 0)
            audit = json.loads((Path(directory) / 'input_audit.json').read_text())
            self.assertEqual(audit['attempts_loaded'], 256)
            self.assertEqual(audit['network_calls'], 0)
            self.assertFalse((Path(directory) / 'llm_judge_difficulty.csv').exists())

    def test_prepared_sample_is_blind_and_cannot_overwrite_human_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            args = ([ROOT / 'results/baseline/v2_synthetic_full/trials.csv'], out, 'unused')
            selection = ROOT / 'results/rubric_review/v1/sample.json'
            llm_judge.run(*args, prepare_review=True, selection=selection)
            packet = json.loads((out / 'review_packet.json').read_text())
            form = json.loads((out / 'human_reviews.json').read_text())
            self.assertEqual(len(packet['cases']), 16)
            self.assertTrue(all('original_evaluation' not in c['source'] for c in packet['cases']))
            self.assertTrue(all(r['task_judgment'] is None for r in form['reviews']))
            before = (out / 'human_reviews.json').read_bytes()
            with self.assertRaisesRegex(ValueError, 'preserve human labels'):
                llm_judge.run(*args, prepare_review=True, selection=selection)
            self.assertEqual((out / 'human_reviews.json').read_bytes(), before)
            comparison = compare_reviews(out / 'human_reviews.json', out / 'review_packet.json')
            self.assertEqual(comparison['status'], 'awaiting_human_review')
            self.assertFalse(comparison['agreement_metrics_computed'])


class HumanComparisonTests(unittest.TestCase):
    def test_real_labels_are_required_and_evidence_is_checked_before_agreement(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            task = {'test_case_id': 'Task_W1_TC1', 'milestones': [{'step': 1}]}
            row = {'domain': 'sample', 'task_id': task['test_case_id'], 'trial': 0,
                   'transcript': {'conversation': [], 'tool_events': [
                       {'name': 'operation', 'arguments': {}, 'output': {'status': 'done'}, 'error': False}]}}
            write_review_packet(out, [(row, ('sample', row['task_id']), task)], llm_judge.load_rubric(),
                                llm_judge.file_hash(llm_judge.RUBRIC_PATH))
            form_path = out / 'human_reviews.json'; packet_path = out / 'review_packet.json'
            form = json.loads(form_path.read_text()); review = form['reviews'][0]
            evidence = [{'locator': '#/tool_events/0/output/status', 'excerpt': 'done'}]
            review.update(reviewer='Unit-test fixture reviewer', task_judgment='met',
                          task_rationale='Operation returned done.', task_evidence=evidence)
            review['milestones'][0].update(applicable=True, material=True,
                applicability_basis='Required operation.', judgment='met', rationale='Operation returned done.',
                evidence=evidence)
            form_path.write_text(json.dumps(form))
            result = compare_reviews(form_path, packet_path)
            self.assertEqual(result['status'], 'awaiting_judge_results')
            # This is a deterministic test double, not production human or model evidence.
            judged = llm_judge.judge_trials([row], {('sample', row['task_id']): task}, 'offline',
                                            judge=lambda *_: review)
            csv_path = out / 'judgments.csv'; llm_judge._write_csv(csv_path, judged)
            result = compare_reviews(form_path, packet_path, csv_path)
            self.assertEqual(result['task_comparison']['agreement'], 1)
            review['task_evidence'][0]['excerpt'] = 'fabricated'
            form_path.write_text(json.dumps(form))
            with self.assertRaisesRegex(ValueError, 'excerpt is not present'):
                compare_reviews(form_path, packet_path, csv_path)
