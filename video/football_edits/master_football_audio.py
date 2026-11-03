#!/usr/bin/env python3
"""Two-pass offline broadcast loudness mastering without touching real-match pictures.

Usage: python video/football_edits/master_football_audio.py path/to/render.mp4
Target: -16 LUFS integrated, <= -1.5dBTP, LRA ~8. Original MP4 replaced only
after export/validation succeeds. We never alter the original match frames.
"""
import json,re,subprocess,sys,os
from pathlib import Path

def main():
    if len(sys.argv)!=2:raise SystemExit("usage: master_football_audio.py existing_video.mp4")
    p=Path(sys.argv[1]).resolve()
    if not p.is_file():raise FileNotFoundError(p)
    first=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(p),"-vn",
        "-af","loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json","-f","null","-"],
        text=True,capture_output=True,timeout=120)
    if first.returncode:raise RuntimeError("FFmpeg loudness measurement failed: "+first.stderr[-1200:])
    blocks=re.findall(r'\{\s*"input_i"[^}]*\}',first.stderr,re.S)
    if not blocks:raise RuntimeError("No measured FFmpeg loudnorm JSON")
    m=json.loads(blocks[-1])
    filter_=("loudnorm=I=-16:TP=-1.5:LRA=8:"
        "measured_I="+m["input_i"]+":measured_TP="+m["input_tp"]+
        ":measured_LRA="+m["input_lra"]+
        ":measured_thresh="+m["input_thresh"]+
        ":offset="+m["target_offset"]+":linear=true:print_format=json")
    temp=p.with_name(p.stem+".mastering.tmp.mp4")
    try:
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(p),
            "-map","0:v:0","-map","0:a:0","-c:v","copy","-af",filter_,
            "-c:a","aac","-b:a","192k","-movflags","+faststart",str(temp)]
        subprocess.run(cmd,check=True,timeout=120)
        if temp.stat().st_size < 100000:raise RuntimeError("Mastered video too small")
        info=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size",
                  "-of","json",str(temp)],text=True)
        if float(json.loads(info)["format"]["duration"])<15:raise RuntimeError("Mastered file truncated")
        os.replace(temp,p)
        print("AUDIO_TWO_PASS_MASTERED",str(p),"target=-16LUFS truepeak=-1.5dB",flush=True)
    finally:
        if temp.exists():temp.unlink()
if __name__=="__main__":main()
