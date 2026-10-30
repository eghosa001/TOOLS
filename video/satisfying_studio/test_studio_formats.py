"""ASMR studio 47-format source gate tests; deterministic, no media downloads."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import studio_formats as fmt
import quality_gate as gate
import physics_verify as physics


class MultiFormatStudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan_path = fmt.init_project("domino-marble", self.root / "domino")
        self.plan = json.loads(self.plan_path.read_text())
        self.dir = self.plan_path.parent

    def add_assets(self, role="scene"):
        a = self.dir / ("actual.blend" if role == "scene" else "original.mov")
        a.write_bytes(b"test fixture only - not physically rendered")
        b = self.dir / "actual_foley.wav"
        b.write_bytes(b"test fixture only - not actually auditioned")
        f = fmt.get_format(self.plan["format_id"])
        self.plan["asset_inventory"] = [
            {"role": role, "file": a.name, "sha256": fmt.sha256(a),
             "source_url": "https://example.org/original-owner-source",
             "license": "original", "material": f["material"],
             "gesture": f["action"], "reviewed": True},
            {"role": "foley", "file": b.name, "sha256": fmt.sha256(b),
             "source_url": "https://example.org/original-foley",
             "license": "original", "material": f["material"],
             "gesture": f["action"], "reviewed": True,
             "auditioned_against_picture": True},
        ]
        self.plan_path.write_text(json.dumps(self.plan))

    def test_catalogue_has_exactly_47_unique_categories(self):
        all_formats = fmt.catalogue()["formats"]
        self.assertEqual(len(all_formats), 47)
        self.assertEqual(len({x["id"] for x in all_formats}), 47)
        self.assertEqual({x["group"] for x in all_formats},
                         set(fmt.catalogue()["modules"]))

    def test_init_previews_are_explicitly_unapproved(self):
        self.assertFalse(self.plan["preview_review"]["approved"])
        self.assertFalse(self.plan["final_review"]["approved"])
        self.assertEqual(self.plan["duration_seconds"], 5)
        self.assertEqual(self.plan["selected_asset_route"], "scene")

    def test_full_catalogue_has_valid_starter_manifests(self):
        for f in fmt.catalogue()["formats"]:
            with self.subTest(format=f["id"]):
                with tempfile.TemporaryDirectory() as root:
                    p = fmt.init_project(f["id"], Path(root) / "out")
                    loaded, _ = gate.load_plan(p)
                    self.assertEqual(loaded["format_id"], f["id"])
                    self.assertIn("Missing real recorded", ";".join(
                        fmt.inspect_assets(loaded, p.parent)))

    def test_missing_recordings_prevent_motion_render(self):
        with self.assertRaisesRegex(gate.GateError, "format source preflight failed"):
            gate.check_format_inputs(self.plan, self.dir)

    def test_verified_assets_pass_preflight_but_not_artistic_gate(self):
        self.add_assets()
        self.assertEqual(fmt.inspect_assets(self.plan, self.dir), [])
        gate.check_format_inputs(self.plan, self.dir)
        with self.assertRaises(gate.GateError):
            gate.check_preview(self.plan, self.dir)

    def test_foley_different_gesture_rejected_even_if_sha_matches(self):
        self.add_assets()
        self.plan["asset_inventory"][-1]["gesture"] = "unrelated scrape"
        problems = fmt.inspect_assets(self.plan, self.dir)
        self.assertTrue(any("material/gesture" in p for p in problems))

    def test_stale_hash_rejected(self):
        self.add_assets()
        self.plan["asset_inventory"][0]["sha256"] = "wrong"
        self.assertTrue(any("SHA256 mismatch" in p for p in fmt.inspect_assets(self.plan, self.dir)))

    def test_hybrid_route_has_to_be_chosen(self):
        with tempfile.TemporaryDirectory() as root:
            p = fmt.init_project("nail-polish-cracking", Path(root) / "out")
            d = json.loads(p.read_text())
            self.assertIn("Choose an explicit", ";".join(fmt.inspect_assets(d, p.parent)))

    def test_real_capture_route_cannot_be_switched_to_blender(self):
        with tempfile.TemporaryDirectory() as root:
            p = fmt.init_project("whispering", Path(root) / "out")
            d = json.loads(p.read_text())
            d["selected_asset_route"] = "scene"
            self.assertTrue(any("needs original real footage" in x
                                for x in fmt.inspect_assets(d, p.parent)))

    def test_new_landscape_preview_and_final_minima(self):
        data = {"aspect_ratio": "16:9"}
        gate.check_output_geometry({"width": 960, "height": 540}, "16:9", preview=True)
        gate.check_output_geometry({"width": 1280, "height": 720}, "16:9", preview=False)
        with self.assertRaisesRegex(gate.GateError, "16:9"):
            gate.check_output_geometry({"width": 720, "height": 1280}, "16:9", preview=False)

    def test_long_requires_registered_format_and_genuine_manual_timeline(self):
        self.plan["delivery_intent"] = "long"
        self.plan["production_kind"] = "long-form"
        self.plan["duration_seconds"] = 600
        self.plan["manually_directed_shots"][0]["end_seconds"] = 600
        self.plan_path.write_text(json.dumps(self.plan))
        data, _ = gate.load_plan(self.plan_path)
        self.assertEqual(data["duration_seconds"], 600)
        data["production_kind"] = "pilot"
        self.plan_path.write_text(json.dumps(data))
        with self.assertRaisesRegex(gate.GateError, "Pilot"): 
            gate.load_plan(self.plan_path)

    def test_shot_physics_evidence_is_mandatory_and_solver_specific(self):
        self.add_assets()
        with self.assertRaises(physics.PhysicsEvidenceError):
            physics.verify_shots(self.plan, self.dir)

    def test_parent_and_absolute_source_paths_rejected(self):
        for source in ("../outside.mp4", "/tmp/private.mp4", ""):
            with self.subTest(source=source):
                with self.assertRaises(fmt.StudioFormatError):
                    fmt.safe_file(self.dir, source)

    def test_no_reuse_of_existing_directory_contents(self):
        with self.assertRaises(fmt.StudioFormatError):
            fmt.init_project("soap-cutting", self.dir)


if __name__ == "__main__":
    unittest.main()
