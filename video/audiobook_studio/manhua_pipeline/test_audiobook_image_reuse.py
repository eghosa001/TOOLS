"""Regression tests for intentional illustrated-audiobook still reuse.

The validator checks source/image hashes and reviewer fields, not image semantics.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scene_locked_quality import check_episode


class AudiobookStillReuseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.script = self.root / "source.txt"
        self.script.write_text("At the workshop. Still at the workshop.", encoding="utf8")
        self.image = self.root / "workshop.png"
        # The validator does not decode pixels, only checks size and hashes.
        self.image.write_bytes(b"test-fixture-not-real-image" * 600)
        self.image_hash = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.base_visual = {
            "must_show": ["workshop"],
            "must_not_show": ["unrelated setting"],
            "setting": "workshop",
            "period": "present",
            "character_references": [],
        }

    def _write_manifest(self, reuse_justification=None):
        second_visual = dict(self.base_visual)
        if reuse_justification is not None:
            second_visual["reuse_justification"] = reuse_justification
        data = {
            "schema": 1, "story_id": "fixture-story", "episode_id": "ep1",
            "source_sha256": hashlib.sha256(self.script.read_bytes()).hexdigest(),
            "narrator": {"engine": "kokoro", "voice": "am_michael", "speed": 1.25},
            "beats": [
                {"id": "beat_1", "text": "At the workshop.", "visual": dict(self.base_visual),
                 "image": "workshop.png", "image_sha256": self.image_hash},
                {"id": "beat_2", "text": "Still at the workshop.", "visual": second_visual,
                 "image": "workshop.png", "image_sha256": self.image_hash},
            ],
        }
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(data), encoding="utf8")
        return manifest

    def test_justified_reuse_passes(self):
        manifest = self._write_manifest(
            "The spoken passage remains in the same workshop, without a new visual event."
        )
        result = check_episode(self.script, manifest, require_pixel_review=False)
        self.assertEqual(result["total_beats"], 2)

    def test_unexplained_duplicate_still_fails(self):
        manifest = self._write_manifest()
        with self.assertRaisesRegex(ValueError, "reuse_justification"):
            check_episode(self.script, manifest, require_pixel_review=False)

    def test_empty_reuse_reason_fails(self):
        manifest = self._write_manifest("same")
        with self.assertRaisesRegex(ValueError, "reuse_justification"):
            check_episode(self.script, manifest, require_pixel_review=False)


if __name__ == "__main__":
    unittest.main()
