"""Regression tests for the owner's mandatory MUSIC-FIRST audiobook workflow."""
from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video.audiobook_studio.manhua_pipeline import music_bed
from video.audiobook_studio.manhua_pipeline.assemble_existing import assemble
from video.audiobook_studio.tests.test_episode_quality_gate import example


class MusicFirstTests(unittest.TestCase):
    def test_missing_music_blocks_before_narration_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "E01_MASTER.mp4"
            preflight = Path(temp) / "episode_quality.json"
            preflight.write_text(json.dumps(example()))
            args = argparse.Namespace(
                quality_scorecard=str(preflight),
                output=str(output), audio=str(Path(temp) / "missing_narration.wav"),
                art_policy="full_color_panels", draft_preview=False,
                music_mood="mystery", music_level=.10, music_file=None)
            with self.assertRaisesRegex(ValueError, "MUSIC_FIRST_REQUIRED"):
                assemble(args)

    def test_original_music_preflight_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "E01_MASTER.mp4"
            music_file = Path(temp) / "original_music.wav"
            music_file.write_bytes(b"\x01" * 51200)
            evidence = {
                "status": "MUSIC_BED_READY", "file": str(music_file),
                "sha256": music_bed._hash(music_file),
                "type": "new_original_composition",
                "mood": "mystery", "level": .10, "rights": "new original instrumental"}
            with patch.object(music_bed, "prepare_music", return_value=(music_file, evidence)):
                receipt = music_bed.prebuild_music_before_voice(
                    output, mood="mystery", level=.10)
            self.assertTrue(receipt.is_file())
            review = music_bed.require_music_first_preflight(
                output, mood="mystery", level=.10)
            self.assertEqual(review["status"], "MUSIC_PREPARED_BEFORE_ASSEMBLY")
            self.assertFalse(review["human_audibility_review_completed"])

            with self.assertRaisesRegex(ValueError, "MUSIC_FIRST_EVIDENCE_MISMATCH"):
                music_bed.require_music_first_preflight(output, mood="tension", level=.10)
            with self.assertRaisesRegex(ValueError, "MUSIC_FIRST_EVIDENCE_MISMATCH"):
                music_bed.require_music_first_preflight(output, mood="mystery", level=.04)
            music_file.write_bytes(b"\x02" * 51200)
            with self.assertRaisesRegex(ValueError, "MUSIC_FIRST_EVIDENCE_MISMATCH"):
                music_bed.require_music_first_preflight(output, mood="mystery", level=.10)

    def test_music_mix_is_speech_ducked(self):
        graph = music_bed.music_filter(64.0, .10)
        self.assertIn("sidechaincompress", graph)
        self.assertIn("amix=inputs=2", graph)
        self.assertIn("alimiter", graph)


if __name__ == "__main__":
    unittest.main()
