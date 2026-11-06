#!/usr/bin/env python3
"""Run approved Audiobook Studio scripts INSIDE a PRIVATE Kaggle GPU notebook.

The manuscript ZIP must arrive from a private Kaggle dataset. This PUBLIC code
contains no story text and never releases/publicly uploads media.
Config is provided by the trusted GitHub Actions wrapper.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path("/kaggle/working/AUDIOBOOK_STUDIO")
ALLOWED = {"preflight", "audition", "chapter", "images", "video", "full"}
CONFIG = globals().get("CONFIG", {"phase": "preflight", "book": 1, "chapter": 1, "max_images": 14})

def verified_extract(zpath: pathlib.Path, target: pathlib.Path):
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        dest = target.resolve()
        for info in z.infolist():
            p = (dest / info.filename).resolve()
            if not p.is_relative_to(dest):
                raise ValueError("Unsafe path in private Kaggle ZIP")
        z.extractall(target)

def call(*args):
    subprocess.run([sys.executable, *map(str, args)], check=True)

def main():
    phase = str(CONFIG.get("phase", "preflight"))
    book = int(CONFIG.get("book", 1))
    chapter = int(CONFIG.get("chapter", 1))
    max_images = int(CONFIG.get("max_images", 14))
    if phase not in ALLOWED or book not in range(1, 5) or chapter not in range(1, 5):
        raise ValueError("Invalid phase/book/chapter")
    source = next(pathlib.Path("/kaggle/input").rglob("AUDIOBOOK_STUDIO_QWEN_VIDEO_PIPELINE_2026-11-06.zip"), None)
    if source is None:
        raise FileNotFoundError("Private approved-source ZIP missing. Refuse any fabricated narration/video.")
    verified_extract(source, ROOT)
    # Owner-approved Ryan reference and fixed audiobook narration profile are required.
    # Manuscripts remain private. A stale ZIP must fail rather than synthesize a
    # merely similar voice with the old/different voice-direction instruction.
    import ast
    lock = ROOT / "VOICE_REFERENCE" / "RYAN_VOICE_STANDARD_APPROVED.json"
    if not lock.exists():
        raise RuntimeError("Private source ZIP predates owner's Ryan voice approval; replace with voice-locked package")
    profile = json.loads(lock.read_text(encoding="utf-8"))
    expected_model = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
    expected_instruct = "A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting."
    expected_hashes = {
        "male_ryan_original_qwen_audition.mp3": "80485deabb10b8d181603ff82f55fb7b1c2e8ce3e899e077270bef1feb7c3886",
        "male_ryan_original_qwen_audition.wav": "779c5b3a6033a4483fa31d6d7b295c3b9fcddc60dbfc2007af19cfb2ca8b9bfa",
    }
    if (profile.get("profile_id") != "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1"
        or profile.get("model") != expected_model
        or profile.get("speaker") != "Ryan"
        or profile.get("language") != "English"
        or profile.get("instruct") != expected_instruct
        or profile.get("approval_scope") != "NARRATOR_TIMBRE_AND_DELIVERY_ONLY"):
        raise RuntimeError("Unapproved or modified Qwen Ryan voice profile")
    for filename, expected_sha in expected_hashes.items():
        p = ROOT / "VOICE_REFERENCE" / filename
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError("Owner-approved Ryan reference audio missing or modified: " + filename)
    for rel, direction in (
        ("gpu_narration.py", "INSTRUCTION"),
        ("approved_scripts/qwen3_audiobook_runner.py", "INSTRUCT"),
    ):
        constants = {}
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        constants[target.id] = node.value.value
        if any((
            constants.get("MODEL") != expected_model,
            constants.get("SPEAKER") != "Ryan",
            constants.get("LANGUAGE") != "English",
            constants.get(direction) != expected_instruct,
        )):
            raise RuntimeError("Chapter synthesis is not pinned to approved Ryan audition: " + rel)
    print("OWNER_APPROVED_RYAN_PROFILE_VERIFIED", profile["profile_id"], flush=True)
    progress = next(pathlib.Path("/kaggle/input").rglob("AUDIOBOOK_PROGRESS_BUNDLE.zip"), None)
    if progress is not None:
        verified_extract(progress, ROOT)
    kit = ROOT / "approved_scripts"
    out = ROOT / "output"
    boards = ROOT / "STORYBOARDS"
    manifests = sorted(kit.glob("BOOK_*/CHAPTER_*/narration_manifest.json"))
    if len(manifests) != 16:
        raise RuntimeError(f"Expected 16 canonical source manifests, got {len(manifests)}")
    # Preflight checks every source hash WITHOUT loading a GPU model.
    call(ROOT / "gpu_narration.py", "--kit", kit, "--out", out, "--mode", "preflight")
    if phase in {"audition", "chapter", "full"}:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "qwen-tts", "soundfile", "accelerate"], check=True)
        cmd = [ROOT / "gpu_narration.py", "--kit", kit, "--out", out, "--mode", phase]
        if phase in {"chapter", "full"}:
            cmd += ["--book", book, "--chapter", chapter]
        call(*cmd)
    if phase in {"images", "full"}:
        # Original, passage-linked illustrations only; visual approval remains pending.
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers", "transformers", "accelerate", "safetensors"], check=True)
        call(ROOT / "generate_scene_images.py", "--storyboards", boards, "--book", book, "--chapter", chapter, "--max-images", max_images)
    if phase in {"video", "full"}:
        board = boards / f"BOOK_{book:02d}" / f"CHAPTER_{chapter:02d}" / "visual_storyboard.json"
        found = list(out.glob(f"BOOK_{book:02d}_*/CHAPTER_{chapter:02d}_*"))
        if len(found) != 1:
            raise FileNotFoundError("Resume private narrated chapter output before video assembly")
        folder = found[0]
        call(ROOT / "assemble_chapter_video.py", "--board", board,
             "--timeline", folder / "chapter_timeline.json",
             "--audio", folder / "chapter_male_ryan_unapproved.mp3",
             "--out", out / f"BOOK_{book:02d}_CHAPTER_{chapter:02d}_DRAFT_REVIEW.mp4")
    # Save private resume bundle; includes story-sensitive timings and illustrations.
    bundle = ROOT / "AUDIOBOOK_PROGRESS_BUNDLE.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=5) as z:
        for folder in (out, boards):
            if folder.exists():
                for f in folder.rglob("*"):
                    if f.is_file():
                        z.write(f, f.relative_to(ROOT))
    report = {"phase": phase, "book": book, "chapter": chapter,
              "canonical_chapters_verified": 16, "private_input_loaded": True,
              "video_publicly_published": False, "human_voice_approved": False,
              "final_media_approved": False}
    (ROOT / "PRODUCTION_RUN_REPORT.json").write_text(json.dumps(report, indent=2))
    print("PRIVATE_AUDIOBOOK_STAGE_COMPLETE", json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
