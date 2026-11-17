import copy
import json
from types import SimpleNamespace
import unittest

from difficulty.environment_policy import validate_environment_assessment, CURRENT_POLICY
from difficulty.llm_judge import _call_judge, judge_trials, compute_judge_difficulty, POLICY_VERSION


class OutcomePolicyV03Tests(unittest.TestCase):
    def setUp(self):
        self.trace = {'tool_events': [{'output': {'error': 'Required document missing',
                      'status': 'not_created'}}], 'conversation': []}
        evidence = [{'locator': '#/tool_events/0/output/status', 'excerpt': 'not_created'}]
        self.raw = {'task_judgment': 'unmet', 'task_rationale': 'Creation explicitly did not occur.',
            'task_evidence': evidence, 'task_contradictions': [], 'milestones': [
                {'step': 1, 'applicable': True, 'material': True,
                 'applicability_basis': 'Creation required.', 'judgment': 'unmet',
                 'rationale': 'Explicit noncreation.', 'evidence': evidence, 'contradictions': []}],
            'environment_assessment': {'status': 'supported_blocker',
                'prevents_required_execution': True, 'rationale': 'Necessary document absent.',
                'evidence': [{'locator': '#/tool_events/0/output/error',
                              'excerpt': 'Required document missing'}]},
            'blocker_recognition': {'status': 'not_established', 'rationale': 'No recognition observed.',
                                    'evidence': []},
            'difficulty_eligible': False, 'difficulty_exclusion_reason': 'Required document missing'}
        self.task = {'test_case_id': 'example', 'title': 'Create record', 'rationale': 'Test',
                     'input_conditions': [], 'expected_success_outcome': {'status': 'created'},
                     'milestones': [{'step': 1}], 'expected_tool_calls': ['create_record']}

    def test_blocked_unmet_and_unverifiable_allowed_but_met_forbidden(self):
        for label in ['unmet', 'unverifiable']:
            result = validate_environment_assessment(self.raw, {'task_judgment': label},
                                                     self.trace, CURRENT_POLICY)
            self.assertEqual(result['difficulty_eligible'], 0)
        with self.assertRaisesRegex(ValueError, 'cannot coexist'):
            validate_environment_assessment(self.raw, {'task_judgment': 'met'}, self.trace, CURRENT_POLICY)
        with self.assertRaisesRegex(ValueError, 'unverifiable outcome'):
            validate_environment_assessment(self.raw, {'task_judgment': 'unmet'}, self.trace)

    def test_exclusion_evidence_and_unknown_policy_enforced(self):
        bad = copy.deepcopy(self.raw); bad['difficulty_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'not difficulty eligible'):
            validate_environment_assessment(bad, bad, self.trace, CURRENT_POLICY)
        bad = copy.deepcopy(self.raw); bad['environment_assessment']['evidence'][0]['excerpt'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'excerpt is not present'):
            validate_environment_assessment(bad, bad, self.trace, CURRENT_POLICY)
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            validate_environment_assessment(self.raw, self.raw, self.trace, 'unknown')

    def test_current_model_path_validates_and_preserves_separate_assessment(self):
        requests = []
        def create(**kw):
            requests.append(kw)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(self.raw)))])
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        output = _call_judge(self.task, self.trace, 'offline', client,
                             evaluation_context={'complete_tool_log': True})
        self.assertEqual(output['task_judgment'], 'unmet')
        self.assertEqual(output['difficulty_eligible'], 0)
        self.assertEqual(output['policy_version'], POLICY_VERSION)
        self.assertIn('provisional_outcome_v0.3', requests[0]['messages'][0]['content'])
        self.assertIn('evaluation_context', json.loads(requests[0]['messages'][1]['content']))
        rows = judge_trials([{'domain': 'sample', 'task_id': 'example', 'trial': 0,
                              'transcript': self.trace}], {('sample', 'example'): self.task},
                            'offline', judge=lambda *_: output)
        self.assertEqual(rows[0]['environment_blocked'], 1)
        self.assertEqual(compute_judge_difficulty(rows)[0]['difficulty'], '')

    def test_denominator_ignores_blocked_fail_and_rejects_mixed_policy(self):
        base = {'domain': 'sample', 'task_id': 'example', 'status': 'valid',
                'policy_version': CURRENT_POLICY, 'difficulty_exclusion_reason': '',
                'environment_assessment_json': '{}', 'environment_blocked': 0, 'difficulty_eligible': 1}
        blocked = {**base, 'task_judgment': 'unmet', 'difficulty_eligible': 0,
                   'environment_blocked': 1, 'difficulty_exclusion_reason': 'Missing document'}
        rows = [{**base, 'task_judgment': 'met'}, {**base, 'task_judgment': 'unmet'}, blocked]
        summary = compute_judge_difficulty(rows)[0]
        self.assertEqual(summary['difficulty'], .5)
        self.assertEqual(summary['n_eligible'], 2)
        with self.assertRaisesRegex(ValueError, 'different outcome policies'):
            compute_judge_difficulty([blocked, {**blocked, 'policy_version': 'provisional_outcome_v0.2'}])
        with self.assertRaisesRegex(ValueError, 'not difficulty eligible'):
            compute_judge_difficulty([{**blocked, 'difficulty_eligible': 1}])
        with self.assertRaisesRegex(ValueError, 'explicit difficulty eligibility'):
            compute_judge_difficulty([{k:v for k,v in blocked.items() if k != 'difficulty_eligible'}])


if __name__ == '__main__':
    unittest.main()
