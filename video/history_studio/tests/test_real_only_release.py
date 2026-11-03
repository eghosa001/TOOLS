#!/usr/bin/env python3
"""History pre-upload tests, no YouTube credentials required."""
import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "youtube_direct" / "verify_real_only_release.py"
spec = importlib.util.spec_from_file_location("history_real_release", MODULE)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def sample(video):
    checksum = hashlib.sha256(video.read_bytes()).hexdigest()
    footage = {
        "id": "s1", "spoken_text": "Actual footage of the harbour.",
        "start_seconds": 0, "end_seconds": 7,
        "shot_subject": "Original recorded harbour scene",
        "why_this_visual": "Genuine footage depicts the specific documented location.",
        "visual_kind": "REAL_FOOTAGE", "editor_approved_by": "Historical editor",
        "editorial_status": "APPROVED",
        "authentic_source_searches": [{
            "query": "original archival harbour film",
            "source_url": "https://www.loc.gov/collections/national-screening-room/",
            "outcome": "Manually selected and reviewed footage"}],
        "asset": {
            "source_page_url": "https://www.loc.gov/collections/national-screening-room/",
            "creator": "Example archivist", "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "file_identity": "Sample-test.mp4",
            "attribution": "Sample test footage, Example archivist, CC BY 4.0",
            "commercial_use_confirmed": True, "modifications_allowed": True,
            "origin_type": "CAMERA_FILM", "non_synthetic_verified": True,
            "authentic_capture_verified": True,
        },
    }
    still = copy.deepcopy(footage)
    still.update({"id": "s2", "start_seconds": 7, "end_seconds": 10,
                  "visual_kind": "ARCHIVAL_PHOTO"})
    still["asset"]["origin_type"] = "CAMERA_PHOTO"
    motion1 = {
        "id": "s1", "start_seconds": 0, "end_seconds": 7,
        "visual_kind": "ARCHIVAL_EVENT_FILM", "non_synthetic_verified": True,
        "capture_type": "CAMERA_FILM", "motion_verified": True,
        "commercial_rights_verified": True, "modifications_allowed": True,
        "source_page_url": "https://www.loc.gov/collections/national-screening-room/",
        "license_evidence_url": "https://creativecommons.org/licenses/by/4.0/",
        "license_name": "CC BY 4.0",
    }
    motion2 = copy.deepcopy(motion1)
    motion2.update({"id": "s2", "start_seconds": 7, "end_seconds": 10,
                    "visual_kind": "STILL_PHOTO", "capture_type": "CAMERA_PHOTO"})
    source = {
        "shots": [footage, still], "master_sha256": checksum,
        "source_first_editorial_approval": "APPROVED",
        "final_editorial_review": {
            "approved_for_facts_uncovered": True,
            "reviewer": "Human historical editor",
            "reviewed_mp4_sha256": checksum,
            "visual_and_audio_review_notes": "Footage and audio individually checked",
        }
    }
    motion = {"shots": [motion1, motion2], "duration_seconds": 10,
              "master_sha256": checksum}
    return source, motion


class RealOnlyReleaseTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.video = Path(self.folder.name) / "film.mp4"
        self.video.write_bytes(b"Fixture MP4 hash; tests verify ledgers only, not media decoding")
        self.source, self.motion = sample(self.video)

    def tearDown(self):
        self.folder.cleanup()

    def verify(self):
        return release.verify(self.video, self.source, self.motion)

    def test_verified_real_only_footage_passes(self):
        self.assertEqual(self.verify()["status"], "PASS")

    def test_ai_image_rejected(self):
        self.source["shots"][1]["visual_kind"] = "AI_ART"
        self.assertEqual(self.verify()["status"], "FAIL")

    def test_ai_video_rejected(self):
        self.motion["shots"][0]["visual_kind"] = "ORIGINAL_RECONSTRUCTION_FILM"
        self.assertEqual(self.verify()["status"], "FAIL")

    def test_no_commercial_rights_rejected(self):
        self.motion["shots"][0]["commercial_rights_verified"] = False
        self.assertEqual(self.verify()["status"], "FAIL")

    def test_edited_master_after_review_rejected(self):
        self.video.write_bytes(b"Changed video since editorial review")
        self.assertEqual(self.verify()["status"], "FAIL")

    def test_missing_editorial_approval_rejected(self):
        self.source.pop("final_editorial_review")
        self.assertEqual(self.verify()["status"], "FAIL")

    def test_different_storyboards_rejected(self):
        self.motion["shots"][1]["start_seconds"] = 8
        self.assertEqual(self.verify()["status"], "FAIL")

    def test_untested_thumbnail_rejected(self):
        thumb = Path(self.folder.name) / "thumb.jpg"
        thumb.write_bytes(b"Real sample thumbnail image")
        self.assertEqual(release.verify(self.video,self.source,self.motion,thumb)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
