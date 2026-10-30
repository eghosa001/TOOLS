"""Structural regression checks; no video is generated."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import pipeline
import quality_gate


class NinefoldPipelineTests(unittest.TestCase):
    def setUp(self):
        self.s = pipeline.read_json(HERE / "pilot_shots.json")
        self.a = pipeline.read_json(HERE / "asset_register.json")

    def test_exact_12_shots_and_720_frames(self):
        self.assertEqual(12, len(self.s["shots"]))
        self.assertFalse(pipeline.validate(self.s, self.a, HERE, "structure"))

    def test_explicit_asset_register_catches_unknown(self):
        s = copy.deepcopy(self.s)
        s["shots"][0]["asset_ids"].append("invented_asset")
        self.assertTrue(any("unknown asset" in x for x in pipeline.validate(s, self.a, HERE, "structure")))

    def test_gaps_and_overlaps_are_rejected(self):
        s = copy.deepcopy(self.s)
        s["shots"][1]["start_frame"] = 59
        self.assertTrue(pipeline.validate(s, self.a, HERE, "structure"))

    def test_unapproved_work_cannot_be_assembled(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(pipeline.validate(self.s, self.a, Path(tmp), "assembly"))

    def test_quality_toolbox_requires_all_production_capabilities(self):
        report = pipeline.doctor()
        for name in ("Krita", "OpenToonz", "Blender", "Godot", "Audacity", "Kdenlive", "Rhubarb Lip Sync", "Piper", "ffmpeg", "ffprobe"):
            self.assertIn(name, report["tools"])
        self.assertEqual(report["full_toolchain_ready"], not bool(report["missing_tools"]))

    def test_finished_look_review_is_blocked_without_actual_media(self):
        template = pipeline.read_json(HERE / "first_proof_review_template.json")
        failures = quality_gate.assess(template, None)
        self.assertGreater(len(failures), 10)
        self.assertTrue(any("Missing real finished-look" in failure for failure in failures))

    def test_init_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "test"
            self.assertEqual(4, len(pipeline.init(root)["new_files"]))
            self.assertEqual(0, len(pipeline.init(root)["new_files"]))
            self.assertTrue((root / "07_review" / "ep101_first_proof.json").is_file())


if __name__ == "__main__":
    unittest.main()
