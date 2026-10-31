#!/usr/bin/env python3
"""Immutable-source assembler for Ninefold Tide's private Naya Godot workbench.

Copies approved visual *references* verbatim; it never approves final animated art.
No video generation, public art upload, automatic GPU use or network access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

SOURCES = {
    "naya_phase19": ("Ninefold_Phase19_Naya_ArtRig_Integration_Patch.zip", "a4b2bd530c4751ab9751db98bfa001525763cc42a845f48467e89f63a5b0a7cb"),
    "naya_phase20": ("Ninefold_Phase20_Joint_And_Rail_Grip_Patch.zip", "a32865d216df556c9f22eae21309bd5fc648c3629ac9bacdf8280a7116f6d64b"),
    "harbour_phase24": ("Ninefold_Phase24_Curated_Godot_Project.zip", "c6c824b3fd23ede6e7fe3e3c2966b555be9453e71725b8896a44201630581324"),
}
CANON = {
    "series": "https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit",
    "cast": "https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit",
    "art_index": "https://docs.google.com/document/d/1roYu1Frb2awFvwSI7mms2_llnag58qDVCmnUEfb5F24/edit",
}
PROJECT_FILE = '''config_version=5

[application]
config/name="Ninefold Tide — Naya technical rig review"
run/main_scene="res://scenes/Naya_Rail_Grip_Review.tscn"

[display]
window/size/viewport_width=1280
window/size/viewport_height=1024

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_unpack(zpath: Path, dest: Path, *, prefix: str = "") -> int:
    """Secure ZIP unpack; allows only plain files, with bounded uncompressed bytes."""
    count, total = 0, 0
    with zipfile.ZipFile(zpath) as archive:
        for item in archive.infolist():
            raw = item.filename.replace("\\", "/")
            components = PurePosixPath(raw).parts
            if not raw or raw.startswith("/") or ".." in components or ":" in raw or not components:
                raise ValueError(f"Unsafe archive path: {raw!r}")
            if prefix:
                if not raw.startswith(prefix):
                    raise ValueError(f"Unexpected project root in {zpath.name}: {raw}")
                raw = raw[len(prefix):]
                if not raw:
                    continue
            if item.is_dir():
                continue
            mode = item.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"Refusing symlink: {raw}")
            count += 1
            total += item.file_size
            if count > 3000 or total > 400 * 1024 * 1024:
                raise ValueError(f"Source ZIP exceeds safe extraction limit: {zpath.name}")
            target = (dest / raw).resolve()
            if not target.is_relative_to(dest.resolve()):
                raise ValueError(f"Path escaped staging directory: {raw}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item, "r") as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
    return count


def validate_sources(root: Path) -> dict:
    manifest_path = root / "ART_SOURCE_MANIFEST.json"
    entries = json.loads(manifest_path.read_text(encoding="utf8"))["assets"]
    if len(entries) < 80:
        raise ValueError(f"Incomplete Phase20 source manifest: {len(entries)} entries")
    for item in entries:
        filename = root / item["file"]
        if not filename.is_file():
            raise FileNotFoundError(f"Missing approved-source-derived asset: {item['file']}")
        if sha256(filename) != item["file_sha256"]:
            raise ValueError(f"Checksum mismatch: {item['file']}")
    rig = json.loads((root / "assets/naya/rig.json").read_text(encoding="utf8"))
    flags = rig["flags"]
    for forbidden in ("shot_art_and_motion_approved", "rail_contact_human_approved", "5_view_rig", "independent_paint_behind_at_joints"):
        if flags.get(forbidden) is not False:
            raise ValueError(f"Unsafe release state or missing explicit false flag: {forbidden}")
    if "rail_grip" not in rig:
        raise ValueError("Missing Phase20 rail-contact rig")
    if not (root / "scripts/naya_phase20_rig.gd").is_file():
        raise FileNotFoundError("Missing Phase20 rig GDScript")
    if any(root.rglob("*.mp4")) or any(root.rglob("*.webm")):
        raise ValueError("Unexpected video output in a pre-video rig package")
    return {"verified_source_artifacts": len(entries), "joint_structures": len(rig["parts"]), "final_art_approved": False}


def assemble(inputs: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Output directory must be new or empty; refusing to overwrite artwork")
    resolved = {}
    for key, (filename, expected) in SOURCES.items():
        path = inputs / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing private source ZIP: {path}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"Unapproved or changed source archive {filename}: expected {expected}, got {actual}")
        resolved[key] = {"file": filename, "sha256": actual}
    temp = Path(tempfile.mkdtemp(prefix="ninefold-private-build-", dir=str(output.parent.resolve())))
    try:
        naya = temp / "naya"
        harbour = temp / "harbour_review"
        naya.mkdir(); harbour.mkdir()
        safe_unpack(inputs / SOURCES["naya_phase19"][0], naya)
        safe_unpack(inputs / SOURCES["naya_phase20"][0], naya)
        safe_unpack(inputs / SOURCES["harbour_phase24"][0], harbour, prefix="Ninefold_Phase24_Godot_Curated_Library/")
        (naya / "project.godot").write_text(PROJECT_FILE, encoding="utf8")
        summary = validate_sources(naya)
        if not (harbour / "project.godot").is_file():
            raise ValueError("Missing Godot project in Phase24 harbour workshop")
        report = {
            "project": "The Ninefold Tide", "intent": "private pre-video technical rig assembly",
            "canon": CANON, "packages": resolved, "naya": summary,
            "harbour": "separate Godot review project; final production approval pending",
            "godot_engine_tested_in_this_build": False,
            "kaggle_execution_verified": False,
            "video_created": False, "release_permitted": False,
            "note": "Original source bytes preserved. Do not publish private PNG files to GitHub."
        }
        (temp / "BUILD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        temp.rename(output)
        return report
    finally:
        if temp.exists():
            shutil.rmtree(temp, ignore_errors=True)


def run_engine(root: Path, godot: str) -> dict:
    """Does not request a video, movie writer, screenshot, or rendered frame."""
    exe = shutil.which(godot) if not Path(godot).is_file() else godot
    if not exe:
        raise FileNotFoundError("Godot not installed; native engine checks NOT passed")
    naya, harbour = root / "naya", root / "harbour_review"
    commands = [
        [exe, "--headless", "--path", str(naya), "--editor", "--import", "--quit"],
        [exe, "--headless", "--path", str(naya), "--script", "res://tests/godot_engine_rig_test.gd"],
        [exe, "--headless", "--path", str(harbour), "--editor", "--import", "--quit"],
    ]
    outcomes = []
    for cmd in commands:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=180)
        outcomes.append({"command": cmd[1:], "exit_code": p.returncode, "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-3000:]})
        if p.returncode or "SCRIPT ERROR" in (p.stdout + p.stderr) or "Assertion failed" in (p.stdout + p.stderr):
            break
    report = {"engine_ok": len(outcomes) == len(commands) and all(p["exit_code"] == 0 for p in outcomes), "checks": outcomes, "video_created": False}
    (root / "ENGINE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    if not report["engine_ok"]:
        raise RuntimeError("Native Godot validation failed; review ENGINE_REPORT.json")
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", type=Path, help="Directory holding the three private source ZIPs")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--godot", default="godot", help="Godot 4.7.2 executable")
    ap.add_argument("--engine-test", action="store_true", help="Run engine checks; never render video")
    args = ap.parse_args()
    if args.input_dir:
        result = assemble(args.input_dir, args.output_dir)
        print(json.dumps(result, indent=2))
    else:
        if not args.output_dir.is_dir():
            ap.error("Specify --input-dir to assemble a project")
    if args.engine_test:
        print(json.dumps(run_engine(args.output_dir, args.godot), indent=2))


if __name__ == "__main__":
    main()