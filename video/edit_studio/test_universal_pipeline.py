#!/usr/bin/env python3
"""Regression tests: ANY media genre; six scores; actual FFmpeg output; no auto-publish."""
import hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import new_edit,quality_gate,release_gate,render_edit

class UniversalPipelineTests(unittest.TestCase):
    def test_every_category_uses_same_manifest(self):
        for category in new_edit.CATEGORIES:
            m=new_edit.template("One original scene with a surprising outcome",category,"narrative")
            self.assertEqual(m["pipeline"],"universal_edit")
            self.assertEqual(m["category"],category)
            self.assertIs(m["editorial_review"]["approved"],False)
            self.assertFalse(m["originality"]["uses_voice"])

    def test_music_only_and_comedy_not_forced_to_use_football_rules(self):
        for category,style in [("anime","character_study"),("movie","music_sync"),("gaming","comedy"),("sports","narrative"),("other","tutorial")]:
            m=new_edit.template("A real moment transformed by the original editor",category,style)
            self.assertEqual(m["style"],style)
            self.assertNotIn("football_specific",m)
            self.assertNotIn("mandatory_voice",m)

    def test_quality_gate_rejects_without_human_evidence(self):
        self.assertEqual(quality_gate.evaluate({},"none.mp4","release")["status"],"HOLD")
        card={"scores":{k:9 for k in quality_gate.WEIGHTS},
            "evidence":{k:"Specific observation from inspecting the entire original clip and final edit." for k in quality_gate.WEIGHTS}}
        self.assertEqual(quality_gate.evaluate(card,None,"draft")["status"],"DRAFT_SCORED")
        self.assertEqual(quality_gate.evaluate(card,None,"release")["status"],"HOLD")

    def test_quality_gate_all_genres_same_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"review.mp4";path.write_bytes(b"unit-test-placeholder-not-a-video")
            card={"scores":{k:9.0 for k in quality_gate.WEIGHTS},
                  "evidence":{k:"I reviewed the exact corresponding footage, sound and editorial effect in the completed sequence." for k in quality_gate.WEIGHTS},
                  "reviewer":"Human Editor","reviewed_on":"2026-11-04",
                  "complete_export_watched_with_audio":True,
                  "every_used_source_verified":True,
                  "spoken_names_checked_or_not_applicable":True,"sound_licences_checked":True,
                  "reviewed_video_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
            self.assertEqual(quality_gate.evaluate(card,path,"release")["status"],"PASS")
            card["scores"]["viewer_engagement"]=5.0
            self.assertEqual(quality_gate.evaluate(card,path,"release")["status"],"HOLD")
            card["scores"]["viewer_engagement"]=9.0
            path.write_bytes(b"changed")
            self.assertEqual(quality_gate.evaluate(card,path,"release")["status"],"HOLD")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"Requires FFmpeg on runner")
    def test_actual_nonfootball_timeline_render(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);(base/"clips").mkdir()
            source=base/"clips/source.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","lavfi",
                 "-i","testsrc2=size=320x180:rate=15","-f","lavfi",
                 "-i","sine=frequency=440:sample_rate=48000","-t","6.2",
                 "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p","-c:a","aac",
                 str(source)],check=True,timeout=75)
            m=new_edit.template("A gaming scene recut as an original mini story","gaming","narrative","square")
            m["media_sources"]=[{
                "id":"source","creator":"Original synthetic fixture owned by this CI test, not a user media asset",
                "source_page":"https://example.com/ci-testing","rights_evidence":"https://example.com/ci-testing/license",
                "rights_status":"cc0","commercial_use":True,"derivatives_allowed":True,
                "reviewed_on":"2026-11-04","sha256":release_gate.hash_file(source),"file":"clips/source.mp4"}]
            m["timeline"]=[]
            for i in range(2):
                m["timeline"].append({
                    "source_id":"source","start_sec":i*3,"end_sec":(i+1)*3,
                    "editorial_reason":"This deliberately paced clip advances the original two-part example sequence.",
                    "complete_moment":{"visually_reviewed":True,"beginning_included":True,
                      "payoff_included":True,"evidence_note":"The whole synthetic test action is present before and after this scene."}})
            m["originality"].update({
                "creative_thesis":"This unit test uses two original parts to make a single useful editing story.",
                "source_to_story_map":[
                    "The opening introduces the moving test scene as its own editorial choice.",
                    "The ending brings the exact same real test footage to a complete payoff."],
                "contribution_modes":["original_narrative_structure"]
            })
            m["attribution"]="CI-generated non-production test clip; no user media or rights claims."
            # This test exercises NEW schema v2 on a real FFmpeg draft render.
            from test_reference_quality_gate import sample as reference_sample
            m["reference_profile"] = reference_sample()["reference_profile"]
            m["reference_profile"]["output_format"] = "square"
            m["reference_profile"]["shot_craft"] = m["reference_profile"]["shot_craft"][:2]
            m["reference_profile"]["beat_map"][-1]["at_sec"] = 5.2

            # Two separate cleared synthetic CI audio tracks exercise voice+music,
            # neither a forced narrator nor any real/copyrighted user media.
            m["audio_sources"]=[]
            for aid,frequency in [("music",220),("voice",660)]:
                audiopath=base/"clips"/(aid+".wav")
                subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                   "-f","lavfi","-i",f"sine=frequency={frequency}:sample_rate=48000",
                   "-t","6.2",str(audiopath)],check=True,timeout=30)
                m["audio_sources"].append({
                   "id":aid,"creator":"CI generated, editor-owned audio test fixture",
                   "source_page":"https://example.com/ci-audio",
                   "rights_evidence":"https://example.com/ci-audio/license",
                   "rights_status":"cc0","commercial_use":True,"derivatives_allowed":True,
                   "reviewed_on":"2026-11-04","sha256":release_gate.hash_file(audiopath),
                   "file":"clips/"+aid+".wav"})
            m["originality"]["uses_voice"]=True
            m["originality"]["voice_source_id"]="voice"
            m["render"]["bed_audio_source_id"]="music"
            m["render"]["voice_audio_source_id"]="voice"
            m["render"]["source_audio_gain"]=0.18
            m["render"]["duck_bed_under_source"]=True  # exercise real dialogue-priority mix
            self.assertEqual(release_gate.validate_plan(m)["category"],"gaming")
            out=base/"candidate/output.mp4"
            report=render_edit.render(m,base,out)
            self.assertTrue(out.exists());self.assertGreater(out.stat().st_size,100000)
            self.assertEqual(report["status"],"UNPUBLISHED_EDITORIAL_PREVIEW_NOT_CLEARED_FOR_RELEASE")
            meta=release_gate.probe(out)
            self.assertTrue(any(x["codec_type"]=="video" and x["width"]==1080 and x["height"]==1080 for x in meta["streams"]))
            self.assertTrue(any(x["codec_type"]=="audio" for x in meta["streams"]))
            self.assertGreater(float(meta["format"]["duration"]),5.2)
            self.assertEqual(m["editorial_review"]["approved"],False)

if __name__=="__main__":
    unittest.main()
