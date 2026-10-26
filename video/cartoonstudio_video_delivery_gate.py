#!/usr/bin/env python3
"""Hard delivery-quality gate for CartoonStudio preview/full MP4 artifacts.

Checks real decoded video/audio streams, exact target format, duration,
non-silent spoken audio and no decode failure. Never renders an episode.
A successful technical test is NOT a substitute for human visual approval.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def ffprobe(path: Path):
    completed = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                                "-of", "json", str(path)], capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise ValueError("MP4_FFPROBE_FAILED: " + completed.stderr[-500:])
    return json.loads(completed.stdout)


def verify(path: Path, mode: str, *, check_decode: bool=True):
    errors=[]
    path=Path(path)
    if not path.is_file():
        return {"passed":False,"errors":["MISSING_ACTUAL_MP4"],"file":str(path)}
    if path.suffix.lower()!=".mp4" or path.stat().st_size<50_000:
        errors.append("NOT_A_USABLE_MP4")
    metadata=ffprobe(path)
    streams=metadata.get("streams",[])
    videos=[s for s in streams if s.get("codec_type")=="video"]
    audios=[s for s in streams if s.get("codec_type")=="audio"]
    if len(videos)!=1:errors.append("REQUIRE_EXACTLY_ONE_VIDEO_STREAM")
    if not audios:errors.append("AUDIO_STREAM_MISSING")
    length=float(metadata.get("format",{}).get("duration",0))
    if mode=="preview" and not (2.8<=length<=3.3):
        errors.append("PREVIEW_NOT_THREE_SECONDS")
    if mode=="full" and length<=3.3:
        errors.append("FULL_MOVIE_TOO_SHORT")
    codec=None
    frame_rate=None
    if len(videos)==1:
        v=videos[0]
        codec=v.get("codec_name")
        if codec!="h264":errors.append("VIDEO_CODEC_MUST_BE_H264")
        if (v.get("width"),v.get("height"))!=(1280,720):
            errors.append("WRONG_1280X720_RESOLUTION")
        try:frame_rate=Fraction(v.get("avg_frame_rate","0/1"))
        except (ZeroDivisionError,ValueError):frame_rate=Fraction(0)
        if frame_rate!=24:errors.append("WRONG_24FPS_RATE")
        if v.get("pix_fmt")!="yuv420p":errors.append("PIXEL_FORMAT_NOT_YUV420P")
    if audios:
        if audios[0].get("codec_name") not in ("aac","opus"):
            errors.append("UNEXPECTED_AUDIO_CODEC")
        audur=float(audios[0].get("duration",length))
        if abs(audur-length)>0.25:errors.append("AUDIO_VIDEO_DURATION_DRIFT")
    if check_decode and videos:
        dec=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror",
                            "-i",str(path),"-map","0:v:0","-f","null","-"],
                           capture_output=True,text=True,timeout=120)
        if dec.returncode:errors.append("ACTUAL_VIDEO_FRAMES_DID_NOT_DECODE")
    # Detect total silence, but allow introductory pauses. Works without changing the original audio.
    if audios and 0<length<3600:
        proc=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-i",str(path),
                            "-map","0:a:0","-af","volumedetect","-vn","-f","null","-"],
                            capture_output=True,text=True,timeout=120)
        if proc.returncode:errors.append("AUDIO_DECODE_FAILED")
        else:
            found=re.findall(r"mean_volume:\s*(-?(?:\d+\.\d+|\d+|inf)) dB",proc.stderr)
            if found and (found[-1]=="-inf" or float(found[-1])< -55):
                errors.append("AUDIO_IS_SILENT_OR_INAUDIBLE")
    return {"passed":not errors,"errors":errors,"file":str(path),
            "duration_seconds":round(length,3),"frame_rate":str(frame_rate),
            "video_codec":codec,"audio_present":bool(audios),
            "resolution":([videos[0].get("width"),videos[0].get("height")] if videos else None),
            "quality_review_by_person_completed":False,
            "episode_authorized_for_full_render":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mp4",type=Path,required=True)
    p.add_argument("--mode",choices=("preview","full"),required=True)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    try:report=verify(a.mp4,a.mode)
    except (ValueError,subprocess.TimeoutExpired,KeyError,TypeError) as exc:
        report={"passed":False,"errors":[str(exc)],"file":str(a.mp4)}
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("CARTOONSTUDIO_MP4_DELIVERY_"+("PASS" if report["passed"] else "BLOCKED"))
    for error in report["errors"]:print("BLOCKER",error)
    if not report["passed"]:raise SystemExit(2)


if __name__=="__main__":
    main()
