import copy
import json
from pathlib import Path
import tempfile
import unittest

from difficulty import designed_profiles_v2 as v2
from difficulty import design_feature_review as review
from difficulty.designed_difficulty import REPO


class DesignedProfilesV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=v2.build();cls.byid={r['task_id']:r for r in cls.doc['tasks']}

    def test_all_tasks_are_profiles_not_new_scores(self):
        self.assertEqual((self.doc['task_count'],self.doc['domain_count'],self.doc['network_calls']),(64,7,0))
        self.assertEqual(len(self.byid),64)
        self.assertTrue(all(r['v2_combined_score'] is None for r in self.doc['tasks']))
        self.assertTrue(all(r['exact_atomic_actions'] is None for r in self.doc['tasks']))
        c=self.byid['HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1']
        self.assertEqual((c['v1_action_groups'],c['proposed_operation_unit_count']),(5,8))
        self.assertEqual(c['additional_reference_calls_from_repetition'],2)

    def test_coordination_distinguishes_claims_without_false_merge_matches(self):
        e=self.byid['InsuranceClaimsIntakeAndTriageAgent_W1_TC1']
        f=self.byid['InsuranceClaimsIntakeAndTriageAgent_W8_TC1']
        self.assertEqual(e['v1_score_reference_only'],f['v1_score_reference_only'])
        self.assertEqual((e['linked_records_requirements'],e['multi_party_requirements']),(0,0))
        self.assertEqual((f['linked_records_requirements'],f['multi_party_requirements']),(1,2))
        self.assertEqual(self.byid['ManufacturingPurchaseToPayAutomationAgent_P2P_W8_TC1']['linked_records_requirements'],0)
        ap=self.byid['ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1']
        self.assertEqual(ap['approval_requirements'],1)
        approval=next(x for x in ap['coordination_evidence'] if x['kind']=='approval')
        self.assertEqual(len(approval['evidence']),2)
        self.assertEqual(self.byid['HealthcareOnboarding_W2_TC1']['linked_records_requirements'],1)

    def test_changed_source_and_invented_coordination_rejected(self):
        original=json.loads(v2.ANNOTATIONS.read_text())
        variants=[]
        changed=copy.deepcopy(original);changed['source_sha256']={};variants.append(changed)
        changed=copy.deepcopy(original);changed['tasks'][0]['milestones'][0]['operation_units']=['Repeated','Repeated'];variants.append(changed)
        changed=copy.deepcopy(original)
        row=next(r for r in changed['tasks'] if r['coordination_requirements'])
        row['coordination_requirements'][0]['evidence'][0]['excerpt']='invented';variants.append(changed)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'annotations.json'
            for value in variants:
                p.write_text(json.dumps(value))
                with self.assertRaises(ValueError):v2.build(p)

    def test_outputs_reproduce_and_preserve_baseline(self):
        original=(REPO/'results/difficulty/designed_v1/scores.json').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a';b=Path(folder)/'b'
            v2.write_outputs(a,self.doc);v2.write_outputs(b,v2.build())
            for f in a.iterdir():self.assertEqual(f.read_bytes(),(b/f.name).read_bytes())
            with self.assertRaisesRegex(ValueError,'fresh'):v2.write_outputs(a,self.doc)
        self.assertEqual(original,(REPO/'results/difficulty/designed_v1/scores.json').read_bytes())


class DesignFeatureReviewTests(unittest.TestCase):
    def test_packets_hide_proposals_and_enforce_small_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'packet';m=review.prepare(p)
            self.assertEqual((m['n_requests'],m['api_calls']),(3,0))
            requests=json.loads((p/'requests.json').read_text())['requests']
            for request in requests:
                payload=json.loads(request['messages'][1]['content'])
                self.assertEqual(set(payload),{'task_id','domain','source_catalog'})
                self.assertNotIn('v1_score',request['messages'][1]['content'])
                self.assertNotIn('operation_units',request['messages'][1]['content'])
                self.assertNotIn('supplied_tag',request['messages'][1]['content'])
                for source in payload['source_catalog']:
                    if source['source_id']=='T_input':
                        self.assertTrue(source['locator'].endswith('/representative_input'))
            with self.assertRaisesRegex(ValueError,'one to three'):review.prepare(Path(folder)/'too_many',review.DEFAULT_IDS+['HealthcarePA_W8_TC1'])

    def test_response_citations_identity_duplicates_and_schema(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'packet';review.prepare(p)
            request=json.loads((p/'requests.json').read_text())['requests'][0]
            payload=json.loads(request['messages'][1]['content']);source=next(s for s in payload['source_catalog'] if s['source_id']=='M1')
            raw={'review_version':review.VERSION,'task_id':request['task_id'],
                 'action_units':[{'id':'a1','description':'Offline fixture operation, not a model judgment',
                    'evidence':[{'source_id':'M1','excerpt':source['text']}]}],
                 'business_checks':[],'coordination_requirements':[],'uncertainties':[]}
            self.assertEqual(review.validate_response(raw,request)['action_units'],1)
            bad=copy.deepcopy(raw);bad['action_units'][0]['evidence'][0]['excerpt']='invented'
            with self.assertRaisesRegex(ValueError,'not present'):review.validate_response(bad,request)
            bad={**raw,'task_judgment':'met'}
            with self.assertRaisesRegex(ValueError,'schema'):review.validate_response(bad,request)
            bad=copy.deepcopy(raw);bad['action_units']*=2
            with self.assertRaisesRegex(ValueError,'Duplicated'):review.validate_response(bad,request)

    def test_saved_comparison_queues_disagreements_without_updates(self):
        with tempfile.TemporaryDirectory() as folder:
            packet=Path(folder)/'packet';review.prepare(packet)
            responses=Path(folder)/'responses';responses.mkdir()
            for req in json.loads((packet/'requests.json').read_text())['requests']:
                # Deterministic offline fixture; not an API response or gold review.
                raw={'review_version':review.VERSION,'task_id':req['task_id'],'action_units':[],
                     'business_checks':[],'coordination_requirements':[],
                     'uncertainties':[{'id':'u1','description':'Offline fixture has not assessed this task','evidence':[]}]}
                (responses/(req['review_id']+'.json')).write_text(json.dumps(raw))
            result=review.compare_saved(packet,responses,Path(folder)/'compared')
            self.assertEqual(len(result['comparisons']),3)
            self.assertFalse(result['profiles_updated']);self.assertFalse(result['scores_updated'])
            self.assertTrue(all(r['operation_unit_delta']<0 for r in result['comparisons']))
            targets=packet/'comparison_targets_NOT_FOR_MODEL.json';targets.write_text('[]')
            with self.assertRaisesRegex(ValueError,'changed'):review.compare_saved(packet,responses,Path(folder)/'invalid')


if __name__=='__main__':unittest.main()
