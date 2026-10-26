#!/usr/bin/env python3
"""Fail-closed CartoonStudio series production gate.

Checks actual model binaries, license/identity, active canonical speakers,
native speech performance evidence, source integration and preview approval.
No Kaggle call, no video render, no story or canon mutation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

REQUIRED = ("lelli", "brin", "odo", "tavi", "miko", "pippa", "nori", "kolo",
            "suri", "marn", "fen", "rumi", "bex", "luma", "zaza")
VALID_LICENSES = {"CC0-1.0", "CC-BY-4.0"}
BANNED = ("original_clay", "proposed_clay", "quaternius", "kaykit", "cuto",
          "cutemonster", "procedural", "prototype", "fallback", "low_poly",
          "low-poly")
HASH = re.compile(r"^[0-9a-f]{64}$")


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read_json(path: Path, errors: list[str], label: str):
    if not path.is_file():
        errors.append(f"MISSING_{label} {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError, OSError) as exc:
        errors.append(f"BAD_{label} {type(exc).__name__}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"BAD_{label}_OBJECT")
        return {}
    return value


def stage_checks(story, root, assets: Path, errors: list[str]):
    story_text = story.get("dialogue")
    char_map = story.get("characters")
    if not isinstance(char_map, dict) or not char_map:
        errors.append("MISSING_CANON_CHARACTERS")
        return set()
    if not isinstance(story_text, list) or not story_text:
        errors.append("MISSING_CANON_DIALOGUE")
        return set()
    speakers = set()
    for index, entry in enumerate(story_text, 1):
        if not isinstance(entry, dict) or not isinstance(entry.get("text"), str) or not entry["text"].strip():
            errors.append(f"MALFORMED_DIALOGUE_LINE {index}")
            continue
        speaker = entry.get("speaker")
        if speaker not in char_map:
            errors.append(f"UNKNOWN_DIALOGUE_SPEAKER {index}")
        else:
            speakers.add(speaker)
    if not speakers:
        errors.append("NO_ACTUAL_SPEAKERS")
    if set(char_map) - set(REQUIRED):
        errors.append("CANON_KEY_OUTSIDE_SERIES_CAST")
    records = root.get("characters")
    if not isinstance(records, dict):
        errors.append("MISSING_APPROVED_CAST_RECORDS")
        return speakers
    if set(records) != set(REQUIRED):
        errors.append(f"CAST_COUNT_AND_KEYS_INVALID expected={len(REQUIRED)} found={len(records)}")
    if not assets.is_dir():
        errors.append(f"ACTUAL_ASSET_DIRECTORY_MISSING {assets}")
        return speakers
    unique_hash = set()
    unique_files = set()
    for key in REQUIRED:
        item = records.get(key)
        if not isinstance(item, dict):
            errors.append(f"UNAPPROVED_MODEL {key}")
            continue
        filename = item.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            errors.append(f"MISSING_MODEL_PATH {key}")
            continue
        path = (assets / filename).resolve()
        if path == assets or assets not in path.parents or path.suffix.lower() not in (".blend", ".glb", ".gltf"):
            errors.append(f"INVALID_MODEL_FILE {key}")
            continue
        if not path.is_file() or path.stat().st_size < 500_000:
            errors.append(f"MISSING_OR_DEGRADED_ORIGINAL_MODEL {key}")
            continue
        if path in unique_files:
            errors.append(f"DUPLICATE_MODEL_PATH {key}")
        unique_files.add(path)
        declared = item.get("sha256", "")
        if not isinstance(declared, str) or not HASH.fullmatch(declared):
            errors.append(f"MISSING_PINNED_SHA256 {key}")
        else:
            actual = digest(path)
            if actual != declared:
                errors.append(f"SOURCE_BYTES_CHECKSUM_MISMATCH {key}")
            if declared in unique_hash:
                errors.append(f"DUPLICATE_MODEL_BINARY {key}")
            unique_hash.add(declared)
        description = " ".join(str(item.get(field, "")) for field in ("filename", "creator", "source"))
        if any(word in description.casefold() for word in BANNED):
            errors.append(f"REJECTED_LOW_DETAIL_OR_FALLBACK {key}")
        license_name = item.get("license")
        if license_name not in VALID_LICENSES:
            errors.append(f"UNVERIFIED_COMMERCIAL_LICENSE {key}")
        if not isinstance(item.get("source"), str) or not item["source"].startswith("https://"):
            errors.append(f"UNVERIFIED_OFFICIAL_SOURCE {key}")
        if not isinstance(item.get("creator"), str) or not item["creator"].strip():
            errors.append(f"MISSING_ARTIST {key}")
        if license_name == "CC-BY-4.0" and not item.get("attribution"):
            errors.append(f"MISSING_CC_BY_CREDIT {key}")
        review = item.get("visual_review", {})
        if not isinstance(review, dict) or review.get("approved_by_user") is not True:
            errors.append(f"UNAPPROVED_IDENTITY_AND_MODEL {key}")
        tech = item.get("technical_audit", {})
        if not isinstance(tech, dict):
            errors.append(f"MISSING_NATIVE_TECHNICAL_AUDIT {key}")
            continue
        if tech.get("rig_bones", 0) < 20 or tech.get("faces", 0) < 9000:
            errors.append(f"INADEQUATE_ORIGINAL_SKINNED_RIG {key}")
        if key in speakers:
            if tech.get("speaking_face_test_passed") is not True:
                errors.append(f"UNVERIFIED_SPEAKING_FACE {key}")
            if tech.get("wav_viseme_alignment_passed") is not True:
                errors.append(f"UNVERIFIED_DIALOGUE_WAV_ALIGNMENT {key}")
            if tech.get("rendered_speech_review_approved") is not True:
                errors.append(f"UNAPPROVED_SPEAKING_PERFORMANCE {key}")
    missing_speakers = speakers - set(records)
    if missing_speakers:
        errors.append("MISSING_STORY_SPEAKERS_IN_CAST " + ",".join(sorted(missing_speakers)))
    return speakers


def readiness(story_path: Path, manifest_path: Path, assets: Path, mode: str,
              integration_path: Path, approval_path: Path | None = None,
              preview_mp4: Path | None = None):
    errors = []
    story, manifest = (read_json(story_path, errors, "STORY"),
                       read_json(manifest_path, errors, "APPROVED_CAST_MANIFEST"))
    story_hash = digest(story_path) if story_path.is_file() else None
    cast_hash = digest(manifest_path) if manifest_path.is_file() else None
    active = stage_checks(story, manifest, assets.resolve(), errors)
    integration = read_json(integration_path, errors, "RENDERER_INTEGRATION")
    if integration.get("production_native_import_passed") is not True:
        errors.append("PRODUCTION_RENDERER_NATIVE_IMPORT_NOT_TESTED")
    if integration.get("no_procedural_or_clay_fallback") is not True:
        errors.append("PRODUCTION_RENDERER_FALLBACK_NOT_DISABLED")
    if integration.get("all_story_speakers_mapped_to_mounted_assets") is not True:
        errors.append("RENDERER_STORY_TO_REAL_FILE_MAPPING_INCOMPLETE")
    if integration.get("single_shot_audio_subtitles_sync_verified") is not True:
        errors.append("SPEECH_AUDIO_SUBTITLE_SYNCHRONIZATION_NOT_PROVEN")
    if integration.get("actual_1280x720_24fps_render_quality_reviewed") is not True:
        errors.append("TARGET_OUTPUT_VISUAL_REVIEW_NOT_APPROVED")
    if integration.get("story_sha256") != story_hash:
        errors.append("RENDERER_TEST_NOT_BOUND_TO_EXACT_STORY")
    if integration.get("cast_sha256") != cast_hash:
        errors.append("RENDERER_TEST_NOT_BOUND_TO_EXACT_CAST")
    if mode == "full":
        if approval_path is None:
            errors.append("FULL_RENDER_REQUIRES_EXPLICIT_PREVIEW_APPROVAL_FILE")
        else:
            approval = read_json(approval_path, errors, "PREVIEW_APPROVAL")
            if approval.get("approved_by_user") is not True or not str(approval.get("approved_by", "")).strip():
                errors.append("NO_RECORDED_USER_PREVIEW_APPROVAL")
            if approval.get("story_sha256") != story_hash or approval.get("cast_sha256") != cast_hash:
                errors.append("PREVIEW_APPROVED_FOR_DIFFERENT_STORY_OR_CAST")
            if not isinstance(approval.get("preview_run_id"), int) or approval["preview_run_id"] <= 0:
                errors.append("NO_VERIFIABLE_PREVIEW_RUN_ID")
            if preview_mp4 is None or not preview_mp4.is_file():
                errors.append("REVIEWED_PREVIEW_MP4_MISSING")
            else:
                observed = digest(preview_mp4)
                if not HASH.fullmatch(str(approval.get("preview_sha256", ""))) or approval["preview_sha256"] != observed:
                    errors.append("PREVIEW_VIDEO_CONTENT_MISMATCH")
                if preview_mp4.stat().st_size < 50_000:
                    errors.append("PREVIEW_VIDEO_TOO_SMALL")
    return {
        "status": "READY" if not errors else "BLOCKED",
        "production_ready": not errors,
        "render_authorized": False,  # This script never authorizes a run by itself.
        "request_mode": mode,
        "story_sha256": story_hash,
        "cast_sha256": cast_hash,
        "active_speakers": sorted(active),
        "original_dialogue_lines": len(story.get("dialogue", [])) if isinstance(story.get("dialogue"), list) else 0,
        "blocking_issues": sorted(set(errors)),
        "no_kaggle_or_video_render_started": True,
        "series_canon_changed": False,
    }


def self_test():
    import copy
    with tempfile.TemporaryDirectory() as folder:
        d = Path(folder)
        story = d / "story.json"
        cast = d / "cast.json"
        integration = d / "renderer.json"
        assets = d / "assets"
        assets.mkdir()
        story.write_text(json.dumps({"characters": {"lelli": {}},
                                      "dialogue": [{"speaker": "lelli", "text": "Original line."}]}))
        # Sufficient synthetic binaries for *gate logic* only, not fake real-source production.
        actors = {}
        for index, key in enumerate(REQUIRED):
            content = bytes([index+1]) * 500_001
            filename = f"actor_{index}.glb"
            (assets / filename).write_bytes(content)
            actors[key] = {
                "filename": filename, "sha256": hashlib.sha256(content).hexdigest(),
                "license": "CC0-1.0", "creator": "Fixture only",
                "source": "https://example.org/original-fixture", "visual_review": {"approved_by_user": True},
                "technical_audit": {"rig_bones": 21, "faces": 9001,
                    "speaking_face_test_passed": True,
                    "wav_viseme_alignment_passed": True,
                    "rendered_speech_review_approved": True}}
        cast.write_text(json.dumps({"characters": actors}))
        good_integration = {"production_native_import_passed": True,
            "no_procedural_or_clay_fallback": True,
            "all_story_speakers_mapped_to_mounted_assets": True,
            "single_shot_audio_subtitles_sync_verified": True,
            "actual_1280x720_24fps_render_quality_reviewed": True,
            "story_sha256": digest(story), "cast_sha256": digest(cast)}
        integration.write_text(json.dumps(good_integration))
        assert readiness(story, cast, assets, "preview", integration)["status"] == "READY"
        assert readiness(story, cast, assets, "full", integration)["status"] == "BLOCKED"
        no_preview = readiness(story, cast, assets, "full", integration)
        assert "FULL_RENDER_REQUIRES_EXPLICIT_PREVIEW_APPROVAL_FILE" in no_preview["blocking_issues"]
        broken = copy.deepcopy(actors)
        broken["lelli"]["technical_audit"]["wav_viseme_alignment_passed"] = False
        cast.write_text(json.dumps({"characters": broken}))
        assert "UNVERIFIED_DIALOGUE_WAV_ALIGNMENT lelli" in readiness(
            story, cast, assets, "preview", integration)["blocking_issues"]
        cast.write_text(json.dumps({"characters": actors}))
        (assets / actors["brin"]["filename"]).write_bytes(b"broken")
        assert "MISSING_OR_DEGRADED_ORIGINAL_MODEL brin" in readiness(
            story, cast, assets, "preview", integration)["blocking_issues"]
        actors["lelli"]["filename"] = "../outside.blend"
        cast.write_text(json.dumps({"characters": actors}))
        assert "INVALID_MODEL_FILE lelli" in readiness(
            story, cast, assets, "preview", integration)["blocking_issues"]
    print("PASS: fail-closed source hashes, full approval, dialogue visemes, path traversal and missing asset tests")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--story", type=Path, default=Path("video/story.json"))
    p.add_argument("--manifest", type=Path, default=Path("video/professional-cast-approved.json"))
    p.add_argument("--assets", type=Path, default=Path("video/professional-approved-assets"))
    p.add_argument("--renderer", type=Path, default=Path("video/professional-renderer-evidence.json"))
    p.add_argument("--mode", choices=("preview", "full"), default="preview")
    p.add_argument("--preview-approval", type=Path)
    p.add_argument("--preview-mp4", type=Path)
    p.add_argument("--output", type=Path, default=Path("artifacts/cartoonstudio-production-readiness.json"))
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    report = readiness(args.story, args.manifest, args.assets, args.mode,
                       args.renderer, args.preview_approval, args.preview_mp4)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print("CARTOONSTUDIO_PRODUCTION_" + report["status"], len(report["blocking_issues"]))
    for issue in report["blocking_issues"]:
        print("BLOCKER", issue)
    if report["status"] != "READY":
        raise SystemExit(2)
    print("PREVIEW_INPUTS_VALIDATED_NO_RENDER_STARTED")


if __name__ == "__main__":
    main()
