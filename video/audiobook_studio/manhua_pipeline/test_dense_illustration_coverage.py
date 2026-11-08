"""A full audiobook cannot hold one illustration for a minute.

Synthetic text only: never commit unpublished user manuscripts or artwork here.
"""
import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from video.audiobook_studio.manhua_pipeline.assemble_existing import _scenes
from video.audiobook_studio.manhua_pipeline.core import dense_illustration_plan
from video.audiobook_studio.manhua_pipeline.kaggle_runner import scene_timeline


class DenseIllustrationCoverageTests(unittest.TestCase):
    def make_chunks(self, count=25, words_per_chunk=144):
        pattern = ("The engineer examined the copper conduit while the young "
                   "cultivator watched for a dangerous structural fault nearby")
        source = pattern.split()
        result = []
        for i in range(count):
            text = " ".join(source[j % len(source)] for j in range(words_per_chunk))
            result.append({"index": i, "words": words_per_chunk, "text": text})
        return result

    def test_24_minute_narration_needs_hundreds_of_distinct_shots(self):
        chunks = self.make_chunks()
        shots = dense_illustration_plan(chunks, style="science_fiction")
        self.assertGreaterEqual(len(shots), 180)
        self.assertLessEqual(len(shots), 288)
        self.assertEqual([s["scene"] for s in shots], list(range(len(shots))))
        self.assertEqual(len({s["key"] for s in shots}), len(shots))
        self.assertEqual(" ".join(s["source_text"] for s in shots),
                         " ".join(c["text"] for c in chunks))
        spans = scene_timeline(shots, [57.6] * len(chunks))
        self.assertAlmostEqual(sum(spans), 24 * 60, delta=0.001)
        self.assertLessEqual(max(spans), 10.0)
        self.assertLessEqual(sum(spans) / len(spans), 8.0)

    def test_one_minute_per_picture_is_rejected(self):
        old_24_stills = [
            {"scene": i, "start_chunk": i, "end_chunk": i + 1}
            for i in range(24)
        ]
        with self.assertRaisesRegex(ValueError, "ILLUSTRATION_CADENCE_FAILED"):
            scene_timeline(old_24_stills, [60.0] * 24)

    def test_unusually_slow_voice_triggers_more_illustrations(self):
        chunks = self.make_chunks()
        shots = dense_illustration_plan(chunks, style="science_fiction")
        with self.assertRaisesRegex(ValueError, "ILLUSTRATION_CADENCE_FAILED"):
            scene_timeline(shots, [105.0] * len(chunks))

    def test_cpu_assembler_refuses_24_one_minute_images(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panels = []
            for i in range(24):
                p = root / f"frame_{i:03d}.png"
                p.write_bytes(bytes([i]) * 2048)
                panels.append({"image": str(p), "seconds": 60.0})
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps(panels))
            args = SimpleNamespace(timeline=str(timeline), image=None)
            with self.assertRaisesRegex(ValueError, "ILLUSTRATION_CADENCE_FAILED"):
                _scenes(args, 24 * 60)

    def test_cpu_assembler_refuses_reused_identical_art(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "same.png"
            p.write_bytes(b"x" * 2048)
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps([
                {"image": str(p), "seconds": 5.0},
                {"image": str(p), "seconds": 5.0},
            ]))
            args = SimpleNamespace(timeline=str(timeline), image=None)
            with self.assertRaisesRegex(ValueError, "DUPLICATED_ILLUSTRATIONS"):
                _scenes(args, 10.0)

    def test_cannot_skip_narration_words_or_overlap(self):
        chunks = self.make_chunks(count=2)
        shots = dense_illustration_plan(chunks, style="science_fiction")
        shots[1]["chunk_start_word"] += 1
        with self.assertRaisesRegex(ValueError, "gaps or overlaps"):
            scene_timeline(shots, [58.0] * len(chunks))


if __name__ == "__main__":
    unittest.main()
