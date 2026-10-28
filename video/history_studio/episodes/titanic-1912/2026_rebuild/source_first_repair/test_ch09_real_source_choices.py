#!/usr/bin/env python3
"""Source-first Titanic lifeboat evacuation editorial preflight, no movie generation."""
import json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parent.parent
HERE=pathlib.Path(__file__).resolve().parent
class TestShotChoices(unittest.TestCase):
    def test_24_consecutive_sound_aligned_fixed_editor_choices(self):
        script=json.loads((HERE/"CHAPTER09_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())
        original=json.loads((ROOT/"MANUAL_SCENE_LEDGER_DRAFT.json").read_text())["scenes"]
        assert script["chapter"]==9
        got=[s["scene_id"] for s in script["shots"]]
        expected=[s["scene_id"] for s in original if s["chapter"]==9]
        self.assertEqual(len(got),24)
        self.assertEqual(got,expected)
        self.assertEqual(len(set(got)),24)
        self.assertFalse(script["publication_approved"])
    def test_no_random_repeated_photos_to_fake_release(self):
        s=json.loads((HERE/"CHAPTER09_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())["shots"]
        kinds=[x["visual_kind"] for x in s]
        self.assertEqual(kinds.count("photo"),16)
        self.assertEqual(kinds.count("graphic"),8)
        self.assertGreaterEqual(len(set(x["source_asset_id"] for x in s if x["visual_kind"]=="photo")),10)
        for z in s:
            self.assertGreater(len(z["editorial_why"]),90)
            self.assertFalse(z["real_image_id_and_licence_editor_approved"])
            self.assertFalse(z["whole_video_reviewed"])
            self.assertFalse(z["public_release_approved"])
    def test_the_eight_diagrams_are_exact_existing_authored_subjects(self):
        plan=json.loads((ROOT/"REMAINING_11_CHAPTERS_DIRECTED_ART_TYPES.json").read_text())
        approved=set(plan["expected_approved_graphics_per_chapter"]["9"])
        shots=json.loads((HERE/"CHAPTER09_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())["shots"]
        for z in shots:
            if z["visual_kind"]=="graphic":
                self.assertIn(z["source_asset_id"],approved)
    def test_old_private_video_is_not_modified_or_misrepresented(self):
        p=(HERE/"assemble_nine_corrected_chapters.py").read_text()
        self.assertIn('"full_source_first_gate":"FAIL"',p)
        self.assertIn('"youtube_private_draft_updated":False',p)
        self.assertIn('"newly_reedited_shots":174',p)
if __name__=="__main__":unittest.main()
