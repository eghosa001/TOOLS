"""No extreme Flow clip stretching, no padding, no rapid repeated takes."""
import unittest

from production.longform_motion_guard import NoStretchError, validate


def shot(i, duration=200, speed=1, sha=None):
    return {
        "source_path": f"shot_{i}.mp4",
        "source_sha256": sha or f"{i:064x}",
        "source_duration_seconds": duration,
        "in_seconds": 0,
        "out_seconds": duration,
        "playback_speed": speed,
        "license": "original",
        "approved": True,
    }


class MotionLengthGateTests(unittest.TestCase):
    def test_ten_minute_distinct_footage(self):
        report = validate({"target_seconds": 600, "clips": [
            shot(1), shot(2), shot(3)]}, verify_files=False)
        self.assertEqual(report["picture_seconds"], 600)
        self.assertFalse(report["publication_approved"])

    def test_18_point_75_slowdown_rejected(self):
        with self.assertRaisesRegex(NoStretchError, "NO STRETCHING"):
            validate({"target_seconds": 150, "clips": [
                shot(1, duration=8, speed=1 / 18.75)]}, verify_files=False)

    def test_four_eight_second_clips_not_ten_minutes(self):
        with self.assertRaisesRegex(NoStretchError, "distinct footage"):
            validate({"target_seconds": 600, "clips": [
                shot(i, duration=8) for i in range(1, 5)]}, verify_files=False)

    def test_early_reuse_rejected_even_with_renamed_source(self):
        with self.assertRaisesRegex(NoStretchError, "repeated footage too soon"):
            validate({"target_seconds": 400, "clips": [
                shot(1), shot(2, sha=f"{1:064x}")]}, verify_files=False)

    def test_later_reuse_is_allowed_but_not_marked_publishable(self):
        clips = [shot(1, 100), shot(2, 190), shot(3, 190), shot(1, 100)]
        report = validate({"target_seconds": 580, "clips": clips}, verify_files=False)
        self.assertEqual(report["unique_sources"], 3)
        self.assertFalse(report["publication_approved"])

    def test_missing_rights_fail(self):
        clip = shot(1)
        clip["license"] = ""
        with self.assertRaisesRegex(NoStretchError, "missing license"):
            validate({"target_seconds": 200, "clips": [clip]}, verify_files=False)

    def test_freeze_and_loop_fail(self):
        for flag in ["freeze", "loop", "reverse", "interpolate"]:
            clip = shot(1)
            clip[flag] = True
            with self.subTest(flag=flag), self.assertRaises(NoStretchError):
                validate({"target_seconds": 200, "clips": [clip]}, verify_files=False)


if __name__ == "__main__":
    unittest.main()
