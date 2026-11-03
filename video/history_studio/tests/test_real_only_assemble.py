#!/usr/bin/env python3
"""Only genuine, licensed media can reach the single documentary preview renderer."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
module = HERE.parent / "real_only_assemble.py"
spec = importlib.util.spec_from_file_location("real_only_assemble", module)
assembly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembly)

fixture_spec = importlib.util.spec_from_file_location(
    "history_release_fixture", HERE / "test_real_only_release.py")
fixture = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(fixture)


class PreviewPlanTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        film = self.root / "camera_original.mp4"
        photo = self.root / "real_camera_photo.jpg"
        audio = self.root / "narration.wav"
        for path, data in ((film, b"Recorded source film fixture"),
                           (photo, b"Physical camera photograph fixture"),
                           (audio, b"Recorded original narration fixture")):
            path.write_bytes(data)
        self.source, self.motion = fixture.sample(film)
        for shot, path in zip(self.source["shots"], (film, photo)):
            shot["asset"]["local_path"] = path.name
            shot["asset"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.source["audio"] = {
            "local_path": audio.name,
            "sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
            "commercial_rights_verified": True,
            "source_description": "Commercially authorized original recorded narration",
        }

    def tearDown(self):
        self.folder.cleanup()

    def validate(self):
        with patch.object(assembly, "probe_seconds", return_value=10.0):
            return assembly.review_plan(self.source, self.motion, self.root)

    def test_real_camera_film_and_photo_are_permitted(self):
        self.assertEqual(self.validate()["real_film_share"], 0.7)

    def test_synthetic_footage_rejected(self):
        self.motion["shots"][0]["visual_kind"] = "ORIGINAL_RECONSTRUCTION_FILM"
        with self.assertRaises(ValueError):
            self.validate()

    def test_ai_image_rejected(self):
        self.source["shots"][1]["visual_kind"] = "AI_ART"
        with self.assertRaises(ValueError):
            self.validate()

    def test_mismatched_source_image_rejected(self):
        self.source["shots"][1]["asset"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate()

    def test_unauthorized_audio_rejected(self):
        self.source["audio"]["commercial_rights_verified"] = False
        with self.assertRaises(ValueError):
            self.validate()

    def test_wrong_timing_rejected(self):
        self.motion["shots"][1]["start_seconds"] = 9
        with self.assertRaises(ValueError):
            self.validate()

    def test_unverified_camera_photo_rejected(self):
        self.source["shots"][1]["asset"]["non_synthetic_verified"] = False
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == "__main__":
    unittest.main()
