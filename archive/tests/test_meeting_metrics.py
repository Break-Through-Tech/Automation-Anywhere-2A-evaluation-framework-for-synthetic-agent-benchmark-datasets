import unittest
from difficulty.meeting_metrics import runtime_summary, build

class DifficultyReportingTests(unittest.TestCase):
    def row(self,n,outcome,eligible,blocked=False):
        return dict(domain='example',task_id='task',trial=n,outcome=outcome,
                    execution_eligible=eligible,environment_blocked=blocked,
                    source_policy='test_rules',exclusion_reason='' if eligible else 'excluded with evidence')

    def test_noncompletion_with_blocker_is_logged_but_not_difficulty(self):
        rows=[self.row(0,'pass',True),self.row(1,'fail',True),
              self.row(2,'fail',False,True),self.row(3,'unverifiable',False)]
        r=runtime_summary(rows)[0]
        self.assertEqual(r['n_fail_logged'],2)
        self.assertEqual(r['n_eligible'],2)
        self.assertEqual(r['execution_difficulty'],.5)

    def test_unassessed_is_not_a_fourth_outcome_or_unverifiable(self):
        r=runtime_summary([self.row(0,None,False),self.row(1,'unverifiable',False)])[0]
        self.assertEqual(r['n_unassessed'],1)
        self.assertEqual(r['n_unverifiable_logged'],1)
        self.assertIsNone(r['execution_difficulty'])

    def test_rejects_mixed_policies_and_ineligible_contributions(self):
        rows=[self.row(0,'pass',True),self.row(1,'fail',True)]
        rows[1]['source_policy']='other'
        with self.assertRaises(ValueError):runtime_summary(rows)
        with self.assertRaises(ValueError):runtime_summary([self.row(0,'fail',True,True)])
        with self.assertRaises(ValueError):runtime_summary([self.row(0,'unverifiable',True)])
        with self.assertRaises(ValueError):runtime_summary([rows[0],rows[0]])

    def test_original_inventory_and_historical_policy_are_preserved(self):
        summary,features,ledger,tasks=build()
        self.assertEqual(len(features),64);self.assertEqual(len(ledger),256)
        self.assertEqual(len(tasks),64)
        self.assertEqual(summary['execution']['n_assessed'],16)
        self.assertEqual(summary['execution']['n_unassessed'],240)
        self.assertEqual(summary['execution']['logged_outcomes'],{'unverifiable':16})
        self.assertIsNone(summary['execution']['execution_difficulty'])
        self.assertEqual(summary['overall']['supplied_label_counts'],{'easy':43,'hard':3,'medium':18})
