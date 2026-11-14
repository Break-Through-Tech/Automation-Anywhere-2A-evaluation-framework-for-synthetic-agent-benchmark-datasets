import copy
import json
from pathlib import Path
import tempfile
import unittest

from difficulty import designed_profiles_v3 as v3
from difficulty.saved_trials import file_hash


class DesignedProfilesV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=v3.build();cls.byid={r['task_id']:r for r in cls.doc['tasks']}

    def test_complete_source_scope_coverage_and_no_new_scalar(self):
        self.assertEqual((self.doc['task_count'],self.doc['domain_count'],self.doc['network_calls']),(64,7,0))
        self.assertEqual(sum(bool(r['added_global_operations']) for r in self.doc['tasks']),12)
        self.assertEqual(sum(r['added_global_operation_count'] for r in self.doc['tasks']),22)
        self.assertTrue(all(r['v3_combined_score'] is None for r in self.doc['tasks']))
        for row in self.doc['tasks']:
            self.assertTrue(row['global_requirement_dispositions'])
            self.assertEqual(row['proposed_operation_unit_count']-row['v2_operation_unit_count'],len(row['added_global_operations']))
            for operation in row['added_global_operations']:v3.check_source_evidence(operation['evidence'])

    def test_updated_insurance_adds_three_checks_not_ambient_logging(self):
        c=self.byid['HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1']
        self.assertEqual((c['v2_operation_unit_count'],c['proposed_operation_unit_count'],c['business_check_groups']),(8,11,5))
        self.assertEqual(c['external_response_requirements'],1)
        self.assertEqual(c['linked_records_requirements'],0)
        self.assertFalse(any('logging' in o['description'].lower() for o in c['added_global_operations']))
        missing=self.byid['HealthcareOnboarding_W8_TC1']
        self.assertNotIn('global:G0_initial',{o['key'] for o in missing['added_global_operations']})
        duplicate=self.byid['HealthcareOnboarding_W6_TC1']
        self.assertNotIn('global:G2',{o['key'] for o in duplicate['added_global_operations']})
        selfpay=self.byid['HealthcareOnboarding_W5_TC1']
        self.assertNotIn('global:G1',{o['key'] for o in selfpay['added_global_operations']})

    def test_covered_risk_and_inactive_pa_phases_are_not_added_twice(self):
        risk=self.byid['BankingFraudMonitoringSupportAgent_BankingFraud_W3_TC1']
        self.assertEqual(risk['added_global_operation_count'],0)
        self.assertEqual(next(e for e in risk['global_requirement_dispositions'] if e['key']=='G1')['disposition'],'covered')
        self.assertEqual(self.byid['HealthcarePA_W8_TC1']['added_global_operation_count'],0)
        self.assertEqual(self.byid['HealthcarePA_W6_TC1']['added_global_operation_count'],1)

    def test_coordination_events_are_deduplicated_and_routine_ids_not_links(self):
        ap=self.byid['ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1']
        self.assertEqual((ap['handoff_requirements'],ap['approval_requirements'],ap['distinct_coordination_events']),(1,1,1))
        commercial=self.byid['InsuranceClaimsIntakeAndTriageAgent_W8_TC1']
        self.assertEqual((commercial['handoff_requirements'],commercial['multi_party_requirements'],commercial['linked_records_requirements'],commercial['distinct_coordination_events']),(2,2,1,3))
        c=self.byid['HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1']
        source=c['sources']['json_file'];base=c['sources']['json_case_pointer']
        req={'id':'routine_id','kind':'linked_records','description':'Routine ID passing',
             'evidence':[{'source':source,'locator':base+'/representative_input/provider_id','excerpt':'PROV-13579'}]}
        kept,excluded=v3.coordination_profile(c['task_id'],[req])
        self.assertFalse(kept);self.assertEqual(len(excluded),1)
        req={'id':'api_result','kind':'external_response','description':'Ordinary tool result',
             'evidence':[c['milestones'][1]['evidence']]}
        kept,excluded=v3.coordination_profile(c['task_id'],[req])
        self.assertFalse(kept);self.assertEqual(len(excluded),1)

    def test_scope_drift_and_duplicate_work_are_rejected(self):
        original=json.loads(v3.ANNOTATIONS.read_text());variants=[]
        bad=copy.deepcopy(original);bad['rulebook_sha256']='changed';variants.append(bad)
        bad=copy.deepcopy(original);bad['tasks'][0]['global_requirements'].pop();variants.append(bad)
        bad=copy.deepcopy(original)
        row=next(r for r in bad['tasks'] if r['added_operations']);row['added_operations'].append(row['added_operations'][0]);variants.append(bad)
        bad=copy.deepcopy(original);bad['tasks'][0]['global_requirements'][0]['evidence'][0]['excerpt']='invented';variants.append(bad)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'annotation.json'
            for value in variants:
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):v3.build(path)

    def test_profiles_reproduce_and_previous_versions_are_unchanged(self):
        paths=[v3.REPO/'results/difficulty/designed_v1/scores.json',v3.REPO/'results/difficulty/designed_v2/profiles.json',v3.REPO/'results/difficulty/design_review_run_v1/combined_summary.json']
        before={p:file_hash(p) for p in paths}
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a';b=Path(folder)/'b'
            v3.write_outputs(a,self.doc);v3.write_outputs(b,v3.build())
            for f in a.iterdir():self.assertEqual(f.read_bytes(),(b/f.name).read_bytes())
            with self.assertRaisesRegex(ValueError,'fresh'):v3.write_outputs(a,self.doc)
            with self.assertRaisesRegex(ValueError,'overlaps'):v3.write_outputs(v3.DATA_DIR/'output',self.doc)
        self.assertEqual(before,{p:file_hash(p) for p in paths})


if __name__=='__main__':unittest.main()
