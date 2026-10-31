"""Safe unit fixtures: generated waveforms test *technical* checks, not naturalness."""
import hashlib
import json
import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import foley_source_gate as m


class FoleySourceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.plan = json.loads(m.PLAN.read_text(encoding="utf-8"))

    def fake_wav(self, name, frequency=220, *, amplitude=0.12, rate=48000):
        """Artificial test waveform — never a creative Foley sound asset."""
        path = self.workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as dst:
            dst.setnchannels(1)
            dst.setsampwidth(2)
            dst.setframerate(rate)
            values = [int(32767 * amplitude * math.sin(2 * math.pi * frequency * i / rate))
                      for i in range(4800)]
            dst.writeframes(struct.pack("<" + "h" * len(values), *values))
        return path

    def fill(self, same_waveform=False):
        for i, cue in enumerate(self.plan["cues"]):
            p = self.fake_wav(f"test_{i}.wav", frequency=220 if same_waveform else 220 + i * 31)
            cue.update({
                "asset_path": p.name,
                "wav_sha256": m.digest(p),
                "source_rights_verified": True,
                "technically_verified": True,
                "human_review_approved": True,
                "human_reviewer": "Test Fixture Person",
                "rights": {
                    "basis": "creator_recorded",
                    "creator": "Synthetic technical test — no real creative use",
                    "proof_reference": "Nonproduction unit test fixture"
                }
            })

    def test_plan_is_explicitly_not_finished(self):
        result = m.plan_check(self.plan)
        self.assertEqual(result["planned_cues"], 12)
        self.assertFalse(result["natural_audio_approved"])

    def test_missing_sound_blocks_release(self):
        with self.assertRaisesRegex(ValueError, "Sound missing"):
            m.final_audio_check(self.plan, self.workspace)

    def test_good_test_wavs_pass_technical_source_only_not_mix(self):
        self.fill()
        report = m.final_audio_check(self.plan, self.workspace)
        self.assertEqual(report["inspected_cues"], 12)
        self.assertFalse(report["episode_sound_mix_approved"])

    def test_same_generic_effect_for_every_cue_is_rejected(self):
        self.fill(same_waveform=True)
        with self.assertRaisesRegex(ValueError, "Duplicate generic effect"):
            m.final_audio_check(self.plan, self.workspace)

    def test_unreviewed_source_is_rejected(self):
        self.fill()
        self.plan["cues"][2]["human_review_approved"] = False
        with self.assertRaisesRegex(ValueError, "Human listening"):
            m.final_audio_check(self.plan, self.workspace)

    def test_no_license_proof_is_rejected(self):
        self.fill()
        self.plan["cues"][5]["rights"]["proof_reference"] = None
        with self.assertRaisesRegex(ValueError, "Missing provenance"):
            m.final_audio_check(self.plan, self.workspace)

    def test_wrong_hash_is_rejected(self):
        self.fill()
        self.plan["cues"][0]["wav_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            m.final_audio_check(self.plan, self.workspace)

    def test_clipped_and_empty_pcm_are_rejected(self):
        peak = self.fake_wav("peak.wav", frequency=300, amplitude=1.0)
        with self.assertRaisesRegex(ValueError, "clipped"):
            m.wav_inspection(peak)
        silent = self.workspace / "silent.wav"
        with wave.open(str(silent), "wb") as dst:
            dst.setnchannels(1)
            dst.setsampwidth(2)
            dst.setframerate(48000)
            dst.writeframes(b"\x00\x00" * 480)
        with self.assertRaisesRegex(ValueError, "digital silence"):
            m.wav_inspection(silent)


if __name__ == "__main__":
    unittest.main()
