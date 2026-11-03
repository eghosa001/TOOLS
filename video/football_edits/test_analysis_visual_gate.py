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
    # Artificial team and player names below are fixtures for validating the gate,
    # not claims that any real-world match was played.
    if kind=="match_footage":
        base.update({"depicted_teams":["Home Test FC","Archive Opponent FC"],
                     "depicted_players":["Home Test Player"],
                     "recorded_match_teams":["Home Test FC","Archive Opponent FC"]})
    elif kind=="player_photo":
        base.update({"depicted_teams":[],
                     "depicted_players":["Home Test Player" if id=="player_a" else "Away Test Player"]})
    elif kind=="other_real_football_footage":
        base.update({"depicted_teams":["Unrelated Training FC"],"depicted_players":[]})
    else:
        base.update({"depicted_teams":["Home Test FC"],"depicted_players":[]})
    if kind!="editorial_graphic":
        base.update({
            "source_page":"https://commons.wikimedia.org/wiki/File:Example",
            "rights_evidence":"https://commons.wikimedia.org/wiki/File:Example",
            "rights_status":"cc_by","license_url":"https://creativecommons.org/licenses/by/4.0/",
            "commercial_use":True,"derivatives_allowed":True,
            "rights_checked_on":"2026-11-03","creator":"Original photographer",
            "source_origin":"independent_creator",
            "rights_holder_name":"Original photographer",
            "copyright_control_verified":True,
        })
        if "footage" in kind:
            base.update({"genuine_moving_camera_footage":True,"original_recording_checked":True})
        if kind=="match_footage":
            base.update({"recorded_match":"Home Test FC vs Archive Opponent FC",
                         "recorded_match_date":"2026-10-01"})
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
    s["focal_entities"]=(["Home Test Player","Away Test Player"] if frame=="player_photo_versus"
                         else ["Home Test Player" if ids[0]=="player_a" else "Away Test Player"] if frame=="real_player_photo"
                         else ["Home Test FC"])
    s.update(extra)
    return s


def good():
    return {
        "schema_version":1,"pipeline":"football_analysis_real_media",
        "visual_policy":"REAL_CAPTURED_MEDIA_NO_GENERATIVE_VISUALS",
        "format":"short","analysis_type":"match_preview",
        "title":"Test fixture tactical analysis with relevant original clips",
        "original_analysis":"This original analysis explains how an aggressive defensive line might create openings for counterattacks behind the full backs.",
        "automatic_shot_selection":False,"automatic_media_fallback":False,
        "target":{"teams":["Home Test FC","Away Test FC"],
                  "players":["Home Test Player","Away Test Player"],
                  "fixture_date":"2026-11-03",
                  "latest_previous_matches":[
                    {"team":"Home Test FC","opponent":"Alaves Test FC",
                     "played_on":"2026-10-31","goals_for":6,"goals_against":1,
                     "competition":"League one","result_source":"https://example.org/home-result",
                     "footage_decision":"not_needed",
                     "decision_reason":"Not necessary to show this match in the test tactical edit."},
                    {"team":"Away Test FC","opponent":"Fulham Test FC",
                     "played_on":"2026-10-31","goals_for":1,"goals_against":1,
                     "competition":"League two","result_source":"https://example.org/away-result",
                     "footage_decision":"rights_unavailable",
                     "footage_location":"https://example.org/away-video",
                     "decision_reason":"Video view page does not establish adaptation and commercial rights."}]},
        "sources":[source("match","match_footage","Home Test FC filmed previous match"),
                   source("player_a","player_photo","Barcelona right winger"),
                   source("player_b","player_photo","Aston Villa left back"),
                   source("diagram","editorial_graphic","Original labelled high line diagram")],
        "shots":[
            shot(0,8,"match_action",["match"]),
            shot(8,12,"player_photo_versus",["player_a","player_b"],
                 face_each_other=True,player_names=["Home Test Player","Away Test Player"]),
            shot(12,23,"match_action",["match"]),
            shot(23,27,"tactical_diagram",["diagram"]),
            shot(27,40,"match_action",["match"]),
        ]
    }


class FootballAnalysisVisualGateTests(unittest.TestCase):
    def test_good_photo_versus_and_real_footage_pass(self):
        r=gate.validate_plan(good())
        self.assertEqual(r["real_footage_share"],0.8)
        self.assertEqual(r["match_action_share"],0.8)
        self.assertEqual(r["broll_share"],0.0)
        self.assertEqual(r["photo_share"],0.1)
        self.assertEqual(r["graphics_share"],0.1)

    def test_below_80_percent_real_moving_footage_is_blocked(self):
        m=good()
        # Shift half a second from real match footage to the tactical card:
        # 31.5 of 40 seconds is 78.75% genuine action and must fail.
        m["shots"][3]["end_sec"]=27.5
        m["shots"][4]["start_sec"]=27.5
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_rejects_ronaldo_real_madrid_footage_for_another_match(self):
        m=good()
        m["sources"][0].update({
            "recorded_match":"Real Madrid vs Juventus",
            "recorded_match_teams":["Real Madrid","Juventus"],
            "recorded_match_date":"2026-10-01",
            "depicted_teams":["Real Madrid","Juventus"],
            "depicted_players":["Cristiano Ronaldo"]})
        with self.assertRaisesRegex(gate.VisualGateError,"unrelated"):
            gate.validate_plan(m)

    def test_rejects_unrelated_real_player_photo(self):
        m=good()
        m["sources"][1]["depicted_players"]=["Cristiano Ronaldo"]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_rejects_unrelated_shot_focus_even_with_relevant_footage(self):
        m=good()
        m["shots"][0]["focal_entities"]=["Cristiano Ronaldo"]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_rejects_misidentified_versus_photograph(self):
        m=good()
        m["shots"][1]["player_names"]=["Home Test Player","Cristiano Ronaldo"]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_rejects_unrelated_recording_for_exact_match_review(self):
        m=good()
        m["analysis_type"]="match_review"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_rejects_post_fixture_footage_in_preview(self):
        m=good()
        m["sources"][0]["recorded_match_date"]="2026-11-04"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_rejects_unrelated_training_broll_even_if_licensed(self):
        m=good()
        m["sources"].append(source("broll","other_real_football_footage","Unrelated team training"))
        m["shots"][0]=shot(0,8,"real_football_broll",["broll"])
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_preview_requires_both_latest_completed_games(self):
        m=good()
        del m["target"]["latest_previous_matches"]
        with self.assertRaisesRegex(gate.VisualGateError,"BOTH clubs"):
            gate.validate_plan(m)

    def test_preview_rejects_incomplete_latest_game_check(self):
        m=good()
        m["target"]["latest_previous_matches"].pop()
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_latest_game_must_precede_fixture(self):
        m=good()
        m["target"]["latest_previous_matches"][0]["played_on"]="2026-11-03"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_latest_video_cannot_claim_inclusion_without_exact_source(self):
        m=good()
        m["target"]["latest_previous_matches"][0]["footage_decision"]="include"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_latest_unlicensed_video_must_record_exact_watch_page(self):
        m=good()
        del m["target"]["latest_previous_matches"][1]["footage_location"]
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_latest_video_omission_needs_relevance_or_rights_reason(self):
        m=good()
        m["target"]["latest_previous_matches"][0]["decision_reason"]=""
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_latest_match_names_must_cover_both_sides(self):
        m=good()
        m["target"]["latest_previous_matches"][1]["team"]="Home Test FC"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_independent_creator_is_allowed_not_only_club_channel(self):
        m=good()
        m["sources"][0]["source_origin"]="independent_creator"
        m["sources"][0]["rights_holder_name"]="Independent Match Filmer"
        self.assertGreaterEqual(gate.validate_plan(m)["real_footage_share"],0.8)

    def test_broadcaster_footage_is_allowed_with_direct_license(self):
        m=good()
        m["sources"][0]["source_origin"]="broadcaster"
        m["sources"][0]["rights_status"]="commercial_license"
        m["sources"][0]["rights_holder_name"]="Authorized sports broadcaster"
        self.assertEqual(gate.validate_plan(m)["match_action_share"],0.8)

    def test_third_party_reupload_without_rights_is_blocked(self):
        m=good()
        m["sources"][0]["source_origin"]="archive"
        m["sources"][0]["copyright_control_verified"]=False
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

    def test_unknown_origin_blocked_even_if_footage_real(self):
        m=good()
        m["sources"][0]["source_origin"]="unlicensed_social_mirror"
        with self.assertRaises(gate.VisualGateError):
            gate.validate_plan(m)

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

    def test_generic_stock_cannot_replace_actual_match_footage(self):
        m=good()
        m["sources"].append(source("broll","other_real_football_footage","Anonymous football training footage"))
        m["shots"][0]=shot(0,8,"real_football_broll",["broll"])
        m["shots"][2]=shot(12,23,"real_football_broll",["broll"])
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
