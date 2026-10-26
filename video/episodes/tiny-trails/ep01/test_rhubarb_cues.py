#!/usr/bin/env python3
"""No-render regression checks for phonetic cue payload / original dialogue lock."""
import hashlib
import json
import struct
import tempfile
import unittest
import wave
from pathlib import Path

import mouth_animation as motion
import prepare_rhubarb_cues as cues

HERE = Path(__file__).resolve().parent


def fake_wav(path, samples=8000):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(struct.pack("<" + "h" * samples, *([1000] * samples)))


class MouthCueTests(unittest.TestCase):
    def test_valid_actual_timed_shapes(self):
        self.assertEqual(cues.check_cues([
            {"start": 0, "end": .20, "value": "D"},
            {"start": .20, "end": .50, "value": "X"}], .50), 2)

    def test_reject_malformed_cues(self):
        wrong=[
          [{"start":0.10,"end":0.50,"value":"D"}],
          [{"start":0.0,"end":0.50,"value":"INVALID"}],
          [{"start":0.0,"end":0.30,"value":"D"},{"start":0.2,"end":0.5,"value":"X"}],
          [{"start":0.0,"end":0.5,"value":"X"}],
          [{"start":0.0,"end":0.5,"value":"D"},{"start":0.5,"end":1.9,"value":"X"}]
        ]
        for invalid in wrong:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                cues.check_cues(invalid, .5)

    def test_orig_audio_and_dialogue_bindings_are_strict(self):
        story=json.loads((HERE/"story.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            rows=[]
            for line in story["dialogue"]:
                wav=temp / ("line_%03d.wav" % line["id"])
                fake_wav(wav)
                rows.append({
                  "id":line["id"],"speaker":line["speaker"],
                  "text_sha256":hashlib.sha256(line["text"].encode()).hexdigest(),
                  "wav_sha256":cues.sha256(wav),
                  "story_start":line["start"],"story_end":line["end"],
                  "cues":[{"start":0,"end":.20,"value":"D"},
                          {"start":.20,"end":.50,"value":"X"}]})
            payload={"schema_version":1,"title":story["title"],
                     "original_story_sha256":cues.sha256(HERE/"story.json"),
                     "lines":rows}
            (temp/"mouth-cues.json").write_text(json.dumps(payload))
            validated=motion.verify_manifest(temp,story,required=True)
            self.assertEqual(len(validated),15)
            start,end,levels=motion.jaw_samples_for_line(story["dialogue"][0],rows[0])
            self.assertEqual(len(levels),end-start+1)
            self.assertGreater(max(levels),min(levels))
            # Audio was changed but mouth cues weren't regenerated => fail closed.
            with (temp/"line_001.wav").open("ab") as f:
                f.write(b"x")
            with self.assertRaises(ValueError):
                motion.verify_manifest(temp,story,required=True)


if __name__ == "__main__":
    unittest.main()
