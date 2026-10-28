#!/usr/bin/env python3
"""Great Pyramid: assemble 15 MANUALLY directed chapters; fail closed on missing files.

Mechanical muxing, technical validation, credits, chapters, captions only.
The picture editorial approvals occur in the per-chapter shot maps.
Never claim a human continuous audiovisual review or upload this file automatically.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

LABELS=[
"The Space Nobody Has Entered",
"Khufu and a Monument Built for Eternity",
"Before Giza: Djoser and Sneferu",
"Stone, Quarries and the Logistics of a Pyramid",
"Merer's Diary: A Voice From the Building Site",
"The Lost River That Changed the Map of Egypt",
"The Workers' Lost City",
"Ramps, Ropes, Sledges and the Engineering Debate",
"Inside Khufu's Stone Labyrinth",
"The Big Void: Seeing Through Stone With Cosmic Rays",
"The North-Face Corridor and the Robots",
"Khufu's Buried Boats",
"The Great Sphinx and Questions of Age",
"Claims, Evidence and Scientific Retractions",
"What Remains: The Real Secrets of Giza",
]
def invoke(args, stdout=None):
    p=subprocess.run([str(x) for x in args],capture_output=stdout is None,text=True,
                     stdout=stdout if stdout is not None else subprocess.PIPE)
    if p.returncode:
        raise RuntimeError("FFmpeg failed: "+str(args[:5])+"\n"+(p.stderr or "")[-4000:])
    return p.stdout if stdout is None else None
def probe(file):
    return json.loads(invoke(["ffprobe","-v","error","-show_streams","-show_format",
                             "-of","json",file]))
def duration(path):
    return float(probe(path)["format"]["duration"])
def hash_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def parse_time(t):
    h,m,s=t.replace(",",".").split(":")
    return int(h)*3600+int(m)*60+float(s)
def fmt(t):
    if t<0: t=0.
    a=int(t);ms=round((t-a)*1000)
    if ms==1000:a+=1;ms=0
    return f"{a//3600:02}:{a//60%60:02}:{a%60:02},{ms:03d}"
def merge_srt(srt,offset,number_start):
    entries=re.split(r"\r?\n\r?\n",srt.strip())
    out=[];number=number_start
    for b in entries:
        match=re.search(r"(\d\d:\d\d:\d\d[,.]\d{3})\s*-->\s*(\d\d:\d\d:\d\d[,.]\d{3})",b)
        if not match: continue
        lines=b[match.end():].strip()
        if not lines:continue
        a=parse_time(match.group(1))+offset
        z=parse_time(match.group(2))+offset
        if z<=a:raise ValueError("Invalid SRT cue")
        out.append(f"{number}\n{fmt(a)} --> {fmt(z)}\n{lines}\n")
        number+=1
    assert len(out)>=5,("Insufficient subtitles",offset)
    return out,number

def preflight(root):
    tracks=[];meta=[];credits=[];all_srt=[];seq=1;start=0.;any_prelim=[]
    for i in range(1,16):
        dirname=root/f"{i:02}"
        mp=dirname/f"Great_Pyramid_Chapter{i:02}_MANUALLY_DIRECTED_REVIEW.mp4"
        shotfile=dirname/f"LOCKED_CHAPTER{i:02}_SHOT_MAP.json"
        rightsfile=dirname/"ASSET_RIGHTS.json"
        confirmed=dirname/"FULL_DECODE.txt"
        assert all(f.is_file() and f.stat().st_size>100 for f in [mp,shotfile,rightsfile]),"Missing chapter "+str(i)
        assert confirmed.is_file() and "decode" in confirmed.read_text().lower(),("Missing full codec decode",i)
        data=probe(mp)
        v=[s for s in data["streams"] if s.get("codec_type")=="video"]
        a=[s for s in data["streams"] if s.get("codec_type")=="audio"]
        assert len(v)==1 and len(a)==1,(i,v,a)
        assert v[0]["codec_name"]=="h264" and (v[0]["width"],v[0]["height"])==(1920,1080),(i,v[0])
        assert a[0]["codec_name"]=="aac",(i,a[0])
        assert v[0].get("r_frame_rate")=="24/1",(i,v[0].get("r_frame_rate"))
        secs=float(data["format"]["duration"])
        shots=json.loads(shotfile.read_text(encoding="utf-8"))
        assert len(shots)>=20 and all(z["id"].startswith(f"C{i:02d}-S") for z in shots),(i,len(shots))
        assert shots[0]["start_seconds"]<=.01,(i,shots[0]["start_seconds"])
        assert abs(shots[-1]["end_seconds"]-secs)<1.3,(i,"Audio-to-picture runtime mismatch")
        assert all(shots[j+1]["start_seconds"]>=shots[j]["end_seconds"]-.12 for j in range(len(shots)-1))
        media=json.loads(rightsfile.read_text(encoding="utf-8"))
        for entry in media:
            assert entry.get("source") and entry.get("license") and entry.get("creator"),(i,entry)
            credits.append({"chapter":i,**entry})
        srt=dirname/f"chapter_{i:02}_ALIGNED_REVIEW.srt"
        if not srt.exists():
            srt=dirname/f"chapter_{i:02}_PRELIMINARY.srt"
            any_prelim.append(i)
        assert srt.is_file(),("No caption file",i)
        block,seq=merge_srt(srt.read_text(encoding="utf-8-sig"),start,seq)
        all_srt.extend(block)
        meta.append({
          "chapter":i,"title":LABELS[i-1],"start_seconds":round(start,3),
          "end_seconds":round(start+secs,3),"duration_seconds":round(secs,3),
          "shot_count":len(shots),"video_sha256":hash_file(mp),
          "source_video":mp.name,"captions":srt.name,
          "narration_coverage_assigned":True,
          "continuous_editorial_approval":False
        })
        tracks.append(mp)
        start+=secs
    return tracks,meta,credits,all_srt,any_prelim

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--chapters",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--validate-only",action="store_true")
    p.add_argument("--skip-decode",action="store_true")
    args=p.parse_args()
    root=Path(args.chapters).resolve()
    out=Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=True)
    tracks,meta,credits,subs,prelim=preflight(root)
    expected=sum(x["duration_seconds"] for x in meta)
    (out/"LOCKED_CHAPTERS.json").write_text(json.dumps(meta,indent=2))
    (out/"SOURCE_AND_RIGHTS_LEDGER.json").write_text(json.dumps(credits,indent=2))
    (out/"documentary_REVIEW.srt").write_text("\n".join(subs)+"\n",encoding="utf-8")
    playlist=out/"chapter_sources.txt"
    playlist.write_text("".join(f"file '{x.as_posix()}'\n" for x in tracks))
    info={"chapter_count":len(meta),"approved_script_shot_segments":sum(x["shot_count"] for x in meta),
      "expected_runtime_seconds":expected,
      "captions_with_estimated_internal_word_timings":prelim,
      "technical_preflight":"PASS",
      "license_record_count":len(credits),
      "scene_by_scene_visual_review":"NOT YET PERFORMED FOR THE COMBINED FILM",
      "continuous_audiovisual_review":"NOT COMPLETED",
      "release_grade":"EDITORIAL_REVIEW_ONLY",
      "youtube_upload_permitted":False}
    (out/"QA_STATUS.json").write_text(json.dumps(info,indent=2))
    if args.validate_only:
        print(json.dumps(info,indent=2));return
    movie=out/"Great_Pyramid_Facts_Uncovered_15_Chapter_DIRECTED_REVIEW_1080p.mp4"
    invoke(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
        "-f","concat","-safe","0","-i",playlist,
        "-map","0:v:0","-map","0:a:0","-c:v","copy",
        "-af","loudnorm=I=-17:TP=-1.2:LRA=11",
        "-c:a","aac","-b:a","224k","-ar","48000","-ac","2",
        "-movflags","+faststart",movie])
    p=probe(movie)
    runtime=float(p["format"]["duration"])
    assert abs(runtime-expected)<3.,(runtime,expected)
    info.update({"actual_runtime_seconds":runtime,
                 "final_mp4_sha256":hash_file(movie),
                 "video_audio_probe":"PASS"})
    if not args.skip_decode:
        with (out/"decode_errors.log").open("w") as e:
            r=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin",
              "-xerror","-i",str(movie),"-map","0:v:0","-map","0:a:0","-f","null","-"],
              stdout=subprocess.DEVNULL,stderr=e)
        assert r.returncode==0,("Full assembled master decode failed",r.returncode)
        info["full_decode"]="PASS"
    else:
        info["full_decode"]="NOT_RUN"
    (out/"QA_STATUS.json").write_text(json.dumps(info,indent=2))
    print(json.dumps(info,indent=2))

if __name__=="__main__": main()
