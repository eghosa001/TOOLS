#!/usr/bin/env python3
"""Actual rendered frame inspection images across the eight newly revised Titanic chapters.

Samples real MP4 pixels; rejects black/corrupt samples, writes contact sheets.
This does NOT replace a continuous audiovisual human screening.
"""
from __future__ import annotations
from pathlib import Path
import json,subprocess,math,statistics
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent.parent
FILM=ROOT/"source_first_repair"/"eight_master_review"/"TITANIC_86MIN_EIGHT_REAL_ARCHIVE_CHAPTERS_EDITOR_REVIEW.mp4"
TIMES=json.loads((ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json").read_text())["chapters"]
OUT=ROOT/"source_first_repair"/"frame_review_eight_corrected";OUT.mkdir(exist_ok=True)
FT=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
SAMPLES=(.025,.185,.355,.525,.695,.865,.975)
def run(cmd):
    subprocess.run([str(x) for x in cmd],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def main():
    qa=[];problems=[]
    for chapter in (1,2,3,4,5,8,12,13):
        d=TIMES[str(chapter)];start=float(d["start_seconds"]);end=float(d["end_seconds"])
        thumbs=[]
        for number,fraction in enumerate(SAMPLES):
            position=start+fraction*(end-start)
            path=OUT/f"chapter{chapter:02d}_sample{number+1}.jpg"
            run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",f"{position:.3f}",
                 "-i",FILM,"-frames:v","1","-vf","scale=388:218","-q:v","3",path])
            with Image.open(path) as im:
                p=im.convert("RGB");small=p.resize((64,36))
                pix=list(small.getdata());mean=sum(sum(q)/3 for q in pix)/len(pix)
                if mean<4:problems.append({"chapter":chapter,"time":position,"problem":"POSSIBLE BLACK SCREEN"})
                thumbs.append((path,mean,position))
        sheet=Image.new("RGB",(4*406,2*269),(8,16,27))
        draw=ImageDraw.Draw(sheet)
        draw.text((15,7),f"TITANIC • CHAPTER {chapter:02d} • rendered MP4 excerpts",font=FT,fill=(244,222,176))
        for j,(path,mean,pos) in enumerate(thumbs):
            x=(j%4)*406+11;y=(j//4)*260+36
            with Image.open(path) as im:sheet.paste(im,(x,y))
            draw.text((x,y+222),f"{pos/60:.1f} min  brightness {mean:.1f}",font=FT,fill=(208,215,217))
        sheet.save(OUT/f"titanic_chapter{chapter:02d}_actual_frames_contact_sheet.jpg",quality=91)
        qa.append({"chapter":chapter,"images":[{"time":round(t,3),"average_brightness":round(v,2)} for _,v,t in thumbs]})
        print("ACTUAL_RENDERED_FILM_FRAME_CONTACT_SHEET",chapter,len(thumbs),flush=True)
    report={"chapters":8,"actual_video_samples":len(qa)*len(SAMPLES),
       "contact_sheets":8,"suspected_blank_or_invalid_frames":problems,
       "actual_full_human_viewing":"NOT PERFORMED",
       "audio_entire_film_review":"NOT PERFORMED",
       "source":FILM.name,"release_approved":False}
    (OUT/"CONTACT_SHEET_QA.json").write_text(json.dumps(report,indent=2))
    if problems:raise RuntimeError(f"Potential blank frames: {problems[:10]}")
    print("TITANIC_EIGHT_CORRECTED_CHAPTERS_56_REAL_FRAME_SAMPLES_PASS",report["actual_video_samples"],flush=True)
if __name__=="__main__":main()
