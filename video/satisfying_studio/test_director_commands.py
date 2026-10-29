"""Unit safety checks for AI-production-director edits to REAL Blender scenes."""
import unittest
from production.director_commands import validate_directive, DirectorCommandError

SHA = "a"*64
BASE = {"camera_lens_mm": 61.0, "gel_roughness": .12,
        "gel_transmission": .48, "gel_subsurface": .25,
        "key_light_energy": 160.0}


def cmd(changes, reason="Measured reflections at frame 70 are too sharp and glassy"):
    return {"source_blend_sha256": SHA, "reason": reason, "changes": changes}


class DirectBlenderControlTests(unittest.TestCase):
    def test_valid_real_scene_edit(self):
        self.assertEqual(validate_directive(cmd({
            "camera_lens_mm": 59.0, "gel_roughness": .14}), BASE),
            {"camera_lens_mm": 59.0, "gel_roughness": .14})

    def test_arbitrary_python_and_physics_fakes_rejected(self):
        for name in ("python", "exec", "delete_scene", "physics_bake", "foley_swap"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(DirectorCommandError, "Unapproved"):
                    validate_directive(cmd({name: 1}), BASE)

    def test_massive_lens_change_is_blocked(self):
        with self.assertRaisesRegex(DirectorCommandError, "Unsafe large"):
            validate_directive(cmd({"camera_lens_mm": 45.0}), BASE)

    def test_shader_value_beyond_safe_range_is_blocked(self):
        with self.assertRaisesRegex(DirectorCommandError, "Out-of-bounds"):
            validate_directive(cmd({"gel_roughness": .95}), BASE)

    def test_reason_must_be_a_real_explanation(self):
        with self.assertRaisesRegex(DirectorCommandError, "specific"):
            validate_directive(cmd({"gel_roughness": .13}, reason="AI says yes"), BASE)

    def test_extra_fields_are_rejected(self):
        item=cmd({"gel_roughness": .14})
        item["approve_9_of_10"] = True
        with self.assertRaisesRegex(DirectorCommandError, "Unexpected"):
            validate_directive(item, BASE)


if __name__ == "__main__":
    unittest.main()
