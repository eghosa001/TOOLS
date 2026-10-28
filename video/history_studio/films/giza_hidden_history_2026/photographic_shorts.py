#!/usr/bin/env python3
"""Two 1080x1920 source-first Great Pyramid Shorts.
Seven shots EACH are individually selected against narration anchors.
Real Commons images and published research figures dominate; two Merer explanatory
graphics are expressly labelled. No fake ancient papyrus/inspector photo and
no automatic media search or image placement.
"""
from __future__ import annotations
import argparse,json,sys,subprocess,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter,ImageFont,ImageOps
from directed_shorts import BEATS,cue_words,anchor_time
from directed_chapter01 import get_photo,sha

BASE=Path(__file__).resolve().parent
FPS=24;W=1080;H=1920
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PLAIN="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
GOLD=(238,190,91);WHITE=(255,248,235)
# This is an EXPLICIT, editor-authored shot list. There is no auto-matching.
# G2 modern aerial view; I0 Grand Gallery; G4 archival north-side photograph;
# N0 published muography detector figure (later research, not direct Big Void image);
# G0 historic aerial; NILE research paleogeography map; G3 Matson archival Giza.
SELECTED={
 "01":["G2","I0",None,"I1","G4","N0","G0"],
 "02":["G2",None,None,"NILE","G0","G4","G3"],
}
SUBJECTS={
 "01":[
   "GIZA • ACTUAL GREAT PYRAMID","THE REAL GRAND GALLERY",
   "MUON DETECTION • ORIGINAL EXPLANATORY SCHEMATIC",
   "THE ACTUAL PYRAMID INTERIOR","HISTORIC PHOTOGRAPH • NORTH SIDE",
   "PUBLISHED MUON DETECTOR FIGURE • NOT A VOID PHOTO","HISTORIC ARCHIVAL AERIAL VIEW"],
 "02":[
   "GIZA • DESTINATION OF MERER'S LIMESTONE",
   "WADI AL-JARF • SCHEMATIC LOCATION, NOT A PERIOD MAP",
   "MERER'S ANCIENT LOG • NO VERIFIED PORTRAIT OR PAPYRUS PHOTO",
   "PUBLISHED PALEO-NILE RECONSTRUCTION • NOT AN ANCIENT MAP",
   "AUTHENTIC HISTORICAL VIEW OF KHUFU'S PYRAMID",
   "ARCHIVAL PHOTOGRAPH • REAL ENTRANCE",
   "HISTORIC GIZA • NOT AN ANCIENT TRANSPORT FILM"],
}
SCENE_NOTES={
 "01":[
   "Real site exterior shown while introducing the detected anomaly.",
   "Grand Gallery image shows real architectural context, not Big Void contents.",
   "No direct image of the 2017 unseen cavity; detector method is shown schematically.",
   "Actual interior gallery shown while discussing uncertain purpose.",
   "Historic northern face of Khufu pyramid, not a photograph of treasure.",
   "Published figure shows relevant muography technology from a DIFFERENT study; do not misidentify as original 2017 detectors.",
   "Verified archival aerial photograph depicts real Giza, closing invitation."],
 "02":[
   "Actual Giza site photographed today, destination of limestone linked to Khufu.",
   "No photo is asserted to be the original Wadi al-Jarf papyrus. Site location shown as original clear schematic.",
   "There is no authenticated portrait of the inspector Merer or unlicensed document substitute.",
   "Ahramat Branch scientific map is modern paleogeography, not Merer's recorded boat route.",
   "Actual historic Great Pyramid vista supplies real geographic context for a written ancient record.",
   "The North Entrance photograph is real; it cannot establish how each stone was raised.",
   "Archival Giza panorama, not fabricated Old Kingdom footage."]
}

def run(args):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError("Command failed: "+p.stderr[-2000:])
    return p.stdout.strip()
def dur(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",path]))
def f(sz,bold=True):return ImageFont.truetype(BOLD if bold else PLAIN,sz)
def linebreak(d,caption,maxw,px):
    words=caption.split();lines=[];current=""
    for w in words:
        trial=(current+" "+w).strip()
        if d.textbbox((0,0),trial,font=f(px))[2]>maxw and current:
            lines.append(current);current=w
        else:current=trial
    if current:lines.append(current)
    return lines
def plate(item,asset,head,detail,path,short,n):
    im=Image.new("RGB",(W,H),(14,22,33))
    if item is not None:
        photo=Image.open(asset["path"]).convert("RGB")
        bg=ImageOps.fit(photo,(W,H),Image.Resampling.LANCZOS)
        bg=ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(42))).enhance(.30)
        im.paste(bg)
        fg=ImageOps.contain(photo,(1080,1460),Image.Resampling.LANCZOS)
        im.paste(fg,((W-fg.width)//2,190+(1460-fg.height)//2))
        d=ImageDraw.Draw(im,"RGBA")
        d.rectangle((0,0,W,155),fill=(8,17,28,196))
        d.rectangle((0,1330,W,H),fill=(6,15,26,225))
        label=SUBJECTS[short][n]
        lines=linebreak(d,label,990,26)
        for k,t in enumerate(lines[:3]):
            d.text((46,56+k*37),t,font=f(26),fill=GOLD)
    else:
        d=ImageDraw.Draw(im,"RGBA")
        for y in range(200,1500,80):
            d.line([(35,y),(1050,y)],fill=(55,78,92,88),width=2)
        d.rounded_rectangle((85,390,1000,1150),radius=45,fill=(24,52,65,242),outline=GOLD,width=6)
        if short=="01":
            # Muons travel through differing stone densities. No claim to show actual readings.
            d.polygon([(540,455),(170,1000),(910,1000)],fill=(124,111,91),outline=GOLD,width=5)
            for xx in [220,360,510,650,805]:
                d.line([(xx,490),(xx+40,1090)],fill=(70,199,203),width=5)
            d.rounded_rectangle((390,930,690,1005),radius=12,fill=(38,123,134))
            d.text((420,946),"DETECTORS",font=f(33),fill=WHITE)
        else:
            # Note: rectangles show modern record categories, not invented hieroglyphic text.
            for j,label in enumerate(("INSPECTOR MERER","WADI AL-JARF","LIMESTONE DELIVERIES")):
                d.rounded_rectangle((140,483+j*200,942,607+j*200),radius=18,fill=(67,82,84),outline=GOLD,width=3)
                d.text((180,515+j*200),label,font=f(33),fill=WHITE)
        d.rectangle((0,0,W,150),fill=(8,17,28,196))
        d.text((42,72),"ORIGINAL EXPLANATORY SCHEMATIC • NOT ARCHIVAL FOOTAGE",
               font=f(20),fill=GOLD)
    d=ImageDraw.Draw(im,"RGBA")
    title=BEATS[short][n][1]
    lines=linebreak(d,title,986,51)
    assert len(lines)<=3,(title,lines)
    for k,line in enumerate(lines):
        d.text((48,1410+k*68),line,font=f(51),fill=WHITE,stroke_width=2,stroke_fill=(4,9,18))
    d.line([(45,1595),(1009,1595)],fill=GOLD,width=4)
    # Keep lower area available for burned-in speech captions.
    d.rectangle((0,1860,W,H),fill=(7,14,22,250))
    d.text((34,1880),"FACTS UNCOVERED  •  STORIES & EVIDENCE",font=f(22),fill=GOLD)
    im.save(path,quality=94,subsampling=0)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--catalog",type=Path,default=BASE/"verified_candidate_asset_catalog.json")
    a=ap.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
    catalog=json.loads(a.catalog.read_text())["photos"]
    for n in ("01","02"):
        root=out/n;root.mkdir(exist_ok=True)
        src=a.source/f"short_{n}_CAPTIONED_REVIEW.mp4"
        subtitle=a.source/f"short_{n}_ALIGNED.srt"
        assert src.exists() and subtitle.exists(),(src,subtitle)
        words=cue_words(subtitle)
        anchors=[anchor_time(words,beat[0]) for beat in BEATS[n]]
        duration=dur(src)
        boundaries=[0.]+anchors[1:]+[duration]
        assert len(boundaries)==8 and all(b>a for a,b in zip(boundaries,boundaries[1:]))
        manifest=[];assets={}
        for i,choice in enumerate(SELECTED[n]):
            asset=None
            if choice:
                if choice not in assets:
                    p=catalog[choice]
                    record={"id":"real_"+choice,"commons_title":p["title"],
                        "expected_licence":p["license"],
                        "credit":p["creator"],"source":p["source"]}
                    local=root/("real_"+choice+".jpg")
                    proof=get_photo(record,local)
                    assets[choice]={"path":local,"record":proof}
                asset=assets[choice]
            image=root/f"scene_{i+1:02d}.jpg"
            plate(choice,asset,BEATS[n][i][1],BEATS[n][i][3],image,n,i)
            manifest.append({
                "scene":i+1,"exact_narration_anchor":BEATS[n][i][0],
                "start_seconds":round(boundaries[i],3),
                "end_seconds":round(boundaries[i+1],3),
                "selected_authentic_asset":choice,
                "visual_kind":"REAL_LICENSED_PHOTOGRAPH_OR_PUBLISHED_FIGURE" if choice else "DOCUMENTARY_DIAGRAM",
                "subject_disclosure":SUBJECTS[n][i],
                "editorial_reason":SCENE_NOTES[n][i],
                "source_page_url":asset["record"]["source"] if asset else None,
                "license":asset["record"]["license"] if asset else "ORIGINAL_DRAWING",
                "sha256":asset["record"]["sha256"] if asset else sha(image),
            })
        imageList=root/"segments.txt"
        clips=[]
        for i,shot in enumerate(manifest):
            pic=root/f"scene_{i+1:02d}.jpg"
            clip=root/f"shot_{i+1:02d}.mp4"
            frames=round((shot["end_seconds"]-shot["start_seconds"])*FPS)
            assert frames>=15
            run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                 "-loop","1","-framerate","24","-i",pic,
                 "-frames:v",frames,
                 "-vf","zoompan=z='min(zoom+0.00007,1.025)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1080x1920:fps=24,format=yuv420p",
                 "-c:v","libx264","-preset","veryfast","-crf","19","-an",clip])
            clips.append(clip)
        imageList.write_text("".join(f"file '{q.resolve()}'\n" for q in clips))
        silent=root/"picture.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-f","concat","-safe","0","-i",imageList,"-c","copy",silent])
        finished=out/f"giza_short_{n}_AUTHENTIC_IMAGES_CAPTIONED_REVIEW.mp4"
        # Already audio-aligned SRT, carried over from actual voice, not approximated.
        run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-i",silent,"-i",src,
             "-map","0:v:0","-map","1:a:0",
             "-vf",f"subtitles={subtitle.resolve()}:force_style='FontName=DejaVu Sans,FontSize=30,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Shadow=0,Alignment=2,MarginV=235'",
             "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
             "-c:a","copy","-shortest","-movflags","+faststart",finished])
        real=sum(bool(s["selected_authentic_asset"]) for s in manifest)
        assert real>=5 and abs(dur(finished)-duration)<1
        (out/f"giza_short_{n}_AUTHENTIC_SHOT_MAP.json").write_text(json.dumps(manifest,indent=2))
        (out/f"giza_short_{n}_ASSET_RIGHTS.json").write_text(json.dumps(
            [x["record"] for x in assets.values()],indent=2))
        (out/f"giza_short_{n}_VOICE_ALIGNED.srt").write_text(subtitle.read_text())
        print("AUTHENTIC_SHORT_DONE",n,finished.stat().st_size,real,flush=True)
if __name__=="__main__":main()
