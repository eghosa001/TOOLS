"""Regression tests for canon-linked Season One character/world readiness."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "animation" / "tools"))
import s1_readiness as m


class S1CanonReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in (m.CAST, m.CHARACTERS, m.WORLD, m.CAM):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, p)

    def change(self, rel, fn):
        p = self.root / rel
        doc = json.loads(p.read_text(encoding="utf8"))
        fn(doc)
        p.write_text(json.dumps(doc), encoding="utf8")

    def test_verified_intake_is_not_approved_art(self):
        r = m.validate(self.root)
        self.assertEqual(r["tracked_character_roles"], 20)
        self.assertEqual(r["pilot_leads"], 3)
        self.assertEqual(r["pilot_physical_objects"], 10)
        self.assertEqual(r["critical_episode_stages"], 8)
        self.assertFalse(r["artwork_ready"])
        self.assertFalse(r["world_ready"])
        self.assertFalse(r["full_production_ready"])

    def test_cast_age_drift_blocked(self):
        self.change(m.CHARACTERS, lambda d: d["regular_cast"][0].update(age=19))
        with self.assertRaisesRegex(ValueError, "age drift"):
            m.validate(self.root)

    def test_false_character_approval_blocked(self):
        self.change(m.CHARACTERS, lambda d: d["priority_leads"][0].update(human_art_approved=True))
        with self.assertRaisesRegex(ValueError, "falsely art-approved"):
            m.validate(self.root)

    def test_missing_view_blocked(self):
        self.change(m.CHARACTERS, lambda d: d["priority_leads"][0]["view_sources"].pop("profile"))
        with self.assertRaisesRegex(ValueError, "missing turnaround"):
            m.validate(self.root)

    def test_height_drift_blocked(self):
        self.change(m.CHARACTERS, lambda d: d["priority_leads"][2].update(height_cm=164))
        with self.assertRaisesRegex(ValueError, "height drift"):
            m.validate(self.root)

    def test_rope_reassignment_blocked(self):
        self.change(m.WORLD, lambda d: next(a for a in d["physical_objects"] if a["id"] == "heavy_hawser").update(mobility="fixed"))
        with self.assertRaisesRegex(ValueError, "three ropes conflated"):
            m.validate(self.root)

    def test_camera_shift_blocked(self):
        self.change(m.WORLD, lambda d: d["camera_reference"].update(hand_target_m=[2, 2, 2]))
        with self.assertRaisesRegex(ValueError, "contact drift"):
            m.validate(self.root)

    def test_damaged_glider_continuity_blocked(self):
        self.change(m.WORLD, lambda d: next(a for a in d["cross_episode_state"] if a["asset"] == "kito_full_glider").update(transition="still_flying"))
        with self.assertRaisesRegex(ValueError, "prop state drift"):
            m.validate(self.root)

    def test_e112_gate_stage_cannot_disappear(self):
        self.change(m.WORLD, lambda d: d["episode_geography"].pop())
        with self.assertRaisesRegex(ValueError, "missing critical staging"):
            m.validate(self.root)


if __name__ == "__main__":
    unittest.main()
