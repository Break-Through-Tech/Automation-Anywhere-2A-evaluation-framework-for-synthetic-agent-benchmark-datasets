import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from difficulty import clarified_design_run as release
from difficulty.design import judge
from difficulty.design.rubric import digest
from difficulty.required_path_calibration import clarified
from test_numeric_design import fixture_case, stub_judgment, FakeResponse


class ClarifiedRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def packet(self, count=1, repeats=1):
        rows=[fixture_case(self.root, str(i)) for i in range(count)]
        old=self.root/'old';judge.prepare_packet(rows,old,'offline-stub-model',repeats=repeats,source_bound_evidence=True)
        m,_,qs=judge.load_packet(old)
        for q in qs:
            q['api_request']=clarified(q['api_request']);q['request_sha256']=digest(q['api_request'])
        p=self.root/'release';p.mkdir()
        manifest={'n_tasks':len(rows),'n_requests':len(qs),'cached_requests':0,'proposed_new_call_cap':len(qs),
            'requests_sha256':digest(qs),'inventory_sha256':digest(rows),'bindings_sha256':digest([])}
        for name,value in [('manifest.json',manifest),('requests.json',qs),('inventory_PRIVATE_COMPARISON.json',rows),('cache_bindings.json',[])]:judge.write_json(p/name,value)
        return p,rows,qs

    def client(self, rows):
        replies=[]
        for i,row in enumerate(rows):
            wire=stub_judgment(row)
            for obj in [*wire['dimensions'].values(),wire['intended_endpoint'],*wire['units']]:obj['evidence']=[{'citation_id':'E0000'}]
            response=FakeResponse(wire);dump=response.model_dump
            response.model_dump=lambda _dump=dump,_id=str(i),**kw:_dump(**kw)|{'id':_id}
            replies.append(response)
        c=Mock();c.responses.create.side_effect=replies;return c

    def test_no_authorization_never_constructs_client(self):
        p,_,_=self.packet()
        with self.assertRaises(PermissionError):release.run(p,1)

    def test_request_mutation_is_rejected_before_spending(self):
        p,_,_=self.packet();q=json.loads((p/'requests.json').read_text());q[0]['api_request']['model']='different';(p/'requests.json').write_text(json.dumps(q))
        with self.assertRaisesRegex(ValueError,'changed'):release.load(p)

    def test_paid_cap_and_resume_do_not_replay_completed_request(self):
        p,rows,_=self.packet(2);c=self.client(rows)
        self.assertEqual(release.run(p,1,authorize_paid=True,client=c)['new_calls_this_invocation'],1)
        self.assertEqual(release.report(p)['datasets']['synthetic']['n_scored'],1)
        self.assertEqual(release.run(p,1,authorize_paid=True,client=c)['new_calls_total'],2)
        self.assertEqual(c.responses.create.call_count,2)
        self.assertEqual(release.run(p,1,authorize_paid=True,client=c)['new_calls_this_invocation'],0)

    def test_first_error_stops_without_retry(self):
        p,_,_=self.packet(3);c=Mock();c.responses.create.side_effect=RuntimeError('offline failure')
        result=release.run(p,3,authorize_paid=True,client=c)
        self.assertEqual(c.responses.create.call_count,1)
        self.assertEqual(result['stop_reason'],'unusable_response_requires_diagnosis')
        with self.assertRaisesRegex(ValueError,'diagnosis'):release.run(p,3,authorize_paid=True,client=c)

    def test_unresolved_intent_is_never_automatically_replayed(self):
        p,_,qs=self.packet();(p/'intents').mkdir();judge.write_json(p/'intents'/(qs[0]['request_id']+'.json'),{})
        with self.assertRaisesRegex(ValueError,'unresolved'):release.run(p,1,authorize_paid=True,client=Mock())

    def test_error_stops_dispatch_with_only_bounded_inflight_calls(self):
        p,_,_=self.packet(5);c=Mock();c.responses.create.side_effect=RuntimeError('offline failure')
        result=release.run(p,5,authorize_paid=True,concurrency=3,client=c)
        self.assertEqual(c.responses.create.call_count,3)
        self.assertEqual(result['stop_reason'],'unusable_response_requires_diagnosis')
        self.assertEqual(result['remaining_requests'],2)

    def test_incomplete_planned_repeats_do_not_yield_a_task_mean(self):
        p,rows,_=self.packet(repeats=3);c=self.client(rows)
        release.run(p,1,authorize_paid=True,client=c)
        task=release.report(p)['tasks'][0]
        self.assertEqual(task['status'],'pending')
        self.assertIsNone(task['score'])
        self.assertEqual(task['n_planned_judgments'],3)


if __name__=='__main__':unittest.main()
