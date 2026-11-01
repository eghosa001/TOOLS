#!/usr/bin/env python3
"""Fail-closed, scene-by-scene sound/picture parity gate for ASMR publication.

No waveform or filename can prove semantic sound synchronization. This validator
requires verifiable recorded-source hashes AND an actual editor's timecoded,
exact-export, full-headphone audiovisual observations before any release.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
RIGHTS = {"original", "CC0", "CC BY 4.0", "CC BY-SA 4.0",
          "CC BY 3.0", "Pexels License", "Pixabay Content License",
          "Mixkit Stock Video Free License"}
INTENSITY = {"delicate", "gentle", "moderate", "forceful", "impact"}


class SceneParityError(ValueError):
    pass


def demand(ok: bool, message: str) -> None:
    if not ok:
        raise SceneParityError("STOP: ASMR scene/sound parity: " + message)


def descriptive(value, minimum=24) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def path_in_project(root: Path, relative: str) -> Path:
    demand(isinstance(relative, str) and relative.strip(), "audio source path required")
    path = Path(relative)
    demand(not path.is_absolute() and ".." not in path.parts,
           "audio source must be a relative project file")
    candidate = (root / path).resolve()
    demand(candidate.is_relative_to(root.resolve()), "audio source escapes project folder")
    demand(candidate.is_file() and candidate.stat().st_size > 0,
           "audio source missing or empty: " + relative)
    return candidate


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_scene_audio_parity(plan: dict, root: Path, master_sha: str,
                                scan_sha: str) -> int:
    """Validate exact-master editor-authored AV proof for *every* planned shot.

    This is a REQUIRED supplement to quality_gate's full master listening and
    shot/contact review. It checks honesty/completeness of evidence, not whether
    a video sounds nice; human audition is still an indispensable prerequisite.
    """
    review = plan.get("final_review")
    demand(isinstance(review, dict), "missing final_review")
    report = review.get("scene_audio_parity")
    demand(isinstance(report, dict) and report.get("schema_version") == 1,
           "scene_audio_parity v1 evidence missing")
    demand(report.get("approved") is True and report.get("unresolved_issues") == [],
           "scene parity not approved or unresolved mismatches remain")
    demand(report.get("reviewed_master_sha256") == master_sha
           and bool(SHA256.fullmatch(master_sha)),
           "parity review not bound to EXACT final MP4 SHA256")
    demand(report.get("reviewed_av_scan_sha256") == scan_sha,
           "parity review not bound to EXACT post-render AV scan")
    demand(descriptive(report.get("reviewer"), 2)
           and descriptive(report.get("review_method"), 35),
           "identify genuine reviewer and full playback/listening method")
    for field in ("full_video_watched", "full_audio_listened_on_headphones",
                  "reviewed_after_last_picture_edit", "reviewed_after_last_audio_edit"):
        demand(report.get(field) is True,
               field + " must be true after reviewing exact locked master")
    demand(descriptive(report.get("whole_film_observations"), 75),
           "document observed overall continuity, cut timing, sonic dynamics and mismatches")

    recordings = report.get("sound_sources")
    demand(isinstance(recordings, list) and recordings,
           "identify and hash every source recording used in scene sound")
    ids = set()
    for n, item in enumerate(recordings, 1):
        demand(isinstance(item, dict), f"source {n} invalid")
        source_id = item.get("id")
        demand(descriptive(source_id, 3) and source_id not in ids,
               f"source {n} ID missing or duplicated")
        ids.add(source_id)
        require_hash = item.get("sha256")
        demand(isinstance(require_hash, str) and SHA256.fullmatch(require_hash),
               f"source {source_id}: complete SHA256 required")
        actual = path_in_project(root, item.get("file"))
        demand(file_sha256(actual) == require_hash,
               f"source {source_id}: recording has changed or source was not recovered")
        demand(item.get("license") in RIGHTS,
               f"source {source_id}: individually verified commercial license required")
        url = item.get("source_url")
        demand(isinstance(url, str) and (url.startswith("https://")
               or (item.get("license") == "original" and url.startswith("studio://"))),
               f"source {source_id}: original, auditable rights/source link required")
        demand(descriptive(item.get("recorded_material"), 4)
               and descriptive(item.get("recorded_action"), 8)
               and descriptive(item.get("recorded_environment"), 5),
               f"source {source_id}: actual recorded material/action/environment required")

    shots = plan.get("manually_directed_shots")
    scenes = report.get("scene_checks")
    demand(isinstance(shots, list) and bool(shots) and isinstance(scenes, list)
           and len(scenes) == len(shots),
           "one scene-specific audio review is required for EVERY planned shot")
    total = 0
    previous_end = 0
    for index, (shot, scene) in enumerate(zip(shots, scenes), 1):
        prefix = f"scene {index}"
        demand(isinstance(scene, dict) and scene.get("scene_index") == index,
               f"{prefix}: wrong/missing timecoded review")
        start, end = shot["start_seconds"], shot["end_seconds"]
        sf, ef = round(float(start) * 24), round(float(end) * 24)
        demand(scene.get("start_frame") == sf and scene.get("end_frame") == ef
               and sf == previous_end and ef > sf,
               f"{prefix}: review does not cover exact final video frames")
        previous_end = ef
        for field in ("visible_material", "visible_action", "visual_environment",
                      "actual_audio_material", "actual_audio_action", "audio_environment"):
            demand(descriptive(scene.get(field), 6),
                   f"{prefix}: missing real visual or audible {field}")
        bed_ids = scene.get("sound_source_ids")
        demand(isinstance(bed_ids, list) and bool(bed_ids)
               and all(isinstance(sid, str) and sid in ids for sid in bed_ids),
               f"{prefix}: missing/unverifiable recorded audio bed/foley identity")
        for flag in ("reviewed_picture_and_sound_together", "material_match",
                     "environment_match", "intensity_match", "no_unmatched_audible_events",
                     "audio_reviewed_after_effects"):
            demand(scene.get(flag) is True, f"{prefix}: failed or missing {flag}")
        for field, minimum in (
            ("audible_texture_observations", 45),
            ("rain_or_action_intensity_observations", 45),
            ("audio_mix_and_perspective_notes", 45),
            ("sync_and_transition_notes", 45),
        ):
            demand(descriptive(scene.get(field), minimum),
                   f"{prefix}: actual headphone/visual observations needed for {field}")
        if index > 1:
            demand(descriptive(scene.get("transition_vs_previous"), 40),
                   f"{prefix}: review actual audio and visual transition from prior shot")

        if scene.get("visual_effects_affect_sound") is True:
            demand(descriptive(scene.get("effect_sound_reevaluation_notes"), 55),
                   f"{prefix}: newly generated rain/visual action must be re-auditioned")
            demand(scene.get("effect_sound_reevaluation_passed") is True,
                   f"{prefix}: prior soundtrack does not auto-approve new visual effects")
        elif scene.get("visual_effects_affect_sound") is not False:
            raise SceneParityError("STOP: ASMR scene/sound parity: "
                                   f"{prefix}: visual effects sound relevance not evaluated")

        visible = scene.get("salient_visible_events")
        cues = scene.get("synchronized_sound_events")
        demand(isinstance(visible, list) and isinstance(cues, list),
               f"{prefix}: declare visible salient events and mapped audible events")
        demand(len(visible) == len(set(visible)) and all(descriptive(i, 3) for i in visible),
               f"{prefix}: event IDs invalid/duplicated")
        demand(len(visible) == len(cues),
               f"{prefix}: unmatched visible splash, drip, touch, impact or traffic event")
        actual_ids = set()
        for n, cue in enumerate(cues, 1):
            demand(isinstance(cue, dict), f"{prefix}: cue {n} malformed")
            event_id = cue.get("event_id")
            demand(event_id in visible and event_id not in actual_ids,
                   f"{prefix}: cue {n} not mapped to distinct visible event")
            actual_ids.add(event_id)
            vs, onset = cue.get("visual_frame"), cue.get("audio_onset_frame")
            demand(type(vs) is int and type(onset) is int
                   and sf <= vs < ef and sf <= onset < ef and abs(vs - onset) <= 1,
                   f"{prefix}: cue {event_id} exceeds ONE-FRAME audio/video tolerance")
            demand(cue.get("sound_source_id") in bed_ids,
                   f"{prefix}: cue {event_id} lacks original recorded source")
            demand(descriptive(cue.get("visible_event"), 10)
                   and descriptive(cue.get("heard_event"), 10),
                   f"{prefix}: cue {event_id} has no described witnessed contact/audio")
            for flag in ("material_match", "force_match", "auditioned_with_picture"):
                demand(cue.get(flag) is True, f"{prefix}: cue {event_id} failed {flag}")
            demand(cue.get("visual_intensity") in INTENSITY
                   and cue.get("visual_intensity") == cue.get("audible_intensity"),
                   f"{prefix}: cue {event_id} mismatched loudness/force")
            demand(descriptive(cue.get("review_notes"), 35),
                   f"{prefix}: cue {event_id} lacks real audiovisual audition notes")
            total += 1

        if not visible:
            demand(descriptive(scene.get("no_distinct_audible_events_reason"), 55),
                   f"{prefix}: explain why continuous ambience has no salient synced event")
            demand(scene.get("ambient_only_suitable") is True,
                   f"{prefix}: generic ambient rain cannot replace material-specific contact")
    return total
