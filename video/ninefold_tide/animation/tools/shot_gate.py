#!/usr/bin/env python3
"""Ninefold fail-closed, offline gate for approved hand-drawn shot packages.

Only reads local evidence. Never generates drawings, confers creative approval,
downloads Drive files, starts a paid model or publishes an episode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

CANON_ROLES = {"series_bible", "character_bible", "episode_script", "director_shots", "art_index"}
STAGE_ORDER = ("intake", "keys", "frames", "export")
STAGE_APPROVALS = {
    "intake": ("canon", "character_model"),
    "keys": ("keys", "breakdowns"),
    "frames": ("inbetweens", "cleanup", "paint", "comp", "frame_review"),
    "export": ("rights", "final_picture"),
}
DRAWING_GROUPS = {
    "keys": ("keys", "breakdowns"),
    "frames": ("inbetweens", "cleanup", "paint", "comp"),
}
REVIEW_CHECKS = ("identity", "age_and_proportions", "anatomy_and_silhouette",
                 "hand_rail_contact", "costume_and_props", "perspective_and_foot_plant",
                 "continuity_and_acting", "line_paint_shadows", "background_integration")


class ShotGateError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ShotGateError("JSON root must be an object")
    return obj


def local_file(root: Path, rel: object) -> Path:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or "\\" in rel:
        raise ShotGateError("asset path must be a nonempty forward-slash relative path")
    root = root.resolve()
    p = (root / rel).resolve()
    if not p.is_relative_to(root) or not p.is_file():
        raise ShotGateError("missing or escaping local evidence: " + rel)
    return p


def evidence(root: Path, row: object, label: str, png: bool = False,
             size: tuple[int, int] | None = None) -> Path:
    if not isinstance(row, dict):
        raise ShotGateError(label + ": file evidence must be an object")
    p = local_file(root, row.get("path"))
    digest = row.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ShotGateError(label + ": full lowercase SHA-256 required")
    if sha256(p) != digest:
        raise ShotGateError(label + ": changed evidence checksum")
    if png:
        if p.suffix.lower() != ".png":
            raise ShotGateError(label + ": approved source must be PNG")
        try:
            with Image.open(p) as im:
                if im.format != "PNG" or (size is not None and im.size != size):
                    raise ShotGateError(label + ": PNG dimensions or encoding mismatch")
                im.verify()
        except OSError as exc:
            raise ShotGateError(label + ": broken PNG") from exc
    return p


def approval(root: Path, data: dict, name: str) -> None:
    row = data.get("approvals", {}).get(name)
    if not isinstance(row, dict) or row.get("approved") is not True:
        raise ShotGateError(name + ": no explicit human approval")
    if not isinstance(row.get("reviewer"), str) or len(row["reviewer"].strip()) < 3:
        raise ShotGateError(name + ": named reviewer required")
    evidence(root, row.get("evidence"), name + " review")


def validate(data: dict, root: Path, stage: str) -> dict:
    if stage not in STAGE_ORDER:
        raise ShotGateError("unknown production stage")
    if data.get("schema_version") != 1:
        raise ShotGateError("unsupported shot schema")
    if not re.fullmatch(r"E\d{3}", str(data.get("episode", ""))):
        raise ShotGateError("episode must look like E101")
    if not re.fullmatch(r"CAM\d{2}[A-Z]?", str(data.get("camera", ""))):
        raise ShotGateError("camera must look like CAM03B")
    if data.get("fps") != 24 or type(data.get("frame_count")) is not int or data["frame_count"] <= 0:
        raise ShotGateError("approved timing needs 24fps and positive integer frame_count")
    resolution = data.get("resolution")
    if (not isinstance(resolution, list) or len(resolution) != 2
            or any(type(n) is not int or n < 64 or n > 4096 for n in resolution)):
        raise ShotGateError("invalid output resolution")
    size = tuple(resolution)
    canon = data.get("canon")
    if not isinstance(canon, list):
        raise ShotGateError("Drive canon list missing")
    roles = set()
    for doc in canon:
        if not isinstance(doc, dict):
            raise ShotGateError("invalid canon document")
        role = doc.get("role")
        if role in roles:
            raise ShotGateError("duplicate canon role")
        roles.add(role)
        if (not isinstance(doc.get("url"), str)
                or not doc["url"].startswith("https://docs.google.com/")
                or not isinstance(doc.get("reviewed_by"), str)
                or len(doc["reviewed_by"].strip()) < 3):
            raise ShotGateError("Drive document requires a real URL and named review: " + str(role))
    if not CANON_ROLES.issubset(roles):
        raise ShotGateError("missing source-of-truth roles: " + ", ".join(sorted(CANON_ROLES - roles)))
    for key in STAGE_APPROVALS["intake"]:
        approval(root, data, key)
    if stage == "intake":
        return {"stage": stage, "status": "PASS", "release_approved": False}

    drawings = data.get("drawings", {})
    if not isinstance(drawings, dict):
        raise ShotGateError("drawing registry missing")
    for group in DRAWING_GROUPS["keys"]:
        rows = drawings.get(group)
        if not isinstance(rows, list) or not rows:
            raise ShotGateError("missing independently drawn " + group)
        for n, row in enumerate(rows):
            evidence(root, row, f"{group}[{n}]", png=True)
    for key in STAGE_APPROVALS["keys"]:
        approval(root, data, key)
    if stage == "keys":
        return {"stage": stage, "status": "PASS", "release_approved": False}

    for group in DRAWING_GROUPS["frames"]:
        rows = drawings.get(group)
        if not isinstance(rows, list) or not rows:
            raise ShotGateError("missing source drawings: " + group)
        for n, row in enumerate(rows):
            evidence(root, row, f"{group}[{n}]", png=True)
    for key in STAGE_APPROVALS["frames"]:
        approval(root, data, key)
    seq = data.get("sequence")
    if not isinstance(seq, dict):
        raise ShotGateError("numbered sequence missing")
    ledger = read_json(evidence(root, seq.get("ledger"), "sequence ledger"))
    directory = seq.get("directory")
    if not isinstance(directory, str):
        raise ShotGateError("sequence directory missing")
    frame_dir = (root.resolve() / directory).resolve()
    if not frame_dir.is_relative_to(root.resolve()) or not frame_dir.is_dir():
        raise ShotGateError("sequence directory is missing or escapes root")
    expected = [f"frame_{n:06d}.png" for n in range(1, data["frame_count"] + 1)]
    actual = sorted(x.name for x in frame_dir.glob("frame_*.png"))
    if actual != sorted(expected) or sorted(ledger.get("frames", {})) != sorted(expected):
        raise ShotGateError("sequence requires exact continuous numbered frames, no gaps or extras")
    if ledger.get("resolution") != resolution or ledger.get("fps") != data["fps"]:
        raise ShotGateError("sequence ledger size/fps mismatch")
    for name in expected:
        evidence(root, {"path": directory + "/" + name,
                        "sha256": ledger["frames"][name]}, "sequence " + name,
                 png=True, size=size)
    if stage == "frames":
        return {"stage": stage, "status": "PASS", "frames": len(expected), "release_approved": False}
    for key in STAGE_APPROVALS["export"]:
        approval(root, data, key)
    checks = data.get("picture_review")
    if not isinstance(checks, dict):
        raise ShotGateError("frame-by-frame visual review absent")
    for name in REVIEW_CHECKS:
        row = checks.get(name)
        if not isinstance(row, dict) or row.get("passed") is not True:
            raise ShotGateError("visual check failed or missing: " + name)
        if not isinstance(row.get("reviewer"), str) or len(row["reviewer"].strip()) < 3:
            raise ShotGateError("named visual reviewer missing: " + name)
        evidence(root, row.get("evidence"), name + " visual review")
    return {"stage": stage, "status": "PASS", "frames": len(expected),
            "release_approved": False, "note": "Export eligibility only; sound and full-film review remain separate."}


def index_sequence(data: dict, root: Path, output: Path) -> dict:
    """Prepare an unsigned evidence ledger; never marks drawing or sequence approved."""
    seq = data.get("sequence", {})
    directory = seq.get("directory")
    if not isinstance(directory, str):
        raise ShotGateError("sequence.directory missing")
    frames = {}
    for n in range(1, data["frame_count"] + 1):
        name = f"frame_{n:06d}.png"
        p = local_file(root, directory + "/" + name)
        with Image.open(p) as image:
            if image.size != tuple(data["resolution"]) or image.format != "PNG":
                raise ShotGateError(name + ": wrong format or dimensions")
            image.verify()
        frames[name] = sha256(p)
    actual = sorted(p.name for p in (root / directory).glob("frame_*.png"))
    if actual != sorted(frames):
        raise ShotGateError("extra numbered frames")
    if output.exists():
        raise ShotGateError("refusing to overwrite existing ledger")
    output.parent.mkdir(parents=True, exist_ok=True)
    obj = {"fps": 24, "resolution": data["resolution"], "frames": frames,
           "approval": "UNSIGNED_TECHNICAL_INVENTORY"}
    output.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf8")
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("check", "index", "export"))
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--asset-root", type=Path)
    p.add_argument("--stage", choices=STAGE_ORDER, default="intake")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        data = read_json(args.manifest)
        root = (args.asset_root or args.manifest.parent).resolve()
        if args.command == "index":
            if args.output is None:
                raise ShotGateError("index requires --output")
            result = index_sequence(data, root, args.output)
            report = {"status": "INDEXED_NOT_APPROVED", "frames": len(result["frames"])}
        else:
            stage = "export" if args.command == "export" else args.stage
            report = validate(data, root, stage)
            if args.command == "export":
                if args.output is None or args.output.exists():
                    raise ShotGateError("provide an unused --output .mp4")
                if args.output.suffix.lower() != ".mp4":
                    raise ShotGateError("only .mp4 shot previews supported")
                ffmpeg = shutil.which("ffmpeg")
                if not ffmpeg:
                    raise ShotGateError("FFmpeg not installed locally")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error",
                                "-nostdin", "-n", "-framerate", "24",
                                "-i", str(root / data["sequence"]["directory"] / "frame_%06d.png"),
                                "-frames:v", str(data["frame_count"]),
                                "-c:v", "libx264", "-crf", "18",
                                "-pix_fmt", "yuv420p", str(args.output)], check=True)
                report["shot_export"] = str(args.output)
                report["release_approved"] = False
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
