"""Regression tests: these fixture flags DO NOT represent genuine media review."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from scene_audio_parity_gate import SceneParityError, validate_scene_audio_parity


class SceneAudioParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        f = self.root / "recorded_rain.wav"
        f.write_bytes(b"test fixture only: recorded rain source, not publication audio")
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        self.master = "a" * 64
        self.scan = "b" * 64
        source = {"id": "rain", "file": "recorded_rain.wav",
                  "sha256": sha, "license": "CC0",
                  "source_url": "https://bigsoundbank.com/apartment-closed-window-s2387.html",
                  "recorded_material": "natural water drops",
                  "recorded_action": "recorded ongoing rainfall on a glass window",
                  "recorded_environment": "inside an apartment near a window"}
        self.scene = {
            "scene_index": 1, "start_frame": 0, "end_frame": 180,
            "visible_material": "water on glass", "visible_action": "heavy rain streaking down window",
            "visual_environment": "apartment window in rain",
            "actual_audio_material": "water rain drops against window",
            "actual_audio_action": "recorded steady rainfall with soft intermittent hits",
            "audio_environment": "recorded inside an apartment by a window",
            "sound_source_ids": ["rain"],
            "reviewed_picture_and_sound_together": True,
            "material_match": True, "environment_match": True, "intensity_match": True,
            "no_unmatched_audible_events": True, "audio_reviewed_after_effects": True,
            "audible_texture_observations":
                "Fixture: the soft recorded patter is present during visible rain on glass without a harsh synthetic noise floor.",
            "rain_or_action_intensity_observations":
                "Fixture: the density of recorded impacts remains at a comparable gentle rate throughout this window segment.",
            "audio_mix_and_perspective_notes":
                "Fixture: rain has an indoor glass perspective and the stereo placement does not jump within the shot.",
            "sync_and_transition_notes":
                "Fixture: observed glass impact coincides with the one recorded tap and rain intensity remains plausible.",
            "visual_effects_affect_sound": False,
            "salient_visible_events": ["droplet-1"],
            "synchronized_sound_events": [{
                "event_id": "droplet-1", "visual_frame": 48, "audio_onset_frame": 49,
                "sound_source_id": "rain",
                "visible_event": "single drop impacts glass surface",
                "heard_event": "soft recorded water impact on glass",
                "material_match": True, "force_match": True,
                "auditioned_with_picture": True,
                "visual_intensity": "gentle", "audible_intensity": "gentle",
                "review_notes": "Fixture: matched actual single tap and its soft decay with a recorded impact.",
            }],
        }
        second = copy.deepcopy(self.scene)
        second.update({
            "scene_index": 2, "start_frame": 180, "end_frame": 360,
            "transition_vs_previous":
                "Fixture: a gentle cut retains interior perspective and moves from wet glass to a brighter adjacent pane.",
        })
        second["synchronized_sound_events"][0]["visual_frame"] = 222
        second["synchronized_sound_events"][0]["audio_onset_frame"] = 223
        self.plan = {
            "manually_directed_shots": [
                {"start_seconds": 0, "end_seconds": 7.5},
                {"start_seconds": 7.5, "end_seconds": 15},
            ],
            "final_review": {
                "scene_audio_parity": {
                    "schema_version": 1, "approved": True, "unresolved_issues": [],
                    "reviewer": "Unit fixture only",
                    "review_method": "Fixture of a full exact-master headphones and picture playback review, never evidence of actual playback",
                    "full_video_watched": True, "full_audio_listened_on_headphones": True,
                    "reviewed_after_last_picture_edit": True,
                    "reviewed_after_last_audio_edit": True,
                    "reviewed_master_sha256": self.master,
                    "reviewed_av_scan_sha256": self.scan,
                    "whole_film_observations":
                        "Fixture: every shot has a corresponding audio setting and the one-frame contact times were independently mapped; not actual video approval.",
                    "sound_sources": [source],
                    "scene_checks": [copy.deepcopy(self.scene), second],
                }
            }
        }

    def validate(self):
        return validate_scene_audio_parity(self.plan, self.root, self.master, self.scan)

    def test_complete_two_shot_evidence_fixture_passes_schema(self):
        self.assertEqual(self.validate(), 2)

    def test_missing_report_blocks(self):
        del self.plan["final_review"]["scene_audio_parity"]
        with self.assertRaisesRegex(SceneParityError, "evidence missing"):
            self.validate()

    def test_missing_scene_blocks_even_if_earlier_shot_passed(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"].pop()
        with self.assertRaisesRegex(SceneParityError, "EVERY planned shot"):
            self.validate()

    def test_stale_master_after_video_edit_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["reviewed_master_sha256"] = "c" * 64
        with self.assertRaisesRegex(SceneParityError, "EXACT final"):
            self.validate()

    def test_stale_av_scan_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["reviewed_av_scan_sha256"] = "d" * 64
        with self.assertRaisesRegex(SceneParityError, "EXACT post-render"):
            self.validate()

    def test_unverified_sound_source_hash_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["sound_sources"][0]["sha256"] = "f"*64
        with self.assertRaisesRegex(SceneParityError, "recording has changed"):
            self.validate()

    def test_missing_headphone_review_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["full_audio_listened_on_headphones"] = False
        with self.assertRaisesRegex(SceneParityError, "headphones"):
            self.validate()

    def test_wrong_material_or_environment_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"][1]["environment_match"] = False
        with self.assertRaisesRegex(SceneParityError, "environment_match"):
            self.validate()

    def test_scene_loudness_mismatch_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"][1]["intensity_match"] = False
        with self.assertRaisesRegex(SceneParityError, "intensity_match"):
            self.validate()

    def test_two_frame_audio_impact_mismatch_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"][0]["synchronized_sound_events"][0]["audio_onset_frame"] = 51
        with self.assertRaisesRegex(SceneParityError, "ONE-FRAME"):
            self.validate()

    def test_unmatched_visible_splash_blocks(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"][0]["salient_visible_events"].append("second-splash")
        with self.assertRaisesRegex(SceneParityError, "unmatched visible"):
            self.validate()

    def test_same_audio_source_as_generic_ambient_bed_not_enough(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"][0]["synchronized_sound_events"] = []
        with self.assertRaisesRegex(SceneParityError, "unmatched visible"):
            self.validate()

    def test_ambient_only_needs_reason_and_suitability(self):
        scene = self.plan["final_review"]["scene_audio_parity"]["scene_checks"][1]
        scene.update({"salient_visible_events": [], "synchronized_sound_events": []})
        with self.assertRaisesRegex(SceneParityError, "explain why continuous ambience"):
            self.validate()
        scene["no_distinct_audible_events_reason"] = (
            "Fixture: no individualized raindrop or physical impact was audible; "
            "the scene depicts diffuse rainfall far behind an apartment window.")
        scene["ambient_only_suitable"] = True
        self.assertEqual(self.validate(), 1)

    def test_new_rain_overlay_requires_sound_reaudition(self):
        scene = self.plan["final_review"]["scene_audio_parity"]["scene_checks"][0]
        scene["visual_effects_affect_sound"] = True
        with self.assertRaisesRegex(SceneParityError, "newly generated rain"):
            self.validate()
        scene["effect_sound_reevaluation_notes"] = (
            "Fixture: rewatched and reheard final falling-rain overlays; the existing "
            "indoor patter still reflects visible density, no new audible close impacts.")
        scene["effect_sound_reevaluation_passed"] = True
        self.assertEqual(self.validate(), 2)
        scene["audio_reviewed_after_effects"] = False
        with self.assertRaisesRegex(SceneParityError, "audio_reviewed_after_effects"):
            self.validate()

    def test_transition_context_required(self):
        self.plan["final_review"]["scene_audio_parity"]["scene_checks"][1]["transition_vs_previous"] = ""
        with self.assertRaisesRegex(SceneParityError, "transition from prior shot"):
            self.validate()

    def test_muted_different_material_cannot_be_passed_with_generic_bed(self):
        scene = self.plan["final_review"]["scene_audio_parity"]["scene_checks"][1]
        scene["material_match"] = False
        with self.assertRaisesRegex(SceneParityError, "material_match"):
            self.validate()

    def test_source_clip_license_must_allow_commercial_use(self):
        source = self.plan["final_review"]["scene_audio_parity"]["sound_sources"][0]
        source["license"] = "Unknown internet audio"
        with self.assertRaisesRegex(SceneParityError, "commercial license"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
