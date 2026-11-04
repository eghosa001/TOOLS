#!/usr/bin/env python3
"""Tests require no TTS model, internet, or extra Python dependencies."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "speech_gate.py"
spec = importlib.util.spec_from_file_location("speech_gate", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class HumanSpeechGateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.audio = Path(self.folder.name) / "speech.wav"
        self.audio.write_bytes(b"real-binary-audio-hash-test" * 20)
        self.spoken = (
            "Apollo Eleven descended toward the Moon. Armstrong checked the landing site. "
            "Aldrin watched the instruments. The crew heard another warning and continued. "
            "Mission Control confirmed the flight path. The spacecraft touched the Moon. "
            "The crew reported a safe landing. Astronauts later stepped outside and worked."
        )
        self.words = gate.count_words(self.spoken)
        self.seconds = 60 * self.words / 179
        self.m = {
            "mode": "short",
            "canonical_script": self.spoken,
            "spoken_script": self.spoken,
            "target_wpm": [170, 210],
            "post_tempo_factor": 1.08,
            "commercial_audio_rights_verified": True,
            "names": [{
                "canonical": "Armstrong", "spoken_form": "Armstrong",
                "checked_against_reference": True,
                "reference_url": "https://www.nasa.gov/history/",
                "listener_verified_correct": True,
            }],
        }

    def tearDown(self):
        self.folder.cleanup()

    def evaluate(self, stage="draft", silence=None):
        return gate.audit(self.m, self.audio, stage,
                          duration=self.seconds,
                          silence=[] if silence is None else silence)

    def test_fast_clear_narration_passes_draft(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "PASS")
        self.assertAlmostEqual(result["measured_wpm"], 179, places=1)

    def test_slow_robovoice_fails_even_when_technically_valid_audio(self):
        self.seconds = 60 * self.words / 121
        self.assertEqual(self.evaluate()["status"], "FAIL")

    def test_too_fast_mangled_speech_fails(self):
        self.seconds = 60 * self.words / 255
        self.assertEqual(self.evaluate()["status"], "FAIL")

    def test_ambiguous_numerical_year_is_rejected(self):
        self.m["spoken_script"] = self.spoken.replace("Apollo Eleven", "Apollo Eleven in 1969")
        self.assertEqual(self.evaluate()["status"], "FAIL")

    def test_1_48_speed_stretch_is_blocked(self):
        self.m["post_tempo_factor"] = 1.48
        self.assertEqual(self.evaluate()["status"], "FAIL")

    def test_invalid_name_reference_blocks_release(self):
        self.m["names"][0]["checked_against_reference"] = False
        self.m["names"][0]["reference_url"] = "http://example.com"
        self._valid_review()
        outcome = self.evaluate("release")
        self.assertEqual(outcome["status"], "FAIL")
        self.assertTrue(any("name[1]" in e for e in outcome["errors"]))

    def _valid_review(self):
        self.m["human_listening_review"] = {
            "reviewer": "Actual editorial listener",
            "notes": "Full audio heard, including correct Armstrong, natural pacing and final cadence.",
            "complete_listen": True,
            "natural_conversational_prosody": True,
            "all_proper_names_correct": True,
            "all_names_inventory_complete": True,
            "no_clipped_or_swallowed_words": True,
            "matches_picture_and_subtitles": True,
            "audio_sha256": hashlib.sha256(self.audio.read_bytes()).hexdigest(),
        }

    def test_cannot_publish_without_human_listening(self):
        self.assertEqual(self.evaluate("release")["status"], "FAIL")

    def test_full_real_listener_can_sign_exact_audio(self):
        self._valid_review()
        outcome = self.evaluate("release")
        self.assertEqual(outcome["status"], "PASS")
        self.assertTrue(outcome["human_naturalness_certified"])

    def test_modified_voice_invalidates_approval(self):
        self._valid_review()
        self.audio.write_bytes(b"altered audio file" * 22)
        self.assertEqual(self.evaluate("release")["status"], "FAIL")

    def test_unreviewed_lengthy_pauses_fail_publication(self):
        self._valid_review()
        self.assertEqual(self.evaluate("release", silence=[
            {"start": 2.1, "end": 3.3, "length": 1.2},
        ])["status"], "FAIL")
        self.m["human_listening_review"]["intentional_pauses_reviewed"] = True
        self.assertEqual(self.evaluate("release", silence=[
            {"start": 2.1, "end": 3.3, "length": 1.2},
        ])["status"], "PASS")

    def test_missing_pronunciation_inventory_cannot_publish(self):
        self._valid_review()
        self.m["names"] = []
        self.assertEqual(self.evaluate("release")["status"], "FAIL")
        self.m["no_proper_names_attested"] = True
        self.assertEqual(self.evaluate("release")["status"], "PASS")

    def test_missing_name_inventory_approval_cannot_publish(self):
        self._valid_review()
        self.m["human_listening_review"]["all_names_inventory_complete"] = False
        self.assertEqual(self.evaluate("release")["status"], "FAIL")

    def test_missing_commercial_license_fails(self):
        self.m["commercial_audio_rights_verified"] = False
        self.assertEqual(self.evaluate()["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
