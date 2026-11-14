from copy import deepcopy
import unittest
from difficulty.required_path_repeatability import ROLES, summarize
from difficulty.required_path_calibration import THRESHOLDS


def observations():
    return [{'role': r, 'arm': a, 'repeat': n, 'status': 'scored',
             'score': 40 if r == 'simple_control' else 75}
            for r in sorted(ROLES) for a in ('original', 'clarified') for n in range(3)]


class RepeatabilityTests(unittest.TestCase):
    def test_complete_stable_study_passes_without_automatic_adoption(self):
        r = summarize(observations(), THRESHOLDS)
        self.assertTrue(r['numeric_candidate_gate_pass'])
        self.assertFalse(r['automatic_adoption'])

    def test_missing_result_never_becomes_partial_mean(self):
        data = observations(); item = data.pop()
        r = summarize(data, THRESHOLDS)
        self.assertFalse(r['complete'])
        arm = next(c for c in r['cases'] if c['role']==item['role'])['arms'][item['arm']]
        self.assertIsNone(arm['mean'])

    def test_error_is_not_a_zero_or_convenient_exclusion(self):
        data = observations(); data[0].update(status='api_error', score=None)
        r = summarize(data, THRESHOLDS)
        self.assertFalse(r['numeric_candidate_gate_pass'])
        self.assertEqual(len(r['unusable']), 1)

    def test_original_instability_does_not_invalidate_stable_candidate(self):
        data = observations()
        next(x for x in data if x['role']=='sim_exit' and x['arm']=='original' and x['repeat']==1)['score']=95
        r = summarize(data, THRESHOLDS)
        self.assertFalse(r['arms']['original']['repeatability_pass'])
        self.assertTrue(r['numeric_candidate_gate_pass'])

    def test_candidate_instability_blocks_gate(self):
        data = observations()
        next(x for x in data if x['role']=='sim_exit' and x['arm']=='clarified' and x['repeat']==1)['score']=95
        self.assertFalse(summarize(data, THRESHOLDS)['numeric_candidate_gate_pass'])

    def test_arms_are_not_pooled(self):
        data = observations()
        for x in data:
            if x['role']=='sim_exit' and x['arm']=='clarified': x['score']=50
        case = next(c for c in summarize(data, THRESHOLDS)['cases'] if c['role']=='sim_exit')
        self.assertEqual(case['mean_shift'], -25)
        self.assertEqual(case['arms']['original']['mean'], 75)

    def test_collapsed_complexity_control_blocks_gate(self):
        data = observations()
        for x in data:
            if x['role']=='complex_control' and x['arm']=='clarified': x['score']=40
        self.assertFalse(summarize(data, THRESHOLDS)['numeric_candidate_gate_pass'])

    def test_duplicates_are_rejected(self):
        data = observations(); data.append(deepcopy(data[0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            summarize(data, THRESHOLDS)
