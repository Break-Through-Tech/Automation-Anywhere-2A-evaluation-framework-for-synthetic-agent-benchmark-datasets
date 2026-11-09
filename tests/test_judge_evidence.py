"""Offline regressions for citation failures observed in saved judge responses."""
import copy
import json
from types import SimpleNamespace
import unittest

from difficulty.judge_evidence import check_evidence, pointer_value
from difficulty.llm_judge import _call_judge, _parse_judgment


class JudgeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.transcript = {
            'tool_events': [{'output': {'status': 'created', 'verified': True, 'amount': 500.0}}],
            'conversation': [{'content': 'The account is still pending.'}],
        }
        self.task = {'title': 'Example', 'rationale': 'Offline test',
                     'input_conditions': [], 'expected_success_outcome': {},
                     'expected_tool_calls': ['create_account'],
                     'milestones': [{'step': 1, 'description': 'Create the account'}]}
        evidence = [{'locator': '#/tool_events/0/output/status', 'excerpt': 'created'}]
        self.judgment = {
            'task_judgment': 'met', 'task_rationale': 'Creation was recorded.',
            'task_evidence': evidence, 'task_contradictions': [],
            'milestones': [{'step': 1, 'applicable': True, 'material': True,
                            'applicability_basis': 'Required by the task.',
                            'judgment': 'met', 'rationale': 'The output records creation.',
                            'evidence': copy.deepcopy(evidence), 'contradictions': []}],
        }

    def validate(self, judgment):
        parsed = _parse_judgment(json.dumps(judgment), self.task['milestones'])
        check_evidence(parsed, self.transcript)
        return parsed

    def test_exact_leaf_and_conversation_quotations_are_accepted(self):
        self.validate(self.judgment)
        self.judgment['task_evidence'] += [
            {'locator': '#/conversation/0/content', 'excerpt': 'still pending'},
            {'locator': '#/tool_events/0/output/verified', 'excerpt': 'true'},
            {'locator': '#/tool_events/0/output/amount', 'excerpt': '500.0'},
        ]
        self.validate(self.judgment)

    def test_reference_wrapper_missing_field_and_negative_index_are_rejected(self):
        for locator in ['#/task/milestones/0', '#/agent_transcript/tool_events/0/output/status',
                        '#/tool_events/0/output/account_id', '#/tool_events/-1/output/status',
                        '#/tool_events/00/output/status']:
            with self.subTest(locator=locator):
                judgment = copy.deepcopy(self.judgment)
                judgment['task_evidence'][0]['locator'] = locator
                with self.assertRaisesRegex(ValueError, 'does not resolve'):
                    self.validate(judgment)

    def test_paraphrases_ellipses_and_wrong_field_quotes_are_rejected(self):
        for excerpt in ['Account creation succeeded', 'cre...ated', 'pending']:
            with self.subTest(excerpt=excerpt):
                judgment = copy.deepcopy(self.judgment)
                judgment['milestones'][0]['evidence'][0]['excerpt'] = excerpt
                with self.assertRaisesRegex(ValueError, 'excerpt is not present'):
                    self.validate(judgment)

    def test_missing_booleans_and_empty_evidence_entries_are_rejected(self):
        for field in ['applicable', 'material']:
            judgment = copy.deepcopy(self.judgment)
            del judgment['milestones'][0][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'applicability and materiality'):
                self.validate(judgment)
        for evidence in [[], [{'locator': '', 'excerpt': ''}]]:
            judgment = copy.deepcopy(self.judgment)
            judgment['milestones'][0]['evidence'] = evidence
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                self.validate(judgment)

    def test_unverifiable_can_have_no_execution_evidence(self):
        judgment = copy.deepcopy(self.judgment)
        judgment.update(task_judgment='unverifiable', task_evidence=[])
        judgment['milestones'][0].update(judgment='unverifiable', evidence=[])
        self.validate(judgment)

    def test_json_pointer_escaped_keys_resolve(self):
        self.assertEqual(pointer_value({'a/b': {'~status': 'done'}}, '#/a~1b/~0status'), 'done')

    def test_whole_json_values_allow_serialization_whitespace_only(self):
        transcript = {'arguments': {'payer_id': 'PAYER-EXAMPLE', 'amount': 500.0},
                      'documents': ['Progress Notes', 'Imaging Report']}
        def validate(locator, excerpt):
            check_evidence({'task_evidence': [{'locator': locator, 'excerpt': excerpt}],
                            'milestones': []}, transcript)
        validate('#/arguments', '{"payer_id":"PAYER-EXAMPLE","amount":500.0}')
        validate('#/documents', '["Progress Notes","Imaging Report"]')
        for locator, excerpt in [
            ('#/arguments', '{"payer_id":"PAYER-OTHER","amount":500.0}'),
            ('#/arguments', '{"payer_id":"PAYER-EXAMPLE"}'),
            ('#/arguments', '{"payer_id":"PAYER-EXAMPLE","amount":true}'),
            ('#/arguments', '{"payer_id":"PAYER-OTHER","payer_id":"PAYER-EXAMPLE","amount":500.0}'),
            ('#/documents', '["Imaging Report","Progress Notes"]'),
            ('#/documents', '["ProgressNotes","Imaging Report"]'),
            ('#/documents', '["Progress Notes", ...]'),
        ]:
            with self.subTest(excerpt=excerpt), self.assertRaisesRegex(ValueError, 'excerpt is not present'):
                validate(locator, excerpt)

    def test_model_call_checks_evidence_before_accepting_response(self):
        def client_for(judgment):
            response = SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(judgment)))])
            return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
                create=lambda **kwargs: response)))
        result = _call_judge(self.task, self.transcript, 'offline-fake', client_for(self.judgment))
        self.assertEqual(result['task_judgment'], 'met')
        judgment = copy.deepcopy(self.judgment)
        judgment['task_evidence'][0]['excerpt'] = 'not in the transcript'
        with self.assertRaisesRegex(ValueError, 'excerpt is not present'):
            _call_judge(self.task, self.transcript, 'offline-fake', client_for(judgment))


if __name__ == '__main__':
    unittest.main()
