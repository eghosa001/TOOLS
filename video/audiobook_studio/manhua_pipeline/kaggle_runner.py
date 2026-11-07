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
from video.audiobook_studio.manhua_pipeline.core import BUNDLE, NEGATIVE, VOICE, digest, open_package, scene_plan, split_chunks, STYLES, validate_slug

WORK = Path(os.environ.get("MANHUA_WORK_DIR", "/kaggle/working/manhua-studio"))
MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "Ryan"
LANGUAGE = "English"
INSTRUCTION = "A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting."
IMAGE_MODELS = {
    "fast": {"id": "stabilityai/sdxl-turbo", "steps": 3, "guidance": 0.0},
    "quality": {"id": "cagliostrolab/animagine-xl-3.1", "steps": 22, "guidance": 6.0},
}


def run(args: list[str], *, output=False) -> str | None:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout if output else None


def find_source() -> Path:
    path = Path(os.environ.get("MANHUA_INPUT_DIR", "/kaggle/input"))
    matches = sorted(path.rglob(BUNDLE)) if path.exists() else []
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one PRIVATE MANHUA_STORY_PACKAGE.zip in Kaggle inputs")
    return matches[0]


def checkpoint_out(meta: dict, ep: dict, source_dir: Path) -> Path:
    # Every asset is bound to the EXACT episode source, never to a title alone.
    from video.audiobook_studio.episode_fastlane import efficient_checkpoint
    dest = WORK / "MANHUA_PROGRESS.zip"
    efficient_checkpoint(source_dir, dest, source_sha256=ep["sha256"], voice_profile=VOICE)
    return dest


def restore_cache(ep: dict, target: Path) -> bool:
    from video.audiobook_studio.episode_fastlane import inspect_checkpoint
    inputs = Path(os.environ.get("MANHUA_INPUT_DIR", "/kaggle/input"))
    matches = list(inputs.rglob("MANHUA_PROGRESS.zip")) if inputs.exists() else []
    if not matches:
        return False
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
    return True


def voice_chunks(parts: list[dict], out: Path) -> tuple[list[Path], list[float]]:
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
        dtype = torch.bfloat16 if torch.cuda.get_device_capability(0)[0] >= 8 else torch.float32
        voice = Qwen3TTSModel.from_pretrained(MODEL, device_map="cuda:0", dtype=dtype,
                                               attn_implementation="sdpa")
        for i in need:
            torch.manual_seed(20261107 + i)
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


def illustrate(meta: dict, scenes: list[dict], roots: Path, refs: dict[str, bytes], *, mode="fast") -> tuple[list[Path], Path, dict]:
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
    pipe=AutoPipelineForText2Image.from_pretrained(cfg["id"],torch_dtype=torch.float16,
                                                   use_safetensors=True)
    pipe.enable_model_cpu_offload()
    # Generate persistent character look sheets before loading IP-Adapter.
    # Newly generated sheets become visual references for the scene panels,
    # not just disconnected portrait files.
    for ci,person in enumerate(casts):
        dest=art/f"character-{person['id']}.png"
        if not dest.is_file() and person["id"] not in available_refs:
            prompt=(f"{STYLES[meta['style']]}; character reference portrait, "
                    f"{person['visual_description']}; clean face and outfit, solo, front three-quarter view, "
                    "upper body, neutral expression, no words, original design")
            _model_run(pipe,cfg,prompt,dest,seed=90000+ci*43,reference=None,size=(1024,1024))
        available_refs[person["id"]]=available_refs.get(person["id"],dest)
    ip_adapter=False
    if available_refs:
        try:
            pipe.load_ip_adapter("h94/IP-Adapter",subfolder="sdxl_models",
                                 weight_name="ip-adapter_sdxl.bin")
            pipe.set_ip_adapter_scale(0.55)
            # Register the newly loaded image encoder with Accelerate too.
            # Offload was previously installed before load_ip_adapter(), which
            # left CLIP encoder weights on CPU while its input was on CUDA.
            pipe.enable_model_cpu_offload()
            ip_adapter=True
        except (OSError,RuntimeError,ValueError,ImportError) as exc:
            print("REFERENCE_CONDITIONING_UNAVAILABLE", type(exc).__name__, flush=True)
    created=0
    for i in missing_scenes:
        ref=None
        # Select reference of the FIRST named character present in the actual
        # narration passage, not a random character from the cast list.
        if ip_adapter:
            for person in casts:
                label=person.get("name",person["id"])
                if re.search(r"\b"+re.escape(label)+r"\b",scenes[i].get("source_text", ""),re.I):
                    ref=Image.open(available_refs[person["id"]]).convert("RGB")
                    break
        try:
            _model_run(pipe,cfg,scenes[i]["prompt"],pictures[i],seed=11000+i*19,
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
            pipe.enable_model_cpu_offload()
            ip_adapter=False
            _model_run(pipe,cfg,scenes[i]["prompt"],pictures[i],seed=11000+i*19,
                       reference=None,size=(1024,576))
        created+=1
        print("MANHUA_ART_PROGRESS",i+1,len(scenes),flush=True)
    if not thumb.is_file():
        hero=casts[0] if casts else None
        hook=str(meta.get("thumbnail_hook") or meta["title"])[:80]
        hero_desc=hero["visual_description"] if hero else "a main protagonist consistent with the story"
        prompt=(f"{STYLES[meta['style']]}; dramatic premium YouTube manhua thumbnail, "
                f"powerful expressive close-up {hero_desc}, eye-catching story conflict, "
                "strong silhouette, striking lighting, background with open space for title, "
                "original character design, high detail, no words")
        cover=art/"thumbnail-original.png"
        ref=Image.open(available_refs[hero["id"]]).convert("RGB") if hero and ip_adapter else None
        _model_run(pipe,cfg,prompt,cover,seed=18881,reference=ref,size=(1024,576))
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
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
    return pictures,thumb,{"model":cfg["id"],"cache_hits":len(pictures)-created,
                           "generated":created,"ip_adapter_active":ip_adapter,
                           "reference_reused":bool(refs),"character_consistency_human_reviewed":False}


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
    report=validate_review_video(tmp,expected_audio_seconds=actual)
    tmp.replace(target)
    report["sha256"]=sha256(target)
    return report


def process(*, story_id: str, episode: int, phase: str, quality: str="fast") -> dict:
    validate_slug(story_id)
    if phase not in ("preflight","review") or quality not in IMAGE_MODELS:
        raise ValueError("Allowed phases: preflight (no GPU), review (private GPU)")
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
    wavs,durations=voice_chunks(parts,work)
    audio=master_audio(wavs,durations,work)
    pictures,thumbnail,art_stats=illustrate(meta,scenes,work,refs,mode=quality)
    lengths=scene_timeline(scenes,durations)
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
            "owner_narration_listening_approved":False,
            "visual_continuity_approved":False,"ready_for_youtube":False,
            "publicly_published":False}
    (WORK/"MANHUA_REVIEW_REPORT.json").write_text(json.dumps(report,indent=2))
    shutil.copy2(thumbnail,WORK/thumbnail.name)
    return {"status":"PRIVATE_REVIEW_GENERATED", "story_id":story_id,"episode":episode,
            "duration_s":report["duration_s"],"scenes":len(scenes),"voice":"Ryan",
            "art_engine":art_stats["model"],"owner_review_required":True}


def cli() -> None:
    from argparse import ArgumentParser
    p=ArgumentParser(description="Private story-unlimited original manhua audiobook renderer")
    p.add_argument("--story-id",required=True)
    p.add_argument("--episode",required=True,type=int)
    p.add_argument("--phase",choices=("preflight","review"),default="preflight")
    p.add_argument("--quality",choices=IMAGE_MODELS,default="fast")
    args=p.parse_args()
    output=process(story_id=args.story_id,episode=args.episode,phase=args.phase,quality=args.quality)
    print("MANHUA_PIPELINE_RESULT",json.dumps(output),flush=True)


if __name__=="__main__":
    cli()