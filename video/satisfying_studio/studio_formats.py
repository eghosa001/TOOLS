#!/usr/bin/env python3
"""Offline, fail-closed production catalogue and asset preflight for 47 ASMR formats.

This does not generate fake footage, download copyrighted materials, select
Foley automatically, grant creative approval, or claim that a format has already
passed a render test. It prepares one precisely defined, editor-directed shot
and refuses missing media/rights evidence before any expensive render.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

CATALOGUE = Path(__file__).resolve().parent / "formats" / "catalogue.json"
PERMITTED_LICENSES = {"original", "CC0", "CC BY 4.0", "Pexels License"}
MEDIA_ROLES = {"scene", "footage", "foley"}
MODES = {"blender", "real_capture", "hybrid"}
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
    if data.get("schema_version") != 1:
        raise StudioFormatError("Unsupported format catalogue version")
    items = data.get("formats")
    if not isinstance(items, list) or len(items) != 47:
        raise StudioFormatError("Expected the 47 owner-requested studio formats")
    ids = [item["id"] for item in items]
    if len(set(ids)) != 47 or any(item["production_mode"] not in MODES for item in items):
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
        "source_and_rights": "Original scene or real recorded take, exact asset paths, authors, "
                             "licences and hashes required before render",
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
        "format_catalogue_version": 1,
        "production_mode": f["production_mode"],
        "selected_asset_route": (
            "choose_scene_or_footage" if f["production_mode"] == "hybrid"
            else ("scene" if f["production_mode"] == "blender" else "footage")
        ),
        "required_evidence_solver": f["required_evidence_solver"],
        "delivery_intent": deliverable,
        "aspect_ratio": aspect,
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
        "production_state": "UNAPPROVED_ASSETS_REQUIRED",
    }
    manifest = directory / "production.json"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (directory / "NEXT_STEPS.txt").write_text(
        "FORMAT: " + f["title"] + "\nMODULE: " + f["group"] +
        "\nPHYSICS/SOURCE: " + f["required_evidence_solver"] +
        "\nCRITICAL RISK: " + f["critical_quality_risk"] +
        "\n\n1. Replace concept, camera treatment and exact timed shot plan.\n"
        "2. For hybrid formats choose selected_asset_route: scene OR footage.\n"
        "3. Supply real relative files in asset_inventory with sha256, source_url,\n"
        "   licensed use, exact material and gesture, and actual audition evidence.\n"
        "4. Run studio_formats.py check production.json; it fails until assets pass.\n"
        "5. Produce a still, 3-5 second physical motion+real sound proof.\n"
        "6. Obtain genuine preview approval before final rendering.\n"
        "7. Follow quality_gate.py / POST_RENDER_AV_REVIEW.md for exact master.\n"
        "8. Long-form delivery intent is only a 5s pilot scaffold: develop a real\n"
        "   8-12 min independently timed, manually shot-authored master after approval.\n"
        "No video has been created, quality scored, or approved by this scaffold.\n",
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
    if data.get("format_catalogue_version") != 1:
        issues.append("Expected format_catalogue_version=1")
    if data.get("production_mode") != f["production_mode"]:
        issues.append("Production mode differs from canonical format; no silent substitution")
    if data.get("required_evidence_solver") != f["required_evidence_solver"]:
        issues.append("Required solver/source was changed; change concept or restore standard")
    route = data.get("selected_asset_route")
    if route not in {"scene", "footage"}:
        issues.append("Choose an explicit selected_asset_route: scene or footage")
    elif f["production_mode"] == "blender" and route != "scene":
        issues.append("This format needs an authored editable Blender scene")
    elif f["production_mode"] == "real_capture" and route != "footage":
        issues.append("This format needs original real footage; do not fake filmed subjects")
    elif f["production_mode"] == "hybrid" and route == "scene" and f["required_evidence_solver"] == "physical_footage":
        issues.append("This format currently requires filmed footage until CGI physics has been demonstrated")

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
            issues.append(prefix + "role must be scene/footage/foley")
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
        if role == "footage" and path.suffix.lower() not in {".mp4", ".mov", ".mkv"}:
            issues.append(prefix + "genuine video source required")
            continue
        if role == "foley" and path.suffix.lower() not in {".wav", ".flac", ".ogg", ".mp3"}:
            issues.append(prefix + "actual recorded sound file required")
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
    if route in {"scene", "footage"} and route not in approved:
        issues.append("Missing verified " + route + " asset")
    if "foley" not in approved:
        issues.append("Missing real recorded, material-and-action-matched Foley")
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
                      else "provide verified source files and editor audition evidence",
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
