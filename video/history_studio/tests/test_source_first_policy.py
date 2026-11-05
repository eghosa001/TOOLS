#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE=Path(__file__).resolve().parents[1]/"source_first_policy.py"
spec=importlib.util.spec_from_file_location("source_first_policy",MODULE)
source=importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)

def valid_photo():
    return {
      "id":"C01-S01",
      "spoken_text":"The actual Grand Gallery descends deep into the pyramid.",
      "start_seconds":0,"end_seconds":10,
      "shot_subject":"Actual Grand Gallery",
      "why_this_visual":"The selected genuine photo depicts the exact narrated interior.",
      "visual_relevance":{"match_type":"EXACT_OBJECT","depicts_specific_spoken_claim":True,
         "generic_visual_proxy":False,"independently_viewed":True,
         "specific_thing_visible":"the original physical Grand Gallery of the Great Pyramid",
         "why_claim_matches_picture":"The photographed place is the actual narrated Grand Gallery rather than an unrelated structure."},
      "visual_kind":"AUTHENTIC_PHOTO","editor_approved_by":"Documentary editor",
      "editorial_status":"APPROVED",
      "authentic_source_searches":[
        {"query":"Grand Gallery licensed photo","source_url":"https://commons.wikimedia.org/wiki/File:Example.jpg",
         "outcome":"Photo selected after viewing its source page"}
      ],
      "asset":{
        "source_page_url":"https://commons.wikimedia.org/wiki/File:Example.jpg",
        "creator":"Example Photographer","license":"CC BY-SA 4.0",
        "license_url":"https://creativecommons.org/licenses/by-sa/4.0/",
        "file_identity":"File:Example.jpg",
        "attribution":"Example Photographer / Grand Gallery / CC BY-SA 4.0",
        "commercial_use_confirmed":True,"modifications_allowed":True,
        "origin_type":"CAMERA_PHOTO","non_synthetic_verified":True,
        "authentic_capture_verified":True,
        "share_alike_compliance":"Editor to apply CC BY-SA 4.0 to derivative material as required."
      }
    }

def result(shot, **kwargs):
    item={"shots":[shot],"min_authentic_shot_share":0.6,
          "source_first_editorial_approval":"APPROVED"}
    item.update(kwargs)
    return source.validate(item)

class RealImageFirstTests(unittest.TestCase):
    def test_valid_licensed_real_photo_passes(self):
        self.assertEqual(result(valid_photo())["status"],"PASS")
    def test_rejects_missing_licence(self):
        a=valid_photo();a["asset"].pop("license")
        self.assertEqual(result(a)["status"],"FAIL")
    def test_rejects_noncommercial(self):
        a=valid_photo();a["asset"]["license"]="CC BY-NC 4.0"
        self.assertEqual(result(a)["status"],"FAIL")
    def test_rejects_no_derivatives(self):
        a=valid_photo();a["asset"]["license"]="CC BY-ND 4.0"
        self.assertEqual(result(a)["status"],"FAIL")
    def test_rejects_sharealike_without_compliance(self):
        a=valid_photo();a["asset"].pop("share_alike_compliance")
        self.assertEqual(result(a)["status"],"FAIL")
    def test_rejects_mere_official_webpage_without_rights(self):
        a=valid_photo()
        a["asset"]["source_page_url"]="https://egymonuments.gov.eg/monuments/the-great-pyramid/"
        a["asset"]["license"]="All rights reserved"
        self.assertEqual(result(a)["status"],"FAIL")
    def test_rejects_diagram_without_search_and_exception(self):
        a=valid_photo()
        a["visual_kind"]="DOCUMENTARY_DIAGRAM"
        a.pop("asset")
        self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"FAIL")
    def test_diagram_is_not_an_approved_source(self):
        a=valid_photo();a["visual_kind"]="DOCUMENTARY_DIAGRAM"
        self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"FAIL")
    def test_ai_image_is_never_accepted_even_with_research_or_disclosure(self):
        a=valid_photo();a["visual_kind"]="AI_ART"
        a["individual_exception_approved"]=True
        a["on_screen_disclosure"]="AI-GENERATED ARTISTIC RECONSTRUCTION"
        self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"FAIL")
    def test_ai_video_and_cgi_never_accepted(self):
        for kind in ("AI_VIDEO","ORIGINAL_RECONSTRUCTION_FILM","CGI","RENDERED_ANIMATION"):
            with self.subTest(kind=kind):
                a=valid_photo();a["visual_kind"]=kind
                self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"FAIL")
    def test_real_origin_must_be_verified(self):
        a=valid_photo();a["asset"]["non_synthetic_verified"]=False
        self.assertEqual(result(a)["status"],"FAIL")
        a=valid_photo();a["asset"]["origin_type"]="SYNTHETIC_3D"
        self.assertEqual(result(a)["status"],"FAIL")
    def test_unrelated_modern_stock_rejected_even_if_licensed_and_labelled(self):
        a=valid_photo()
        a["spoken_text"]="An X-ray microtomography scan revealed the papyrus layers."
        a["shot_subject"]="A radiologist scans a human patient with a CT machine"
        a["on_screen_context_label"]="MODERN MEDICAL CT / ILLUSTRATIVE"
        a["visual_relevance"]={
          "match_type":"EXPLICITLY_RELEVANT_CONTEXT",
          "depicts_specific_spoken_claim":False,
          "generic_visual_proxy":True,
          "independently_viewed":True,
          "specific_thing_visible":"hospital medical scanner",
          "why_claim_matches_picture":"Medical CT is not the scroll imaging beamline and does not show the scientific result."
        }
        check=result(a)
        self.assertEqual(check["status"],"FAIL")
        self.assertTrue(any("generic proxy footage" in x for x in check["errors"]))

    def test_generic_keyboard_is_not_virtual_unwrapping(self):
        a=valid_photo()
        a["spoken_text"]="The algorithm virtually unwraps the ancient scroll."
        a["shot_subject"]="Unrelated person typing on a keyboard"
        a["on_screen_context_label"]="MODERN COMPUTER / ILLUSTRATIVE"
        a["visual_relevance"].update({
          "match_type":"EXPLICITLY_RELEVANT_CONTEXT",
          "specific_thing_visible":"a computer",
          "depicts_specific_spoken_claim":False,
          "generic_visual_proxy":True
        })
        self.assertEqual(result(a)["status"],"FAIL")

    def test_wrong_instrument_rejected(self):
        a=valid_photo()
        a["visual_relevance"].update({
          "match_type":"ACTUAL_INSTRUMENT",
          "specific_thing_visible":"an unrelated microscope",
          "equipment_used_in_narrated_process":False
        })
        self.assertEqual(result(a)["status"],"FAIL")

    def test_missing_relevance_gate_fails_even_with_good_license(self):
        a=valid_photo()
        a.pop("visual_relevance")
        self.assertEqual(result(a)["status"],"FAIL")

    def test_real_current_location_context_with_true_label_passes(self):
        a=valid_photo()
        a["spoken_text"]="Mount Vesuvius stands above the buried Roman cities."
        a["shot_subject"]="Present-day Mount Vesuvius"
        a["on_screen_context_label"]="MOUNT VESUVIUS TODAY"
        a["visual_relevance"].update({
          "match_type":"ACTUAL_SITE",
          "specific_thing_visible":"Mount Vesuvius itself",
          "why_claim_matches_picture":"The photographed mountain is the original geographical location named in the actual spoken narration."
        })
        self.assertEqual(result(a)["status"],"PASS")

    def test_paid_licensed_source_requires_permission_evidence(self):
        a=valid_photo()
        a["asset"].update({"license":"COMMERCIAL LICENSE",
                           "license_url":"https://example.org/licensing",
                           "rights_holder":"Licensor","license_evidence_ref":"contract-01"})
        self.assertEqual(result(a)["status"],"PASS")
        a["asset"].pop("license_evidence_ref")
        self.assertEqual(result(a)["status"],"FAIL")
    def test_release_requires_file_hash(self):
        a=valid_photo()
        self.assertEqual(source.validate({"shots":[a],"min_authentic_shot_share":0,
            "source_first_editorial_approval":"APPROVED"},phase="release")["status"],"FAIL")
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"photo.jpg";target.write_bytes(b"real source picture")
            a["asset"]["local_path"]="photo.jpg"
            a["asset"]["sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
            data={"shots":[a],"source_first_editorial_approval":"APPROVED"}
            self.assertEqual(source.validate(data,phase="release",root=Path(d))["status"],"PASS")
            a["asset"]["sha256"]="f"*64
            self.assertEqual(source.validate(data,phase="release",root=Path(d))["status"],"FAIL")
    def test_no_generic_illustrations_to_reach_real_shot_ratio(self):
        good=valid_photo()
        other=copy.deepcopy(good);other["id"]="C01-S02"
        other["visual_kind"]="DOCUMENTARY_DIAGRAM";other.pop("asset")
        item={"shots":[good,other],"source_first_editorial_approval":"APPROVED"}
        r=source.validate(item)
        self.assertEqual(r["status"],"FAIL")
        self.assertTrue(any("prohibited visual_kind" in e for e in r["errors"]))
    def test_legacy_unreviewed_storyboard_fails(self):
        a={"id":"C01-S01","paragraph":1,"sentence_start":1,"sentence_end":2,
           "visual_type":"evidence","photo_id":None,"editorial_status":"DIRECTOR_ASSIGNED"}
        self.assertEqual(result(a)["status"],"FAIL")

if __name__=="__main__":
    unittest.main()
