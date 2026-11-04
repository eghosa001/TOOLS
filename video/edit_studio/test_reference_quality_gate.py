#!/usr/bin/env python3
"""Fail-closed regression tests for v2 reference-led edit production."""
import copy
import unittest

from reference_quality_gate import ReferenceQualityError, SCORES, validate_reference_profile


def sample():
    return {
        "schema_version": 2,
        "timeline": [
            {"source_id": "a", "start_sec": 0, "end_sec": 3},
            {"source_id": "a", "start_sec": 3, "end_sec": 6},
            {"source_id": "a", "start_sec": 6, "end_sec": 9},
        ],
        "output": {"sha256": "c" * 64},
        "reference_profile": {
            "no_ai_generated_assets": True,
            "output_format": "short_vertical",
            "editorial_premise": "Show how a small choice changes the outcome.",
            "opening_hook": "Begin with an unanswered character dilemma and reaction.",
            "turning_point": "Reveal a hidden motive through a matching action.",
            "final_payoff": "Complete the consequence without hiding the real reaction.",
            "emotional_or_comedic_intent": "Move the viewer from curiosity into surprise.",
            "style_difference_from_references": "Use our own critical interpretation and source selection.",
            "reference_evidence": [
                {
                    "creator": "FicTic Editz",
                    "url": "https://www.dailymotion.com/video/x9qcvs2",
                    "source_title": "Already Broken Thomas Shelby Edit",
                    "inspection_level": "description_or_transcript",
                    "specific_observation": "The published transcript documents several brief lines of dialogue before the resolution.",
                    "checked_on": "2026-11-04",
                },
                {
                    "creator": "Eagle Stan",
                    "url": "https://www.youtube.com/@Eagle_Stan16",
                    "source_title": "Eagle Stan channel reference",
                    "inspection_level": "metadata_only",
                    "specific_observation": "Published titles cover character moments humor comparisons and other deliberately chosen subjects.",
                    "checked_on": "2026-11-04",
                },
            ],
            "beat_map": [
                {"at_sec": 0.0, "type": "hook",
                 "viewer_reason": "Invite the viewer into an immediate question.",
                 "sound_and_picture": "Keep the face visible with clear dialogue."},
                {"at_sec": 3.0, "type": "reveal",
                 "viewer_reason": "Expose the decisive piece of new information.",
                 "sound_and_picture": "Align the reaction to the incoming music."},
                {"at_sec": 7.0, "type": "payoff",
                 "viewer_reason": "Finish the action and resulting emotional reaction.",
                 "sound_and_picture": "Reduce music and hold the critical shot."},
            ],
            "shot_craft": [
                {"shot_index": i, "transition": "straight_cut",
                 "subject_and_eye_trace": "Keep the subject face positioned consistently",
                 "visible_action": "Preserve the entire meaningful on screen motion",
                 "cut_motivation": "Cut when character intention becomes clear",
                 "motion_continuity": "Avoid reversing screen direction unnecessarily",
                 "audio_layer_plan": "Prioritize the dialogue over background music",
                 "on_screen_text_plan": "Use restrained captions away from controls",
                 "scene_payoff_protected": True}
                for i in (1, 2, 3)
            ],
            "sound_design": {
                "dialogue_priority": "Keep every important spoken word clear above music.",
                "music_entry_and_exit": "Introduce the pulse after the spoken setup resolves.",
                "impact_and_foley": "Use licensed physical sound only when the image supports it.",
                "anti_clipping_and_silence": "Monitor peaks, transitions and unwanted silent audio gaps.",
            },
            "human_reference_comparison": {
                "watched_entire_export": True,
                "listened_to_entire_export": True,
                "side_by_side_reference_compared": True,
                "small_screen_safe_areas_checked": True,
                "no_black_flashes_or_audio_clicks": True,
                "no_ai_assets_verified": True,
                "reviewer": "Editorial human",
                "reviewed_on": "2026-11-04",
                "reviewed_output_sha256": "c" * 64,
                "scores": {x: 9 for x in SCORES},
                "comparison_notes": "Compared the opening timing, dialogue separation, motion continuity and payoff against the chosen video reference.",
            },
        },
    }


class ReferenceQualityTests(unittest.TestCase):
    def test_metadata_evidence_valid_for_plan_not_release(self):
        m = sample()
        self.assertEqual(validate_reference_profile(m)["reference_gate"], "passed")
        with self.assertRaisesRegex(ReferenceQualityError, "actually viewed"):
            validate_reference_profile(m, "release")

    def test_can_release_only_after_documented_actual_review(self):
        m = sample()
        first = m["reference_profile"]["reference_evidence"][0]
        first["inspection_level"] = "frames_and_audio_reviewed"
        first["timestamp_samples"] = [
            {"time_sec": t, "on_screen_and_sound": "Observed a real face and audible source dialogue change here."}
            for t in (0, 4, 7)
        ]
        self.assertTrue(validate_reference_profile(m, "release")["scored_from_real_export"])
        m["reference_profile"]["human_reference_comparison"]["scores"]["rhythm"] = 8.4
        with self.assertRaisesRegex(ReferenceQualityError, "rhythm"):
            validate_reference_profile(m, "release")

    def test_no_generated_parts(self):
        m = sample()
        m["reference_profile"]["no_ai_generated_assets"] = False
        with self.assertRaisesRegex(ReferenceQualityError, "No AI-generated"):
            validate_reference_profile(m)

    def test_unnatural_placeholder_shot_blocked(self):
        m = sample()
        m["reference_profile"]["shot_craft"][0]["cut_motivation"] = "cool"
        with self.assertRaisesRegex(ReferenceQualityError, "cut_motivation"):
            validate_reference_profile(m)

    def test_fake_frame_claim_requires_timestamped_audio_video_notes(self):
        m = sample()
        m["reference_profile"]["reference_evidence"][0]["inspection_level"] = "frames_and_audio_reviewed"
        with self.assertRaisesRegex(ReferenceQualityError, "timestamp"):
            validate_reference_profile(m)

    def test_hook_cannot_be_delayed(self):
        m = sample()
        m["reference_profile"]["beat_map"][0]["at_sec"] = 2.5
        with self.assertRaisesRegex(ReferenceQualityError, "1.5"):
            validate_reference_profile(m)

    def test_unobserved_reference_cannot_claim_visual_review(self):
        m = sample()
        m["reference_profile"]["reference_evidence"][1]["specific_observation"] = "very good"
        with self.assertRaises(ReferenceQualityError):
            validate_reference_profile(m)

    def test_legacy_v1_is_explicitly_not_reference_certified(self):
        r = validate_reference_profile({"schema_version": 1}, "release")
        self.assertEqual(r["reference_gate"], "legacy_v1_no_reference_profile")


if __name__ == "__main__":
    unittest.main()
