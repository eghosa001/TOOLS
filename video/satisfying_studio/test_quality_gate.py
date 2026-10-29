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

    def add_baked_physics(self):
        # Genuine filesystem evidence (not Blender execution): unit-test only.
        blend = self.root / "render" / "tested_physics.blend"
        blend.write_bytes(b"unit-test-blender-cache-file")
        proof = {
            "solver": "blender_softbody",
            "source_blend": blend.name,
            "source_blend_sha256": q.sha256(blend),
            "baked_point_cache": True,
            "cached_frames": 720,
            "director_floating_risk": False,
            "director_camera": {"action": "keep", "lens": 61},
        }
        camera = [{"frame": frame, "min_x": .20, "max_x": .80,
                   "min_y": .15, "max_y": .85}
                  for frame in (1, 24, 48, 70, 90, 105, 120)]
        (self.root / "render" / "actual_physics_camera_framing.json").write_text(
            json.dumps(camera), encoding="utf-8")
        manifest = self.root / "render" / "physics_bake_manifest.json"
        manifest.write_text(json.dumps(proof), encoding="utf-8")
        self.plan["physics_cache_manifest"] = "render/physics_bake_manifest.json"

    def approve_preview(self):
        self.plan["preview_review"] = {
            "approved": True, "reviewer": "Video editor",
            "reviewed_preview_sha256": q.sha256(self.preview),
            "observations": "Watched moving marbles and heard each impact at its matching moment.",
            "visual_score": 9, "material_realism_score": 9, "texture_detail_score": 9,
            "lighting_color_score": 9, "physical_coherence_score": 9,
            "motion_score": 9, "foley_quality_score": 9, "audio_sync_score": 9,
            "satisfaction_score": 9, "blocking_issues": [],
            "benchmark_video_ids": ["kKOJZbthcyo", "7gV-0be8WqE"],
            "benchmark_visual_comparison": "Examined the tactile material appearance and coherent close-up movement against reference scenes.",
            "benchmark_audio_comparison": "Compared the squeeze sound, release sound, tiny crack and contact timing with reference scenes.",
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

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_missing_reference_comparison_blocks(self, _):
        self.approve_preview()
        del self.plan["preview_review"]["benchmark_audio_comparison"]
        with self.assertRaisesRegex(q.GateError, "benchmark_audio_comparison"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_missing_material_realism_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["material_realism_score"] = 8
        with self.assertRaisesRegex(q.GateError, "material_realism_score"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_low_foley_quality_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["foley_quality_score"] = 8
        with self.assertRaisesRegex(q.GateError, "foley_quality_score"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_unapproved_reference_id_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["benchmark_video_ids"] = ["fictional-id"]
        with self.assertRaisesRegex(q.GateError, "reference video ID"):
            q.check_preview(self.plan, self.root)

    def test_exact_five_second_plan_allowed(self):
        self.plan["duration_seconds"] = 5
        self.plan["manually_directed_shots"] = [
            {"start_seconds": 0, "end_seconds": 5,
             "visual_intent": "Iridescent close-up reveal on reflective textured stone",
             "movement": "Controlled 3D squeeze and translucent deformation",
             "sound_cue": "Manually placed wet squeeze, crack and glass click",
             "source_and_rights": "Original authored Blender meshes and licensed Foley"}]
        self.save()
        validated, _ = q.load_plan(self.manifest)
        self.assertEqual(validated["duration_seconds"], 5)

    def test_discontinuous_manual_timeline_blocks(self):
        self.plan["manually_directed_shots"][1]["start_seconds"] = 15.8
        self.save()
        with self.assertRaisesRegex(q.GateError, "gap, overlap"):
            q.load_plan(self.manifest)

    @patch.object(q, "media_info", return_value={"duration": 30, "width": 720, "height": 1280})
    def test_release_requires_explicit_final_review(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        def fake_media(p):
            return {"duration": 5, "width": 540, "height": 960} if p == self.preview else {
                "duration": 30, "width": 720, "height": 1280}
        mocked.side_effect = fake_media
        with self.assertRaisesRegex(q.GateError, "not approved"):
            q.check_final(self.plan, self.root)
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Viewed the entire 30-second film and inspected every audio beat.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Reviewed actual final photoreal materials and macro lens presentation against user videos.",
            "benchmark_audio_comparison": "Verified full final Foley sync, textures and tactile impact sounds against user references.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.assertEqual(q.check_final(self.plan, self.root), q.sha256(self.final))

    @patch.object(q, "media_info")
    def test_540p_final_still_rejected(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960}
            if p == self.preview else
            {"duration": 30, "width": 540, "height": 960}
        )
        with self.assertRaisesRegex(q.GateError, "720x1280"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_missing_physics_prevents_release_even_with_approved_preview(self, mocked):
        self.approve_preview()
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960}
            if p == self.preview else
            {"duration": 30, "width": 720, "height": 1280}
        )
        with self.assertRaisesRegex(q.GateError, "physics"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_false_bake_proof_prevents_release(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        manifest = self.root / self.plan["physics_cache_manifest"]
        data = json.loads(manifest.read_text())
        data["baked_point_cache"] = False
        manifest.write_text(json.dumps(data))
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960}
            if p == self.preview else
            {"duration": 30, "width": 720, "height": 1280}
        )
        with self.assertRaisesRegex(q.GateError, "physics"):
            q.check_final(self.plan, self.root)

    def test_timeout_stops_renderer(self):
        log = self.root / "timeout.log"
        with self.assertRaisesRegex(q.GateError, "stopped after"):
            q.run_limited([sys.executable, "-c", "import time; time.sleep(10)"], 0.1, log)
        self.assertTrue(log.exists())



    def prepare_long_episode(self, fmt, material="translucent jelly"):
        self.plan["duration_seconds"] = 60
        self.plan["editorial_format"] = fmt
        self.plan["editorial_thesis"] = "Show a satisfying tactile pattern with matching sounds"
        self.plan["material_family"] = material
        self.plan["manually_directed_shots"][1]["end_seconds"] = 60
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["material_family"] = material
            shot["editorial_link"] = "One visual sensory idea with deliberate sound"
            if i:
                shot["transition_intent"] = "Direct continuation or meaningful contrast"

    def test_long_episode_blocks_unknown_editorial_format(self):
        self.prepare_long_episode("totally_random")
        self.save()
        with self.assertRaisesRegex(q.GateError, "editorial_format"):
            q.load_plan(self.manifest)

    def test_long_episode_accepts_same_material_ritual(self):
        self.prepare_long_episode("single-material")
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "single-material")

    def test_focused_material_blocks_unplanned_dye_cutaway(self):
        self.prepare_long_episode("single-material")
        self.plan["manually_directed_shots"][1]["material_family"] = "paint dye"
        self.save()
        with self.assertRaisesRegex(q.GateError, "unexpectedly changes"):
            q.load_plan(self.manifest)

    def test_comparison_accepts_two_real_materials(self):
        self.prepare_long_episode("comparison")
        self.plan["comparison_axis"] = "identical crush pressure"
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["material_family"] = "jelly" if i == 0 else "crunchy shell"
            shot["comparison_axis"] = "identical crush pressure"
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "comparison")

    def test_comparison_rejects_unrelated_actions(self):
        self.prepare_long_episode("comparison")
        self.plan["comparison_axis"] = "identical crush pressure"
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["comparison_axis"] = "identical crush pressure" if i == 0 else "random cutting"
        self.save()
        with self.assertRaisesRegex(q.GateError, "same clear test"):
            q.load_plan(self.manifest)

    def test_thematic_compilation_accepts_multiple_triggers(self):
        self.prepare_long_episode("themed-compilation")
        self.plan["manually_directed_shots"][1]["material_family"] = "crunchy sand"
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "themed-compilation")

    def test_compilation_rejects_unmotivated_transition(self):
        self.prepare_long_episode("themed-compilation")
        self.plan["manually_directed_shots"][1].pop("transition_intent")
        self.save()
        with self.assertRaisesRegex(q.GateError, "intentional transition missing"):
            q.load_plan(self.manifest)

    def test_process_transformation_stages(self):
        self.prepare_long_episode("process-transformation")
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["process_stage"] = "cleaning" if i == 0 else "finishing"
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "process-transformation")

    def test_surreal_world_requires_world_identity(self):
        self.prepare_long_episode("surreal-world")
        self.save()
        with self.assertRaisesRegex(q.GateError, "fantasy-world identity"):
            q.load_plan(self.manifest)



if __name__ == "__main__":
    unittest.main()
