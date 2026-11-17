import copy
import unittest

from difficulty.environment_policy import validate_environment_assessment
from difficulty.llm_judge import compute_judge_difficulty


class EnvironmentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.trace = {'tool_events': [{'output': {'error': 'Required document missing'}}],
                      'conversation': [{'content': 'The required document is missing; I will pause.'}]}
        self.raw = {'environment_assessment': {'status': 'supported_blocker',
                    'prevents_required_execution': True, 'rationale': 'Necessary material is absent.',
                    'evidence': [{'locator': '#/tool_events/0/output/error', 'excerpt': 'Required document missing'}]},
                    'blocker_recognition': {'status': 'supported_positive', 'rationale': 'The agent identified it.',
                    'evidence': [{'locator': '#/conversation/0/content', 'excerpt': 'required document is missing'}]},
                    'difficulty_eligible': False, 'difficulty_exclusion_reason': 'Missing required document'}

    def test_blocker_recognition_is_separate_and_blocked_attempt_is_excluded(self):
        result = validate_environment_assessment(self.raw, {'task_judgment': 'unverifiable'}, self.trace)
        self.assertEqual(result['blocker_recognition_status'], 'supported_positive')
        self.assertEqual(result['difficulty_eligible'], 0)

    def test_blocked_attempt_cannot_be_unmet_or_eligible(self):
        with self.assertRaisesRegex(ValueError, 'unverifiable outcome'):
            validate_environment_assessment(self.raw, {'task_judgment': 'unmet'}, self.trace)
        invalid = copy.deepcopy(self.raw); invalid['difficulty_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'not difficulty eligible'):
            validate_environment_assessment(invalid, {'task_judgment': 'unverifiable'}, self.trace)

    def test_supported_recognition_cannot_rely_on_invented_evidence(self):
        self.raw['blocker_recognition']['evidence'][0]['excerpt'] = 'invented observation'
        with self.assertRaisesRegex(ValueError, 'excerpt is not present'):
            validate_environment_assessment(self.raw, {'task_judgment': 'unverifiable'}, self.trace)

    def test_excluded_attempts_do_not_influence_difficulty(self):
        def row(judgment, eligible):
            return {'domain': 'example', 'task_id': 'task', 'status': 'valid',
                    'task_judgment': judgment, 'policy_version': 'provisional_outcome_v0.2',
                    'difficulty_eligible': eligible}
        blocked = row('unverifiable', 0)
        result = compute_judge_difficulty([row('met', 1), row('unmet', 1), blocked])[0]
        self.assertEqual(result['n_eligible'], 2)
        self.assertEqual(result['difficulty'], 0.5)
        self.assertEqual(compute_judge_difficulty([blocked])[0]['difficulty'], '')
        with self.assertRaisesRegex(ValueError, 'different outcome policies'):
            compute_judge_difficulty([blocked, {**blocked, 'policy_version': 'provisional_outcome_v0.1'}])


if __name__ == '__main__':
    unittest.main()
