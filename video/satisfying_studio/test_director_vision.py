"""Actual vision stays conservative; no arbitrary AI Python/edit commands."""
import unittest
from production.director_vision import classify, observation_to_command
from production.director_commands import validate_directive

SHA="f"*64
PRESENT={"gel_roughness": .115,"gel_transmission": .48,
         "gel_subsurface": .25,"key_light_energy":160.0,
         "camera_lens_mm":61.0}


class VisionControlTests(unittest.TestCase):
    def test_uncertain_real_model_output_has_no_command(self):
        self.assertEqual(classify("Uncertain."), "UNKNOWN")
        self.assertIsNone(observation_to_command("UNKNOWN",PRESENT,SHA))

    def test_glassy_authorizes_only_small_shader_change(self):
        d=observation_to_command("GLASSY",PRESENT,SHA)
        self.assertEqual(set(d["changes"]),{
            "gel_roughness","gel_transmission","gel_subsurface"})
        self.assertEqual(validate_directive(d,PRESENT),d["changes"])

    def test_dark_image_authorizes_only_lighting(self):
        d=observation_to_command("DARK",PRESENT,SHA)
        self.assertEqual(set(d["changes"]),{"key_light_energy"})

    def test_waxy_authorizes_small_transmission_and_scatter(self):
        d=observation_to_command("WAXY",PRESENT,SHA)
        self.assertEqual(set(d["changes"]),{"gel_subsurface","gel_transmission"})

    def test_no_self_approval_for_good_image(self):
        self.assertIsNone(observation_to_command("OK",PRESENT,SHA))

    def test_completely_invalid_reply_fails_conservatively(self):
        self.assertEqual(classify("a beautiful masterpiece"),"UNKNOWN")


if __name__=="__main__":
    unittest.main()
