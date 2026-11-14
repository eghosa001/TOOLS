#!/usr/bin/env python3
"""Fail-closed evidence validation for Mythveil's audio-first video mode.

This validates the structure of private, signed evidence. It does NOT
independently prove a human listened or that the YouTube upload succeeded.
No private manifest or evidence packet should be committed to GitHub.
"""
from __future__ import annotations

import re

from release_naming import validate_manifest

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RULES = {str(i) for i in range(1, 110)}
STORY = {f"{i:02d}" for i in range(1, 17)}
AUDIO_WEIGHTS = {
    "naturalness": .25,
    "word_and_name_fidelity": .20,
    "emotional_fit_dialogue": .20,
    "timbre_and_comfort": .15,
    "pacing": .10,
    "technical_mastering": .10,
}
QUALITY = {
    "canon_and_story_fidelity", "opening_hook_and_listening_clarity",
    "plot_stakes_and_payoffs", "dialogue_and_character_distinction",
    "voice_pronunciation_and_pacing", "full_episode_audio_mix",
    "single_cover_rights_and_legibility", "encoded_mp4_and_metadata",
}
HOLDS = {
    "story_and_bible", "independent_literary_and_originality",
    "voice_names_and_full_audio", "visual_and_final_mp4",
    "owner_final_publication_approval",
}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def filled(value):
    return isinstance(value, str) and bool(value.strip())

def sha(value):
    return isinstance(value, str) and bool(HEX64.fullmatch(value))

def exact(value, keys, label):
    need(isinstance(value, dict) and set(value) == keys,
         label + ": missing or unexpected records")

def review(item, label, *, permit_supersession=False):
    need(isinstance(item, dict), label + ": missing review")
    for key in ("reviewer", "evidence", "reviewed_at"):
        need(filled(item.get(key)), label + ": missing " + key)
    if item.get("status") == "pass":
        return
    if permit_supersession and item.get("status") in ("superseded", "not_applicable"):
        need(item.get("owner_exception_approved") is True and
             filled(item.get("owner_approval_reference")) and
             filled(item.get("reason")),
             label + ": supersession needs specific owner approval and evidence")
        return
    raise ValueError(label + ": not passed")

def validate_audio_first_packet(packet, *, postupload=False):
    need(isinstance(packet, dict) and packet.get("production_mode") == "audio_first",
         "AUDIO_FIRST_MODE_REQUIRED")
    need(packet.get("master_rules_version") == "1.1",
         "MASTER_RULES_VERSION_REQUIRED")
    manifest = packet.get("release_manifest")
    need(isinstance(manifest, dict) and manifest.get("production_mode") == "audio_first",
         "AUDIO_FIRST_RELEASE_MANIFEST_MODE_REQUIRED")
    identity = validate_manifest(manifest)

    reviews = packet.get("master_rule_reviews")
    exact(reviews, RULES, "109 rules")
    for key, entry in reviews.items():
        review(entry, "rule " + key, permit_supersession=True)

    story = packet.get("universal_story_scorecard_16")
    exact(story, STORY, "16 story criteria")
    for key, entry in story.items():
        need(isinstance(entry, dict), "story " + key + ": missing")
        score = entry.get("score")
        if score == "N/A":
            need(filled(entry.get("reason")) and
                 filled(entry.get("owner_approval_reference")) and
                 entry.get("owner_exception_approved") is True,
                 "story " + key + ": N/A must be owner-approved")
        else:
            need(type(score) in (int, float) and 8 <= score <= 10 and
                 filled(entry.get("scene_evidence")),
                 "story " + key + ": score or narrative evidence insufficient")
        need(filled(entry.get("reviewer")), "story " + key + ": reviewer missing")

    quality = packet.get("audio_first_quality_scorecard")
    exact(quality, QUALITY, "audio-first quality")
    for key, entry in quality.items():
        need(isinstance(entry, dict) and type(entry.get("score")) in (int, float)
             and 8 <= entry["score"] <= 10 and filled(entry.get("evidence"))
             and filled(entry.get("reviewer"))
             and filled(entry.get("signed_review_reference")),
             "AUDIO_FIRST_QUALITY_BLOCKED: " + key)

    audio = packet.get("full_episode_audio_review")
    need(isinstance(audio, dict) and filled(audio.get("human_reviewer"))
         and filled(audio.get("signed_review_reference")),
         "SIGNED_HUMAN_AUDIO_REVIEW_REQUIRED")
    for key in ("approved_script_sha256", "narration_audio_sha256"):
        need(sha(audio.get(key)), "AUDIO_REVIEW_HASH_MISSING: " + key)
    for key in ("entire_episode_listened", "headphones_tested",
                "phone_speaker_tested", "speech_script_fidelity_checked",
                "no_clipping_or_masked_words"):
        need(audio.get(key) is True, "AUDIO_REVIEW_BLOCKED: " + key)
    total = 0.0
    for key, weight in AUDIO_WEIGHTS.items():
        item = audio.get(key)
        need(isinstance(item, dict) and
             type(item.get("score")) in (int, float) and
             8 <= item["score"] <= 10 and filled(item.get("evidence")),
             "AUDIO_REVIEW_SCORE_BLOCKED: " + key)
        total += weight * item["score"]
    need(total >= 8.5, "AUDIO_WEIGHTED_SCORE_BLOCKED")

    music = packet.get("music_first_and_final_mix")
    need(isinstance(music, dict), "MUSIC_FIRST_EVIDENCE_REQUIRED")
    for key in ("preflight_receipt_sha256", "music_source_sha256"):
        need(sha(music.get(key)), "MUSIC_FIRST_HASH_MISSING: " + key)
    for key in ("preflight_receipt_reference", "rights_provenance_reference"):
        need(filled(music.get(key)), "MUSIC_RIGHTS_OR_PREFLIGHT_MISSING: " + key)
    for key in ("music_prepared_before_new_voice", "same_bed_verified_in_final_mix",
                "music_audible_on_phone_and_headphones",
                "voice_fully_intelligible_over_bed",
                "beginning_middle_end_music_spot_checks", "no_unintentional_music_gaps",
                "no_clipping_pumping_or_rough_music_loops"):
        need(music.get(key) is True, "AUDIO_MIX_BLOCKED: " + key)

    video = packet.get("final_video_review")
    need(isinstance(video, dict) and filled(video.get("human_reviewer"))
         and filled(video.get("review_reference")), "SIGNED_FINAL_MP4_REVIEW_REQUIRED")
    for key in ("final_mp4_sha256", "approved_thumbnail_sha256", "cover_image_sha256"):
        need(sha(video.get(key)), "FINAL_VIDEO_HASH_MISSING: " + key)
    need(audio["approved_script_sha256"] == video.get("approved_script_sha256") and
         audio["narration_audio_sha256"] == video.get("narration_audio_sha256"),
         "AUDIO_SCRIPT_VIDEO_HASH_MISMATCH")
    for key in ("watched_entire_encoded_mp4", "full_audio_and_static_cover_checked",
                "single_cover_consistent", "cover_and_thumbnail_rights_verified",
                "cover_legible_on_phone", "video_audio_streams_verified",
                "music_and_voice_checked", "approved_thumbnail_checked"):
        need(video.get(key) is True, "FINAL_AUDIO_FIRST_VIDEO_BLOCKED: " + key)
    voice_duration = video.get("narration_duration_ms")
    video_duration = video.get("video_duration_ms")
    need(type(voice_duration) is int and type(video_duration) is int and
         voice_duration > 0 and abs(video_duration - voice_duration) <= 1000,
         "FINAL_VIDEO_DURATION_MISMATCH")

    holds = packet.get("release_holds")
    exact(holds, HOLDS, "five release holds")
    for key, entry in holds.items():
        review(entry, "hold " + key)
    need(filled(holds["owner_final_publication_approval"].get("owner_approval_reference")),
         "EXPLICIT_OWNER_APPROVAL_REQUIRED")
    need(holds["independent_literary_and_originality"].get("independent_human_review") is True,
         "INDEPENDENT_HUMAN_REVIEW_REQUIRED")

    meta = packet.get("upload_metadata")
    need(isinstance(meta, dict), "UPLOAD_METADATA_REQUIRED")
    need(meta.get("title") == identity["youtube_title"],
         "UPLOAD_TITLE_MISMATCH")
    need(meta.get("description_headline") == identity["description_headline"],
         "UPLOAD_DESCRIPTION_MISMATCH")
    need(filled(meta.get("existing_series_playlist_id")), "PLAYLIST_ID_REQUIRED")
    for key in ("connector_title_field_mapping_verified",
                "correct_channel_session_verified", "playlist_insert_permission_verified"):
        need(meta.get(key) is True, "UPLOAD_BLOCKED: " + key)
    if postupload:
        live = packet.get("verified_live_youtube_metadata")
        need(isinstance(live, dict) and filled(live.get("video_id")),
             "LIVE_API_VERIFICATION_REQUIRED")
        need(live.get("title") == identity["youtube_title"], "LIVE_TITLE_MISMATCH")
        need(live.get("channel_id") == manifest["channel_id"],
             "LIVE_CHANNEL_MISMATCH")
        need(live.get("playlist_id") == meta["existing_series_playlist_id"] and
             live.get("playlist_item_video_id") == live["video_id"],
             "LIVE_PLAYLIST_MEMBERSHIP_NOT_VERIFIED")
        need(live.get("description_headline") == identity["description_headline"],
             "LIVE_DESCRIPTION_MISMATCH")
        need(live.get("approved_thumbnail_visually_verified") is True and
             filled(live.get("official_api_or_watch_page_evidence")),
             "LIVE_THUMBNAIL_OR_API_EVIDENCE_MISSING")
    return identity["youtube_title"]
