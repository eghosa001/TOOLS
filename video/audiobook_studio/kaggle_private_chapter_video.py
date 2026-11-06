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
ALLOWED = {"preflight", "audition", "chapter", "images", "video"}
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
    if phase in {"audition", "chapter"}:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "qwen-tts", "soundfile", "accelerate"], check=True)
        cmd = [ROOT / "gpu_narration.py", "--kit", kit, "--out", out, "--mode", phase]
        if phase == "chapter":
            cmd += ["--book", book, "--chapter", chapter]
        call(*cmd)
    elif phase == "images":
        # Original, passage-linked illustrations only; visual approval remains pending.
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers", "transformers", "accelerate", "safetensors"], check=True)
        call(ROOT / "generate_scene_images.py", "--storyboards", boards, "--book", book, "--chapter", chapter, "--max-images", max_images)
    elif phase == "video":
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
