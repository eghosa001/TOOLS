#!/usr/bin/env python3
"""Deterministic tests for structural screenplay checks, NEVER automatic art ratings."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("story_quality_gate", ROOT / "story_quality_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class StoryFirstTests(unittest.TestCase):
    def setUp(self):
        self.scripts = [
            json.loads((ROOT / "storyboards" / name).read_text())
            for name in ("operation-mincemeat-64s.json", "st-louis-1904-marathon-64s.json")
        ]

    def test_both_original_stories_have_structural_arc(self):
        for script in self.scripts:
            with self.subTest(script=script["title"]):
                report = gate.check_story(script)
                self.assertTrue(report["story_pass"])
                self.assertFalse(report["editorial_approved"])
                self.assertFalse(report["render_authorized"])

    def test_draft_cannot_authorize_full_render(self):
        for script in self.scripts:
            with self.subTest(script=script["title"]):
                with self.assertRaisesRegex(ValueError, "not personally reviewed"):
                    gate.check_story(script, require_editor_approval=True)

    def test_no_hook_is_never_accepted(self):
        script = copy.deepcopy(self.scripts[0])
        script["story_arc"].pop("hook")
        with self.assertRaisesRegex(ValueError, "Missing story beats"):
            gate.check_story(script)

    def test_buried_reveal_is_rejected(self):
        script = copy.deepcopy(self.scripts[1])
        script["story_arc"]["reveal_seconds"] = 60
        with self.assertRaisesRegex(ValueError, "reversal"):
            gate.check_story(script)

    def test_mandatory_end_subscription_is_audible_not_autoinjected(self):
        script = copy.deepcopy(self.scripts[1])
        script["shots"][-1]["spoken"] = "The real winner survived an extraordinary race."
        with self.assertRaisesRegex(ValueError, "subscription"):
            gate.check_story(script)

    def test_legacy_stories_do_not_imply_approval(self):
        old = {"seconds": 64, "title": "Unmodified London prototype"}
        report = gate.check_story(old, filename="great-fire-london-64s.json")
        self.assertFalse(report["story_pass"])
        self.assertFalse(report["editorial_approved"])
        with self.assertRaisesRegex(ValueError, "story_arc"):
            gate.check_story(old, require_editor_approval=True,
                             filename="great-fire-london-64s.json")

    def test_unknown_story_cannot_skip_premise_and_outcome(self):
        with self.assertRaisesRegex(ValueError, "story_arc"):
            gate.check_story({"seconds":64}, filename="new-64s.json")


if __name__ == "__main__":
    unittest.main()
