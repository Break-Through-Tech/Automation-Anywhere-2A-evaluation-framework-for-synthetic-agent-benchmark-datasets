import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from difficulty import design_feature_review as review
from difficulty.saved_trials import file_hash


class FrozenCountingRuleTests(unittest.TestCase):
    def request_and_response(self):
        text='Route invoice to AP; after AP approval, process payment.'
        request={'task_id':'hypothetical_ap','messages':[{'role':'system','content':'Offline schema fixture'},
                  {'role':'user','content':json.dumps({'source_catalog':[{'source_id':'S1','text':text}]})}]}
        evidence=[{'source_id':'S1','excerpt':text}]
        response={'review_version':review.VERSION,'task_id':'hypothetical_ap',
            'action_units':[{'id':'a1','description':'Route invoice to AP','evidence':evidence},
                            {'id':'a2','description':'Process payment','evidence':evidence}],
            'business_checks':[], 'coordination_requirements':[
                {'id':'c1','event_key':'ap_review','kind':'handoff','description':'Transfer invoice to AP','evidence':evidence},
                {'id':'c2','event_key':'ap_review','kind':'approval','description':'Require AP approval','evidence':evidence}],
            'uncertainties':[]}
        return request,response

    def test_nested_tool_groups_are_flattened_and_argument_names_are_not_tools(self):
        tools={'system_tools':[{'name':'SUCCESS','args':[]}],
               'domain_tools':[{'name':'extract_loss_details','signature':'extract_loss_details(text)',
                                'args':[{'name':'source_text','type':'string'}]}]}
        result=review.tool_definitions(tools)
        self.assertEqual(set(result),{'SUCCESS','extract_loss_details'})
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            review.tool_definitions({'a':[{'name':'same','args':[]}], 'b':[{'name':'same','args':[]}]})

    def test_prepared_requests_include_all_reference_and_workflow_tool_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/'packet';review.prepare(folder)
            for req in json.loads((folder/'requests.json').read_text())['requests']:
                payload=json.loads(req['messages'][1]['content'])
                catalog={s['source_id']:s['text'] for s in payload['source_catalog']}
                definitions=json.loads(catalog['C']);names=set(json.loads(catalog['R']))
                workflow=json.loads(catalog['W'])
                names.update(name for step in workflow['steps'] for name in step.get('tools_used',[]))
                self.assertTrue(definitions)
                self.assertTrue(names.issubset(definitions))
                self.assertTrue(all('args' in tool or 'signature' in tool for tool in definitions.values()))

    def test_one_coordination_event_may_have_two_nonadditive_categories(self):
        request,raw=self.request_and_response();result=review.validate_response(raw,request)
        self.assertEqual(result['action_units'],2)
        self.assertEqual(result['business_check_groups'],0)
        self.assertEqual(result['coordination'],{'handoff':1,'approval':1})
        self.assertEqual(result['distinct_coordination_events'],1)

    def test_repeated_mentions_do_not_create_another_same_category_event(self):
        request,raw=self.request_and_response()
        duplicate=copy.deepcopy(raw['coordination_requirements'][1]);duplicate['id']='c3';duplicate['description']='Another mention of the same AP approval'
        raw['coordination_requirements'].append(duplicate)
        with self.assertRaisesRegex(ValueError,'Duplicate coordination event/category'):
            review.validate_response(raw,request)

    def test_missing_event_key_or_an_invented_decision_count_is_rejected(self):
        request,raw=self.request_and_response();bad=copy.deepcopy(raw)
        del bad['coordination_requirements'][0]['event_key']
        with self.assertRaisesRegex(ValueError,'fields'):review.validate_response(bad,request)
        bad={**raw,'decision_count':1}
        with self.assertRaisesRegex(ValueError,'schema'):review.validate_response(bad,request)

    def test_packets_include_frozen_rules_and_reject_a_changed_rulebook(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'packet';manifest=review.prepare(out)
            self.assertEqual(manifest['rulebook_version'],review.RULEBOOK_VERSION)
            self.assertEqual(manifest['rulebook_sha256'],file_hash(review.RULEBOOK))
            requests=json.loads((out/'requests.json').read_text())['requests']
            for request in requests:
                self.assertIn(review.RULEBOOK.read_text(),request['messages'][0]['content'])
                payload=json.loads(request['messages'][1]['content'])
                self.assertEqual(set(payload),{'task_id','domain','source_catalog'})
            changed=Path(directory)/'changed.md';changed.write_text(review.RULEBOOK.read_text()+'\nChanged counting interpretation.\n')
            with patch.object(review,'RULEBOOK',changed):
                with self.assertRaisesRegex(ValueError,'rulebook/version changed'):
                    review.compare_saved(out,Path(directory)/'no_responses',Path(directory)/'comparison')


if __name__=='__main__':unittest.main()
