#!/usr/bin/env python3
"""Construct four playable 1080p episodes from exact existing chapter masters,
without approximate seek, scene replacement, extra audio or video re-encoding.
"""
from __future__ import annotations
import json,pathlib,subprocess,shutil
ROOT=pathlib.Path(__file__).resolve().parent
SRC=ROOT/"streaming_inputs"
OUT=ROOT/"streamable_four_parts";OUT.mkdir(exist_ok=True)
expected=5212.561687
groups=[
    (1,4,[SRC/"Titanic_Chapters_01_to_04_1080p_Review_Cut.mp4"]),
    (5,8,[SRC/f"TITANIC_CHAPTER_{i:02d}_DIRECTED_REVIEW.mp4" for i in range(5,9)]),
    (9,12,[SRC/f"TITANIC_CHAPTER_{i:02d}_DIRECTED_REVIEW.mp4" for i in range(9,13)]),
    (13,15,[SRC/f"TITANIC_CHAPTER_{i:02d}_DIRECTED_REVIEW.mp4" for i in range(13,16)])
]
results=[]
for index,(first,last,files) in enumerate(groups,1):
    for x in files:
        if not x.is_file():raise FileNotFoundError("Cannot synthesize video from unspecified source "+str(x))
    dest=OUT/f"Titanic_Ch{first:02d}-{last:02d}_1080p_24fps_REVIEW.mp4"
    if len(files)==1:shutil.copy2(files[0],dest)
    else:
        script=OUT/f"chapter_group_{index:02d}.txt"
        script.write_text("".join("file '"+str(f.resolve())+"'\n" for f in files))
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
          "-i",script,"-c","copy","-movflags","+faststart",dest],check=True)
    data=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",dest]))
    v=next(t for t in data["streams"] if t["codec_type"]=="video")
    a=next(t for t in data["streams"] if t["codec_type"]=="audio")
    assert (v["width"],v["height"])==(1920,1080) and v["codec_name"]=="h264" and v["r_frame_rate"]=="24/1"
    assert a["codec_name"]=="aac" and int(a["sample_rate"])==48000
    duration=float(data["format"]["duration"])
    source_seconds=sum(float(json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-of","json",f]))["format"]["duration"]) for f in files)
    assert abs(duration-source_seconds)<1.1,(index,duration,source_seconds)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",dest,"-f","null","-"],check=True)
    result={"part":index,"chapters":[first,last],"file":dest.name,"seconds":duration,"bytes":dest.stat().st_size,
            "source_pictures_unchanged":True,"complete_decode":"PASS","publication_approved":False}
    results.append(result)
    print("CHAPTER_ALIGNED_STREAMABLE_1080P_PART_DECODED",json.dumps(result),flush=True)
total=sum(t["seconds"] for t in results)
assert abs(total-expected)<5,(total,expected)
(OUT/"FOUR_SECTIONS_QA.json").write_text(json.dumps({"parts":results,"four_parts_seconds":total,
    "complete_original_15_chapter_film":"Retained unmodified in source full master artifact",
    "all_parts_decoded":True,"source_chapter_boundaries_exact":True,"youtube_published":False,
    "continuous_subjective_audiovisual_review":False,"editorial_release_approved":False},indent=2))
