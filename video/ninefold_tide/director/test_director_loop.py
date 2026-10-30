"""Unit tests: no hallucinated approvals, canon changes or unsafe scene substitutions."""
import copy
import json
import unittest
from pathlib import Path

import director_loop as director

class DirectorLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=director.read(director.CANON)
        cls.shots=director.read(director.SHOTS)
        cls.assets=director.read(director.ASSETS)

    def test_all_twelve_canon_shots_have_valid_structure(self):
        report=director.plan(self.config,self.shots,self.assets)
        self.assertEqual(report["errors"],[])
        self.assertEqual(len(report["shots"]),12)
        self.assertFalse(report["publication_authorized"])
        self.assertFalse(report["artistic_review_completed"])
        self.assertTrue(all(not s["ready_for_release"] and s["human_review_required"] for s in report["shots"]))
        self.assertTrue(all(s["technique"]["character_performance"]=="hand_drawn_2d_priority" for s in report["shots"]))

    def test_no_change_to_original_dialogue_or_shots(self):
        before=json.dumps(self.shots,sort_keys=True)
        director.plan(self.config,self.shots,self.assets)
        self.assertEqual(json.dumps(self.shots,sort_keys=True),before)

    def test_rope_physics_specific_canon(self):
        report=director.plan(self.config,self.shots,self.assets)
        by_id={shot["id"]:shot for shot in report["shots"]}
        self.assertIn("MISSES bow ring",by_id["ep101_006"]["canonical_physics"])
        self.assertIn("MESSENGER",by_id["ep101_012"]["canonical_physics"])
        self.assertIn("stanchion",by_id["ep101_008"]["canonical_physics"])
        self.assertIn("left",by_id["ep101_010"]["canonical_physics"].lower())

    def test_structural_timeline_deviation_is_rejected(self):
        changed=copy.deepcopy(self.shots)
        changed["shots"][1]["start_frame"]=changed["shots"][1]["start_frame"]+1
        self.assertTrue(any("gap" in issue for issue in director.validate(self.config,changed,self.assets)))

    def test_nonapproved_reference_assets_stay_nonapproved(self):
        result=director.plan(self.config,self.shots,self.assets)
        self.assertTrue(result["shots"][0]["unapproved_assets"])
        self.assertTrue(all(not x["ready_for_release"] for x in result["shots"]))

    def test_blender_issues_produce_evidence_based_actions_not_approvals(self):
        evidence={"shots":{"ep101_006":{"scene":{"has_camera":False,"fps":30,
          "missing_external_files":[{"image":"bad","filepath":"missing.png"}],"animated_object_count":0},
          "frames":{"frame_count":48,"near_black_samples":2,
          "constant_sampled_sequence":True}}}}
        result=director.plan(self.config,self.shots,self.assets,evidence)
        shot=result["shots"][5]
        codes={x["code"] for x in shot["issues"]}
        self.assertTrue({"missing-camera","fps","unresolved-media","near-black","constant-frames"}.issubset(codes))
        self.assertFalse(shot["ready_for_release"])
        self.assertFalse(result["publication_authorized"])
        self.assertTrue(result["technical_issue_count"]>=5)

    def test_no_observation_does_not_prove_quality(self):
        result=director.plan(self.config,self.shots,self.assets)
        self.assertEqual(result["technical_issue_count"],0)
        self.assertEqual(result["shots"][5]["scene_evidence"],"not_provided")
        self.assertFalse(result["artistic_review_completed"])

    def test_immutable_timeline_digest_catches_changes(self):
        changed=copy.deepcopy(self.shots)
        changed["shots"][0]["dialogue"]="Invented substitute"
        before=director.plan(self.config,self.shots,self.assets)["immutable_timeline_sha256"]
        after=director.plan(self.config,changed,self.assets)["immutable_timeline_sha256"]
        self.assertNotEqual(before,after)

if __name__=="__main__":
    unittest.main()
