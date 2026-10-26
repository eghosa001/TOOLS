#!/usr/bin/env python3
"""Facts Uncovered episode: Herculaneum 2026 — source-checked archival slideshow video.
Renders one documentary and two Shorts from verified Creative Commons images,
original editorial graphics, and user-commissioned licensed narration.
"""
from __future__ import annotations
import io, json, math, os, pathlib, re, subprocess, sys, time, urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests
OUT=pathlib.Path("video/history_studio/films/herculaneum_2026/output")
AS=OUT/"assets"; OUT.mkdir(parents=True,exist_ok=True); AS.mkdir(exist_ok=True)
HEAD={"User-Agent":"FactsUncoveredHistoryDocumentary/1.0 (educational media research; https://github.com/eghosa001/TOOLS)"}
FONTS=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
FILES=[
 "Herculaneum papyri.jpg",
 "Herculanean Rolls - Papyrus 157-152.JPG",
 "Heruclaneum Papyrus 1521 f001r, British Library 01.jpg",
 "Abbot-Piaggio-machine-Herculaneum-papyri.jpg",
 "Villa of the Papyri.jpg",
 "PHerc. Paris 4.webp",
 "Herculaneum papyrus 1425.png",
 "Tesoro letterario di Ercolano p27.jpg",
 "ARA 1809 V01 D032 Apparatus used to unroll the Herculenean papyri.jpg",
]
MAIN_SCENES=[
("BURIED FOR 2,000 YEARS","A lost Roman library is being read again"),
("THE BOOK NO ONE COULD OPEN","Preserved by heat. Too fragile to unroll."),
("AD 79 • MOUNT VESUVIUS","Herculaneum and Pompeii were devastated."),
("THE VILLA OF THE PAPYRI","A private Roman collection survived."),
("TURNED TO CHARCOAL","The scrolls became brittle and black."),
("A CENTURIES-OLD PROBLEM","Opening a scroll could destroy its writing."),
("WHAT CHANGED?","X-ray scans created three-dimensional maps."),
("UNWRAPPING WITHOUT TOUCH","Software traces the hidden papyrus layers."),
("JUNE 25, 2026","A breakthrough announced by Vesuvius Challenge."),
("SCROLL PHERC. 1667","The surviving inner portion read end to end."),
("22 COLUMNS OF GREEK","Roughly 1.4 metres of preserved writing."),
("WHAT DID IT REALLY SAY?","Ethics. Reason. Impulse. Moral progress."),
("A POSSIBLE STOIC WORK","The author is still unknown."),
("SCROLL PHERC. 139","Philodemus: On Gods, Book Eight."),
("SEPTEMBER 2026","Promising new lead-ink imaging research."),
("MORE THAN 600 UNOPENED","Hundreds of scrolls still await study."),
("EVIDENCE, NOT SENSATION","Archaeology, imaging and scholarship together."),
("THE LIBRARY SPEAKS AGAIN","Subscribe • Facts Uncovered: Stories & Evidence"),
]
SHORT1_SCENES=[
("THE BOOK NOBODY COULD OPEN","2,000 years in volcanic ash."),
("MOUNT VESUVIUS • AD 79","The eruption carbonised a Roman library."),
("TOO FRAGILE TO TOUCH","One wrong move could destroy the writing."),
("2026 BREAKTHROUGH","The scroll was digitally unwrapped."),
("ANCIENT GREEK REVEALED","A text on ethics and human behaviour."),
("NOT A SECRET PROPHECY","Documented evidence, not invented claims."),
("FACTS UNCOVERED","Subscribe for more extraordinary history."),
]
SHORT2_SCENES=[
("ROME'S LOST LIBRARY","Sealed for nearly 2,000 years."),
("A LOST BOOK TITLE","Philodemus: On Gods, Book Eight."),
("WHY IT MATTERS","A work extended to at least eight books."),
("NOT EVERY SCROLL IS READ","Important mysteries remain."),
("600+ STILL UNOPENED","An enormous library still awaits study."),
("THE NEXT DISCOVERY","Follow Facts Uncovered • Stories & Evidence"),
]
def sh(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def duration(f):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
      "-of","default=noprint_wrappers=1:nokey=1",str(f)],text=True).strip())
def fetch(url,out,timeout=50):
    with requests.get(url,headers=HEAD,stream=True,timeout=timeout,allow_redirects=True) as r:
        r.raise_for_status()
        with out.open("wb") as f:
            total=0
            for chunk in r.iter_content(512*1024):
                if chunk:
                    total+=len(chunk)
                    if total>26_000_000: raise ValueError("oversize source")
                    f.write(chunk)
def get_images():
    accepted=[]
    for fname in FILES:
        try:
            query=requests.get("https://commons.wikimedia.org/w/api.php",params={
                "action":"query","format":"json","prop":"imageinfo",
                "titles":"File:"+fname,"iiprop":"url|extmetadata","iiurlwidth":2000
            },headers=HEAD,timeout=24).json()
            pages=list(query["query"]["pages"].values())
            ii=pages[0]["imageinfo"][0]
            meta=ii.get("extmetadata",{})
            lic=re.sub("<[^>]+>","",meta.get("LicenseShortName",{}).get("value","")).strip()
            lic_url=meta.get("LicenseUrl",{}).get("value","")
            label=(lic+" "+lic_url).lower()
            if not any(x in label for x in ("cc by","cc0","public domain","pdm","pd-old")) or "noncommercial" in label or "nc"==lic.lower():
                print("SKIP_LICENSE",fname,lic,flush=True);continue
            url=ii.get("thumburl") or ii["url"]
            path=AS/("wiki_%02d.jpg"%len(accepted))
            tmp=AS/"download.tmp";fetch(url,tmp)
            im=Image.open(tmp).convert("RGB")
            if min(im.size)<500: raise ValueError("small image")
            im.thumbnail((2200,2200));im.save(path,quality=91)
            accepted.append({"name":fname,"license":lic,"license_url":lic_url,
                 "author":re.sub("<[^>]+>"," ",meta.get("Artist",{}).get("value","")).strip()[:200],
                 "source":"https://commons.wikimedia.org/wiki/File:"+urllib.parse.quote(fname.replace(" ","_")),
                 "local":str(path)})
            tmp.unlink(missing_ok=True)
        except Exception as e:print("SOURCE_UNAVAILABLE",fname,str(e)[:180],flush=True)
    (OUT/"IMAGE_CREDITS.json").write_text(json.dumps(accepted,indent=2))
    print("REAL_ARCHIVAL_IMAGES",len(accepted),flush=True)
    return accepted
def font(size,bold=True):
    return ImageFont.truetype(FONTS[0 if bold else 1],size)
def draw_abstract(w,h,i):
    """Original labeled diagram when an archival image cannot be retrieved."""
    im=Image.new("RGB",(w,h),(15,21,30));d=ImageDraw.Draw(im)
    for j in range(22):
        x=int(w*.5+w*.38*math.cos(j*.71+i));y=int(h*.5+h*.30*math.sin(j*.97+i))
        rad=int(35+j*3);col=(45+j,50+j//2,49+j//3)
        d.ellipse((x-rad,y-rad,x+rad,y+rad),outline=col,width=3)
    return im
def textwrap_px(d,text,f,maxw):
    words=text.split();lines=[];line=""
    for word in words:
        trial=(line+" "+word).strip()
        if d.textbbox((0,0),trial,font=f)[2]>maxw and line:
            lines.append(line);line=word
        else:line=trial
    if line:lines.append(line)
    return lines
def image_cover(im,w,h):
    iw,ih=im.size;s=max(w/iw,h/ih);t=im.resize((int(iw*s)+2,int(ih*s)+2),Image.Resampling.LANCZOS)
    a=(t.width-w)//2;b=(t.height-h)//2;return t.crop((a,b,a+w,b+h))
def compose_card(scene,i,w,h,imgs,vertical=False):
    title,deck=scene;use_img=bool(imgs)
    base=Image.new("RGB",(w,h),(10,17,24))
    src=Image.open(imgs[(i*3+i//3)%len(imgs)]["local"]) if use_img else draw_abstract(w,h,i)
    # Clearly show original evidence. Do not make modern scans appear to be the PHerc.1667 scan.
    bg=image_cover(src,w,h).filter(ImageFilter.GaussianBlur(25 if vertical else 19))
    bg=ImageEnhance.Brightness(bg).enhance(.29)
    base.paste(bg,(0,0));d=ImageDraw.Draw(base,"RGBA")
    # Artwork/evidence framed on the right in landscape, centered in portrait.
    if vertical:
        bx=int(w*.075);by=int(h*.25);bw=int(w*.85);bh=int(h*.43)
    else:
        bx=int(w*.49);by=int(h*.135);bw=int(w*.46);bh=int(h*.69)
    artwork=image_cover(src,bw,bh)
    base.paste(artwork,(bx,by));d=ImageDraw.Draw(base,"RGBA")
    d.rounded_rectangle((bx-3,by-3,bx+bw+3,by+bh+3),radius=10,outline=(211,178,116,240),width=4)
    d.rectangle((0,0,w,int(h*.013)),fill=(204,162,85,255))
    pad=int(w*(.075 if vertical else .045))
    d.text((pad,int(h*.045)),"FACTS UNCOVERED  /  STORIES & EVIDENCE",fill=(225,189,120,255),
        font=font(int(h*(.022 if vertical else .031))))
    if vertical:
        tsize=int(h*.047);tx=pad;ty=int(h*.11);width=w-2*pad
    else:
        tsize=int(h*.061);tx=pad;ty=int(h*.28);width=int(w*.42)
    f=font(tsize);lines=textwrap_px(d,title,f,width)
    for li,line in enumerate(lines[:4]):
        y=ty+li*int(tsize*1.23)
        d.text((tx+2,y+3),line,fill=(0,0,0,200),font=f)
        d.text((tx,y),line,fill=(255,247,227,255),font=f)
    if vertical:
        yd=int(h*.73);deckw=w-2*pad
    else:
        yd=min(int(h*.74),ty+len(lines)*int(tsize*1.25)+28);deckw=int(w*.41)
    f2=font(int(h*(.025 if vertical else .030)),False)
    for j,line in enumerate(textwrap_px(d,deck,f2,deckw)[:4]):
        d.text((tx,yd+j*int(h*.036)),line,font=f2,fill=(232,236,232,255))
    d.text((pad,int(h*.951)),"ARCHIVAL PHOTOGRAPH / EDITORIAL GRAPHIC" if use_img else "ORIGINAL EDUCATIONAL ILLUSTRATION",
        font=font(int(h*.014),False),fill=(210,213,218,210))
    return base.convert("RGB")
def render(name,scenes,audio,imgs,vertical=False,clip_at=0,clip_seconds=None):
    w,h=(1080,1920) if vertical else (1920,1080)
    target=(clip_seconds or duration(audio))+.25
    seconds=target/len(scenes)
    framesdir=AS/name;framesdir.mkdir(exist_ok=True)
    segments=[]
    for i,scene in enumerate(scenes):
        f=framesdir/("card_%02d.jpg"%i)
        compose_card(scene,i,w,h,imgs,vertical).save(f,quality=91,subsampling=0)
        seg=framesdir/("segment_%02d.mp4"%i)
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24",
             "-i",str(f),"-t",str(seconds),
             "-vf",f"zoompan=z='min(zoom+0.00023,1.065)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps=24,format=yuv420p",
             "-an","-c:v","libx264","-preset","veryfast","-crf","22","-r","24","-pix_fmt","yuv420p",
             "-movflags","+faststart",str(seg)]
        sh(cmd);segments.append(seg)
    lst=framesdir/"concat.txt"
    lst.write_text("".join("file '"+p.name+"'\n" for p in segments))
    visual=framesdir/"silent.mp4"
    sh(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
        "-i",str(lst),"-c","copy",str(visual)])
    targetfile=OUT/(name+".mp4")
    mux=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(visual)]
    if clip_at: mux+=["-ss",str(clip_at)]
    mux+=["-i",str(audio),"-map","0:v:0","-map","1:a:0"]
    if clip_seconds:mux+=["-t",str(clip_seconds)]
    mux+=["-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-shortest","-movflags","+faststart",str(targetfile)]
    sh(mux)
    assert targetfile.stat().st_size>200_000
    print("RENDER_READY",targetfile,round(duration(targetfile),1),targetfile.stat().st_size,flush=True)
    return targetfile
def main():
    imgs=get_images()
    audio=AS/"main.mp3";short=AS/"short1.mp3"
    # ElevenLabs documentary narration generated for this exact script.
    for name,dest in (("MAIN_VOICE_URL",audio),("SHORT_VOICE_URL",short)):
        url=os.environ.get(name,"")
        if not url:raise RuntimeError("Missing generated narration: "+name)
        fetch(url,dest,timeout=110)
        assert dest.stat().st_size>20_000
    first=render("Facts_Uncovered_Herculaneum_2026_Documentary",MAIN_SCENES,audio,imgs)
    s1=render("Facts_Uncovered_Herculaneum_2026_Short_01",SHORT1_SCENES,short,imgs,True)
    # Second distinct short remixes a segment of the original full-length voiceover.
    s2=render("Facts_Uncovered_Herculaneum_2026_Short_02",SHORT2_SCENES,audio,imgs,True,
              clip_at=143,clip_seconds=40)
    thumb=compose_card(("AI READ A 2,000-YEAR-OLD SCROLL","What was actually inside?"),8,1280,720,imgs)
    thumb.save(OUT/"thumbnail.jpg",quality=93)
    thumb2=compose_card(("BURIED 2,000 YEARS","And AI finally read it"),3,1080,1920,imgs,True)
    thumb2.save(OUT/"short_cover.jpg",quality=93)
    manifest={"topic":"Herculaneum scrolls","long_video_seconds":duration(first),
              "short1_seconds":duration(s1),"short2_seconds":duration(s2),
              "copyright":"Images: see IMAGE_CREDITS.json; narration: user-commissioned; original editorial graphics: project author",
              "AI_usage":"Machine learning is subject matter; images are licensed archival photographs and original educational graphics; no counterfeit AI archaeological photographs."}
    (OUT/"DELIVERY.json").write_text(json.dumps(manifest,indent=2))
    print("PACKAGE_COMPLETE",flush=True)
if __name__=="__main__":main()
