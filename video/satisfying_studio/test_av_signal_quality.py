"""All-47-format CGI signal QA tests; real FFmpeg generated fixtures, not creative examples."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from production import av_signal_quality as audit


class QualityProfiles(unittest.TestCase):
    def test_all_47_have_unique_group_appropriate_audio_and_video_review(self):
        profiles = audit.formats_covered()
        self.assertEqual(len(profiles), 47)
        self.assertEqual(len(set(profiles)), 47)
        self.assertEqual(set(p["group"] for p in profiles.values()),
                         set(audit.DIRECTOR_REQUIREMENTS))
        for key, value in profiles.items():
            with self.subTest(key=key):
                self.assertTrue(value["cgi_only"])
                self.assertFalse(value["user_media_required"])
                self.assertTrue(value["needs_genuine_recorded_sound"])
                self.assertTrue(value["needs_actual_headphone_and_picture_review"])
                self.assertGreater(len(value["visual_director_check"]), 15)
                self.assertGreater(len(value["audio_director_check"]), 15)

    def test_ffmpeg_summary_parsing_uses_final_summary_not_momentary_values(self):
        stderr = """
        [Parsed_ebur128] t: 0.1 I: -9.2 LUFS
        [Parsed_ebur128] Summary:
          Integrated loudness:
            I:         -22.6 LUFS
            Threshold: -32.6 LUFS
          Loudness range:
            LRA: 2.4 LU
          True peak:
            Peak:      -3.1 dBFS
        """
        result = audit.parse_ebur128_summary(stderr)
        self.assertEqual(result["integrated_loudness_lufs"], -22.6)
        self.assertEqual(result["true_peak_dbtp"], -3.1)
        self.assertFalse(result["is_an_auditory_review"])

    def test_bad_signal_blocks_independent_of_subjective_notes(self):
        image = {"frames_sampled": 5, "luminance_mean": 108,
                 "strong_local_gradient_fraction": .16}
        bad = audit.assess("wax-cracking", image,
                           {"integrated_loudness_lufs": -5,
                            "true_peak_dbtp": .3})
        self.assertFalse(bad["signal_preflight_passed"])
        self.assertGreaterEqual(len(bad["blocking_signal_issues"]), 2)
        self.assertFalse(bad["creative_approval"])

    def test_inaudible_master_never_passes(self):
        x = audit.assess("jelly", {"frames_sampled": 5},
                         {"integrated_loudness_lufs": -70,
                          "true_peak_dbtp": -50})
        self.assertFalse(x["signal_preflight_passed"])

    def test_silent_master_has_no_ebur128_signal_approval(self):
        x = audit.assess("brushing", {"frames_sampled": 5},
                         {"integrated_loudness_lufs": None,
                          "true_peak_dbtp": None})
        self.assertFalse(x["signal_preflight_passed"])

    def test_frame_warning_not_false_artistic_failure(self):
        x = audit.assess("rain-nature", {"frames_sampled": 5,
                          "luminance_mean": 11,
                          "strong_local_gradient_fraction": .005},
                         {"integrated_loudness_lufs": -22,
                          "true_peak_dbtp": -3})
        self.assertTrue(x["signal_preflight_passed"])
        self.assertTrue(x["editorial_investigation_flags"])
        self.assertFalse(x["visual_reference_parity_verified"])
        self.assertFalse(x["audio_action_sync_verified"])

    def test_unregistered_genre_rejected(self):
        with self.assertRaises(ValueError):
            audit.assess("filmed-stock-short", {}, {})

    def test_very_high_true_peak_warning_is_not_equivalent_to_pass(self):
        x = audit.assess("ice-shaving", {"frames_sampled": 5},
                         {"integrated_loudness_lufs": -19,
                          "true_peak_dbtp": -1.5})
        self.assertTrue(x["signal_preflight_passed"])
        self.assertTrue(any("mastering" in flag for flag in x["editorial_investigation_flags"]))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/ffprobe not installed")
    def test_actual_encoded_stereo_master_ebu_full_scan(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "fixture-not-asmr.mp4"
            subprocess.run(
                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "lavfi", "-i", "color=c=blue:s=360x640:r=24",
                 "-f", "lavfi", "-i", "sine=frequency=350:sample_rate=48000",
                 "-t", "3", "-map", "0:v", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-ac", "2", "-b:a", "192k", str(path)],
                check=True, timeout=45)
            output = audit.analyze_sound(path, timeout=45)
            self.assertIsNotNone(output["true_peak_dbtp"])
            self.assertIsNotNone(output["integrated_loudness_lufs"])
            self.assertLess(output["true_peak_dbtp"], 0.0)
            self.assertFalse(output["is_an_auditory_review"])
            assessed = audit.assess(
                "wax-cracking",
                {"frames_sampled": 3, "luminance_mean": 80,
                 "strong_local_gradient_fraction": .2},
                output)
            self.assertTrue(assessed["signal_preflight_passed"])
            self.assertFalse(assessed["creative_approval"])
            # Do not merely unit-test the EBU summary: exercise the complete
            # exact-master picture decode, silence, frame-detail and encoder
            # gates on a real encoded file. This remains synthetic QA only.
            from production import post_render_av_review
            report = post_render_av_review.analyze(path, format_id="jelly")
            self.assertEqual(report["format_id"], "jelly")
            self.assertEqual(report["unresolved_technical_blockers"], [])
            self.assertTrue(report["master_signal_qa"]["signal_preflight_passed"])
            self.assertTrue(report["cgi_frame_diagnostics"]["frames_sampled"] >= 3)
            self.assertFalse(report["master_signal_qa"]["creative_approval"])
            self.assertFalse(report["master_signal_qa"]["physical_timbre_verified"])





class RegisteredCGIPreviewReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/"render").mkdir()
        self.master = self.root/"render"/"preview.mp4"
        self.master.write_bytes(b"synthetic gate fixture not an approved real video")
        self.report = self.root/"render"/"preview_scan.json"
        self.data = {
            "format_id": "jelly",
            "preview_file": "render/preview.mp4",
            "preview_av_scan_file": "render/preview_scan.json",
            "delivery_aspect_ratio": "9:16",
            "preview_review": {"approved": False},
        }

    def test_registered_preview_cannot_skip_actual_audio_video_scan(self):
        import quality_gate as gate
        fake_info = {"duration": 5.0, "width": 720, "height": 1280}
        with patch.object(gate, "check_format_inputs"), patch.object(gate, "media_info",
                                                                     return_value=fake_info):
            with self.assertRaisesRegex(gate.GateError, "preview AV scan missing"):
                gate.check_preview(self.data, self.root)

    def test_registered_preview_rejects_stale_scan_even_if_editor_approved(self):
        import quality_gate as gate
        self.report.write_text(json.dumps({
            "scan_complete": True, "master_sha256": "wrong",
            "format_id": "jelly", "master_signal_qa": {
                "signal_preflight_passed": True, "blocking_signal_issues": []
            }, "unresolved_technical_blockers": []
        }))
        fake_info = {"duration": 5.0, "width": 720, "height": 1280}
        with patch.object(gate, "check_format_inputs"), patch.object(gate, "media_info",
                                                                     return_value=fake_info):
            with self.assertRaisesRegex(gate.GateError, "preview scan stale"):
                gate.check_preview(self.data, self.root)

    def test_registered_master_rejects_missing_signal_profile(self):
        import quality_gate as gate
        data = {
            "format_id": "jelly", "av_scan_file": "render/preview_scan.json",
            "duration_seconds": 5,
        }
        self.report.write_text(json.dumps({
            "schema_version": 1, "scan_complete": True, "master_sha256": "abc",
            "duration_seconds": 5, "unresolved_technical_blockers": [],
            "audio_continuity": {"passed": True, "gaps": []}
        }))
        with self.assertRaisesRegex(gate.GateError, "format QA was not run"):
            gate.check_post_render_av_review(data, self.root, "abc", {})

    def test_good_signal_still_needs_genuine_visual_and_headphone_review(self):
        import quality_gate as gate
        data = {
            "format_id": "jelly", "av_scan_file": "render/preview_scan.json",
            "duration_seconds": 5,
        }
        self.report.write_text(json.dumps({
            "schema_version": 1, "scan_complete": True, "format_id": "jelly",
            "master_sha256": "abc", "duration_seconds": 5,
            "unresolved_technical_blockers": [],
            "audio_continuity": {"passed": True, "gaps": []},
            "master_signal_qa": {
                "format_id": "jelly", "signal_preflight_passed": True,
                "blocking_signal_issues": [], "creative_approval": False
            },
        }))
        with self.assertRaisesRegex(gate.GateError, "review must be bound"):
            gate.check_post_render_av_review(data, self.root, "abc", {})


if __name__ == "__main__":
    unittest.main()
