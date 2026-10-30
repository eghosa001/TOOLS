#!/usr/bin/env python3
"""Isolated Kaggle trial: real Kandinsky 6 Lite distilled AI video+audio.
No Blender outputs, fake videos, paid APIs or automatic quality approval.
"""
import hashlib
import base64
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

MODEL = "kandinskylab/Kandinsky-6.0-Lite-distill-5s-Diffusers"
FORMAT_ID = "foam-squeezing"
# This placeholder is filled exclusively by the image-reference packaging step.
# A Kaggle generation without its approved first-frame image MUST fail.
REFERENCE_IMAGE_B64 = "__ASMR_REFERENCE_IMAGE_B64__"
REFERENCE_SHA256 = "4119d6cb8f7ad54b40c9a4a4cc5b2b9f1aac6cdbc215d8fd8ff097cdab902202"
TITLE = "Turquoise Foam Compression ASMR | Slow Satisfying Rebound (5s Pilot)"
PROMPT = (
    "One uninterrupted five-second photorealistic macro ASMR video. "
    "A vivid turquoise open-cell sponge cube rests on polished black glass. "
    "A single transparent flat acrylic press begins hovering visibly above the sponge. "
    "During the first second it lowers gently onto the upper face. "
    "During seconds one to three the press compresses the sponge slowly to half its height, "
    "with coherent porous material deformation and realistic pressure spreading through its surface. "
    "During seconds three to five the press lifts, allowing the same sponge to slowly and elastically "
    "return to its original shape. Only one sponge, one press and one uninterrupted compression-release action. "
    "The sponge retains its exact turquoise colour and pore texture, and the acrylic plate keeps its geometry. "
    "Locked three-quarter macro camera, shallow depth of field, refined teal and magenta rim lighting, "
    "studio reflections, no hands, no cuts, no scene changes, no object morphing, no liquid, no extra objects. "
    "Audible professional close-microphone ASMR: delicate airy foam compression, tiny damp pore clicks, "
    "gentle elastic release exactly matching the contact and rebound, no music, narration or ambience."
)
OUT = Path("/kaggle/working")
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "kandinsky6_foam_status.json"

def status(step, **data):
    LOG.write_text(json.dumps({"step": step, "model": MODEL, "title": TITLE, **data}, indent=2))
    print("KANDINSKY_STATUS", step, json.dumps(data), flush=True)

def run(*args, timeout=300):
    return subprocess.run(list(args), check=True, timeout=timeout)

try:
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("No NVIDIA CUDA GPU supplied by Kaggle.")
    gpu = torch.cuda.get_device_name(0)
    cc = torch.cuda.get_device_capability(0)
    dtype = torch.bfloat16 if cc[0] >= 8 and torch.cuda.is_bf16_supported() else torch.float16
    # T4 is compute capability 7.5, no native BF16. FP16 is an EXPERIMENT, not a proven fix.
    cache = Path("/kaggle/temp/kandinsky6_hf")
    cache.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(cache).free / 1024**3
    mem_gb = __import__("psutil").virtual_memory().total / 1024**3
    status("gpu_preflight", gpu=gpu, cc=cc, dtype=str(dtype), free_cache_gb=round(free_gb, 1), ram_gb=round(mem_gb,1))
    if not REFERENCE_IMAGE_B64 or REFERENCE_IMAGE_B64 == "__ASMR_REFERENCE_IMAGE_B64__":
        raise RuntimeError("Image-to-video reference missing. Refusing text-only fallback.")
    image_bytes = base64.b64decode(REFERENCE_IMAGE_B64, validate=True)
    image_sha = hashlib.sha256(image_bytes).hexdigest()
    if image_sha != REFERENCE_SHA256:
        raise RuntimeError("Reference image SHA256 mismatch; stopping before GPU download.")
    # Kaggle images may ship with an older Pillow build without AVIF decoding.
    # Upgrade before opening the SHA-verified reference; no GPU model is changed.
    run(sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q", "pillow>=11.3.0", timeout=180)
    from PIL import Image
    source_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if source_image.width < 256 or source_image.height < 456 or source_image.height <= source_image.width:
        raise RuntimeError("Expected a credible vertical first frame, at least 256x456.")
    reference_path = OUT / "foam_reference.png"
    source_image.resize((480, 864), Image.Resampling.LANCZOS).save(reference_path)
    status("reference_verified", format_id=FORMAT_ID, reference_sha256=image_sha, source_dimensions=list(source_image.size), image=str(reference_path))
    if free_gb < 29:
        raise RuntimeError("Less than 29 GB scratch disk available for 25 GB Kandinsky checkpoint; refusing partial download.")
    if mem_gb < 25:
        raise RuntimeError("Insufficient host RAM for sequential model offloading; no attempt to use smaller models.")
    os.environ["HF_HOME"] = str(cache)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    status("install_dependencies")
    run(sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-cache-dir", "-q",
        "git+https://github.com/huggingface/diffusers.git", "accelerate>=1.1.0",
        "transformers>=4.57.0", "imageio-ffmpeg>=0.5.1", "safetensors>=0.5.0", "pillow>=11.3.0", timeout=700)
    from diffusers import Kandinsky6TI2VAPipeline
    from diffusers.utils import encode_video
    status("loading_official_model")
    pipe = Kandinsky6TI2VAPipeline.from_pretrained(MODEL, torch_dtype=dtype, low_cpu_mem_usage=True)
    pipe.enable_sequential_cpu_offload()
    pipe.vae.enable_tiling()
    kwargs = {"image": Image.open(reference_path).convert("RGB")}
    status("image_to_video_selected", image=str(reference_path), sha256=image_sha, format_id=FORMAT_ID)
    status("generating", seconds=5, steps=10, guidance=1.0)
    start = time.monotonic()
    with torch.inference_mode():
        result = pipe(prompt=PROMPT, height=864, width=480, num_frames=121,
                      num_inference_steps=10, guidance_scale=1.0,
                      generator=torch.Generator("cpu").manual_seed(20261030), **kwargs)
    elapsed = round(time.monotonic() - start, 2)
    if result.audio is None:
        raise RuntimeError("Kandinsky produced no audio; refusing to label the silent result ASMR.")
    raw = OUT / "foam_original_audio.mp4"
    encode_video(result.frames[0], fps=24, output_path=str(raw),
                 audio=result.audio[0][None], audio_sample_rate=pipe.audio_sample_rate)
    final = OUT / "foam_asmr_pilot_UNAPPROVED.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
        "-map","0:v:0","-map","0:a:0","-c:v","copy","-c:a","aac","-ar","48000",
        "-af","loudnorm=I=-19:TP=-2:LRA=9","-movflags","+faststart",str(final),timeout=150)
    probe = subprocess.check_output(["ffprobe","-v","error","-show_entries",
       "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
       "-of","json",str(final)], text=True)
    meta=json.loads(probe)
    kinds={s["codec_type"] for s in meta.get("streams",[])}
    duration=float(meta["format"]["duration"])
    if not {"video","audio"}.issubset(kinds) or duration<4.8 or duration>5.3:
        raise RuntimeError("Real MP4 invalid or missing audio: "+str(meta))
    digest=hashlib.sha256(final.read_bytes()).hexdigest()
    status("completed_UNAPPROVED", file=str(final), sha256=digest, bytes=final.stat().st_size,
           reference_sha256=image_sha, generation_mode="image_to_audio_video",
           inference_seconds=elapsed, duration=duration, streams=meta["streams"],
           note="Technical output ONLY; no claim of convincing physics, audible quality or 9/10 approval.")
except Exception as exc:
    status("FAILED", error=type(exc).__name__+": "+str(exc), traceback=traceback.format_exc()[-6000:])
    raise
