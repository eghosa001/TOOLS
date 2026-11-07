#!/usr/bin/env python3
"""Generic private Kaggle runner: any approved original story -> 2D manhua review MP4.

A single Kaggle run may build a *private unapproved review*. No YouTube publish,
public manuscript upload, 3D, filler audio, or procedural replacement artwork.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
import zipfile

from video.audiobook_studio.episode_fastlane import chunk_key, validated_wav, sha256, validate_review_video
from video.audiobook_studio.manhua_pipeline.core import SCHEMA, BUNDLE, NEGATIVE, VOICE, digest, open_package, scene_plan, split_chunks, STYLES, validate_slug

WORK = Path(os.environ.get("MANHUA_WORK_DIR", "/kaggle/working/manhua-studio"))


def selected_gpu() -> tuple[int, str]:
    """Bind this worker to a physical GPU in its own Kaggle T4x2 runtime.

    Only GPU phases call this. CPU preflight remains GPU-independent.
    Independent Kaggle kernel sessions cannot access one another's GPUs.
    """
    import torch
    raw = os.environ.get("MANHUA_GPU_SLOT", "0")
    if raw not in ("0", "1"):
        raise RuntimeError("MANHUA_GPU_SLOT must be 0 or 1")
    slot = int(raw)
    if not torch.cuda.is_available() or slot >= torch.cuda.device_count():
        raise RuntimeError(f"Requested cuda:{slot} is unavailable in THIS Kaggle runtime")
    torch.cuda.set_device(slot)
    return slot, f"cuda:{slot}"
MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "Ryan"
LANGUAGE = "English"
INSTRUCTION = "A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting."
IMAGE_MODELS = {
    "fast": {"id": "stabilityai/sdxl-turbo", "steps": 3, "guidance": 0.0},
    "quality": {"id": "cagliostrolab/animagine-xl-3.1", "steps": 22, "guidance": 6.0},
}


def choose_image_memory_mode(*, free_bytes: int, total_bytes: int,
                             setting: str = "auto") -> str:
    """Fast GPU-resident quality generation only when memory margin is safe."""
    if setting not in ("auto", "offload"):
        raise ValueError("Image memory mode must be auto or offload")
    if (setting == "auto" and total_bytes >= 15 * 1024**3
            and free_bytes >= 14 * 1024**3):
        return "GPU_RESIDENT"
    return "CPU_OFFLOAD"


def select_tts_precision(*, cuda_major: int, setting: str = "auto") -> str:
    """Choose tensor-core inference precision without changing the Qwen model/voice.

    Tesla T4 (CUDA capability 7.5) has FP16 tensor cores but no native BF16.
    Retain FP32 as an explicit, conservative emergency rollback.
    """
    if setting not in ("auto", "fp16", "bf16", "fp32"):
        raise ValueError("TTS precision must be auto, fp16, bf16 or fp32")
    if setting == "auto":
        return "bf16" if cuda_major >= 8 else "fp16" if cuda_major >= 7 else "fp32"
    if setting == "bf16" and cuda_major < 8:
        raise ValueError("BF16 precision needs Ampere or later CUDA hardware")
    if setting == "fp16" and cuda_major < 7:
        raise ValueError("FP16 fast path not supported on this GPU")
    return setting


def run(args: list[str], *, output=False) -> str | None:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout if output else None


def find_source() -> Path:
    """Reuse the approved private bundle, including Kaggle-unpacked ZIP datasets.

    Kaggle datasets may unpack MANHUA_STORY_PACKAGE.zip into manifest.json
    and episodes/*.txt. Validate every episode against the signed-in-package
    SHA-256 manifest and reconstruct only in private Kaggle working storage.
    Never require a second upload or place manuscript bytes in GitHub logs.
    """
    path = Path(os.environ.get("MANHUA_INPUT_DIR", "/kaggle/input"))
    matches = sorted(path.rglob(BUNDLE)) if path.exists() else []
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise RuntimeError("Multiple private story packages: select one dataset")
    manifests = sorted(path.rglob("manifest.json")) if path.exists() else []
    if len(manifests) != 1:
        raise RuntimeError("Expected one verified private package ZIP or unpacked manifest")
    source = manifests[0]
    root = source.parent
    data = source.read_bytes()
    meta = json.loads(data)
    episodes = meta.get("episodes", [])
    if (meta.get("schema") != SCHEMA or meta.get("source_approved") is not True
            or not episodes or len(episodes) > 999):
        raise RuntimeError("Invalid or unapproved unpacked private manuscript")
    files = []
    for number, entry in enumerate(episodes, 1):
        name = entry.get("file", "")
        if name != f"episodes/ep{number:03}.txt":
            raise RuntimeError("Unsafe or out-of-order private episode path")
        raw = (root / name).read_bytes()
        if digest(raw) != entry.get("sha256"):
            raise RuntimeError("Private episode digest mismatch")
        files.append((name, raw))
    for ref in (meta.get("references") or {}).values():
        name = ref.get("file", "")
        item = Path(name)
        if (item.is_absolute() or ".." in item.parts or len(item.parts) != 2
                or item.parts[0] != "references" or item.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp")):
            raise RuntimeError("Unsafe private character reference path")
        raw = (root / item).read_bytes()
        if digest(raw) != ref.get("sha256"):
            raise RuntimeError("Private character reference digest mismatch")
        files.append((name, raw))
    if digest("\n\n".join(raw.decode("utf-8") for name, raw in files if name.startswith("episodes/")).encode("utf-8")) != meta.get("full_source_sha256"):
        raise RuntimeError("Full owner-approved manuscript digest mismatch")
    output = WORK / "verified-private-input" / BUNDLE
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial.zip")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", data)
        for name, raw in files:
            z.writestr(name, raw)
    temporary.replace(output)
    print("PRIVATE_KAGGLE_DATASET_REUSED", {
        "episodes": len(files), "all_source_hashes_verified": True}, flush=True)
    return output


def checkpoint_out(meta: dict, ep: dict, source_dir: Path) -> Path:
    # Every asset is bound to the EXACT episode source, never to a title alone.
    from video.audiobook_studio.episode_fastlane import efficient_checkpoint
    dest = WORK / "MANHUA_PROGRESS.zip"
    efficient_checkpoint(source_dir, dest, source_sha256=ep["sha256"], voice_profile=VOICE)
    # Archive OUTSIDE the checkpoint input tree: no recursive ZIP growth.
    episode_copy = WORK / "episode_checkpoints" / source_dir.parent.name / source_dir.name / "MANHUA_PROGRESS.zip"
    episode_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dest, episode_copy)
    return dest


def restore_cache(ep: dict, target: Path) -> bool:
    """Restore private SHA-bound cache whether Kaggle keeps or extracts the ZIP."""
    from video.audiobook_studio.episode_fastlane import inspect_checkpoint
    inputs = Path(os.environ.get("MANHUA_PROGRESS_INPUT_DIR", os.environ.get("MANHUA_INPUT_DIR", "/kaggle/input")))
    matches = list(inputs.rglob("MANHUA_PROGRESS.zip")) if inputs.exists() else []
    if not matches:
        manifests = list(inputs.rglob("__checkpoint_manifest.json")) if inputs.exists() else []
        if not manifests:
            return False
        if len(manifests) != 1:
            raise RuntimeError("Multiple extracted private checkpoints")
        manifest = manifests[0]
        meta = json.loads(manifest.read_bytes())
        if meta.get("source_sha256") != ep["sha256"] or meta.get("voice_profile") != VOICE:
            raise RuntimeError("Extracted checkpoint is from another episode or voice")
        raw_files = []
        for name, expected in (meta.get("files") or {}).items():
            item = Path(name)
            if item.is_absolute() or ".." in item.parts or "\\" in name:
                raise RuntimeError("Unsafe extracted checkpoint filename")
            raw = (manifest.parent / item).read_bytes()
            if digest(raw) != expected:
                raise RuntimeError("Extracted private checkpoint SHA mismatch")
            raw_files.append((name, raw))
        cached = WORK / "verified-private-progress" / "MANHUA_PROGRESS.zip"
        cached.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(cached, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("__checkpoint_manifest.json", manifest.read_bytes())
            for name, raw in raw_files:
                archive.writestr(name, raw)
        matches = [cached]
    if len(matches) != 1:
        raise RuntimeError("Multiple cache bundles; cannot select safely")
    inspect_checkpoint(matches[0], source_sha256=ep["sha256"], voice_profile=VOICE)
    with zipfile.ZipFile(matches[0]) as z:
        for name in z.namelist():
            if name == "__checkpoint_manifest.json":
                continue
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(name))
    print("MANHUA_PRIVATE_EPISODE_CACHE_REUSED", flush=True)
    return True


def voice_chunks(parts: list[dict], out: Path, *, checkpoint=None) -> tuple[list[Path], list[float]]:
    """Use cached Ryan speech FIRST; initialize one GPU model for remaining chunks."""
    paths = []
    for item in parts:
        key = chunk_key(item["text"], model=MODEL, speaker=SPEAKER, instruction=INSTRUCTION)
        paths.append(out / "narration" / f"{item['index']:04d}-{key}.wav")
    for file in paths:
        file.parent.mkdir(parents=True, exist_ok=True)
    need = [i for i, f in enumerate(paths) if not validated_wav(f)]
    if need:
        import numpy as np
        import soundfile as sf
        import torch
        from qwen_tts import Qwen3TTSModel
        if not torch.cuda.is_available():
            raise RuntimeError("Qwen Ryan narration requires a private Kaggle GPU")
        slot, device = selected_gpu()
        precision = select_tts_precision(
            cuda_major=torch.cuda.get_device_capability(slot)[0],
            setting=os.environ.get("MANHUA_TTS_PRECISION", "auto"))
        dtype = {"bf16": torch.bfloat16, "fp16": torch.float16,
                 "fp32": torch.float32}[precision]
        print("MANHUA_RYAN_INFERENCE_PRECISION", precision, flush=True)
        try:
            voice = Qwen3TTSModel.from_pretrained(
                MODEL, device_map=device, dtype=dtype,
                attn_implementation="sdpa")
        except (RuntimeError, ValueError) as exc:
            if precision != "fp16":
                raise
            # Do not abandon the production when an FP16 kernel is unsupported.
            print("MANHUA_TTS_FP16_LOAD_FALLBACK_FP32", type(exc).__name__, flush=True)
            torch.cuda.empty_cache()
            voice = Qwen3TTSModel.from_pretrained(
                MODEL, device_map=device, dtype=torch.float32,
                attn_implementation="sdpa")
            precision = "fp32"
        for order,i in enumerate(need, 1):
            torch.manual_seed(20261107 + i)
            chunk_started = time.monotonic()
            try:
                with torch.inference_mode():
                    waveforms, rate = voice.generate_custom_voice(text=parts[i]["text"],
                        speaker=SPEAKER, language=LANGUAGE, instruct=INSTRUCTION)
                arr = np.asarray(waveforms[0])
                if arr.size < rate // 4 or not np.isfinite(arr).all():
                    raise ValueError("Non-finite or empty Qwen Ryan segment")
            except (RuntimeError, ValueError) as exc:
                if precision != "fp16":
                    raise
                # Retry this same chunk at FP32, preserving all prior valid WAVs.
                # Never silently accept clipped, empty, or non-finite speech.
                print("MANHUA_TTS_FP16_CHUNK_FALLBACK_FP32",i + 1,type(exc).__name__,flush=True)
                del voice
                gc.collect()
                torch.cuda.empty_cache()
                voice = Qwen3TTSModel.from_pretrained(
                    MODEL, device_map=device, dtype=torch.float32,
                    attn_implementation="sdpa")
                precision = "fp32"
                torch.manual_seed(20261107 + i)
                with torch.inference_mode():
                    waveforms, rate = voice.generate_custom_voice(text=parts[i]["text"],
                        speaker=SPEAKER, language=LANGUAGE, instruct=INSTRUCTION)
                arr = np.asarray(waveforms[0])
                if arr.size < rate // 4 or not np.isfinite(arr).all():
                    raise RuntimeError("Bad Qwen Ryan audio segment: " + str(i))
            temp = paths[i].with_suffix(".partial.wav")
            sf.write(str(temp), arr, rate, subtype="PCM_16")
            if not validated_wav(temp):
                raise RuntimeError("Invalid Qwen Ryan 24k mono file: " + str(i))
            temp.replace(paths[i])
            print("MANHUA_RYAN_PROGRESS", i + 1, len(paths), flush=True)
            print("MANHUA_RYAN_CHUNK_SECONDS", i + 1,
                  round(time.monotonic()-chunk_started, 2), precision, flush=True)
            if checkpoint and (order % 6 == 0 or order == len(need)):
                checkpoint("narration", order, len(need))
        del voice
        gc.collect()
        torch.cuda.empty_cache()
    else:
        print("MANHUA_RYAN_ALL_CHUNKS_CACHED", len(paths), flush=True)
    durations=[]
    for f in paths:
        if not validated_wav(f):
            raise RuntimeError("Narrator WAV missing/corrupt after generation")
        with wave.open(str(f), "rb") as w:
            durations.append(w.getnframes() / w.getframerate())
    return paths, durations


def master_audio(files: list[Path], durations: list[float], out: Path) -> Path:
    master=out/"narration_review.m4a"
    if master.is_file() and master.stat().st_mtime >= max(f.stat().st_mtime for f in files):
        return master
    lines=[]
    for f in files:
        if "'" in str(f):
            raise ValueError("Unsupported quote in private audio path")
        lines.append("file '"+str(f.resolve())+"'")
    listing=out/"narration_concat.txt"
    listing.write_text("\n".join(lines)+"\n")
    tmp=out/"narration_review.partial.m4a"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0", "-i",str(listing),
         "-af","loudnorm=I=-16:TP=-1.5:LRA=11","-ar","48000","-ac","2","-c:a","aac","-b:a","160k",str(tmp)])
    tmp.replace(master)
    length=float(run(["ffprobe","-v","error","-show_entries","format=duration",
                    "-of","default=noprint_wrappers=1:nokey=1",str(master)],output=True).strip())
    if abs(length-sum(durations)) > max(2.0,len(durations)*.05):
        raise RuntimeError("Narration master duration mismatch")
    return master


def _model_run(pipe, cfg: dict, prompt: str, path: Path, *, seed: int, reference=None, size=None):
    import torch
    from PIL import Image
    kwargs={"prompt":prompt, "num_inference_steps":cfg["steps"],
            "guidance_scale":cfg["guidance"],
            "generator":torch.Generator(device="cpu").manual_seed(seed),
            "width":size[0], "height":size[1]}
    if cfg["guidance"] > 0:
        kwargs["negative_prompt"] = NEGATIVE
    if reference is not None:
        kwargs["ip_adapter_image"] = reference
    image=pipe(**kwargs).images[0].convert("RGB")
    temp=path.with_suffix(".partial.png")
    image.save(temp)
    if Image.open(temp).size != tuple(size):
        raise RuntimeError("Wrong generated art dimensions")
    temp.replace(path)


def illustrate(meta: dict, scenes: list[dict], roots: Path, refs: dict[str, bytes], *, mode="fast", retake_attempt: int = 0, checkpoint=None) -> tuple[list[Path], Path, dict]:
    """2D scene panels, character/reference reuse and separate dramatic thumbnail."""
    cfg=IMAGE_MODELS[mode]
    art=roots/"illustrations"
    art.mkdir(parents=True,exist_ok=True)
    pictures=[art/f"scene-{s['scene']:04}-{s['key']}.png" for s in scenes]
    thumb=roots/"THUMBNAIL_REVIEW.png"
    casts=meta.get("characters") or []
    available_refs={}
    for name,data in refs.items():
        target=art/Path(name).name
        if not target.is_file():
            target.write_bytes(data)
        available_refs[Path(name).stem]=target
    missing_scenes=[i for i,p in enumerate(pictures) if not p.is_file()]
    if not meta.get("image_model_rights_reviewed"):
        raise RuntimeError("Commercial/license review of selected illustration model is required")
    if not missing_scenes and thumb.is_file():
        return pictures,thumb,{"model":cfg["id"],"cache_hits":len(pictures),"generated":0,
                              "ip_adapter_active":bool(available_refs),"reference_reused":bool(available_refs)}
    import torch
    from PIL import Image,ImageOps,ImageDraw,ImageFont
    from diffusers import AutoPipelineForText2Image
    if not torch.cuda.is_available():
        raise RuntimeError("Original 2D manhua art requires a GPU; no abstract placeholder fallback")
    slot, device = selected_gpu()
    model_load_started=time.monotonic()
    pipe=AutoPipelineForText2Image.from_pretrained(cfg["id"],torch_dtype=torch.float16,
                                                   use_safetensors=True)
    print("MANHUA_IMAGE_MODEL_LOAD_SECONDS",round(time.monotonic()-model_load_started,2),flush=True)
    # Avoid CPU↔GPU transfers on sufficiently large GPUs. Fall back to safe
    # CPU offloading on low-memory hardware or the first CUDA allocation OOM;
    # this never substitutes a lower-quality model or changes the scene plan.
    free_bytes, total_bytes = torch.cuda.mem_get_info(slot)
    residency_requested = choose_image_memory_mode(
        free_bytes=free_bytes, total_bytes=total_bytes,
        setting=os.environ.get("MANHUA_IMAGE_MEMORY_MODE", "auto")) == "GPU_RESIDENT"
    gpu_resident = False
    if residency_requested:
        try:
            pipe.to(device)
            gpu_resident=True
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower():
                raise
            torch.cuda.empty_cache()
    if not gpu_resident:
        pipe.enable_model_cpu_offload(gpu_id=slot)
    print("MANHUA_IMAGE_MEMORY_MODE", "GPU_RESIDENT" if gpu_resident else "CPU_OFFLOAD",
          {"free_gib":round(free_bytes/1024**3,2)}, flush=True)
    def generate_image(*args, **kwargs):
        nonlocal gpu_resident
        try:
            return _model_run(*args, **kwargs)
        except RuntimeError as exc:
            if not gpu_resident or "out of memory" not in str(exc).lower():
                raise
            pipe.enable_model_cpu_offload(gpu_id=slot)
            gpu_resident=False
            torch.cuda.empty_cache()
            print("MANHUA_GPU_IMAGE_OOM_SAFE_OFFLOAD_RETRY", flush=True)
            return _model_run(*args, **kwargs)
    # Generate persistent character look sheets before loading IP-Adapter.
    # Newly generated sheets become visual references for the scene panels,
    # not just disconnected portrait files.
    for ci,person in enumerate(casts):
        dest=art/f"character-{person['id']}.png"
        if not dest.is_file() and person["id"] not in available_refs:
            prompt=(f"{STYLES[meta['style']]}; character reference portrait, "
                    f"{person['visual_description']}; clean face and outfit, solo, front three-quarter view, "
                    "upper body, neutral expression, no words, original design")
            generate_image(pipe,cfg,prompt,dest,seed=90000+ci*43,reference=None,size=(1024,1024))
        available_refs[person["id"]]=available_refs.get(person["id"],dest)
    if checkpoint:
        checkpoint("character-references", len(casts), len(casts))
    ip_adapter=False
    if available_refs:
        try:
            pipe.load_ip_adapter("h94/IP-Adapter",subfolder="sdxl_models",
                                 weight_name="ip-adapter_sdxl.bin")
            pipe.set_ip_adapter_scale(0.55)
            # Register the newly loaded image encoder with Accelerate too.
            # Offload was previously installed before load_ip_adapter(), which
            # left CLIP encoder weights on CPU while its input was on CUDA.
            if gpu_resident:
                pipe.to(device)
            else:
                pipe.enable_model_cpu_offload(gpu_id=slot)
            ip_adapter=True
        except (OSError,RuntimeError,ValueError,ImportError) as exc:
            print("REFERENCE_CONDITIONING_UNAVAILABLE", type(exc).__name__, flush=True)
    created=0
    for i in missing_scenes:
        scene_started=time.monotonic()
        ref=None
        # Select reference of the FIRST named character present in the actual
        # narration passage, not a random character from the cast list.
        if ip_adapter:
            for person in casts:
                label=person.get("name",person["id"])
                if re.search(r"\b"+re.escape(label)+r"\b",scenes[i].get("source_text", ""),re.I):
                    ref=Image.open(available_refs[person["id"]]).convert("RGB")
                    break
        # An SDXL UNet with IP-Adapter installed requires image_embeds on
        # EVERY forward pass. Unnamed/environment-only passages deliberately
        # have no character reference: unload the adapter rather than passing
        # None and crashing with encoder_hid_dim_type='ip_image_proj'.
        # This preserves scene truth instead of inserting an unrelated face.
        if ip_adapter and ref is None:
            pipe.unload_ip_adapter()
            ip_adapter=False
            if not gpu_resident:
                pipe.enable_model_cpu_offload(gpu_id=slot)
            print("MANHUA_IP_ADAPTER_UNLOADED_FOR_REFERENCELESS_SCENE",i+1,flush=True)
        try:
            generate_image(pipe,cfg,scenes[i]["prompt"] + (" CRITICAL RETAKE: ensure every narrated on-screen requirement is visibly present; do not show an irrelevant calm pose or duplicated character." if retake_attempt else ""),pictures[i],seed=11000+i*19+retake_attempt*911,
                       reference=ref,size=(1024,576))
        except RuntimeError as exc:
            # A newly attached SDXL IP-Adapter sometimes has its encoder on
            # CPU despite CUDA inputs. Retry only that specific compatibility
            # failure without reference conditioning; do not swallow OOM or
            # unrelated image errors and never substitute placeholder artwork.
            mismatch = ("Input type" in str(exc) and "weight type" in str(exc))
            if not (ref is not None and mismatch):
                raise
            print("IP_ADAPTER_DEVICE_MISMATCH_RETRY_WITH_SOURCE_PROMPT",flush=True)
            pipe.unload_ip_adapter()
            pipe.enable_model_cpu_offload(gpu_id=slot)
            ip_adapter=False
            generate_image(pipe,cfg,scenes[i]["prompt"] + (" CRITICAL RETAKE: ensure every narrated on-screen requirement is visibly present; do not show an irrelevant calm pose or duplicated character." if retake_attempt else ""),pictures[i],seed=11000+i*19+retake_attempt*911,
                       reference=None,size=(1024,576))
        created+=1
        print("MANHUA_ART_PROGRESS",i+1,len(scenes),flush=True)
        print("MANHUA_ART_SCENE_SECONDS",i+1,
              round(time.monotonic()-scene_started,2),flush=True)
        if checkpoint and (created % 5 == 0 or created == len(missing_scenes)):
            checkpoint("illustrations", created, len(missing_scenes))
    if not thumb.is_file():
        hero=casts[0] if casts else None
        hook=str(meta.get("thumbnail_hook") or meta["title"])[:80]
        hero_desc=hero["visual_description"] if hero else "a main protagonist consistent with the story"
        # A thumbnail must show the same protagonist and the already narrated
        # opening action. It must not introduce an invented second protagonist.
        opening = scenes[0].get("visual_requirements", []) if scenes else []
        opening_action = "; ".join(
            r["must_show"] for r in opening
            if r["id"] != "narrated_beat")[:460]
        prompt=(f"{STYLES[meta['style']]}; dramatic premium YouTube manhua thumbnail, "
                "EXACTLY ONE protagonist, ONE person total, no doubles, no collage, "
                f"powerful expressive close-up of this single hero: {hero_desc}. "
                f"Show the episode's real opening event: {opening_action}. "
                "One focal face, strong silhouette, striking lighting, clear contrasting "
                "background with open space for the title; original manhua art, "
                "beautiful expressive features, precise anatomy, no extra people, no words")
        cover=art/"thumbnail-original.png"
        ref=Image.open(available_refs[hero["id"]]).convert("RGB") if hero and ip_adapter else None
        if ip_adapter and ref is None:
            pipe.unload_ip_adapter()
            ip_adapter=False
            if not gpu_resident:
                pipe.enable_model_cpu_offload(gpu_id=slot)
            print("MANHUA_IP_ADAPTER_UNLOADED_FOR_REFERENCELESS_THUMBNAIL",flush=True)
        generate_image(pipe,cfg,prompt + (" RETAKE: ONE and only one protagonist, large readable focal character, no double figures." if retake_attempt else ""),cover,seed=18881+retake_attempt*911,reference=ref,size=(1024,576))
        base=ImageOps.fit(Image.open(cover).convert("RGB"),(1280,720))
        draw=ImageDraw.Draw(base)
        font_file="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        try:
            font=ImageFont.truetype(font_file,size=72)
        except OSError:
            font=ImageFont.load_default(size=72)
        label=hook.strip().upper()
        if len(label)>48: label=label[:47].rsplit(" ",1)[0]+"…"
        # Text is added with the font renderer; models are poor at lettering.
        lines=[]
        while label and len(lines)<3:
            width=min(len(label),19)
            boundary=label.rfind(" ",0,width+1)
            if boundary>8: width=boundary
            lines.append(label[:width].strip());label=label[width:].strip()
        y=720-110*len(lines)-45
        for line in lines:
            draw.text((52,y),line,font=font,fill="white",stroke_width=6,stroke_fill="#0f1625")
            y+=110
        base.save(thumb,optimize=True)
    if checkpoint:
        checkpoint("illustrations-and-thumbnail", len(scenes), len(scenes))
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
    return pictures,thumb,{"model":cfg["id"],"cache_hits":len(pictures)-created,
                           "generated":created,"ip_adapter_active":ip_adapter,
                           "reference_reused":bool(refs),"character_consistency_human_reviewed":False}


def evaluate_visuals(scenes: list[dict], pictures: list[Path], thumbnail: Path,
                     work: Path) -> dict:
    """Private pixel-based image QA, independent of prompt text and FFmpeg.

    CLIP provides *triage*, not proof of visual correctness; no human
    acceptance is inferred. Cached models/assets are reused when available.
    """
    from video.audiobook_studio.manhua_pipeline.visual_quality import (
        vision_review, thumbnail_contract, episode_gate)
    model = processor = None
    if os.environ.get("MANHUA_SKIP_VISION_MODEL") != "1":
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor
            model_id = "openai/clip-vit-base-patch32"
            processor = CLIPProcessor.from_pretrained(model_id)
            model = CLIPModel.from_pretrained(model_id).eval()
            if torch.cuda.is_available():
                _, device = selected_gpu()
                model = model.to(device)
            print("MANHUA_VISUAL_QA_MODEL_READY", model_id, flush=True)
        except (OSError, ImportError, RuntimeError, ValueError) as exc:
            print("MANHUA_VISUAL_QA_UNAVAILABLE", type(exc).__name__, flush=True)
            model = processor = None
    findings = []
    for scene, picture in zip(scenes, pictures):
        result = vision_review(picture, scene.get("visual_requirements", []),
                               model=model, processor=processor)
        result["scene"] = scene["scene"]
        result["source_sha256"] = scene["source_sha256"]
        findings.append(result)
    cover = vision_review(thumbnail, thumbnail_contract(),
                          model=model, processor=processor)
    gate = episode_gate(scene_reviews=findings, thumbnail_review=cover,
                        scenes_expected=len(scenes))
    record = {"schema": "manhua-source-to-pixels-v1",
              "scenes": findings, "thumbnail": cover, "gate": gate,
              "scope": "PRIVATE_REVIEW_ONLY",
              "never_claim_human_visual_approval": True}
    (work / "PRIVATE_VISUAL_QA_REPORT.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False))
    if gate["needs_correction"]:
        print("MANHUA_VISUAL_QA_HOLD",
              gate["failed_or_unverified_items"], flush=True)
    del model, processor
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
    return gate


def discard_unverified_art_from_cache(work: Path, pictures: list[Path],
                                      thumbnail: Path, visual_gate: dict) -> dict:
    """Persist approved reusable art, never reuse known-failed scene pixels.

    A QA hold may still produce private review metadata, but failed images must
    remain missing so the next run regenerates only those specific panels.
    """
    if not visual_gate.get("needs_correction"):
        return {"removed_scenes": [], "removed_thumbnail": False}
    report = json.loads((work / "PRIVATE_VISUAL_QA_REPORT.json").read_text())
    records = report.get("scenes", [])
    if len(records) != len(pictures):
        raise RuntimeError("Cannot prune inconsistent image quality evidence")
    removed=[]
    for index, (record, path) in enumerate(zip(records, pictures)):
        if record.get("status") != "AUTOMATED_TRIAGE_PASS":
            path.unlink(missing_ok=True)
            removed.append(index)
    rejected_thumbnail=report.get("thumbnail", {}).get("status") != "AUTOMATED_TRIAGE_PASS"
    if rejected_thumbnail:
        thumbnail.unlink(missing_ok=True)
    print("MANHUA_UNVERIFIED_IMAGE_CACHE_PRUNED",
          {"scenes":removed,"thumbnail":rejected_thumbnail},flush=True)
    return {"removed_scenes":removed,"removed_thumbnail":rejected_thumbnail}


def scene_timeline(scenes: list[dict], durations: list[float]) -> list[float]:
    if not scenes or not durations:
        raise ValueError("No source linked timeline")
    result=[];end=0
    for i,s in enumerate(scenes):
        start,stop=s["start_chunk"],s["end_chunk"]
        if start != end or not start < stop <= len(durations):
            raise ValueError("Scenes do not span narration without gaps/overlap")
        length=sum(durations[start:stop])
        if length<=0:raise ValueError("Empty narration scene")
        result.append(length);end=stop
    if end!=len(durations):raise ValueError("Last scene does not cover final spoken sentence")
    return result


def render_review(images: list[Path], seconds: list[float], audio: Path, target: Path) -> dict:
    if len(images)!=len(seconds) or not images:
        raise ValueError("Audio-to-panel timeline incomplete")
    # A single FFmpeg encode (not a second GPU generation pass); small steady
    # Ken Burns movement is applied to original 2D pictures only.
    lines=[]
    for path,duration in zip(images,seconds):
        if not path.is_file() or duration<=0 or "'" in str(path):
            raise ValueError("Missing/unsafe illustrated scene")
        lines += ["file '"+str(path.resolve())+"'",f"duration {duration:.6f}"]
    lines += ["file '"+str(images[-1].resolve())+"'"]
    listing=target.parent/"scene_concat.txt"
    listing.write_text("\n".join(lines)+"\n")
    actual=sum(seconds)
    tmp=target.with_suffix(".partial.mp4")
    run(["ffmpeg","-hide_banner","-loglevel","error","-y", "-f","concat","-safe","0","-i",str(listing),
         "-i",str(audio),"-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
         "fps=24,zoompan=z='min(zoom+0.00008,1.09)':d=1:x='iw/2-(iw/zoom/2)':"
         "y='ih/2-(ih/zoom/2)':s=1920x1080:fps=24,format=yuv420p",
         "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","copy", "-t",str(actual),
         "-movflags","+faststart",str(tmp)])
    # A short, owner-requested smoke clip is intentionally under the production
    # validator's 10-second minimum; still require real A/V, codec and Full HD.
    report=validate_review_video(tmp,expected_audio_seconds=actual,
                                 min_duration_seconds=1.0 if actual < 10 else 10.0)
    tmp.replace(target)
    report["sha256"]=sha256(target)
    return report


def process(*, story_id: str, episode: int, phase: str, quality: str="quality") -> dict:
    validate_slug(story_id)
    if phase not in ("preflight","assets","review") or quality not in IMAGE_MODELS:
        raise ValueError("Allowed phases: preflight, assets (generate once), review (legacy preview)")
    source=find_source()
    meta,script,refs=open_package(source,expected_story_id=story_id,episode=episode)
    ep=meta["episodes"][episode-1]
    parts=split_chunks(script)
    scenes=scene_plan(parts,style=meta["style"],characters=meta.get("characters"),
                      briefs=meta.get("scene_briefs",{}).get(str(episode)))
    # Name grounding for conditional image reference reuse: no invented cast.
    for scene in scenes:
        scene["source_text"]=" ".join(p["text"] for p in parts[scene["start_chunk"]:scene["end_chunk"]])
    work=WORK/story_id/f"ep{episode:03}"
    work.mkdir(parents=True,exist_ok=True)
    plan={"story_id":story_id,"episode":episode,"source_sha256":ep["sha256"],
          "voice_profile":VOICE,"style":meta["style"],"scenes":scenes,
          "narration_chunk_count":len(parts),"human_review_required":True}
    (work/"PRIVATE_SCENE_PLAN.json").write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    if phase=="preflight":
        result={"status":"PRIVATE_PREFLIGHT_PASS","story_id":story_id,"episode":episode,
                "chunks":len(parts),"panels":len(scenes),"approved_source_sha256":ep["sha256"],
                "no_gpu_used":True,"art_generated":False,"release_approved":False}
        (WORK/"PRIVATE_PREFLIGHT_REPORT.json").write_text(json.dumps(result,indent=2))
        return result
    if not meta.get("image_model_rights_reviewed"):
        raise RuntimeError("Review image model rights before spending GPU credits on narration or art")
    restore_cache(ep,work)
    started=time.monotonic()
    def phase_checkpoint(stage: str, done: int, count: int) -> None:
        checkpoint_started=time.monotonic()
        checkpoint_out(meta,ep,work)
        print("MANHUA_CHECKPOINT_SECONDS",stage,
              round(time.monotonic()-checkpoint_started,2),flush=True)
        print("MANHUA_PRIVATE_PROGRESS_SAVED",stage,done,count,flush=True)
    wavs,durations=voice_chunks(parts,work,checkpoint=phase_checkpoint)
    audio=master_audio(wavs,durations,work)
    phase_checkpoint("master-narration",len(wavs),len(wavs))
    pictures,thumbnail,art_stats=illustrate(meta,scenes,work,refs,mode=quality,checkpoint=phase_checkpoint)
    visual_gate=evaluate_visuals(scenes,pictures,thumbnail,work)
    # One targeted art-only retry if PIXEL evidence strongly contradicts
    # narration. Reuse all approved Qwen speech and unaffected illustrations.
    if visual_gate["needs_correction"]:
        evidence=json.loads((work/"PRIVATE_VISUAL_QA_REPORT.json").read_text())
        repair=[]
        for index,record in enumerate(evidence["scenes"]):
            if record.get("status")=="REJECT_BAD_IMAGE" or (
                record.get("status")=="NEEDS_SCENE_CORRECTION" and
                any(r.get("positive_probability",1.0)<0.42
                    for r in record.get("requirements",[]))):
                repair.append(index)
        cover_record=evidence["thumbnail"]
        retake_cover=cover_record.get("status")=="REJECT_BAD_IMAGE" or (
            cover_record.get("status")=="NEEDS_SCENE_CORRECTION" and
            any(r.get("positive_probability",1.0)<0.42
                for r in cover_record.get("requirements",[])))
        if repair or retake_cover:
            for index in repair:
                pictures[index].unlink(missing_ok=True)
            if retake_cover:
                thumbnail.unlink(missing_ok=True)
            print("MANHUA_TARGETED_ART_RETAKE",{
                "scenes":repair,"thumbnail":bool(retake_cover),
                "voice_regeneration":False},flush=True)
            pictures,thumbnail,art_stats=illustrate(
                meta,scenes,work,refs,mode=quality,retake_attempt=1,
                checkpoint=phase_checkpoint)
            visual_gate=evaluate_visuals(scenes,pictures,thumbnail,work)
            visual_gate["one_targeted_retake_attempted"]=True
        else:
            visual_gate["one_targeted_retake_attempted"]=False
    lengths=scene_timeline(scenes,durations)
    # This manifest is the bridge from slow GPU ASSET GENERATION to fast
    # CPU-only FFmpeg assembly. Values come from REAL Qwen audio timings.
    timeline=[{"image":"illustrations/"+p.name,
               "seconds":round(lengths[i],6),
               "source_sha256":scenes[i]["source_sha256"],
               "image_sha256":sha256(p)}
              for i,p in enumerate(pictures)]
    (work/"PRIVATE_SCENE_TIMELINE.json").write_text(
        json.dumps(timeline,indent=2))
    if phase=="assets":
        checkpoint=WORK / "MANHUA_PROGRESS.zip"
        result={"schema":SCHEMA,"story_id":story_id,"episode":episode,
                "source_sha256":ep["sha256"],"voice_profile":VOICE,
                "audio_sha256":sha256(audio),"audio":"narration_review.m4a",
                "thumbnail_sha256":sha256(thumbnail),
                "thumbnail":"THUMBNAIL_REVIEW.png",
                "timeline":"PRIVATE_SCENE_TIMELINE.json",
                "visual_qa":"PRIVATE_VISUAL_QA_REPORT.json",
                "visual_quality_gate":visual_gate,
                "checkpoint":checkpoint.name,
                "scenes":len(scenes),"qwen_audio_seconds":round(sum(durations),3),
                "gpu_mp4_rendered":False,
                "ready_for_youtube":False,"publicly_published":False}
        (WORK/"PRIVATE_ASSETS_REPORT.json").write_text(
            json.dumps(result,indent=2))
        discard_unverified_art_from_cache(work,pictures,thumbnail,visual_gate)
        checkpoint_out(meta,ep,work)
        return {"status":("PRIVATE_ASSETS_REQUIRE_CORRECTION"
                          if visual_gate["needs_correction"] else "PRIVATE_ASSETS_READY"),
                "story_id":story_id,"episode":episode,
                "scenes":len(scenes),"audio_cached":True,
                "gpu_video_rendered":False,"human_review_required":True}
    video=WORK/f"{story_id}_ep{episode:03}_MANHUA_REVIEW.mp4"
    media=render_review(pictures,lengths,audio,video)
    checkpoint=checkpoint_out(meta,ep,work)
    report={"schema":SCHEMA,"story_id":story_id,"episode":episode,
            "source_sha256":ep["sha256"],"voice_profile":VOICE,
            "narrator":"Qwen Ryan, owner-approved identity, not full listening approval",
            "art":art_stats,"scenes":len(scenes),"spoken_words":sum(p["words"] for p in parts),
            "duration_s":media["duration_seconds"], "review_video":video.name,
            "review_video_sha256":media["sha256"], "thumbnail":thumbnail.name,
            "thumbnail_sha256":sha256(thumbnail),"checkpoint":checkpoint.name,
            "render_seconds":round(time.monotonic()-started,1),"technical_review":media,
            "visual_quality_gate":visual_gate,
            "visual_qa_report":"PRIVATE_VISUAL_QA_REPORT.json",
            "owner_narration_listening_approved":False,
            "visual_continuity_approved":False,"ready_for_youtube":False,
            "publicly_published":False}
    (WORK/"MANHUA_REVIEW_REPORT.json").write_text(json.dumps(report,indent=2))
    shutil.copy2(thumbnail,WORK/thumbnail.name)
    return {"status":("PRIVATE_REVIEW_NEEDS_VISUAL_CORRECTION" if visual_gate["needs_correction"] else "PRIVATE_REVIEW_GENERATED"), "story_id":story_id,"episode":episode,
            "duration_s":report["duration_s"],"scenes":len(scenes),"voice":"Ryan",
            "art_engine":art_stats["model"],"owner_review_required":True}


def cli() -> None:
    from argparse import ArgumentParser
    p=ArgumentParser(description="Private story-unlimited original manhua audiobook renderer")
    p.add_argument("--story-id",required=True)
    p.add_argument("--episode",required=True,type=int)
    p.add_argument("--phase",choices=("preflight","assets","review"),default="preflight")
    p.add_argument("--quality",choices=IMAGE_MODELS,default="quality")
    args=p.parse_args()
    output=process(story_id=args.story_id,episode=args.episode,phase=args.phase,quality=args.quality)
    print("MANHUA_PIPELINE_RESULT",json.dumps(output),flush=True)


if __name__=="__main__":
    cli()