"""Offline, free E101 sound-picture handoff tests; no WAV/art downloads."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "audio"))
import verify_pilot_plan as gate


class PilotPlanningGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in (gate.SHOTS, gate.VOICE_LINES, gate.TIMING, gate.CUES):
            destination = self.root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / rel, destination)

    def change(self, rel, callback):
        path = self.root / rel
        doc = json.loads(path.read_text(encoding="utf8"))
        callback(doc)
        path.write_text(json.dumps(doc), encoding="utf8")

    def test_current_plan_passes_but_does_not_approve(self):
        result = gate.check(self.root)
        self.assertEqual(result["status"], "PLAN_INTEGRITY_PASS_NOT_PRODUCTION_APPROVAL")
        self.assertEqual((result["frames"], result["shots"], result["dialogue_clips"], result["unrecorded_sound_cues"]),
                         (816, 12, 7, 12))
        self.assertFalse(result["episode_ready"])

    def test_dialogue_drift_fails_closed(self):
        self.change(gate.VOICE_LINES, lambda doc: doc["dialogue_lines"][0].update(canonical_text="Different words"))
        with self.assertRaisesRegex(ValueError, "voice script drift"):
            gate.check(self.root)

    def test_voice_overrun_fails_closed(self):
        self.change(gate.TIMING, lambda doc: doc["selected_audio_fit"][0].update(duration_seconds=6.0))
        with self.assertRaisesRegex(ValueError, "overruns"):
            gate.check(self.root)

    def test_cue_past_shot_boundary_fails_closed(self):
        self.change(gate.CUES, lambda doc: doc["cues"][0].update(end_frame=200))
        with self.assertRaisesRegex(ValueError, "violates picture timeline"):
            gate.check(self.root)

    def test_unrecorded_foley_cannot_be_marked_approved(self):
        self.change(gate.CUES, lambda doc: doc["cues"][0].update(human_review_approved=True))
        with self.assertRaisesRegex(ValueError, "incorrectly marked approved"):
            gate.check(self.root)

    def test_unreviewed_retime_fails_closed(self):
        self.change(gate.TIMING, lambda doc: doc["shots"][0].update(added_frames=2))
        with self.assertRaisesRegex(ValueError, "unreviewed frame extension"):
            gate.check(self.root)

    def test_cannot_promote_voice_approvals_from_metadata(self):
        self.change(gate.VOICE_LINES, lambda doc: doc["dialogue_lines"][0].update(approved=True))
        with self.assertRaisesRegex(ValueError, "human-approved"):
            gate.check(self.root)


if __name__ == "__main__":
    unittest.main()
