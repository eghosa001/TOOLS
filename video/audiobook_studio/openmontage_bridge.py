#!/usr/bin/env python3
"""Private OpenMontage handoff and guarded Mythveil audiobook assembly.

OpenMontage helps stage scenes; the existing repo remains the ONE authorized
audio/music/panel timing/render/release pipeline. No upload or publication here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VOICE = "am_michael"
REQUIRED = ("series_title", "episode_number", "episode_title", "approved_script",
            "narration_audio", "timeline", "quality_scorecard",
            "visual_qa_report", "master_mp4")


def _path(value: str, directory: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Private input/output path is missing")
    path = Path(value).expanduser()
    return (path if path.is_absolute() else directory / path).resolve()


def read_manifest(filename: Path) -> tuple[dict, Path]:
    filename = Path(filename).expanduser().resolve(strict=True)
    # Private inputs must never be accidentally staged or committed in TOOLS.
    if filename.is_relative_to(ROOT):
        raise ValueError("Private episode manifest must live OUTSIDE the public TOOLS repository")
    value = json.loads(filename.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or any(k not in value for k in REQUIRED):
        raise ValueError("Private manifest is missing required fields")
    if not all(isinstance(value[k], str) and value[k].strip()
               for k in REQUIRED if k != "episode_number"):
        raise ValueError("Manifest has empty required fields")
    if type(value["episode_number"]) is not int or not 1 <= value["episode_number"] <= 999:
        raise ValueError("episode_number must be a positive integer")
    if "REPLACE_WITH" in value["episode_title"] or "REPLACE_WITH" in value["series_title"]:
        raise ValueError("Use the real owner-approved episode and series title")
    if _path(value["master_mp4"], filename.parent).is_relative_to(ROOT):
        raise ValueError("Private master video must not be written into the public repository")
    if value.get("narrator", VOICE) != VOICE:
        raise ValueError("The approved Kokoro Michael voice cannot be changed")
    if value.get("publish", False) is not False:
        raise ValueError("OpenMontage handoff never authorizes publication")
    mood = value.get("music_mood", "mystery")
    if mood not in ("mystery", "tension", "wonder", "reflective", "action"):
        raise ValueError("Unsupported approved music mood")
    level = value.get("music_level", 0.10)
    if type(level) not in (int, float) or not 0.02 <= level <= 0.20:
        raise ValueError("Music gain must be between 0.02 and 0.20")
    if bool(value.get("music_file")) != bool(value.get("music_rights_file")):
        raise ValueError("External music requires its matching rights evidence")
    return value, filename.parent


def full_title(manifest: dict) -> str:
    return (f'{manifest["series_title"]} | Episode '
            f'{manifest["episode_number"]:02d}: '
            f'{manifest["episode_title"]} | Audiobook')


def commands(manifest: dict, directory: Path) -> tuple[list[str], list[str]]:
    get = lambda key: str(_path(manifest[key], directory))
    output = get("master_mp4")
    mood = manifest.get("music_mood", "mystery")
    level = str(manifest.get("music_level", 0.10))
    music = [sys.executable, "-m", "video.audiobook_studio.manhua_pipeline.music_bed",
             "--output", output, "--music-mood", mood, "--music-level", level]
    render = [sys.executable, "-m", "video.audiobook_studio.manhua_pipeline.assemble_existing",
              "--art-policy", "full_color_panels", "--quality-scorecard",
              get("quality_scorecard"), "--source-text", get("approved_script"),
              "--audio", get("narration_audio"), "--timeline", get("timeline"),
              "--visual-qa-report", get("visual_qa_report"), "--require-visual-qa",
              "--output", output, "--preset", "ultrafast",
              "--music-mood", mood, "--music-level", level]
    if manifest.get("thumbnail"):
        render += ["--thumbnail", get("thumbnail")]
    if manifest.get("music_file"):
        options = ["--music-file", get("music_file"),
                   "--music-rights-file", get("music_rights_file")]
        music += options
        render += options
    return music, render


def prepare(manifest: dict, directory: Path, montage_root: Path | None) -> Path:
    script = _path(manifest["approved_script"], directory)
    if not script.is_file() or not script.read_text(encoding="utf-8-sig").strip():
        raise ValueError("Approved local spoken-script file is required before handoff")
    montage = "NOT_VERIFIED_LOCAL"
    if montage_root is not None:
        root = Path(montage_root).expanduser().resolve()
        if not ((root / "AGENT_GUIDE.md").is_file()
                and (root / "pipeline_defs" / "animation.yaml").is_file()):
            raise ValueError("Supplied OpenMontage checkout is missing agent guide/pipeline")
        montage = str(root)
    prompt = manifest.get("scene_prompts")
    if prompt and not _path(prompt, directory).is_file():
        raise ValueError("Approved scene-prompt file does not exist locally")
    prompt_note = ("Private prompt source: " + str(_path(prompt, directory))
                   if prompt else "No approved prompt file supplied")
    body = "\n".join([
        "# OpenMontage / Mythveil: PRIVATE production handoff",
        "",
        "Canonical title: " + full_title(manifest),
        "Local OpenMontage checkout: " + montage,
        "Approved source file: " + str(script),
        prompt_note,
        "Private episode folder: " + str(directory),
        "",
        "Use OpenMontage's animation pipeline for scene planning, asset",
        "inventory, provider comparison and storyboard approval only.",
        "This is a SOURCE-LOCKED illustrated audiobook, not a rewrite.",
        "Do not generate replacement narration, video clips, 3D animation,",
        "unlicensed media or generic filler. Do not use Perchance bots.",
        "Reuse previously approved same-series art and references first.",
        "Create ONLY full-color, consistent, source-accurate 16:9 2D art.",
        "Match every proposed scene to its exact spoken beat; do not",
        "force one image per prompt if the story requires another cadence.",
        "Images must be saved to the designated PRIVATE Drive workspace",
        "and receive verified scene-by-scene visual/rights approval.",
        "",
        "Never start artwork, voice, music or rendering without a signed",
        "preproduction scorecard >=8/10 per assigned team member.",
        "MUSIC FIRST for new episodes; narration is Kokoro am_michael",
        "at 1.25 synthesis speed, never second-speeded or regenerated",
        "when approved audio already exists. Preserve existing hashes.",
        "Only the existing TOOLS color-panel timeline and FFmpeg",
        "assembler may produce the 1080p/24fps/H.264/AAC final MP4.",
        "Run this bridge with --phase render ONLY after all private",
        "source/audio/image/timing/rights/scorecard inputs exist.",
        "The scene-image/voice gate, 16 hard gates, human full-video",
        "review and private verified Drive handoff remain mandatory.",
        "NEVER upload or publish to YouTube without separate owner consent.",
        "",
    ])
    out = directory / "OPENMONTAGE_PRIVATE_AUDIOBOOK_WORK_ORDER.md"
    out.write_text(body, encoding="utf-8")
    return out


def render(manifest: dict, directory: Path) -> None:
    needed = ("approved_script", "narration_audio", "timeline",
              "quality_scorecard", "visual_qa_report")
    for key in needed:
        if not _path(manifest[key], directory).is_file():
            raise ValueError("RENDER_BLOCKED: missing private " + key)
    # This is the actual owner-approved production preflight, not a substitute.
    from video.audiobook_studio.episode_quality_gate import validate_scorecard
    scorecard = json.loads(_path(manifest["quality_scorecard"], directory)
                           .read_text(encoding="utf-8"))
    validate_scorecard(scorecard, phase="preproduction")
    music, assembly = commands(manifest, directory)
    # A first-run soundtrack is generated and hashed before assembly.
    subprocess.run(music, check=True, cwd=ROOT)
    subprocess.run(assembly, check=True, cwd=ROOT)
    print("ASSEMBLY_COMPLETE_TECHNICAL_ONLY: full human review and Drive QA still required")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--phase", choices=("prepare", "render"), default="prepare")
    ap.add_argument("--openmontage-root", type=Path)
    args = ap.parse_args()
    try:
        manifest, directory = read_manifest(args.manifest)
        if args.phase == "prepare":
            out = prepare(manifest, directory, args.openmontage_root)
            print("PRIVATE_OPENMONTAGE_HANDOFF_PREPARED:", out)
        else:
            render(manifest, directory)
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print("AUDIOBOOK_OPENMONTAGE_BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
