"""Offline production gates: prevent technical proofs from becoming final animation."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shot_gate


class ProductionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        def asset(filename, image=False):
            p = self.root / filename
            p.parent.mkdir(parents=True, exist_ok=True)
            if image:
                Image.new("RGBA", (64, 64), (70, 90, 100, 255)).save(p)
            else:
                p.write_text("Reviewer evidence\n", encoding="utf8")
            return {"path": filename, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        self.asset = asset
        self.data = {
            "schema_version": 1, "episode": "E101", "camera": "CAM03B",
            "fps": 24, "frame_count": 2, "resolution": [64, 64],
            "canon": [
                {"role": role, "url": "https://docs.google.com/document/d/verified-doc/edit",
                 "reviewed_by": "Example Reviewer"}
                for role in sorted(shot_gate.CANON_ROLES)
            ],
            "approvals": {name: {"approved": True, "reviewer": "Example Reviewer",
                                  "evidence": asset(f"reviews/{name}.txt")}
                          for names in shot_gate.STAGE_APPROVALS.values() for name in names},
            "drawings": {
                kind: [asset(f"{kind}/pose.png", True)]
                for types in shot_gate.DRAWING_GROUPS.values() for kind in types
            },
            "sequence": {"directory": "export/frames"},
            "picture_review": {
                name: {"passed": True, "reviewer": "Example Reviewer",
                       "evidence": asset(f"reviews/{name}.txt")}
                for name in shot_gate.REVIEW_CHECKS
            },
        }
        for i in range(1, 3):
            asset(f"export/frames/frame_{i:06d}.png", True)
        ledger = shot_gate.index_sequence(self.data, self.root, self.root / "reviews/frame_ledger.json")
        self.assertEqual(2, len(ledger["frames"]))
        self.data["sequence"]["ledger"] = self.asset_ledger()

    def asset_ledger(self):
        p = self.root / "reviews/frame_ledger.json"
        return {"path": "reviews/frame_ledger.json", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    def test_can_review_complete_approved_sequence_without_granting_release(self):
        result = shot_gate.validate(self.data, self.root, "export")
        self.assertEqual("PASS", result["status"])
        self.assertFalse(result["release_approved"])

    def test_missing_canon_approval_is_blocked(self):
        self.data["approvals"]["canon"]["approved"] = False
        with self.assertRaisesRegex(shot_gate.ShotGateError, "canon"):
            shot_gate.validate(self.data, self.root, "intake")

    def test_missing_breakdowns_and_unapproved_keys_block(self):
        self.data["drawings"]["breakdowns"] = []
        with self.assertRaisesRegex(shot_gate.ShotGateError, "breakdowns"):
            shot_gate.validate(self.data, self.root, "keys")

    def test_changed_art_is_blocked(self):
        (self.root / "keys/pose.png").write_bytes(b"changed")
        with self.assertRaisesRegex(shot_gate.ShotGateError, "checksum"):
            shot_gate.validate(self.data, self.root, "keys")

    def test_missing_inbetween_is_blocked(self):
        self.data["drawings"]["inbetweens"] = []
        with self.assertRaisesRegex(shot_gate.ShotGateError, "inbetweens"):
            shot_gate.validate(self.data, self.root, "frames")

    def test_missing_frame_is_blocked(self):
        (self.root / "export/frames/frame_000002.png").unlink()
        with self.assertRaisesRegex(shot_gate.ShotGateError, "continuous"):
            shot_gate.validate(self.data, self.root, "frames")

    def test_unreviewed_contact_blocks_export(self):
        self.data["picture_review"]["hand_rail_contact"]["passed"] = False
        with self.assertRaisesRegex(shot_gate.ShotGateError, "hand_rail_contact"):
            shot_gate.validate(self.data, self.root, "export")

    def test_outside_path_rejected(self):
        self.data["drawings"]["keys"][0]["path"] = "../escape.png"
        with self.assertRaises(shot_gate.ShotGateError):
            shot_gate.validate(self.data, self.root, "keys")

    def test_fake_ledger_blocks(self):
        ledger = json.loads((self.root / "reviews/frame_ledger.json").read_text())
        ledger["frames"]["frame_000001.png"] = "0" * 64
        (self.root / "reviews/frame_ledger.json").write_text(json.dumps(ledger))
        self.data["sequence"]["ledger"] = self.asset_ledger()
        with self.assertRaisesRegex(shot_gate.ShotGateError, "checksum"):
            shot_gate.validate(self.data, self.root, "frames")


if __name__ == "__main__":
    unittest.main()
