#!/usr/bin/env python3
"""Kaggle-only original-rig 72-frame fast 480p CUDA preview. NO full-story mode.

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
# Faster samples/bounces; still real 1280x720 and all 72 animated frames.
FAST_PROFILE="fast"
PINNED_RENDERER_COMMIT="d01b46a300799e2b2308f454177b284db607c305"
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
    """Accept checked original tarball or Kaggle's transparently unpacked dataset."""
    packs=[p for p in INPUT.rglob("episode-pack.tar.gz") if p.is_file()]
    unpacked=[p.parent.parent for p in INPUT.rglob("assets-verified.json")
              if p.parent.name=="assets" and (p.parent.parent/"video/episodes/tiny-trails/ep01/story.json").is_file()]
    if len(packs)==1:
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
        print("EP01_VERIFIED_ARCHIVE_SHA256",expected,flush=True)
    elif len(packs)==0 and len(unpacked)==1:
        root=unpacked[0]
        print("EP01_KAGGLE_UNPACKED_PRIVATE_SOURCE",root,flush=True)
    else:
        inventory=[str(p.relative_to(INPUT)) for p in INPUT.rglob("*") if p.is_file()]
        raise RuntimeError("EP01_PRIVATE_INPUT_LAYOUT_MISMATCH archives="+str(len(packs))+
                           " extracted_roots="+str(len(unpacked))+" files="+repr(inventory[:35]))
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

def upgrade_only_renderer_code(ep):
    """Re-use original verified actor/WAV dataset; update only executable renderer code.

    Git object SHA pins source content. This never changes the story, audio or 3D assets.
    """
    url=("https://raw.githubusercontent.com/eghosa001/TOOLS/"+
         PINNED_RENDERER_COMMIT+"/video/episodes/tiny-trails/ep01/render_ep01_fast480.py")
    with urllib.request.urlopen(url,timeout=35) as response:
        script=response.read()
    if len(script)<15000 or b'EP01_VERIFIED_CYCLES_CUDA_GPU' not in script:
        raise RuntimeError("EP01_FAST_RENDERER_SOURCE_UNEXPECTED")
    if not (ep/"render_ep01_native.py").is_file():
        raise RuntimeError("EP01_ORIGINAL_RENDERER_NOT_IN_PINNED_PACK")
    target=ep/"render_ep01_fast480.py"
    target.write_bytes(script)
    print("EP01_FAST_RENDERER_PINNED_GIT_COMMIT",PINNED_RENDERER_COMMIT,flush=True)


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
    if len(v)!=1 or v[0]["codec_name"]!="h264" or (v[0]["width"],v[0]["height"])!=(854,480):
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
    frame_seconds=[json.loads(line)["render_seconds"]
                   for line in PROGRESS.read_text().splitlines() if line.strip()]
    typical=sorted(frame_seconds)[len(frame_seconds)//2]
    print("EP01_FAST_PROFILE_REAL_FRAME_MEDIAN_SECONDS",round(typical,3),
          "PROJECTED_20_MINUTES_RENDER_ONLY_HOURS_ONE_WORKER",
          round(28800*typical/3600,2),"EXTRAPOLATION_ONLY",flush=True)
    report={"actual_mp4":OUTPUT.name,"seconds":duration,"frames":72,
            "render_profile":FAST_PROFILE,
            "resolution":[854,480],"real_cuda_cycles_required":True,
            "frame_log":PROGRESS.name,"full_rendered":False,
            "visual_approval":False}
    (WORK/"tiny-trails-ep01-gpu-preview-verification.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    shutil.copyfile(WORK/"episode-cues/subtitles.srt",WORK/"tiny-trails-ep01-subtitles.srt")
    print("EP01_KAGGLE_REAL_THREE_SECOND_MP4_VERIFIED_NEEDS_HUMAN_REVIEW",json.dumps(report),flush=True)

def main():
    ensure_real_cuda_device()
    ep,root,cues=load_bundle()
    upgrade_only_renderer_code(ep)
    blender=verified_blender()
    env=os.environ.copy()
    env["CARTOONSTUDIO_EXPLICIT_EP01_PREVIEW"]="YES"
    args=[str(blender),"-b","-t","4","--disable-autoexec","--python-exit-code","1",
          "--python",str(ep/"render_ep01_fast480.py"),"--",
          "--asset-dir",str(root/"assets"),
          "--assets",str(root/"assets/assets-verified.json"),
          "--audio-dir",str(root/"voices"),
          "--output",str(OUTPUT),
          "--mode","preview","--authorize-preview","--render-device","cuda_cycles",
          "--preview-profile",FAST_PROFILE,
          "--progress-jsonl",str(PROGRESS)]
    command(args,timeout=1200,env=env)
    verify_mp4()

if __name__=="__main__":
    main()
