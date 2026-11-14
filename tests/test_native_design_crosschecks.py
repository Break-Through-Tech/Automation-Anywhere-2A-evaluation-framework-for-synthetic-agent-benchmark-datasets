"""Reference diagnostics must preserve absent evidence and source meaning."""
import json
import unittest

from difficulty.native_design_crosschecks import reference_features, leaves


def row(dataset, calls, completion=True):
    source = {'path':'fixture.json','locator':'#/case','sha256':'fixture-hash'}
    if dataset=='synthetic':
        catalog=[{'source_id':'reference_calls','text':json.dumps(calls)}]
        sources={'reference_calls':source}
    else:
        endpoint={'actions':calls,'nl_assertions':['Refuse'] if completion else [],
                  'communicate_info':[], 'env_assertions':None}
        catalog=[{'source_id':'completion_design','text':json.dumps(endpoint)}]
        catalog += [{'source_id':f'reference_{i+1:03}','text':json.dumps(c)} for i,c in enumerate(calls)]
        sources={'completion_design':source}
    return {'dataset':dataset,'payload':{'source_catalog':catalog},'sources':sources}


class ReferenceDesignChecks(unittest.TestCase):
    def test_shared_nonterminal_definition_and_repeats(self):
        synthetic=[{'name':'lookup','tool_inputs':{'id':'x'}},
                   {'name':'lookup','tool_inputs':{'id':'y'}},
                   {'name':'SUCCESS','tool_inputs':{}}]
        native=[{'name':'lookup','arguments':{'id':'x'}},
                {'name':'lookup','arguments':{'id':'y'}}]
        a=reference_features(row('synthetic',synthetic))
        b=reference_features(row('tau2',native))
        self.assertEqual(a['features'],b['features'])
        self.assertEqual(a['features']['reference_tool_interactions'],2)
        self.assertEqual(a['features']['repeated_reference_calls'],1)
        self.assertEqual(len(a['excluded_terminal_signals']),1)
        self.assertEqual(b['counted_calls'][1]['source']['locator'],'#/case/actions/1')

    def test_empty_list_and_missing_completion_are_distinct(self):
        explicit=reference_features(row('tau2',[],completion=True))
        missing=reference_features(row('tau2',[],completion=False))
        self.assertEqual(explicit['features']['reference_tool_interactions'],0)
        self.assertEqual(explicit['reference_status'],'documented_list')
        self.assertTrue(all(v is None for v in missing['features'].values()))
        self.assertEqual(missing['reference_status'],'unavailable')

    def test_native_transfer_is_not_excluded_as_a_terminal(self):
        v=reference_features(row('tau2',[{'name':'transfer_to_human_agents','arguments':{'summary':'problem'}}]))
        self.assertEqual(v['features']['reference_tool_interactions'],1)

    def test_nested_argument_leaves_do_not_count_collections(self):
        self.assertEqual(leaves({'empty':[], 'none':None, 'records':[{'a':1,'b':2},{}]}),3)

    def test_duplicate_unit_representation_is_not_double_counted(self):
        v=row('tau2',[{'name':'lookup','arguments':{}}])
        self.assertEqual(reference_features(v)['features']['reference_tool_interactions'],1)
        v['payload']['source_catalog'].append({'source_id':'reference_002','text':json.dumps({'name':'extra','arguments':{}})})
        with self.assertRaisesRegex(ValueError,'differs'):
            reference_features(v)

    def test_bad_argument_evidence_is_rejected_not_zero(self):
        v=row('synthetic',[{'name':'lookup'}])
        with self.assertRaisesRegex(ValueError,'arguments'):
            reference_features(v)

    def test_python_reference_expression_is_static_and_dynamic_values_are_missing(self):
        v=row('synthetic',[])
        v['payload']['source_catalog'][0]['text']='[ # comment\n {"name": "lookup", "tool_inputs": {"id": input_data["id"]}}]'
        features=reference_features(v)
        self.assertEqual(features['features']['reference_tool_interactions'],1)
        self.assertIsNone(features['features']['reference_argument_leaves'])
        self.assertEqual(features['reference_representation'],'static_python_expression')

    def test_python_calls_inside_arguments_are_never_executed(self):
        v=row('synthetic',[])
        v['payload']['source_catalog'][0]['text']='[{"name": "lookup", "tool_inputs": danger()}]'
        self.assertIsNone(reference_features(v)['features']['reference_argument_leaves'])


if __name__=='__main__':
    unittest.main()
