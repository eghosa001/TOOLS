#!/usr/bin/env python3
"""Titanic — manually authored, audio-locked two-Short film compositor.
Each sequence and graphic is intentionally specified by a human/editor.
NO keyword matching, random B-roll, stock substitutions, or looping slideshow.
Preflight and result are review candidates, not automatic publication approval.
"""
from __future__ import annotations
import json, math, os, pathlib, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=pathlib.Path(__file__).resolve().parent
OUTPUT=ROOT/"shorts_review_2026"
OUTPUT.mkdir(parents=True,exist_ok=True)
SCRIPTS=json.loads((ROOT/"SHORTS_FINAL_SCRIPTS_AND_VISUAL_DIRECTION.json").read_text())
MODEL=pathlib.Path(os.environ["KOKORO_MODEL"])
VOICES=pathlib.Path(os.environ["KOKORO_VOICES"])
W,H=1080,1920
GOLD=(234,190,119); WHITE=(247,245,235); GREY=(186,206,218); CYAN=(120,203,225)
BG=(7,19,31)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_CACHE={}
def font(size,bold=False,serif=False):
    k=(size,bold,serif)
    if k not in FONT_CACHE:
        FONT_CACHE[k]=ImageFont.truetype(SERIF if serif else BOLD if bold else FONT,size)
    return FONT_CACHE[k]
def draw_wrapped(d,t,x,y,maxw,sz=40,colour=WHITE,spacing=10,bold=False):
    f=font(sz,bold)
    words=t.split()
    lines=[]
    cur=""
    for word in words:
        cand=(cur+" "+word).strip()
        if cur and d.textbbox((0,0),cand,font=f)[2]>maxw:
            lines.append(cur);cur=word
        else:cur=cand
    if cur:lines.append(cur)
    for line in lines:
        d.text((x,y),line,font=f,fill=colour)
        y+=sz+spacing
    return y
def center(d,t,y,sz=48,fill=WHITE,bold=False,serif=False):
    f=font(sz,bold,serif)
    box=d.textbbox((0,0),t,font=f)
    d.text(((W-(box[2]-box[0]))//2,y),t,font=f,fill=fill)
def base(number,chapter):
    im=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(im)
    for y in range(H):
        a=y/H
        col=(max(0,int(7+4*a)),int(19+16*a),int(31+18*a))
        d.line((0,y,W,y),fill=col)
    # fixed, deliberate cartographic rule lines, not random stars
    for x in (68,1012):
        d.line((x,145,x,1450),fill=(30,61,76),width=2)
    d.line((68,137,1012,137),fill=(92,125,142),width=2)
    d.text((76,86),"FACTS UNCOVERED",font=font(36,True),fill=WHITE)
    d.text((76,149),chapter.upper(),font=font(21,True),fill=GOLD)
    d.text((950,152),f"{number:02}",font=font(24,True),fill=GREY)
    return im,d
def headline(d,small,main,sub=""):
    d.text((77,254),small.upper(),font=font(29,True),fill=CYAN)
    y=304
    y=draw_wrapped(d,main.upper(),76,y,916,70,GOLD,10,True)
    if sub:draw_wrapped(d,sub,80,y+22,900,27,GREY,5)
def boat(d,x,y,scale=1,col=GOLD):
    w=int(118*scale);h=int(35*scale)
    d.polygon([(x,y),(x+w,y),(x+w-18*scale,y+h),(x+18*scale,y+h)],fill=(42,84,105),outline=col)
    d.line((x+14*scale,y-14*scale,x+w-14*scale,y-14*scale),fill=GREY,width=max(2,int(3*scale)))
    d.line((x+14*scale,y-14*scale,x+14*scale,y),fill=GREY,width=2)
    d.line((x+w-14*scale,y-14*scale,x+w-14*scale,y),fill=GREY,width=2)
def ship(d,y=1050,scale=1.0):
    left=int(115*scale);right=int(978*scale)
    sy=int(y)
    d.polygon([(left,sy),(right,sy),(right-130*scale,sy+180*scale),(left+130*scale,sy+180*scale)],fill=(18,40,53),outline=(179,190,182))
    d.rectangle((left+105*scale,sy-110*scale,right-100*scale,sy),fill=(164,155,129))
    d.rectangle((left+200*scale,sy-175*scale,right-190*scale,sy-105*scale),fill=(205,190,152))
    for i in range(4):
        xx=left+273*scale+i*128*scale
        d.polygon([(xx,sy-174*scale),(xx+19*scale,sy-360*scale),(xx+68*scale,sy-360*scale),(xx+83*scale,sy-174*scale)],fill=(198,137,84),outline=(224,191,134))
        d.rectangle((xx+14*scale,sy-360*scale,xx+73*scale,sy-327*scale),fill=(18,20,24))
    for row in (sy+60*scale,sy+96*scale):
        for xx in range(int(left+140*scale),int(right-80*scale),int(55*scale)):
            d.ellipse((xx,row,xx+7*scale,row+7*scale),fill=GOLD)
def panel(d,x,y,w,h):
    d.rounded_rectangle((x,y,x+w,y+h),radius=24,fill=(20,46,63),outline=(82,123,139),width=2)
def big(d,s,y,sub):
    center(d,s,y,130,GOLD,True)
    center(d,sub,y+153,29,GREY,True)
def bar(d,x,y,w,ratio,label,num):
    d.rounded_rectangle((x,y,x+w,y+48),radius=15,fill=(39,66,81))
    d.rounded_rectangle((x,y,x+w*ratio,y+48),radius=15,fill=GOLD)
    d.text((x,y-54),label,font=font(29,True),fill=WHITE)
    d.text((x+w-180,y-57),str(num),font=font(32,True),fill=GOLD)
def seabed(d):
    for i in range(5):
        pts=[(x,int(1140+i*58+18*math.sin(x/90+i))) for x in range(85,1020,10)]
        d.line(pts,fill=(35+i*8,82+i*7,100+i*7),width=3)
    d.ellipse((150,1200,880,1330),fill=(10,31,43),outline=(65,104,120),width=4)
def figure(d):
    # Historical object is a clearly labeled silhouette, not a counterfeit photo.
    center(d,"ILLUSTRATIVE SILHOUETTE",555,24,CYAN)
    d.ellipse((463,656,563,776),fill=(177,184,187))
    d.polygon([(440,774),(573,774),(625,1110),(382,1110)],fill=(153,164,171))
    d.polygon([(390,813),(434,801),(340,975),(315,1040),(290,1025)],fill=(169,175,178))
    d.polygon([(572,805),(606,800),(722,750),(754,730),(773,765),(692,804),(604,913)],fill=(169,175,178))
    d.polygon([(388,1105),(621,1105),(596,1182),(413,1182)],fill=(121,135,146))
    d.rectangle((365,1181,646,1219),fill=(146,159,166))
    d.text((365,1240),"Bronze statuette, not a photograph",font=font(24),fill=GREY)
def iceberg(d):
    d.polygon([(610,950),(750,590),(818,762),(906,672),(1025,981)],fill=(115,172,196),outline=(189,222,232))
    d.polygon([(660,937),(756,690),(803,794),(922,754),(994,957)],fill=(57,117,148))
    d.line((75,977,1010,977),fill=CYAN,width=7)
def closing(d):
    d.ellipse((385,550,695,860),outline=GOLD,width=9)
    d.polygon([(475,635),(475,790),(615,714)],fill=GOLD)
    center(d,"FACTS UNCOVERED",930,63,WHITE,True)
    center(d,"STORIES & EVIDENCE",1017,30,GREY)
    d.rounded_rectangle((225,1132,855,1263),radius=28,fill=(180,47,40))
    center(d,"SUBSCRIBE",1160,62,WHITE,True)
    center(d,"More evidence-led history",1353,31,CYAN)
def visual(kind,im,d):
    if kind=="s1_ship":
        headline(d,"The evacuation","20 LIFEBOATS","Titanic — period-correct illustrative ship silhouette")
        ship(d,900,.95)
        for i in range(20):boat(d,104+(i%5)*186,1290+(i//5)*82,.76)
        center(d,"ILLUSTRATIVE VISUALIZATION",1650,23,GREY)
    elif kind=="s1_aboard":
        headline(d,"British 1912 inquiry","PEOPLE ON BOARD")
        big(d,"2,201",640,"PASSENGERS AND CREW")
        d.line((170,1045,910,1045),fill=GOLD,width=6)
        center(d,"Reported in the British inquiry",1150,31,WHITE)
        center(d,"Official counts differ between records",1230,25,GREY)
    elif kind=="s1_boats":
        headline(d,"Total rescue equipment","1,178 PLACES")
        for i in range(20):boat(d,105+(i%5)*188,655+(i//5)*144,.82)
        d.rounded_rectangle((140,1250,940,1410),radius=23,fill=(18,52,71),outline=GOLD,width=4)
        center(d,"TOTAL RATED CAPACITY",1300,42,WHITE,True)
    elif kind=="s1_types":
        headline(d,"Official breakdown","14 + 2 + 4")
        for a,(title,num,cap) in enumerate([("STANDARD",14,910),("EMERGENCY",2,80),("COLLAPSIBLE",4,188)]):
            y=625+a*230
            panel(d,120,y,840,190)
            d.text((155,y+21),title,font=font(32,True),fill=GREY)
            d.text((155,y+74),str(num),font=font(69,True),fill=GOLD)
            d.text((438,y+99),f"{cap} spaces",font=font(32),fill=WHITE)
    elif kind=="s1_deficit":
        headline(d,"Even if every seat was used","1,023 WITHOUT A SEAT")
        bar(d,160,755,760,1,"PEOPLE ABOARD",2201)
        bar(d,160,1000,760,1178/2201,"LIFEBOAT SPACES",1178)
        d.text((156,1185),"ILLUSTRATIVE CAPACITY COMPARISON",font=font(25,True),fill=GREY)
    elif kind=="s1_empty":
        headline(d,"British inquiry evidence","SOME BOATS LEFT PARTLY EMPTY")
        for i,(number,actual,capacity) in enumerate([("BOAT 1",12,40),("BOAT 7",27,65)]):
            y=680+i*345
            panel(d,112,y,865,280)
            d.text((145,y+25),number,font=font(43,True),fill=WHITE)
            d.text((145,y+111),f"{actual} / {capacity}",font=font(86,True),fill=GOLD)
            d.rounded_rectangle((145,y+227,918,y+250),radius=8,fill=(34,64,84))
            d.rounded_rectangle((145,y+227,145+773*(actual/capacity),y+250),radius=8,fill=GOLD)
        center(d,"Per 1912 British inquiry • Actual totals disputed",1452,22,GREY)
    elif kind=="s1_causes":
        headline(d,"Not one isolated failure","THE ICE + THE EVACUATION")
        iceberg(d)
        d.rounded_rectangle((148,1115,932,1285),radius=21,fill=(20,55,73),outline=GOLD,width=3)
        center(d,"THE RESCUE SYSTEM",1143,43,WHITE,True)
        center(d,"Could not carry everyone",1214,29,GREY)
        center(d,"Illustrative historical reconstruction",1450,24,GREY)
    elif kind=="s2_wreck":
        headline(d,"Deep North Atlantic","THE WRECK IS CHANGING")
        seabed(d)
        d.polygon([(205,1020),(782,913),(733,1160),(326,1205)],fill=(54,91,103),outline=(140,166,170))
        for xx in range(330,760,90):
            d.line((xx,1030,xx,1100),fill=(181,174,138),width=5)
        center(d,"ORIGINAL WRECK ILLUSTRATION",1480,25,GREY)
    elif kind=="s2_bow":
        headline(d,"2024 expedition","15 FEET OF RAILING")
        d.polygon([(520,580),(720,1110),(760,1340),(280,1340),(320,1110)],fill=(48,93,110),outline=(165,205,212))
        d.polygon([(520,640),(661,1080),(690,1300),(345,1300),(380,1080)],fill=(29,66,85))
        d.line((373,1005,336,1160),fill=GOLD,width=17)
        d.line((334,1162,162,1162),fill=GOLD,width=5)
        d.text((112,1101),"PORT SIDE",font=font(28,True),fill=WHITE)
        d.text((110,1205),"MISSING",font=font(33,True),fill=GOLD)
        center(d,"SCHEMATIC • NOT TO SCALE",1460,25,GREY)
    elif kind=="s2_diana":
        headline(d,"2024 rediscovery","DIANA OF VERSAILLES")
        figure(d)
        center(d,"Found in the debris field",1440,30,WHITE)
    elif kind=="s2_decay":
        headline(d,"More than a century later","SLOW DEEP-SEA DECAY")
        for n,x in enumerate((110,570)):
            panel(d,x,680,405,590)
            d.text((x+40,720),"EARLIER" if n==0 else "TODAY",font=font(34,True),fill=GOLD)
            for k in range(7):
                xx=x+35+k*48
                d.line((xx,850,xx+(24 if n else 0),1100),fill=(93,140,151) if n else (152,183,185),width=5 if n else 7)
            d.line((x+35,1100,x+360,1100),fill=GREY,width=6)
            if n:
                for v in range(12):
                    ex=x+55+(v%5)*63;ey=945+(v%3)*68
                    d.ellipse((ex,ey,ex+12,ey+27),fill=(128,85,56))
        center(d,"Illustrative comparison • Not measured change",1460,25,GREY)
    elif kind=="s2_scan":
        headline(d,"Modern mapping","2022 → 2025")
        for i,(year,desc) in enumerate([("2022","Digital survey conducted"),("2025","Survey widely presented")]):
            y=715+i*325
            panel(d,136,y,808,230)
            d.text((174,y+31),year,font=font(91,True),fill=GOLD)
            d.text((178,y+147),desc,font=font(30),fill=WHITE)
        d.line((531,958,531,1040),fill=CYAN,width=7)
        d.polygon([(506,1025),(556,1025),(531,1063)],fill=CYAN)
    elif kind=="s2_evidence":
        headline(d,"Historical investigation","TWO FORMS OF EVIDENCE")
        for i,(title,subtitle) in enumerate([("1912","WITNESS TESTIMONY"),("2020s","PHYSICAL WRECK SURVEYS")]):
            y=670+i*375
            panel(d,135,y,800,290)
            d.text((182,y+35),title,font=font(83,True),fill=GOLD)
            d.text((182,y+168),subtitle,font=font(30,True),fill=WHITE)
        center(d,"Neither can answer every question alone",1537,25,GREY)
    elif kind=="close":
        closing(d)
    else:raise ValueError("Unapproved shot "+kind)
def subtitle_box(im,d,spoken):
    # One accurately time-locked sentence block per shot; full exact SRT also included.
    panel(d,93,1588,894,247)
    for y in range(1605,1612):
        d.line((116,y,964,y),fill=(78,126,146))
    text=spoken
    sz=33
    for candidate in (37,35,33,31,29):
        test=ImageDraw.Draw(im)
        linecount=0;words=[];cur=""
        for w in text.split():
            nw=(cur+" "+w).strip()
            if cur and test.textbbox((0,0),nw,font=font(candidate,True))[2]>817:
                linecount+=1;cur=w
            else:cur=nw
        if cur:linecount+=1
        if linecount<=4:sz=candidate;break
    draw_wrapped(d,spoken,126,1630,827,sz,WHITE,11,True)
def build_video(tag,shots,engine):
    outdir=OUTPUT/tag;outdir.mkdir(exist_ok=True)
    files=[];entries=[];now=0
    for idx,(text,kind) in enumerate(shots):
        image,draw=base(idx+1,"Titanic • Lifeboats" if tag.endswith("01") else "Titanic • Wreck")
        visual(kind,image,draw)
        subtitle_box(image,draw,text)
        plate=outdir/f"scene_{idx+1:02}.png";image.save(plate,optimize=True)
        wav,sr=engine.create(text,voice="am_michael",speed=0.94,lang="en-us")
        wav=np.asarray(wav,dtype=np.float32).reshape(-1)
        assert sr==24000 and np.isfinite(wav).all() and len(wav)>int(sr*1.2)
        audio=outdir/f"scene_{idx+1:02}.wav";sf.write(audio,wav,sr,subtype="PCM_24")
        dur=len(wav)/sr
        video=outdir/f"scene_{idx+1:02}.mp4"
        # Restrained, exact-frame static artwork: no generic Ken Burns loops.
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",str(plate),
                        "-i",str(audio),"-t",f"{dur:.5f}","-c:v","libx264","-preset","veryfast","-crf","19",
                        "-pix_fmt","yuv420p","-r","24","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",
                        "-movflags","+faststart",str(video)],check=True)
        files.append(video)
        entries.append({"scene":idx+1,"narration":text,"selected_visual":kind,"start_seconds":round(now,3),
          "end_seconds":round(now+dur,3),"visual_asset":plate.name,"graphic_original":True,
          "audio_source":audio.name,"creative_selection":"MANUALLY WRITTEN IN FIXED SHOT TABLE",
          "visual_review":"NOT VERIFIED IN ACTUAL VIDEO"})
        now+=dur
        print("SHOT_RENDERED",tag,idx+1,len(shots),round(dur,2),flush=True)
    listing=outdir/"concat.txt"
    listing.write_text("".join("file '"+str(x.resolve())+"'\n" for x in files))
    result=OUTPUT/(tag+"_review_1080x1920.mp4")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(listing),
                    "-c","copy","-movflags","+faststart",str(result)],check=True)
    def timecode(seconds):
        millis=round(seconds*1000);hours,millis=divmod(millis,3600000)
        minutes,millis=divmod(millis,60000);sec,millis=divmod(millis,1000)
        return f"{hours:02}:{minutes:02}:{sec:02},{millis:03}"
    srt=OUTPUT/(tag+"_review.srt")
    srt.write_text("\n".join(f"{j}\n{timecode(e['start_seconds'])} --> {timecode(e['end_seconds'])}\n{e['narration']}\n" for j,e in enumerate(entries,1)),encoding="utf8")
    (OUTPUT/(tag+"_manual_shot_timeline.json")).write_text(json.dumps({"video":result.name,"shots":entries,
      "all_visual_assets":"ORIGINAL SVG/PIL DESIGNS, NO EXTERNAL FOOTAGE","total_narrated_seconds":round(now,3),
      "release_approved":False},indent=2))
    ff=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(result)]))
    v=next(s for s in ff["streams"] if s["codec_type"]=="video")
    a=next(s for s in ff["streams"] if s["codec_type"]=="audio")
    assert v["codec_name"]=="h264" and (v["width"],v["height"])==(1080,1920) and a["codec_name"]=="aac"
    assert 40<=float(ff["format"]["duration"])<=65,(tag,now)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",str(result),"-f","null","-"],check=True)
    # Every Short ends with the actual spoken and on-screen subscribe cue.
    assert shots[-1][1]=="close" and "Subscribe to Facts Uncovered" in shots[-1][0]
    qa={"file":result.name,"seconds":float(ff["format"]["duration"]),"codec":"h264+aac",
      "resolution":"1080x1920","shots":len(shots),"narration_audio":"re-synthesized and timed per fixed shot",
      "subtitle_alignment":"shot/sentence exact; word-level not assessed",
      "complete_render_decode":"PASS",
      "technical_only":"Not a continuous human audiovisual viewing review",
      "historical_sources":"1912 British inquiry and 2024 RMS Titanic, Inc. expedition",
      "publication_approved":False,"visual_full_review":"NOT PERFORMED"}
    (OUTPUT/(tag+"_technical_review.json")).write_text(json.dumps(qa,indent=2))
    return qa
def main():
    first=[
("Titanic had twenty lifeboats. They couldn't save everyone aboard.","s1_ship"),
("The official British investigation counted two thousand two hundred and one people on the ship.","s1_aboard"),
("But all twenty boats combined had room for only eleven hundred and seventy-eight.","s1_boats"),
("Fourteen were standard lifeboats, two were smaller emergency boats, and four were collapsibles.","s1_types"),
("Even if every seat had been filled, more than a thousand people would still have lacked a place.","s1_deficit"),
("And during the confusion, several boats left partly empty.","s1_empty"),
("The problem wasn't just the iceberg. It was also a rescue system that could never evacuate everyone.","s1_causes"),
("For the full story, watch our Titanic documentary. Subscribe to Facts Uncovered for more history.","close")]
    second=[
("Titanic's wreck is changing before our eyes.","s2_wreck"),
("In twenty twenty-four, an expedition found that a fifteen-foot section of railing had fallen from the port side of the ship's famous bow.","s2_bow"),
("The same expedition rediscovered a bronze statuette of the goddess Diana in the debris field.","s2_diana"),
("The deep ocean is slowly changing what remains of Titanic.","s2_decay"),
("And while a detailed digital survey was carried out in twenty twenty-two, its findings reached a wider audience in twenty twenty-five.","s2_scan"),
("Those images are new evidence, but they cannot tell us everything about the final night.","s2_evidence"),
("See how historians investigate the wreck in our full Titanic documentary. Subscribe to Facts Uncovered for more historical discoveries.","close")]
    import re
    normalize=lambda x:re.sub(r"\s+"," ",x).strip()
    assert normalize(" ".join(t for t,_ in first))==normalize(SCRIPTS["deliverables"][0]["narration"])
    assert normalize(" ".join(t for t,_ in second))==normalize(SCRIPTS["deliverables"][1]["narration"])
    from kokoro_onnx import Kokoro
    engine=Kokoro(str(MODEL),str(VOICES))
    results=[build_video("titanic_short_01",first,engine),build_video("titanic_short_02",second,engine)]
    (OUTPUT/"DELIVERY_REPORT.json").write_text(json.dumps({"project":"Titanic two explicitly directed Shorts",
      "technical_exports":results,"release_approved":False,
      "reason":"Continuous film-and-audio review, personal media approval, and licensed final main documentary unavailable"},indent=2))
    print("TWO_EDITOR_DIRECTED_SHORTS_REVIEW_EXPORTS_DONE",json.dumps(results),flush=True)
if __name__=="__main__":
    main()
