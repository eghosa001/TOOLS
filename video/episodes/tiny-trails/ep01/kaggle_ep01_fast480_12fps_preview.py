#!/usr/bin/env python3
"""12-fps unique CUDA frames duplicated to 24-fps 3-second 480p MP4. NO full-story mode.

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
TEMP=Path("/tmp/cartoonstudio-ep01")  # bulky temporary files never become Kaggle output
BLENDER_RELEASE="blender-3.6.23-linux-x64.tar.xz"
BLENDER_URL="https://download.blender.org/release/Blender3.6/"
OUTPUT=WORK/"tiny-trails-ep01-preview-3s.mp4"
# Faster samples/bounces; still real 1280x720 and all 72 animated frames.
FAST_PROFILE="fast"
PINNED_RENDERER_COMMIT="05f69951b90d96ff3724a7ab0af75935429e13c7"
PROGRESS=WORK/"tiny-trails-ep01-frame-timings.jsonl"
FRAMES=TEMP/"twos-png-frames"

def command(args,timeout=2400,env=None):
    print("EP01_GPU_COMMAND",args[0],flush=True)
    return subprocess.run(args,check=True,timeout=timeout,env=env)

def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as reader:
        for b in iter(lambda:reader.read(1048576),b""):
            digest.update(b)
    return digest.hexdigest()

def prepare_writable_source(source, target):
    """Copy verified input files into an isolated writable workspace, never in place."""
    source=Path(source).resolve()
    target=Path(target).resolve()
    if not source.is_dir() or source==target or source in target.parents:
        raise RuntimeError("EP01_UNSAFE_OR_ABSENT_ORIGINAL_SOURCE")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source,target,symlinks=False)
    if not (target/"video/episodes/tiny-trails/ep01/story.json").is_file():
        raise RuntimeError("EP01_WRITABLE_SOURCE_COPY_INCOMPLETE")
    return target


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
        root=TEMP/"ep01_source"
        root.mkdir(parents=True,exist_ok=True)
        with tarfile.open(archive,"r:gz") as tar:
            for m in tar.getmembers():
                p=Path(m.name)
                if p.is_absolute() or ".." in p.parts or not (m.isfile() or m.isdir()) or m.issym() or m.islnk():
                    raise RuntimeError("EP01_UNSAFE_SOURCE_ARCHIVE_ENTRY")
            tar.extractall(root)
        print("EP01_VERIFIED_ARCHIVE_SHA256",expected,flush=True)
    elif len(packs)==0 and len(unpacked)==1:
        # Kaggle inputs are read-only, never attempt to write renderer code into them.
        source=unpacked[0]
        root=prepare_writable_source(source,TEMP/"ep01_source")
        print("EP01_PRIVATE_SOURCE_COPIED_TO_WRITABLE_WORKDIR",
              source,"=>",root,flush=True)
    else:
        inventory=[str(p.relative_to(INPUT)) for p in INPUT.rglob("*") if p.is_file()]
        raise RuntimeError("EP01_PRIVATE_INPUT_LAYOUT_MISMATCH archives="+str(len(packs))+
                           " extracted_roots="+str(len(unpacked))+" files="+repr(inventory[:35]))
    if not root.resolve().is_relative_to(TEMP.resolve()):
        raise RuntimeError("EP01_ASSETS_MUST_RESIDE_IN_TEMP_WORKSPACE")
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
         PINNED_RENDERER_COMMIT+"/video/episodes/tiny-trails/ep01/render_ep01_fast480_on_twos.py")
    with urllib.request.urlopen(url,timeout=35) as response:
        script=response.read()
    if len(script)<15000 or b'EP01_VERIFIED_CYCLES_CUDA_GPU' not in script:
        raise RuntimeError("EP01_FAST_RENDERER_SOURCE_UNEXPECTED")
    if not (ep/"render_ep01_native.py").is_file():
        raise RuntimeError("EP01_ORIGINAL_RENDERER_NOT_IN_PINNED_PACK")
    target=ep/"render_ep01_fast480_on_twos.py"
    if not target.parent.is_dir() or not os.access(target.parent,os.W_OK):
        raise RuntimeError("EP01_TARGET_NOT_WRITABLE_WORKSPACE "+str(target.parent))
    target.write_bytes(script)
    print("EP01_FAST_RENDERER_PINNED_GIT_COMMIT",PINNED_RENDERER_COMMIT,flush=True)


def verified_blender():
    folder=TEMP/"blender-install"
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
        ["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(OUTPUT)],text=True,timeout=60))
    v=[s for s in data["streams"] if s["codec_type"]=="video"]
    a=[s for s in data["streams"] if s["codec_type"]=="audio"]
    if len(v)!=1 or v[0]["codec_name"]!="h264" or (v[0]["width"],v[0]["height"])!=(854,480):
        raise RuntimeError("EP01_KAGGLE_H264_480P_VIDEO_INVALID")
    if v[0].get("nb_read_frames")!="72":
        raise RuntimeError("EP01_MP4_MUST_CONTAIN_EXACTLY_72_DECODED_FRAMES")
    if not (abs(float(v[0].get("avg_frame_rate","0/1").split("/")[0]) /
                max(1.0,float(v[0].get("avg_frame_rate","0/1").split("/")[-1]))-24)<0.01):
        raise RuntimeError("EP01_MP4_MUST_BE_24_FPS")
    if not any(s["codec_name"]=="aac" for s in a):
        raise RuntimeError("EP01_KAGGLE_SPOKEN_AUDIO_AAC_MISSING")
    duration=float(data["format"]["duration"])
    if not 2.8<=duration<=3.3:
        raise RuntimeError("EP01_PREVIEW_DURATION_MUST_BE_THREE_SECONDS")
    frames=[json.loads(line)["frame"] for line in PROGRESS.read_text().splitlines() if line.strip()]
    if sorted(frames)!=list(range(1,73,2)):
        raise RuntimeError("EP01_TWOS_MISSING_36_GPU_FRAME_LOG_RECORDS "+str(len(frames)))
    command(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],timeout=180)
    frame_seconds=[json.loads(line)["render_seconds"]
                   for line in PROGRESS.read_text().splitlines() if line.strip()]
    typical=sorted(frame_seconds)[len(frame_seconds)//2]
    print("EP01_FAST_PROFILE_REAL_FRAME_MEDIAN_SECONDS",round(typical,3),
          "PROJECTED_20_MINUTES_RENDER_ONLY_HOURS_ONE_WORKER",
          round(28800*typical/3600,2),"EXTRAPOLATION_ONLY",flush=True)
    report={"actual_mp4":OUTPUT.name,"seconds":duration,"frames":72,
            "distinct_rendered_gpu_frames":36,"duplicated_output_frames":36,
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
          "--python",str(ep/"render_ep01_fast480_on_twos.py"),"--",
          "--asset-dir",str(root/"assets"),
          "--assets",str(root/"assets/assets-verified.json"),
          "--audio-dir",str(root/"voices"),
          "--output",str(OUTPUT),
          "--mode","preview","--authorize-preview","--render-device","cuda_cycles",
          "--preview-profile",FAST_PROFILE,
          "--progress-jsonl",str(PROGRESS),"--frames-dir",str(FRAMES)]
    command(args,timeout=1200,env=env)
    # Do not shift either dialogue or timeline: original voice starts at 1s.
    story=json.loads((ep/"story.json").read_text(encoding="utf-8"))
    line=story["dialogue"][0]
    if line["id"]!=1 or line["start"]!=1 or line["end"]>3:
        raise RuntimeError("EP01_TWOS_SPOKEN_TIMELINE_CHANGED")
    voice=root/"voices"/"line_001.wav"
    if not voice.is_file():raise RuntimeError("EP01_TWOS_WAV_MISSING")
    command(["ffmpeg","-y","-v","error","-framerate","12",
             "-pattern_type","glob","-i",str(FRAMES/"frame_*.png"),
             "-i",str(voice),
             "-filter_complex","[1:a]adelay=1000:all=1,apad=whole_dur=3[a]",
             "-map","0:v","-map","[a]","-r","24","-frames:v","72",
             "-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","128k","-t","3","-movflags","+faststart",
             str(OUTPUT)],timeout=180,env=env)
    verify_mp4()

if __name__=="__main__":
    main()
