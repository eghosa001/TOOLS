#!/usr/bin/env python3
"""Split the completed fixed Titanic master at exact chapter boundaries.
No image choice or re-encoding. Four independently playable 1080p MP4 parts
allow low-data cloud streaming rather than a large mobile download.
"""
from __future__ import annotations
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent
src=ROOT/"master_review_export"/"TITANIC_COMPLETE_15_CHAPTERS_1080P_24FPS_EDITORIAL_REVIEW.mp4"
timing=json.loads((ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json").read_text())
out=ROOT/"streamable_four_parts"
out.mkdir(exist_ok=True)
edges=[0,timing["chapters"]["5"]["start_seconds"],
       timing["chapters"]["9"]["start_seconds"],
       timing["chapters"]["13"]["start_seconds"],timing["runtime_seconds"]]
result=[]
for j,(start,stop) in enumerate(zip(edges,edges[1:]),1):
    dest=out/(f"Titanic_{['Ch01-04','Ch05-08','Ch09-12','Ch13-15'][j-1]}_1080p_24fps_REVIEW.mp4")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",f"{start:.3f}",
        "-t",f"{stop-start:.3f}","-i",str(src),"-map","0:v:0","-map","0:a:0",
        "-c","copy","-avoid_negative_ts","make_zero","-movflags","+faststart",str(dest)],check=True)
    ff=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(dest)]))
    video=next(s for s in ff["streams"] if s["codec_type"]=="video")
    audio=next(s for s in ff["streams"] if s["codec_type"]=="audio")
    assert video["codec_name"]=="h264" and (video["width"],video["height"])==(1920,1080)
    assert audio["codec_name"]=="aac"
    duration=float(ff["format"]["duration"])
    assert abs(duration-(stop-start))<2.0,(j,duration,stop-start)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",str(dest),"-f","null","-"],check=True)
    data={"part":j,"file":dest.name,"actual_seconds":duration,"bytes":dest.stat().st_size,
          "whole_video_preserved":"Four parts are only a delivery alternative; complete main MP4 is retained.",
          "picture_reencoded":False,"repaired_or_editor_approved":False}
    result.append(data)
    print("STREAMABLE_1080P_PART_DECODED",json.dumps(data),flush=True)
(out/"FOUR_SECTIONS_QA.json").write_text(json.dumps({"parts":result,"original_15_chapter_master":src.name,
   "all_parts_decoded":True,"youtube_published":False,"editorial_release_approved":False},indent=2))
assert sum(p["bytes"] for p in result)>20_000_000
