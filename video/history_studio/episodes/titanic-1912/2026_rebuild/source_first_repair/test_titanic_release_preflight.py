#!/usr/bin/env python3
"""Only production-relevant negative gates: no rerender or unrelated CI."""
from __future__ import annotations
import importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("titanic_preflight",HERE/"titanic_release_preflight.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def test_without_verified_manifest_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);r=m.check(p/"missing.json",p,p/"film.mp4",p/"signoff.json")
            self.assertFalse(r["release_approved"])
            self.assertIn("MISSING",r["errors"][0])
    def test_legacy_302_unapproved_shots_cannot_pass(self):
        p=HERE.parent/"MANUAL_SCENE_LEDGER_DRAFT.json"
        old=json.loads(p.read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/"legacy.json"
            f.write_text(json.dumps({"shots":old["scenes"],"source_first_editorial_approval":"NOT_APPROVED"}))
            (root/"film.mp4").write_bytes(b"not a real film")
            (root/"signoff.json").write_text('{"approved_for_youtube_publication":true}')
            r=m.check(f,root,root/"film.mp4",root/"signoff.json")
            self.assertFalse(r["release_approved"])
            self.assertEqual(r["source_first_status"],"FAIL")
            self.assertTrue(any("editor" in x.lower() or "authentic" in x.lower() for x in r["errors"]))
    def test_no_synthetic_signoff_can_overwrite_real_digest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"missing.json").write_text("{}")
            r=m.check(p/"missing.json",p,p/"film.mp4",p/"signoff.json")
            self.assertFalse(r["release_approved"])
    def test_manifest_digest_mismatch_prevents_release_even_with_video_signoff(self):
        # Isolate the binding check by mocking policy approval, not by
        # manufacturing fake source licences or claiming editorial acceptance.
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            manifest=root/"reviewed_sources.json"
            manifest.write_text(json.dumps({"shots":[{"id":f"s{i}"} for i in range(302)],
                "min_authentic_shot_share":.6}))
            film=root/"film.mp4"
            film.write_bytes(b"synthetic-test-only")
            record={
                "reviewer_name":"Test Reviewer",
                "reviewed_mp4_sha256":m.sha(film),
                "approved_source_manifest_sha256":"0"*64,
                "actual_86_minute_full_playback_with_sound":True,
                "all_302_narration_to_visual_matches_inspected":True,
                "rights_and_attributions_individually_approved":True,
                "spoken_final_subscribe_audited":True,
                "onscreen_final_subscribe_audited":True,
                "caption_audio_alignment_audited":True,
                "audio_music_and_narrator_quality_audited":True,
                "black_frames_focus_and_lighting_audited":True,
                "reconstruction_labels_inspected":True,
                "approved_for_youtube_publication":True
            }
            signoff=root/"signoff.json"
            signoff.write_text(json.dumps(record))
            class ApprovedPolicy:
                @staticmethod
                def validate(*args,**kwargs):
                    return {"status":"PASS","authentic_fraction":.7,"errors":[]}
            with patch.object(m,"getpolicy",return_value=ApprovedPolicy):
                r=m.check(manifest,root,film,signoff)
                self.assertFalse(r["release_approved"])
                self.assertEqual(r["source_first_status"],"PASS")
                self.assertTrue(any("MANIFEST SHA mismatch" in x for x in r["errors"]))
                # Only a matching manifest digest can satisfy this binding;
                # actual media inspection is a separate, mandatory requirement.
                record["approved_source_manifest_sha256"]=m.sha(manifest)
                signoff.write_text(json.dumps(record))
                r=m.check(manifest,root,film,signoff)
                self.assertNotIn("SIGNOFF MANIFEST SHA mismatch",r["errors"])
if __name__=="__main__":unittest.main()
