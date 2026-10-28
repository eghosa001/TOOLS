"""Tests for fail-closed studio gates; no Blender, FFmpeg or paid services needed."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import quality_gate as q


class StudioGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {
            "concept": "Original 30-second marble-run design with five planned beats",
            "duration_seconds": 30,
            "preview_file": "render/sample.mp4",
            "final_file": "render/final.mp4",
            "manually_directed_shots": [
                {"start_seconds": 0, "end_seconds": 15,
                 "visual_intent": "Top-down view of marble spirals",
                 "movement": "One marble rolling along the track",
                 "sound_cue": "Rolling marble and three clicks",
                 "source_and_rights": "Original scene built in Blender"},
                {"start_seconds": 15, "end_seconds": 30,
                 "visual_intent": "Marbles converge into a single row",
                 "movement": "Acceleration through a narrowing gate",
                 "sound_cue": "Closely synchronized marble collisions",
                 "source_and_rights": "Original scene built in Blender"},
            ],
        }
        (self.root / "render").mkdir()
        self.preview = self.root / self.plan["preview_file"]
        self.preview.write_bytes(b"representative-example-preview")
        self.final = self.root / self.plan["final_file"]
        self.final.write_bytes(b"example-master")
        self.manifest = self.root / "production.json"
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.plan), encoding="utf-8")

    def approve_preview(self):
        self.plan["preview_review"] = {
            "approved": True, "reviewer": "Video editor",
            "reviewed_preview_sha256": q.sha256(self.preview),
            "observations": "Watched moving marbles and heard each impact at its matching moment.",
            "visual_score": 9, "motion_score": 9, "audio_sync_score": 9,
            "satisfaction_score": 9, "blocking_issues": [],
        }

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_unapproved_preview_blocks(self, _):
        with self.assertRaisesRegex(q.GateError, "not been personally approved"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_exact_approved_preview_passes(self, _):
        self.approve_preview()
        self.assertEqual(q.check_preview(self.plan, self.root), q.sha256(self.preview))

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_modified_preview_invalidates_approval(self, _):
        self.approve_preview()
        self.preview.write_bytes(b"modified file")
        with self.assertRaisesRegex(q.GateError, "changed after approval"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_substandard_review_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["motion_score"] = 8
        with self.assertRaisesRegex(q.GateError, "motion_score"):
            q.check_preview(self.plan, self.root)

    def test_discontinuous_manual_timeline_blocks(self):
        self.plan["manually_directed_shots"][1]["start_seconds"] = 15.8
        self.save()
        with self.assertRaisesRegex(q.GateError, "gap, overlap"):
            q.load_plan(self.manifest)

    @patch.object(q, "media_info", return_value={"duration": 30, "width": 1080, "height": 1920})
    def test_release_requires_explicit_final_review(self, mocked):
        self.approve_preview()
        def fake_media(p):
            return {"duration": 5, "width": 540, "height": 960} if p == self.preview else {
                "duration": 30, "width": 1080, "height": 1920}
        mocked.side_effect = fake_media
        with self.assertRaisesRegex(q.GateError, "not approved"):
            q.check_final(self.plan, self.root)
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Viewed the entire 30-second film and inspected every audio beat.",
            "blocking_issues": [],
        }
        self.assertEqual(q.check_final(self.plan, self.root), q.sha256(self.final))

    def test_timeout_stops_renderer(self):
        log = self.root / "timeout.log"
        with self.assertRaisesRegex(q.GateError, "stopped after"):
            q.run_limited([sys.executable, "-c", "import time; time.sleep(10)"], 0.1, log)
        self.assertTrue(log.exists())


if __name__ == "__main__":
    unittest.main()
