"""Offline checks for the paired budget, cached judgments and staged request integrity."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from difficulty import required_path_calibration as study
from difficulty.design import inputs, judge
from difficulty.design.rubric import digest
from test_numeric_design import stub_judgment, FakeResponse


class PairedStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        source=self.root/'source.txt';source.write_text('Read the source; apply the rule; record the result.')
        cases=[];self.rows=[]
        for i in range(6):
            name=['sim','airline','retail','fraud','C01','C02'][i]
            b=inputs.CaseBuilder('validation_fixture' if i>=4 else 'synthetic','fixture',name,None,self.root)
            b.add('S',source.read_text(),source,'whole fixture','scenario');b.unit('U1','S','task_requirements')
            row=b.finish();self.rows.append(row);p=self.root/f'base_{i}';judge.prepare_packet([row],p,'offline-model',source_bound_evidence=True)
            wire=stub_judgment(row)
            for a in [*wire['dimensions'].values(),wire['intended_endpoint'],*wire['units']]:a['evidence']=[{'citation_id':'E0000'}]
            response=FakeResponse(wire);dump=response.model_dump
            response.model_dump=lambda _dump=dump,_id=f'baseline_{i}',**kw:_dump(**kw)|{'id':_id}
            client=Mock();client.responses.create.return_value=response
            judge.run_packet(p,authorize_paid=True,client=client)
            q=judge.load_packet(p)[2][0];cases.append({'role':name,'packet':str(p),'request_id':q['request_id']})
        # A separate fake clarified response, never a paid call.
        p=self.root/'clarified';p.mkdir();base_q=judge.load_packet(self.root/'base_0')[2][0]
        q=deepcopy(base_q);q['request_id']='cached_clarified';q['api_request']=study.clarified(q['api_request']);q['request_sha256']=digest(q['api_request'])
        row=self.rows[0];wire=stub_judgment(row)
        for a in [*wire['dimensions'].values(),wire['intended_endpoint'],*wire['units']]:a['evidence']=[{'citation_id':'E0000'}]
        raw=FakeResponse(wire).model_dump();raw['id']='clarified_cache'
        for name in ('raw','results'):(p/name).mkdir()
        judge.write_json(p/'raw/cached_clarified.json',raw)
        value,arithmetic=judge.canonical_judgment(wire,row)
        result={'status':'validated','validator_version':judge.VALIDATOR_VERSION,'request_sha256':q['request_sha256'],'input_sha256':row['input_sha256'],'model_judgment':wire,'judgment':value,'score_arithmetic':arithmetic,'request_binding':judge.request_binding(wire,row),'evidence_diagnostics':judge.evidence_diagnostics(value,row),'returned_model':raw['model'],'response_id':raw['id'],'raw_sha256':inputs.file_hash(p/'raw/cached_clarified.json')}
        judge.write_json(p/'results/cached_clarified.json',result);judge.write_json(p/'requests.json',[q]);judge.write_json(p/'inventory_PRIVATE_COMPARISON.json',[row])
        self.selection={'cases':cases,'cached_clarified':{'packet':str(p),'request_id':q['request_id']}}

    def tearDown(self):self.temp.cleanup()

    def test_preparation_reuses_seven_exact_judgments_without_api(self):
        with patch('openai.OpenAI',side_effect=AssertionError('Must not construct API client')):
            m=study.prepare(self.selection,self.root/'study')
        self.assertEqual((m['total_planned_judgments'],m['cached_judgments'],m['proposed_new_call_cap']),(36,7,29))
        self.assertEqual((len(m['phase1']),len(m['phase2_interleaved_order'])),(5,24))
        self.assertTrue(m['phase2_requires_phase1_review'])
        self.assertEqual(len(list((self.root/'study/results').glob('*.json'))),7)

    def test_request_mutation_is_rejected(self):
        out=self.root/'study';study.prepare(self.selection,out);p=out/'requests.json';qs=json.loads(p.read_text());qs[-1]['api_request']['model']='other';p.write_text(json.dumps(qs))
        with self.assertRaisesRegex(ValueError,'fingerprints'):study.check(out)

    def test_stage_order_and_threshold_mutation_are_rejected(self):
        out=self.root/'study';study.prepare(self.selection,out);p=out/'manifest.json';m=json.loads(p.read_text());m['phase1'].reverse();p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'scheduling'):study.check(out)
        m['thresholds']['max_repeat_range']=100;p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'fingerprints'):study.check(out)

    def test_cached_raw_tampering_is_rejected(self):
        out=self.root/'study';study.prepare(self.selection,out);p=next((out/'raw').glob('*.json'));p.write_text('{}')
        with self.assertRaisesRegex(ValueError,'raw response'):study.check(out)

    def test_duplicate_case_is_rejected(self):
        selection=deepcopy(self.selection);selection['cases'][1].update(packet=selection['cases'][0]['packet'],request_id=selection['cases'][0]['request_id'])
        with self.assertRaisesRegex(ValueError,'duplicate'):study.prepare(selection,self.root/'study')


if __name__=='__main__':unittest.main()
