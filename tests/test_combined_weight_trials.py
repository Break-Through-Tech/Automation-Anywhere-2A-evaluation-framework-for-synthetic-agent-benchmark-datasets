from copy import deepcopy
import unittest
from difficulty.combined_weight_trials import prepare_inputs, trial


def fixtures():
    labels=[{'dataset':'tau2','agent_category':'airline','task_id':'airline:0','workflow_keys':'a'},
            {'dataset':'tau2','agent_category':'airline','task_id':'airline:1','workflow_keys':'b'},
            {'dataset':'synthetic','agent_category':'bank','task_id':'one','workflow_keys':'x'}]
    catalog=[{'dataset':d,'agent_category':g,'workflow_key':k} for d,g,keys in [('tau2','airline',['a','b']),('synthetic','bank',['x','y'])] for k in keys]
    tasks=[{'dataset':d,'domain':g,'task_id':tid,'score':s,'status':'scored'} for d,g,tid,s in [('tau2','airline','0',50),('tau2','airline','1',50),('synthetic','bank','one',60)]]
    return labels,catalog,{'release_protocol':'designed_difficulty_v1.1_required_path','tasks':tasks}


class CombinedWeightTests(unittest.TestCase):
    def test_normalization_and_known_contributions(self):
        data=prepare_inputs(*fixtures());r={x['dataset']:x for x in trial(data,.5)}
        self.assertEqual(r['tau2']['combined_index_0_100'],75)
        self.assertEqual(r['synthetic']['combined_index_0_100'],42.5)
        for x in r.values():self.assertAlmostEqual(x['coverage_contribution_0_100']+x['difficulty_contribution_0_100'],x['combined_index_0_100'])

    def test_endpoints_preserve_input_scale(self):
        data=prepare_inputs(*fixtures())
        self.assertEqual(next(x for x in trial(data,0) if x['dataset']=='synthetic')['combined_index_0_100'],60)
        self.assertEqual(next(x for x in trial(data,1) if x['dataset']=='synthetic')['combined_index_0_100'],25)

    def test_missing_or_duplicate_inventory_is_rejected(self):
        for duplicate in (False,True):
            labels,cat,diff=fixtures()
            if duplicate:labels.append(deepcopy(labels[0]))
            else:labels.pop()
            with self.assertRaisesRegex(ValueError,'inventory'):prepare_inputs(labels,cat,diff)

    def test_unknown_workflow_and_unscored_case_are_rejected(self):
        labels,cat,diff=fixtures();labels[0]['workflow_keys']='unknown'
        with self.assertRaisesRegex(ValueError,'workflow'):prepare_inputs(labels,cat,diff)
        labels,cat,diff=fixtures();diff['tasks'][0]['status']='unscorable'
        with self.assertRaisesRegex(ValueError,'Incomplete'):prepare_inputs(labels,cat,diff)

    def test_nonfinite_values_and_invalid_weights_are_rejected(self):
        for bad in (float('nan'),float('inf'),True,101):
            labels,cat,diff=fixtures();diff['tasks'][0]['score']=bad
            with self.assertRaises(ValueError):prepare_inputs(labels,cat,diff)
        data=prepare_inputs(*fixtures())
        for bad in (-.1,1.1,float('nan'),True):
            with self.assertRaises(ValueError):trial(data,bad)

    def test_original_release_is_not_silently_pooled(self):
        labels,cat,diff=fixtures();diff['release_protocol']='old'
        with self.assertRaisesRegex(ValueError,'release'):prepare_inputs(labels,cat,diff)


if __name__=='__main__':unittest.main()
