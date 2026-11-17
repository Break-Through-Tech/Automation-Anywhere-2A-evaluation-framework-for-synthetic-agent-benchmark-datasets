"""One supplied Python task ID across the runner, judge, and saved baseline."""
import contextlib
import csv
import io
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from baseline.synthetic_environment import load_cases
from data import run_test_cases
from difficulty.llm_judge import load_synthetic_cases, judge_trials, compute_judge_difficulty

ROOT = Path(__file__).resolve().parents[1]


class SyntheticTaskIdTests(unittest.TestCase):
    def test_all_saved_ids_and_class_names_resolve_to_one_canonical_id(self):
        lookup = load_synthetic_cases()
        source_cases = load_cases()
        self.assertEqual(len(source_cases), 64)
        for domain, case in source_cases:
            with self.subTest(task=case.test_case_id):
                self.assertIs(lookup[(domain, case.__name__)], lookup[(domain, case.test_case_id)])
                self.assertEqual(lookup[(domain, case.__name__)]['test_case_id'], case.test_case_id)
        canonical = {(domain, record['test_case_id']) for (domain, _), record in lookup.items()}
        self.assertEqual(len(canonical), 64)
        with (ROOT / 'results/baseline/v2_synthetic_full/trials.csv').open(newline='') as handle:
            saved = {(r['domain'], r['task_id']) for r in csv.DictReader(handle)}
        self.assertEqual(canonical, saved)

    def test_json_reference_and_legacy_class_ids_emit_only_the_python_id(self):
        lookup = load_synthetic_cases()
        domain = 'banking_accounts_deposits'
        legacy = 'TestCase2_DigitalAccountOpeningAgent_W1_easy'
        canonical = 'DigitalAccountOpeningAgent_W1_TC2'
        reference = 'DigitalAccountOpening_W1_TC2'
        self.assertIs(lookup[(domain, reference)], lookup[(domain, canonical)])
        rows = [{'domain': domain, 'task_id': name, 'trial': trial, 'error': 'saved failure'}
                for trial, name in enumerate((legacy, reference, canonical))]
        never_called = Mock(side_effect=AssertionError('No judge calls expected'))
        results = judge_trials(rows, lookup, 'offline', judge=never_called)
        self.assertEqual({r['task_id'] for r in results}, {canonical})
        summary = compute_judge_difficulty(results)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['n_trials'], 3)
        never_called.assert_not_called()

    def test_duplicate_attempt_under_different_names_is_rejected_before_judging(self):
        lookup = load_synthetic_cases()
        domain, case = load_cases()[0]
        rows = [{'domain': domain, 'task_id': name, 'trial': 0, 'transcript': 'example'}
                for name in (case.test_case_id, case.__name__)]
        never_called = Mock(side_effect=AssertionError('Must reject duplicates first'))
        with self.assertRaisesRegex(ValueError, 'Duplicate canonical'):
            judge_trials(rows, lookup, 'offline', judge=never_called)
        never_called.assert_not_called()

    def test_runner_uses_supplied_id_and_serializes_it_without_model_calls(self):
        domain = 'example_domain'
        module = types.ModuleType(domain + '.test_cases')
        case = type('TestCase1_Example_W1_easy', (),
                    {'__module__': module.__name__, 'test_case_id': 'Example_W1_TC1'})
        setattr(module, case.__name__, case)
        with patch.object(run_test_cases.importlib, 'import_module', return_value=module), \
                contextlib.redirect_stdout(io.StringIO()):
            loaded = run_test_cases.load_test_case_classes(domain)
        self.assertEqual(list(loaded), ['Example_W1_TC1'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trials.jsonl'
            run_test_cases.save_judge_trials([{'inputs': {'agent_name': domain,
                'test_id': next(iter(loaded))}, 'error': 'offline example'}], path)
            self.assertEqual(json.loads(path.read_text())['task_id'], 'Example_W1_TC1')

    def test_runner_rejects_duplicate_or_missing_supplied_ids(self):
        module = types.ModuleType('example.test_cases')
        for name in ('TestCase1', 'TestCase2'):
            setattr(module, name, type(name, (),
                    {'__module__': module.__name__, 'test_case_id': 'same-id'}))
        with patch.object(run_test_cases.importlib, 'import_module', return_value=module):
            with self.assertRaisesRegex(ValueError, 'Duplicate test_case_id'):
                run_test_cases.load_test_case_classes('example')
            delattr(module.TestCase2, 'test_case_id')
            with self.assertRaisesRegex(ValueError, 'Missing test_case_id'):
                run_test_cases.load_test_case_classes('example')

    def test_reference_mapping_rejects_ambiguous_and_unmatched_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            domain = root / 'example'; domain.mkdir()
            (domain / 'test_cases.py').write_text(
                'class TestCase1:\n    test_case_id = "Prefix_W1_TC1"\n    expected_tool_calls = []\n'
                'class TestCase2:\n    test_case_id = "Other_W1_TC1"\n    expected_tool_calls = []\n')
            (domain / 'test_cases.json').write_text(json.dumps({'workflows': [
                {'test_cases': [{'test_case_id': 'Ref_W1_TC1'}]}]}))
            with self.assertRaisesRegex(ValueError, 'Expected one Python'):
                load_synthetic_cases(root)
            (domain / 'test_cases.json').write_text(json.dumps({'workflows': [
                {'test_cases': [{'test_case_id': 'Ref_W9_TC9'}]}]}))
            with self.assertRaisesRegex(ValueError, 'Expected one Python'):
                load_synthetic_cases(root)
