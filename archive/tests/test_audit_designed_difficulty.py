import copy
import json
from pathlib import Path
import tempfile
import unittest

from difficulty.audit_designed_difficulty import SCORES, audit_document, sensitivity, write_audit
from difficulty.designed_difficulty import COMPONENTS


class DesignedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(SCORES.read_text())

    def test_ties_preserve_boundary_and_do_not_invent_rank_order(self):
        result=audit_document(self.doc)
        self.assertEqual((result['n_distinct_component_profiles'],result['n_tasks_in_tied_profiles'],
                          result['n_tied_profile_groups']),(35,40,11))
        self.assertEqual(len(result['top_band_with_boundary_ties']),8)
        self.assertEqual(len(result['bottom_band_with_boundary_ties']),5)
        byid={r['task_id']:r for r in self.doc['tasks']}
        a=byid['InsuranceClaimsIntakeAndTriageAgent_W1_TC1']
        b=byid['InsuranceClaimsIntakeAndTriageAgent_W8_TC1']
        self.assertEqual(tuple(a[k] for k in COMPONENTS),tuple(b[k] for k in COMPONENTS))
        self.assertEqual(a['score_variants'],b['score_variants'])

    def test_ablation_is_separate_from_ordinary_weight_changes(self):
        result=sensitivity(self.doc['tasks'])
        self.assertEqual(result['action_heavy']['max_absolute_rank_change'],10)
        self.assertEqual(result['tool_heavy']['max_absolute_rank_change'],6)
        self.assertEqual(result['without_checks']['max_absolute_rank_change'],20.5)
        self.assertEqual(result['without_checks']['comparison_type'],'component_removal')
        self.assertEqual(result['action_heavy']['comparison_type'],'weight_change')

    def test_audit_reproduces_and_scores_are_unchanged(self):
        before=SCORES.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a';b=Path(folder)/'b'
            result=write_audit(SCORES,a);write_audit(SCORES,b)
            self.assertTrue(result['no_api_calls'])
            self.assertFalse(result['scores_changed'])
            for name in ['audit.json','README.md']:
                self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())
            with self.assertRaisesRegex(ValueError,'fresh'):write_audit(SCORES,a)
        self.assertEqual(before,SCORES.read_bytes())

    def test_audit_rejects_a_score_that_does_not_reproduce(self):
        changed=copy.deepcopy(self.doc);changed['tasks'][0]['score']+=1
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'scores.json';path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'exact reproducible'):
                write_audit(path,Path(folder)/'out')


if __name__=='__main__':unittest.main()
