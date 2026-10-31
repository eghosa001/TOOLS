#!/usr/bin/env python3
"""Offline, fail-closed intake of generated or hand-drawn image assets for Ninefold shots.

Never calls an image generator, Drive or paid service. Never approves drawings.
Never modifies the canonical public repo shot manifest. Requires a private asset root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageOps

DRAWING_STAGES = frozenset({"keys", "breakdowns", "inbetweens", "cleanup", "paint", "comp"})
REFERENCE_STAGES = frozenset({"character_model", "background", "environment_reference", "prop_reference"})
VALID_STAGES = DRAWING_STAGES | REFERENCE_STAGES
VALID_ORIGINS = frozenset({"chatgpt_image", "google_drive", "artist", "technical_previz"})
STATUS = "PENDING_HUMAN_ART_REVIEW"
REGISTER = "review/art_intake.json"


class IntakeError(ValueError):
    pass


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def shot_spec(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise IntakeError("Expected a shot_gate schema_version=1 manifest")
    if not re.fullmatch(r"E\d{3}", str(data.get("episode", ""))):
        raise IntakeError("Invalid episode")
    if not re.fullmatch(r"CAM\d{2}[A-Z]?", str(data.get("camera", ""))):
        raise IntakeError("Invalid camera")
    if data.get("fps") != 24 or data.get("resolution") not in ([1280, 720], [1920, 1080]):
        raise IntakeError("Expected 24fps and a supported 16:9 shot resolution")
    return data


def safe_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # The metadata file may be rewritten, but imported image files NEVER are.
    fd, temp = tempfile.mkstemp(prefix=".intake-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2, ensure_ascii=False)
            out.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def validate_origin(origin: str, source_ref: str) -> None:
    if origin not in VALID_ORIGINS or not source_ref or len(source_ref) > 2048:
        raise IntakeError("Origin and nonempty source reference required")
    if origin == "google_drive":
        u = urlparse(source_ref)
        if u.scheme != "https" or u.hostname not in {"drive.google.com", "docs.google.com"}:
            raise IntakeError("Google Drive source must use a verifiable Drive/Docs URL")


def registered_art(root: Path, row: dict) -> Path:
    """Keep persisted register paths in the private asset root, including symlinks."""
    if not isinstance(row, dict) or not isinstance(row.get("path"), str):
        raise IntakeError("Invalid registered art record")
    rel = Path(row["path"])
    if rel.is_absolute() or "\\" in row["path"] or ".." in rel.parts or not rel.parts:
        raise IntakeError("Registered image has an unsafe relative path")
    resolved_root = root.resolve()
    resolved = (root / rel).resolve()
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise IntakeError("Registered art is absent or escapes private root")
    if digest(resolved) != row.get("sha256"):
        raise IntakeError("Registered art checksum changed")
    return resolved


def registry_read(path: Path, shot_id: str) -> dict:
    if not path.exists():
        return {"schema_version": 1, "shot_id": shot_id, "status": "UNAPPROVED", "assets": []}
    reg = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(reg, dict) or reg.get("schema_version") != 1 or reg.get("shot_id") != shot_id or not isinstance(reg.get("assets"), list):
        raise IntakeError("Asset register is corrupt or belongs to a different shot")
    return reg


def add_asset(*, shot: Path, root: Path, source: Path, stage: str,
              origin: str, source_ref: str, frame: int | None, notes: str = "") -> dict:
    spec = shot_spec(shot)
    shot_id = spec["episode"] + "/" + spec["camera"]
    if stage not in VALID_STAGES:
        raise IntakeError("Unsupported art intake stage")
    if frame is not None and (type(frame) is not int or frame <= 0 or frame > spec["frame_count"]):
        raise IntakeError("Frame index outside current shot timing")
    if stage in DRAWING_STAGES and frame is None:
        raise IntakeError("A numbered frame is required for every drawing stage")
    if stage in REFERENCE_STAGES and frame is not None:
        raise IntakeError("Reference art must not masquerade as timed drawings")
    validate_origin(origin, source_ref)
    if not source.is_file() or source.stat().st_size > 30_000_000:
        raise IntakeError("Source missing or exceeds 30 MB art-intake limit")
    if not root.exists() or not root.is_dir():
        raise IntakeError("Create a private asset root before importing")
    if source.resolve().is_relative_to(root.resolve()):
        raise IntakeError("Source must be outside target root so originals remain untouched")
    with Image.open(source) as raw:
        if raw.format not in {"PNG", "JPEG", "WEBP"}:
            raise IntakeError("Only PNG/JPEG/WebP stills are supported")
        im = ImageOps.exif_transpose(raw)
        if stage in DRAWING_STAGES and list(im.size) != spec["resolution"]:
            raise IntakeError("Frame art must match the shot's locked resolution; no automatic crop")
        if stage in REFERENCE_STAGES and (im.width < 256 or im.height < 256):
            raise IntakeError("Reference image too small for art review")
        im = im.convert("RGBA")
        src_hash = digest(source)
        name = f'{spec["episode"]}_{spec["camera"]}_{stage}'
        if frame is not None:
            name += f'_f{frame:06d}'
        name += f'_{src_hash[:16]}.png'
        rel = (Path(stage) if stage in DRAWING_STAGES else Path("references") / stage) / name
        destination = root / rel
        reg_file = root / REGISTER
        reg = registry_read(reg_file, shot_id)
        if any(e.get("role") == stage and e.get("frame") == frame and e.get("source_sha256") == src_hash for e in reg["assets"]):
            raise IntakeError("Source already registered; refusing duplicate")
        # Frame alternatives are possible but must be resolved during human review.
        if destination.exists() or destination.is_symlink():
            raise IntakeError("Refusing to overwrite imported art")
        destination.parent.mkdir(parents=True, exist_ok=True)
        im.save(destination, format="PNG", optimize=True)
    entry = {"role": stage, "frame": frame, "path": rel.as_posix(),
             "sha256": digest(destination), "resolution": list(im.size),
             "source_sha256": src_hash, "origin": origin, "source_ref": source_ref,
             "review_status": STATUS, "notes": notes[:1000],
             "imported_utc": datetime.now(timezone.utc).isoformat()}
    reg["assets"].append(entry)
    safe_write(reg_file, reg)
    return entry


def bind_manifest(*, shot: Path, root: Path, output: Path) -> dict:
    spec = shot_spec(shot)
    reg = registry_read(root / REGISTER, spec["episode"] + "/" + spec["camera"])
    if output.resolve() == shot.resolve() or output.exists():
        raise IntakeError("Cannot overwrite a public or existing manifest")
    if not output.resolve().is_relative_to(root.resolve()):
        raise IntakeError("Output shot manifest must live inside the private asset root")
    for stage in sorted(DRAWING_STAGES):
        candidates = [a for a in reg["assets"] if a["role"] == stage]
        seen = set()
        for row in candidates:
            if row["frame"] in seen:
                raise IntakeError(stage + ": competing drawings for the same frame; review and resolve first")
            seen.add(row["frame"])
            try:
                registered_art(root, row)
            except IntakeError as exc:
                raise IntakeError(stage + ": " + str(exc)) from exc
        spec["drawings"][stage] = [{"path": a["path"], "sha256": a["sha256"]}
                                    for a in sorted(candidates, key=lambda x: x["frame"])]
    # The original manifest has a false approval gate. Preserve ALL approvals exactly.
    if any(v.get("approved") is True for v in spec.get("approvals", {}).values()):
        raise IntakeError("Use a fresh, unapproved shot brief; this tool cannot carry approvals forward")
    spec["status"] = "BLOCKED_PENDING_ART"
    spec["art_intake_register"] = REGISTER
    safe_write(output, spec)
    return {"status": "BOUND_BUT_UNAPPROVED", "manifest": str(output),
            "drawing_counts": {r: len(spec["drawings"][r]) for r in sorted(DRAWING_STAGES)}}


def contact_sheet(*, shot: Path, root: Path, output: Path) -> dict:
    spec = shot_spec(shot)
    reg = registry_read(root / REGISTER, spec["episode"] + "/" + spec["camera"])
    if output.exists():
        raise IntakeError("Refusing to overwrite an existing review sheet")
    if not reg["assets"]:
        raise IntakeError("No imported art to review")
    width, tile_w, tile_h = 1120, 520, 340
    rows = (len(reg["assets"]) + 1) // 2
    sheet = Image.new("RGB", (width, 92 + tile_h * rows), "#17202a")
    draw = ImageDraw.Draw(sheet)
    draw.text((28, 18), "NINEFOLD - PRIVATE ART INTAKE - UNAPPROVED", fill="#ffb5a6")
    draw.text((28, 44), spec["episode"] + " / " + spec["camera"] + "    NOT A RELEASE OR APPROVED MODEL SHEET", fill="#ffffff")
    for i, row in enumerate(reg["assets"]):
        p = registered_art(root, row)
        with Image.open(p) as im:
            thumb = im.convert("RGB")
            thumb.thumbnail((tile_w - 32, tile_h - 72), Image.Resampling.LANCZOS)
        x = 24 + (i % 2) * 560
        y = 92 + (i // 2) * tile_h
        sheet.paste(thumb, (x + (tile_w - thumb.width) // 2, y + 8))
        draw.text((x + 9, y + tile_h - 56), f'{row["role"]}  frame {row["frame"] or "reference"}', fill="#ffffff")
        draw.text((x + 9, y + tile_h - 38), "PENDING HUMAN ART REVIEW", fill="#ffb5a6")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, "PNG", optimize=True)
    return {"status": "REVIEW_ONLY", "artwork": len(reg["assets"]), "sheet": str(output)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("add", "bind", "contact"))
    p.add_argument("--shot", type=Path, required=True)
    p.add_argument("--asset-root", type=Path, required=True)
    p.add_argument("--source", type=Path)
    p.add_argument("--stage", choices=sorted(VALID_STAGES))
    p.add_argument("--origin", choices=sorted(VALID_ORIGINS))
    p.add_argument("--source-ref")
    p.add_argument("--frame", type=int)
    p.add_argument("--notes", default="")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        if args.command == "add":
            if not all([args.source, args.stage, args.origin, args.source_ref]):
                raise IntakeError("add needs source, stage, origin and source-ref")
            report = add_asset(shot=args.shot, root=args.asset_root, source=args.source,
                               stage=args.stage, origin=args.origin, source_ref=args.source_ref,
                               frame=args.frame, notes=args.notes)
        elif args.command == "bind":
            if not args.output:
                raise IntakeError("bind needs --output")
            report = bind_manifest(shot=args.shot, root=args.asset_root, output=args.output)
        else:
            if not args.output:
                raise IntakeError("contact needs --output")
            report = contact_sheet(shot=args.shot, root=args.asset_root, output=args.output)
        print(json.dumps(report, indent=2))
        return 0
    except (IntakeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
