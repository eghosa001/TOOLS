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
    def test_diagram_exception_can_pass_when_complete_and_intentional(self):
        a=valid_photo();a["visual_kind"]="DOCUMENTARY_DIAGRAM";a.pop("asset")
        a["authentic_source_searches"].append(
            {"query":"ScanPyramids void photograph",
             "source_url":"https://commons.wikimedia.org/wiki/Category:Great_Pyramid_of_Giza",
             "outcome":"None shows inaccessible measured void"})
        a["why_authentic_image_inadequate"]=(
            "The Big Void has not been physically entered; no real photograph of its interior exists.")
        a["individual_exception_approved"]=True
        a["research_source"]="https://doi.org/10.1038/nature24647"
        a["on_screen_disclosure"]="SCIENTIFIC SCHEMATIC • NOT A PHOTOGRAPH"
        self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"PASS")
    def test_ai_image_requires_explicit_disclosure(self):
        a=valid_photo();a["visual_kind"]="AI_ART";a.pop("asset")
        a["authentic_source_searches"].append(
            {"query":"Egyptian ancient worksite archive","source_url":"https://commons.wikimedia.org/wiki/Category:Ancient_Egypt",
             "outcome":"No footage of exact historical event"})
        a["why_authentic_image_inadequate"]="No real camera was present at this ancient Egyptian event."
        a["individual_exception_approved"]=True
        a["research_source"]="https://egymonuments.gov.eg/monuments/the-great-pyramid/"
        a["on_screen_disclosure"]="ARTISTIC RECONSTRUCTION"
        self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"FAIL")
        a["no_fabricated_evidence"]=True
        a["on_screen_disclosure"]="AI-GENERATED ARTISTIC RECONSTRUCTION"
        self.assertEqual(result(a,min_authentic_shot_share=0)["status"],"PASS")
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
        self.assertTrue(any("Authentic visual share" in e for e in r["errors"]))
    def test_legacy_unreviewed_storyboard_fails(self):
        a={"id":"C01-S01","paragraph":1,"sentence_start":1,"sentence_end":2,
           "visual_type":"evidence","photo_id":None,"editorial_status":"DIRECTOR_ASSIGNED"}
        self.assertEqual(result(a)["status"],"FAIL")

if __name__=="__main__":
    unittest.main()
