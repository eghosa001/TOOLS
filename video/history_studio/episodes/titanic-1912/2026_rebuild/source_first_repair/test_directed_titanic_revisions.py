#!/usr/bin/env python3
"""Fast source-first Titanic regressions only; no video regeneration."""
from __future__ import annotations
import json,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
def load(p):return json.loads((HERE/p).read_text())
class Revision(unittest.TestCase):
    def test_both_shorts_explicit_unique_visuals_and_no_third_party_modern_scans(self):
        x=load("SHORTS_SOURCE_FIRST_15_DIRECTED_SHOTS.json")
        shots=x["shots"];self.assertEqual(len(shots),16)
        for tag,count in (("titanic_short_01",8),("titanic_short_02",8)):
            group=[z for z in shots if z["tag"]==tag]
            self.assertEqual([z["index"] for z in group],list(range(1,count+1)))
            self.assertTrue(all(z["why"] and z["title"] for z in group))
        self.assertEqual(len([x for x in shots if x["kind"]!="DOCUMENTARY_DIAGRAM" and x["tag"]=="titanic_short_01"]),5)
        self.assertEqual(len([x for x in shots if x["kind"]!="DOCUMENTARY_DIAGRAM" and x["tag"]=="titanic_short_02"]),5)
        self.assertFalse(x["release_approved"])
        self.assertTrue(all(z["url"].startswith("https://commons.wikimedia.org/wiki/File:")
                            and z["licence"]=="PUBLIC DOMAIN" for z in x["photo_sources"]))
        self.assertIn("2024",next(x for x in shots if x["tag"].endswith("02") and x["index"]==2)["subtitle"])
    def test_chapter01_intro_has_10_authentic_images_and_spoken_subscribe(self):
        x=load("CHAPTER01_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),16)
        self.assertEqual(sum(s["visual_kind"]!="graphic" for s in shots),10)
        self.assertEqual(sum(s["visual_kind"]=="graphic" for s in shots),6)
        self.assertTrue(x["subscribe_onscreen_on_final_shot"])
        self.assertFalse(x["public_release_approved"])
    def test_chapter05_ice_warning_messages_not_misidentified(self):
        x=load("CHAPTER05_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),20)
        self.assertEqual(sum(z["visual_kind"]!="graphic" for z in shots),10)
        self.assertEqual(sum(z["visual_kind"]=="graphic" for z in shots),10)
        self.assertFalse(x["release_approved"])
        record=next(z for z in shots if z["scene_id"]=="T05_P10_A")
        self.assertIn("NOT CONFIRMED FATAL BERG",record["onscreen_label"])
        self.assertEqual({z["id"] for z in x["source_candidates"]},
            {"amerika_warning_1912","us_navy_ice_memo_1912",
             "titanic_wireless_signal_1912","lightoller_murdoch_photo",
             "captain_smith_photo","carpathia_iceberg_loc"})
    def test_chapter02_fixed_18_and_12_real_construction_photos(self):
        x=load("CHAPTER02_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),18)
        self.assertEqual(sum(z["visual_kind"]!="graphic" for z in shots),12)
        self.assertEqual(sum(z["visual_kind"]=="graphic" for z in shots),6)
        self.assertFalse(x["film_released"])
        self.assertEqual([z["scene_id"] for z in shots],
          [f"T02_P{p:02d}_{side}" for p in range(1,10) for side in ("A","B")])
    def test_chapter03_fixed_16_and_11_real_historical_items(self):
        x=load("CHAPTER03_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),16)
        self.assertEqual(sum(z["visual_kind"]!="graphic" for z in shots),11)
        self.assertFalse(x["film_released"])
    def test_chapter04_fixed_20_and_11_genuine_lifeboat_photos(self):
        x=load("CHAPTER04_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),20)
        self.assertEqual(sum(z["visual_kind"]!="graphic" for z in shots),11)
        self.assertEqual(sum(z["visual_kind"]=="graphic" for z in shots),9)
        self.assertFalse(x["release_approved"])
        self.assertEqual([z["scene_id"] for z in shots],
          [f"T04_P{p:02d}_{side}" for p in range(1,11) for side in ("A","B")])
    def test_chapter12_fixed_20_and_16_genuine_sources(self):
        x=load("CHAPTER12_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),20)
        self.assertEqual(sum(z["visual_kind"]!="graphic" for z in shots),16)
        self.assertFalse(x["editorial_release_approved"])
    def test_chapter13_fixed_20_and_12_genuine_sources(self):
        x=load("CHAPTER13_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")
        shots=x["shots"]
        self.assertEqual(len(shots),20)
        self.assertEqual(sum(z["visual_kind"]!="graphic" for z in shots),12)
        self.assertFalse(x["video_full_screen_review"])
    def test_four_replaced_chapters_are_original_narration_cuts_without_reordering(self):
        original=json.loads((ROOT/"MANUAL_SCENE_LEDGER_DRAFT.json").read_text())["scenes"]
        for chap in (1,2,3,4,5,12,13):
            target=load(f"CHAPTER{chap:02d}_EXPLICIT_HISTORICAL_PICTURE_EDIT.json")["shots"]
            ids=[z["scene_id"] for z in original if z["chapter"]==chap]
            self.assertEqual(ids,[z["scene_id"] for z in target])
            self.assertTrue(all(z["editorial_why"] for z in target))
    def test_no_full_film_release_claim_from_two_chapters(self):
        x=load("SHORTS_SOURCE_FIRST_15_DIRECTED_SHOTS.json")
        self.assertFalse(x["release_approved"])
        s=(HERE/"assemble_partial_source_first_main_film.py").read_text()
        self.assertIn('"full_source_first_gate":"FAIL"',s)
        self.assertIn('"other_262_shots_legacy_visuals":True',s)
if __name__=="__main__":unittest.main()
