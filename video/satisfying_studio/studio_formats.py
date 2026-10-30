#!/usr/bin/env python3
"""CGI-only 47-format ASMR studio planner and source-quality preflight.

The STUDIO sources and builds all original Blender geometry and licensed Foley.
The user supplies no filming, speech, recordings or images. This planner does
NOT claim an unrendered CGI scene has passed material, frame or sound review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

CATALOGUE = Path(__file__).resolve().parent / "formats" / "catalogue.json"
PERMITTED_LICENSES = {"original", "CC0", "CC BY 4.0", "Pexels License"}
MEDIA_ROLES = {"scene", "foley"}
MODES = {"blender"}
DELIVERABLES = {"preview", "short", "long"}


class StudioFormatError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def catalogue() -> dict:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        raise StudioFormatError("Unsupported format catalogue version")
    items = data.get("formats")
    if not isinstance(items, list) or len(items) != 47:
        raise StudioFormatError("Expected the 47 owner-requested studio formats")
    ids = [item["id"] for item in items]
    if len(set(ids)) != 47 or any(item["production_mode"] != "blender" or item.get("capture_policy") != "CGI_ONLY_NO_EXTERNAL_FOOTAGE" for item in items):
        raise StudioFormatError("Format IDs or production modes are invalid")
    return data


def get_format(format_id: str) -> dict:
    return next((f for f in catalogue()["formats"] if f["id"] == format_id), None) or _unknown(format_id)


def _unknown(name: str) -> dict:
    raise StudioFormatError("Unknown format: " + str(name))


def safe_file(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise StudioFormatError("Media file path is missing")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise StudioFormatError("Media path must be relative and contained within project")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise StudioFormatError("Media path escapes production project")
    return resolved


def _default_shot(f: dict, duration: int) -> dict:
    return {
        "start_seconds": 0,
        "end_seconds": duration,
        "material_family": f["material"],
        "visual_intent": "Original close-up design of " + f["material"] +
                         "; exact art direction and camera contact bounds must be approved",
        "movement": "One manually authored physical sequence: " + f["action"] +
                    "; use " + f["required_evidence_solver"] + " evidence",
        "sound_cue": "Audition and position " + f["foley"] + " at observed contact frames",
        "source_and_rights": "Studio authors original editable Blender scene and sources commercial-cleared Foley; "
                             "no user footage or user recordings required",
    }


def init_project(format_id: str, directory: Path, aspect: str = "9:16",
                 deliverable: str = "preview") -> Path:
    f = get_format(format_id)
    if aspect not in {"9:16", "16:9"}:
        raise StudioFormatError("Only 9:16 and 16:9 aspect ratios supported")
    if deliverable not in DELIVERABLES:
        raise StudioFormatError("Unsupported deliverable")
    directory = directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise StudioFormatError("Output directory is not empty; refusing to overwrite existing work")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "render").mkdir(exist_ok=True)
    pilot = 5
    data = {
        "format_id": f["id"],
        "format_catalogue_version": 2,
        "production_mode": f["production_mode"],
        "selected_asset_route": "scene",
        "media_policy": "CGI_ONLY",
        "assets_responsibility": "studio",
        "user_supplied_media_required": False,
        "required_evidence_solver": f["required_evidence_solver"],
        "delivery_intent": deliverable,
        "aspect_ratio": aspect,
        "delivery_aspect_ratio": aspect,
        "production_kind": "pilot",
        "planned_long_seconds": 600 if deliverable == "long" else None,
        "concept": "UNAPPROVED original " + f["title"] +
                   " test; replace this concept with a deliberately authored treatment",
        "duration_seconds": pilot,
        "fps": 24,
        "editorial_format": "single-material",
        "editorial_thesis": "One deliberate tactile transformation with audio matching its material",
        "material_family": f["material"],
        "manually_directed_shots": [_default_shot(f, pilot)],
        "asset_inventory": [],
        "physics_cache_manifest": "render/physics_bake_manifest.json",
        "preview_file": "render/preview_with_foley.mp4",
        "final_file": "render/finished_with_foley.mp4",
        "av_scan_file": "render/post_render_av_scan.json",
        "preview_review": {"approved": False},
        "final_review": {"approved": False},
        "production_state": "STUDIO_MUST_AUTHOR_CGI_AND_SOURCE_FOLEY",
    }
    manifest = directory / "production.json"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (directory / "NEXT_STEPS.txt").write_text(
        "CGI ONLY: " + f["title"] + "\\n"
        "The studio is responsible for scene, physics, lighting, framing and audio.\\n"
        "Do not ask the user to upload footage or sound.\\n"
        "1. Create the Blender scene via studio CGI authoring and save editable .blend.\\n"
        "2. Bake the appropriate physical simulation and inspect geometry/camera.\\n"
        "3. Source recorded, license-cleared Foley from the studio's CC0 cache or a\\n"
        "   verified free commercial-use archive; do NOT use random generic effects.\\n"
        "4. Record local scene and Foley hashes, provenance, and actual auditory review.\\n"
        "5. Run studio_formats.py check production.json; fix every failure internally.\\n"
        "6. Render 3-5s synchronized proof and perform full picture/headphone review.\\n"
        "7. Continue 8-12m and four Shorts only after real 9/10 review signoff.\\n"
        "8. The project is unapproved until the exact MP4 passes quality_gate release.\\n",
        encoding="utf-8",
    )
    return manifest


def inspect_assets(data: dict, root: Path) -> list[str]:
    """Return every actionable missing requirement; do not silently assume assets."""
    issues: list[str] = []
    try:
        f = get_format(data.get("format_id", ""))
    except StudioFormatError as exc:
        return [str(exc)]
    if data.get("format_catalogue_version") != 2:
        issues.append("Expected format_catalogue_version=2")
    if data.get("production_mode") != f["production_mode"]:
        issues.append("Production mode differs from canonical format; no silent substitution")
    if data.get("required_evidence_solver") != f["required_evidence_solver"]:
        issues.append("Required solver/source was changed; change concept or restore standard")
    route = data.get("selected_asset_route")
    if data.get("media_policy") != "CGI_ONLY" or data.get("assets_responsibility") != "studio":
        issues.append("All registered ASMR projects must be CGI-only with studio-owned sourcing")
    if data.get("user_supplied_media_required") is not False:
        issues.append("User media must never be required for registered ASMR projects")
    if route != "scene":
        issues.append("CGI-only ASMR requires selected_asset_route=scene; footage is prohibited")

    raw = data.get("asset_inventory")
    if not isinstance(raw, list):
        return issues + ["asset_inventory must be an explicit list"]
    approved = set()
    for idx, item in enumerate(raw, 1):
        prefix = "Asset " + str(idx) + ": "
        if not isinstance(item, dict):
            issues.append(prefix + "invalid record")
            continue
        role = item.get("role")
        if role not in MEDIA_ROLES:
            issues.append(prefix + "role must be scene or foley; source footage is prohibited")
            continue
        try:
            path = safe_file(root, item.get("file"))
        except StudioFormatError as exc:
            issues.append(prefix + str(exc))
            continue
        if not path.is_file() or path.stat().st_size == 0:
            issues.append(prefix + "real source file missing or empty: " + str(item.get("file")))
            continue
        if item.get("sha256") != sha256(path):
            issues.append(prefix + "SHA256 mismatch; inspect original media again")
            continue
        if role == "scene" and path.suffix.lower() != ".blend":
            issues.append(prefix + "editable Blender .blend scene required")
            continue
        if role == "foley" and path.suffix.lower() not in {".wav", ".flac", ".ogg", ".mp3"}:
            issues.append(prefix + "actual recorded sound file required")
            continue
        if item.get("asset_owner") != "studio":
            issues.append(prefix + "studio must supply this asset, never ask the user")
            continue
        if item.get("license") not in PERMITTED_LICENSES:
            issues.append(prefix + "commercial licence not checked")
            continue
        if not isinstance(item.get("source_url"), str) or len(item["source_url"]) < 12:
            issues.append(prefix + "source URL/provenance missing")
            continue
        if item.get("material") != f["material"] or item.get("gesture") != f["action"]:
            issues.append(prefix + "material/gesture does not match selected format")
            continue
        if item.get("reviewed") is not True:
            issues.append(prefix + "file must have actually been seen or heard by editor")
            continue
        if role == "foley" and item.get("auditioned_against_picture") is not True:
            issues.append(prefix + "Foley must be auditioned against picture, not filename")
            continue
        approved.add(role)
    if "scene" not in approved:
        issues.append("Missing studio-authored verified Blender scene")
    if "foley" not in approved:
        issues.append("Missing studio-sourced commercially licensed material-and-action-matched Foley")
    return issues


def inspect_manifest(manifest: Path) -> dict:
    manifest = manifest.resolve()
    if not manifest.is_file():
        raise StudioFormatError("Missing production.json: " + str(manifest))
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise StudioFormatError("Production manifest must be a JSON object")
    issues = inspect_assets(data, manifest.parent)
    return {
        "manifest": str(manifest),
        "format_id": data.get("format_id"),
        "asset_preflight_passed": not issues,
        "issues": issues,
        "scope": "Source readiness only. Not a rendered preview or artistic approval.",
        "next_stage": "original still + authored physical motion/real Foley proof" if not issues
                      else "studio must author Blender scene, source licensed Foley and perform audition",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    desc = sub.add_parser("describe")
    desc.add_argument("format_id")
    init = sub.add_parser("init")
    init.add_argument("format_id")
    init.add_argument("directory", type=Path)
    init.add_argument("--aspect", choices=["9:16", "16:9"], default="9:16")
    init.add_argument("--deliverable", choices=sorted(DELIVERABLES), default="preview")
    check = sub.add_parser("check")
    check.add_argument("manifest", type=Path)
    args = p.parse_args(argv)
    try:
        if args.command == "list":
            for f in catalogue()["formats"]:
                print(f'{f["id"]:25} {f["title"]:35} {f["group"]:18} '
                      f'{f["production_mode"]}  [recipe only; NOT quality-approved]')
        elif args.command == "describe":
            print(json.dumps(get_format(args.format_id), indent=2))
        elif args.command == "init":
            print("CREATED UNAPPROVED PILOT PLAN:", init_project(
                args.format_id, args.directory, args.aspect, args.deliverable))
        else:
            report = inspect_manifest(args.manifest)
            print(json.dumps(report, indent=2))
            return 0 if report["asset_preflight_passed"] else 2
    except (StudioFormatError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
