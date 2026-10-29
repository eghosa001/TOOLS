"""Reference evidence integrity tests: never mistake metadata for actual watching."""
import json
import re
import unittest
from pathlib import Path

FILE = Path(__file__).with_name("reference_studies") / "reference_library.json"

class ReferenceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(FILE.read_text(encoding="utf-8"))

    def test_all_previous_original_and_popular_examples_are_catalogued(self):
        ids={v["id"] for v in self.registry["videos"]}
        expected={"kKOJZbthcyo","S47YZ2C7nv4","7gV-0be8WqE",
                  "XJ1SaNX4s8I","j2TVdltvJ_k","Cv19w_2-rMc",
                  "hUSNOEnXdyg","uM48_CTggJY","lzHMQWgZjaI"}
        self.assertTrue(expected.issubset(ids), expected-ids)

    def test_ids_and_sources_are_unique(self):
        vids=self.registry["videos"]
        self.assertEqual(len(vids),self.registry["video_count"])
        ids=[v["id"] for v in vids]
        self.assertEqual(len(ids),len(set(ids)))
        for v in vids:
            self.assertRegex(v["id"],r"^[A-Za-z0-9_-]{11}$")
            self.assertIn(v["id"],v["url"])
            self.assertTrue(v["url"].startswith("https://"))
            self.assertTrue(v["source_document_url"].startswith("https://"))
            self.assertTrue(v["observations"])

    def test_no_unwatched_reference_misrepresented_as_full_review(self):
        for v in self.registry["videos"]:
            if v["decoded_video_frames_examined"] == 0:
                self.assertFalse(v["frame_by_frame_visual_review_completed"])
                self.assertFalse(v["full_audio_listening_completed"])
            for observation in v["observations"]:
                self.assertTrue(observation["provenance"])
                self.assertTrue(observation["time"])
        self.assertIn("BLOCKED",self.registry["status"])

if __name__=="__main__":
    unittest.main()
