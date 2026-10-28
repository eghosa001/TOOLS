#!/usr/bin/env python3
"""Two deliberately art-directed real-photo-first Great Pyramid vertical Shorts.

7 exact narration beats per Short are inherited unchanged from previous videos.
The choices below are NOT search terms or a generated montage: they are an explicit
sequence of individual historical photos and necessary scientific exceptions.
"""
from __future__ import annotations
import argparse,json,math,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
from directed_chapter01 import archive_assets
from directed_shorts import BEATS,frame as original_concept_frame
from curate_remaining_authentic_photo_shots import get_photo

W,H,FPS=1080,1920,24
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
# Every numbered slot is explicitly approved against its exact spoken topic.
# Short 02's first three elements MUST remain diagrams: no accurate public photo
# of the Merer papyrus, Wadi al-Jarf port, or Inspector Merer's face was verified.
IMAGE_EDIT_DECISIONS={
 "01":["G","I","X",None,"V","G","A"],
 "02":[None,None,None,"F","T","G","G"]
}
DIAGRAM_DISCLOSURES={
 ("01",4):"THE PURPOSE OF THE BIG VOID IS UNKNOWN — SCIENTIFIC EXPLANATION",
 ("02",1):"MODERN PAPYRUS SCHEMATIC — NOT THE ORIGINAL DIARY",
 ("02",2):"ILLUSTRATIVE RED SEA PORT — NOT AN ANCIENT PHOTOGRAPH",
 ("02",3):"MODERN ARTISTIC FIGURE — NOT A PORTRAIT OF MERER",
}
def run(*args):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError("FFmpeg error: "+p.stderr[-1700:])
    return p.stdout.strip()
def title_block(draw,words,x,y,width,initial=67):
    for sz in range(initial,38,-2):
        font=ImageFont.truetype(BOLD,sz)
        lines=[];buf=""
        for word in words.split():
            cand=(buf+" "+word).strip()
            if draw.textbbox((0,0),cand,font=font)[2]>width and buf:
                lines.append(buf);buf=word
            else:buf=cand
        if buf:lines.append(buf)
        if len(lines)<=3:
            for j,line in enumerate(lines):
                draw.text((x,y+j*(sz+14)),line,font=font,fill="#ffffff",
                          stroke_fill="#07121b",stroke_width=2)
            return
    raise ValueError("Caption title too large: "+words)
def real_frame(beat,img,photo,out):
    original=Image.open(img).convert("RGB")
    outimage=ImageOps.fit(original,(W,H),Image.Resampling.LANCZOS,centering=(.52,.47)).convert("RGBA")
    veil=Image.new("RGBA",(W,H),(0,0,0,0))
    shade=ImageDraw.Draw(veil,"RGBA")
    for y in range(0,950,7):
        alpha=int(210*(1-y/950)**1.9)
        shade.rectangle((0,y,W,y+7),fill=(4,11,20,alpha))
    shade.rectangle((0,1450,W,H),fill=(6,13,24,178))
    outimage=Image.alpha_composite(outimage,veil)
    d=ImageDraw.Draw(outimage,"RGBA")
    d.rectangle((0,0,W,12),fill=(227,183,95,255))
    d.text((75,87),"FACTS UNCOVERED",font=ImageFont.truetype(BOLD,39),fill="#f0c27b")
    title_block(d,beat[1],75,228,930,65)
    d.rounded_rectangle((58,1335,1022,1465),radius=24,fill=(5,19,30,202),outline="#c5a76f",width=3)
    f=ImageFont.truetype(FONT,28)
    desc=beat[3].split()
    lines=[];current=""
    for x in desc:
        t=(current+" "+x).strip()
        if d.textbbox((0,0),t,font=f)[2]>885 and current:
            lines.append(current);current=x
        else:current=t
    if current:lines.append(current)
    for k,line in enumerate(lines[:3]):d.text((89,1363+k*31),line,font=f,fill="#ffffff")
    source=photo["photo_context"]
    d.text((69,1824),source[:80],font=ImageFont.truetype(FONT,18),fill="#e5dbbf")
    outimage.convert("RGB").save(out,quality=94,subsampling=0)
def one(short,source,out):
    beats=BEATS[short]
    decisions=IMAGE_EDIT_DECISIONS[short]
    assert len(beats)==len(decisions)==7
    prev=json.loads((source/f"giza_short_{short}_shot_map.json").read_text())
    shots=prev["beats"]
    assert len(shots)==7 and all(float(v["end"])>float(v["start"]) for v in shots)
    archived={}
    for token in set(t for t in decisions if t):
        archived[token]={"id":"real_"+token.lower(),**get_photo(token)}
    assets=archive_assets(out,{"original_photos":list(archived.values())})
    clips=[];reports=[]
    for i,(beat,shot,token) in enumerate(zip(beats,shots,decisions),start=1):
        plate=out/f"{short}_authentic_plate_{i:02}.jpg"
        if token:
            record=assets[archived[token]["id"]]
            real_frame(beat,record["path"],archived[token],plate)
            kind="AUTHENTIC_SOURCE_PHOTO"
            source_page=archived[token]["source"]
            label=archived[token]["photo_context"]
        else:
            original_concept_frame(beat[1],beat[2],beat[3],beat[0],plate)
            kind="ORIGINAL_EXPLANATORY_DIAGRAM"
            source_page="https://doi.org/10.1038/nature24647" if short=="01" else "https://aeraweb.org/"
            label=DIAGRAM_DISCLOSURES[(short,i)]
        clip=out/f"scene_{short}_{i:02}.mp4"
        length=float(shot["end"])-float(shot["start"])
        frames=round(length*FPS)
        assert frames>12
        vf=f"zoompan=z='min(zoom+0.00007,1.025)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s={W}x{H}:fps={FPS},format=yuv420p"
        run("ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-loop","1","-framerate",FPS,"-i",plate,"-frames:v",frames,"-vf",vf,
            "-c:v","libx264","-preset","veryfast","-crf",19,"-pix_fmt","yuv420p","-an",clip)
        clips.append(clip)
        reports.append({"shot":i,"start":shot["start"],"end":shot["end"],
            "spoken_anchor":beat[0],"visual_kind":kind,"source":source_page,
            "visual_disclosure":label,"actual_photo_id":token,"editorial_selection":"EXPLICIT_NUMERICAL_SHOT"})
    cat=out/f"short_{short}_edit_list.txt"
    cat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in clips))
    silent=out/f"short_{short}_silent.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
        "-f","concat","-safe","0","-i",cat,"-c","copy",silent)
    src=source/f"short_{short}_CAPTIONED_REVIEW.mp4"
    subtitles=source/f"short_{short}_ALIGNED.srt"
    assert src.is_file() and subtitles.is_file()
    exported=out/f"short_{short}_AUTHENTIC_PHOTO_CAPTIONED_REVIEW.mp4"
    vf=("subtitles="+str(subtitles.resolve())+":force_style='FontName=DejaVu Sans,FontSize=28,"
        "Outline=3,Shadow=0,Alignment=2,MarginV=264'")
    run("ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
        "-i",silent,"-i",src,"-map","0:v:0","-map","1:a:0",
        "-vf",vf,"-c:v","libx264","-preset","medium","-crf",19,"-pix_fmt","yuv420p",
        "-c:a","copy","-movflags","+faststart","-shortest",exported)
    old_len=float(run("ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=noprint_wrappers=1:nokey=1",src))
    new_len=float(run("ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=noprint_wrappers=1:nokey=1",exported))
    assert abs(old_len-new_len)<.5,(old_len,new_len)
    assert sum(s["visual_kind"]=="AUTHENTIC_SOURCE_PHOTO" for s in reports)>3
    cover=out/f"short_{short}_AUTHENTIC_COVER.jpg"
    ImageOps.fit(Image.open(out/f"{short}_authentic_plate_01.jpg"),(1080,1920)).save(cover,quality=92)
    (out/f"short_{short}_SOURCE_AND_SHOT_MAP.json").write_text(json.dumps(reports,indent=2))
    return exported
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for n in ("01","02"):
        video=one(n,args.source,args.out)
        print("REAL_PHOTO_SHORT_COMPLETE",n,video,video.stat().st_size,flush=True)
if __name__=="__main__":main()
