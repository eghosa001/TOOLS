"""Offline QA for the Ninefold Tide voice pipeline. Does not download models."""
import copy
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
import voice_pipeline as vp


class VoicePipelineTest(unittest.TestCase):
    def setUp(self):
        self.c = vp.load(ROOT / "cast.json")
        self.l = vp.load(ROOT / "pronunciation_lexicon.json")
        self.s = vp.load(ROOT / "pilot_voice_lines.json")

    def test_all_twenty_characters_are_canon_indexed(self):
        self.assertEqual(20, len(self.c["characters"]))
        self.assertEqual(20, self.c["character_count"])
        for person in self.c["characters"]:
            self.assertEqual(False, person["reference"]["approved"])
            self.assertFalse(person["casting_status"] == "fully approved")
        for id in ("fara", "mari", "ren", "calen", "emmet", "elen"):
            self.assertIn(id, [c["id"] for c in self.c["characters"]])
        self.assertEqual({"naya", "kito", "iri"}, {v["id"] for v in self.c["characters"][:3]})

    def test_seven_dialogue_turns_match_locked_script(self):
        errors = vp.audit(self.c, self.l, self.s, ROOT, "structure")
        self.assertEqual([], errors)

    def test_no_voice_pretends_to_be_approved(self):
        failures = vp.audit(self.c, self.l, self.s, ROOT, "release")
        self.assertTrue(any("not auditioned" in problem for problem in failures))
        self.assertTrue(any("pronunciation" in problem for problem in failures))
        self.assertTrue(any("approved natural-performance take" in problem for problem in failures))

    def test_provisional_name_never_silently_changes_spoken_script(self):
        text = "Kito and Iri met Naya at Mastmarket."
        spoken, warnings = vp.apply_lexicon(text, self.l, strict=False)
        self.assertEqual(text, spoken)
        self.assertGreaterEqual(len(warnings), 4)
        with self.assertRaises(ValueError):
            vp.apply_lexicon(text, self.l, strict=True)

    def test_only_checked_approved_alias_is_used(self):
        lex = copy.deepcopy(self.l)
        kito = next(x for x in lex["terms"] if x["written"] == "Kito")
        kito["approved"] = True
        kito["model_speech_alias"] = "Kee-toh"
        kito["alias_verified"] = True
        spoken, _ = vp.apply_lexicon("Kito speaks to Kito.", lex, strict=False)
        self.assertEqual("Kee-toh speaks to Kee-toh.", spoken)

    def test_pcm_metrics_and_checksum_are_based_on_real_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "sine.wav"
            rate = 24000
            values = [int(5000 * math.sin(2 * math.pi * 230 * i / rate)) for i in range(rate)]
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(struct.pack("<" + "h" * len(values), *values))
            report = vp.inspect_wav(wav)
            self.assertAlmostEqual(report["duration_seconds"], 1.0)
            self.assertLess(report["clipped_ratio"], .001)
            self.assertEqual(len(report["sha256"]), 64)

    def test_human_review_requires_strict_listening_bar(self):
        empty = {"scores": {k: 5 for k in vp.QUALITIES}}
        self.assertGreater(len(vp.check_review(empty)), 3)

    def test_working_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self.assertEqual(3, len(vp.prepare(path)["created"]))
            cast = path / "cast.json"
            cast.write_text("manual change", encoding="utf-8")
            self.assertEqual(0, len(vp.prepare(path)["created"]))
            self.assertEqual(cast.read_text(), "manual change")


if __name__ == "__main__":
    unittest.main()
