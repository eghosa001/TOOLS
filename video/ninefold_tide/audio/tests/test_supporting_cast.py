"""Offline cast expansion and audio-led timing tests. No model downloads."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SERIES=ROOT.parent
class SupportingCastAndTimelineTest(unittest.TestCase):
    def test_all_twenty_canon_actors_and_six_additions(self):
        c=json.loads((ROOT/"cast.json").read_text())
        self.assertEqual(c["character_count"],20)
        ids={x["id"] for x in c["characters"]}
        self.assertEqual(len(ids),20)
        self.assertTrue({"calen","emmet","elen","fara","mari","ren"}<=ids)
        self.assertEqual(17,len(ids-{"naya","kito","iri"}))
        for person in c["characters"]:
            self.assertFalse(person["reference"]["approved"])
            self.assertTrue(person["reference_text"])
            self.assertTrue(person["voice_design_prompt"])
        self.assertIsNone(next(p for p in c["characters"] if p["id"]=="ren")["age"])

    def test_audio_led_proposal_is_34_seconds_without_shot_loss(self):
        proposal=json.loads((ROOT/"pilot_34s_proposed_timing.json").read_text())
        orig=json.loads((SERIES/"pilot_shots.json").read_text())
        shots=proposal["shots"]
        self.assertEqual(816,proposal["total_frames"])
        self.assertEqual(720,orig["total_frames"])
        self.assertEqual([s["id"] for s in orig["shots"]],[s["shot_id"] for s in shots])
        self.assertEqual(34.0,proposal["total_seconds"])
        self.assertEqual(0,shots[0]["start_frame"])
        self.assertEqual(816,shots[-1]["end_frame"])
        self.assertEqual({"ep101_003":36,"ep101_004":24,"ep101_007":36},
                         {x["shot_id"]:x["added_frames"] for x in shots if x["added_frames"]})
        for left,right in zip(shots,shots[1:]):
            self.assertEqual(left["end_frame"],right["start_frame"])
        duration={s["shot_id"]:s["duration_frames"]/24 for s in shots}
        for line in proposal["selected_audio_fit"]:
            self.assertLessEqual(line["duration_seconds"],duration[line["line_id"]])

    def test_supporting_kaggle_batch_code_compiles_and_keeps_model_cache_temporary(self):
        code=json.loads((ROOT/"kaggle_supporting_cast_20.ipynb").read_text())
        cells=[c for c in code["cells"] if c["cell_type"]=="code"]
        self.assertEqual(1,len(cells))
        source="".join(cells[0]["source"])
        compile(source,"cast_batch","exec")
        self.assertIn("/kaggle/temp/ninefold_cast_huggingface_cache",source)
        self.assertIn("UNAPPROVED",source)
        self.assertIn("--takes",source)
        self.assertIn("2",source)

if __name__=="__main__":
    unittest.main()
