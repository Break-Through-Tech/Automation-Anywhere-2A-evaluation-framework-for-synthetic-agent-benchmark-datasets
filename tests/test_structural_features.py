import unittest
import copy
import json
from pathlib import Path
import tempfile

from difficulty.structural_features import extract, load_for_framework, review_sample, workflow_features


class StructuralFeatureTests(unittest.TestCase):
    def test_workflow_steps_tool_mentions_and_reference_calls_are_distinct(self):
        result = workflow_features({'steps': [
            {'step': 1, 'description': 'Read input', 'tools_used': ['read', 'read']},
            {'step': 2, 'description': 'If approval fails, escalate; otherwise proceed',
             'tools_used': ['HUMAN_IN_THE_LOOP']},
            {'step': 3, 'description': 'Finish', 'tools_used': ['SUCCESS']},
        ]})
        self.assertEqual(result['workflow_step_count'], 3)
        self.assertEqual(result['workflow_domain_tool_mentions'], 2)
        self.assertEqual(result['workflow_system_tool_mentions'], 2)
        self.assertEqual(result['workflow_decision_cue_step_count'], 1)
        self.assertEqual(result['workflow_decision_cue_evidence'][0]['step'], 2)

    def test_cue_count_is_not_an_inferred_branch_count(self):
        result = workflow_features({'steps': [
            {'step': 1, 'description': 'Verify identification and classification', 'tools_used': []},
            {'step': 2, 'description': 'Request approval', 'tools_used': []},
        ]})
        # Unconditional approval is still a wording cue, not proof of a branch.
        self.assertEqual(result['workflow_decision_cue_step_count'], 1)
        self.assertEqual(result['workflow_decision_cue_evidence'][0]['matched_cues'], ['approval'])

    def test_real_tasks_have_unique_canonical_ids_and_reviewable_provenance(self):
        features = extract()
        self.assertEqual(features['task_count'], 64)
        self.assertEqual(features['domain_count'], 7)
        self.assertEqual(len({(r['domain'], r['task_id']) for r in features['tasks']}), 64)
        self.assertEqual(len(features['source_sha256']), 21)
        for row in features['tasks']:
            calls = row['reference_tool_sequence']
            self.assertEqual(row['reference_domain_tool_call_count'] + row['reference_system_tool_call_count'], len(calls))
            self.assertIsNone(row['task_path_step_count'])
            self.assertIsNone(row['task_decision_point_count'])
            self.assertGreater(row['sources']['python_class_line'], 0)
            self.assertEqual(row['sources']['canonical_task_id'], row['task_id'])
        sample = review_sample(features)
        self.assertEqual(len(sample['reviews']), 7)
        self.assertEqual(len({r['features']['domain'] for r in sample['reviews']}), 7)
        self.assertTrue(all(r['counts_and_tag_verified'] is None for r in sample['reviews']))

    def test_framework_join_rejects_duplicate_missing_and_stale_features(self):
        features = extract()
        tasks = [{'dataset': 'synthetic', 'domain': r['domain'], 'task_id': r['task_id']}
                 for r in features['tasks']]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'features.json'
            path.write_text(json.dumps(features))
            _, mapping, sources = load_for_framework(path, tasks)
            self.assertEqual(len(mapping), 64)
            self.assertEqual(len(sources), 21)
            variants = []
            duplicate = copy.deepcopy(features)
            duplicate['tasks'].append(duplicate['tasks'][0])
            variants.append(duplicate)
            missing = copy.deepcopy(features)
            missing['tasks'].pop()
            variants.append(missing)
            stale = copy.deepcopy(features)
            stale['source_sha256'][next(iter(stale['source_sha256']))] = '0' * 64
            variants.append(stale)
            for value in variants:
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    load_for_framework(path, tasks)


if __name__ == '__main__':
    unittest.main()
