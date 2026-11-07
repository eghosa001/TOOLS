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




class PrivateDatasetFastPathRegressionTests(unittest.TestCase):
    """Prevent the exact ZIP-extraction, cache-loss and repeat-launch defects."""

    def _make_private_fixture(self, base):
        import zipfile
        from video.audiobook_studio.manhua_pipeline.core import create_package
        script1 = "The ancient apprentice raised one hand."
        script2 = "The blue formation dimmed behind him."
        whole = base / "approved.txt"
        first = base / "ep1.txt"
        second = base / "ep2.txt"
        whole.write_text(script1 + "\n\n" + script2)
        first.write_text(script1)
        second.write_text(script2)
        ref = base / "hero.png"
        ref.write_bytes(b"synthetic original portrait fixture")
        package = base / "MANHUA_STORY_PACKAGE.zip"
        create_package(
            story_id="offline-smoke", title="Private Synthetic Fixture",
            manuscript=whole, episodes={1:first,2:second}, output=package,
            source_approved=True, image_model_rights_reviewed=True,
            references={"hero":ref},
            characters=[{"id":"hero","visual_description":"Brown robe, black hair"}],
        )
        inputs = base / "kaggle-unpacked"
        inputs.mkdir()
        with zipfile.ZipFile(package) as z:
            z.extractall(inputs)
        return package, inputs

    def test_unpacked_kaggle_dataset_rebuilds_private_source_without_upload(self):
        import os
        from video.audiobook_studio.manhua_pipeline import kaggle_runner
        from video.audiobook_studio.manhua_pipeline.core import open_package
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            package, extracted=self._make_private_fixture(base)
            with patch.dict(os.environ, {"MANHUA_INPUT_DIR":str(extracted)}):
                with patch.object(kaggle_runner,"WORK",base/"private-output"):
                    recovered=kaggle_runner.find_source()
                    self.assertNotEqual(recovered,package)
                    meta,ep,refs=open_package(recovered,expected_story_id="offline-smoke",episode=1)
                    self.assertEqual(ep,"The ancient apprentice raised one hand.")
                    self.assertEqual(len(meta["episodes"]),2)
                    self.assertEqual(list(refs),["references/hero.png"])

    def test_kaggle_unpacked_source_tampering_is_rejected_pre_gpu(self):
        import os
        from video.audiobook_studio.manhua_pipeline import kaggle_runner
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            _, extracted=self._make_private_fixture(base)
            (extracted/"episodes"/"ep001.txt").write_text("Changed without approval")
            with patch.dict(os.environ, {"MANHUA_INPUT_DIR":str(extracted)}):
                with patch.object(kaggle_runner,"WORK",base/"private-output"):
                    with self.assertRaisesRegex(RuntimeError,"digest mismatch"):
                        kaggle_runner.find_source()

    def test_extracted_private_progress_restores_only_matching_episode(self):
        import os,zipfile
        from video.audiobook_studio.episode_fastlane import efficient_checkpoint
        from video.audiobook_studio.manhua_pipeline import kaggle_runner
        from video.audiobook_studio.manhua_pipeline.core import digest
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            source=base/"cache-content"/"narration"
            source.mkdir(parents=True)
            (source/"part-001.wav").write_bytes(b"synthetic PCM fixture"*100)
            episode_hash=digest(b"owner approved synthetic episode")
            archive=base/"MANHUA_PROGRESS.zip"
            efficient_checkpoint(source.parent,archive,source_sha256=episode_hash)
            extracted=base/"kaggle-unpacked-progress"
            extracted.mkdir()
            with zipfile.ZipFile(archive) as z:
                z.extractall(extracted)
            target=base/"restored"
            with patch.dict(os.environ,{"MANHUA_INPUT_DIR":str(extracted)}):
                with patch.object(kaggle_runner,"WORK",base/"private-output"):
                    self.assertTrue(kaggle_runner.restore_cache({"sha256":episode_hash},target))
                    self.assertEqual((target/"narration"/"part-001.wav").read_bytes(),
                                     (source/"part-001.wav").read_bytes())



class FastNarrationPrecisionTests(unittest.TestCase):
    def test_t4_uses_fp16_tensor_cores_instead_of_fp32(self):
        from video.audiobook_studio.manhua_pipeline.kaggle_runner import select_tts_precision
        self.assertEqual(select_tts_precision(cuda_major=7), "fp16")
        self.assertEqual(select_tts_precision(cuda_major=8), "bf16")
        self.assertEqual(select_tts_precision(cuda_major=6), "fp32")

    def test_conservative_rollback_and_invalid_overrides(self):
        from video.audiobook_studio.manhua_pipeline.kaggle_runner import select_tts_precision
        self.assertEqual(select_tts_precision(cuda_major=7, setting="fp32"), "fp32")
        with self.assertRaises(ValueError):
            select_tts_precision(cuda_major=7, setting="bf16")
        with self.assertRaises(ValueError):
            select_tts_precision(cuda_major=7, setting="low")

    def test_tts_runtime_instrumentation_is_present(self):
        import inspect
        from video.audiobook_studio.manhua_pipeline.kaggle_runner import voice_chunks
        source=inspect.getsource(voice_chunks)
        self.assertIn("MANHUA_RYAN_CHUNK_SECONDS", source)
        self.assertIn("MANHUA_TTS_FP16_CHUNK_FALLBACK_FP32", source)


class FastQualityRuntimeTests(unittest.TestCase):

    def test_rejected_art_is_not_cached_for_next_episode_render(self):
        from video.audiobook_studio.manhua_pipeline.kaggle_runner import discard_unverified_art_from_cache
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            panels=[root/f"shot-{i}.png" for i in range(3)]
            for panel in panels: panel.write_bytes(b"original approved-fiction artwork fixture")
            thumbnail=root/"cover.png"
            thumbnail.write_bytes(b"original thumbnail fixture")
            report={"scenes":[{"status":"AUTOMATED_TRIAGE_PASS"},
                              {"status":"NEEDS_SCENE_CORRECTION"},
                              {"status":"AUTOMATED_TRIAGE_PASS"}],
                    "thumbnail":{"status":"NEEDS_SCENE_CORRECTION"}}
            (root/"PRIVATE_VISUAL_QA_REPORT.json").write_text(json.dumps(report))
            result=discard_unverified_art_from_cache(
                root,panels,thumbnail,{"needs_correction":True})
            self.assertEqual(result["removed_scenes"],[1])
            self.assertFalse(panels[1].exists())
            self.assertTrue(panels[0].exists())
            self.assertTrue(panels[2].exists())
            self.assertFalse(thumbnail.exists())

    def test_gpu_resident_fast_path_requires_real_memory_headroom(self):
        from video.audiobook_studio.manhua_pipeline.kaggle_runner import choose_image_memory_mode
        gib = 1024**3
        self.assertEqual(choose_image_memory_mode(
            free_bytes=15*gib,total_bytes=16*gib), "GPU_RESIDENT")
        self.assertEqual(choose_image_memory_mode(
            free_bytes=13*gib,total_bytes=16*gib), "CPU_OFFLOAD")
        self.assertEqual(choose_image_memory_mode(
            free_bytes=15*gib,total_bytes=16*gib,setting="offload"), "CPU_OFFLOAD")
        self.assertEqual(choose_image_memory_mode(
            free_bytes=9*gib,total_bytes=12*gib), "CPU_OFFLOAD")
        with self.assertRaises(ValueError):
            choose_image_memory_mode(free_bytes=16*gib,total_bytes=16*gib,
                                     setting="invalid")

    def test_progress_callback_is_supported_by_tts_and_art_generation(self):
        import inspect
        from video.audiobook_studio.manhua_pipeline import kaggle_runner
        self.assertIn("checkpoint",inspect.signature(kaggle_runner.voice_chunks).parameters)
        self.assertIn("checkpoint",inspect.signature(kaggle_runner.illustrate).parameters)
        self.assertIn("checkpoint_out(meta,ep,work)",inspect.getsource(kaggle_runner.process))


if __name__ == "__main__":
    unittest.main()
