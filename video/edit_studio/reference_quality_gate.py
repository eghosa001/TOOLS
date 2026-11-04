#!/usr/bin/env python3
"""Reference-led editing quality gate. Human judgement is required at release.

Schema v2 of universal_edit adds reference craft/shot design; schema v1 remains
legacy-compatible. Neither scoring nor a tutorial proves a reference was watched.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

STORY_BEATS = {"hook", "setup", "escalation", "reveal", "payoff", "resolution"}
TRANSITIONS = {
    "straight_cut", "motivated_match_cut", "hold", "masked_reveal",
    "velocity_ramp", "whip_pan", "dissolve", "flash", "other",
}
INSPECTION_LEVELS = {"metadata_only", "description_or_transcript",
                     "tutorial_reviewed", "frames_and_audio_reviewed"}
SCORES = (
    "hook", "narrative_payoff", "shot_selection", "rhythm",
    "motivated_motion_and_effects", "color_and_subject_clarity",
    "dialogue_music_foley", "mobile_readability", "original_contribution",
)


class ReferenceQualityError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise ReferenceQualityError(message)


def words(value, minimum, label):
    need(isinstance(value, str) and len(value.strip().split()) >= minimum,
         f"{label}: need {minimum} descriptive words")


def is_https(value):
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)


def valid_date(value):
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_reference_profile(manifest, phase="plan"):
    """Validate a substantive reference style plan, then signed human export review.

    Only new schema_version=2 productions require this. Do not apply v2 results
    retrospectively to a v1 asset. For new work the authoring rules require v2.
    """
    need(phase in {"plan", "release"}, "unknown reference QA phase")
    if manifest.get("schema_version") == 1:
        return {"reference_gate": "legacy_v1_no_reference_profile"}
    need(manifest.get("schema_version") == 2, "unsupported edit manifest schema version")
    p = manifest.get("reference_profile")
    need(isinstance(p, dict), "v2 requires reference_profile")
    need(p.get("no_ai_generated_assets") is True,
         "No AI-generated visuals, voices, music, or synthetic insert assets in reference-led edits")
    need(p.get("output_format") in {"short_vertical", "long_landscape", "long_vertical"},
         "Output aspect/delivery format must be chosen")
    for field in ("editorial_premise", "opening_hook", "turning_point", "final_payoff",
                  "emotional_or_comedic_intent", "style_difference_from_references"):
        words(p.get(field), 5, field)

    refs = p.get("reference_evidence")
    need(isinstance(refs, list) and len(refs) >= 2,
         "At least two specific and distinct reference links required")
    seen = set()
    directly_reviewed = 0
    for n, ref in enumerate(refs, 1):
        need(isinstance(ref, dict), f"reference {n}: invalid")
        url = ref.get("url")
        need(is_https(url) and url not in seen, f"reference {n}: distinct HTTPS source required")
        seen.add(url)
        words(ref.get("creator"), 1, f"reference {n} creator")
        words(ref.get("source_title"), 2, f"reference {n} title")
        words(ref.get("specific_observation"), 8, f"reference {n} observation")
        need(ref.get("inspection_level") in INSPECTION_LEVELS,
             f"reference {n}: evidence level must distinguish metadata from actual viewing")
        need(valid_date(ref.get("checked_on")), f"reference {n}: checked_on ISO date required")
        if ref["inspection_level"] == "frames_and_audio_reviewed":
            samples = ref.get("timestamp_samples")
            need(isinstance(samples, list) and len(samples) >= 3,
                 f"reference {n}: actual visual/audio check needs >=3 timestamp observations")
            previous = -1.0
            for s in samples:
                need(isinstance(s, dict), f"reference {n}: invalid timestamp sample")
                t = s.get("time_sec")
                need(type(t) in (int, float) and t >= 0 and t > previous,
                     f"reference {n}: timestamps must be strictly increasing")
                previous = t
                words(s.get("on_screen_and_sound"), 7,
                      f"reference {n} at {t}s observed image/audio")
            directly_reviewed += 1
    beats = p.get("beat_map")
    need(isinstance(beats, list) and len(beats) >= 3, "Need >=3 authored narrative/audio beats")
    last_time = -1.0
    types = set()
    for i, beat in enumerate(beats, 1):
        need(isinstance(beat, dict), f"beat {i}: invalid")
        t = beat.get("at_sec")
        need(type(t) in (int, float) and t > last_time and t >= 0,
             f"beat {i}: output time must strictly increase")
        last_time = t
        name = beat.get("type")
        need(name in STORY_BEATS, f"beat {i}: unknown narrative phase")
        types.add(name)
        words(beat.get("viewer_reason"), 5, f"beat {i} audience purpose")
        words(beat.get("sound_and_picture"), 5, f"beat {i} visual/audio cue")
    need("hook" in types and "payoff" in types, "Opening hook and ending payoff are mandatory")
    need(beats[0]["at_sec"] <= 1.5, "First meaningful visual/audio beat must arrive by 1.5s")

    shots = p.get("shot_craft")
    timeline = manifest.get("timeline", [])
    need(isinstance(shots, list) and len(shots) == len(timeline) and bool(shots),
         "Every selected shot requires its own focused craft decision")
    for i, shot in enumerate(shots, 1):
        need(isinstance(shot, dict) and shot.get("shot_index") == i,
             f"shot craft {i}: must match source timeline ordering")
        need(shot.get("transition") in TRANSITIONS, f"shot craft {i}: transition not specified")
        for field in ("subject_and_eye_trace", "visible_action", "cut_motivation",
                      "motion_continuity", "audio_layer_plan", "on_screen_text_plan"):
            words(shot.get(field), 3, f"shot craft {i} {field}")
        need(shot.get("scene_payoff_protected") is True,
             f"shot craft {i}: preserve meaningful source action/reaction")

    mix = p.get("sound_design", {})
    need(isinstance(mix, dict), "sound_design must be an object")
    for field in ("dialogue_priority", "music_entry_and_exit",
                  "impact_and_foley", "anti_clipping_and_silence"):
        words(mix.get(field), 5, f"sound_design {field}")

    if phase == "release":
        need(directly_reviewed >= 1,
             "Release requires at least one reference actually viewed and listened to with timestamps")
        review = p.get("human_reference_comparison")
        need(isinstance(review, dict), "Human reference-to-export comparison required")
        for field in ("watched_entire_export", "listened_to_entire_export",
                      "side_by_side_reference_compared", "small_screen_safe_areas_checked",
                      "no_black_flashes_or_audio_clicks", "no_ai_assets_verified"):
            need(review.get(field) is True, f"human_reference_comparison.{field} must be checked")
        words(review.get("reviewer"), 2, "reviewer identity")
        need(valid_date(review.get("reviewed_on")), "review date required")
        need(review.get("reviewed_output_sha256") == manifest.get("output", {}).get("sha256")
             and isinstance(review.get("reviewed_output_sha256"), str)
             and len(review["reviewed_output_sha256"]) == 64,
             "Reference comparison must sign exact exported MP4 SHA256")
        scores = review.get("scores")
        need(isinstance(scores, dict), "Manual nine-part craft scorecard required")
        for criterion in SCORES:
            score = scores.get(criterion)
            need(type(score) in (int, float) and 8.5 <= score <= 10,
                 f"manual {criterion} score must meet 8.5/10; revise, do not publish")
        words(review.get("comparison_notes"), 12,
              "specific differences, flaws and adjustments after actual comparison")
    return {"reference_gate": "passed", "reference_count": len(refs),
            "actual_video_audio_references_reviewed": directly_reviewed,
            "scored_from_real_export": phase == "release"}
