"""Synthetic regression tests for the dedicated audio-first audiobook release gate."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mandatory_release_gate import validate_packet
from audio_first_release_gate import QUALITY
from test_mandatory_release_gate import packet as legacy_packet

def audio_first_packet():
    data = legacy_packet()
    data["production_mode"] = "audio_first"
    data["release_manifest"]["production_mode"] = "audio_first"
    # The old illustrated scorecard may be archived, but is not an audio-first
    # release dependency. A distinct scored listening and cover review replaces it.
    data.pop("episode_quality_scorecard", None)
    data["audio_first_quality_scorecard"] = {
        key: dict(score=9, evidence="Synthetic episode-specific review details",
                  reviewer="Synthetic reviewer",
                  signed_review_reference="Synthetic review signature")
        for key in QUALITY
    }
    data["full_episode_audio_review"].update(
        approved_script_sha256="e"*64,
        narration_audio_sha256="f"*64,
    )
    data["final_video_review"] = dict(
        human_reviewer="Synthetic reviewer",
        review_reference="Synthetic full-length encoded MP4 review",
        final_mp4_sha256="a"*64,
        approved_thumbnail_sha256="b"*64,
        cover_image_sha256="c"*64,
        approved_script_sha256="e"*64,
        narration_audio_sha256="f"*64,
        watched_entire_encoded_mp4=True,
        full_audio_and_static_cover_checked=True,
        single_cover_consistent=True,
        cover_and_thumbnail_rights_verified=True,
        cover_legible_on_phone=True,
        video_audio_streams_verified=True,
        music_and_voice_checked=True,
        approved_thumbnail_checked=True,
        narration_duration_ms=60000,
        video_duration_ms=60500,
    )
    return data

class AudioFirstReleaseTests(unittest.TestCase):
    def test_cover_and_full_narration_can_pass_without_scene_art(self):
        data=audio_first_packet()
        self.assertIn("Episode 02", validate_packet(data, postupload=True))
        self.assertNotIn("source_accurate_images", data["final_video_review"])
        self.assertNotIn("voice_image_priority_review", data)

    def test_no_explicit_owner_approval_blocks(self):
        data=audio_first_packet()
        data["release_manifest"]["owner_public_release_approved"]=False
        with self.assertRaisesRegex(ValueError, "explicit owner approval"):
            validate_packet(data)

    def test_mode_and_visual_supersession_are_explicit(self):
        data=audio_first_packet()
        del data["release_manifest"]["production_mode"]
        with self.assertRaisesRegex(ValueError, "AUDIO_FIRST_RELEASE_MANIFEST_MODE_REQUIRED"):
            validate_packet(data)
        data=audio_first_packet()
        data["master_rule_reviews"]["92"]["status"]="superseded"
        with self.assertRaisesRegex(ValueError, "supersession"):
            validate_packet(data)
        data["master_rule_reviews"]["92"].update(
            owner_exception_approved=True, reason="Owner retired scene art",
            owner_approval_reference="2026-11-14 owner audio-first direction")
        self.assertIn("Episode 02", validate_packet(data))

    def test_full_audio_and_cover_checks_cannot_be_bypassed(self):
        for key in ("watched_entire_encoded_mp4",
                    "single_cover_consistent",
                    "cover_and_thumbnail_rights_verified",
                    "music_and_voice_checked"):
            data=audio_first_packet()
            data["final_video_review"][key]=False
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "FINAL_AUDIO_FIRST_VIDEO_BLOCKED"):
                validate_packet(data)

    def test_unlistened_audio_blocks(self):
        data=audio_first_packet()
        data["full_episode_audio_review"]["entire_episode_listened"]=False
        with self.assertRaisesRegex(ValueError, "AUDIO_REVIEW_BLOCKED"):
            validate_packet(data)

    def test_script_or_audio_hash_mismatch_blocks(self):
        data=audio_first_packet()
        data["final_video_review"]["narration_audio_sha256"]="d"*64
        with self.assertRaisesRegex(ValueError, "AUDIO_SCRIPT_VIDEO_HASH_MISMATCH"):
            validate_packet(data)

    def test_video_duration_must_match_narration(self):
        data=audio_first_packet()
        data["final_video_review"]["video_duration_ms"]=70000
        with self.assertRaisesRegex(ValueError, "FINAL_VIDEO_DURATION_MISMATCH"):
            validate_packet(data)

    def test_low_score_blocks(self):
        data=audio_first_packet()
        data["audio_first_quality_scorecard"]["opening_hook_and_listening_clarity"]["score"]=7
        with self.assertRaisesRegex(ValueError, "AUDIO_FIRST_QUALITY_BLOCKED"):
            validate_packet(data)

    def test_live_playlist_must_be_verified(self):
        data=audio_first_packet()
        data["verified_live_youtube_metadata"]["playlist_item_video_id"]=None
        with self.assertRaisesRegex(ValueError, "LIVE_PLAYLIST_MEMBERSHIP_NOT_VERIFIED"):
            validate_packet(data,postupload=True)

if __name__=="__main__":
    unittest.main()
