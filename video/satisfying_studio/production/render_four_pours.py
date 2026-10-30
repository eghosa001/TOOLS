#!/usr/bin/env python3
"""Reproduce manually-authored Pexels/CC0 Sandfall Short; NEVER automatically quality-approve.

Requires already downloaded legitimate raw assets. No user's video/audio,
generative model, paid stock account, or auto-picked scenes. This is a
specific editor-authored timeline rather than an automatic video assembler.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from licensed_footage_gate import verify

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"releases"/"SAND_FOUR_POURS_30S_SOURCE_LEDGER_2026-10-30.json"

def cmd(*parts, timeout=150):
    subprocess.run(list(parts),check=True,timeout=timeout)

def probe(path):
    x=subprocess.check_output(["ffprobe","-v","error","-count_frames",
         "-show_entries","format=duration:stream=codec_type,width,height,nb_read_frames,sample_rate,channels",
         "-of","json",str(path)],timeout=40)
    d=json.loads(x);v=next(s for s in d["streams"] if s["codec_type"]=="video")
    a=next(s for s in d["streams"] if s["codec_type"]=="audio")
    if int(v["nb_read_frames"])!=720 or a["sample_rate"]!="48000" or abs(float(d["format"]["duration"])-30)>.1:
        raise RuntimeError("Final 30s ASMR video does not decode to expected 720 unique-frame timeline")
    return d

def render(assets:Path,out:Path,manifest:Path):
    assets=assets.resolve();out=out.resolve()
    report=verify(manifest,assets,probe=True,release=False)
    data=json.loads(manifest.read_text(encoding="utf-8"))
    out.mkdir(parents=True,exist_ok=True)
    parts=[]
    for i,shot in enumerate(data["shots"],1):
        f=assets/shot["path"]
        dest=out/f"authored_shot_{i:02d}.mp4"
        vf=("scale=720:1280:force_original_aspect_ratio=decrease:flags=lanczos,"
            "pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=0x10121a,"
            "setsar=1,fps=24,eq=contrast=1.035:saturation=1.045")
        cmd("ffmpeg","-nostdin","-hide_banner","-v","error","-y",
            "-ss",str(shot["start"]),"-i",str(f),"-t",str(shot["duration"]),
            "-an","-vf",vf,"-c:v","libx264","-preset","veryfast",
            "-crf","19","-pix_fmt","yuv420p","-r","24",
            "-frames:v",str(24*shot["duration"]),str(dest))
        parts.append(dest)
    timeline=out/"MANUAL_ORDER_OF_SHOTS.txt"
    timeline.write_text("".join("file '"+p.name+"'\n" for p in parts))
    picture=out/"editor_selected_picture_only.mp4"
    cmd("ffmpeg","-nostdin","-v","error","-y",
        "-f","concat","-safe","0","-i",str(timeline),"-c","copy",str(picture))

    # Pre-auditioned candidate types are actual sand-on-sand recordings, NOT
    # original on-set sound; the picture's source AAC is nominal silence.
    s1=assets/data["sound_sources"][0]["file"]
    s2=assets/data["sound_sources"][1]["file"]
    audio=out/"manually_cued_recorded_sand_48k.wav"
    fg=(
      "[0:a]atrim=start=7:duration=30,asetpts=PTS-STARTPTS,highpass=f=55,"
      "lowpass=f=11500,volume=0.85[bed];"
      "[1:a]atrim=start=0:duration=3.4,asetpts=PTS-STARTPTS,"
      "adelay=400|400,volume=0.23,afade=t=in:st=0:d=0.05,"
      "afade=t=out:st=3.0:d=0.4[a1];"
      "[2:a]atrim=start=4:duration=3,asetpts=PTS-STARTPTS,"
      "adelay=9300|9300,volume=0.23,afade=t=out:st=2.6:d=0.4[a2];"
      "[3:a]atrim=start=8:duration=3,asetpts=PTS-STARTPTS,"
      "adelay=17300|17300,volume=0.2,afade=t=out:st=2.6:d=0.4[a3];"
      "[bed][a1][a2][a3]amix=inputs=4:duration=first:dropout_transition=0,"
      "aresample=48000,loudnorm=I=-20:TP=-2.2:LRA=12,"
      "pan=stereo|c0=c0|c1=c0[a]"
    )
    cmd("ffmpeg","-nostdin","-v","error","-y","-i",str(s1),
        "-i",str(s2),"-i",str(s2),"-i",str(s2),
        "-filter_complex",fg,"-map","[a]","-t","30","-c:a","pcm_s24le",str(audio))
    hd=out/"SAND_FOUR_POURS_ASMR_30S_HD_REVIEW.mp4"
    cmd("ffmpeg","-nostdin","-v","error","-y","-i",str(picture),
        "-i",str(audio),"-map","0:v:0","-map","1:a:0",
        "-c:v","copy","-c:a","aac","-b:a","256k",
        "-ar","48000","-ac","2","-t","30","-movflags","+faststart",str(hd))
    mobile=out/"SAND_FOUR_POURS_ASMR_30S_MOBILE_REVIEW.mp4"
    cmd("ffmpeg","-nostdin","-v","error","-y","-i",str(hd),
        "-vf","scale=360:640:flags=lanczos","-c:v","libx264","-preset","veryfast",
        "-crf","27","-c:a","aac","-b:a","96k","-movflags","+faststart",str(mobile))
    media={}
    for f in (hd,mobile):
        media[f.name]=dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                           probe=probe(f))
        cmd("ffmpeg","-nostdin","-v","error","-i",str(f),"-f","null","-",timeout=100)
    result=dict(stage="ACTUAL_MP4_RENDERED_NOT_ARTISTICALLY_APPROVED",
                footage_source="commercially licensed Pexels stock",
                audio_source="recorded CC0 sand Foley, NOT source-synchronous audio",
                rights_preflight=report, exports=media,
                full_visual_audio_review_completed=False,
                monetization_approved=False,publishable=False)
    (out/"REAL_STOCK_RENDER_QA_UNAPPROVED.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets-dir",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=MANIFEST)
    args=p.parse_args()
    print(json.dumps(render(args.assets_dir,args.out_dir,args.manifest),indent=2))
