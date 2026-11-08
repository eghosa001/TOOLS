"""Offline tests: one audiobook standard works for unrelated original stories."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from .scene_locked_quality import check_episode, file_digest
from .kokoro_cpu_episode import cache_id


class UniversalAudiobookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "approved_episode.txt"
        self.beats = self.root / "beats.json"
        (self.root / "images").mkdir()
        self._story(
            story_id="lantern-story",
            passages=[
                ("The lantern was extinguished.", "present", "unlit lantern", "visible flame"),
                ("Yesterday, it lit the entire hall.", "memory", "bright lantern in the old hall", "modern control panel"),
            ],
        )

    def _story(self, *, story_id, passages):
        self.source.write_text("\n\n".join(p[0] for p in passages) + "\n", encoding="utf-8")
        beats = []
        for i, (text, period, positive, negative) in enumerate(passages):
            picture = self.root / "images" / f"{story_id}-{i}.png"
            picture.write_bytes(b"\x89PNG\r\n" + bytes([i+50]) * 15000)
            image_hash = file_digest(picture)
            beats.append({
                "id": f"shot_{i}", "text": text,
                "image": f"images/{picture.name}", "image_sha256": image_hash,
                "visual": {
                    "period": period,
                    "setting": story_id + " fictional setting",
                    "must_show": [positive],
                    "must_not_show": [negative],
                    "character_references": []
                },
                "pixel_review": {
                    "reviewer": "unit_test_human_editor",
                    "inspected_actual_image": True,
                    "exact_speech_match": True,
                    "period_and_world_state_correct": True,
                    "character_and_props_consistent": True,
                    "rights_recorded": True,
                    "no_bad_text_or_duplicates": True,
                    "image_sha256": image_hash,
                },
            })
        self.data = {
            "schema": 1, "story_id": story_id, "episode_id": "ep01",
            "source_sha256": file_digest(self.source),
            "narrator": {"engine": "kokoro", "voice": "am_michael",
                         "speed": 1.25, "post_atempo": 1.0},
            "beats": beats,
        }
        self._save()

    def _save(self):
        self.beats.write_text(json.dumps(self.data), encoding="utf-8")

    def _run(self, **kw):
        self._save()
        return check_episode(self.source, self.beats, **kw)

    def test_mystery_story_passes(self):
        result = self._run()
        self.assertEqual(result["story_id"], "lantern-story")
        self.assertEqual(result["total_beats"], 2)

    def test_unrelated_space_story_passes_without_cultivation(self):
        self._story(
            story_id="space-station",
            passages=[
                ("The airlock sealed.", "present", "closed airlock", "open airlock"),
                ("A red alert flashed across the console.", "present", "red alert on console", "quiet blank monitor"),
            ],
        )
        result = self._run()
        self.assertEqual(result["story_id"], "space-station")
        self.assertEqual(result["total_beats"], 2)

    def test_missing_narration_fails(self):
        self.data["beats"].pop()
        with self.assertRaisesRegex(ValueError, "verbatim"):
            self._run()

    def test_invented_narration_fails(self):
        self.data["beats"][0]["text"] += " The world ended."
        with self.assertRaisesRegex(ValueError, "verbatim"):
            self._run()

    def test_story_state_restrictions_required(self):
        self.data["beats"][0]["visual"]["must_not_show"] = []
        with self.assertRaisesRegex(ValueError, "disallowed contradictions"):
            self._run()

    def test_story_specific_period_required(self):
        self.data["beats"][1]["visual"]["period"] = ""
        with self.assertRaisesRegex(ValueError, "present from flashback"):
            self._run()

    def test_duplicate_frame_rejected(self):
        self.data["beats"][1]["image"] = self.data["beats"][0]["image"]
        self.data["beats"][1]["image_sha256"] = self.data["beats"][0]["image_sha256"]
        self.data["beats"][1]["pixel_review"]["image_sha256"] = self.data["beats"][0]["image_sha256"]
        with self.assertRaisesRegex(ValueError, "repeated image"):
            self._run()

    def test_stale_image_rejected(self):
        image = self.root / self.data["beats"][0]["image"]
        image.write_bytes(b"\x89PNG\r\n" + b"x" * 15000)
        with self.assertRaisesRegex(ValueError, "reviewed SHA"):
            self._run()

    def test_mismatched_editor_review_rejected(self):
        self.data["beats"][0]["pixel_review"]["exact_speech_match"] = False
        with self.assertRaisesRegex(ValueError, "review is incomplete"):
            self._run()

    def test_story_world_review_required(self):
        self.data["beats"][0]["pixel_review"]["period_and_world_state_correct"] = False
        with self.assertRaisesRegex(ValueError, "review is incomplete"):
            self._run()

    def test_no_double_speedup(self):
        self.data["narrator"]["post_atempo"] = 1.25
        with self.assertRaisesRegex(ValueError, "second speed-up"):
            self._run()

    def test_approved_default_voice(self):
        self.data["narrator"]["voice"] = "Ryan"
        with self.assertRaisesRegex(ValueError, "Kokoro Michael"):
            self._run()

    def test_cache_invalidates_when_speed_or_text_changes(self):
        a = cache_id("The airlock sealed.", 1.25)
        self.assertNotEqual(a, cache_id("The airlock sealed.", 1.10))
        self.assertNotEqual(a, cache_id("The airlock opened.", 1.25))

    def test_shared_source_has_no_story_canon(self):
        base = Path(__file__).resolve().parent
        rules = (base / "scene_locked_quality.py").read_text()
        standard = (base.parent / "CURRENT_PRODUCTION_DEFAULT_2026-11-08.md").read_text()
        for canon in ("Eternal Dao", "The Graves That Answer", "Golden Core", "Li Tianming", "Wen Qingshi"):
            self.assertNotIn(canon, rules)
            self.assertNotIn(canon, standard)


if __name__ == "__main__":
    unittest.main()
