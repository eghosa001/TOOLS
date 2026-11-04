"""Approved narrator profile contract; includes exact user-approved sample provenance."""
import json
import re
import unittest
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1] / "APPROVED_NARRATION_VOICE.json"


class ApprovedNaturalNarratorProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_real_user_listening_approval_applies_to_exact_sample(self):
        p = self.profile
        self.assertEqual(p["approval_status"], "USER_APPROVED_VOICE_SAMPLE")
        self.assertEqual(p["approval_origin"], "explicit_chat_approval_after_listening")
        self.assertEqual(p["tts_model"], "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
        self.assertEqual(p["speaker"], "Ryan")
        self.assertEqual(p["reference_sample"]["sha256"],
                         "1cc86a47c3605d60d9f820f2dc06e62804b5e41a0259519987cb515527c7ec93")
        self.assertRegex(p["reference_sample"]["drive_url"], r"^https://drive\.google\.com/file/d/")
        self.assertEqual(p["sample_measured_wpm"], 185.2)

    def test_voice_preference_is_not_blanket_video_release_approval(self):
        p = self.profile
        self.assertFalse(p["full_video_release_approved"])
        self.assertEqual(p["target_wpm"], [170, 210])
        self.assertLessEqual(p["max_post_tempo_factor"], 1.25)
        self.assertIn("human listening", p["remaining_release_checks"])


if __name__ == "__main__":
    unittest.main()
