import hashlib
import json
import tempfile
import unittest
import wave
from pathlib import Path
from godot_episode_timeline import compile_timeline


class TestEpisodeTimeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = json.loads((Path(__file__).parent / "story.json").read_text())

    def test_canonical_74_lines_unchanged(self):
        snapshot = json.dumps(self.story["dialogue"], ensure_ascii=False, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as root:
            result = compile_timeline(self.story, Path(root))
            self.assertEqual(result["line_count"], 74)
            self.assertEqual(result["audio_line_count"], 0)
            self.assertEqual(result["timing_source"], "estimated_silent")
            self.assertEqual(result["dialogue_sha256"], hashlib.sha256(snapshot.encode()).hexdigest())
            for event, source in zip(result["events"], self.story["dialogue"]):
                self.assertEqual((event["speaker"], event["text"]), (source["speaker"], source["text"]))
                self.assertGreater(event["end"], event["start"])
            for a, b in zip(result["events"], result["events"][1:]):
                self.assertGreater(b["start"], a["end"])
            self.assertEqual((Path(root) / "subtitles.srt").read_text().count(" --> "), 74)
        self.assertEqual(snapshot, json.dumps(self.story["dialogue"], ensure_ascii=False, separators=(",", ":")))

    def test_actual_wav_duration(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / "audio").mkdir()
            with wave.open(str(root / "audio/line_001.wav"), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(16000)
                f.writeframes(b"\x00\x00" * 32000)
            result = compile_timeline(self.story, root / "out", root / "audio")
            self.assertEqual(result["timing_source"], "mixed")
            self.assertEqual(result["audio_line_count"], 1)
            self.assertEqual(result["events"][0]["end"], 2.0)
            self.assertTrue((root / "out/audio/line_001.wav").is_file())

    def test_rejects_unknown_speaker(self):
        altered = json.loads(json.dumps(self.story))
        altered["dialogue"][0]["speaker"] = "not_in_cast"
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                compile_timeline(altered, Path(root))


if __name__ == "__main__":
    unittest.main()
