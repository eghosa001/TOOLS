"""Regression tests for the exact 1986 Challenger upload error."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_youtube_shorts import assess


class ShortsGeometryTests(unittest.TestCase):
    def test_correct_1080x1920_master_passes(self):
        self.assertEqual(assess(1080, 1920, "1:1", 29.6, True)["status"], "PASS")

    def test_challenger_false_portrait_4x3_fails(self):
        result = assess(1080, 1920, "64:27", 29.6, True)
        self.assertEqual(result["status"], "FAIL")
        self.assertAlmostEqual(result["display_aspect_ratio"], 4 / 3)

    def test_landscape_fails(self):
        self.assertEqual(assess(1920, 1080, "1:1", 30, True)["status"], "FAIL")

    def test_over_three_minutes_fails(self):
        self.assertEqual(assess(1080, 1920, "1:1", 180.1, True)["status"], "FAIL")

    def test_missing_narration_fails(self):
        self.assertEqual(assess(1080, 1920, "1:1", 30, False)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
