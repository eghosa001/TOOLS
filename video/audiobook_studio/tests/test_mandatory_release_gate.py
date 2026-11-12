import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mandatory_release_gate import validate_packet
from release_naming import canonical_identity
from test_episode_quality_gate import example as example_team_scorecard

def approval():
    return dict(status="pass", reviewer="synthetic test", evidence="synthetic",
                reviewed_at="2026-11-12")

def packet():
    title, series = "The Blue Thread", "The Villain's Second Son"
    base = canonical_identity(series, 2, title)
    base.pop("narration_filename_prefix")
    release = dict(base, series_title=series, episode_number=2, episode_title=title,
                   narration_filename="The_Villains_Second_Son_E02_The_Blue_Thread_NARRATION_KokoroMichael.wav",
                   channel_id="UC9gPFT64nrou4TMSxu1NZKg",
                   owner_public_release_approved=True)
    holds = {x: approval() for x in ("story_and_bible", "independent_literary_and_originality",
             "voice_names_and_full_audio", "visual_and_final_mp4", "owner_final_publication_approval")}
    holds["owner_final_publication_approval"]["owner_approval_reference"] = "synthetic"
    holds["independent_literary_and_originality"]["independent_human_review"] = True
    audio = dict(human_reviewer="synthetic", signed_review_reference="synthetic",
                 entire_episode_listened=True, headphones_tested=True, phone_speaker_tested=True,
                 speech_script_fidelity_checked=True, no_clipping_or_masked_words=True)
    for key in ("naturalness", "word_and_name_fidelity", "emotional_fit_dialogue",
                "timbre_and_comfort", "pacing", "technical_mastering"):
        audio[key] = dict(score=9, evidence="synthetic")
    video = dict(human_reviewer="synthetic", review_reference="synthetic",
                 final_mp4_sha256="a"*64, approved_thumbnail_sha256="b"*64)
    for key in ("watched_entire_encoded_mp4", "source_accurate_images", "full_color_artwork",
                "character_and_prop_continuity", "scene_to_audio_alignment",
                "music_and_voice_checked", "licensed_assets_verified", "approved_thumbnail_checked"):
        video[key] = True
    playlist = "PLsynthetic"
    quality = example_team_scorecard()
    quality["episode_id"] = "E02"
    quality["predelivery"]["final_mp4_sha256"] = "a"*64
    music = {"preflight_receipt_sha256": "c"*64,
             "music_source_sha256": "d"*64,
             "preflight_receipt_reference": "private example music first receipt",
             "rights_provenance_reference": "private example composition rights"}
    for field in ("music_prepared_before_new_voice",
                  "same_bed_verified_in_final_mix",
                  "music_audible_on_phone_and_headphones",
                  "voice_fully_intelligible_over_bed",
                  "beginning_middle_end_music_spot_checks",
                  "no_unintentional_music_gaps",
                  "no_clipping_pumping_or_rough_music_loops"):
        music[field] = True
    return dict(master_rules_version="1.1", release_manifest=release,
                episode_quality_scorecard=quality,
                music_first_and_final_mix=music,
                master_rule_reviews={str(i):approval() for i in range(1,110)},
                universal_story_scorecard_16={f"{i:02d}":dict(
                    score=9, scene_evidence="synthetic", reviewer="synthetic") for i in range(1,17)},
                full_episode_audio_review=audio, final_video_review=video,
                release_holds=holds,
                upload_metadata=dict(title=release["youtube_title"],
                    description_headline=release["description_headline"],
                    existing_series_playlist_id=playlist,
                    connector_title_field_mapping_verified=True,
                    correct_channel_session_verified=True,
                    playlist_insert_permission_verified=True),
                verified_live_youtube_metadata=dict(video_id="abc",
                    playlist_item_video_id="abc", title=release["youtube_title"],
                    channel_id=release["channel_id"], playlist_id=playlist,
                    description_headline=release["description_headline"],
                    approved_thumbnail_visually_verified=True,
                    official_api_or_watch_page_evidence="synthetic"))

class GateTests(unittest.TestCase):
    def test_synthetic_packet(self):
        self.assertIn("Episode 02", validate_packet(packet(), postupload=True))
    def test_missing_rule_blocks(self):
        p=packet(); del p["master_rule_reviews"]["94"]
        with self.assertRaisesRegex(ValueError, "109 rules"): validate_packet(p)
    def test_suppressed_rule_blocks(self):
        p=packet(); p["master_rule_reviews"]["94"]["status"]="pending"
        with self.assertRaisesRegex(ValueError, "rule 94"): validate_packet(p)
    def test_exception_without_owner_blocks(self):
        p=packet(); p["master_rule_reviews"]["70"]["status"]="superseded"
        with self.assertRaisesRegex(ValueError, "owner approval"): validate_packet(p)
    def test_bad_story_score_blocks(self):
        p=packet(); p["universal_story_scorecard_16"]["11"]["score"]=7
        with self.assertRaisesRegex(ValueError, "story 11"): validate_packet(p)
    def test_unlistened_episode_blocks(self):
        p=packet(); p["full_episode_audio_review"]["entire_episode_listened"]=False
        with self.assertRaisesRegex(ValueError, "entire_episode_listened"): validate_packet(p)
    def test_wrong_title_blocks(self):
        p=packet(); p["upload_metadata"]["title"]="Li Tianming faces a repair exam"
        with self.assertRaisesRegex(ValueError, "UPLOAD_TITLE_MISMATCH"): validate_packet(p)
    def test_wrong_live_title_blocks(self):
        p=packet(); p["verified_live_youtube_metadata"]["title"]="Chapter summary"
        with self.assertRaisesRegex(ValueError, "LIVE_TITLE_MISMATCH"): validate_packet(p,postupload=True)
    def test_description_link_not_playlist_membership(self):
        p=packet(); p["verified_live_youtube_metadata"]["playlist_item_video_id"]=None
        with self.assertRaisesRegex(ValueError, "LIVE_PLAYLIST"): validate_packet(p,postupload=True)
    def test_no_independent_reader_blocks(self):
        p=packet(); p["release_holds"]["independent_literary_and_originality"]["independent_human_review"]=False
        with self.assertRaisesRegex(ValueError, "INDEPENDENT_HUMAN"): validate_packet(p)

if __name__ == "__main__":
    unittest.main()
