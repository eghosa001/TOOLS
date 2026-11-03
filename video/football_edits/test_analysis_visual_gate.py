#!/usr/bin/env python3
"""Regression checks for real-camera, match-footage-first football analysis."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location(
    "football_analysis_visual_gate",Path(__file__).with_name("analysis_visual_gate.py"))
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def source(id,kind,subject):
    base={
        "id":id,"kind":kind,"subject":subject,
        "editorial_reason":"Authentic subject-specific visual selected to explain this play",
        "file":"assets/"+id+".mp4" if "footage" in kind else "assets/"+id+".png",
        "sha256":"a"*64,"is_ai_generated":False,
        "camera_capture":kind!="editorial_graphic"
    }
    if kind!="editorial_graphic":
        base.update({
            "source_page":"https://commons.wikimedia.org/wiki/File:Example",
            "rights_evidence":"https://commons.wikimedia.org/wiki/File:Example",
            "rights_status":"cc_by","license_url":"https://creativecommons.org/licenses/by/4.0/",
            "commercial_use":True,"derivatives_allowed":True,
            "rights_checked_on":"2026-11-03","creator":"Original photographer",
        })
        if "footage" in kind:
            base.update({"genuine_moving_camera_footage":True,"original_recording_checked":True})
        if kind=="match_footage":
            base.update({"recorded_match":"Barcelona vs Aston Villa",
                         "recorded_match_date":"2026-11-03"})
    else:
        base["created_by_editor"]=True
    return base


def shot(start,end,frame,ids,**extra):
    s={
        "start_sec":start,"end_sec":end,"frame_type":frame,"source_ids":ids,
        "spoken_line":"A specific original football tactical explanation in the narration.",
        "editorial_reason":"This exact shot demonstrates the football movement in the script.",
        "manually_selected":True}
    if frame in {"match_action","real_football_broll"}:
        s.update({"source_in_sec":start+30,"source_out_sec":end+30,"real_motion_verified":True})
    elif frame in {"real_player_photo","player_photo_versus"}:
        s["photographs_unaltered_identity"]=True
    else:
        s["illustrative_not_match_recording"]=True
    s.update(extra)
    return s


def good():
    return {
        "schema_version":1,"pipeline":"football_analysis_real_media",
        "visual_policy":"REAL_CAPTURED_MEDIA_NO_GENERATIVE_VISUALS",
        "format":"short","analysis_type":"match_preview",
        "title":"Barcelona vs Villa tactical analysis with authentic clips",
        "original_analysis":"This original analysis explains how an aggressive defensive line might create openings for counterattacks behind the full backs.",
        "automatic_shot_selection":False,"automatic_media_fallback":False,
        "sources":[source("match","match_footage","Barcelona vs Aston Villa genuine historical match"),
                   source("player_a","player_photo","Barcelona right winger"),
                   source("player_b","player_photo","Aston Villa left back"),
                   source("diagram","editorial_graphic","Original labelled high line diagram")],
        "shots":[
            shot(0,8,"match_action",["match"]),
            shot(8,12,"player_photo_versus",["player_a","player_b"],
                 face_each_other=True,player_names=["Player A","Player B"]),
            shot(12,23,"match_action",["match"]),
            shot(23,29,"tactical_diagram",["diagram"]),
            shot(29,38,"match_action",["match"]),
            shot(38,40,"stat_card",["diagram"]),
        ]
    }


class FootballAnalysisVisualGateTests(unittest.TestCase):
    def test_good_photo_versus_and_real_footage_pass(self):
        r=gate.validate_plan(good())
        self.assertEqual(r["real_footage_share"],0.7)
        self.assertEqual(r["photo_share"],0.1)
        self.assertEqual(r["graphics_share"],0.2)

    def test_no_synthetic_face_images(self):
        m=good();m["sources"][1]["is_ai_generated"]=True
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_ai_footage_fallback(self):
        m=good();m["automatic_media_fallback"]=True
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_automatic_shot_selection(self):
        m=good();m["automatic_shot_selection"]=True
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_unlicensed_footage(self):
        m=good();m["sources"][0]["commercial_use"]=False
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_cannot_label_photograph_as_real_moving_footage(self):
        m=good();m["sources"][0]["genuine_moving_camera_footage"]=False
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_synthetic_visual_kind(self):
        m=good();m["shots"][0]["frame_type"]="ai_football_video"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_generic_video_in_place_of_match_action(self):
        m=good();m["sources"][0]["kind"]="other_real_football_footage"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_still_heavy_slideshow(self):
        m=good()
        m["shots"]=[
          shot(0,6,"real_player_photo",["player_a"]),
          shot(6,12,"real_player_photo",["player_b"]),
          shot(12,18,"tactical_diagram",["diagram"]),
          shot(18,24,"real_player_photo",["player_a"]),
          shot(24,30,"tactical_diagram",["diagram"]),
          shot(30,40,"match_action",["match"])
        ]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_fake_versus_of_one_player(self):
        m=good();m["shots"][1]["source_ids"]=["player_a"]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_very_long_static_cards(self):
        m=good();m["shots"][3]["end_sec"]=32
        m["shots"][4]["start_sec"]=32
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_source_id_unknown(self):
        m=good();m["shots"][3]["source_ids"]=["random_clip"]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_no_missing_shot_timeline(self):
        m=good();m["shots"][2]["start_sec"]=13
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_player_comparison_requires_photo_versus(self):
        m=good();m["analysis_type"]="player_comparison"
        m["shots"][1]=shot(8,12,"real_player_photo",["player_a"])
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_release_does_not_auto_approve_from_a_good_plan(self):
        with self.assertRaises(gate.VisualGateError):
            gate.validate_release(good(),Path("."))


if __name__=="__main__":
    unittest.main()
