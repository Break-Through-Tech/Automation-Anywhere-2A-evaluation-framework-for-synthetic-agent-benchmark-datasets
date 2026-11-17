"""No model calls: preserve frozen inputs and limit the proposed prompt-only test."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from difficulty import required_path_probe as probe
from difficulty.design import inputs, judge


class RequiredPathProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.packets=[]
        source=self.root/'source.txt';source.write_text('Check the state; escalate when required.')
        for i in range(4):
            builder=inputs.CaseBuilder('synthetic','fixture',str(i),None,self.root)
            builder.add('scenario',source.read_text(),source,'whole document','scenario')
            builder.unit('task','scenario','task_requirements')
            packet=self.root/f'original_{i}'
            judge.prepare_packet([builder.finish()],packet,'offline-model',source_bound_evidence=True)
            self.packets.append(packet)

    def tearDown(self):
        self.tmp.cleanup()

    def test_prepare_never_calls_api_and_only_appends_system_guidance(self):
        with patch('openai.OpenAI',side_effect=AssertionError('No API during preparation')):
            result=probe.prepare(self.packets,self.root/'probe')
        self.assertEqual(result['api_calls'],0)
        self.assertEqual(result['proposed_call_cap'],4)
        self.assertFalse(result['published_scores_changed'])
        request=json.loads((self.root/'probe/requests.json').read_text())[0]['api_request']
        original=judge.load_packet(self.packets[0])[2][0]['api_request']
        self.assertEqual(request['input'][1],original['input'][1])
        self.assertEqual(request['text'],original['text'])
        self.assertTrue(request['input'][0]['content'].startswith(original['input'][0]['content']))
        self.assertIn('Once a decisive mandatory exit is established',request['input'][0]['content'])

    def test_changed_request_is_rejected(self):
        out=self.root/'probe';probe.prepare(self.packets,out)
        path=out/'requests.json';value=json.loads(path.read_text());value[0]['api_request']['max_output_tokens']=1;path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'fingerprints'):
            probe.check(out)

    def test_changed_clarification_is_rejected(self):
        out=self.root/'probe';probe.prepare(self.packets,out)
        modified=self.root/'draft.md';modified.write_text(probe.ADDENDUM.read_text().replace('Once a decisive','After a decisive'))
        with patch.object(probe,'ADDENDUM',modified):
            with self.assertRaisesRegex(ValueError,'fingerprints'):
                probe.check(out)

    def test_unbounded_or_duplicate_selection_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Exactly four'):
            probe.prepare(self.packets[:3],self.root/'small')
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            probe.prepare([self.packets[0]]*4,self.root/'duplicate')

    def test_original_source_change_is_rejected(self):
        out=self.root/'probe';probe.prepare(self.packets,out)
        (self.root/'source.txt').write_text('Changed source')
        with self.assertRaisesRegex(ValueError,'Changed'):
            probe.check(out)


if __name__=='__main__':
    unittest.main()
