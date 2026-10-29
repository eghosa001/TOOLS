#!/usr/bin/env python3
"""Private Kaggle production proof: one original 120-frame (5s) Blender ASMR cut.

This is a manually directed, editor-authored Blender scene and fixed Foley
cue sheet, NOT an AI generator or automatic shot-picker. Render timeout is
the user's 180-second preview cap. Produces a technically checkable audiovisual
MP4, **NOT automatic 9/10 aesthetic approval**.
"""
from pathlib import Path
import importlib.util,json,os,subprocess,time

assets_found=list(Path("/kaggle/input").rglob("ASSET_PROVENANCE.json"))
if len(assets_found)!=1:
    raise RuntimeError("Exactly one authorized ASMR private asset dataset required")
assets=assets_found[0].parent
# Source code is bundled from this exact Git commit into the Kaggle kernel,
# never silently loaded from an older cached asset-library dataset.
scripts=Path("/kaggle/working/satisfying_asmr_source_snapshot")
source_names=("official_blender.py","prismatic_gel_scene.py","hand_authored_foley.py")
if not scripts.is_dir():
    raise RuntimeError("No pinned GitHub production source snapshot; refusing stale Kaggle dataset source")
for filename in source_names:
    if not (scripts/filename).is_file():
        raise RuntimeError("Bundled ASMR production source missing: "+filename)
spec=importlib.util.spec_from_file_location("satisfying_blender_lts",scripts/"official_blender.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
# /tmp is NOT persisted by Kaggle; large tool archives will not be exported.
blender=module.install("/tmp/satisfying_studio_blender_lts")
out=Path("/kaggle/working/satisfying_asmr_five_second")
out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update(
    ASMR_ASSETS=str(assets),
    ASMR_OUT=str(out),
    ASMR_MODE="ANIMATION",
    ASMR_DEVICE="GPU",
    ASMR_GPU_BACKEND="OPTIX",
    ASMR_REQUIRE_GPU="1",
    ASMR_DENOISE="1",
    ASMR_W="720",
    ASMR_H="1280",
    ASMR_SAMPLES="20",
)
print("EDITOR_AUTHORED_5S_120_FRAME_BLENDER_RENDER_START",
      "source_snapshot",str(scripts),"output",str(out),flush=True)
t=time.monotonic()
try:
    subprocess.run([str(blender),"-b","-t","4","--python",str(scripts/"prismatic_gel_scene.py")],
                   env=env,check=True,timeout=2100)
except subprocess.TimeoutExpired as exc:
    raise RuntimeError("STOP: 120-frame production exceeds the scoped 35-minute GPU budget") from exc
render_seconds=time.monotonic()-t
frames=sorted((out/"frames").glob("frame_*.png"))
print("RENDER_FRAME_COUNT",len(frames),"RENDER_SECONDS",round(render_seconds,1),flush=True)
if len(frames)!=120:
    raise RuntimeError("STOP: expected exactly 120 Blender-produced frames, got "+str(len(frames)))

print("AUTHOR_SELECTED_CC0_FOLEY_MIX_BEGIN",flush=True)
subprocess.run(["python",str(scripts/"hand_authored_foley.py")],
               check=True,timeout=90,env=env)
audio=out/"original_CC0_foley_5sec.wav"
if not audio.is_file():raise RuntimeError("No actual recorded-Foley master")
video=out/"satisfying_prismatic_five_second_INTERNAL_UNAPPROVED.mp4"
cmd=[
    "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
    "-framerate","24","-start_number","1",
    "-i",str(out/"frames"/"frame_%04d.png"),
    "-i",str(audio),
    "-map","0:v:0","-map","1:a:0",
    "-c:v","libx264","-pix_fmt","yuv420p","-preset","medium","-crf","16",
    "-r","24",
    "-af","highpass=f=55,loudnorm=I=-20:TP=-2:LRA=9:linear=false",
    "-ar","48000","-c:a","aac","-b:a","256k",
    "-t","5","-movflags","+faststart",
    str(video)
]
subprocess.run(cmd,check=True,timeout=120)
r=subprocess.run(["ffprobe","-v","error",
                   "-show_entries","format=duration:stream=codec_type,width,height,nb_frames",
                   "-of","json",str(video)],capture_output=True,text=True,check=True,timeout=20)
metadata=json.loads(r.stdout)
streams=metadata.get("streams",[])
v=next((s for s in streams if s.get("codec_type")=="video"),{})
assert int(v.get("width",0))>=720 and int(v.get("height",0))>=1280
assert int(v.get("nb_frames",0))==120
assert any(s.get("codec_type")=="audio" for s in streams)
assert abs(float(metadata["format"]["duration"])-5.0)<.07
# Check that the audio/video stream itself survived muxing; visual acceptance
# and headphone audition are still separate mandatory creative decisions.
q=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-i",str(video),
                  "-af","ebur128=peak=true","-f","null","-"],
                 capture_output=True,text=True,timeout=35)
(out/"MASTERING_METER.log").write_text(q.stderr[-4000:])
if q.returncode:
    raise RuntimeError("Unable to measure the mastered recorded-Foley soundtrack")
(out/"TECHNICAL_PROOF_NOT_APPROVED.txt").write_text(
    "Genuine 5-second 24fps Blender/Cycles OptiX animation with recorded CC0 Foley.\n"
    "This is an INTERNAL TECHNICAL PROOF. The user explicitly forbids releasing a poor CGI preview.\n"
    "Must be inspected fully against all four references; nine scores >=9/10 required.\n"
    "Until genuinely inspected and approved it is NOT the requested premium deliverable.\n"
)
print("TECHNICAL_5S_AV_PROOF_READY_NOT_QUALITY_APPROVED",video,video.stat().st_size,flush=True)
