"""Regression tests for the audiobook's exact-narration, no-filler picture gate."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from .scene_locked_quality import check_episode, file_digest, normalized
from .kokoro_cpu_episode import cache_id


class SourceLockedQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "approved_private_episode.txt"
        self.source.write_text("The Golden Core was gone.\n\nBefore the courtyard opened, he had reached the Late Golden Core Stage.\n", encoding="utf-8")
        self.beats = self.root / "private_beats.json"
        self.images = self.root / "images"
        self.images.mkdir()
        self.review = {k: True for k in (
            "inspected_actual_image", "exact_speech_match",
            "period_and_cultivation_correct", "character_and_props_consistent",
            "rights_recorded", "no_bad_text_or_duplicates")}
        self.review["reviewer"] = "unit_test_editor"
        paragraphs = [
            ("The Golden Core was gone.", "present", "empty dantian", "visible golden core"),
            ("Before the courtyard opened, he had reached the Late Golden Core Stage.",
             "memory", "past Golden Core", "present-day alley"),
        ]
        self.rows = []
        for i, (text, period, show, hide) in enumerate(paragraphs):
            img = self.images / f"shot_{i}.png"
            img.write_bytes(b"\x89PNG\r\n" + bytes([i + 40]) * 15000)
            digest = file_digest(img)
            review = copy.deepcopy(self.review)
            review["image_sha256"] = digest
            self.rows.append({
                "id": f"scene_{i}", "text": text, "image": f"images/shot_{i}.png",
                "image_sha256": digest, "visual": {
                    "period": period, "setting": "original fictional setting",
                    "must_show": [show], "must_not_show": [hide],
                    "character_references": []},
                "pixel_review": review})
        self.base = {
            "schema": 1, "story_id": "fictional-test", "episode_id": "ep01",
            "source_sha256": file_digest(self.source),
            "narrator": {"engine": "kokoro", "voice": "am_michael",
                         "speed": 1.25, "post_atempo": 1.0},
            "beats": self.rows}
        self._save()

    def _save(self):
        self.beats.write_text(json.dumps(self.base), encoding="utf-8")

    def _pass(self):
        self._save()
        return check_episode(self.source, self.beats)

    def test_valid_exact_coverage(self):
        x = self._pass()
        self.assertEqual(x["status"], "SOURCE_AND_REVIEW_LEDGER_PASS")
        self.assertEqual(x["total_beats"], 2)

    def test_omitted_line_fails(self):
        self.base["beats"] = self.rows[:1]
        with self.assertRaisesRegex(ValueError, "verbatim"):
            self._pass()

    def test_invented_narration_fails(self):
        self.base["beats"][1]["text"] += " He was king."
        with self.assertRaisesRegex(ValueError, "verbatim"):
            self._pass()

    def test_wrong_present_core_fails(self):
        self.base["beats"][0]["visual"]["must_not_show"] = ["generic background"]
        with self.assertRaisesRegex(ValueError, "vanished core"):
            self._pass()

    def test_former_core_must_be_memory(self):
        self.base["beats"][1]["visual"]["period"] = "present"
        with self.assertRaisesRegex(ValueError, "only in memory"):
            self._pass()

    def test_no_repeat_image_for_different_beats(self):
        self.base["beats"][1]["image"] = self.rows[0]["image"]
        self.base["beats"][1]["image_sha256"] = self.rows[0]["image_sha256"]
        self.base["beats"][1]["pixel_review"]["image_sha256"] = self.rows[0]["image_sha256"]
        with self.assertRaisesRegex(ValueError, "repeated image"):
            self._pass()

    def test_replaced_unreviewed_image_fails(self):
        (self.images / "shot_0.png").write_bytes(b"\x89PNG\r\n" + b"x" * 15000)
        with self.assertRaisesRegex(ValueError, "reviewed SHA"):
            self._pass()

    def test_missing_visual_review_fails(self):
        self.base["beats"][0]["pixel_review"]["exact_speech_match"] = False
        with self.assertRaisesRegex(ValueError, "review is incomplete"):
            self._pass()

    def test_no_double_speed(self):
        self.base["narrator"]["post_atempo"] = 1.25
        with self.assertRaisesRegex(ValueError, "second speed-up"):
            self._pass()

    def test_narrator_identity_locked(self):
        self.base["narrator"]["voice"] = "Ryan"
        with self.assertRaisesRegex(ValueError, "Kokoro Michael"):
            self._pass()

    def test_voice_cache_changes_when_speed_or_text_changes(self):
        a = cache_id("Li Tianming rose.", 1.25)
        self.assertNotEqual(a, cache_id("Li Tianming rose.", 1.10))
        self.assertNotEqual(a, cache_id("Li Tianming sat.", 1.25))


if __name__ == "__main__":
    unittest.main()
