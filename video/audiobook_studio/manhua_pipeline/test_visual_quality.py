"""Offline source-to-image QA tests: no GPUs, no private novels and no remote APIs."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from video.audiobook_studio.manhua_pipeline.assemble_existing import (_verify_visual_evidence, _verify_narration_audible, _scenes)

from video.audiobook_studio.manhua_pipeline.core import scene_plan, split_chunks
from video.audiobook_studio.manhua_pipeline.visual_quality import (
    requirements_for, source_grounded_prompt, episode_gate, thumbnail_contract,
)


SMOKE = "The young cultivator opened his eyes as spiritual light gathered around him."


class NarrationVisualAlignmentTests(unittest.TestCase):
    def test_spiritual_awakened_actions_cannot_be_lost(self):
        ids = {r["id"] for r in requirements_for(SMOKE)}
        self.assertIn("eyes_open", ids)
        self.assertIn("spiritual_aura", ids)
        self.assertIn("single_protagonist", ids)
        self.assertIn("narrated_beat", ids)

    def test_source_rules_override_vague_or_inaccurate_brief(self):
        prompt, rules = source_grounded_prompt(
            passage=SMOKE, style="Chinese 2D manhua",
            brief="A relaxed young man sitting quietly without magic")
        self.assertIn("EYES ARE OPEN", prompt)
        self.assertIn("VISIBLE luminous spiritual energy LIGHT", prompt)
        self.assertIn("ONE protagonist", prompt)
        self.assertIn("Exact current narration:", prompt)
        self.assertTrue(any(r["id"] == "spiritual_aura" for r in rules))

    def test_scene_plan_requires_image_inspection_not_brief(self):
        scenes = scene_plan(split_chunks(SMOKE), style="cultivation",
                            characters=[{"id":"young-cultivator",
                                         "visual_description":"blue robes, long dark hair"}],
                            briefs=["Meditation room"])
        self.assertEqual(len(scenes), 1)
        self.assertTrue(scenes[0]["needs_editorial_visual_review"])
        self.assertIn("spiritual energy LIGHT", scenes[0]["prompt"])
        self.assertIn("EYES ARE OPEN", scenes[0]["prompt"])
        self.assertTrue(scenes[0]["source_sha256"])
        self.assertTrue(scenes[0]["key"])

    def test_source_change_invalidates_image_cache(self):
        a = scene_plan(split_chunks(SMOKE), style="cultivation")
        b = scene_plan(split_chunks(
            "The young cultivator closed his eyes and extinguished the spiritual light."),
            style="cultivation")
        self.assertNotEqual(a[0]["key"], b[0]["key"])

    def test_generic_passage_still_requires_image_grounding(self):
        rules = requirements_for("The old manor stood silent beyond the river.")
        self.assertEqual(rules[0]["id"], "narrated_beat")

    def test_crowded_scene_not_forced_to_one_person(self):
        rules = requirements_for("Two young cultivators opened their eyes.")
        self.assertNotIn("single_protagonist", {r["id"] for r in rules})

    def test_thumbnail_must_not_duplicate_protagonist(self):
        self.assertIn("EXACTLY ONE", thumbnail_contract()[0]["must_show"])

    def test_unverified_pixels_block_approval(self):
        scene = {"status":"VISUAL_REVIEW_PENDING"}
        thumb = {"status":"AUTOMATED_TRIAGE_PASS"}
        gate = episode_gate(scene_reviews=[scene], thumbnail_review=thumb,
                            scenes_expected=1)
        self.assertTrue(gate["needs_correction"])
        self.assertFalse(gate["ready_for_youtube"])
        self.assertFalse(gate["human_visual_review_approved"])

    def test_apparent_model_success_never_becomes_human_approval(self):
        gate = episode_gate(
            scene_reviews=[{"status":"AUTOMATED_TRIAGE_PASS"}],
            thumbnail_review={"status":"AUTOMATED_TRIAGE_PASS"},
            scenes_expected=1)
        self.assertTrue(gate["automated_visual_triage_passed"])
        self.assertFalse(gate["human_visual_review_approved"])
        self.assertFalse(gate["ready_for_youtube"])

    def test_fast_cpu_assembly_rejects_unreviewed_production(self):
        with tempfile.TemporaryDirectory() as td:
            panel = Path(td) / "panel.png"
            panel.write_bytes(b"synthetic image fixture")
            args = SimpleNamespace(visual_qa_report=None, require_visual_qa=True)
            with self.assertRaisesRegex(ValueError, "requires --visual-qa-report"):
                _verify_visual_evidence(args, [(panel, 5.0)], None)

    def test_fast_cpu_assembly_rejects_stale_image_review(self):
        with tempfile.TemporaryDirectory() as td:
            panel = Path(td) / "panel.png"
            panel.write_bytes(b"changed image fixture")
            report = Path(td) / "quality.json"
            report.write_text(json.dumps({
                "scenes": [{"image_sha256": "wronghash", "source_sha256": "source",
                            "status":"AUTOMATED_TRIAGE_PASS"}],
                "thumbnail": {}, "gate": {"automated_visual_triage_passed": True,
                                          "needs_correction": False}}))
            timeline = Path(td) / "timing.json"
            timeline.write_text(json.dumps([{"image": "panel.png", "seconds":5,
                "image_sha256": "wronghash", "source_sha256":"0"*64}]))
            args = SimpleNamespace(visual_qa_report=str(report), require_visual_qa=True,
                                   timeline=str(timeline))
            with self.assertRaisesRegex(ValueError, "reviewed timeline"):
                _verify_visual_evidence(args, [(panel, 5.0)], None)

    def test_fast_cpu_strict_mode_only_accepts_source_bound_pixel_triage(self):
        from video.audiobook_studio.episode_fastlane import sha256
        with tempfile.TemporaryDirectory() as td:
            panel = Path(td) / "panel.png"
            panel.write_bytes(b"illustration fixture, no actual pictures distributed")
            report = Path(td) / "quality.json"
            payload = {
                "scenes": [{"image_sha256": sha256(panel), "source_sha256": "actual-source",
                            "status":"AUTOMATED_TRIAGE_PASS", "technical_ok": True,
                            "image_model_verified": True,
                            "requirements": [{"id":"narrated_beat","result":"MATCH_LIKELY"}]}],
                "thumbnail": {}, "gate": {"automated_visual_triage_passed": True,
                                          "needs_correction": False}}
            report.write_text(json.dumps(payload))
            timeline = Path(td) / "timing.json"
            timeline.write_text(json.dumps([{"image":"panel.png","seconds":5.0,
                "image_sha256":sha256(panel),"source_sha256":"a"*64}]))
            payload["scenes"][0]["source_sha256"] = "a"*64
            report.write_text(json.dumps(payload))
            args = SimpleNamespace(visual_qa_report=str(report), require_visual_qa=True,
                                   timeline=str(timeline))
            result = _verify_visual_evidence(args, [(panel, 5.0)], None)
            self.assertTrue(result["source_to_image_verified"])
            self.assertFalse(result["human_visual_review_approved"])
            payload["gate"]["needs_correction"] = True
            report.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "unmatched, uncertain"):
                _verify_visual_evidence(args, [(panel, 5.0)], None)

    def test_gpu_assets_phase_never_encodes_a_video(self):
        from video.audiobook_studio.manhua_pipeline import kaggle_runner as kr
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            picture = base / "scene.png"; picture.write_bytes(b"synthetic scene bytes")
            cover = base / "cover.png"; cover.write_bytes(b"synthetic thumbnail bytes")
            audio = base / "voice.m4a"; audio.write_bytes(b"synthetic approved audio bytes")
            meta = {"style":"cultivation", "characters":[], "scene_briefs":{},
                    "episodes":[{"sha256":"source-hash"}],
                    "image_model_rights_reviewed":True}
            fake_qa = {"needs_correction":False, "automated_visual_triage_passed":True}
            with (patch.object(kr,"WORK",base),
                  patch.object(kr,"find_source",return_value=base/"input.zip"),
                  patch.object(kr,"open_package",return_value=(meta,SMOKE,{})),
                  patch.object(kr,"restore_cache",return_value=False),
                  patch.object(kr,"voice_chunks",return_value=([audio],[4.8])),
                  patch.object(kr,"master_audio",return_value=audio),
                  patch.object(kr,"illustrate",return_value=([picture],cover,{"model":"cached"})),
                  patch.object(kr,"evaluate_visuals",return_value=fake_qa),
                  patch.object(kr,"checkpoint_out",return_value=base/"MANHUA_PROGRESS.zip"),
                  patch.object(kr,"render_review",side_effect=AssertionError("GPU video encode forbidden"))):
                result=kr.process(story_id="smoke-test-001",episode=1,
                                  phase="assets",quality="fast")
            self.assertEqual(result["status"],"PRIVATE_ASSETS_READY")
            self.assertFalse(result["gpu_video_rendered"])
            manifest=json.loads((base/"PRIVATE_ASSETS_REPORT.json").read_text())
            self.assertEqual(manifest["voice_profile"],
                             "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1")
            self.assertFalse(manifest["gpu_mp4_rendered"])
            timeline=json.loads((base/"smoke-test-001"/"ep001"/
                                 "PRIVATE_SCENE_TIMELINE.json").read_text())
            self.assertEqual(len(timeline),1)
            self.assertEqual(timeline[0]["seconds"],4.8)
            self.assertTrue(timeline[0]["image_sha256"])
            self.assertEqual(list(base.glob("*.mp4")),[])

    def test_strict_gate_refuses_unverified_visual_model_claim(self):
        from video.audiobook_studio.episode_fastlane import sha256
        with tempfile.TemporaryDirectory() as td:
            panel=Path(td)/"scene.png";panel.write_bytes(b"real bytes checked by hash")
            timeline=Path(td)/"timeline.json"
            timeline.write_text(json.dumps([{"image":"scene.png","seconds":4.8,
                "image_sha256":sha256(panel),"source_sha256":"c"*64}]))
            report=Path(td)/"quality.json"
            record={
                "scenes":[{"source_sha256":"c"*64,"image_sha256":sha256(panel),
                           "status":"AUTOMATED_TRIAGE_PASS","technical_ok":True,
                           "image_model_verified":False,"requirements":[{"id":"narrated_beat"}]}],
                "thumbnail":{},"gate":{"automated_visual_triage_passed":True,
                                       "needs_correction":False}}
            report.write_text(json.dumps(record))
            args=SimpleNamespace(visual_qa_report=str(report),require_visual_qa=True,
                                 timeline=str(timeline))
            with self.assertRaisesRegex(ValueError,"unmatched, uncertain"):
                _verify_visual_evidence(args,[(panel,4.8)],None)

    def test_timeline_wrong_source_sha_blocks_strict_delivery(self):
        from video.audiobook_studio.episode_fastlane import sha256
        with tempfile.TemporaryDirectory() as td:
            panel = Path(td)/"scene.png"; panel.write_bytes(b"panel")
            manifest=Path(td)/"timeline.json"
            manifest.write_text(json.dumps([{"image":"scene.png","seconds":5,
                "source_sha256":"a"*64,"image_sha256":sha256(panel)}]))
            report=Path(td)/"qa.json"
            report.write_text(json.dumps({
                "scenes":[{"source_sha256":"b"*64,"image_sha256":sha256(panel),
                           "status":"AUTOMATED_TRIAGE_PASS"}],
                "thumbnail":{},"gate":{"automated_visual_triage_passed":True,"needs_correction":False}
            }))
            args=SimpleNamespace(visual_qa_report=str(report),require_visual_qa=True,timeline=str(manifest))
            with self.assertRaisesRegex(ValueError,"Narration source or panel differs"):
                _verify_visual_evidence(args,[(panel,5)],None)

    def test_timeline_modified_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            panel=Path(td)/"scene.png";panel.write_bytes(b"x"*1200)
            timeline=Path(td)/"timing.json"
            timeline.write_text(json.dumps([{"image":"scene.png","seconds":5.0,
                "image_sha256":"f"*64,"source_sha256":"a"*64}]))
            args=SimpleNamespace(timeline=str(timeline),image=None)
            with self.assertRaisesRegex(ValueError,"Timeline image hash"):
                _scenes(args,5.0)

    def test_actual_mp4_audio_must_be_audible(self):
        silent=SimpleNamespace(returncode=0,stderr="[Parsed_volumedetect] mean_volume: -inf dB\\n"
                                          "max_volume: -inf dB")
        with patch("video.audiobook_studio.manhua_pipeline.assemble_existing.subprocess.run",
                   return_value=silent):
            with self.assertRaisesRegex(ValueError,"no measurable narration"):
                _verify_narration_audible(Path("not-accessed.mp4"),4.8)
        audible=SimpleNamespace(returncode=0,stderr="mean_volume: -19.8 dB\\nmax_volume: -4.4 dB")
        with patch("video.audiobook_studio.manhua_pipeline.assemble_existing.subprocess.run",
                   return_value=audible):
            d=_verify_narration_audible(Path("not-accessed.mp4"),4.8)
            self.assertTrue(d["audible_audio_decoded"])
            self.assertAlmostEqual(d["mean_db"],-19.8)

    def test_incomplete_review_is_error(self):
        with self.assertRaises(ValueError):
            episode_gate(scene_reviews=[], thumbnail_review={"status":"AUTOMATED_TRIAGE_PASS"},
                         scenes_expected=1)


if __name__ == "__main__":
    unittest.main()
