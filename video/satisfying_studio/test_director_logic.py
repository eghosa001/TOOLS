"""Fast failure-first tests: the ASMR Director never invents quality approval."""
import math
import unittest
from production.director_logic import (
    framing_action, validate_framing, float_diagnostic,
    material_parameter_warnings, DirectorBlocked,
)


def extents(x0=.2, x1=.82, y0=.1, y1=.9):
    return [{"frame": n, "min_x": x0, "max_x": x1,
             "min_y": y0, "max_y": y1} for n in (1, 60, 120)]


class DirectorLogicTests(unittest.TestCase):
    def test_keeps_correct_camera_without_change(self):
        self.assertEqual(framing_action(extents(), 61)["action"], "keep")

    def test_minor_crop_is_corrected_without_physics_rebake(self):
        before = extents(x0=.03, x1=.98, y0=.13, y1=.9)
        result = framing_action(before, 61, margin=.045)
        self.assertEqual(result["action"], "zoom_out")
        self.assertLess(result["lens"], 61)
        after = []
        for frame in before:
            row = {"frame": frame["frame"]}
            for k in ("min_x", "max_x", "min_y", "max_y"):
                row[k] = .5 + (frame[k]-.5)*result["zoom_factor"]
            after.append(row)
        self.assertTrue(validate_framing(after, margin=.045))

    def test_large_crop_requires_restage_not_tiny_subject(self):
        with self.assertRaisesRegex(DirectorBlocked, "Unsafe to auto-zoom"):
            framing_action(extents(x0=-.3, x1=1.3), 61)

    def test_insufficient_frame_evidence_blocks_camera_change(self):
        with self.assertRaisesRegex(DirectorBlocked, "multiple actual"):
            framing_action(extents()[:1], 61)

    def test_invalid_nonfinite_camera_metrics_rejected(self):
        with self.assertRaisesRegex(DirectorBlocked, "Invalid physical"):
            framing_action(extents(x1=math.nan), 61)

    def test_offscreen_frame_fails_final_preflight(self):
        with self.assertRaisesRegex(DirectorBlocked, "outside composition"):
            validate_framing(extents(x1=1.05))

    def test_floating_risk_detected_from_real_bake_not_visual_guess(self):
        values = [{"frame": 1, "min_xyz": [0, 0, .015]},
                  {"frame": 120, "min_xyz": [0, 0, .1]}]
        self.assertTrue(float_diagnostic(values)["floating_risk"])

    def test_plausible_settle_passes_but_does_not_self_approve(self):
        values = [{"frame": 1, "min_xyz": [0, 0, .015]},
                  {"frame": 120, "min_xyz": [0, 0, .02]}]
        self.assertFalse(float_diagnostic(values)["floating_risk"])

    def test_glassy_wet_gel_node_risk_warned(self):
        self.assertTrue(material_parameter_warnings(.97, .01, .05))

    def test_no_fabricated_photorealism_number(self):
        # The Director reports physical properties only; never a '9/10' score.
        self.assertEqual(material_parameter_warnings(.5, .25, .12), [])


if __name__ == "__main__":
    unittest.main()
