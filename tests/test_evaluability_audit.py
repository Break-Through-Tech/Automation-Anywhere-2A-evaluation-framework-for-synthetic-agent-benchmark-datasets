import ast
import unittest

from difficulty.audit_evaluability import audit, compare_fields, literal_return


class EvaluabilityAuditTests(unittest.TestCase):
    def test_literal_return_is_inspected_without_executing_function(self):
        tree = ast.parse('''
class Base:
    def lookup(self, identifier):
        raise RuntimeError("must not execute")
        return {"amount": 500.0}
class Case(Base):
    pass
''')
        classes = {n.name: n for n in tree.body}
        found = literal_return(classes, 'Case', 'lookup')
        self.assertEqual(found['value']['amount'], 500.0)
        self.assertIn('if execution reaches', found['scope'])

    def test_multiple_returns_are_unresolved_rather_than_guessed(self):
        tree = ast.parse('''
class Case:
    def lookup(self, flag):
        if flag:
            return {"status": "ok"}
        return {"status": "failed"}
''')
        self.assertIsNone(literal_return({'Case': tree.body[0]}, 'Case', 'lookup'))

    def test_unique_field_matching_preserves_ambiguity_and_partial_objects(self):
        def output(value):
            return {'value':value,'method_line':1,'return_line':2}
        findings = compare_fields([{'step':1,'expected_state':{'amount':100.0,'status':'done',
                    'limits':{'withdrawal':10},'unknown':True}}],
                    {'a':output({'amount':500.0,'status':'done','limits':{'withdrawal':10,'transfer':20}}),
                     'b':output({'status':'done'})})
        by_field = {f['reference_field']:f['finding'] for f in findings}
        self.assertEqual(by_field['amount'],'literal_difference_requires_review')
        self.assertEqual(by_field['status'],'ambiguous_tool_mapping')
        self.assertEqual(by_field['limits'],'literal_subset_match')
        self.assertEqual(by_field['unknown'],'no_exact_static_field_mapping')

    def test_inventory_and_known_fixed_transaction_difference(self):
        result = audit()
        self.assertEqual(result['task_count'],64)
        self.assertEqual(result['domain_count'],7)
        self.assertEqual(result['network_calls'],0)
        self.assertEqual(result['new_tool_executions'],0)
        self.assertTrue(all(r['new_task_judgment'] is None for r in result['tasks']))
        case = next(r for r in result['tasks'] if r['domain']=='banking_fraud_monitoring'
                    and r['task_id']=='BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC2')
        difference = next(f for f in case['field_findings'] if f['reference_field']=='transaction_id')
        self.assertEqual(difference['reference_value'],'TX-20002')
        self.assertEqual(difference['candidate_value'],'TX-998877')
        self.assertEqual(difference['finding'],'literal_difference_requires_review')
