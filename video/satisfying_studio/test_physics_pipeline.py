"""Fast physics pipeline tests (no GPU, network or expensive simulator builds)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from production import sph_fluid_pipeline as sph
import physics_verify


class PhysicsPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_roller_physics_object_names_match_real_blender_scene(self):
        production = Path(__file__).parent / "production"
        scene = (production / "prismatic_gel_scene.py").read_text(encoding="utf-8")
        bake = (production / "blender_softbody_prepare.py").read_text(encoding="utf-8")
        for object_name in (
            "One continuous volumetric deforming jewel",
            "Clear round ASMR roller — visible jelly contact",
            "ASMR studio stone collider",
        ):
            self.assertIn(object_name, scene)
            self.assertIn(object_name, bake)

    def test_no_sph_scene_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "authored SPlisHSPlasH"):
            sph.run(self.root / "missing.json", self.root / "out", 5, 120, 0.01,
                    "SPHSimulator", "splashsurf")

    def test_missing_sph_solver_is_not_an_acceptable_fallback(self):
        scene = self.root / "scene.json"
        scene.write_text('{"fluidModels": []}')
        with patch.object(sph.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "not installed"):
                sph.run(scene, self.root / "out", 5, 120, 0.01,
                        "SPHSimulator", "splashsurf")

    def test_particle_frames_must_be_contiguous(self):
        frames = [self.root / ("Fluid_%04d.bgeo" % n) for n in (1, 2, 4)]
        with self.assertRaisesRegex(RuntimeError, "Missing frames"):
            sph.particle_sequence(frames)

    def test_reconstructed_real_cache_workflow_runs_when_tools_produce_frames(self):
        scene = self.root / "fluid.json"
        scene.write_text('{"purpose": "authored fluid simulation"}')

        def fake_run(cmd, **kw):
            if "SPHSimulator" in cmd[0]:
                particle_dir = self.root / "out" / "particles"
                for i in range(1, 121):
                    (particle_dir / ("Fluid_%04d.bgeo" % i)).write_bytes(b"P" * 256)
            else:
                mesh_dir = self.root / "out" / "meshes"
                for i in range(1, 121):
                    (mesh_dir / ("fluid_%04d.obj" % i)).write_text(
                        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n" + "#test\n" * 30)
        with patch.object(sph.shutil, "which", side_effect=lambda x: x):
            with patch.object(sph.subprocess, "run", side_effect=fake_run) as mocked:
                proof = sph.run(scene, self.root / "out", 5, 120, 0.01,
                                "SPHSimulator", "splashsurf")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(proof["simulated_frames"], 120)
        self.assertEqual(proof["surface_mesh_files"], 120)
        self.assertEqual(physics_verify.verify(
            {"duration_seconds": 5, "fps": 24,
             "physics_cache_manifest": "out/physics_bake_manifest.json"},
            self.root)["solver"], "SPlisHSPlasH")

    def test_faked_blender_bake_cannot_be_verified(self):
        root = self.root
        (root / "physics_bake_manifest.json").write_text(json.dumps({
            "solver": "blender_softbody", "source_blend": "fake.blend",
            "baked_point_cache": False, "cached_frames": 120}))
        with self.assertRaisesRegex(physics_verify.PhysicsEvidenceError,
                                    "baked Blender"):
            physics_verify.verify({"duration_seconds": 5, "fps": 24,
                                    "physics_cache_manifest": "physics_bake_manifest.json"}, root)


if __name__ == "__main__":
    unittest.main()
