"""No-download post-render AV scanner tests; no FFmpeg installation required."""
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess

import post_render_av_review as av


class PostRenderScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.master = Path(self.tmp.name) / "master.mp4"
        self.master.write_bytes(b"fake master for unit testing")
        self.report = Path(self.tmp.name) / "av.json"

    def mock_commands(self, command, **_):
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({
                "format": {"duration": "5.0"},
                "streams": [
                    {"codec_type": "video", "width": 720, "height": 1280,
                     "avg_frame_rate": "24/1"},
                    {"codec_type": "audio", "sample_rate": "48000", "channels": 2},
                ],
            }), stderr="")
        return subprocess.CompletedProcess(
            command, 0, stdout="",
            stderr="[blackdetect] black_start:1.000 black_end:1.600 black_duration:0.600\n",
        )

    @patch.object(av.shutil, "which", return_value="/usr/bin/placeholder")
    @patch.object(av.subprocess, "run")
    @patch.object(av, "check_audio")
    def test_scans_exact_master_without_approving_quality(self, audio, subprocess_run, _):
        subprocess_run.side_effect = self.mock_commands
        audio.return_value = {"passed": True, "gaps": []}
        with patch.object(av, "frame_metrics", return_value={"frames_sampled": 5, "luminance_mean": 42}):
            result = av.scan_to_file(self.master, self.report)
        self.assertEqual(result["master_sha256"], hashlib.sha256(self.master.read_bytes()).hexdigest())
        self.assertEqual(len(result["possible_black_intervals"]), 1)
        self.assertEqual(result["review_status"][:10], "UNAPPROVED")
        self.assertEqual(json.loads(self.report.read_text())["scan_complete"], True)
        self.assertEqual(result["unresolved_technical_blockers"], [])
        self.assertEqual(result["cgi_frame_diagnostics"]["frames_sampled"], 5)

    @patch.object(av.shutil, "which", return_value="/usr/bin/placeholder")
    @patch.object(av.subprocess, "run")
    @patch.object(av, "check_audio")
    def test_silence_blocker_is_preserved_not_self_approved(self, audio, subprocess_run, _):
        subprocess_run.side_effect = self.mock_commands
        audio.return_value = {
            "passed": False, "gaps": [{"start_s": 1, "end_s": 1.8}]
        }
        with patch.object(av, "frame_metrics", return_value={"frames_sampled": 5, "luminance_mean": 42}):
            result = av.scan_to_file(self.master, self.report)
        self.assertEqual(result["unresolved_technical_blockers"], ["unwanted soundtrack silence"])
        self.assertFalse(result["audio_continuity"]["passed"])

    def test_missing_mp4_fails(self):
        with self.assertRaises(ValueError):
            av.analyze(self.master.parent / "missing.mp4")


if __name__ == "__main__":
    unittest.main()
