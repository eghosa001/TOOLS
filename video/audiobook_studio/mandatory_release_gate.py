#!/usr/bin/env python3
"""Fail-closed evidence gate for the 109 mandatory rules and 16 story criteria.

This validates supplied evidence, not the truth of a human review.
The private packet and owner approval must never be committed to GitHub.
"""
import argparse
import json
import re
from pathlib import Path
from release_naming import validate_manifest

RULES = {str(i) for i in range(1, 110)}
SCORES = {f"{i:02d}" for i in range(1, 17)}
WEIGHTS = {"naturalness": .25, "word_and_name_fidelity": .20,
           "emotional_fit_dialogue": .20, "timbre_and_comfort": .15,
           "pacing": .10, "technical_mastering": .10}
HOLDS = {"story_and_bible", "independent_literary_and_originality",
         "voice_names_and_full_audio", "visual_and_final_mp4",
         "owner_final_publication_approval"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def exact_keys(value, expected, label):
    require(isinstance(value, dict) and set(value) == expected,
            f"{label}: missing or unexpected records")


def checked_review(item, label, exceptions=False):
    require(isinstance(item, dict), f"{label}: missing review")
    for key in ("reviewer", "evidence", "reviewed_at"):
        require(nonempty(item.get(key)), f"{label}: missing {key}")
    if item.get("status") == "pass":
        return
    if exceptions and item.get("status") in ("not_applicable", "superseded"):
        require(nonempty(item.get("reason")) and
                nonempty(item.get("owner_approval_reference")) and
                item.get("owner_exception_approved") is True,
                f"{label}: exception requires explicit owner approval and reason")
        return
    raise ValueError(f"{label}: not passed")


def validate_packet(packet, *, postupload=False):
    require(isinstance(packet, dict) and packet.get("master_rules_version") == "1.1",
            "MASTER_RULES_VERSION_REQUIRED")
    identity = validate_manifest(packet.get("release_manifest"))
    rules = packet.get("master_rule_reviews")
    exact_keys(rules, RULES, "109 rules")
    for num in range(1, 110):
        checked_review(rules[str(num)], f"rule {num}", exceptions=True)

    scorecard = packet.get("universal_story_scorecard_16")
    exact_keys(scorecard, SCORES, "16 story criteria")
    for num in sorted(SCORES):
        item = scorecard[num]
        require(isinstance(item, dict), f"story {num}: review missing")
        score = item.get("score")
        if score == "N/A":
            require(nonempty(item.get("reason")) and
                    nonempty(item.get("owner_approval_reference")) and
                    item.get("owner_exception_approved") is True,
                    f"story {num}: N/A needs specific reason and explicit owner approval")
        else:
            require(type(score) in (int, float) and 8 <= score <= 10,
                    f"story {num}: score must be >=8")
            require(nonempty(item.get("scene_evidence")),
                    f"story {num}: specific scene evidence required")
        require(nonempty(item.get("reviewer")),
                f"story {num}: named reviewer required")

    audio = packet.get("full_episode_audio_review")
    require(isinstance(audio, dict), "FULL_AUDIO_REVIEW_REQUIRED")
    require(nonempty(audio.get("human_reviewer")) and
            nonempty(audio.get("signed_review_reference")), "SIGNED_HUMAN_AUDIO_REVIEW_REQUIRED")
    for field in ("entire_episode_listened", "headphones_tested", "phone_speaker_tested",
                  "speech_script_fidelity_checked", "no_clipping_or_masked_words"):
        require(audio.get(field) is True, "AUDIO_REVIEW_BLOCKED: " + field)
    total = 0
    for name, weight in WEIGHTS.items():
        item = audio.get(name)
        require(isinstance(item, dict), f"audio {name}: evidence missing")
        score = item.get("score")
        require(type(score) in (int, float) and 8 <= score <= 10 and
                nonempty(item.get("evidence")), f"audio {name}: score/evidence insufficient")
        total += score * weight
    require(total >= 8.5, f"AUDIO_WEIGHTED_SCORE_BLOCKED: {total:.2f} < 8.5")

    video = packet.get("final_video_review")
    require(isinstance(video, dict), "FINAL_VIDEO_REVIEW_REQUIRED")
    require(nonempty(video.get("human_reviewer")) and
            nonempty(video.get("review_reference")), "SIGNED_FINAL_VIDEO_REVIEW_REQUIRED")
    for field in ("final_mp4_sha256", "approved_thumbnail_sha256"):
        require(bool(re.fullmatch(r"[0-9a-f]{64}", str(video.get(field, "")))),
                "MISSING_HASH: " + field)
    for field in ("watched_entire_encoded_mp4", "source_accurate_images",
                  "full_color_artwork", "character_and_prop_continuity",
                  "scene_to_audio_alignment", "music_and_voice_checked",
                  "licensed_assets_verified", "approved_thumbnail_checked"):
        require(video.get(field) is True, "FINAL_VIDEO_BLOCKED: " + field)

    holds = packet.get("release_holds")
    exact_keys(holds, HOLDS, "five release holds")
    for name in sorted(HOLDS):
        checked_review(holds[name], "hold " + name)
    require(nonempty(holds["owner_final_publication_approval"].get("owner_approval_reference")),
            "EXPLICIT_OWNER_APPROVAL_REQUIRED")
    require(holds["independent_literary_and_originality"].get("independent_human_review") is True,
            "INDEPENDENT_HUMAN_REVIEW_REQUIRED")

    metadata = packet.get("upload_metadata")
    require(isinstance(metadata, dict), "UPLOAD_METADATA_REQUIRED")
    require(metadata.get("title") == identity["youtube_title"],
            "UPLOAD_TITLE_MISMATCH: description is not the approved title")
    require(metadata.get("description_headline") == identity["description_headline"],
            "UPLOAD_DESCRIPTION_MISMATCH")
    require(nonempty(metadata.get("existing_series_playlist_id")),
            "PLAYLIST_ID_REQUIRED")
    for field in ("connector_title_field_mapping_verified",
                  "correct_channel_session_verified", "playlist_insert_permission_verified"):
        require(metadata.get(field) is True, "UPLOAD_BLOCKED: " + field)

    if postupload:
        live = packet.get("verified_live_youtube_metadata")
        require(isinstance(live, dict), "LIVE_API_VERIFICATION_REQUIRED")
        require(nonempty(live.get("video_id")), "LIVE_VIDEO_ID_REQUIRED")
        require(live.get("title") == identity["youtube_title"],
                "LIVE_TITLE_MISMATCH: repair existing video, do not reupload")
        require(live.get("channel_id") == packet["release_manifest"]["channel_id"],
                "LIVE_CHANNEL_MISMATCH")
        require(live.get("playlist_id") == metadata["existing_series_playlist_id"] and
                live.get("playlist_item_video_id") == live["video_id"],
                "LIVE_PLAYLIST_MEMBERSHIP_NOT_VERIFIED")
        require(live.get("description_headline") == identity["description_headline"],
                "LIVE_DESCRIPTION_MISMATCH")
        require(live.get("approved_thumbnail_visually_verified") is True and
                nonempty(live.get("official_api_or_watch_page_evidence")),
                "LIVE_THUMBNAIL_OR_API_EVIDENCE_MISSING")
    return identity["youtube_title"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("private_packet", type=Path)
    p.add_argument("--phase", choices=("preupload", "postupload"), default="preupload")
    args = p.parse_args()
    try:
        packet = json.loads(args.private_packet.read_text(encoding="utf-8"))
        name = validate_packet(packet, postupload=args.phase == "postupload")
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        p.exit(2, f"PUBLICATION_BLOCKED: {error}\n")
    print("RELEASE_PACKET_PASS" if args.phase == "preupload" else "LIVE_RELEASE_VERIFIED", name)


if __name__ == "__main__":
    main()
