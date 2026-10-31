#!/usr/bin/env python3
"""The Ninefold Tide production gates: manual decisions, deterministic tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_WORKSPACE = ROOT / "workspace"
STAGES = (
    "00_reference", "01_character_design", "02_environments", "03_props",
    "04_voice_foley_music", "05_director_storyboards",
    "06_animated_shots", "07_review", "08_masters",
)
REQUIRED_APPROVALS = (
    "script_canon", "storyboard", "character_models", "artwork_rights",
    "voice_takes", "sound_mix", "final_timeline",
)
TOOLS = {
    "python": [sys.executable], "ffmpeg": ["ffmpeg"], "ffprobe": ["ffprobe"],
    "Krita": ["krita"], "OpenToonz": ["opentoonz", "OpenToonz"],
    "Blender": ["blender"], "Godot": ["godot", "godot4", "Godot"],
    "Audacity": ["audacity"], "Kdenlive": ["kdenlive"],
    "Rhubarb Lip Sync": ["rhubarb"], "Piper": ["piper"],
}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def checksum(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def media_path(value: str | None, workspace: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    return path if path.is_absolute() else workspace / path


def doctor() -> dict:
    """Report the COMPLETE installed studio toolbox, not just the editing apps."""
    winget_packages = {
        "Krita": "KDE.Krita", "OpenToonz": "DWANGO.OpenToonz",
        "Blender": "BlenderFoundation.Blender", "Godot": "GodotEngine.GodotEngine",
        "Audacity": "Audacity.Audacity", "Kdenlive": "KDE.Kdenlive",
        "ffmpeg": "Gyan.FFmpeg", "ffprobe": "Gyan.FFmpeg",
    }
    installed_ids = ""
    if os.name == "nt" and shutil.which("winget"):
        try:
            run = subprocess.run(["winget", "list", "--accept-source-agreements"],
                                 text=True, capture_output=True, timeout=40, check=False)
            if run.returncode == 0:
                installed_ids = run.stdout.lower()
        except (OSError, subprocess.TimeoutExpired):
            pass
    appdata = Path(os.environ.get("LOCALAPPDATA", "")) / "NinefoldTideTools"
    explicit_paths = {
        "Rhubarb Lip Sync": appdata / "rhubarb" / "rhubarb.exe",
        "Piper": appdata / "piper-venv" / "Scripts" / "piper.exe",
    } if os.name == "nt" else {}
    tools = {}
    for name, aliases in TOOLS.items():
        found = next((shutil.which(alias) for alias in aliases if shutil.which(alias)), None)
        if not found and name in explicit_paths and explicit_paths[name].is_file():
            found = str(explicit_paths[name])
        winget_id = winget_packages.get(name)
        detected_in_winget = bool(winget_id and winget_id.lower() in installed_ids)
        tools[name] = {"available": bool(found or detected_in_winget),
                       "on_path": bool(found), "executable": found,
                       "winget_installed": detected_in_winget}
    # 'python' is always available because this script is running under it.
    tools["python"]["available"] = sys.version_info >= (3, 11)
    missing = [name for name, state in tools.items() if not state["available"]]
    return {"python_3_11_or_newer": sys.version_info >= (3, 11),
            "full_toolchain_ready": not missing, "missing_tools": missing,
            "tools": tools,
            "note": "Checks only this machine. Missing PATH does not prove software is absent; "
                    "other app locations or licenses may still require human verification. "
                    "Tool availability does NOT certify animation, voice or final art quality."}


def init(workspace: Path) -> dict:
    workspace.mkdir(parents=True, exist_ok=True)
    for stage in STAGES:
        (workspace / stage).mkdir(exist_ok=True)
    copies = {
        ROOT / "pilot_shots.json": workspace / "05_director_storyboards" / "ep101_pilot.json",
        ROOT / "asset_register.json": workspace / "00_reference" / "asset_register.json",
        ROOT / "config.json": workspace / "00_reference" / "config_snapshot.json",
        ROOT / "first_proof_review_template.json": workspace / "07_review" / "ep101_first_proof.json",
    }
    created = []
    for source, target in copies.items():
        if not target.exists():
            shutil.copyfile(source, target)
            created.append(str(target))
    return {"workspace": str(workspace), "stage_folders": list(STAGES), "new_files": created}


def probe(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ], text=True)
    return json.loads(raw)


def validate(shots: dict, register: dict, workspace: Path, stage: str) -> list[str]:
    errors = []
    settings = read_json(ROOT / "config.json")
    fps = settings["target"]["fps"]
    expected = settings["target"]["frames"]
    if shots.get("fps") != fps or shots.get("total_frames") != expected:
        errors.append("Episode fps/total_frames must match the canon config")
    registry = {a.get("id"): a for a in register.get("assets", [])}
    rows = shots.get("shots")
    if not isinstance(rows, list) or len(rows) != 12:
        return errors + ["Pilot requires exactly 12 manually specified shots"]
    cursor = 0
    for idx, shot in enumerate(rows, 1):
        label = shot.get("id", f"shot {idx}")
        if shot.get("id") != f"ep101_{idx:03d}":
            errors.append(f"{label}: incorrect shot ID/order")
        start, end = shot.get("start_frame"), shot.get("end_frame")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"{label}: frame endpoints must be integers")
        elif start != cursor or end <= start:
            errors.append(f"{label}: gap, overlap or zero-length shot")
        else:
            cursor = end
        if not shot.get("editorial_reason") or not shot.get("description"):
            errors.append(f"{label}: missing director-authored decision")
        ids = shot.get("asset_ids", [])
        if not isinstance(ids, list) or not ids:
            errors.append(f"{label}: missing explicit asset references")
            ids = []
        for asset_id in ids:
            if asset_id not in registry:
                errors.append(f"{label}: unknown asset {asset_id}")
        if stage != "assembly":
            continue
        # New production contract: legacy MP4s cannot enter a final cut unless
        # every individual shot was reviewed as an approved IMAGE SEQUENCE.
        frame_pkg = media_path(shot.get("frame_package_manifest"), workspace)
        if frame_pkg is None or not frame_pkg.is_file():
            errors.append(f"{label}: frame_package_manifest required before final assembly")
        else:
            try:
                from animation.tools import shot_gate
                package = shot_gate.read_json(frame_pkg)
                if package.get("episode") != "E101":
                    errors.append(f"{label}: frame package episode mismatch")
                if not shot.get("camera_id") or package.get("camera") != shot.get("camera_id"):
                    errors.append(f"{label}: frame package camera_id mismatch")
                if isinstance(start, int) and isinstance(end, int) and package.get("frame_count") != end - start:
                    errors.append(f"{label}: frame package and cut length disagree")
                if package.get("resolution") != [settings["target"]["width"], settings["target"]["height"]]:
                    errors.append(f"{label}: final-frame package must match target resolution")
                shot_gate.validate(package, frame_pkg.parent, "export")
            except (OSError, ValueError, KeyError, ImportError) as exc:
                errors.append(f"{label}: frame-sequence production gate: {exc}")
        if shot.get("shot_status") != "approved" or shot.get("editor_approved") is not True:
            errors.append(f"{label}: approved shot status/editor approval missing")
        if not shot.get("cut_approved_by"):
            errors.append(f"{label}: exact cut needs named human director/editor")
        clip = media_path(shot.get("video_path"), workspace)
        if clip is None or not clip.is_file():
            errors.append(f"{label}: approved rendered MP4 missing")
        elif shot.get("video_sha256") != checksum(clip):
            errors.append(f"{label}: video checksum mismatch")
        for asset_id in ids:
            asset = registry.get(asset_id, {})
            if not (asset.get("rights_confirmed") is True and asset.get("approved_for_animation") is True):
                errors.append(f"{label}: asset {asset_id} has no art/rights approval")
            src = media_path(asset.get("local_path"), workspace)
            if src is None or not src.is_file():
                errors.append(f"{label}: source file for {asset_id} missing")
            elif asset.get("sha256") != checksum(src):
                errors.append(f"{label}: asset {asset_id} checksum mismatch")
            if not asset.get("source_url") or asset.get("license") in (None, "", "unverified"):
                errors.append(f"{label}: asset {asset_id} provenance/licence missing")
    if cursor != expected:
        errors.append(f"Shot coverage must finish at frame {expected}, got {cursor}")
    if stage == "assembly":
        for key in REQUIRED_APPROVALS:
            if shots.get("director_approvals", {}).get(key) is not True:
                errors.append(f"Director gate not signed: {key}")
        mix = shots.get("mix", {})
        wav = media_path(mix.get("path"), workspace)
        if mix.get("approved") is not True or not mix.get("reviewed_by"):
            errors.append("Final dialogue/Foley/music mix not approved")
        if wav is None or not wav.is_file():
            errors.append("Approved audio WAV mix missing")
        elif checksum(wav) != mix.get("sha256"):
            errors.append("Audio mix checksum mismatch")
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            errors.append("FFmpeg and FFprobe required for media assembly")
        # Audio casting and pronunciation are separate creative release gates.
        # Never accept a final soundtrack merely because it is a valid WAV.
        try:
            import importlib.util
            module_path = ROOT / "audio" / "voice_pipeline.py"
            spec = importlib.util.spec_from_file_location("ninefold_voice_pipeline", module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("Cannot load audio pipeline")
            voice = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(voice)
            audio_dir = workspace / "04_voice_foley_music"
            def audio_data(name):
                local = audio_dir / name
                return voice.load(local if local.is_file() else ROOT / "audio" / name)
            voice_errors = voice.audit(audio_data("cast.json"),
                                      audio_data("pronunciation_lexicon.json"),
                                      audio_data("pilot_voice_lines.json"),
                                      audio_dir, "release")
            errors.extend("Audio gate: " + issue for issue in voice_errors)
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            errors.append("Audio performance review unavailable: " + str(exc))
    return errors


def assemble(shots: dict, workspace: Path, output: Path) -> dict:
    register = read_json(workspace / "00_reference" / "asset_register.json")
    errors = validate(shots, register, workspace, "assembly")
    if errors:
        raise ValueError("ASSEMBLY BLOCKED:\n" + "\n".join(errors))
    if output.exists():
        raise ValueError(f"Refusing to overwrite existing master: {output}")
    settings = read_json(ROOT / "config.json")["target"]
    fps, width, height = settings["fps"], settings["width"], settings["height"]
    tolerance = 2 / fps
    clips = []
    for shot in shots["shots"]:
        video = media_path(shot["video_path"], workspace)
        info = probe(video)
        streams = [v for v in info["streams"] if v.get("codec_type") == "video"]
        if not streams:
            raise ValueError(f"Shot {shot['id']} has no video")
        v = streams[0]
        if (v.get("width"), v.get("height")) != (width, height):
            raise ValueError(f"Shot {shot['id']} not {width}x{height}")
        num, den = (int(x) for x in v.get("avg_frame_rate", "0/1").split("/"))
        if den == 0 or abs(num / den - fps) > 0.01:
            raise ValueError(f"Shot {shot['id']} not {fps} fps")
        duration = float(info["format"]["duration"])
        target = (shot["end_frame"] - shot["start_frame"]) / fps
        if abs(duration - target) > tolerance:
            raise ValueError(f"Shot {shot['id']} duration {duration} != {target}")
        clips.append(video)
    wav = media_path(shots["mix"]["path"], workspace)
    audio_streams = [x for x in probe(wav)["streams"] if x.get("codec_type") == "audio"]
    if not audio_streams:
        raise ValueError("Approved mix contains no audio")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ninefold_manual_timeline_") as temp:
        list_file = Path(temp) / "cuts.txt"
        # FFmpeg concat demuxer: exact director-selected order; never choose/reorder.
        def q(path: Path) -> str:
            return "file '" + str(path.resolve()).replace("'", "'\\''") + "'"
        list_file.write_text("\n".join(q(p) for p in clips) + "\n", encoding="utf-8")
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
               "-f", "concat", "-safe", "0", "-i", str(list_file), "-i", str(wav),
               "-map", "0:v:0", "-map", "1:a:0", "-r", str(fps),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-t", str(settings["seconds"]), "-movflags", "+faststart", str(output)]
        subprocess.run(cmd, check=True)
    return {"output": str(output), "sha256": checksum(output), "release_approved": False}


def verify(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    streams = probe(path)
    video = [v for v in streams["streams"] if v.get("codec_type") == "video"]
    audio = [a for a in streams["streams"] if a.get("codec_type") == "audio"]
    conf = read_json(ROOT / "config.json")["target"]
    if not video or not audio:
        raise ValueError("Master needs both picture and sound")
    if (video[0].get("width"), video[0].get("height")) != (conf["width"], conf["height"]):
        raise ValueError("Master resolution does not match approved target")
    num, den = (int(x) for x in video[0].get("avg_frame_rate", "0/1").split("/"))
    if den == 0 or abs(num / den - conf["fps"]) > 0.01:
        raise ValueError("Master frame rate does not match approved target")
    if abs(float(streams["format"]["duration"]) - conf["seconds"]) > 0.35:
        raise ValueError("Master running time inconsistent with approved shots")
    return {"technical_streams": "PASS", "sha256": checksum(path),
            "creative_release_approval": "PENDING director full picture-and-sound review"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "doctor", "validate", "assemble", "verify"))
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--stage", choices=("structure", "assembly"), default="structure")
    parser.add_argument("--shot-list", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--strict-tools", action="store_true", help="Fail if any full studio tool is missing")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    try:
        if args.command == "doctor":
            report = doctor()
            print(json.dumps(report, indent=2))
            return 1 if args.strict_tools and not report["full_toolchain_ready"] else 0
        elif args.command == "init":
            report = init(workspace)
        elif args.command == "verify":
            if not args.input:
                parser.error("--input is required for verify")
            report = verify(args.input)
        else:
            sheet_path = args.shot_list or (
                workspace / "05_director_storyboards" / "ep101_pilot.json"
                if args.command == "assemble" or args.stage == "assembly"
                else ROOT / "pilot_shots.json"
            )
            registry_path = args.registry or (
                workspace / "00_reference" / "asset_register.json"
                if args.command == "assemble" or args.stage == "assembly"
                else ROOT / "asset_register.json"
            )
            sheet, registry = read_json(sheet_path), read_json(registry_path)
            if args.command == "validate":
                errors = validate(sheet, registry, workspace, args.stage)
                report = {"stage": args.stage, "status": "PASS" if not errors else "BLOCKED", "errors": errors}
                print(json.dumps(report, indent=2))
                return 1 if errors else 0
            if not args.output:
                parser.error("--output is required for assemble")
            report = assemble(sheet, workspace, args.output)
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
