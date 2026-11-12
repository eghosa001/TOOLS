import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from episode_quality_gate import HARD_GATES, ROLES, validate_scorecard

PRE="2026-11-12T10:00:00Z"
BEGIN="2026-11-12T10:01:00Z"
END="2026-11-12T11:00:00Z"

def example():
    p={"schema_version":1,"series_id":"Example_Story","episode_id":"E03",
       "source_sha256":"a"*64,
       "team_roster":[{"member_id":"lead","name":"Example reviewer","roles":list(ROLES)}]}
    for phase in HARD_GATES:
        when=PRE if phase=="preproduction" else END
        cards={}
        for role,config in ROLES.items():
            cards[role]=[{"member_id":"lead","reviewer":"Example reviewer",
                          "signed_review_reference":"Private example signature",
                          "reviewed_at":when,"approved":True,
                          "scores":{k:{"score":8,"evidence":"Example scene-specific checked evidence"}
                                    for k in config[phase]}}]
        stage={"checked_at":when,"hard_gates":{g:True for g in HARD_GATES[phase]},
               "team_scorecards":cards,"unresolved_blockers":[]}
        if phase=="predelivery":
            stage.update({"production_started_at":BEGIN,"final_mp4_sha256":"b"*64,
                          "drive_file_id":"1ExampleDriveFileId",
                          "drive_file_url":"https://drive.google.com/file/d/1ExampleDriveFileId/view",
                          "drive_file_size_bytes":5000,
                          "drive_verification_reference":"Drive metadata review receipt",
                          "final_encoded_video_review_reference":"Complete video watch log"})
        p[phase]=stage
    return p

class ScorecardTests(unittest.TestCase):
    def test_all_roles_and_15_final_categories_8_pass(self):
        p=example()
        a=validate_scorecard(p)
        b=validate_scorecard(p,"predelivery")
        self.assertEqual(a["lowest_score"],8)
        self.assertEqual(b["lowest_score"],8)
        self.assertEqual(b["category_scores_checked"],15)
    def test_any_79_fails_even_if_other_scores_10(self):
        p=example()
        for role in ROLES:
            for rec in p["predelivery"]["team_scorecards"][role]:
                for score in rec["scores"].values():score["score"]=10
        p["predelivery"]["team_scorecards"]["story_editor"][0]["scores"]["scene_accuracy"]["score"]=7.9
        with self.assertRaisesRegex(ValueError,"SCORE_BELOW_8"):
            validate_scorecard(p,"predelivery")
    def test_preproduction_79_blocks_production(self):
        p=example()
        p["preproduction"]["team_scorecards"]["visual_director"][0]["scores"]["proven_scene_artwork_method"]["score"]=7.9
        with self.assertRaisesRegex(ValueError,"SCORE_BELOW_8"):validate_scorecard(p)
    def test_every_team_member_including_second_review_is_mandatory(self):
        p=example()
        p["team_roster"].append({"member_id":"other","name":"Second member","roles":["sound_engineer"]})
        with self.assertRaisesRegex(ValueError,"MISSING_TEAM_MEMBER_REVIEW"):validate_scorecard(p)
    def test_missing_role_blocks(self):
        p=example()
        p["team_roster"][0]["roles"].remove("visual_director")
        with self.assertRaisesRegex(ValueError,"ALL_SIX_ROLES"):validate_scorecard(p)
    def test_another_member_can_never_be_overridden_by_team_average(self):
        p=example()
        p["team_roster"].append({"member_id":"other","name":"Second reviewer",
                                 "roles":["sound_engineer"]})
        other={"member_id":"other","reviewer":"Second reviewer",
               "signed_review_reference":"Second signed human review",
               "reviewed_at":PRE,"approved":True,
               "scores":{"music_first_rights_and_workflow_ready":
                   {"score":8,"evidence":"Verified soundtrack and rights receipt"}}}
        p["preproduction"]["team_scorecards"]["sound_engineer"].append(other)
        second=other.copy()
        second["reviewed_at"]=END
        second["scores"]={"audio_mix_quality":
                          {"score":7.9,"evidence":"Music masked a sentence in scene 12"}}
        p["predelivery"]["team_scorecards"]["sound_engineer"].append(second)
        with self.assertRaisesRegex(ValueError,"SCORE_BELOW_8"):
            validate_scorecard(p,"predelivery")

    def test_reviewer_must_match_assigned_team_member(self):
        p=example()
        p["preproduction"]["team_scorecards"]["story_editor"][0]["reviewer"]="Someone else"
        with self.assertRaisesRegex(ValueError,"REVIEWER_ROSTER_IDENTITY_MISMATCH"):
            validate_scorecard(p)

    def test_unsigned_review_blocks(self):
        p=example()
        p["predelivery"]["team_scorecards"]["release_qa"][0]["signed_review_reference"]=""
        with self.assertRaisesRegex(ValueError,"SIGNED_REVIEW"):validate_scorecard(p,"predelivery")
    def test_missing_final_category_blocks(self):
        p=example()
        del p["predelivery"]["team_scorecards"]["visual_director"][0]["scores"]["background_world_accuracy"]
        with self.assertRaisesRegex(ValueError,"ALL_ASSIGNED_CATEGORIES"):validate_scorecard(p,"predelivery")
    def test_hard_gates_fail_closed(self):
        p=example()
        p["preproduction"]["hard_gates"]["drive_delivery_method_verified"]=False
        with self.assertRaisesRegex(ValueError,"HARD_GATE_FAILED"):validate_scorecard(p)
        p=example()
        del p["predelivery"]["hard_gates"]["story_image_match"]
        with self.assertRaisesRegex(ValueError,"ALL_HARD_GATES"):validate_scorecard(p,"predelivery")
    def test_no_unresolved_blocker(self):
        p=example()
        p["preproduction"]["unresolved_blockers"]=["Bad characters"]
        with self.assertRaisesRegex(ValueError,"UNRESOLVED_BLOCKERS"):validate_scorecard(p)
    def test_preflight_must_precede_first_work(self):
        p=example()
        p["predelivery"]["production_started_at"]="2026-11-12T09:00:00Z"
        with self.assertRaisesRegex(ValueError,"PREFLIGHT_MUST_PRECEDE_PRODUCTION"):
            validate_scorecard(p,"predelivery")
    def test_assembler_blocks_before_audio_when_scorecard_missing(self):
        from argparse import Namespace
        from video.audiobook_studio.manhua_pipeline.assemble_existing import assemble
        with self.assertRaisesRegex(ValueError,"PREPRODUCTION_8_PLUS_SCORECARD_REQUIRED"):
            assemble(Namespace(art_policy="full_color_panels", quality_scorecard=None))

    def test_art_compositor_blocks_before_asset_loading(self):
        from video.audiobook_studio.manhua_pipeline.compose_reusable import compose
        with self.assertRaisesRegex(ValueError,"PREPRODUCTION_8_PLUS_SCORECARD_REQUIRED"):
            compose(Path("/missing/manifest.json"), Path("/missing/approved.txt"), Path("/missing/out"))

    def test_actual_file_hash_and_size(self):
        p=example()
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"verified.mp4"
            content=b"testvideo"*800
            f.write_bytes(content)
            p["predelivery"]["drive_file_size_bytes"]=len(content)
            p["predelivery"]["final_mp4_sha256"]=hashlib.sha256(content).hexdigest()
            self.assertTrue(validate_scorecard(p,"predelivery",f)["actual_mp4_hash_checked"])
            p["predelivery"]["final_mp4_sha256"]="b"*64
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):validate_scorecard(p,"predelivery",f)
    def test_boolean_and_string_not_scores(self):
        for score in (True,"8",None,7.99,10.1):
            p=example()
            p["preproduction"]["team_scorecards"]["story_editor"][0]["scores"]["approved_canon_and_script"]["score"]=score
            with self.subTest(score=score),self.assertRaisesRegex(ValueError,"SCORE_BELOW_8"):
                validate_scorecard(p)

if __name__=="__main__":
    unittest.main()

