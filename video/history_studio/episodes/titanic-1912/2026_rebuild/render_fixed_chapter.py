#!/usr/bin/env python3
"""Mechanical FFmpeg exporter for a *specifically authored* Titanic chapter.

This cannot choose, infer, match, or substitute footage. The caller's
chapter design module must render every explicit scene asset ID, and every
archive must have a named source item. Missing sources cause hard failure.
Editorial and full audiovisual release remain blocked until reviewed.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,pathlib,subprocess
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parent
AUDIO=ROOT/"recorded_longform"
TIMING=ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json"
ARCH=ROOT/"archive_intake"
OVERRIDES=ROOT/"ARCHIVE_SCENE_EDITORIAL_REPLACEMENTS.json"

def execute(cmd):
    subprocess.run([str(x) for x in cmd],check=True)
def get_design(file):
    spec=importlib.util.spec_from_file_location("selected_titanic_chapter_artist",str(file))
    if not spec or not spec.loader:raise RuntimeError("No explicit director file")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if not callable(getattr(module,"draw_scene",None)):raise RuntimeError("Design module must have draw_scene(name)")
    return module
def asset_image(row,chapter,artist):
    if row["asset_type"]=="graphic":
        return artist.draw_scene(row["asset_id"])
    if row["asset_type"]!="archive":raise ValueError("Unapproved asset type "+row["asset_type"])
    ledger=json.loads((ARCH/"ARCHIVE_ASSET_LEDGER.json").read_text())
    item=next((x for x in ledger["images"] if x["asset_id"]==row["asset_id"]),None)
    if not item or not item["file"]:raise FileNotFoundError("Selected archive missing; no substitutes: "+row["asset_id"])
    # Chapter design module owns exact crop/framing for each selected photo.
    if not hasattr(artist,"draw_archive"):raise RuntimeError("Art director must author archive composition")
    return artist.draw_archive(row["asset_id"],ARCH/item["file"],item)
def audio_for_chapter(chapter,destination):
    records=json.loads((AUDIO/"NARRATION_TIME_LEDGER.json").read_text())["records"]
    chosen=[r for r in records if r["chapter"]==chapter]
    assert chosen
    with sf.SoundFile(destination,"w",samplerate=24000,channels=1,subtype="PCM_24") as out:
        for rec in chosen:
            voice=AUDIO/(f"T{chapter:02d}_P{rec['paragraph']:02d}.flac")
            data,sr=sf.read(voice,dtype="float32")
            if data.ndim!=1 or sr!=24000:raise RuntimeError("Unexpected audio format "+str(voice))
            out.write(data)
            out.write(np.zeros(round(rec["pause_after_seconds"]*sr),dtype=np.float32))
    return float(chosen[-1]["end_seconds"]-chosen[0]["start_seconds"]),chosen
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--chapter",type=int,required=True)
    parser.add_argument("--designer",type=pathlib.Path,required=True)
    args=parser.parse_args()
    if args.chapter not in range(2,16):raise ValueError("Chapter 1 has separate handmade film")
    artist=get_design(args.designer)
    chapter=args.chapter
    main_root=ROOT/(f"directed_chapter{chapter:02d}")
    plates=main_root/"plates";clips=main_root/"cut_clips"
    for p in (main_root,plates,clips):p.mkdir(exist_ok=True,parents=True)
    scene_data=json.loads(TIMING.read_text())["scenes"]
    shots=[dict(x) for x in scene_data if x["chapter"]==chapter]
    decisions=json.loads(OVERRIDES.read_text())["changes"]
    override={entry[0]:(entry[1],entry[2]) for entry in decisions}
    for row in shots:
        if row["scene_id"] in override:
            row["asset_type"],row["asset_id"]=override[row["scene_id"]]
    if not shots:raise RuntimeError("No hand-authored shots in chapter")
    accepted=set(artist.APPROVED_ASSETS)
    wanted=set(q["asset_id"] for q in shots if q["asset_type"]=="graphic")
    if wanted!=accepted:raise RuntimeError(f"Director asset inventory mismatch: missing={wanted-accepted}, extra={accepted-wanted}")
    video_clips=[]
    for i,row in enumerate(shots,1):
        artwork=asset_image(row,chapter,artist)
        if artwork.size!=(1920,1080):raise RuntimeError("Wrong artwork dimensions "+str(row["scene_id"]))
        png=plates/f"{i:02}_{row['asset_id']}.png"
        artwork.save(png,optimize=True)
        clip=clips/f"cut_{i:02}.mp4"
        frames=max(1,round(row["duration_seconds"]*24))
        execute(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",png,
          "-frames:v",frames,"-c:v","libx264","-preset","veryfast","-crf","20",
          "-pix_fmt","yuv420p","-r","24",clip])
        video_clips.append(clip)
        print("EDITOR_DIRECTED_SHOT",chapter,i,len(shots),row["scene_id"],row["asset_id"],flush=True)
    paths=main_root/"picture_concat.txt"
    paths.write_text("".join("file '"+str(p.resolve())+"'\n" for p in video_clips))
    silent=main_root/"silent_picture.mp4"
    execute(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",paths,
      "-c","copy","-movflags","+faststart",silent])
    joined=main_root/"chapter_narration.wav"
    expected,records=audio_for_chapter(chapter,joined)
    film=main_root/f"TITANIC_CHAPTER_{chapter:02d}_DIRECTED_REVIEW.mp4"
    execute(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",joined,
      "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","224k",
      "-ar","48000","-ac","2","-af","loudnorm=I=-16:TP=-1:LRA=9",
      "-shortest","-movflags","+faststart",film])
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(film)]))
    dur=float(info["format"]["duration"])
    assert abs(dur-expected)<1.4,(dur,expected)
    v=next(x for x in info["streams"] if x["codec_type"]=="video")
    a=next(x for x in info["streams"] if x["codec_type"]=="audio")
    assert (v["width"],v["height"])==(1920,1080) and v["codec_name"]=="h264"
    assert a["codec_name"]=="aac"
    execute(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",film,"-f","null","-"])
    (main_root/"SHOT_MAP_EDITS_REVIEW.json").write_text(json.dumps({"chapter":chapter,"scenes":shots,"release_approved":False},indent=2))
    status={"file":film.name,"chapter":chapter,"seconds":dur,"shots":len(shots),
        "encoded_width":1920,"encoded_height":1080,
        "technical_stream_decode":"PASS",
        "picture_selection":"FIXED SCRIPTED BY EDITOR; NO AUTOMATIC STORY/PIC MATCH",
        "historical_media_rights":"ITEM-SPECIFIC FINAL REVIEW PENDING",
        "continuous_audio_visual_review":"NOT PERFORMED",
        "captions":"WORD-LEVEL CAPTIONS PENDING",
        "full_documentary_completion":False,"publication_approved":False}
    (main_root/"CHAPTER_QA.json").write_text(json.dumps(status,indent=2))
    print("MANUALLY_DIRECTED_CHAPTER_RENDERED_REVIEW_ONLY",json.dumps(status),flush=True)
if __name__=="__main__":main()
