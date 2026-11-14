from copy import deepcopy
import unittest
from unittest.mock import patch

from difficulty.native_semantic_profiles import analyze


def fixtures():
    row = {'dataset': 'tau2', 'domain': 'example', 'task_id': '1',
        'input_sha256': 'frozen', 'payload': {'case_key': 'one',
        'source_catalog': [{'source_id': 'scenario', 'text': 'Check the record. Ask for approval.'}]},
        'sources': {'scenario': {'path': 'task.json', 'locator': '#/0', 'sha256': 'source'}}}
    ev = [{'source_id': 'scenario', 'excerpt': 'Check the record.'}]
    profile = {'case_key': 'one', 'input_sha256': 'frozen', 'status': 'provisional_complete',
        'scope_rationale': 'Selected requirement.', 'excluded_work': ['Unused branch.'], 'uncertainties': [],
        'operations': [{'key': 'check', 'description': 'Check', 'rationale': 'Required.',
            'business_check': True, 'evidence': ev}],
        'coordination_events': [{'key': 'approval', 'description': 'Request approval',
            'rationale': 'One event, two tags.', 'categories': ['approval', 'external_response'], 'evidence': ev}]}
    return [row], {'tasks': [profile]}, {'tasks': [{'dataset': 'tau2', 'domain': 'example',
        'task_id': '1', 'case_key': 'one', 'input_sha256': 'frozen', 'score': 60}]}


class SemanticProfilesTest(unittest.TestCase):
    def run_profile(self, data):
        with patch('difficulty.native_semantic_profiles.verify_sources'):
            return analyze(*data)

    def test_coordination_categories_do_not_duplicate_an_event(self):
        r = self.run_profile(fixtures())['tasks'][0]
        self.assertEqual(r['features']['distinct_coordination_events'], 1)
        self.assertEqual(r['score'], 60)

    def test_unreviewed_is_missing_not_zero(self):
        data = fixtures(); data[1]['tasks'] = []
        r = self.run_profile(data)['tasks'][0]
        self.assertTrue(all(v is None for v in r['features'].values()))
        self.assertEqual(r['status'], 'not_authored')

    def test_partial_counts_are_excluded_from_complete_features(self):
        data = fixtures(); p = data[1]['tasks'][0]
        p.update(status='unresolved_path', uncertainties=['Order unknown.'])
        r = self.run_profile(data)['tasks'][0]
        self.assertIsNone(r['features']['business_check_groups'])
        self.assertEqual(r['documented_partial_counts']['business_check_groups'], 1)

    def test_duplicate_coordination_key_is_rejected(self):
        data = fixtures(); p = data[1]['tasks'][0]
        p['coordination_events'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.run_profile(data)

    def test_wrong_quote_or_source_is_rejected(self):
        for change in ({'excerpt': 'Invented requirement'}, {'source_id': 'missing'}):
            data = fixtures(); data[1]['tasks'][0]['operations'][0]['evidence'][0].update(change)
            with self.assertRaisesRegex(ValueError, 'frozen source'):
                self.run_profile(data)

    def test_input_or_score_identity_change_is_rejected(self):
        data = fixtures(); data[1]['tasks'][0]['input_sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.run_profile(data)
        data = fixtures(); data[2]['tasks'][0]['task_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.run_profile(data)

    def test_missing_score_and_duplicate_score_are_rejected(self):
        for scores in ([], fixtures()[2]['tasks'] * 2):
            data = fixtures(); data[2]['tasks'] = scores
            with self.assertRaises(ValueError):
                self.run_profile(data)

    def test_unknown_or_repeated_annotation_is_rejected(self):
        data = fixtures(); data[1]['tasks'] *= 2
        with self.assertRaisesRegex(ValueError, 'Duplicate or unknown'):
            self.run_profile(data)


if __name__ == '__main__':
    unittest.main()
