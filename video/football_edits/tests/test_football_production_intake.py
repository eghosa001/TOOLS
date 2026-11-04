"""Regression tests for EVERY future football type; deliberately no media rendering."""
from __future__ import annotations
import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest
from types import SimpleNamespace

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("football_production_intake",ROOT/"production_intake.py")
unit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit)

def blank(analysis_type="match_preview",fmt="short"):
    return unit.new_plan(SimpleNamespace(
        format=fmt,analysis_type=analysis_type,
        team_a="Alpha FC",team_b="Beta FC",
        player_a="First Player",player_b="Second Player",
        fixture_date="2026-12-10" if analysis_type=="match_preview" else "2026-10-31",
        title=None,as_of="2026-11-04"))

def viable_preview():
    p=blank()
    p["target"].update({
        "competition":"International club competition",
        "fixture_time_and_timezone":"19:00 Europe/London",
        "fixture_status":"verified_upcoming"})
    p["research"].update({
        "fixture_sources":["https://official.example.org/fixture/1","https://independent.example.org/game/2"],
        "factual_claims":[
           {"claim":"Example alpha's tactical approach","source_url":"https://official.example.org/recap/1"},
           {"claim":"Example beta defensive shape","source_url":"https://independent.example.org/recap/2"}
        ],
        "searches_by_origin":[
            {"origin":"club","search_result_url":"https://official.example.org/a"},
            {"origin":"broadcaster","search_result_url":"https://broadcast.example.org/a"},
            {"origin":"independent_creator","search_result_url":"https://videographer.example.org/a"}],
        "latest_completed_matches":[
            {"team":"Alpha FC","played_on":"2026-11-01","evidence_url":"https://official.example.org/match/alpha"},
            {"team":"Beta FC","played_on":"2026-11-02","evidence_url":"https://official.example.org/match/beta"}]
    })
    for i,name in enumerate(("Alpha FC","Beta FC"),1):
        p["sources"].append({
            "id":f"video{i}","kind":"match_footage",
            "original_url":f"https://broadcast.example.org/{i}",
            "rights_controller":"Broadcast creator",
            "real_camera_verified":True,"synthetic":False,"rights_status":"pending",
            "actual_match":{"teams":[name,"Sample Opponent"],
                            "date":"2026-11-01" if i==1 else "2026-11-02"}
        })
        p["shots"].append({
            "start_sec":(i-1)*10,"end_sec":i*10,
            "source_id":f"video{i}","visual_type":"match_action",
            "manual_choice":True,"spoken_line":f"Verified tactical commentary line {i}",
            "audio_file":f"qwen_{i}.wav","full_audio_listened":True,
            "on_screen_source_credit":True,"visual_matches_spoken_claim":True,
            "first_frame_actual_football":i==1,"focal_entities":[name],
            "source_in_sec":2,"source_out_sec":12
        })
    return p

class FootballProductionTests(unittest.TestCase):
    def test_default_tempo_is_exactly_135(self):
        p=unit.defaults()
        self.assertEqual(p["audio"]["tempo"],1.35)
        self.assertTrue(p["audio"]["pitch_preserving"])
        self.assertFalse(p["delivery"]["render_on_policy_change"])
        self.assertFalse(p["audio"]["names"]["force_syllable_hyphens"])
    def test_preview_can_start_with_sourced_teams_but_still_unverified(self):
        p=blank()
        self.assertEqual(p["audio"]["tempo"],1.35)
        self.assertEqual(p["status"],"UNVERIFIED_NOT_READY")
        self.assertFalse(p["editorial_review"]["approved"])
    def test_dont_pretend_past_game_is_future(self):
        with self.assertRaises(unit.ProductionBlocked):
            unit.new_plan(SimpleNamespace(format="short",analysis_type="match_preview",
                team_a="Alpha FC",team_b="Beta FC",fixture_date="2026-10-31",
                player_a=None,player_b=None,title=None,as_of="2026-11-04"))
    def test_dont_review_game_that_has_not_happened(self):
        with self.assertRaises(unit.ProductionBlocked):
            unit.new_plan(SimpleNamespace(format="long",analysis_type="match_review",
                team_a="Alpha FC",team_b="Beta FC",fixture_date="2026-12-31",
                player_a=None,player_b=None,title=None,as_of="2026-11-04"))
    def test_unverified_project_blocks_production(self):
        with self.assertRaises(unit.ProductionBlocked):
            unit.validate(blank())
    def test_correctly_sourced_20s_plan_passes_editorial_preflight(self):
        report=unit.validate(viable_preview())
        self.assertEqual(report["status"],"EDITORIAL_PLAN_GATE_PASSED_NOT_COPYRIGHT_CLEARANCE")
        self.assertEqual(report["voice_tempo"],1.35)
        self.assertEqual(report["match_action_share"],1.0)
    def test_goal_for_vs_conceded_mismatch_blocks(self):
        p=viable_preview()
        p["shots"][0].update({"claims_scoring_team":"Alpha FC",
                             "actual_scoring_team":"Sample Opponent",
                             "goal_setup_visible":True,"goal_finish_visible":True})
        with self.assertRaisesRegex(unit.ProductionBlocked,"wrong scoring direction"):
            unit.validate(p)
    def test_cut_before_goal_blocks(self):
        p=viable_preview()
        p["shots"][0].update({"claims_scoring_team":"Alpha FC",
                             "actual_scoring_team":"Alpha FC",
                             "goal_setup_visible":True,"goal_finish_visible":False})
        with self.assertRaises(unit.ProductionBlocked):
            unit.validate(p)
    def test_unrelated_match_fails(self):
        p=viable_preview()
        p["sources"][0]["actual_match"]["teams"]=["Other A","Other B"]
        with self.assertRaises(unit.ProductionBlocked):
            unit.validate(p)
    def test_wrong_tempo_fails(self):
        p=viable_preview()
        p["audio"]["tempo"]=1.48
        with self.assertRaisesRegex(unit.ProductionBlocked,"1.35"):
            unit.validate(p)
    def test_no_real_action_first_frame_fails(self):
        p=viable_preview()
        p["shots"][0]["first_frame_actual_football"]=False
        with self.assertRaisesRegex(unit.ProductionBlocked,"First rendered frame"):
            unit.validate(p)
    def test_plan_does_not_authorize_publication(self):
        p=viable_preview()
        self.assertIn("PLAN_GATE_PASSED",unit.validate(p)["status"])
        with self.assertRaises(unit.ProductionBlocked):
            unit.validate(p,"release")
    def test_photo_versus_cannot_use_wrong_identity(self):
        p=viable_preview()
        p["sources"].extend([
            {"id":"photo_left","kind":"real_player_photo","original_url":"https://commons.example.org/left.jpg",
             "rights_controller":"Named photographer","real_camera_verified":True,"synthetic":False,
             "rights_status":"licensed","depicted_players":["First Player"]},
            {"id":"photo_right","kind":"real_player_photo","original_url":"https://commons.example.org/right.jpg",
             "rights_controller":"Named photographer","real_camera_verified":True,"synthetic":False,
             "rights_status":"licensed","depicted_players":["Second Player"]}
        ])
        p["shots"][1]["player_matchup"]=[
            {"name":"First Player","photo_source_id":"photo_left"},
            {"name":"Wrong Player","photo_source_id":"photo_right"}]
        with self.assertRaisesRegex(unit.ProductionBlocked,"identified source photographs"):
            unit.validate(p)
    def test_real_source_without_rights_review_blocks_release(self):
        p=viable_preview()
        p["editorial_review"].update({
            "every_shot_seen":True,"every_name_heard":True,
            "full_video_watched":True,"all_claims_matched":True,
            "all_goal_directions_verified":True,"every_source_rights_assessed":True,
            "approved":True,"human_reviewer":"Test Editor",
            "output_file":"/some/not_real.mp4",
            "quality_scores":dict.fromkeys(("footage","factual_accuracy","voice","shot_sync","mobile_legibility"),10)})
        p["audio"]["natural_names_reviewed"]=True
        with self.assertRaisesRegex(unit.ProductionBlocked,"Unassessed rights"):
            unit.validate(p,"release")

if __name__=="__main__":
    unittest.main()
