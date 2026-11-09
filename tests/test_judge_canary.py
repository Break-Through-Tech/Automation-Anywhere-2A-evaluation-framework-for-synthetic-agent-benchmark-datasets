import unittest
from difficulty.judge_canary import stop_reason


class JudgeCanaryTests(unittest.TestCase):
    def test_wrong_control_label_stops_after_one_request(self):
        self.assertIn('control label mismatch', stop_reason([
            {'status':'accepted','task_judgment':'unverifiable','expected_judgment':'met'}]))

    def test_stops_after_one_validation_failure(self):
        self.assertIsNotNone(stop_reason([{'status': 'rejected_response'}]))

    def test_stops_after_two_non_successes_without_calling_them_agent_failures(self):
        checks = [{'status': 'accepted', 'task_judgment': j} for j in ['unmet', 'unverifiable']]
        self.assertIn('does not prove agent failure', stop_reason(checks))
        self.assertIsNotNone(stop_reason([{**c, 'task_judgment': 'unverifiable'} for c in checks]))

    def test_never_auto_expands_beyond_three(self):
        good = {'status': 'accepted', 'task_judgment': 'met'}
        self.assertIsNone(stop_reason([]))
        self.assertIsNone(stop_reason([good]))
        self.assertIsNone(stop_reason([good, good]))
        self.assertIn('limit', stop_reason([good, good, good]))
