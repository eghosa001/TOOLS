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
                     "codec_name": "h264", "avg_frame_rate": "24/1"},
                    {"codec_type": "audio", "codec_name": "aac",
                     "sample_rate": "48000", "channels": 2},
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

    @patch.object(av.shutil, "which", return_value="/usr/bin/placeholder")
    @patch.object(av.subprocess, "run")
    @patch.object(av, "check_audio")
    @patch.object(av, "analyze_master")
    def test_all_47_format_scan_includes_objective_audio_and_picture_signal(self, metric, audio,
                                                                              subprocess_run, _):
        subprocess_run.side_effect = self.mock_commands
        audio.return_value = {"passed": True, "gaps": [], "duration_s": 5.0}
        metric.return_value = {
            "format_id": "wax-cracking", "signal_preflight_passed": True,
            "blocking_signal_issues": [], "editorial_investigation_flags": [],
            "creative_approval": False, "audio_action_sync_verified": False
        }
        with patch.object(av, "frame_metrics", return_value={
            "frames_sampled": 5, "luminance_mean": 91,
            "strong_local_gradient_fraction": .12
        }):
            scan = av.scan_to_file(self.master, self.report, format_id="wax-cracking")
        self.assertEqual(scan["format_id"], "wax-cracking")
        self.assertEqual(scan["unresolved_technical_blockers"], [])
        self.assertFalse(scan["master_signal_qa"]["creative_approval"])
        self.assertEqual(metric.call_count, 1)

    @patch.object(av.shutil, "which", return_value="/usr/bin/placeholder")
    @patch.object(av.subprocess, "run")
    @patch.object(av, "check_audio")
    @patch.object(av, "analyze_master")
    def test_unsafe_peak_blocks_cgi_even_if_silence_gate_passes(self, metric, audio,
                                                                 subprocess_run, _):
        subprocess_run.side_effect = self.mock_commands
        audio.return_value = {"passed": True, "gaps": [], "duration_s": 5.0}
        metric.return_value = {
            "format_id": "soap-cutting", "signal_preflight_passed": False,
            "blocking_signal_issues": ["True-peak exceeds -1 dBTP engineering safety ceiling"],
            "editorial_investigation_flags": [], "creative_approval": False
        }
        with patch.object(av, "frame_metrics", return_value={"frames_sampled": 5}):
            scan = av.scan_to_file(self.master, self.report, format_id="soap-cutting")
        self.assertTrue(any("True-peak" in x for x in scan["unresolved_technical_blockers"]))

    @patch.object(av.shutil, "which", return_value="/usr/bin/placeholder")
    @patch.object(av.subprocess, "run")
    @patch.object(av, "check_audio")
    @patch.object(av, "analyze_master")
    def test_audio_picture_length_drift_blocks_master(self, metric, audio,
                                                        subprocess_run, _):
        subprocess_run.side_effect = self.mock_commands
        audio.return_value = {"passed": True, "gaps": [], "duration_s": 4.7}
        metric.return_value = {"format_id": "jelly", "signal_preflight_passed": True,
                               "blocking_signal_issues": [], "editorial_investigation_flags": []}
        with patch.object(av, "frame_metrics", return_value={"frames_sampled": 5}):
            scan = av.scan_to_file(self.master, self.report, format_id="jelly")
        self.assertIn("Picture/audio duration mismatch exceeds 100 ms",
                      scan["unresolved_technical_blockers"])

    def test_missing_mp4_fails(self):
        with self.assertRaises(ValueError):
            av.analyze(self.master.parent / "missing.mp4")


if __name__ == "__main__":
    unittest.main()
