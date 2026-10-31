#!/usr/bin/env python3
"""ASMR semantic-parity regression: prevents repeating the three fake fig chops."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"production"))
from material_audio_parity_gate import check_manifest

BASE={
 "fps":24,"reference_clip_used_as_source":False,
 "visual":{"medium":"LIVE_ACTION_STOCK","requested_medium":"LIVE_ACTION_STOCK","licensed_source":"Pexels/35213988","contact_frame_range":[0,130],"complete_cut_count":1,"force":"gentle","texture_family":"soft_fruit"},
 "foley":{"licensed_source":"Freesound/812387 CC0","recorded_foley":True,"contact_frame_range":[0,130],"complete_cut_count":1,"force":"gentle","texture_family":"soft_fruit"},
 "visual_action_structure":"continuous_slice","foley_action_structure":"continuous_slice","visual_transients":[],"audible_transients":[],
 "human_or_av_capable_review":{"status":"PENDING"}
}
class TestParity(unittest.TestCase):
 def test_true_continuous_cut_structurally_matches(self):
  r=check_manifest(BASE);self.assertTrue(r["passed_structural_checks"]);self.assertFalse(r["release_approved"])
 def test_previous_three_impact_mistake_blocked(self):
  d=copy.deepcopy(BASE);d["foley"]["complete_cut_count"]=3;d["foley"]["force"]="hard"
  r=check_manifest(d);self.assertFalse(r["passed_structural_checks"])
 def test_fake_3d_claim_blocked(self):
  d=copy.deepcopy(BASE);d["visual"]["requested_medium"]="CGI_3D"
  self.assertFalse(check_manifest(d)["passed_structural_checks"])
 def test_source_reference_reuse_blocked(self):
  d=copy.deepcopy(BASE);d["reference_clip_used_as_source"]=True
  self.assertFalse(check_manifest(d)["passed_structural_checks"])
 def test_incorrect_foley_material_blocked(self):
  d=copy.deepcopy(BASE);d["foley"]["texture_family"]="hard_crisp_apple"
  self.assertFalse(check_manifest(d)["passed_structural_checks"])
 def test_frame_mismatch_blocked(self):
  d=copy.deepcopy(BASE);d["foley"]["contact_frame_range"]=[5,130]
  self.assertFalse(check_manifest(d)["passed_structural_checks"])
 def test_technical_pass_not_human_approval(self):
  self.assertFalse(check_manifest(BASE,for_release=True)["release_approved"])
if __name__=="__main__":unittest.main()
