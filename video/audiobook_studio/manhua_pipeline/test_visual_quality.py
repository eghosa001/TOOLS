"""Offline source-to-image QA tests: no GPUs, no private novels and no remote APIs."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from video.audiobook_studio.manhua_pipeline.assemble_existing import _verify_visual_evidence

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
            args = SimpleNamespace(visual_qa_report=str(report), require_visual_qa=True)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                _verify_visual_evidence(args, [(panel, 5.0)], None)

    def test_fast_cpu_strict_mode_only_accepts_source_bound_pixel_triage(self):
        from video.audiobook_studio.episode_fastlane import sha256
        with tempfile.TemporaryDirectory() as td:
            panel = Path(td) / "panel.png"
            panel.write_bytes(b"illustration fixture, no actual pictures distributed")
            report = Path(td) / "quality.json"
            payload = {
                "scenes": [{"image_sha256": sha256(panel), "source_sha256": "actual-source",
                            "status":"AUTOMATED_TRIAGE_PASS"}],
                "thumbnail": {}, "gate": {"automated_visual_triage_passed": True,
                                          "needs_correction": False}}
            report.write_text(json.dumps(payload))
            args = SimpleNamespace(visual_qa_report=str(report), require_visual_qa=True)
            result = _verify_visual_evidence(args, [(panel, 5.0)], None)
            self.assertTrue(result["source_to_image_verified"])
            self.assertFalse(result["human_visual_review_approved"])
            payload["gate"]["needs_correction"] = True
            report.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "unmatched, uncertain"):
                _verify_visual_evidence(args, [(panel, 5.0)], None)

    def test_incomplete_review_is_error(self):
        with self.assertRaises(ValueError):
            episode_gate(scene_reviews=[], thumbnail_review={"status":"AUTOMATED_TRIAGE_PASS"},
                         scenes_expected=1)


if __name__ == "__main__":
    unittest.main()
