"""Private cost-first Modal runner for the existing approved manhua audiobook pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import modal

from video.audiobook_studio.manhua_pipeline.core import (
    VOICE, open_package, dense_illustration_plan, split_chunks, validate_slug
)

# GPU-only dollars/second, Modal public pricing 2026-11-07.
RATES = {"L4": 0.000222, "A10": 0.000306, "L40S": 0.000542,
         "A100-40GB": 0.000583, "H100": 0.001097}
TTS_SECONDS, ART_SECONDS = 1500, 900
SOURCE = "audiobook-manhua-private-sources"
RYAN = "audiobook-manhua-private-ryan"
ART = "audiobook-manhua-private-art"
REVIEWS = "audiobook-manhua-private-reviews"

source_vol = modal.Volume.from_name(SOURCE, create_if_missing=True)
ryan_vol = modal.Volume.from_name(RYAN, create_if_missing=True)
art_vol = modal.Volume.from_name(ART, create_if_missing=True)
review_vol = modal.Volume.from_name(REVIEWS, create_if_missing=True)
tts_model_vol = modal.Volume.from_name("audiobook-manhua-qwen-cache", create_if_missing=True)
art_model_vol = modal.Volume.from_name("audiobook-manhua-art-cache", create_if_missing=True)

def ship_code(image):
    for path in (
        "video/audiobook_studio/episode_fastlane.py",
        "video/audiobook_studio/manhua_pipeline/core.py",
        "video/audiobook_studio/manhua_pipeline/visual_quality.py",
        "video/audiobook_studio/manhua_pipeline/kaggle_runner.py",
        "video/audiobook_studio/manhua_pipeline/assemble_existing.py",
    ):
        image = image.add_local_file(path, remote_path="/root/" + path)
    return image.env({"PYTHONPATH": "/root"})

cpu_image = ship_code(modal.Image.debian_slim(python_version="3.11").apt_install("ffmpeg"))
gpu_image = ship_code(
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0", "fonts-dejavu-core")
    .pip_install("torch>=2.5.1,<3", "qwen-tts", "numpy", "soundfile",
                 "accelerate", "diffusers", "transformers", "safetensors",
                 "pillow", "sentencepiece", "protobuf")
)
app = modal.App("audiobook-manhua-private")

def budget_guard(tts_gpu="L4", art_gpu="L4", maximum_usd=0.80):
    if tts_gpu not in RATES or art_gpu not in RATES:
        raise ValueError("Unsupported GPU")
    if not 0 < maximum_usd <= 3:
        raise ValueError("Invalid per-episode GPU budget")
    worst = TTS_SECONDS * RATES[tts_gpu] + ART_SECONDS * RATES[art_gpu]
    if worst > maximum_usd:
        raise ValueError("GPU timeout-price envelope exceeds requested budget")
    # CPU, RAM, cold starts, and other billing remain additional;
    # configure a separate hard spend limit in Modal Billing settings.
    return {"voice_gpu": tts_gpu, "art_gpu": art_gpu,
            "max_gpu_envelope_usd": round(worst, 3),
            "cpu_and_ram_included": False}

def prepare(story_id, episode):
    validate_slug(story_id)
    file = Path("/private/source") / story_id / "MANHUA_STORY_PACKAGE.zip"
    if not file.is_file():
        raise FileNotFoundError("Private MANHUA_STORY_PACKAGE.zip missing from Modal source volume")
    meta, script, refs = open_package(file, expected_story_id=story_id, episode=episode)
    if not meta.get("image_model_rights_reviewed"):
        raise ValueError("Commercial model rights not yet checked")
    parts = split_chunks(script)
    scenes = dense_illustration_plan(parts, style=meta["style"], characters=meta.get("characters"),
                        briefs=(meta.get("scene_briefs") or {}).get(str(episode)))
    # Dense illustrations already carry their precise, non-overlapping spoken
    # passages. Do not overwrite each with the entire 170-word TTS chunk.
    return meta, parts, scenes, refs

def directory(root, meta, episode):
    source_hash = meta["episodes"][episode-1]["sha256"]
    return Path(root) / meta["story_id"] / ("ep%03d-" % episode + source_hash[:16])


def ensure_full_story_illustration_manifest(meta, story_id, source_archive, art_root):
    """Create the manifest automatically once every story scene image exists.

    The owner has explicitly preapproved every assistant-generated image. This
    writes an owner-authorization record, NOT a claim of human pixel inspection.
    """
    validate_slug(story_id)
    art_root = Path(art_root)
    manifest_path = art_root / story_id / "FULL_STORY_ILLUSTRATIONS_APPROVED.json"
    if manifest_path.exists():
        return manifest_path
    records = {}
    for episode_meta in meta.get("episodes", []):
        episode = episode_meta["number"]
        _, source, _ = open_package(
            source_archive, expected_story_id=story_id, episode=episode)
        scenes = dense_illustration_plan(
            split_chunks(source), style=meta["style"],
            characters=meta.get("characters"),
            briefs=(meta.get("scene_briefs") or {}).get(str(episode)))
        entry = {"source_sha256": episode_meta["sha256"], "scenes": {}}
        image_dir = directory(art_root, meta, episode) / "illustrations"
        for scene in scenes:
            filename = f"scene-{scene['scene']:04}-{scene['key']}.png"
            path = image_dir / filename
            if not path.is_file():
                raise RuntimeError(
                    "FULL_STORY_ILLUSTRATIONS_FILE_MISSING: "
                    f"episode {episode} scene {scene['scene']}")
            entry["scenes"][str(scene["scene"])] = {
                "source_sha256": scene["source_sha256"],
                "file": "illustrations/" + filename,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        records[str(episode)] = entry
    if not records:
        raise RuntimeError("FULL_STORY_ILLUSTRATIONS_EMPTY")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "full-story-illustrations-v1",
        "story_id": story_id,
        "full_source_sha256": meta["full_source_sha256"],
        "owner_artwork_approval": "blanket_preapproved",
        "episodes": records}
    temp = manifest_path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2), encoding="utf-8")
    temp.replace(manifest_path)
    return manifest_path


def require_complete_story_illustrations(meta, story_id, source_archive, art_root):
    """Fail closed until all episodes/scenes are hash-bound; owner preapproved art."""
    validate_slug(story_id)
    source_archive, art_root = Path(source_archive), Path(art_root)
    approved_file = art_root / story_id / "FULL_STORY_ILLUSTRATIONS_APPROVED.json"
    if not approved_file.is_file():
        raise RuntimeError("FULL_STORY_ILLUSTRATIONS_MISSING: complete images before audio/video")
    approval = json.loads(approved_file.read_text(encoding="utf-8"))
    if (approval.get("schema") != "full-story-illustrations-v1"
            or approval.get("story_id") != story_id
            or approval.get("full_source_sha256") != meta.get("full_source_sha256")
            or not (approval.get("owner_artwork_approval") == "blanket_preapproved"
                    or approval.get("human_visual_review_approved") is True)):
        raise RuntimeError("FULL_STORY_ILLUSTRATIONS_UNAPPROVED_OR_STALE")
    episodes = meta.get("episodes") or []
    records = approval.get("episodes")
    if not isinstance(records, dict) or set(records) != {str(e["number"]) for e in episodes}:
        raise RuntimeError("FULL_STORY_ILLUSTRATIONS_INCOMPLETE_EPISODES")
    verified = 0
    for entry in episodes:
        ep = entry["number"]
        source_meta, script, _ = open_package(source_archive, expected_story_id=story_id, episode=ep)
        if source_meta.get("full_source_sha256") != meta["full_source_sha256"]:
            raise RuntimeError("FULL_STORY_MANUSCRIPT_MISMATCH")
        scenes = dense_illustration_plan(split_chunks(script), style=meta["style"],
                            characters=meta.get("characters"),
                            briefs=(meta.get("scene_briefs") or {}).get(str(ep)))
        episode_approval = records[str(ep)]
        if episode_approval.get("source_sha256") != entry["sha256"]:
            raise RuntimeError("FULL_STORY_ILLUSTRATIONS_EPISODE_SOURCE_MISMATCH")
        scene_records = episode_approval.get("scenes")
        if not isinstance(scene_records, dict) or set(scene_records) != {str(item["scene"]) for item in scenes}:
            raise RuntimeError("FULL_STORY_ILLUSTRATIONS_MISSING_SCENES")
        episode_dir = directory(art_root, meta, ep).resolve()
        for item in scenes:
            record = scene_records[str(item["scene"])]
            if record.get("source_sha256") != item["source_sha256"]:
                raise RuntimeError("FULL_STORY_ILLUSTRATIONS_SCENE_SOURCE_MISMATCH")
            rel = record.get("file")
            if (not isinstance(rel, str) or not rel or rel.startswith("/")
                    or "\\" in rel or ".." in Path(rel).parts):
                raise RuntimeError("UNSAFE_ILLUSTRATION_PATH")
            image = (episode_dir / rel).resolve()
            if not image.is_relative_to(episode_dir) or image.suffix.lower() not in (".png", ".webp", ".jpg", ".jpeg"):
                raise RuntimeError("UNSAFE_ILLUSTRATION_FILE")
            if not image.is_file():
                raise RuntimeError("FULL_STORY_ILLUSTRATIONS_FILE_MISSING")
            if hashlib.sha256(image.read_bytes()).hexdigest() != record.get("sha256"):
                raise RuntimeError("FULL_STORY_ILLUSTRATIONS_IMAGE_HASH_MISMATCH")
            verified += 1
    if not verified:
        raise RuntimeError("FULL_STORY_ILLUSTRATIONS_EMPTY")
    return {"status": "FULL_STORY_ILLUSTRATIONS_VERIFIED", "story_id": story_id,
            "episodes": len(episodes), "scenes": verified,
            "full_source_sha256": meta["full_source_sha256"]}


@app.function(image=cpu_image, cpu=0.5, memory=1024, timeout=180,
              volumes={"/private": source_vol.with_mount_options(read_only=True),
                       "/art": art_vol},
              max_containers=1)
def verify_full_story_illustrations(story_id: str, episode: int):
    meta, _, _, _ = prepare(story_id, episode)
    archive = Path("/private/source") / story_id / "MANHUA_STORY_PACKAGE.zip"
    ensure_full_story_illustration_manifest(meta, story_id, archive, Path("/art"))
    result = require_complete_story_illustrations(meta, story_id, archive, Path("/art"))
    art_vol.commit()
    return result

@app.function(image=cpu_image, cpu=0.5, memory=1024, timeout=120,
              volumes={"/private": source_vol.with_mount_options(read_only=True)},
              max_containers=1)
def preflight(story_id: str, episode: int):
    meta, parts, scenes, refs = prepare(story_id, episode)
    return {"status": "PRIVATE_PREFLIGHT_PASS", "story_id": story_id,
            "episode": episode, "source_sha256": meta["episodes"][episode-1]["sha256"],
            "chunks": len(parts), "scenes": len(scenes), "references": len(refs),
            "total_episodes": len(meta["episodes"]),
            "voice_profile": VOICE, "gpu_used": False, "release_approved": False}

@app.function(image=gpu_image, gpu="L4", cpu=2, memory=8192, timeout=TTS_SECONDS,
              max_containers=1,
              volumes={"/private": source_vol.with_mount_options(read_only=True),
                       "/art": art_vol.with_mount_options(read_only=True),
                       "/ryan": ryan_vol, "/models": tts_model_vol},
              env={"HF_HOME": "/models", "MANHUA_GPU_SLOT": "0"})
def generate_ryan(story_id: str, episode: int):
    from video.audiobook_studio.manhua_pipeline import kaggle_runner as engine
    from video.audiobook_studio.episode_fastlane import sha256
    t0 = time.monotonic()
    meta, parts, _, _ = prepare(story_id, episode)
    require_complete_story_illustrations(meta, story_id,
        Path("/private/source") / story_id / "MANHUA_STORY_PACKAGE.zip", Path("/art"))
    dest = directory("/ryan", meta, episode)
    dest.mkdir(parents=True, exist_ok=True)
    files, durations = engine.voice_chunks(parts, dest, checkpoint=lambda *_: ryan_vol.commit())
    master = engine.master_audio(files, durations, dest)
    record = {"source_sha256": meta["episodes"][episode-1]["sha256"],
              "voice_profile": VOICE, "seconds": sum(durations),
              "durations": durations, "audio_sha256": sha256(master),
              "gpu_stage_wall_s": round(time.monotonic()-t0, 2)}
    (dest / "MODAL_RYAN.json").write_text(json.dumps(record, indent=2))
    ryan_vol.commit()
    tts_model_vol.commit()
    return {"source_sha256": record["source_sha256"],
            "seconds": round(record["seconds"], 2),
            "gpu_stage_wall_s": record["gpu_stage_wall_s"]}

@app.function(image=gpu_image, gpu="L4", cpu=2, memory=8192, timeout=ART_SECONDS,
              max_containers=1,
              volumes={"/private": source_vol.with_mount_options(read_only=True),
                       "/art": art_vol, "/models": art_model_vol},
              env={"HF_HOME": "/models", "MANHUA_GPU_SLOT": "0"})
def generate_art(story_id: str, episode: int, quality: str):
    from video.audiobook_studio.manhua_pipeline import kaggle_runner as engine
    if quality not in ("fast", "quality"):
        raise ValueError("Unknown visual mode")
    t0 = time.monotonic()
    meta, _, scenes, refs = prepare(story_id, episode)
    dest = directory("/art", meta, episode)
    dest.mkdir(parents=True, exist_ok=True)
    images, thumbnail, stats = engine.illustrate(
        meta, scenes, dest, refs, mode=quality, checkpoint=lambda *_: art_vol.commit())
    gate = engine.evaluate_visuals(scenes, images, thumbnail, dest)
    report = {"source_sha256": meta["episodes"][episode-1]["sha256"],
              "voice_profile": VOICE, "art": stats, "quality": quality,
              "visual_quality_gate": gate, "gpu_stage_wall_s": round(time.monotonic()-t0, 2)}
    (dest / "MODAL_ART.json").write_text(json.dumps(report, indent=2))
    engine.discard_unverified_art_from_cache(dest, images, thumbnail, gate)
    art_vol.commit()
    art_model_vol.commit()
    return {"source_sha256": report["source_sha256"], "scenes": len(scenes),
            "visual_quality_gate": gate, "gpu_stage_wall_s": report["gpu_stage_wall_s"]}

@app.function(image=cpu_image, cpu=4, memory=6144, timeout=1200, max_containers=1,
              volumes={"/private": source_vol.with_mount_options(read_only=True),
                       "/ryan": ryan_vol.with_mount_options(read_only=True),
                       "/art": art_vol.with_mount_options(read_only=True),
                       "/reviews": review_vol})
def assemble_private_review(story_id: str, episode: int):
    from video.audiobook_studio.manhua_pipeline import kaggle_runner as engine
    from video.audiobook_studio.manhua_pipeline.assemble_existing import assemble
    from video.audiobook_studio.episode_fastlane import sha256
    started = time.monotonic()
    meta, _, scenes, _ = prepare(story_id, episode)
    require_complete_story_illustrations(meta, story_id,
        Path("/private/source") / story_id / "MANHUA_STORY_PACKAGE.zip", Path("/art"))
    audio_dir = directory("/ryan", meta, episode)
    art_dir = directory("/art", meta, episode)
    audio = json.loads((audio_dir / "MODAL_RYAN.json").read_text())
    art = json.loads((art_dir / "MODAL_ART.json").read_text())
    required = meta["episodes"][episode-1]["sha256"]
    if audio["source_sha256"] != required or art["source_sha256"] != required:
        raise ValueError("Wrong episode source digest")
    if audio["voice_profile"] != VOICE or art["voice_profile"] != VOICE:
        raise ValueError("Approved Ryan profile mismatch")
    if art["visual_quality_gate"]["needs_correction"]:
        raise RuntimeError("Image QA hold: requires correction before assembly")
    scenes_images = sorted((art_dir / "illustrations").glob("scene-*.png"))
    if len(scenes_images) != len(scenes):
        raise ValueError("Incomplete image sequence")
    seconds = engine.scene_timeline(scenes, audio["durations"])
    # No repeated static background or 24-image-long episode may pass.
    if len(scenes_images) < len(seconds) or any(d > 10.0 for d in seconds):
        raise RuntimeError("ILLUSTRATION_CADENCE_FAILED")
    if len(set(sha256(image) for image in scenes_images)) != len(scenes_images):
        raise RuntimeError("DUPLICATED_ILLUSTRATIONS_IN_TIMELINE")
    target_dir = directory("/reviews", meta, episode)
    target_dir.mkdir(parents=True, exist_ok=True)
    timeline = target_dir / "PRIVATE_SCENE_TIMELINE.json"
    timeline.write_text(json.dumps([
        {"image": str(image.resolve()), "seconds": round(span, 6),
         "image_sha256": sha256(image), "source_sha256": scene["source_sha256"]}
        for image, span, scene in zip(scenes_images, seconds, scenes)], indent=2))
    video = target_dir / (story_id + "_ep%03d_MANHUA_REVIEW.mp4" % episode)
    args = argparse.Namespace(audio=str(audio_dir/"narration_review.m4a"), image=None,
                              timeline=str(timeline), thumbnail=str(art_dir/"THUMBNAIL_REVIEW.png"),
                              visual_qa_report=str(art_dir/"PRIVATE_VISUAL_QA_REPORT.json"),
                              require_visual_qa=True, output=str(video),
                              motion="none", preset="ultrafast", force=False)
    result = assemble(args)
    report = {"schema": "modal-private-review-v1", "story_id": story_id, "episode": episode,
              "source_sha256": required, "voice_profile": VOICE,
              "review_video": video.name, "review_video_sha256": sha256(video),
              "duration_s": result["duration_seconds"],
              "tts_source": audio["audio_sha256"],
              "assembly_wall_s": round(time.monotonic()-started, 2),
              "technical_review": result["technical_review"],
              "ready_for_youtube": False, "human_listening_approved": False,
              "visual_continuity_approved": False, "publicly_published": False}
    (target_dir/"MANHUA_REVIEW_REPORT.json").write_text(json.dumps(report, indent=2))
    review_vol.commit()
    return {"status": "PRIVATE_REVIEW_GENERATED", "story_id": story_id,
            "episode": episode, "duration_s": report["duration_s"],
            "assembly_wall_s": report["assembly_wall_s"], "video": video.name}

@app.local_entrypoint()
def main(story_id: str, episode: int = 1, phase: str = "preflight",
         quality: str = "quality", tts_gpu: str = "L4", art_gpu: str = "L4",
         max_gpu_cost: float = 0.80):
    """Story preflight -> whole-story art audit -> narration -> private review."""
    if phase not in ("preflight", "assets", "illustrations", "review") or not 1 <= episode <= 999:
        raise ValueError("Invalid phase/episode")
    result = preflight.remote(story_id, episode)
    print("PRIVATE_MODAL_PREFLIGHT", json.dumps(result), flush=True)
    if phase == "preflight":
        return
    complete_art = verify_full_story_illustrations.remote(story_id, episode)
    print("COMPLETE_STORY_ILLUSTRATION_GATE", json.dumps(complete_art), flush=True)
    if phase in ("assets", "illustrations"):
        # Read-only audit of pre-created artwork from private Drive. No media generation.
        return
    envelope = budget_guard(tts_gpu, art_gpu, max_gpu_cost)
    print("GPU_COST_ENVELOPE", json.dumps(envelope), flush=True)
    audio = generate_ryan.with_options(gpu=tts_gpu).remote(story_id, episode)
    print("PRIVATE_MODAL_AUDIO", json.dumps(audio), flush=True)
    print("PRIVATE_MODAL_REVIEW", json.dumps(
        assemble_private_review.remote(story_id, episode)), flush=True)
