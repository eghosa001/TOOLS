#!/usr/bin/env python3
"""Tests that reused-footage shortcuts cannot bypass the policy gate."""
import copy
import importlib.util
import unittest
from pathlib import Path

file = Path(__file__).with_name("release_gate.py")
spec = importlib.util.spec_from_file_location("football_release_gate", file)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def good():
    return {
        "schema_version": 1,
        "workflow": "football_real_footage",
        "title": "Why this Ronaldo goal starts with the movement",
        "visual_policy": "REAL_FOOTAGE_ONLY",
        "footage_mode": "curated_segments",
        "sources": [{
            "id": "cr7", "source_page": "https://commons.wikimedia.org/wiki/File:Example",
            "license_evidence": "https://commons.wikimedia.org/wiki/File:Example",
            "license_url": "https://creativecommons.org/licenses/by/3.0/",
            "creator": "Real Madrid", "license": "CC BY 3.0",
            "commercial_use": True, "derivatives_allowed": True,
            "license_checked_on": "2026-11-03",
            "file": "source.mp4", "sha1": "a" * 40
        }],
        "segments": [{
            "source_id": "cr7", "start_sec": 4.0, "end_sec": 10.0,
            "kind": "goal", "pre_goal_action_verified": True,
            "ball_crossing_line_verified": True,
            "post_goal_resolution_verified": True,
            "scene_notes": "Ball is played through, shot crosses line, reaction is still visible."
        }],
        "coverage_claim": {"type": "selected_highlights"},
        "original_editorial": {
            "angle": "This video shows how off-ball movement creates a cleaner shot for an attacker.",
            "narration_origin": "original_recorded_voice",
            "narration_in_video": True,
            "visual_storytelling": ["Pause movement with arrow", "Replay attacking lane with field label"],
            "commentary": [{
                "text": "Watch the defender drift inside before the forward chooses the space behind.",
                "specific_observation": "The defender tracks toward the ball before the run begins.",
                "factual_source": "https://commons.wikimedia.org/wiki/File:Example"
            }] * 3
        },
        "music": {"origin": "original_composition", "commercial_use": True},
        "attribution_text": "Real Madrid — https://commons.wikimedia.org/wiki/File:Example CC BY 3.0: https://creativecommons.org/licenses/by/3.0/; cropped, annotated and narrated.",
        "editorial_review": {"approved": False}
    }


class FootballGateTests(unittest.TestCase):
    def test_real_plan_passes(self):
        self.assertEqual(gate.validate_plan(good())["complete_goals_recorded"], 1)

    def test_unlicensed_footage_blocks(self):
        m = good()
        m["sources"][0]["commercial_use"] = False
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_ai_visuals_block(self):
        m = good()
        m["visual_policy"] = "GENERATED_FOOTAGE"
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_arbitrary_2_point_6_second_goal_blocks(self):
        m = good()
        m["segments"][0]["end_sec"] = 6.6
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_goal_without_full_finish_blocks(self):
        m = good()
        m["segments"][0]["post_goal_resolution_verified"] = False
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_falsely_claim_all_48_goals_blocks(self):
        m = good()
        m["coverage_claim"] = {"type": "every_goal", "goal_count": 48}
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_minimal_music_only_reuse_blocks(self):
        m = good()
        m["original_editorial"]["narration_in_video"] = False
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_misleading_human_signoff_blocks(self):
        m = good()
        m["editorial_review"] = {"approved": True}
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)

    def test_no_human_signoff_release_blocks(self):
        with self.assertRaises(gate.GateError):
            gate.validate_release(good(), ".")

    def test_unabridged_mode_rejects_random_cuts(self):
        m=good()
        m["footage_mode"]="source_unabridged"
        m["coverage_claim"]={"type":"entire_source"}
        with self.assertRaises(gate.GateError):
            gate.validate_plan(m)


if __name__ == "__main__":
    unittest.main()
