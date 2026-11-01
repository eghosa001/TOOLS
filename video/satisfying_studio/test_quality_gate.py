"""Tests for fail-closed studio gates; no Blender, FFmpeg or paid services needed."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import quality_gate as q


class StudioGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {
            "concept": "Original 30-second marble-run design with five planned beats",
            "duration_seconds": 30,
            "preview_file": "render/sample.mp4",
            "final_file": "render/final.mp4",
            "av_scan_file": "render/post_render_av_scan.json",
            "manually_directed_shots": [
                {"start_seconds": 0, "end_seconds": 15,
                 "visual_intent": "Top-down view of marble spirals",
                 "movement": "One marble rolling along the track",
                 "sound_cue": "Rolling marble and three clicks",
                 "source_and_rights": "Original scene built in Blender"},
                {"start_seconds": 15, "end_seconds": 30,
                 "visual_intent": "Marbles converge into a single row",
                 "movement": "Acceleration through a narrowing gate",
                 "sound_cue": "Closely synchronized marble collisions",
                 "source_and_rights": "Original scene built in Blender"},
            ],
        }
        (self.root / "render").mkdir()
        self.preview = self.root / self.plan["preview_file"]
        self.preview.write_bytes(b"representative-example-preview")
        self.final = self.root / self.plan["final_file"]
        self.final.write_bytes(b"example-master")
        self.manifest = self.root / "production.json"
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.plan), encoding="utf-8")

    def add_baked_physics(self):
        # Genuine filesystem evidence (not Blender execution): unit-test only.
        blend = self.root / "render" / "tested_physics.blend"
        blend.write_bytes(b"unit-test-blender-cache-file")
        proof = {
            "solver": "blender_softbody",
            "source_blend": blend.name,
            "source_blend_sha256": q.sha256(blend),
            "baked_point_cache": True,
            "cached_frames": 720,
            "director_floating_risk": False,
            "director_camera": {"action": "keep", "lens": 61},
        }
        camera = [{"frame": frame, "min_x": .20, "max_x": .80,
                   "min_y": .15, "max_y": .85}
                  for frame in (1, 24, 48, 70, 90, 105, 120)]
        (self.root / "render" / "actual_physics_camera_framing.json").write_text(
            json.dumps(camera), encoding="utf-8")
        manifest = self.root / "render" / "physics_bake_manifest.json"
        manifest.write_text(json.dumps(proof), encoding="utf-8")
        self.plan["physics_cache_manifest"] = "render/physics_bake_manifest.json"

    def attach_av_review_evidence(self):
        """Deterministic fixture only: does not claim a real editor watched anything."""
        scan = {
            "schema_version": 1,
            "scan_complete": True,
            "master_sha256": q.sha256(self.final),
            "duration_seconds": 30,
            "audio_continuity": {"passed": True, "gaps": []},
            "unresolved_technical_blockers": [],
            "warnings": [],
        }
        av_file = self.root / self.plan["av_scan_file"]
        av_file.write_text(json.dumps(scan))
        review = self.plan["final_review"]
        review.update({
            "reviewer": "Unit-test editor fixture",
            "review_method": "Fixture simulating full visual replay and independent headphone playback",
            "full_video_watched": True,
            "full_audio_listened": True,
            "headphone_review_completed": True,
            "reviewed_av_scan_sha256": q.sha256(av_file),
            "shot_reviews": [
                {
                    "shot_index": i, "start_seconds": shot["start_seconds"],
                    "end_seconds": shot["end_seconds"],
                    "visual_observations": "Fixture: material, camera and action continuity checked",
                    "audio_observations": "Fixture: physical Foley timbre and sound presence assessed",
                    "sync_observations": "Fixture: actual simulated contact timing compared with cues",
                    "dynamics_match": True,
                    "dynamics_observations": "Fixture: judged sound force, attack, grain timbre and easing of movement and rest.",
                    "contact_checks": [{
                        "time_seconds": shot["start_seconds"] + 1,
                        "cue_id": "fixture-audio-cue-" + str(i),
                        "material_action_notes": "Fixture: appropriate physical impact and surface texture",
                        "material_action_match": True,
                        "visual_intensity": "moderate",
                        "audio_intensity": "moderate",
                        "energy_match": True,
                        "timbre_harshness_match": True,
                        "dynamics_notes": "Fixture: audible impact force and natural tail match visual motion.",
                        "sync_error_frames": 0,
                    }],
                } for i, shot in enumerate(self.plan["manually_directed_shots"], 1)
            ],
        })
        # Test-only, synthetic attestation shape: it is not evidence anyone
        # listened to or approved a genuine video.
        source = self.root / "render" / "fake_recorded_marble.wav"
        source.write_bytes(b"SCENE PARITY UNIT TEST FIXTURE, NOT VALID PUBLICATION AUDIO")
        parity_scenes = []
        for i, shot in enumerate(self.plan["manually_directed_shots"], 1):
            start_frame = round(shot["start_seconds"] * 24)
            end_frame = round(shot["end_seconds"] * 24)
            event_id = f"fixture-impact-{i}"
            scene = {
                "scene_index": i,
                "start_frame": start_frame, "end_frame": end_frame,
                "visible_material": "glass marbles on a track",
                "visible_action": "glass marble rolling and striking a rail",
                "visual_environment": "indoor marble studio track",
                "actual_audio_material": "recorded glass against metal",
                "actual_audio_action": "soft recorded marble roll and collision",
                "audio_environment": "indoor controlled studio recording",
                "sound_source_ids": ["fixture-marble"],
                "reviewed_picture_and_sound_together": True,
                "material_match": True, "environment_match": True,
                "intensity_match": True,
                "no_unmatched_audible_events": True,
                "audio_reviewed_after_effects": True,
                "audible_texture_observations":
                    "Fixture: granular marble roll remains audible over the whole deliberate movement.",
                "rain_or_action_intensity_observations":
                    "Fixture: the rolling marble builds toward an impact and then fades in force.",
                "audio_mix_and_perspective_notes":
                    "Fixture: the rolling contact remains close and spatially steady within a studio.",
                "sync_and_transition_notes":
                    "Fixture: one clear impact coincides with the planned observed marble collision.",
                "visual_effects_affect_sound": False,
                "salient_visible_events": [event_id],
                "synchronized_sound_events": [{
                    "event_id": event_id, "visual_frame": start_frame + 24,
                    "audio_onset_frame": start_frame + 24,
                    "sound_source_id": "fixture-marble",
                    "visible_event": "glass marble strikes the hard track",
                    "heard_event": "small recorded tap of marble and metal",
                    "material_match": True, "force_match": True,
                    "auditioned_with_picture": True,
                    "visual_intensity": "moderate", "audible_intensity": "moderate",
                    "review_notes": "Fixture: compared the planned impact to this one artificial contact cue.",
                }],
            }
            if i > 1:
                scene["transition_vs_previous"] = (
                    "Fixture: the visual cut and audio track carry marble rolling "
                    "without an unintended shift to a different room or sound.")
            parity_scenes.append(scene)
        review["scene_audio_parity"] = {
            "schema_version": 1, "approved": True, "unresolved_issues": [],
            "reviewer": "Unit-test editor fixture",
            "review_method": "Unit-test simulation of exact-master full visual and headphone review, NOT A REAL HUMAN REVIEW",
            "full_video_watched": True,
            "full_audio_listened_on_headphones": True,
            "reviewed_after_last_picture_edit": True,
            "reviewed_after_last_audio_edit": True,
            "reviewed_master_sha256": q.sha256(self.final),
            "reviewed_av_scan_sha256": q.sha256(av_file),
            "whole_film_observations": (
                "Unit-test fixture: each scene is bound to artificial "
                "recording hashes and planned marble actions. This data does "
                "not attest a real playback or permit a release."),
            "sound_sources": [{
                "id": "fixture-marble",
                "file": "render/fake_recorded_marble.wav",
                "sha256": q.sha256(source),
                "source_url": "studio://test-fixture-only",
                "license": "original",
                "recorded_material": "hard glass and metal",
                "recorded_action": "marble rolling across a short track",
                "recorded_environment": "indoor studio with quiet background",
            }],
            "scene_checks": parity_scenes,
        }

    def approve_preview(self):
        self.plan["preview_review"] = {
            "approved": True, "reviewer": "Video editor",
            "reviewed_preview_sha256": q.sha256(self.preview),
            "observations": "Watched moving marbles and heard each impact at its matching moment.",
            "dynamics_match": True,
            "dynamics_observations": "Fixture: gentle gestures have restrained impact; stronger movement has a natural rising attack and tail.",
            "visual_score": 9, "material_realism_score": 9, "texture_detail_score": 9,
            "lighting_color_score": 9, "physical_coherence_score": 9,
            "motion_score": 9, "foley_quality_score": 9, "audio_sync_score": 9,
            "satisfaction_score": 9, "blocking_issues": [],
            "benchmark_video_ids": ["kKOJZbthcyo", "7gV-0be8WqE"],
            "benchmark_visual_comparison": "Examined the tactile material appearance and coherent close-up movement against reference scenes.",
            "benchmark_audio_comparison": "Compared the squeeze sound, release sound, tiny crack and contact timing with reference scenes.",
        }

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_unapproved_preview_blocks(self, _):
        with self.assertRaisesRegex(q.GateError, "not been personally approved"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_exact_approved_preview_passes(self, _):
        self.approve_preview()
        self.assertEqual(q.check_preview(self.plan, self.root), q.sha256(self.preview))

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_modified_preview_invalidates_approval(self, _):
        self.approve_preview()
        self.preview.write_bytes(b"modified file")
        with self.assertRaisesRegex(q.GateError, "changed after approval"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_substandard_review_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["motion_score"] = 8
        with self.assertRaisesRegex(q.GateError, "motion_score"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_missing_reference_comparison_blocks(self, _):
        self.approve_preview()
        del self.plan["preview_review"]["benchmark_audio_comparison"]
        with self.assertRaisesRegex(q.GateError, "benchmark_audio_comparison"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_missing_material_realism_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["material_realism_score"] = 8
        with self.assertRaisesRegex(q.GateError, "material_realism_score"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_low_foley_quality_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["foley_quality_score"] = 8
        with self.assertRaisesRegex(q.GateError, "foley_quality_score"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_unapproved_reference_id_blocks(self, _):
        self.approve_preview()
        self.plan["preview_review"]["benchmark_video_ids"] = ["fictional-id"]
        with self.assertRaisesRegex(q.GateError, "reference video ID"):
            q.check_preview(self.plan, self.root)

    def test_exact_five_second_plan_allowed(self):
        self.plan["duration_seconds"] = 5
        self.plan["manually_directed_shots"] = [
            {"start_seconds": 0, "end_seconds": 5,
             "visual_intent": "Iridescent close-up reveal on reflective textured stone",
             "movement": "Controlled 3D squeeze and translucent deformation",
             "sound_cue": "Manually placed wet squeeze, crack and glass click",
             "source_and_rights": "Original authored Blender meshes and licensed Foley"}]
        self.save()
        validated, _ = q.load_plan(self.manifest)
        self.assertEqual(validated["duration_seconds"], 5)

    def test_widescreen_long_form_geometry_can_pass(self):
        self.plan["delivery_aspect_ratio"] = "16:9"
        q.check_output_geometry({"width": 960, "height": 540}, "16:9", preview=True)
        q.check_output_geometry({"width": 1920, "height": 1080}, "16:9", preview=False)
        self.approve_preview()
        with patch.object(q, "media_info", return_value={"duration": 5, "width": 960, "height": 540}):
            self.assertEqual(q.check_preview(self.plan, self.root), q.sha256(self.preview))

    def test_landscape_not_silently_allowed_for_short(self):
        with self.assertRaisesRegex(q.GateError, "aspect ratio must be 9:16"):
            q.check_output_geometry({"width": 1920, "height": 1080}, "9:16", preview=False)

    def test_low_resolution_landscape_final_is_rejected(self):
        with self.assertRaisesRegex(q.GateError, "at least 1280x720"):
            q.check_output_geometry({"width": 960, "height": 540}, "16:9", preview=False)

    def test_eight_minute_manifest_requires_explicit_long_form_kind(self):
        self.prepare_long_episode("single-material")
        self.plan["duration_seconds"] = 480
        self.plan["manually_directed_shots"][1]["end_seconds"] = 480
        self.save()
        with self.assertRaisesRegex(q.GateError, "Pilot must be 3-180"):
            q.load_plan(self.manifest)
        self.plan["production_kind"] = "long-form"
        self.plan["delivery_aspect_ratio"] = "16:9"
        self.save()
        data, _ = q.load_plan(self.manifest)
        self.assertEqual(data["duration_seconds"], 480)
        self.assertEqual(data["delivery_aspect_ratio"], "16:9")

    def test_discontinuous_manual_timeline_blocks(self):
        self.plan["manually_directed_shots"][1]["start_seconds"] = 15.8
        self.save()
        with self.assertRaisesRegex(q.GateError, "gap, overlap"):
            q.load_plan(self.manifest)

    @patch.object(q, "media_info", return_value={"duration": 30, "width": 720, "height": 1280})
    def test_release_requires_explicit_final_review(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        def fake_media(p):
            return {"duration": 5, "width": 540, "height": 960} if p == self.preview else {
                "duration": 30, "width": 720, "height": 1280}
        mocked.side_effect = fake_media
        with self.assertRaisesRegex(q.GateError, "not approved"):
            q.check_final(self.plan, self.root)
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Viewed the entire 30-second film and inspected every audio beat.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Reviewed actual final photoreal materials and macro lens presentation against user videos.",
            "benchmark_audio_comparison": "Verified full final Foley sync, textures and tactile impact sounds against user references.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.attach_av_review_evidence()
        self.assertEqual(q.check_final(self.plan, self.root), q.sha256(self.final))

    @patch.object(q, "media_info")
    def test_release_blocks_when_post_render_scan_missing(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960} if p == self.preview
            else {"duration": 30, "width": 720, "height": 1280}
        )
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Fixture: watched whole video and heard the soundtrack.",
            "blocking_issues": [], "reviewer": "Editor fixture",
            "benchmark_visual_comparison": "Fixture comparison of macro realism against actual relevant reference visuals.",
            "benchmark_audio_comparison": "Fixture comparison of Foley realism against actual relevant reference sound.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        with self.assertRaisesRegex(q.GateError, "post-render AV scan missing"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_wrong_master_hash_rejects_post_render_review(self, mocked):
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960} if p == self.preview
            else {"duration": 30, "width": 720, "height": 1280}
        )
        self.approve_preview()
        self.add_baked_physics()
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Fixture: entire master seen and auditioned.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Fixture appearance, colour, motion and editing judged against reference.",
            "benchmark_audio_comparison": "Fixture action-specific acoustic textures and timing judged against reference.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.attach_av_review_evidence()
        av_file = self.root / self.plan["av_scan_file"]
        obj = json.loads(av_file.read_text())
        obj["master_sha256"] = "wrong-file-sha256"
        av_file.write_text(json.dumps(obj))
        self.plan["final_review"]["reviewed_av_scan_sha256"] = q.sha256(av_file)
        with self.assertRaisesRegex(q.GateError, "different export"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_missing_headphone_audition_blocks_even_if_scan_passes(self, mocked):
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960} if p == self.preview
            else {"duration": 30, "width": 720, "height": 1280}
        )
        self.approve_preview()
        self.add_baked_physics()
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Fixture: entire film and soundtrack.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Fixture reviewed macro lighting and realism against known reference films.",
            "benchmark_audio_comparison": "Fixture reviewed tactile sound quality and rhythm against known reference films.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.attach_av_review_evidence()
        self.plan["final_review"]["full_audio_listened"] = False
        with self.assertRaisesRegex(q.GateError, "soundtrack must actually be heard"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_mismatched_contact_blocks_even_if_scores_are_high(self, mocked):
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960} if p == self.preview
            else {"duration": 30, "width": 720, "height": 1280}
        )
        self.approve_preview()
        self.add_baked_physics()
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Fixture: entire film and soundtrack.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Fixture reviewed material lighting and realistic movement against references.",
            "benchmark_audio_comparison": "Fixture listened for natural sound materials versus referenced videos.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.attach_av_review_evidence()
        self.plan["final_review"]["shot_reviews"][1]["contact_checks"][0]["material_action_match"] = False
        with self.assertRaisesRegex(q.GateError, "mismatched sound"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_540p_final_still_rejected(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960}
            if p == self.preview else
            {"duration": 30, "width": 540, "height": 960}
        )
        with self.assertRaisesRegex(q.GateError, "720x1280"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_missing_physics_prevents_release_even_with_approved_preview(self, mocked):
        self.approve_preview()
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960}
            if p == self.preview else
            {"duration": 30, "width": 720, "height": 1280}
        )
        with self.assertRaisesRegex(q.GateError, "physics"):
            q.check_final(self.plan, self.root)

    @patch.object(q, "media_info")
    def test_false_bake_proof_prevents_release(self, mocked):
        self.approve_preview()
        self.add_baked_physics()
        manifest = self.root / self.plan["physics_cache_manifest"]
        data = json.loads(manifest.read_text())
        data["baked_point_cache"] = False
        manifest.write_text(json.dumps(data))
        mocked.side_effect = lambda p: (
            {"duration": 5, "width": 540, "height": 960}
            if p == self.preview else
            {"duration": 30, "width": 720, "height": 1280}
        )
        with self.assertRaisesRegex(q.GateError, "physics"):
            q.check_final(self.plan, self.root)


    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_preview_with_harsh_mismatched_foley_is_rejected(self, _):
        self.approve_preview()
        self.plan["preview_review"]["dynamics_match"] = False
        with self.assertRaisesRegex(q.GateError, "sound intensity/dynamics"):
            q.check_preview(self.plan, self.root)

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_preview_without_actual_dynamics_notes_is_rejected(self, _):
        self.approve_preview()
        self.plan["preview_review"]["dynamics_observations"] = ""
        with self.assertRaisesRegex(q.GateError, "preview requires genuine observations"):
            q.check_preview(self.plan, self.root)

    def test_harsh_cue_does_not_pass_merely_for_material_and_sync(self):
        self.approve_preview()
        self.add_baked_physics()
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Fixture: watched and listened to whole film.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Fixture: checked materials, colours and coherent visuals against actual references.",
            "benchmark_audio_comparison": "Fixture: checked genuine audio cues, timing and sound force against ASMR references.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.attach_av_review_evidence()
        cue = self.plan["final_review"]["shot_reviews"][0]["contact_checks"][0]
        cue["visual_intensity"] = "delicate"
        cue["audio_intensity"] = "forceful"
        with self.assertRaisesRegex(q.GateError, "intensity/harshness"):
            q.check_post_render_av_review(self.plan, self.root, q.sha256(self.final), self.plan["final_review"])
        cue["audio_intensity"] = "delicate"
        cue["timbre_harshness_match"] = False
        with self.assertRaisesRegex(q.GateError, "intensity/harshness"):
            q.check_post_render_av_review(self.plan, self.root, q.sha256(self.final), self.plan["final_review"])
        cue["timbre_harshness_match"] = True
        cue["energy_match"] = False
        with self.assertRaisesRegex(q.GateError, "intensity/harshness"):
            q.check_post_render_av_review(self.plan, self.root, q.sha256(self.final), self.plan["final_review"])

    def test_unsupported_shot_dynamics_cannot_be_approved(self):
        self.approve_preview()
        self.add_baked_physics()
        self.plan["final_review"] = {
            "approved": True, "reviewed_final_sha256": q.sha256(self.final),
            "observations": "Fixture: watched and listened to whole film.",
            "blocking_issues": [],
            "benchmark_visual_comparison": "Fixture: compared the visual response against source examples of similar materials.",
            "benchmark_audio_comparison": "Fixture: compared action-to-sound timbre and force against known ASMR sounds.",
            **{key: 9 for key in q.REQUIRED_QUALITY_SCORES},
        }
        self.attach_av_review_evidence()
        self.plan["final_review"]["shot_reviews"][0]["dynamics_match"] = False
        with self.assertRaisesRegex(q.GateError, "energy/harshness mismatch"):
            q.check_post_render_av_review(self.plan, self.root, q.sha256(self.final), self.plan["final_review"])

    def test_timeout_stops_renderer(self):
        log = self.root / "timeout.log"
        with self.assertRaisesRegex(q.GateError, "stopped after"):
            q.run_limited([sys.executable, "-c", "import time; time.sleep(10)"], 0.1, log)
        self.assertTrue(log.exists())



    def prepare_long_episode(self, fmt, material="translucent jelly"):
        self.plan["duration_seconds"] = 60
        self.plan["editorial_format"] = fmt
        self.plan["editorial_thesis"] = "Show a satisfying tactile pattern with matching sounds"
        self.plan["material_family"] = material
        self.plan["manually_directed_shots"][1]["end_seconds"] = 60
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["material_family"] = material
            shot["editorial_link"] = "One visual sensory idea with deliberate sound"
            if i:
                shot["transition_intent"] = "Direct continuation or meaningful contrast"

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_real_reviewed_independent_youtube_benchmark_allowed(self, _):
        self.approve_preview()
        review = self.plan["preview_review"]
        review["benchmark_video_ids"] = []
        review["researched_benchmarks"] = [{
            "video_url": "https://www.youtube.com/watch?v=hUSNOEnXdyg",
            "title": "Clay Butter ASMR",
            "research_source_url": "https://hooksignals.com/youtube-outliers/asmr",
            "actual_visual_review": True,
            "actual_audio_review": True,
            "review_notes": "Unit test fixture only: editor describes specific material contact, tactile layering, rhythm, and visual-audio correspondences after review."
        }]
        self.assertEqual(q.check_preview(self.plan, self.root), q.sha256(self.preview))

    @patch.object(q, "media_info", return_value={"duration": 5, "width": 540, "height": 960})
    def test_metadata_only_benchmark_does_not_replace_listening(self, _):
        self.approve_preview()
        review = self.plan["preview_review"]
        review["benchmark_video_ids"] = []
        review["researched_benchmarks"] = [{
            "video_url": "https://www.youtube.com/watch?v=hUSNOEnXdyg",
            "title": "Clay Butter ASMR",
            "research_source_url": "https://hooksignals.com/youtube-outliers/asmr",
            "actual_visual_review": True,
            "actual_audio_review": False,
            "review_notes": "Only public title, view count, duration and channel are observed; nothing can establish the real sound performance."
        }]
        with self.assertRaisesRegex(q.GateError, "real viewing AND listening"):
            q.check_preview(self.plan, self.root)

    def test_long_episode_blocks_unknown_editorial_format(self):
        self.prepare_long_episode("totally_random")
        self.save()
        with self.assertRaisesRegex(q.GateError, "editorial_format"):
            q.load_plan(self.manifest)

    def test_long_episode_accepts_same_material_ritual(self):
        self.prepare_long_episode("single-material")
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "single-material")

    def test_focused_material_blocks_unplanned_dye_cutaway(self):
        self.prepare_long_episode("single-material")
        self.plan["manually_directed_shots"][1]["material_family"] = "paint dye"
        self.save()
        with self.assertRaisesRegex(q.GateError, "unexpectedly changes"):
            q.load_plan(self.manifest)

    def test_comparison_accepts_two_real_materials(self):
        self.prepare_long_episode("comparison")
        self.plan["comparison_axis"] = "identical crush pressure"
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["material_family"] = "jelly" if i == 0 else "crunchy shell"
            shot["comparison_axis"] = "identical crush pressure"
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "comparison")

    def test_comparison_rejects_unrelated_actions(self):
        self.prepare_long_episode("comparison")
        self.plan["comparison_axis"] = "identical crush pressure"
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["comparison_axis"] = "identical crush pressure" if i == 0 else "random cutting"
        self.save()
        with self.assertRaisesRegex(q.GateError, "share a clear test"):
            q.load_plan(self.manifest)

    def test_thematic_compilation_accepts_multiple_triggers(self):
        self.prepare_long_episode("themed-compilation")
        self.plan["manually_directed_shots"][1]["material_family"] = "crunchy sand"
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "themed-compilation")

    def test_compilation_rejects_unmotivated_transition(self):
        self.prepare_long_episode("themed-compilation")
        self.plan["manually_directed_shots"][1].pop("transition_intent")
        self.save()
        with self.assertRaisesRegex(q.GateError, "intentional transition missing"):
            q.load_plan(self.manifest)

    def test_process_transformation_stages(self):
        self.prepare_long_episode("process-transformation")
        for i, shot in enumerate(self.plan["manually_directed_shots"]):
            shot["process_stage"] = "cleaning" if i == 0 else "finishing"
        self.save()
        loaded, _ = q.load_plan(self.manifest)
        self.assertEqual(loaded["editorial_format"], "process-transformation")

    def test_surreal_world_requires_world_identity(self):
        self.prepare_long_episode("surreal-world")
        self.save()
        with self.assertRaisesRegex(q.GateError, "fantasy-world identity"):
            q.load_plan(self.manifest)



if __name__ == "__main__":
    unittest.main()
