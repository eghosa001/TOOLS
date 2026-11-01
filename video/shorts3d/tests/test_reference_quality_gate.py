#!/usr/bin/env python3
"""Reference quality policy regression tests: never auto-approve a mediocre video."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import reference_quality_gate as gate


class ReferenceGateTests(unittest.TestCase):
    def setUp(self):
        self.registry = gate.load_json(ROOT / "reference_benchmark.json")
        self.board = {
            "seconds": 64,
            "shots": [
                {"id": "shot-01", "spoken": "The cannon hits the masonry", "end_seconds": 64}
            ],
        }
        ref_notes = (
            "The supplied video has visibly textured period stone, purposeful "
            "troop motion, close camera framing and scene-specific interaction."
        )
        self.review = {
            "schema_version": 1,
            "phase": "preproduction",
            "reviewer": "Human art director",
            "reviewed_at_utc": "2026-11-01T07:00:00Z",
            "references_compared": [
                {"id": r["id"], "sha256": r["sha256"],
                 "specific_comparison_notes": ref_notes}
                for r in self.registry["reference_files"]
            ],
            "editorial_scores": {
                key: {"score": 8.5, "observations": ref_notes}
                for key in self.registry["required_review_dimensions"]
            },
            "visual_reference_near_parity_confirmed": True,
            "unresolved_hard_failures": [],
            "media_sha256": "",
            "lookdev_sample_visually_compared": True,
            "preproduction_approved": True,
            "shot_plans": [{
                "shot_id": "shot-01",
                "visible_action": "A documented cannon launches a projectile into a visible wall.",
                "camera_and_motion": "Track the cannonball from muzzle to impact with continuous movement.",
                "why_this_matches_narration": (
                    "The cannon physically fires, the ball hits the period masonry "
                    "and stones move when the spoken passage says the wall is damaged."
                ),
                "assets": [{
                    "title": "Approved 3D period cannon model",
                    "source_url": "https://example.com/asset-source",
                    "license": "CC0-1.0",
                    "license_url": "https://example.com/license",
                    "commercial_reuse_verified": True,
                    "sha256": "a" * 64,
                }],
                "assets_are_final_manual_selection": True,
            }],
        }
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.video = pathlib.Path(self.temp.name) / "review.mp4"
        self.video.write_bytes(b"real local representative fixture" * 1000)
        self.review["media_sha256"] = gate.sha256(self.video)

    def eval(self, phase="preproduction", proofs=None):
        with mock.patch.object(gate, "validate_video", return_value={"streams": []}):
            return gate.evaluate(
                phase, self.registry, self.board, self.review, self.video, proofs
            )

    def test_good_reference_review_preproduction_passes(self):
        self.assertEqual(self.eval()["status"], "PASS_PREPRODUCTION")

    def test_wrong_or_missing_original_reference_blocks(self):
        self.review["references_compared"][0]["sha256"] = "b" * 64
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "hashes"):
            self.eval()

    def test_any_dimension_below_8_5_blocks(self):
        self.review["editorial_scores"]["narration_action_match"]["score"] = 8.4
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "8.5"):
            self.eval()

    def test_editor_review_must_bind_to_actual_export(self):
        self.video.write_bytes(b"different mp4 export" * 2000)
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "SHA-256 differs"):
            self.eval()

    def test_unlicensed_asset_blocks_even_with_10_10_review(self):
        self.review["shot_plans"][0]["assets"][0]["commercial_reuse_verified"] = False
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "rights"):
            self.eval()

    def test_missing_physically_visible_event_blocks(self):
        self.review["shot_plans"][0]["visible_action"] = "generic establishing pan"
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "EXACT visible physical"):
            self.eval()

    def test_zero_unresolved_hard_failures_required(self):
        self.review["unresolved_hard_failures"] = ["Cathedral not actually depicted"]
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "outstanding"):
            self.eval()

    def test_no_delivery_without_per_shot_proof(self):
        self.review.update({
            "phase": "delivery",
            "viewed_every_second_of_export": True,
            "listened_to_entire_final_mix": True,
            "voice_foley_synchronized": True,
            "no_unintended_long_silence": True,
            "delivery_approved": True,
        })
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "evidence missing"):
            self.eval("delivery")

    def test_proof_has_to_exist_not_just_a_json_boolean(self):
        proofs = pathlib.Path(self.temp.name) / "proofs"
        proofs.mkdir()
        self.review.update({
            "phase": "delivery",
            "viewed_every_second_of_export": True,
            "listened_to_entire_final_mix": True,
            "voice_foley_synchronized": True,
            "no_unintended_long_silence": True,
            "delivery_approved": True,
            "shot_reviews": [{
                "shot_id": "shot-01",
                "visible_action_matches_spoken_words": True,
                "required_objects_and_motion_visible": True,
                "period_and_rights_verified": True,
                "observations": (
                    "I reviewed the actual complete shot and saw the ball strike "
                    "the wall while the narrator precisely described its impact."
                ),
                "proof_frames": {
                    "first_frame": "first.jpg",
                    "midpoint": "mid.jpg",
                    "end_frame": "end.jpg",
                },
            }],
        })
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "missing real"):
            self.eval("delivery", proofs)
        for name in ["first.jpg", "mid.jpg", "end.jpg"]:
            (proofs / name).write_bytes(b"jpeg proof frame bytes" * 160)
        self.assertEqual(
            self.eval("delivery", proofs)["status"], "PASS_DELIVERY"
        )

    def test_missing_reference_registry_blocks(self):
        self.registry["reference_files"] = self.registry["reference_files"][:1]
        with self.assertRaisesRegex(gate.ReferenceGateFailure, "BOTH"):
            self.eval()


if __name__ == "__main__":
    unittest.main()
