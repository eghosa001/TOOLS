#!/usr/bin/env python3
"""TITANIC: Director-authored Chapter 01 source-art and picture preview.

Every visual below was selected deliberately for one exact scene in
MANUAL_SCENE_LEDGER_DRAFT.json. No keyword matching, random B-roll,
stock substitution, or footage search. Mechanical FFmpeg composition
uses ONLY that fixed selected order and real Kokoro sample durations.

REVIEW EXPORT, NOT A PUBLISHABLE FINISHED FILM.
"""
from __future__ import annotations
import json, math, os, pathlib, subprocess, hashlib
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageOps,ImageFilter

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"directed_chapter01";ART=OUT/"plates";CLIPS=OUT/"cut_clips"
AUDIO=ROOT/"recorded_longform"
ARCH=ROOT/"archive_intake"
TIMING=ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json"
for p in (OUT,ART,CLIPS):p.mkdir(parents=True,exist_ok=True)
W,H=1920,1080; CREAM=(248,245,234); GOLD=(232,194,122); MUTED=(167,190,206)
BORDER=(79,111,129); BLUE=(35,92,117)
FONTS="/usr/share/fonts/truetype/dejavu/"
def f(px,bold=False,serif=False):
    name="DejaVuSerif-Bold.ttf" if serif and bold else "DejaVuSerif.ttf" if serif else "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(FONTS+name,px)
def text_center(d,text,y,size=54,fill=CREAM,bold=False,serif=False):
    ft=f(size,bold,serif);bb=d.textbbox((0,0),text,font=ft)
    d.text(((W-bb[2]+bb[0])//2,y),text,font=ft,fill=fill)
def wrap(d,txt,x,y,width,size=43,fill=CREAM,spacing=13,bold=False):
    ft=f(size,bold);row="";lines=[]
    for word in txt.split():
        cand=(row+" "+word).strip()
        if row and d.textbbox((0,0),cand,font=ft)[2]>width:
            lines.append(row);row=word
        else:row=cand
    if row:lines.append(row)
    for line in lines:d.text((x,y),line,font=ft,fill=fill);y+=size+spacing
    return y
def frame(key,subtitle):
    im=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        d.line((0,y,W,y),fill=(int(5+11*t),int(17+19*t),int(30+24*t)))
    d.rectangle((62,65,1858,1013),outline=(47,81,102),width=2)
    d.text((101,91),"FACTS UNCOVERED  /  STORIES & EVIDENCE",font=f(29,True),fill=CREAM)
    d.rectangle((101,142,216,148),fill=GOLD)
    d.text((1590,92),"TITANIC • 1912",font=f(24,True),fill=MUTED)
    d.text((102,961),subtitle,font=f(22),fill=MUTED)
    d.text((1790,963),"01 / 15",font=f(20,True),fill=GOLD)
    return im,d
def title(d,a,b="",sub=""):
    d.text((107,206),a.upper(),font=f(60,True,True),fill=CREAM)
    if b:d.text((109,282),b.upper(),font=f(36,True),fill=GOLD)
    if sub:wrap(d,sub,115,359,1420,24,MUTED,7)
def ship(d,x=150,y=666,scale=1):
    # Original simplified side-profile illustration. Not historical photo.
    ww=int(1430*scale);hh=int(175*scale)
    d.polygon([(x,y),(x+ww,y),(x+ww-125*scale,y+hh),(x+110*scale,y+hh)],
               fill=(13,27,34),outline=(190,191,165))
    d.rectangle((x+96*scale,y-75*scale,x+ww-123*scale,y),fill=(188,179,148))
    d.rectangle((x+240*scale,y-125*scale,x+ww-260*scale,y-76*scale),fill=(222,204,167))
    for j in range(4):
        xx=x+(370+j*196)*scale
        d.rectangle((xx,y-294*scale,xx+91*scale,y-126*scale),fill=(193,134,80))
        d.rectangle((xx,y-294*scale,xx+91*scale,y-256*scale),fill=(13,20,24))
    d.line((x+205*scale,y-94*scale,x+210*scale,y-380*scale),fill=(201,207,207),width=5)
    for row in range(2):
        for xx in range(x+110,x+ww-95,62):
            yy=int(y+51*scale+row*45*scale)
            d.ellipse((xx,yy,xx+7,yy+7),fill=GOLD)
def boat(d,x,y,scale=1):
    ww=int(98*scale)
    d.polygon([(x,y),(x+ww,y),(x+ww-16*scale,y+30*scale),(x+16*scale,y+30*scale)],fill=(76,104,117),outline=GOLD)
    d.line((x+15,y-12*scale,x+ww-15,y-12*scale),fill=CREAM,width=2)
def sea(d,level=770):
    for j in range(1,10):
        yy=level+j*23
        pts=[(x,int(yy+5*math.sin(x/90+j*3))) for x in range(64,1857,11)]
        d.line(pts,fill=(39+j*4,83+j*6,109+j*6),width=2)
def ocean(d,moon=False):
    for j in range(50):
        xx=115+(j*673)%1592;yy=420+(j*197)%244
        d.ellipse((xx,yy,xx+2,yy+2),fill=(129+j%50,149+j%45,164+j%34))
    if moon:d.ellipse((1450,367,1516,433),outline=(167,177,183),width=2)
    sea(d,810)
def clock(d,cx,cy,r,hour,minute):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=GOLD,width=6)
    for k in range(12):
        theta=math.pi*k/6-math.pi/2
        d.line((cx+math.cos(theta)*(r-25),cy+math.sin(theta)*(r-25),
                cx+math.cos(theta)*(r-12),cy+math.sin(theta)*(r-12)),fill=CREAM,width=5)
    theta=(hour%12+minute/60)*math.pi/6-math.pi/2
    d.line((cx,cy,cx+math.cos(theta)*r*.45,cy+math.sin(theta)*r*.45),fill=GOLD,width=8)
    theta=minute*math.pi/30-math.pi/2
    d.line((cx,cy,cx+math.cos(theta)*r*.72,cy+math.sin(theta)*r*.72),fill=CREAM,width=5)
def ruled_document(d,x,y,w,h,heading,date,kind):
    d.rounded_rectangle((x,y,x+w,y+h),radius=7,fill=(232,222,198),outline=(153,132,92),width=4)
    d.text((x+35,y+39),heading,font=f(38,True,True),fill=(36,45,48))
    d.text((x+35,y+105),date,font=f(22),fill=(73,73,66))
    for j in range(7):
        d.line((x+34,y+166+j*54,x+w-43,y+166+j*54),fill=(143,146,130),width=2)
    d.text((x+35,y+h-73),"ILLUSTRATIVE TITLE LAYOUT",font=f(19,True),fill=(105,93,73))
def label_box(d,x,y,w,h,big,small):
    d.rounded_rectangle((x,y,x+w,y+h),radius=16,fill=(24,54,70),outline=GOLD,width=2)
    d.text((x+22,y+29),big,font=f(65,True),fill=GOLD)
    wrap(d,small,x+24,y+119,w-43,24,CREAM,6)
def drawing(name,subtitle):
    im,d=frame(name,subtitle)
    if name=="night_north_atlantic_calm":
        title(d,"NORTH ATLANTIC","SUNDAY • 14 APRIL 1912","Original visualization • the sea is shown calm, not rough")
        ocean(d)
        ship(d,420,719,.67)
    elif name=="crows_nest_collision_warning":
        title(d,"THE LOOKOUT","THREE BELLS • ICE AHEAD")
        ship(d,250,745,.72)
        d.line((607,512,607,368),fill=CREAM,width=8)
        d.ellipse((573,353,640,400),outline=GOLD,width=5)
        d.line((647,387,900,430),fill=GOLD,width=4)
        label_box(d,900,421,725,235,"3","Lookout warning bell strokes")
    elif name=="ship_clock_1140_0220":
        title(d,"THE FINAL 160 MINUTES","TITANIC'S SHIPBOARD CLOCK")
        clock(d,567,662,231,11,40);clock(d,1325,662,231,2,20)
        text_center(d,"11:40 PM                 2:20 AM",906,45,GOLD,True)
        d.line((842,664,1012,664),fill=GOLD,width=8)
        d.polygon([(1008,638),(1046,664),(1008,691)],fill=GOLD)
    elif name=="160min_damage_response_timeline":
        title(d,"TWO HOURS, FORTY MINUTES","COLLISION TO SINKING")
        d.line((211,634,1706,634),fill=GOLD,width=8)
        data=[("11:40","COLLISION"),("MIDNIGHT","ASSESSMENT"),("AFTER 12","LIFEBOATS"),("2:20","SINKS")]
        for i,(tm,lab) in enumerate(data):
            x=218+i*490
            d.ellipse((x-16,618,x+16,650),fill=CREAM)
            d.text((x-80,698),tm,font=f(35,True),fill=GOLD)
            d.text((x-87,752),lab,font=f(23,True),fill=CREAM)
        d.text((200,858),"TIMES IN SHIP'S TIME • MIDNIGHT EVENTS APPROXIMATE",font=f(24),fill=MUTED)
    elif name=="two_1912_inquiries_title_pages":
        title(d,"THE ORIGINAL RECORD","TWO INVESTIGATIONS • 1912")
        ruled_document(d,163,409,717,454,"U.S. SENATE","WASHINGTON • 1912","official")
        ruled_document(d,1033,409,716,454,"BRITISH INQUIRY","LONDON • 1912","official")
    elif name=="eyewitness_conflict_illustration":
        title(d,"WITNESSES DISAGREED","TESTIMONY IS EVIDENCE • NOT A CAMERA")
        for i,(hd,sub) in enumerate([("ACCOUNT A","A witness saw the ship from one position"),("ACCOUNT B","Another witness remembered a different detail")]):
            x=157+i*868
            d.rounded_rectangle((x,446,x+744,827),radius=16,fill=(18,43,61),outline=BORDER,width=3)
            d.ellipse((x+65,492,x+210,637),fill=(118,146,157))
            d.polygon([(x+29,688),(x+244,688),(x+260,780),(x+17,780)],fill=(81,108,126))
            d.text((x+295,504),hd,font=f(38,True),fill=GOLD)
            wrap(d,sub,x+295,583,392,28,CREAM,8)
    elif name=="archival_vs_reconstruction_legend":
        title(d,"WHAT IS ORIGINAL?","DISTINGUISH ARCHIVE FROM RECONSTRUCTION")
        for i,(v,l) in enumerate([("1912","ORIGINAL HISTORICAL PHOTOGRAPH"),("DRAWN","ILLUSTRATED HISTORICAL EXPLANATION")]):
            x=150+i*890
            d.rounded_rectangle((x,466,x+770,845),radius=14,fill=(29,57,70),outline=GOLD if i else BORDER,width=3)
            d.text((x+50,552),v,font=f(77,True,True),fill=GOLD)
            wrap(d,l,x+50,677,660,28,CREAM,11)
    elif name=="lifeboat_14_2_4_layout":
        title(d,"TWENTY BOATS","14 STANDARD  •  2 EMERGENCY  •  4 COLLAPSIBLE")
        for i in range(20):
            xx=170+(i%10)*155;yy=506+(i//10)*150
            boat(d,xx,yy,1.12)
            d.text((xx+21,yy+52),str(i+1),font=f(22,True),fill=MUTED)
        d.text((200,900),"CAPACITY FROM THE 1912 BRITISH WRECK COMMISSIONER'S REPORT",font=f(23),fill=CREAM)
    elif name=="capacity_1178_vs_2201":
        title(d,"NOT ENOUGH PLACES","THE BRITISH INQUIRY'S COUNTS")
        data=[("PEOPLE ABOARD",2201,GOLD),("LIFEBOAT PLACES",1178,CYAN)]
        for i,(lab,val,col) in enumerate(data):
            y=503+i*205
            d.text((152,y),lab,font=f(34,True),fill=CREAM)
            d.rounded_rectangle((152,y+66,1590,y+121),radius=20,fill=(38,67,83))
            d.rounded_rectangle((152,y+66,152+1438*(val/2201),y+121),radius=20,fill=col)
            d.text((1620,y+57),str(val),font=f(47,True),fill=col)
        d.text((200,901),"2,201 − 1,178 = 1,023 WITHOUT A RATED PLACE",font=f(33,True),fill=GOLD)
    elif name=="ice_warning_morning_to_midnight":
        title(d,"ICE WARNINGS","A CHAIN OF MESSAGES")
        d.line((330,515,1600,515),fill=GOLD,width=7)
        for i,(t,s) in enumerate([("9:00 AM","CARONIA"),("1:42 PM","BALTIC"),("11:40 PM","COLLISION")]):
            x=340+i*628
            d.ellipse((x-18,497,x+18,533),fill=CREAM)
            d.text((x-75,585),t,font=f(36,True),fill=GOLD)
            d.text((x-78,638),s,font=f(29,True),fill=CREAM)
        d.text((205,790),"Times from the British inquiry; other messages are addressed later.",font=f(26),fill=MUTED)
    elif name=="carpathia_rescue_distance_uncertain":
        title(d,"THE RESCUE SHIP","HELP WAS COMING • DISTANCE MATTERED")
        d.line((290,680,1530,680),fill=GOLD,width=4)
        for x,t in [(290,"TITANIC"),(1530,"CARPATHIA")]:
            d.ellipse((x-19,661,x+19,699),fill=CREAM)
            d.text((x-100,735),t,font=f(38,True),fill=GOLD)
        d.arc((560,420,1230,920),start=180,end=365,fill=CYAN,width=7)
        d.text((450,837),"SCHEMATIC • NOT A PRECISE COORDINATE MAP",font=f(24),fill=MUTED)
    elif name=="lit_ship_vs_unsafe_open_lifeboat":
        title(d,"WHY WOULD ANYONE LEAVE?","BRIGHT DECKS ABOVE A DARK SEA")
        ship(d,170,700,.85);sea(d,868)
        boat(d,1440,845,1.6)
        d.line((1520,698,1520,835),fill=GOLD,width=3)
        d.text((1170,564),"Illustrative decision",font=f(27,True),fill=GOLD)
    elif name=="boarding_decision_high_above_sea":
        title(d,"THE EVACUATION","A SMALL BOAT OVER OPEN WATER")
        d.line((270,508,1500,508),fill=CREAM,width=6)
        for x in (820,1280):
            d.line((x,510,x,758),fill=GOLD,width=5)
        boat(d,780,765,5)
        sea(d,863)
        text_center(d,"ARTISTIC RECONSTRUCTION • NOT A 1912 PHOTOGRAPH",908,22,MUTED)
    elif name=="channel_logo_evidence_subscribe":
        title(d,"FACTS UNCOVERED","STORIES & EVIDENCE")
        d.ellipse((730,403,1190,857),outline=GOLD,width=11)
        d.polygon([(852,526),(852,739),(1064,634)],fill=GOLD)
        text_center(d,"Follow the sources. Question the myths.",906,32,CREAM)
    else:raise ValueError("The proposed art asset has no individually authored design: "+name)
    return im

def archive_image(name):
    meta=json.loads((ARCH/"ARCHIVE_ASSET_LEDGER.json").read_text())["images"]
    row=next(z for z in meta if z["asset_id"]==name)
    if not row["file"]:raise RuntimeError("Manual source selected but no verified candidate image: "+name)
    src=Image.open(ARCH/row["file"]).convert("RGB")
    im,d=frame(name,"ARCHIVAL PHOTOGRAPH • SOURCE AND RIGHTS LISTED IN EDITORIAL LEDGER")
    # Preserve photograph entirely with natural background, not deformed or center cropped.
    src.thumbnail((1630,690),Image.Resampling.LANCZOS)
    x=(W-src.width)//2;y=230+(620-src.height)//2
    d.rectangle((x-14,y-14,x+src.width+14,y+src.height+14),fill=(42,53,55),outline=GOLD,width=3)
    im.paste(src,(x,y))
    text_center(d,row["requested_description"].upper(),873,26,GOLD,True)
    return im

def write_audio():
    timeline=json.loads((AUDIO/"NARRATION_TIME_LEDGER.json").read_text())
    records=[x for x in timeline["records"] if x["chapter"]==1]
    assert len(records)==8
    path=OUT/"chapter01_sound.wav"
    with sf.SoundFile(path,"w",samplerate=24000,channels=1,subtype="PCM_24") as h:
        for row in records:
            filename=AUDIO/("T01_P%02d.flac"%row["paragraph"])
            sound,sr=sf.read(filename,dtype="float32")
            if sr!=24000:raise RuntimeError("Unexpected sample rate")
            h.write(sound)
            h.write(np.zeros(round(row["pause_after_seconds"]*sr),dtype=np.float32))
    return path,float(records[-1]["end_seconds"])

def run(cmd):
    subprocess.run([str(s) for s in cmd],check=True)

def main():
    allshots=json.loads(TIMING.read_text())["scenes"]
    shots=[x for x in allshots if x["chapter"]==1]
    assert len(shots)==16
    unique={x["asset_id"] for x in shots}
    expected={"night_north_atlantic_calm","crows_nest_collision_warning",
      "ship_clock_1140_0220","160min_damage_response_timeline","two_1912_inquiries_title_pages",
      "eyewitness_conflict_illustration","archival_vs_reconstruction_legend",
      "lifeboat_14_2_4_layout","capacity_1178_vs_2201","ice_warning_morning_to_midnight",
      "carpathia_rescue_distance_uncertain","lit_ship_vs_unsafe_open_lifeboat",
      "boarding_decision_high_above_sea","channel_logo_evidence_subscribe",
      "ship_southampton","departure_3000"}
    if unique!=expected:raise RuntimeError("Unapproved visual selection: "+str(unique^expected))
    clips=[]
    for i,shot in enumerate(shots):
        image=archive_image(shot["asset_id"]) if shot["asset_type"]=="archive" else drawing(shot["asset_id"],"ORIGINAL 2D EXPLANATORY GRAPHIC")
        png=ART/("%02d_"%(i+1)+shot["asset_id"]+".png")
        image.save(png,optimize=True)
        clip=CLIPS/("cut_%02d.mp4"%(i+1))
        n=max(1,round(shot["duration_seconds"]*24))
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",png,
             "-frames:v",n,"-c:v","libx264","-preset","veryfast","-crf","20",
             "-pix_fmt","yuv420p","-r","24",clip])
        clips.append(clip)
        print("CUT_RENDERED",i+1,len(shots),shot["scene_id"],n,flush=True)
    listing=OUT/"concat.txt";listing.write_text("".join("file '"+str(z.resolve())+"'\n" for z in clips))
    silent=OUT/"chapter01_picture_silent.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",listing,
       "-c","copy","-movflags","+faststart",silent])
    voice,expected_dur=write_audio()
    finished=OUT/"TITANIC_CHAPTER_01_MANUALLY_DIRECTED_REVIEW.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",voice,
       "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","224k",
       "-ar","48000","-ac","2","-af","loudnorm=I=-16:TP=-1:LRA=9",
       "-shortest","-movflags","+faststart",finished])
    check=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(finished)]))
    dur=float(check["format"]["duration"])
    assert abs(dur-expected_dur)<1.2,(dur,expected_dur)
    v=next(z for z in check["streams"] if z["codec_type"]=="video")
    a=next(z for z in check["streams"] if z["codec_type"]=="audio")
    assert (v["width"],v["height"])==(1920,1080) and v["codec_name"]=="h264" and a["codec_name"]=="aac"
    run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",finished,"-f","null","-"])
    report={"file":finished.name,"seconds":dur,"shots":16,"chapter":1,"codec":"H.264/AAC",
       "resolution":"1920x1080","source_visuals":[z["asset_id"] for z in shots],
       "narration_source":"Kokoro 2026 151 paragraphs 86.88 minute master; exact Chapter 01 recording",
       "video_review":"NOT FULLY WATCHED AND LISTENED THROUGH",
       "creative_selections":"ALL FIXED AND EXPLICIT IN CHAPTER 01 CODE; NO AUTO SEARCH",
       "media_rights":"individual source status candidate; full publishing rights review pending",
       "subtitles":"word-level speech alignment pending",
       "release_approved":False,
       "chapter_02_15_status":"NOT RENDERED"}
    (OUT/"CHAPTER_01_TECHNICAL_QA.json").write_text(json.dumps(report,indent=2))
    print("TITANIC_CHAPTER01_PICTURE_AND_AUDIO_REVIEW_EXPORT_DONE",json.dumps(report),flush=True)
if __name__=="__main__":main()
