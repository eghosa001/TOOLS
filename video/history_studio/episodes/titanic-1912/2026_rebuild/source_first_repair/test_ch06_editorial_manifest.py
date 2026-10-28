#!/usr/bin/env python3
"""Regression tests for manually selected Chapter06 archive research.

Research candidates are intentionally not approved footage; no video is built.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class Chapter06SafetyTests(unittest.TestCase):
    def test_exact_18_spoken_paragraph_cues_are_individually_authored(self):
        plan = json.loads((HERE / "CHAPTER06_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())
        baseline = json.loads((ROOT / "MANUAL_SCENE_LEDGER_DRAFT.json").read_text())
        original = {row["scene_id"]: row for row in baseline["scenes"] if row["chapter"] == 6}
        choices = plan["shots"]
        self.assertEqual(len(original), 18)
        self.assertEqual(len(choices), 18)
        self.assertEqual(set(original), {row["scene_id"] for row in choices})
        self.assertEqual(len({row["scene_id"] for row in choices}), 18)
        for shot in choices:
            self.assertEqual(shot["original_spoken_paragraph"],
                             original[shot["scene_id"]]["narration_paragraph"])
            self.assertIsNone(shot["shot_in_seconds"])
            self.assertIsNone(shot["shot_out_seconds"])
            self.assertFalse(shot["original_narration_alignment_approved"])
            self.assertFalse(shot["complete_audiovisual_playback_editor_approved"])
            self.assertFalse(shot["publication_approved"])

    def test_named_source_choices_and_no_silent_licence_approvals(self):
        data = json.loads((HERE / "CHAPTER06_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())
        photos = [s for s in data["shots"] if s["visual_kind"] == "photo"]
        diagrams = [s for s in data["shots"] if s["visual_kind"] == "graphic"]
        self.assertEqual((len(photos), len(diagrams)), (11, 7))
        for shot in data["shots"]:
            self.assertTrue(shot["source_page_url"].startswith("https://"))
            self.assertTrue(shot["editorial_why"])
            self.assertTrue(shot["manual_composition"])
            self.assertFalse(shot["commercial_licence_editor_approved"])
            self.assertIsNone(shot["source_file_sha256"])
        self.assertEqual(data["authentic_candidate_beats"], 11)
        self.assertIn("PENDING", data["editorial_status"])


if __name__ == "__main__":
    unittest.main()
