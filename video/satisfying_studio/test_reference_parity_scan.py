"""Lightweight tests; synthetic fixtures are strictly engineering checks, not ASMR approval."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from production import reference_parity_scan as q

class ParityScanTests(unittest.TestCase):
    def test_comparison_does_not_invent_artistic_pass(self):
        x = {"audio_stream": False, "width": 720, "height": 1280,
             "luminance_mean": 30, "strong_local_gradient_fraction": .02}
        y = {"width": 1080, "height": 1920, "luminance_mean": 110,
             "strong_local_gradient_fraction": .1}
        warnings = q.compare(x, y)
        self.assertTrue(any("MISSING AUDIO" in w for w in warnings))
        self.assertTrue(any("NOT an artistic parity" in w for w in warnings))

    def test_silent_file_never_gets_artistic_approval(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg not installed")
        with tempfile.TemporaryDirectory() as dirname:
            p = Path(dirname) / "silent.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "color=c=purple:s=320x576:r=24",
                            "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            str(p)], check=True, timeout=40)
            report = q.produce(p, [p])
            self.assertFalse(report["candidate"]["audio_stream"])
            self.assertEqual(report["candidate"]["near_silent_fraction"], 1.)
            self.assertFalse(report["candidate_release_approved"])
            self.assertEqual(report["comparisons"][0]["reference"]["sha256"], q.sha256(p))
            self.assertGreater(report["candidate"]["frames_sampled"], 0)

    def test_no_phantom_sound_claim_when_technical_audio_exists(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg not installed")
        with tempfile.TemporaryDirectory() as dirname:
            p = Path(dirname) / "synthetic_fixture_only.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "color=c=blue:s=320x576:r=24",
                            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000",
                            "-t", "2", "-c:v", "libx264", "-c:a", "aac",
                            "-pix_fmt", "yuv420p", str(p)], check=True, timeout=40)
            report = q.produce(p, [])
            self.assertTrue(report["candidate"]["audio_stream"])
            self.assertIsNotNone(report["candidate"]["rms_dbfs_p50"])
            self.assertFalse(report["candidate_release_approved"])
            self.assertIn("does not verify source material", report["limitations"])

if __name__ == "__main__":
    unittest.main()
