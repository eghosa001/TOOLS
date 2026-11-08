"""Synthetic-only tests for the owner-mandated permanent full-color workflow."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from video.audiobook_studio.manhua_pipeline.color_panel_policy import (
    full_color_check, validate_color_panel_timeline,
)


def make_image(path, rgb):
    Image.new("RGB", (896, 504), rgb).save(path)


def entry(path, speech, *, panel, seconds=6.0):
    return {
        "story_id": "sample-original-story",
        "episode_id": "episode-01",
        "page_id": "sheet-01",
        "panel_id": panel,
        "image": path.name,
        "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_excerpt": speech,
        "source_sha256": hashlib.sha256(speech.encode()).hexdigest(),
        "seconds": seconds,
    }


class PermanentColorPanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.color_a = self.root / "color_a.png"
        self.color_b = self.root / "color_b.png"
        self.gray = self.root / "grayscale.png"
        self.tint = self.root / "almost_gray.png"
        make_image(self.color_a, (50, 110, 165))
        make_image(self.color_b, (185, 105, 55))
        make_image(self.gray, (105, 105, 105))
        make_image(self.tint, (105, 108, 109))
        self.script = self.root / "approved_source.txt"
        self.script.write_text("An engineer opened a door. The guard approached. They returned home.")
        self.timeline = self.root / "timeline.json"

    def validate(self, scenes, *, duration=18.0):
        return validate_color_panel_timeline(
            scenes, timeline_path=self.timeline,
            source_text=self.script, narration_seconds=duration
        )

    def test_accepts_full_color_and_reuses_one_panel_nonadjacently(self):
        beats = [
            entry(self.color_a, "An engineer opened a door.", panel="left"),
            entry(self.color_b, "The guard approached.", panel="right"),
            entry(self.color_a, "They returned home.", panel="left"),
        ]
        result = self.validate(beats)
        self.assertEqual(result["shots"], 3)
        self.assertEqual(result["distinct_images_checked"], 2)
        self.assertEqual(result["unique_source_pages"], 1)
        self.assertTrue(result["technical_color_gate_passed"])
        self.assertFalse(result["semantics_verified_by_automation"])

    def test_black_and_white_and_faint_tints_are_rejected(self):
        for image in (self.gray, self.tint):
            with self.subTest(image=image.name):
                with self.assertRaisesRegex(ValueError, "FULL_COLOR_REQUIRED"):
                    full_color_check(image)

    def test_full_color_thumbnail_is_allowed(self):
        self.assertTrue(full_color_check(self.color_a)["technical_full_color"])

    def test_rejects_grayscale_panel_inside_colored_episode(self):
        beats = [
            entry(self.color_a, "An engineer opened a door.", panel="left"),
            entry(self.gray, "The guard approached.", panel="middle"),
            entry(self.color_b, "They returned home.", panel="right"),
        ]
        with self.assertRaisesRegex(ValueError, "FULL_COLOR_REQUIRED"):
            self.validate(beats)

    def test_rejects_spoken_source_omission(self):
        beats = [entry(self.color_a, "An engineer opened a door.", panel="left")]
        with self.assertRaisesRegex(ValueError, "SOURCE_COVERAGE_FAILED"):
            self.validate(beats, duration=6.0)

    def test_rejects_tampered_image(self):
        beat = entry(self.color_a, self.script.read_text(), panel="left", seconds=18)
        beat["image_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "IMAGE_HASH_FAILED"):
            self.validate([beat])

    def test_rejects_consecutive_fake_shots(self):
        beats = [
            entry(self.color_a, "An engineer opened a door.", panel="left"),
            entry(self.color_a, "The guard approached.", panel="left"),
            entry(self.color_b, "They returned home.", panel="right"),
        ]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ADJACENT_PANEL"):
            self.validate(beats)

    def test_rejects_incorrect_duration(self):
        beats = [entry(self.color_a, self.script.read_text(), panel="left", seconds=10)]
        with self.assertRaisesRegex(ValueError, "AUDIO_SYNC_FAILED"):
            self.validate(beats, duration=18.0)

    def test_source_is_mandatory(self):
        beat = entry(self.color_a, self.script.read_text(), panel="left", seconds=18)
        with self.assertRaisesRegex(ValueError, "SOURCE_REQUIRED"):
            validate_color_panel_timeline(
                [beat], timeline_path=self.timeline,
                source_text=None, narration_seconds=18.0
            )

    def test_rejects_wrong_story_lookbook_mix(self):
        beats = [
            entry(self.color_a, "An engineer opened a door.", panel="left"),
            entry(self.color_b, "The guard approached.", panel="right"),
            entry(self.color_a, "They returned home.", panel="left"),
        ]
        beats[1]["story_id"] = "other-story"
        with self.assertRaisesRegex(ValueError, "STORY_MIXING_FORBIDDEN"):
            self.validate(beats)


if __name__ == "__main__":
    unittest.main()
