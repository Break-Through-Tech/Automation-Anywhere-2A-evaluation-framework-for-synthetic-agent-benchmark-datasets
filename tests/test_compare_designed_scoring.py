import copy
import json
from pathlib import Path
import tempfile
import unittest

from difficulty import compare_designed_scoring as comparison
from difficulty.saved_trials import file_hash


class ScoringOptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=comparison.build()

    def test_coordination_tags_are_not_added_and_handoff_only_is_excluded(self):
        records=[{'event_key':'ap','kind':'approval'},{'event_key':'ap','kind':'handoff'},
                 {'event_key':'route','kind':'handoff'},{'event_key':'ap','kind':'approval'}]
        self.assertEqual(comparison.additional_coordination_events(records),['ap'])
        records=[{'event_key':'claims','kind':'linked_records'},
                 {'event_key':'routing','kind':'handoff'},{'event_key':'routing','kind':'multi_party'},
                 {'event_key':'experts','kind':'handoff'},{'event_key':'experts','kind':'multi_party'}]
        self.assertEqual(len(comparison.additional_coordination_events(records)),3)

    def test_frozen_scales_and_weight_variants(self):
        values,weights=comparison.candidate_values(11,23,3)
        self.assertTrue(all(v==100 for v in values.values()))
        _,weights=comparison.candidate_values(11,23,0)
        self.assertEqual(weights['0'],100)
        self.assertEqual(weights['0.2'],80)
        for counts in [(12,8,0),(8,24,0),(8,8,4),(-1,2,0),(True,2,0)]:
            with self.assertRaises(ValueError):comparison.candidate_values(*counts)

    def test_examples_demonstrate_a_distinction_not_validation(self):
        r=self.result;self.assertEqual((r['n_tasks'],len(r['reviewed_changed_tasks'])),(64,12))
        self.assertFalse(r['combined_index_adopted'])
        self.assertEqual(r['n_tasks_with_uncertain_global_requirements'],25)
        rows={x['task_id']:x for x in r['tasks']}
        e=rows['InsuranceClaimsIntakeAndTriageAgent_W1_TC1'];c=rows['InsuranceClaimsIntakeAndTriageAgent_W8_TC1']
        self.assertEqual(e['candidate_indices']['workload_only'],c['candidate_indices']['workload_only'])
        self.assertGreater(c['candidate_indices']['workload_coord20'],e['candidate_indices']['workload_coord20'])
        self.assertEqual(r['coordination_weight_sensitivity']['0.2']['max_rank_change_from_no_coordination'],19.5)

    def test_reproducible_comparison_rejects_tampering_and_keeps_profiles(self):
        before=file_hash(comparison.INPUT)
        with tempfile.TemporaryDirectory() as directory:
            a=Path(directory)/'a';b=Path(directory)/'b'
            comparison.write_outputs(a,self.result);comparison.write_outputs(b,comparison.build())
            for f in a.iterdir():self.assertEqual(f.read_bytes(),(b/f.name).read_bytes())
            with self.assertRaisesRegex(ValueError,'fresh'):comparison.write_outputs(a,self.result)
            bad=json.loads(comparison.INPUT.read_text());bad['tasks'][0]['proposed_operation_unit_count']+=1
            source=Path(directory)/'profiles.json';source.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'reproducible'):comparison.build(source)
        self.assertEqual(before,file_hash(comparison.INPUT))


if __name__=='__main__':unittest.main()
