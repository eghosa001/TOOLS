"""Regression checks: fast production must never skip scene meaning or loudness QA."""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from video.audiobook_studio.manhua_pipeline import assemble_existing as a
from video.audiobook_studio.manhua_pipeline import production_audio_gate as g


class ProductionGateTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.picture = self.root / "story_shot.jpg"
        self.picture.write_bytes(b"episode-approved-full-colour-art")
        self.hash = hashlib.sha256(self.picture.read_bytes()).hexdigest()
        self.excerpt = "The wounded guard entered the archive."
        self.source_hash = hashlib.sha256(self.excerpt.encode()).hexdigest()
        self.timeline = self.root / "timeline.json"
        self.timeline.write_text(json.dumps([{
            "image": str(self.picture),
            "image_sha256": self.hash,
            "source_sha256": self.source_hash,
            "source_excerpt": self.excerpt,
            "reused_from_existing_episode": True,
            "reference_art_file": "episode-previous.jpg",
            "seconds": 5.0,
        }]))
        self.report = self.root / "review.json"

    def args(self, *, preview=False, report=True):
        return argparse.Namespace(
            art_policy="full_color_panels", draft_preview=preview,
            require_visual_qa=False,
            visual_qa_report=str(self.report) if report else None,
            timeline=str(self.timeline),
        )

    def review(self, *, current_event=True, reuse_valid=True):
        scene = {
            "source_sha256": self.source_hash,
            "image_sha256": self.hash,
            "status": "AUTOMATED_TRIAGE_PASS",
            "technical_ok": True,
            "image_model_verified": True,
            "requirements": ["approved full-colour look"],
            "source_event_match_verified": current_event,
            "cast_costume_location_verified": True,
            "reuse_suits_this_event": reuse_valid,
            "specific_visual_evidence":
                "The image was inspected at full size against the wounded guard entering an archive.",
        }
        data = {"scenes": [scene], "gate": {
            "automated_visual_triage_passed": True,
            "needs_correction": False,
            "scene_by_scene_review_completed": True,
            "editor_story_match_review_passed": True,
        }}
        self.report.write_text(json.dumps(data))
        return data

    def test_new_episode_blocks_unreviewed_images(self):
        with self.assertRaisesRegex(ValueError, "visual-qa-report"):
            a._verify_visual_evidence(self.args(report=False), [(self.picture, 5)], None)

    def test_internal_draft_is_explicitly_not_approved(self):
        out = a._verify_visual_evidence(self.args(preview=True, report=False),
                                        [(self.picture, 5)], None)
        self.assertEqual(out["status"], "NOT_REVIEWED")
        self.assertFalse(out["source_to_image_verified"])

    def test_new_episode_requires_event_specific_review(self):
        self.review(current_event=False)
        with self.assertRaisesRegex(ValueError, "STORY_IMAGE_MATCH_FAILED"):
            a._verify_visual_evidence(self.args(), [(self.picture, 5)], None)

    def test_old_art_cannot_be_reused_without_story_match(self):
        self.review(reuse_valid=False)
        with self.assertRaisesRegex(ValueError, "STORY_IMAGE_MATCH_FAILED"):
            a._verify_visual_evidence(self.args(), [(self.picture, 5)], None)

    def test_reviewed_appropriate_art_passes_preflight_not_publication(self):
        self.review()
        out = a._verify_visual_evidence(self.args(), [(self.picture, 5)], None)
        self.assertTrue(out["editor_story_match_review_approved"])
        self.assertTrue(out["source_to_image_verified"])
        self.assertFalse(out["human_visual_review_approved"])

    def test_audio_gate_rejects_quiet_or_peaking_sound(self):
        self.assertFalse(g.acceptable({"integrated_lufs": -28.3, "true_peak_dbfs": -8.0}))
        self.assertFalse(g.acceptable({"integrated_lufs": -16, "true_peak_dbfs": 0.0}))
        self.assertTrue(g.acceptable({"integrated_lufs": -16.0, "true_peak_dbfs": -1.7}))

    def test_ebu_r128_extracts_final_summary_not_intermediate_stats(self):
        stderr = """
        [Parsed_ebur128] t: 1.0 I: -33.5 LUFS
        [Parsed_ebur128] Summary:
          Integrated loudness:
            I:         -16.1 LUFS
            Threshold: -26.1 LUFS
          Loudness range:
            LRA: 3.3 LU
          True peak:
            Peak:       -1.5 dBFS
        """
        with mock.patch.object(g.subprocess, "run", return_value=mock.Mock(stderr=stderr)):
            got = g.measured_loudness(self.picture)
        self.assertEqual(got, {"integrated_lufs": -16.1, "true_peak_dbfs": -1.5})


if __name__ == "__main__":
    unittest.main()
