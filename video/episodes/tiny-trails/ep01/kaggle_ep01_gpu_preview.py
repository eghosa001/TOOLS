#!/usr/bin/env python3
"""Kaggle-only original-rig 72-frame CUDA preview. NO full-story mode.

This file is uploaded to a private Kaggle kernel from an explicitly gated
GitHub Actions workflow. Never contains the Kaggle token or reads it.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

INPUT=Path("/kaggle/input")
WORK=Path("/kaggle/working")
BLENDER_RELEASE="blender-3.6.23-linux-x64.tar.xz"
BLENDER_URL="https://download.blender.org/release/Blender3.6/"
OUTPUT=WORK/"tiny-trails-ep01-preview-3s.mp4"
PROGRESS=WORK/"tiny-trails-ep01-frame-timings.jsonl"

def command(args,timeout=2400,env=None):
    print("EP01_GPU_COMMAND",args[0],flush=True)
    return subprocess.run(args,check=True,timeout=timeout,env=env)

def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as reader:
        for b in iter(lambda:reader.read(1048576),b""):
            digest.update(b)
    return digest.hexdigest()

def load_bundle():
    packs=list(INPUT.glob("*/episode-pack.tar.gz"))
    if len(packs)!=1:
        raise RuntimeError("EP01_EXPECTS_EXACTLY_ONE_PRIVATE_INPUT_DATASET "+str(len(packs)))
    archive=packs[0]
    digest=archive.parent/"episode-pack.sha256"
    if not digest.is_file():
        raise RuntimeError("EP01_MISSING_PINNED_PRIVATE_DATASET_CHECKSUM")
    expected=digest.read_text(encoding="ascii").split()[0]
    if sha256(archive)!=expected:
        raise RuntimeError("EP01_PRIVATE_ASSET_DATASET_CHECKSUM_MISMATCH")
    root=WORK/"ep01_source"
    root.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive,"r:gz") as tar:
        for m in tar.getmembers():
            p=Path(m.name)
            if p.is_absolute() or ".." in p.parts or not (m.isfile() or m.isdir()) or m.issym() or m.islnk():
                raise RuntimeError("EP01_UNSAFE_SOURCE_ARCHIVE_ENTRY")
        tar.extractall(root)
    ep=root/"video/episodes/tiny-trails/ep01"
    sys.path.insert(0,str(ep))
    import episode_preflight as gate
    gate.check_legacy()
    story=gate.read(ep/"story.json")
    assets=gate.read(root/"assets/assets-verified.json")
    lines=gate.validate(story,assets)
    gate.check_audio(lines,assets,root/"voices")
    gate.check_assets(assets,root/"assets")
    cues=WORK/"episode-cues"
    gate.write_cues(cues,story,lines,True)
    print("EP01_PRIVATE_REAL_ASSET_WAV_AND_LEGACY_CHECKS_PASS",len(lines),flush=True)
    return ep,root,cues

def verified_blender():
    folder=WORK/"blender-install"
    exe=folder/"blender-3.6.23-linux-x64/blender"
    if exe.is_file():
        return exe
    folder.mkdir(parents=True,exist_ok=True)
    for name in (BLENDER_RELEASE,"blender-3.6.23.sha256"):
        url=BLENDER_URL+name
        target=folder/name
        if not target.is_file():
            urllib.request.urlretrieve(url,target)
    checksums=(folder/"blender-3.6.23.sha256").read_text(encoding="utf-8")
    expected=None
    for line in checksums.splitlines():
        if line.strip().endswith(BLENDER_RELEASE):
            expected=line.split()[0]
            break
    if not expected or sha256(folder/BLENDER_RELEASE)!=expected:
        raise RuntimeError("EP01_OFFICIAL_BLENDER_BINARY_CHECKSUM_MISMATCH")
    command(["tar","-xJf",str(folder/BLENDER_RELEASE),"-C",str(folder)],timeout=300)
    if not exe.is_file():
        raise RuntimeError("EP01_VERIFIED_BLENDER_EXECUTABLE_MISSING")
    command([str(exe),"-b","--factory-startup","--disable-autoexec","--version"],timeout=30)
    return exe

def ensure_real_cuda_device():
    gpu=subprocess.run(["nvidia-smi","-L"],text=True,capture_output=True,timeout=30)
    if gpu.returncode!=0 or "GPU " not in gpu.stdout:
        raise RuntimeError("EP01_KAGGLE_HAS_NO_VISIBLE_NVIDIA_GPU_STOP_NOT_CPU_RENDER")
    print("EP01_KAGGLE_NVIDIA_GPU_VISIBLE",gpu.stdout.strip(),flush=True)

def verify_mp4():
    if not OUTPUT.is_file() or OUTPUT.stat().st_size<10000:
        raise RuntimeError("EP01_KAGGLE_ACTUAL_VIDEO_MISSING")
    data=json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(OUTPUT)],text=True,timeout=60))
    v=[s for s in data["streams"] if s["codec_type"]=="video"]
    a=[s for s in data["streams"] if s["codec_type"]=="audio"]
    if len(v)!=1 or v[0]["codec_name"]!="h264" or (v[0]["width"],v[0]["height"])!=(1280,720):
        raise RuntimeError("EP01_KAGGLE_H264_720P_VIDEO_INVALID")
    if not any(s["codec_name"]=="aac" for s in a):
        raise RuntimeError("EP01_KAGGLE_SPOKEN_AUDIO_AAC_MISSING")
    duration=float(data["format"]["duration"])
    if not 2.8<=duration<=3.3:
        raise RuntimeError("EP01_PREVIEW_DURATION_MUST_BE_THREE_SECONDS")
    frames=[json.loads(line)["frame"] for line in PROGRESS.read_text().splitlines() if line.strip()]
    if sorted(frames)!=list(range(1,73)):
        raise RuntimeError("EP01_MISSING_FRAME_LOG_RECORDS "+str(len(frames)))
    command(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],timeout=180)
    report={"actual_mp4":OUTPUT.name,"seconds":duration,"frames":72,
            "resolution":[1280,720],"real_cuda_cycles_required":True,
            "frame_log":PROGRESS.name,"full_rendered":False,
            "visual_approval":False}
    (WORK/"tiny-trails-ep01-gpu-preview-verification.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    shutil.copyfile(WORK/"episode-cues/subtitles.srt",WORK/"tiny-trails-ep01-subtitles.srt")
    print("EP01_KAGGLE_REAL_THREE_SECOND_MP4_VERIFIED_NEEDS_HUMAN_REVIEW",json.dumps(report),flush=True)

def main():
    ensure_real_cuda_device()
    ep,root,cues=load_bundle()
    blender=verified_blender()
    env=os.environ.copy()
    env["CARTOONSTUDIO_EXPLICIT_EP01_PREVIEW"]="YES"
    args=[str(blender),"-b","-t","4","--disable-autoexec","--python-exit-code","1",
          "--python",str(ep/"render_ep01_native.py"),"--",
          "--asset-dir",str(root/"assets"),
          "--assets",str(root/"assets/assets-verified.json"),
          "--audio-dir",str(root/"voices"),
          "--output",str(OUTPUT),
          "--mode","preview","--authorize-preview","--render-device","cuda_cycles",
          "--progress-jsonl",str(PROGRESS)]
    command(args,timeout=2400,env=env)
    verify_mp4()

if __name__=="__main__":
    main()
