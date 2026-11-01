import contextlib
import csv
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np

import run_all
from coverage.attribute_diversity import compute_attribute_diversity, normalized_entropy
from coverage.vendi_score import vendi_score


class FrameworkTests(unittest.TestCase):
    def test_entropy_known_distributions_and_unknown_categories(self):
        self.assertEqual(normalized_entropy(Counter(a=5), ["a", "b"]), 0)
        self.assertAlmostEqual(normalized_entropy(Counter(a=5, b=5), ["a", "b"]), 1)
        self.assertEqual(normalized_entropy(Counter(), []), 0)
        self.assertEqual(normalized_entropy(Counter(a=5), ["a"]), 0)
        with self.assertRaises(ValueError):
            normalized_entropy(Counter(other=1), ["a", "b"])

    def test_vendi_identical_orthogonal_and_repeated_tasks(self):
        self.assertAlmostEqual(vendi_score(np.ones((5, 3))), 1)
        self.assertAlmostEqual(vendi_score(np.eye(4)), 4)
        # Duplicating all tasks preserves raw VS, but halves normalized VS.
        self.assertAlmostEqual(vendi_score(np.tile(np.eye(4), (2, 1))), 4)

    def test_saved_attributes_are_preserved(self):
        args = run_all.parser().parse_args([])
        tasks, labels = run_all.load_inputs(args.tasks, args.labels_dir)
        counts, scores = compute_attribute_diversity(labels)
        expected = run_all.read_csv(run_all.ROOT / "coverage/attribute_scores.csv")
        self.assertEqual(scores, [{**r, "score": float(r["score"])} for r in expected])
        self.assertEqual(len(tasks), 342)
        self.assertEqual(len(counts), len(run_all.read_csv(run_all.ROOT / "coverage/attribute_counts.csv")))

    def test_structural_scores_preserve_both_existing_implementations(self):
        args = run_all.parser().parse_args([])
        tasks, _ = run_all.load_inputs(args.tasks, args.labels_dir)
        actual = run_all.structural_difficulty(tasks, args.tasks, args.tau_tool_labels,
                                              args.synthetic_tool_labels)
        expected = []
        for p in ("difficulty/write_counts.csv", "results/difficulty/tau2_write_counts.csv"):
            expected.extend(run_all.read_csv(run_all.ROOT / p))
        by_key = {(r["dataset"], r["domain"], r["task_id"]): r for r in actual}
        self.assertEqual(len(by_key), 342)
        for row in expected:
            observed = by_key[(row["dataset"], row["domain"], row["task_id"])]
            self.assertEqual(observed["num_write"], int(row["num_write"]))
            self.assertEqual(observed["num_actions"], int(row["num_actions"]))

    def test_missing_labels_are_rejected(self):
        args = run_all.parser().parse_args([])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "labels_tau2.csv").write_text("task_id,domain,task_type,tools\n")
            with self.assertRaisesRegex(ValueError, "labels must match"):
                run_all.load_inputs(args.tasks, path)

    def test_trial_validation_and_infra_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trials.csv"
            header = "domain,task_id,trial,reward,passed\n"
            path.write_text(header + "airline,0,0,1.0,1\nairline,0,1,,0\n")
            score = run_all.empirical_difficulty(path, {("airline", "0")})[("airline", "0")]
            self.assertEqual((score["n_trials"], score["n_valid"], score["difficulty"]), (2, 1, 0))
            for body in ("airline,0,0,1.0,1\nairline,0,0,1.0,1\n",
                         "airline,unknown,0,1.0,1\n", "airline,0,0,nan,0\n",
                         "airline,0,0,1.0,0\n"):
                with self.subTest(body=body):
                    path.write_text(header + body)
                    with self.assertRaises(ValueError):
                        run_all.empirical_difficulty(path, {("airline", "0")})

    def test_runner_outputs_and_absent_synthetic_trials(self):
        with tempfile.TemporaryDirectory() as directory:
            args = run_all.parser().parse_args(["--output-dir", directory])
            args.synthetic_trials = None
            # Exercise orchestration without downloading a model in the unit test.
            vectors = np.tile(np.array([[1.0, 0.0], [0.0, 1.0]]), (171, 1))
            with patch.object(run_all, "embed", return_value=vectors), \
                 patch.object(run_all, "scatter"), contextlib.redirect_stdout(io.StringIO()):
                summary = run_all.evaluate(args)
            tau = summary["datasets"]["tau2"]
            synthetic = summary["datasets"]["synthetic"]
            self.assertEqual((tau["n_tasks"], tau["empirical_trials_valid"]), (278, 1112))
            self.assertAlmostEqual(tau["mean_empirical_difficulty"], 240 / 1112, places=7)
            self.assertEqual(synthetic["empirical_tasks_scored"], 0)
            self.assertIsNone(synthetic["mean_empirical_difficulty"])
            path = Path(directory)
            self.assertEqual(len(run_all.read_csv(path / "difficulty_tasks.csv")), 342)
            validation = json.loads((path / "difficulty_validation.json").read_text())
            self.assertEqual(validation["tau2"]["airline"]["rho"], .6507)

    def test_framework_rejects_a_still_running_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({"planned_trials": 256}))
            args = run_all.parser().parse_args([])
            args.synthetic_trials = root / "trials.csv"
            with self.assertRaisesRegex(ValueError, "still incomplete"):
                run_all.evaluate(args)


if __name__ == "__main__":
    unittest.main()
