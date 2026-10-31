"""Evidence gate tests; synthetic waveforms test engineering only, never premium Foley."""
import copy
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from production.licensed_footage_gate import (
    StockGateError, verify_contact_audio_ledger, verify_export_audio,
)


class StockAudioReleaseTests(unittest.TestCase):
    def setUp(self):
        self.audio = [{"file": "original_slime.wav", "license": "CC0", "recorded_material": "wet slime", "recorded_action": "hands stretching and squeezing wet slime"}]
        self.shot = {
            "duration": 5.0,
            "material_family": "wet slime",
            "continuous_texture_covered": True,
            "texture_coverage_notes": (
                "The real squelching continues as the hands fold the elastic slime; "
                "audible pressure decreases naturally as the fingers release."
            ),
            "contact_checks": [{
                "visual_contact_frame": 36,
                "audio_onset_frame": 37,
                "sound_source_index": 0,
                "material_family": "wet slime",
                "interaction": "finger pads compressing wet slime",
                "visual_intensity": "gentle",
                "audio_intensity": "gentle",
                "energy_match": True,
                "timbre_harshness_match": True,
                "auditioned_with_picture": True,
                "audition_notes": (
                    "Editor observed finger pressure at frame 36, heard a soft "
                    "wet compression at frame 37, then a natural elastic release."
                ),
            }],
        }

    def check(self, shot):
        return verify_contact_audio_ledger([shot], self.audio)

    def test_editor_mapped_contact_with_matching_source_and_force(self):
        self.assertEqual(self.check(self.shot), 1)

    def test_two_frame_sync_error_blocks_release(self):
        s = copy.deepcopy(self.shot)
        s["contact_checks"][0]["audio_onset_frame"] = 39
        with self.assertRaisesRegex(StockGateError, ">1 frame"):
            self.check(s)

    def test_generic_wrong_material_blocks_release(self):
        s = copy.deepcopy(self.shot)
        s["contact_checks"][0]["material_family"] = "dry gravel"
        with self.assertRaisesRegex(StockGateError, "actual visible material"):
            self.check(s)

    def test_wrong_source_recorded_material_blocks_release(self):
        self.audio[0]["recorded_material"] = "water"
        with self.assertRaisesRegex(StockGateError, "recorded material/action"):
            self.check(self.shot)

    def test_harsh_sound_against_gentle_press_blocks_release(self):
        s = copy.deepcopy(self.shot)
        s["contact_checks"][0]["audio_intensity"] = "impact"
        with self.assertRaisesRegex(StockGateError, "intensity differ"):
            self.check(s)

    def test_unauditioned_cue_blocks_release(self):
        s = copy.deepcopy(self.shot)
        s["contact_checks"][0]["auditioned_with_picture"] = False
        with self.assertRaisesRegex(StockGateError, "not reviewed"):
            self.check(s)

    def test_no_texture_continuity_evidence_blocks_release(self):
        s = copy.deepcopy(self.shot)
        s["continuous_texture_covered"] = False
        with self.assertRaisesRegex(StockGateError, "material texture"):
            self.check(s)

    def test_unidentified_foley_source_blocks_release(self):
        s = copy.deepcopy(self.shot)
        s["contact_checks"][0]["sound_source_index"] = 77
        with self.assertRaisesRegex(StockGateError, "unknown provenance"):
            self.check(s)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg unavailable")
    def test_exact_encoded_stereo_master_and_silence_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "good.mp4"
            subprocess.run([
                "ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi",
                "-i", "color=c=black:s=720x1280:r=24:d=1",
                "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=48000:duration=1",
                "-t", "1", "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000",
                "-ac", "2", "-shortest", "-y", str(good)
            ], check=True, capture_output=True, timeout=60)
            expected = hashlib.sha256(good.read_bytes()).hexdigest()
            result = verify_export_audio(good, expected, 1.0)
            self.assertTrue(result["audio_continuity"]["passed"])
            with self.assertRaisesRegex(StockGateError, "SHA256 mismatch"):
                verify_export_audio(good, "a"*64, 1.0)


if __name__ == "__main__":
    unittest.main()
