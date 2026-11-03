#!/usr/bin/env python3
import copy
import importlib.util
import unittest
from pathlib import Path

f=Path(__file__).with_name("release_gate.py")
spec=importlib.util.spec_from_file_location("universal_edit_release_gate",f)
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def valid(category="anime",style="music_sync"):
    return {
        "schema_version":1,"pipeline":"universal_edit","category":category,
        "style":style,"title":"A character learns what was truly lost",
        "visual_sources_policy":"EXISTING_REAL_OR_ORIGINAL_MEDIA_ONLY",
        "media_sources":[{
            "id":"clip","creator":"Original studio archive",
            "source_page":"https://example.org/source/clip",
            "rights_evidence":"https://example.org/source/clip/license",
            "license_url":"https://creativecommons.org/licenses/by/4.0/",
            "rights_status":"cc_by","commercial_use":True,
            "derivatives_allowed":True,"reviewed_on":"2026-11-03",
            "sha256":"a"*64,"file":"clips/source.mp4",
            "required_credit":"Studio archive CC BY 4.0; adapted"
        }],
        "audio_sources":[],
        "timeline":[{
            "source_id":"clip","start_sec":0,"end_sec":9.5,
            "editorial_reason":"The shot establishes a meaningful decision that changes the character's motivations.",
            "complete_moment":{
                "visually_reviewed":True,"beginning_included":True,"payoff_included":True,
                "evidence_note":"The choice and the resulting reaction remain visible in the sequence."
            }
        }],
        "claims":{"coverage":"single_event"},
        "originality":{
            "creative_thesis":"The edit reinterprets the moment as a choice between friendship and self preservation.",
            "source_to_story_map":[
                "The selected action establishes a decision while original timing highlights its cost."
            ],
            "contribution_modes":["original_narrative_structure","original_explanatory_graphics"],
            "graphics_explanation":"The new graphic links the earlier hesitation and later response to explain the character's decision.",
            "editorial_significance_human_review_required":True,
            "uses_voice":False
        },
        "attribution":"Studio archive; CC BY 4.0; selection and new graphics; https://example.org/source/clip",
        "editorial_review":{"approved":False},
        "output":{"file":"candidate/final.mp4"}
    }

class GenericEditGateTests(unittest.TestCase):
    def test_any_category_and_non_narrated_style(self):
        for category in sorted(g.CATEGORIES):
            m=valid(category=category)
            self.assertEqual(g.validate_plan(m)["category"],category)

    def test_unknown_style_blocked(self):
        m=valid();m["style"]="unreviewed_superstyle"
        with self.assertRaises(g.GateError):g.validate_plan(m)

    def test_social_media_clip_with_unclear_rights_high_risk(self):
        m=valid("movie")
        m["media_sources"][0]["rights_status"]="unclear"
        m["media_sources"][0].pop("commercial_use")
        m["media_sources"][0].pop("derivatives_allowed")
        plan=g.validate_plan(m)
        self.assertTrue(plan["risk_flags"])
        with self.assertRaises(g.GateError):g.validate_release(m,".")

    def test_anime_music_sync_requires_substance(self):
        m=valid()
        m["originality"]["contribution_modes"]=["color_grade","speed_ramp","beat_sync"]
        with self.assertRaises(g.GateError):g.validate_plan(m)

    def test_any_edit_does_not_require_voice(self):
        m=valid("gaming","music_sync")
        self.assertEqual(g.validate_plan(m)["style"],"music_sync")

    def test_full_event_missing_payoff_is_blocked(self):
        m=valid("football","analysis")
        m["timeline"][0]["complete_moment"]["payoff_included"]=False
        with self.assertRaises(g.GateError):g.validate_plan(m)

    def test_tiktok_unlicensed_does_not_pass(self):
        m=valid("celebrity","tribute")
        m["media_sources"][0]["commercial_use"]=False
        with self.assertRaises(g.GateError):g.validate_plan(m)

    def test_claiming_all_events_requires_event_ledger(self):
        m=valid("sports","comparison")
        m["title"]="All 48 goals from a season"
        m["claims"]={"coverage":"highlight_selection"}
        with self.assertRaises(g.GateError):g.validate_plan(m)

    def test_unapproved_video_cannot_release(self):
        with self.assertRaises(g.GateError):g.validate_release(valid(),".")

    def test_approval_without_full_viewing_blocks(self):
        m=valid("tv","character_study")
        m["editorial_review"]={"approved":True,"reviewer":"Sample editor","reviewed_on":"2026-11-03"}
        with self.assertRaises(g.GateError):g.validate_plan(m)

    def test_mutated_export_without_sha_blocks(self):
        m=valid()
        m["editorial_review"]={
            "approved":True,"full_export_watched":True,"audio_listened":True,
            "all_moments_complete":True,"substantive_transformation_confirmed":True,
            "rights_confirmed":True,"reviewer":"Human editor","reviewed_on":"2026-11-03",
            "reviewed_output_sha256":"b"*64
        }
        with self.assertRaises(g.GateError):g.validate_release(m,".")

    def test_specific_scene_edits_not_generic_fill(self):
        m=valid();m["timeline"][0]["editorial_reason"]="cool clip"
        with self.assertRaises(g.GateError):g.validate_plan(m)

if __name__=="__main__":unittest.main()
