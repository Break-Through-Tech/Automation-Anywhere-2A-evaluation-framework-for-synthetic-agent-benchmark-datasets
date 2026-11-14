import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import run_all
from difficulty import designed_difficulty as dd
from difficulty.llm_judge import load_synthetic_cases
from difficulty.structural_features import extract


class DesignedDifficultyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = dd.build()

    def test_normalization_weights_and_invalid_values(self):
        zero = dict.fromkeys(dd.COMPONENTS, 0)
        self.assertEqual(dd.score_counts(zero)[0], 0)
        self.assertEqual(dd.score_counts(dd.SCALES)[0], 100)
        for counts in [{**zero, 'action_groups': -1}, {**zero, 'action_groups': True},
                       {**zero, 'reference_tool_interactions': 24}]:
            with self.assertRaises(ValueError): dd.score_counts(counts)
        with self.assertRaises(ValueError): dd.score_counts(zero, dict.fromkeys(dd.COMPONENTS, .5))

    def test_all_tasks_and_exact_evidence_resolve(self):
        doc = self.document
        self.assertEqual((doc['task_count'], doc['domain_count'], doc['network_calls']), (64, 7, 0))
        self.assertEqual(len({(r['domain'],r['task_id']) for r in doc['tasks']}),64)
        for row in doc['tasks']:
            self.assertIsNone(row['exact_atomic_action_count'])
            self.assertIsNone(row['exact_independent_decision_count'])
            self.assertTrue(0 <= row['score'] <= 100)
            self.assertAlmostEqual(row['score'],sum(row['weighted_points'].values()), places=5)
            for evidence in row['milestone_evidence']:
                value=json.loads((dd.DATA_DIR/evidence['source']).read_text())
                for key in evidence['locator'][2:].split('/'):
                    value=value[int(key)] if isinstance(value,list) else value[key]
                self.assertEqual(value,evidence['expected_description'])

    def test_scenario_groups_exclude_passive_and_terminal_work(self):
        byid={r['task_id']:r for r in self.document['tasks']}
        self.assertEqual(byid['HealthcarePA_W8_TC1']['action_groups'],3)
        self.assertEqual(byid['HealthcarePA_W8_TC1']['shared_workflow_steps_comparison_only'],5)
        c=byid['HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1']
        self.assertEqual((c['action_groups'],c['excluded_external_groups'],c['excluded_terminal_groups']), (5,1,1))
        self.assertEqual(c['reference_tool_interactions'],8)
        b=byid['ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1']
        self.assertEqual((b['action_groups'],b['business_check_groups']), (3,1))

    def test_supplied_tags_are_not_score_inputs_and_semantic_tie_is_exposed(self):
        features=extract()
        for row in features['tasks']:row['class_difficulty_tag']='changed_comparison_label'
        with patch.object(dd,'extract',return_value=features): changed=dd.build()
        self.assertEqual([r['score'] for r in self.document['tasks']], [r['score'] for r in changed['tasks']])
        byid={r['task_id']:r for r in self.document['tasks']}
        e=byid['InsuranceClaimsIntakeAndTriageAgent_W1_TC1']
        f=byid['InsuranceClaimsIntakeAndTriageAgent_W8_TC1']
        self.assertEqual(e['score'],f['score'])
        self.assertEqual(e['rank_easy_first'],f['rank_easy_first'])
        self.assertIn('milestone_groups_may_bundle_multiple_actions_or_entities',f['uncertainty_flags'])

    def test_annotation_drift_duplicates_and_missing_tasks_rejected(self):
        original=json.loads(dd.ANNOTATIONS.read_text());features=extract();cases=load_synthetic_cases()
        variants=[]
        duplicate=copy.deepcopy(original);duplicate['tasks'].append(duplicate['tasks'][0]);variants.append(duplicate)
        missing=copy.deepcopy(original);missing['tasks'].pop();variants.append(missing)
        changed=copy.deepcopy(original);changed['tasks'][0]['milestones'][0]['expected_description']='invented';variants.append(changed)
        stale=copy.deepcopy(original);stale['source_sha256']={};variants.append(stale)
        for variant in variants:
            with self.assertRaises(ValueError): dd.validate_annotations(variant,features,cases)

    def test_framework_loader_rejects_altered_scores_and_missing_identity(self):
        tasks=[{'dataset':'synthetic','domain':r['domain'],'task_id':r['task_id']} for r in self.document['tasks']]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'scores.json';path.write_text(json.dumps(self.document))
            _,mapping,_=dd.load_scores_for_framework(path,tasks);self.assertEqual(len(mapping),64)
            wrong=copy.deepcopy(self.document);wrong['tasks'][0]['score']+=1;path.write_text(json.dumps(wrong))
            with self.assertRaisesRegex(ValueError,'reproducible'): dd.load_scores_for_framework(path,tasks)
            path.write_text(json.dumps(self.document))
            with self.assertRaisesRegex(ValueError,'exactly once'): dd.load_scores_for_framework(path,tasks[:-1])

    def test_outputs_reproduce_and_refuse_overwrite_or_supplied_data(self):
        with tempfile.TemporaryDirectory() as directory:
            a=Path(directory)/'a';b=Path(directory)/'b'
            dd.write_outputs(a,self.document);dd.write_outputs(b,dd.build())
            self.assertEqual(sorted(p.name for p in a.iterdir()), sorted(p.name for p in b.iterdir()))
            for p in a.iterdir():self.assertEqual(p.read_bytes(),(b/p.name).read_bytes())
            with self.assertRaisesRegex(ValueError,'fresh'): dd.write_outputs(a,self.document)
            with self.assertRaisesRegex(ValueError,'overlap'): dd.write_outputs(dd.DATA_DIR/'new_output',self.document)

    def test_optional_framework_attachment_preserves_empirical_results(self):
        with tempfile.TemporaryDirectory() as directory:
            scores=Path(directory)/'scores.json';scores.write_text(json.dumps(self.document))
            args=run_all.parser().parse_args(['--synthetic-designed-scores',str(scores),
                                             '--output-dir',str(Path(directory)/'framework')])
            vectors=np.tile(np.array([[1.,0.],[0.,1.]]),(171,1))
            with patch.object(run_all,'embed',return_value=vectors),patch.object(run_all,'scatter'),contextlib.redirect_stdout(io.StringIO()):
                summary=run_all.evaluate(args)
            self.assertEqual(summary['synthetic_designed_index']['n_tasks'],64)
            with (args.output_dir/'difficulty_tasks.csv').open() as source:
                rows=list(csv.DictReader(source))
            self.assertEqual(len(rows),342)
            self.assertEqual(sum(bool(r['designed_index_score']) for r in rows),64)
            self.assertTrue(all(not r['designed_index_score'] for r in rows if r['dataset']=='tau2'))
            self.assertEqual(summary['datasets']['synthetic']['empirical_tasks_scored'],47)
            metadata=json.loads((args.output_dir/'run_metadata.json').read_text())
            self.assertTrue(any(k.endswith('designed_annotations_v1.json') for k in metadata['inputs']))


if __name__=='__main__': unittest.main()
