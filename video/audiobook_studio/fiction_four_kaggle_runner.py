#!/usr/bin/env python3
"""Private, manually gated Kaggle runner for the FIRST FOUR LONG NOVELS.

Public repository contains this reusable tool only. All manuscript text,
voice references, illustration prompts, generated audio and video stay in
private Kaggle datasets/kernel outputs. It deliberately does not use the
separate four-novella/16-part Audiobook Studio source.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import wave
import zipfile

ROOT = Path(os.environ.get("FICTION_WORK_DIR", "/kaggle/working/fiction-four"))
INPUT = Path(os.environ.get("FICTION_INPUT_DIR", "/kaggle/input"))
SOURCE_NAME = "FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip"
PROGRESS_NAME = "FICTION_FOUR_NOVELS_PROGRESS.zip"
COLLECTION = "fiction-studio-first-four-long-novels"
BOOKS = {
    "disciple": "The Disciple Who Lost His Name",
    "one-coin": "One Coin for a Kingdom",
    "gatekeeper": "The Last Gatekeeper of Black Mountain",
    "reborn": "Reborn Before the Fall",
}
VOICE_ID = "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1"
MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
DIRECTION = "A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting."
REF_HASHES = {
    "male_ryan_original_qwen_audition.mp3": "80485deabb10b8d181603ff82f55fb7b1c2e8ce3e899e077270bef1feb7c3886",
    "male_ryan_original_qwen_audition.wav": "779c5b3a6033a4483fa31d6d7b295c3b9fcddc60dbfc2007af19cfb2ca8b9bfa",
}
CONFIG = globals().get("CONFIG", {})
PHASES = {"preflight", "narrate", "illustrate", "render", "verify"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("Invalid private bundle path")
    base = root.resolve()
    result = (base / name).resolve()
    if result == base or not result.is_relative_to(base):
        raise ValueError("Bundle path escapes private workspace")
    return result


def unpack_private(name: str, target: Path, required: bool) -> bool:
    candidates = list(INPUT.rglob(name)) if INPUT.exists() else []
    if not candidates:
        if required:
            raise FileNotFoundError(
                "Missing PRIVATE " + name + " on Kaggle. Do not use the legacy novella source ZIP."
            )
        return False
    if len(candidates) != 1:
        raise RuntimeError("Multiple private bundles with the same filename")
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(candidates[0]) as z:
        for item in z.infolist():
            if item.is_symlink() if hasattr(item, "is_symlink") else False:
                raise ValueError("Symlinks are forbidden in private bundles")
            dest = safe_path(target, item.filename.rstrip("/"))
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as stream, dest.open("wb") as out:
                    shutil.copyfileobj(stream, out)
    return True


def load_source():
    source = ROOT / "source"
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Long-novel manifest.json missing. Old 16-part novella pack is NOT compatible.")
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    if m.get("schema_version") != 1 or m.get("collection") != COLLECTION:
        raise ValueError("Wrong private collection/version: expected the FIRST FOUR LONG NOVELS")
    entries = m.get("books")
    if not isinstance(entries, list) or len(entries) != len(BOOKS):
        raise ValueError("Private manifest must identify all four long novels")
    mapping = {}
    for item in entries:
        slug = item.get("slug")
        if slug not in BOOKS or slug in mapping or item.get("title") != BOOKS[slug]:
            raise ValueError("Wrong, duplicated or renamed long-novel source")
        path = safe_path(source, item.get("file", ""))
        expected = item.get("sha256", "")
        if not re.fullmatch("[0-9a-f]{64}", expected) or not path.is_file():
            raise ValueError("Approved text file/hash missing: " + slug)
        if sha256(path) != expected:
            raise RuntimeError("Source hash mismatch; manuscript modified without approval: " + slug)
        if not path.read_text(encoding="utf-8").strip():
            raise ValueError("Empty manuscript: " + slug)
        mapping[slug] = item
    if set(mapping) != set(BOOKS):
        raise ValueError("Manifest does not list exactly the first four long novels")
    return source, mapping


def verify_voice(source: Path):
    lock = safe_path(source, "VOICE_REFERENCE/RYAN_VOICE_STANDARD_APPROVED.json")
    if not lock.is_file():
        raise RuntimeError("Approved male Ryan voice reference not provided in PRIVATE source")
    m = json.loads(lock.read_text(encoding="utf-8"))
    required = {
        "profile_id": VOICE_ID, "model": MODEL, "speaker": "Ryan",
        "language": "English", "instruct": DIRECTION,
        "approval_scope": "NARRATOR_TIMBRE_AND_DELIVERY_ONLY",
    }
    for k, v in required.items():
        if m.get(k) != v:
            raise RuntimeError("Owner-approved Ryan profile mismatch: " + k)
    for filename, digest in REF_HASHES.items():
        p = safe_path(source, "VOICE_REFERENCE/" + filename)
        if not p.is_file() or sha256(p) != digest:
            raise RuntimeError("Approved Ryan reference missing or changed: " + filename)


def chunks(text: str, max_words: int = 205):
    """Stable paragraph/sentence chunks, no padding or arbitrary chapter quotas."""
    if not 100 <= max_words <= 230:
        raise ValueError("Narration chunk upper bound must be 100–230 words")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text.strip()) if p.strip()]
    out, current, words = [], [], 0
    for para in paragraphs:
        pieces = re.split(r"(?<=[.!?])\s+(?=[\"'“‘(]?[A-Z0-9])", para)
        for piece in pieces:
            part = piece.strip()
            if not part:
                continue
            count = len(part.split())
            if count > max_words:
                raise ValueError("Oversized unbroken sentence; edit spoken script deliberately")
            if current and words + count > max_words:
                out.append(" ".join(current))
                current, words = [], 0
            current.append(part)
            words += count
    if current:
        out.append(" ".join(current))
    return out


def run(cmd: list[str], capture=False):
    p = subprocess.run(cmd, check=True, text=True, capture_output=capture)
    return p.stdout if capture else None


def media_seconds(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture=True)
    return float(out.strip())


def concat_file(paths: list[Path], target: Path, durations=None):
    # Paths are generated exclusively inside ROOT; ffmpeg concat syntax is escaped.
    lines = []
    for idx, path in enumerate(paths):
        if not path.is_file():
            raise FileNotFoundError("Required private media missing: " + str(path))
        lines.append("file '" + str(path.resolve()).replace("'", "'\\''") + "'")
        if durations is not None:
            lines.append("duration %.6f" % durations[idx])
    if durations:
        lines.append("file '" + str(paths[-1].resolve()).replace("'", "'\\''") + "'")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_approvals(source: Path, slug: str, book_hash: str, *, include_visuals=False):
    approval = safe_path(source, "approvals/" + slug + ".json")
    if not approval.is_file():
        raise RuntimeError("Explicit private owner approval missing: " + slug)
    a = json.loads(approval.read_text(encoding="utf-8"))
    if a.get("source_sha256") != book_hash or a.get("narration_approved") is not True:
        raise RuntimeError("Real narration approval/source hash required before rendering")
    if include_visuals and a.get("visuals_approved") is not True:
        raise RuntimeError("Owner visual approval required before video rendering")


def _valid_cached_wav(path: Path) -> bool:
    """Do not trust a file just because it has a WAV extension and >2kB."""
    try:
        with wave.open(str(path), "rb") as sound:
            return (sound.getnchannels() == 1 and sound.getsampwidth() == 2
                    and sound.getframerate() == 24000
                    and sound.getnframes() >= 24000 // 4)
    except (EOFError, OSError, wave.Error):
        return False


def voice_generate(source: Path, slug: str, book: dict, text: str, start: int, limit: int):
    # Plan and inspect cached segments BEFORE importing/initializing a large GPU model.
    started = time.monotonic()
    all_chunks = chunks(text)
    if start >= len(all_chunks) or limit < 1 or limit > 16:
        raise ValueError("Invalid narration chunk window")
    outdir = ROOT / "output" / slug / "chunks"
    outdir.mkdir(parents=True, exist_ok=True)
    plan = []
    for index, spoken in enumerate(all_chunks):
        key = hashlib.sha256(json.dumps([MODEL, "Ryan", DIRECTION, spoken],
                               ensure_ascii=False).encode()).hexdigest()[:20]
        plan.append({"index": index, "text_sha256": hashlib.sha256(spoken.encode()).hexdigest(),
                     "file": f"{index:05d}-{key}.wav", "words": len(spoken.split())})
    plan_path = outdir.parent / "narration_plan.json"
    desired_plan = {"source_sha256": book["sha256"], "voice_profile": VOICE_ID, "chunks": plan}
    if plan_path.is_file():
        existing_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if existing_plan != desired_plan:
            raise RuntimeError("Old narration checkpoint does not match the current manuscript/voice")
    else:
        plan_path.write_text(json.dumps(desired_plan, indent=2), encoding="utf-8")
    jobs = plan[start:min(start + limit, len(all_chunks))]
    missing = [job for job in jobs if not _valid_cached_wav(outdir / job["file"])]
    if not missing:
        return {"total_chunks": len(plan), "generated_window": [start, min(start + limit, len(plan))],
                "cache_hits": len(jobs), "generated": 0, "gpu_model_loaded": False,
                "elapsed_seconds": round(time.monotonic() - started, 2)}
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel
    if not torch.cuda.is_available():
        raise RuntimeError("Qwen narration requires Kaggle GPU; no substituted voice permitted")
    major = torch.cuda.get_device_capability(0)[0]
    dtype = torch.bfloat16 if major >= 8 else torch.float32
    model = Qwen3TTSModel.from_pretrained(
        MODEL, device_map="cuda:0", dtype=dtype, attn_implementation="sdpa"
    )
    for index in range(start, min(start + limit, len(all_chunks))):
        job = plan[index]
        target = outdir / job["file"]
        if _valid_cached_wav(target):
            continue
        if target.exists():
            target.unlink()  # Corrupt or truncated cache; replace atomically.
        torch.manual_seed(20261107 + index)
        wav, rate = model.generate_custom_voice(
            text=all_chunks[index], speaker="Ryan", language="English", instruct=DIRECTION)
        audio = np.asarray(wav[0])
        if audio.size < rate // 4 or not np.isfinite(audio).all():
            raise RuntimeError("Generated empty/non-finite Qwen output at " + str(index))
        tmp = target.with_suffix(".tmp.wav")
        sf.write(str(tmp), audio, rate, subtype="PCM_16")
        if not _valid_cached_wav(tmp):
            tmp.unlink(missing_ok=True)
            raise RuntimeError("Qwen produced an invalid WAV at chunk " + str(index))
        tmp.replace(target)
    del model
    torch.cuda.empty_cache()
    return {"total_chunks": len(plan), "generated_window": [start, min(start + limit, len(plan))],
            "cache_hits": len(jobs) - len(missing), "generated": len(missing),
            "gpu_model_loaded": True, "elapsed_seconds": round(time.monotonic() - started, 2)}


def complete_audio(slug: str, book: dict):
    folder = ROOT / "output" / slug
    plan = json.loads((folder / "narration_plan.json").read_text(encoding="utf-8"))
    if plan["source_sha256"] != book["sha256"]:
        raise RuntimeError("Narration source differs from approved manuscript")
    files = [folder / "chunks" / c["file"] for c in plan["chunks"]]
    if not files or not all(f.is_file() for f in files):
        missing = sum(not f.is_file() for f in files)
        raise RuntimeError(f"Incomplete Qwen narration: {missing} chunk(s) missing")
    concat_file(files, folder / "chunks.txt")
    mastered = folder / "narration_review.m4a"
    if not mastered.is_file():
        # A 192k AAC master is dramatically smaller than a stereo 48k PCM WAV.
        # Keep original PCM chunks for auditing; do not time-stretch narration.
        tmp = folder / "narration_review.partial.m4a"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-f", "concat", "-safe", "0", "-i", str(folder / "chunks.txt"),
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(tmp)])
        tmp.replace(mastered)
    durations = [media_seconds(f) for f in files]
    if abs(media_seconds(mastered) - sum(durations)) > max(3.0, len(files) * 0.04):
        raise RuntimeError("Master audio duration disagrees with the source chunk timing")
    return mastered, durations


def load_board(source: Path, slug: str, chunk_count: int):
    path = safe_path(source, "storyboards/" + slug + ".json")
    if not path.is_file():
        raise FileNotFoundError("Source-linked private storyboard missing: " + slug)
    m = json.loads(path.read_text(encoding="utf-8"))
    if m.get("slug") != slug or m.get("storyboard_approved") is not True:
        raise ValueError("Storyboards must identify the chosen novel and be approved")
    scenes = m.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Storyboard has no scene images")
    last = 0
    for i, item in enumerate(scenes):
        a, b = item.get("start_chunk"), item.get("end_chunk")
        if not isinstance(a, int) or not isinstance(b, int) or a != last or b <= a or b > chunk_count:
            raise ValueError("Gaps, overlaps or out-of-range visual scene " + str(i))
        safe_path(source, item.get("file", ""))
        last = b
    if last != chunk_count:
        raise ValueError("Visual scenes must cover every spoken chunk")
    return scenes, m


def illustrate(source: Path, slug: str, chunk_count: int, first: int, count: int):
    scenes, board = load_board(source, slug, chunk_count)
    if not board.get("image_model_id") or not board.get("image_model_license_reviewed"):
        raise RuntimeError("Select and rights-review a private image model before illustration")
    if not board.get("continuity_references_approved"):
        raise RuntimeError("Character/style continuity references need owner approval")
    if count < 1 or count > 8:
        raise ValueError("Illustration batch must contain 1–8 scenes")
    import torch
    from diffusers import AutoPipelineForText2Image
    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle GPU required for source-linked illustration")
    pipe = AutoPipelineForText2Image.from_pretrained(
        board["image_model_id"], torch_dtype=torch.float16, use_safetensors=True)
    pipe.enable_model_cpu_offload()
    outputs = []
    for idx in range(first, min(first + count, len(scenes))):
        scene = scenes[idx]
        if not scene.get("prompt") or not scene.get("visual_approved"):
            raise RuntimeError("Illustration prompt approval missing for shot " + str(idx))
        dest = ROOT / "output" / slug / "art" / ("%04d.png" % idx)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.is_file():
            generator = torch.Generator(device="cpu").manual_seed(int(scene.get("seed", idx)))
            image = pipe(scene["prompt"], generator=generator,
                         num_inference_steps=int(board.get("inference_steps", 20))).images[0]
            image.save(dest)
        outputs.append(str(dest.relative_to(ROOT)))
    return {"illustrated": outputs, "media_approval": False}


def render(source: Path, slug: str, book: dict):
    verify_approvals(source, slug, book["sha256"], include_visuals=True)
    audio, chunk_durations = complete_audio(slug, book)
    scenes, _ = load_board(source, slug, len(chunk_durations))
    image_paths, durations = [], []
    for idx, scene in enumerate(scenes):
        image = ROOT / "output" / slug / "art" / ("%04d.png" % idx)
        if not image.is_file():
            image = safe_path(source, scene["file"])
        if not image.is_file():
            raise FileNotFoundError("Approved illustration missing: " + str(idx))
        image_paths.append(image)
        durations.append(sum(chunk_durations[scene["start_chunk"]:scene["end_chunk"]]))
    target = ROOT / "output" / slug / (slug + "_review_only.mp4")
    lst = target.with_suffix(".images.txt")
    concat_file(image_paths, lst, durations)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "concat", "-safe", "0", "-i", str(lst),
         "-i", str(audio),
         "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
                "fps=24,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-c:a", "copy", "-t", str(media_seconds(audio)),
         "-movflags", "+faststart", str(target)])
    return target


def output_bundle():
    # Private Kaggle *kernel output*, never a public GitHub artifact.
    path = ROOT / PROGRESS_NAME
    with zipfile.ZipFile(path, "w") as z:
        folder = ROOT / "output"
        if folder.exists():
            for f in sorted(folder.rglob("*")):
                if f.is_file():
                    # Already-compressed images/video/audio: save CPU time and memory.
                    compress = (zipfile.ZIP_STORED if f.suffix.lower() in
                                {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".m4a", ".mp3", ".zip"}
                                else zipfile.ZIP_DEFLATED)
                    z.write(f, f.relative_to(ROOT), compress_type=compress)
    return path


def main():
    phase = str(CONFIG.get("phase", "preflight"))
    slug = str(CONFIG.get("book", "disciple"))
    start = int(CONFIG.get("start", 0))
    limit = int(CONFIG.get("limit", 8))
    if phase not in PHASES or slug not in BOOKS or start < 0 or limit < 1 or limit > 16:
        raise ValueError("Invalid manual phase/novel/chunk range")
    ROOT.mkdir(parents=True, exist_ok=True)
    unpack_private(SOURCE_NAME, ROOT / "source", required=True)
    source, entries = load_source()
    verify_voice(source)
    # Load optional private progress. The user controls promotion of output
    # back into a PRIVATE Kaggle progress dataset, never public GitHub.
    unpack_private(PROGRESS_NAME, ROOT, required=False)
    selected = entries[slug]
    text = safe_path(source, selected["file"]).read_text(encoding="utf-8")
    plan = chunks(text)
    result = {"status": "preflight_ok", "chunks": len(plan)}
    if phase == "narrate":
        result = voice_generate(source, slug, selected, text, start, limit)
    elif phase == "illustrate":
        result = illustrate(source, slug, len(plan), start, limit)
    elif phase == "render":
        movie = render(source, slug, selected)
        result = {"review_movie": str(movie), "duration_s": media_seconds(movie), "sha256": sha256(movie)}
    elif phase == "verify":
        folder = ROOT / "output" / slug
        movie = folder / (slug + "_review_only.mp4")
        if not movie.exists():
            raise FileNotFoundError("No actual private MP4 to verify")
        result = {"sha256": sha256(movie), "duration_s": media_seconds(movie),
                  "audio_passed_full_listening": False, "final_video_approved": False}
    # Preflight has no media to checkpoint. Do not recompress GB of progress
    # on a CPU-only sanity check.
    archive = output_bundle() if phase != "preflight" else None
    report = {"collection": COLLECTION, "phase": phase, "book": slug,
              "source_sha256": selected["sha256"],
              "voice_profile": VOICE_ID, "production": result,
              "progress_zip": archive.name if archive else None,
              "human_listening_completed": False, "publicly_published": False}
    (ROOT / "PRIVATE_STAGE_REPORT.json").write_text(json.dumps(report, indent=2))
    print("FICTION_FOUR_PRIVATE_STAGE", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
