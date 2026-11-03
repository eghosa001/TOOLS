#!/usr/bin/env python3
"""Regression tests: photos rendered into MP4 never qualify as real video footage."""
import importlib.util
import unittest
from pathlib import Path

mod_path = Path(__file__).resolve().parents[1] / "video_motion_gate.py"
spec = importlib.util.spec_from_file_location("video_motion_gate", mod_path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def shot(kind, a, b, ident="s1"):
    entry = {"id": ident, "visual_kind": kind,
             "start_seconds": a, "end_seconds": b,
             "non_synthetic_verified": True,
             "commercial_rights_verified": True,
             "modifications_allowed": True,
             "source_page_url": "https://www.loc.gov/collections/national-screening-room/",
             "license_evidence_url": "https://www.loc.gov/collections/national-screening-room/",
             "license_name": "PUBLIC DOMAIN"}
    if kind in gate.MOTION_KINDS:
        entry["capture_type"] = "CAMERA_FILM"
        entry["motion_verified"] = True
        if kind != "ARCHIVAL_EVENT_FILM":
            entry["on_screen_disclosure"] = "Period footage — not the event"
    else:
        entry["capture_type"] = "CAMERA_PHOTO"
    return entry

class FootageFirstTests(unittest.TestCase):
    def test_photo_montage_rejected_even_if_encoded_as_mp4(self):
        data = {"shots": [shot("STILL_PHOTO", 0, 90)]}
        self.assertEqual(gate.validate(data)["status"], "FAIL")

    def test_verified_moving_footage_with_some_photos_passes(self):
        data = {"shots": [shot("ARCHIVAL_EVENT_FILM", 0, 70),
                          shot("STILL_PHOTO", 70, 100, "s2")]}
        self.assertEqual(gate.validate(data)["status"], "PASS")

    def test_period_film_without_context_label_rejected(self):
        s = shot("PERIOD_CONTEXT_FILM", 0, 100)
        del s["on_screen_disclosure"]
        self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")

    def test_unlicensed_moving_footage_rejected(self):
        s = shot("ARCHIVAL_EVENT_FILM", 0, 100)
        s["commercial_rights_verified"] = False
        self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")

    def test_missing_or_overlapping_timeline_rejected(self):
        data = {"shots": [shot("ARCHIVAL_EVENT_FILM", 0, 70),
                          shot("STILL_PHOTO", 75, 100, "s2")]}
        self.assertEqual(gate.validate(data)["status"], "FAIL")

    def test_unverified_motion_rejected(self):
        s = shot("ARCHIVAL_EVENT_FILM", 0, 100)
        s["motion_verified"] = False
        self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")

    def test_ai_generated_moving_video_is_forbidden(self):
        for kind in ("AI_VIDEO", "ORIGINAL_RECONSTRUCTION_FILM", "CGI"):
            with self.subTest(kind=kind):
                s = shot(kind, 0, 100)
                self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")

    def test_ai_generated_photo_is_forbidden(self):
        s = shot("AI_STILL", 0, 100)
        self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")

    def test_real_video_cannot_just_claim_ai_is_false(self):
        s = shot("ARCHIVAL_EVENT_FILM", 0, 100)
        s["non_synthetic_verified"] = False
        self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")

    def test_unlicensed_still_rejected(self):
        s = shot("STILL_PHOTO", 0, 40)
        s["commercial_rights_verified"] = False
        self.assertEqual(gate.validate({"shots": [s], "min_motion_share": 0.01})["status"], "FAIL")

    def test_missing_permission_evidence_rejected(self):
        s = shot("ARCHIVAL_EVENT_FILM", 0, 100)
        s.pop("license_evidence_url")
        self.assertEqual(gate.validate({"shots": [s]})["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
