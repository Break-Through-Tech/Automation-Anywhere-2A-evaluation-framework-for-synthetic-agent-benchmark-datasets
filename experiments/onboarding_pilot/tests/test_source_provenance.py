"""Relocation must not bypass the pilot's source-integrity checks."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from experiments.onboarding_pilot.run import saved_sources_match


class SourceProvenanceTests(unittest.TestCase):
    def test_relocation_requires_matching_current_sources_and_original_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            original = b'original implementation\n'
            previous = {"sources": {"baseline/onboarding_pilot/grader.py": hashlib.sha256(original).hexdigest()}}
            current = {"experiments/onboarding_pilot/grader.py": "current-hash"}
            snapshot = out / "source_snapshot/baseline/onboarding_pilot/grader.py"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_bytes(original)
            self.assertFalse(saved_sources_match(out, previous, current))
            record = {"original_sources": previous["sources"], "current_sources": current}
            (out / "relocation.json").write_text(json.dumps(record))
            self.assertTrue(saved_sources_match(out, previous, current))
            self.assertFalse(saved_sources_match(out, previous, {**current, "new.py": "changed"}))
            snapshot.write_bytes(b'changed implementation\n')
            self.assertFalse(saved_sources_match(out, previous, current))
            snapshot.unlink()
            self.assertFalse(saved_sources_match(out, previous, current))

    def test_unmoved_sources_still_use_original_exact_hash_check(self):
        with tempfile.TemporaryDirectory() as directory:
            sources = {"grader.py": "original-hash"}
            self.assertTrue(saved_sources_match(Path(directory), {"sources": sources}, sources))
            self.assertFalse(saved_sources_match(Path(directory), {"sources": sources}, {"grader.py": "changed"}))


if __name__ == "__main__":
    unittest.main()
