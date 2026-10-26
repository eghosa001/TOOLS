#!/usr/bin/env python3
"""Build two sourced documentary masters and six Shorts, with unique timed shots.

No publish step. A finished export still requires whole-film human visual/audio
review under video/history_studio/QUALITY_STANDARD.md.
"""
from __future__ import annotations
import argparse, hashlib, html, io, json, math, os, random, re, subprocess, sys, time, urllib.parse, urllib.request, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

HERE=Path(__file__).resolve().parent
DOC=json.loads((HERE/"episode_research_and_scripts.json").read_text(encoding="utf8"))
OUT=HERE/"output"
OUT.mkdir(exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
assert all(Path(p).exists() for p in (FONT,BOLD,SERIF))

def run(*cmd):
    subprocess.run([str(c) for c in cmd],check=True,stderr=subprocess.PIPE)
def ffprobe(filename):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(filename)]))
def seconds(filename):
    return float(ffprobe(filename)["format"]["duration"])
def fnt(size,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,max(12,int(size)))
def croptext(text,maxlen=63):
    words=text.strip().split()
    lines=[];line=""
    for w in words:
        if len(line+" "+w)>maxlen:
            if line:lines.append(line)
            line=w
        else:line=(line+" "+w).strip()
    if line:lines.append(line)
    return lines
def shade(col,sc=1):
    return tuple(min(255,max(0,int(c*sc))) for c in col)
def shell_get(url,tries=2,maxbytes=14_000_000):
    for trial in range(tries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"HistoryStudio/2026 (https://github.com/eghosa001/TOOLS)","Accept":"application/json,image/*"})
            with urllib.request.urlopen(req,timeout=28) as f:
                block=f.read(maxbytes+1)
            if 500<len(block)<maxbytes:return block
        except Exception as exc:
            print("SOURCE_RETRY",url[:85],str(exc)[:120],flush=True)
            time.sleep(1+trial)
    return None

def allowed_license(ext):
    label=html.unescape(re.sub("<[^>]*>","",ext.get("LicenseShortName",{}).get("value","")))
    z=re.sub(r"[^a-z0-9]","",label.lower())
    if "nc" in z or "nd" in z:return None
    permitted=("publicdomain" in z or z.startswith("pd") or z.startswith("cc0")
               or z.startswith("ccby40") or z.startswith("ccbysa40")
               or z.startswith("ccby30") or z.startswith("ccbysa30"))
    if permitted:
        return label
    return None

def get_wikimedia_assets(id,limit=16):
    """Fetch licensed distinct historical photographs; gracefully omit non-cleared items."""
    if id=="molasses":
        categories=["Boston Molasses Disaster","Boston Elevated Railway after the Molasses Flood"]
        searches=["Boston Molasses Disaster","1919 Boston molasses tank"]
    else:
        categories=["Herculaneum papyri","Villa of the Papyri","Herculaneum scrolls"]
        searches=["Herculaneum papyrus","Villa of the Papyri papyri","Herculaneum carbonized papyrus"]
    raw=[]
    for category in categories:
        q={"action":"query","format":"json","generator":"categorymembers","gcmtitle":"Category:"+category,
           "gcmnamespace":6,"gcmlimit":50,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":2200}
        raw.append(q)
    for term in searches:
        q={"action":"query","format":"json","generator":"search","gsrsearch":term,"gsrnamespace":6,
           "gsrlimit":40,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":2200}
        raw.append(q)
    seen=set();assets=[]
    for q in raw:
        data=shell_get("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(q))
        if not data:continue
        try: pages=json.loads(data).get("query",{}).get("pages",{})
        except (ValueError,TypeError):continue
        for p in pages.values():
            inf=(p.get("imageinfo") or [{}])[0]
            lic=allowed_license(inf.get("extmetadata",{}))
            url=inf.get("thumburl") or inf.get("url")
            typ=inf.get("mime","")
            if not lic or not url or p["title"] in seen:continue
            if not re.search(r"\.(jpg|jpeg|png)(\?|$)",url,re.I):continue
            filename=p["title"].lower()
            if id=="molasses" and not ("molasses" in filename or "boston post-january" in filename):continue
            if id=="herculaneum" and not any(k in filename for k in ("papy", "hercul", "ercolano", "piaggio", "vesuvius", "villa")):continue
            if id=="molasses" and any(b in p["title"].lower() for b in ["2014","marker","2020","map","2025"]):continue
            seen.add(p["title"]);assets.append({"title":p["title"],"url":url,"license":lic,"source":"https://commons.wikimedia.org/wiki/"+urllib.parse.quote(p["title"].replace(" ","_")),"artist":re.sub("<[^>]*>","",inf.get("extmetadata",{}).get("Artist",{}).get("value",""))[:250]})
        if len(assets)>=limit*2:break
    image_dir=OUT/id/"archive";image_dir.mkdir(parents=True,exist_ok=True)
    approved=[]
    for it in assets:
        if len(approved)>=limit:break
        raw=shell_get(it["url"],maxbytes=18_000_000)
        if not raw:continue
        try:
            im=Image.open(io.BytesIO(raw));im.verify()
            im=Image.open(io.BytesIO(raw)).convert("RGB")
            if im.width<700 or im.height<420:continue
            fn=image_dir/f'archive_{len(approved)+1:02}.jpg'
            im.save(fn,quality=94,optimize=True)
            it["file"]=str(fn);it["sha256"]=hashlib.sha256(fn.read_bytes()).hexdigest();approved.append(it)
        except Exception as exc:
            print("INVALID_IMAGE",str(exc)[:120])
    (OUT/id/"IMAGE_CREDITS.json").write_text(json.dumps(approved,indent=2,ensure_ascii=False))
    print("LICENSED_ARCHIVE_IMAGES",id,len(approved),flush=True)
    return approved

def voice_engine():
    model=os.environ.get("PIPER_MODEL")
    config=os.environ.get("PIPER_CONFIG")
    if not model or not config:raise RuntimeError("PIPER_MODEL and PIPER_CONFIG required; no draft eSpeak voice is permitted for release-grade export")
    from piper.voice import PiperVoice
    return PiperVoice.load(model,config_path=config)

def narrate(voice,text,fn):
    fn.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(fn),"wb") as f:
        voice.synthesize_wav(text,f)
    d=seconds(fn)
    if not 1.1<d<160:raise ValueError(f"Invalid narration duration {fn}: {d}")
    return d

def background(size,seed,episode):
    w,h=size;rng=random.Random(seed)
    palette=([(9,20,30),(31,47,56),(226,169,86),(150,95,70)] if episode=="molasses" else [(10,24,35),(28,57,68),(220,181,111),(144,124,89)])
    base=np.zeros((h,w,3),dtype=np.uint8)
    a=np.array(palette[0],dtype=float);b=np.array(palette[1],dtype=float)
    for y in range(h):
        q=y/max(1,h-1)
        base[y,:,:]=np.array((a*(1-q)+b*q),dtype=np.uint8)
    noise=np.random.default_rng(seed).integers(-5,6,(h,w,1),dtype=np.int16)
    base=np.clip(base.astype(np.int16)+noise,0,255).astype(np.uint8)
    im=Image.fromarray(base,"RGB");d=ImageDraw.Draw(im)
    # Different unique architectural and scientific geometry in every shot.
    for i in range(45):
        x=rng.randrange(w);y=rng.randrange(h);sz=rng.randrange(25,max(28,w//4))
        col=shade(palette[2],rng.uniform(.11,.27))
        if i%2:d.arc((x-sz,y-sz,x+sz,y+sz),rng.randrange(0,300),rng.randrange(300,360),fill=col,width=max(2,w//500))
        else:d.line([(x,y),(x+sz,y-rng.randrange(10,130))],fill=col,width=max(2,w//420))
    return im,palette

def narrative_illustration(im,scene,palette,seed,vertical=False):
    """Prefer a subject-specific scene to an unrelated generic icon."""
    kind=scene.get("type","").removesuffix("_detail")
    subview=scene["id"].endswith("_B")
    w,h=im.size;d=ImageDraw.Draw(im)
    cx=int(w*(.50 if vertical else .64));cy=int(h*.49)
    r=int(min(w,h)*.30)
    gold=palette[2];cream=(236,225,202);dark=(42,52,58);rust=(168,98,66);teal=(114,158,164)
    def txt(s,x,y,size=36,color=cream,bold=True):
        d.text((int(x),int(y)),str(s),font=fnt(size,bold),fill=color)
    def rod(a,b,colour=gold,width=9):
        d.line((int(a[0]),int(a[1]),int(b[0]),int(b[1])),fill=colour,width=width)
    if kind=="leak":
        # A close-up of the leaking seam is different from every full-tank illustration.
        d.rounded_rectangle((cx-r*2,cy-r,cx+r*2,cy+r),22,fill=(66,78,82),outline=gold,width=6)
        rod((cx-r*2,cy),(cx+r*2,cy),(218,194,154),13)
        for x in range(cx-r*2+45,cx+r*2,80):
            d.ellipse((x-12,cy-12,x+12,cy+12),fill=cream,outline=dark,width=2)
        for j in range(12 if subview else 8):
            x=cx-r+50+j*50
            y=cy+25+(j%3)*23
            d.ellipse((x-7,y,x+6,y+22+(j%4)*7),fill=rust)
        txt("SEAMS  •  RIVETS  •  LEAKS",cx-r*2+30,cy+r-75,29,gold)
        return True
    if kind=="burst":
        # Ruptured tank with opening, broken steel and a spreading wave.
        d.rounded_rectangle((cx-r,cy-r,cx+r,cy+r),20,fill=(69,82,84),outline=gold,width=9)
        zig=[(cx+15,cy-r),(cx-25,cy-r//3),(cx+45,cy),(cx-35,cy+r//2),(cx+28,cy+r)]
        d.line(zig,fill=(10,22,32),width=28,joint="curve")
        d.line(zig,fill=(240,151,105),width=7)
        for j in range(8):
            yy=cy+r//3+j*int(r*.14)
            pts=[(cx-r*2+k*22, yy+int(math.sin(k*.18+j)*18)) for k in range(int(r*4/22))]
            d.line(pts,fill=shade(rust,1.14+j*.035),width=14)
        if subview:txt("STRUCTURAL FAILURE",cx-r*2,cy-r-60,35,(255,184,145))
        return True
    if kind=="diagram":
        # A measured filled-volume diagram, not a repeat of the cylindrical tank shot.
        x=cx-r;y=cy-r
        d.rounded_rectangle((x,y,cx+r,cy+r),28,outline=gold,width=8)
        d.rectangle((x+15,cy-r//4,cx+r-15,cy+r-15),fill=(144,85,54))
        for j in range(6):
            yy=cy-r+j*r*2//5
            rod((x-30,yy),(x+8,yy),cream,5)
        txt("2.3",cx-r+28,cy-r//3,115,gold)
        txt("MILLION GALLONS",cx-r+30,cy+r//5,33,cream)
        if subview:
            d.arc((cx-r-120,cy-r-120,cx+r+120,cy+r+120),20,340,fill=gold,width=12)
        return True
    if kind=="map":
        # Stylized locality diagram with labelled waterline; explicitly schematic.
        for i in range(7):
            xx=cx-r*2+i*r*2//3;rod((xx,cy-r),(xx+r//7,cy+r),teal,5)
        for i in range(7):
            yy=cy-r+i*r//3;rod((cx-r*2,yy),(cx+r*2,yy-r//7),cream,4)
        d.polygon([(cx+r,cy-r*2),(cx+r*2,cy-r),(cx+r*2,cy+r*2),(cx+r,cy+r*2)],fill=(33,86,112))
        d.ellipse((cx-28,cy-28,cx+28,cy+28),fill=(250,118,91),outline=cream,width=5)
        txt("NORTH END",cx-r*2,cy-r-100,45,gold)
        txt("BOSTON HARBOR",cx+r//2,cy+r,28,cream)
        txt("SCHEMATIC / NOT TO SCALE",cx-r*2,cy+r+35,24,teal)
        return True
    if kind=="victims":
        # Grief and remembrance; no falsely historical invented photographs.
        for j in range(21):
            x=cx-r*2+(j%7)*r*2//3;y=cy-r+(j//7)*r//2
            d.ellipse((x,y,x+25,y+25),fill=(231,201,150))
            rod((x+13,y+25),(x+13,y+60),teal,5)
        txt("21 LIVES LOST",cx-r*2,cy+r-25,60,cream)
        return True
    if kind=="rescue":
        # A rope/ladder and lifelines with moving silhouettes, not repeated iconography.
        for j in range(14):
            yy=cy-r+j*r//6
            rod((cx-r,yy),(cx+r,yy),gold,5)
        rod((cx-r,cy-r),(cx-r//2,cy+r),cream,9)
        rod((cx+r//2,cy-r),(cx+r,cy+r),cream,9)
        for i in range(3):
            x=cx-r*2+i*r*3//4;y=cy+r//4+(i%2)*35
            d.ellipse((x-19,y-85,x+19,y-46),fill=cream)
            rod((x,y-46),(x+12,y+13),cream,12)
            rod((x+7,y-10),(x+60,y-42),cream,9)
            rod((x+12,y+13),(x-10,y+71),cream,8)
        txt("RESCUE THROUGH WRECKAGE",cx-r*2,cy-r-80,30,gold)
        return True
    if kind in ("pherc1667","pherc172","pherc139"):
        # Source-identified manuscript panels avoid implying a random papyrus is the named object.
        label={"pherc1667":"PHerc. 1667","pherc172":"PHerc. 172","pherc139":"PHerc. 139"}[kind]
        summary={"pherc1667":"20 COLUMNS / GREEK ETHICS",
                 "pherc172":"ON VICES / BOOK ONE",
                 "pherc139":"ON GODS / BOOK EIGHT"}[kind]
        d.rounded_rectangle((cx-r*2,cy-r,cx+r*2,cy+r),24,fill=(79,67,54),outline=gold,width=6)
        for j in range(12 if subview else 8):
            x=cx-r*2+48+j*r//3
            if x>cx+r*2-60:break
            for k in range(17):
                yy=cy-r+50+k*int(r*.083)
                d.line((x,yy,x+r//4,yy),fill=(199,165,108),width=3)
        txt(label,cx-r*2+55,cy-r-85,66,gold)
        txt(summary,cx-r*2+50,cy+r-65,38,cream)
        txt("ILLUSTRATION / NOT A TRANSCRIPTION",cx-r*2+50,cy+r-23,23,teal)
        return True
    if kind=="unwrap":
        # Scan cylinder → segmented layers → flat surface, a chronological process.
        d.ellipse((cx-r*2,cy-r,cx-r//2,cy+r),outline=gold,width=9)
        for j in range(5):
            pad=j*23
            d.ellipse((cx-r*2+pad,cy-r+pad,cx-r//2-pad,cy+r-pad),outline=cream,width=4)
        rod((cx-r//3,cy),(cx+r//3,cy),gold,10)
        d.polygon([(cx+r//3,cy-27),(cx+r//3+50,cy),(cx+r//3,cy+27)],fill=gold)
        d.rounded_rectangle((cx+r//2,cy-r,cx+r*2,cy+r),14,outline=cream,width=7)
        for j in range(17):
            y=cy-r+38+j*int(r*.105)
            rod((cx+r//2+35,y),(cx+r*2-30,y),shade(gold,.5+j*.02),4)
        txt("3D SCAN",cx-r*2,cy+r+32,29,gold)
        txt("DIGITAL SURFACE",cx+r//2,cy+r+32,29,gold)
        return True
    if kind=="scanner":
        d.rounded_rectangle((cx-r*2,cy-r,cx+r*2,cy+r),22,fill=(47,63,72),outline=gold,width=5)
        d.ellipse((cx-r,cy-r//2,cx+r,cy+r),fill=(10,22,35),outline=cream,width=16)
        d.ellipse((cx-r//2,cy,cx+r//2,cy+r),outline=teal,width=10)
        for a in range(0,360,30):
            rad=math.radians(a)
            rod((cx,cy+r//4),(cx+math.cos(rad)*r*.85,cy+r//4+math.sin(rad)*r*.85),teal,3)
        txt("X-RAY TOMOGRAPHY",cx-r*2+40,cy-r-70,39,gold)
        return True
    if kind=="layers":
        for j in range(13):
            pad=j*13
            d.ellipse((cx-r*2+pad,cy-r+pad,cx+r*2-pad,cy+r-pad),outline=shade(gold,1-j*.055),width=5)
        txt("INNER PAPYRUS LAYERS",cx-r*2,cy+r+37,34,cream)
        return True
    if kind=="ink":
        d.rounded_rectangle((cx-r*2,cy-r,cx+r*2,cy+r),22,fill=(107,89,68),outline=gold,width=5)
        for j in range(12):
            yy=cy-r+40+j*int(r*.15)
            if yy>cy+r-45:break
            for k in range(14):
                xx=cx-r*2+70+k*45
                if xx>cx+r*2-70:break
                d.arc((xx,yy,xx+30,yy+24),0,200,fill=cream,width=3)
        txt("INK SIGNAL ≠ VERIFIED READING",cx-r*2,cy+r+30,30,gold)
        return True
    return False

def graphic(im,scene,palette,seed,vertical=False):
    """Original scene-specific explanatory illustration; each background composition unique."""
    w,h=im.size;d=ImageDraw.Draw(im);rng=random.Random(seed)
    gold=palette[2];light=(239,229,208);muted=(122,151,157)
    cx=int(w*(.49 if vertical else .67));cy=int(h*(.46 if vertical else .50))
    rr=int(min(w,h)*(.28 if vertical else .3))
    kind=scene.get("type","graphic")
    if narrative_illustration(im,scene,palette,seed,vertical):return
    label=scene.get("heading","").lower()
    if any(t in label for t in ["flood","wave","rupture","molasses","burst","thick"] ) or kind in ("wave","burst","aftermath","cleanup"):
        for i in range(6):
            y=cy+i*(rr//5);points=[(int(x),int(y+math.sin(x/110+i*.7)*rr*.11)) for x in range(cx-rr*2,cx+rr*2,25)]
            if len(points)>1:d.line(points,fill=(156+8*i,100+6*i,55+4*i),width=max(3,rr//17))
        d.polygon([(cx-rr,cy),(cx-rr,cy-rr//2),(cx,cy-rr),(cx+rr,cy-rr//2),(cx+rr,cy)],fill=(80,76,67))
    elif any(t in label for t in ["tank","steel","wall","leak","engineering","pressure","construction"]) or kind in ("tank","diagram","leak","blueprint"):
        box=(cx-rr,cy-rr,cx+rr,cy+rr)
        d.rectangle(box,fill=(57,72,75),outline=gold,width=7)
        d.ellipse((cx-rr,cy-rr-rr//6,cx+rr,cy-rr+rr//6),fill=(97,102,95),outline=gold,width=7)
        for j in range(5):
            y=cy-rr+j*rr//2
            d.line((cx-rr,y,cx+rr,y),fill=(154,136,103),width=4)
        for j in range(5):d.ellipse((cx-rr+20,cy-rr+45*j,cx-rr+31,cy-rr+45*j+11),fill=gold)
    elif any(t in label for t in ["court","trial","legal","sabotage","responsib"] ) or kind in ("court","trial"):
        d.polygon([(cx-rr,cy-rr//2),(cx,cy-rr),(cx+rr,cy-rr//2)],fill=gold)
        for k in range(5):
            x=cx-rr+k*rr//2
            d.rectangle((x,cy-rr//3,x+rr//4,cy+rr),fill=muted)
        d.rectangle((cx-rr-30,cy+rr,cx+rr+30,cy+rr+35),fill=gold)
    elif any(t in label for t in ["scroll","papyri","papyrus","layers","unwrap","words","column","writing","ink","text","book","philodemus","library","p h"] ) or kind in ("sealed","carbon","layers","unwrap","ink","pherc1667","pherc172","pherc139","columns","columns2","themes"):
        for j in range(5):
            off=j*rr//7
            d.rounded_rectangle((cx-rr+off,cy-rr+off//2,cx+rr-off,cy+rr-off//2),radius=25,outline=shade(gold,1-.07*j),width=8)
        for j in range(11):
            x=cx-rr//2+(j%4)*rr//3;y=cy-rr//2+(j//4)*rr//3
            d.line((x,y,x+rr//6,y-rr//9),fill=light,width=3)
        d.arc((cx-rr,cy-rr,cx+rr,cy+rr),0,290,fill=gold,width=12)
    elif any(t in label for t in ["x-ray","scanner","science","machine","software","algorithm","research","digital","imaging","surfaces","geometry","virtual"] ) or kind in ("scanner","challenge","esrf","evidence"):
        for j in range(11):
            ang=2*math.pi*j/11
            x=cx+int(math.cos(ang)*rr);y=cy+int(math.sin(ang)*rr)
            d.line((cx,cy,x,y),fill=(86,132,143),width=5);d.ellipse((x-8,y-8,x+8,y+8),fill=gold)
        d.ellipse((cx-rr//3,cy-rr//3,cx+rr//3,cy+rr//3),outline=light,width=7)
    elif any(t in label for t in ["vesuvius","eruption","roman","villa","herculaneum","volcano"]) or kind in ("vesuvius","villa"):
        d.polygon([(cx-rr*2,cy+rr),(cx-rr//3,cy-rr),(cx+rr//3,cy-rr),(cx+rr*2,cy+rr)],fill=(91,95,89),outline=gold)
        for j in range(15):
            x=cx+rng.randint(-rr,rr);y=cy-rr-rng.randint(rr//8,rr)
            d.ellipse((x-12,y-12,x+12,y+12),fill=shade(light,rng.uniform(.25,.75)))
    else:
        # A specific historical drawing for each subject, not a repeated star icon.
        topic=kind.removesuffix("_detail")
        if topic in ("street","city","map","art_city","aftermath","past","villa"):
            street=cy+rr//2
            d.line((cx-rr*2,street,cx+rr*2,street),fill=gold,width=5)
            for n in range(7):
                bw=rr//2
                x=cx-rr*2+n*int(rr*.62)
                height=int(rr*(.5+(seed+n*37)%80/70))
                d.polygon([(x,street),(x,street-height),(x+bw,street-height),(x+bw,street)],fill=(62+n*8,82+n*4,87+n*3),outline=(156,139,103))
                for yy in range(street-height+25,street-15,35):
                    for xx in range(x+20,x+bw-15,35):
                        d.rectangle((xx,yy,xx+9,yy+14),fill=(179,149,102))
            if topic=="map":
                for n in range(6):
                    y=cy-rr+n*rr//3
                    d.line((cx-rr*2,y,cx+rr*2,y+rr//8),fill=(208,187,143),width=6)
                for n in range(5):
                    x=cx-rr*2+n*rr
                    d.line((x,cy-rr*2,x+rr//4,cy+rr*2),fill=(100,153,171),width=4)
                d.ellipse((cx-18,cy-18,cx+18,cy+18),fill=(239,111,91))
        elif topic in ("rescue","victims","art_rescue"):
            # Human-scale rescue silhouettes and a bridge/ladder.
            for j in range(5):
                x=cx-rr+j*(rr//2);y=cy+rr//2+int(20*math.sin(j))
                d.ellipse((x-13,y-80,x+13,y-53),fill=light)
                d.line((x,y-50,x,y+15),fill=light,width=11)
                d.line((x,y-20,x-28,y+14),fill=light,width=7)
                d.line((x,y-20,x+28,y+3),fill=light,width=7)
                d.line((x,y+15,x-15,y+55),fill=light,width=8)
                d.line((x,y+15,x+17,y+53),fill=light,width=8)
            d.line((cx-rr*2,cy+rr//2,cx+rr*2,cy+rr//2-30),fill=gold,width=8)
            for j in range(11):
                x=cx-rr*2+j*rr//3
                d.line((x,cy+rr//2+8,x,cy+rr//2-44),fill=gold,width=3)
        elif topic in ("temperature",):
            d.rounded_rectangle((cx-rr//5,cy-rr,cx+rr//5,cy+rr),radius=rr//7,outline=light,width=12)
            d.ellipse((cx-rr//3,cy+rr//2,cx+rr//3,cy+rr),fill=(205,95,72))
            d.line((cx,cy-rr//3,cx,cy+rr//2),fill=(205,95,72),width=18)
            for i in range(7):
                y=cy-rr+i*rr//3
                d.line((cx+rr//5,y,cx+rr//3,y),fill=gold,width=5)
        elif topic in ("clock","timeline"):
            d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=gold,width=10)
            for j in range(12):
                a=2*math.pi*j/12
                d.line((cx+math.sin(a)*rr*.78,cy-math.cos(a)*rr*.78,
                        cx+math.sin(a)*rr*.9,cy-math.cos(a)*rr*.9),fill=light,width=5)
            d.line((cx,cy,cx+rr//4,cy-rr//2),fill=light,width=12)
            d.line((cx,cy,cx-rr//3,cy+rr//8),fill=gold,width=8)
            d.ellipse((cx-13,cy-13,cx+13,cy+13),fill=light)
        elif topic in ("engineering","mechanics","rivet","diagram","rail"):
            for n in range(6):
                x=cx-rr*2+n*rr*4//5
                d.line((x,cy-rr,x,cy+rr),fill=gold,width=8)
                for j in range(6):
                    y=cy-rr+j*rr*2//5
                    d.ellipse((x-10,y-10,x+10,y+10),fill=light)
            d.line((cx-rr*2,cy,cx+rr*2,cy-rr//2),fill=(194,120,100),width=15)
            d.arc((cx-rr,cy-rr,cx+rr,cy+rr),20,310,fill=light,width=6)
        elif topic in ("sealed","limits","future","archive","columns","news","evidence"):
            for j in range(8):
                x=cx-rr*2+j*rr//2
                h1=rr*(.4+((seed+j*19)%70)/90)
                d.rounded_rectangle((x,cy-h1,x+rr//3,cy+rr),radius=16,
                       fill=(77+j*5,77+j*3,62+j*2),outline=gold,width=3)
                for k in range(5):
                    yy=cy-h1+30+k*30
                    if yy<cy+rr-20:d.line((x+10,yy,x+rr//3-12,yy),fill=(191,172,127),width=3)
        elif topic in ("philosophy","ethics","closing"):
            for j in range(4):
                x=cx-rr*2+j*rr
                d.rectangle((x,cy-rr//2,x+rr//3,cy+rr),fill=(159,146,113),outline=light,width=3)
                for k in range(5):
                    d.line((x+k*rr//15,cy-rr//2,x+k*rr//15,cy+rr),fill=(114,113,105),width=2)
            d.polygon([(cx-rr*2-20,cy-rr//2),(cx,cy-rr*3//2),(cx+rr*2+20,cy-rr//2)],fill=gold)
            d.rectangle((cx-rr*2-30,cy+rr,cx+rr*2+30,cy+rr+35),fill=gold)
        else:
            # Unique, nonrepeating historical technical sketch for unforeseen subjects.
            rng=random.Random(seed)
            for i in range(15):
                x=cx-rr+rng.randrange(rr*2);y=cy-rr+rng.randrange(rr*2)
                size=rng.randrange(25,max(30,rr//2))
                d.rounded_rectangle((x,y,x+size,y+size*2//3),radius=8,outline=gold,width=3)
                d.line((x+8,y+size//4,x+size-8,y+size//4),fill=light,width=3)
                d.line((x+8,y+size//2,x+size-8,y+size//2),fill=light,width=3)
    # unique informational map of 4 dots, one chapter at a time
    for i in range(4):
        yy=int(h*.81)+i*17
        if yy<h-10:d.line((int(w*.54),yy,int(w*.83),yy),fill=shade(gold,.24+i*.10),width=2)

def plate(path,scene,episode,seed,image=None,vertical=False):
    """Vary compositions and label contextual archive objects accurately."""
    from PIL import ImageOps
    w,h=(1080,1920) if vertical else (1920,1080)
    im,palette=background((w,h),seed,episode)
    gold=palette[2];light=(242,238,226);muted=(174,199,206)
    style=seed%5
    heading=scene["heading"]
    if episode=="herculaneum" and any(x in heading.lower() for x in
        ["sixteen sixty-seven","one thirty-nine","one seventy-two","title found","different scroll"]):
        image=None
    photo_used=False
    if image:
        try:
            src=Image.open(image["file"]).convert("RGB")
            src=ImageEnhance.Contrast(ImageOps.autocontrast(src,cutoff=0.5)).enhance(1.04)
            if vertical:box=(50,250,w-50,1480)
            elif style%2:box=(130,160,w-130,930)
            else:box=(65,120,w-65,950)
            bw,bh=box[2]-box[0],box[3]-box[1]
            src.thumbnail((bw,bh),Image.Resampling.LANCZOS)
            d=ImageDraw.Draw(im)
            d.rounded_rectangle((box[0]-12,box[1]-12,box[2]+12,box[3]+12),16,
                               fill=(30,39,44),outline=gold,width=4)
            im.paste(src,(box[0]+(bw-src.width)//2,box[1]+(bh-src.height)//2))
            photo_used=True
        except Exception as e:print("IMAGE_CONTEXT_WARNING",str(e))
    if not photo_used:
        graphic(im,scene,palette,seed,vertical)
        d=ImageDraw.Draw(im)
        # Unique diagram detail tied to this script beat.
        for i in range(12):
            y=int(h*.14)+i*int(h*.045)
            x=int(w*.09)+((seed//(i+1))%int(w*.16))
            if y<int(h*.81):
                d.line((x,y,x+int(w*.10),y),fill=(108+i*4,94+i*3,73+i*2),width=2)
    layer=Image.new("RGBA",(w,h),(0,0,0,0))
    paint=ImageDraw.Draw(layer)
    if vertical:
        paint.rectangle((0,int(h*.67),w,h),fill=(5,15,25,225))
        x=int(w*.065);y=int(h*.71);fs=67;maxlen=24
    elif style in (0,2,4):
        paint.rectangle((0,int(h*.78),w,h),fill=(5,14,22,216))
        x=int(w*.065);y=int(h*.81);fs=54;maxlen=53
    else:
        paint.rounded_rectangle((int(w*.04),int(h*.075),int(w*.77),int(h*.26)),18,
                                fill=(5,14,22,230))
        x=int(w*.06);y=int(h*.10);fs=49;maxlen=44
    im=Image.alpha_composite(im.convert("RGBA"),layer).convert("RGB")
    d=ImageDraw.Draw(im)
    for i,line in enumerate(croptext(heading,maxlen)[:3]):
        d.text((x,y+i*(fs+8)),line,fill=light,font=fnt(fs,True))
    d.text((int(w*.04),int(h*.025)),"FACTS UNCOVERED   /   STORIES & EVIDENCE",
           fill=gold,font=fnt(24 if vertical else 26,True))
    if photo_used:
        label=("CONTEXT PHOTO — SCROLL ID IN IMAGE CREDITS"
               if episode=="herculaneum" else "AUTHENTIC ARCHIVE — IMAGE CREDITED")
    else:label="HISTORICAL RECONSTRUCTION — NOT ARCHIVAL FOOTAGE"
    d.text((int(w*.04),int(h*.953)),label,fill=muted,font=fnt(18 if vertical else 20))
    im.save(path,format="PNG",compress_level=3)
    return photo_used

def split_lines(text):
    bits=re.split(r'(?<=[.!?])\s+(?=[A-Z])',text.strip())
    if len(bits)<2:return [text.strip()]
    mid=len(bits)//2
    a=" ".join(bits[:mid]).strip();b=" ".join(bits[mid:]).strip()
    return [a,b] if min(len(a.split()),len(b.split()))>=8 else [text.strip()]

def sequence(ep,short,voice,assets,folder):
    ident=ep["id"];vertical=short is not None
    if vertical:
        title=short["title"];sentences=re.split(r'(?<=[.!?])\s+',short["narration"])
        beats=[{"id":short["id"]+"_"+str(i+1),"heading":title if i==0 else (s.split(",")[0][:46] if len(s)>30 else title),"narration":s,"type":short["type"]} for i,s in enumerate(sentences) if len(s.strip())>5]
    else:
        title=ep["title"];beats=[]
        for scene in ep["scenes"]:
            halves=split_lines(scene["narration"])
            for k,half in enumerate(halves):
                beats.append({**scene,"id":scene["id"]+("_A" if k==0 else "_B"),"narration":half,
                              "type":scene["type"] if k==0 else (scene["type"]+"_detail")})
    folder.mkdir(parents=True,exist_ok=True)
    clips=[];image_assignments=[];subtitle_lines=[];position=0.
    for index,beat in enumerate(beats):
        ident_hash=int(hashlib.sha256((ident+beat["id"]).encode()).hexdigest()[:8],16)
        photo=None
        if not vertical and assets and beat["id"].endswith("_A"):
            # An archive image must support this narration beat, not merely be
            # the next random item in a Commons search result.
            title=beat["heading"].lower()
            kind=beat["type"].removesuffix("_detail")
            # Build a trustworthy association between the spoken subject
            # and the particular archival artifact, not just the general topic.
            if ident=="molasses":
                if "newspaper" in title:
                    preferred=("dailyglobe","globe","frontpage","post-january")
                elif any(w in title for w in ("damage","aftermath","wreckage","scale","loss","true")):
                    preferred=("elevated railway after","train structure","wreckage under","molasses disaster")
                elif "city reckons" in title or "remember" in title:
                    preferred=("molasses disaster","molassesdisaster")
                elif "railway" in title:
                    preferred=("elevated railway after","el train structure")
                else:preferred=()
                def valid(a):
                    t=a["title"].lower()
                    if any(v in t for v in ("superimposed","daily globe","frontpage","globe")) and "newspaper" not in title:
                        return False
                    return "molasses" in t or "boston post-january" in t
            else:
                # Commons context images show historical artifacts and 18th-
                # 19th-century facsimiles; none must be passed off as PHerc.
                # 1667, 172 or 139 unless its exact identity is verified.
                if kind=="past":
                    preferred=("piaggio","apparatus used to unroll")
                elif kind in ("carbon","sealed"):
                    preferred=("herculanean rolls","papyrus 157","herculaneum papyrus")
                elif kind=="villa":
                    preferred=("villa of the papyri","villa dei papiri")
                elif kind=="archive":
                    preferred=("tesoro letterario","papyri")
                else:preferred=()
                def valid(a):
                    t=a["title"].lower()
                    return any(z in t for z in ("papy","hercul","ercolano","piaggio","villa"))
            if preferred:
                used=set(image_assignments)
                available=[a for a in assets if a["sha256"] not in used and valid(a)]
                # Exact object/scene relevance wins. If no match, illustrate
                # rather than imply a random artifact is the one narrated.
                scored=sorted(((next((len(preferred)-j for j,s in enumerate(preferred) if s in a["title"].lower()),0),a)
                    for a in available),key=lambda x:x[0],reverse=True)
                if scored and scored[0][0]>0:
                    photo=scored[0][1]
                    image_assignments.append(photo["sha256"])
        platefile=folder/f"plate_{index+1:03}.png"
        narration_file=folder/f"narration_{index+1:03}.wav"
        clip=folder/f"shot_{index+1:03}.mp4"
        if not platefile.exists():plate(platefile,beat,ident,ident_hash,photo,vertical)
        d=narrate(voice,beat["narration"],narration_file) if not narration_file.exists() else seconds(narration_file)
        # Natural audio drives exact shot duration; no image is held longer than its spoken beat.
        # Slow directional zoom adds visual movement without making fake "archival footage."
        pan=["0.48","0.54","0.45","0.5"][index%4]
        if vertical: panzoom="zoompan=z='min(zoom+0.00015,1.065)':d=1:x='(iw-iw/zoom)*0.5':y='(ih-ih/zoom)*0.48':s=1080x1920:fps=24,format=yuv420p"
        else:panzoom="zoompan=z='min(zoom+0.00015,1.065)':d=1:x='(iw-iw/zoom)*"+pan+"':y='(ih-ih/zoom)*0.5':s=1920x1080:fps=24,format=yuv420p"
        if not clip.exists():
            run("ffmpeg","-y","-hide_banner","-loglevel","error","-loop","1","-framerate","24","-i",platefile,
                "-i",narration_file,"-vf",panzoom,"-t",f"{d:.4f}","-r","24",
                "-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",
                "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
                "-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-movflags","+faststart",clip)
        clips.append(clip)
        subtitle_lines.append({"start":round(position,3),"end":round(position+d,3),"text":beat["narration"]})
        position+=d
        print("SHOT",ident,short["id"] if short else "main",index+1,len(beats),"DURATION",round(d,2),"ARCHIVE",bool(photo),flush=True)
    checks=[hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob("plate_*.png"))]
    if len(checks)!=len(set(checks)):raise RuntimeError("Duplicate plate image in final movie; release blocked")
    if len(image_assignments)!=len(set(image_assignments)):raise RuntimeError("Archival photo reused; release blocked")
    # Construct one continuous PCM narration track. Joining separately AAC-encoded
    # shot audio introduces padding and possible subtitle drift at every cut.
    continuous=folder/"continuous_voice.wav"
    with wave.open(str(continuous),"wb") as dst:
        expected_params=None
        for i in range(len(beats)):
            source=folder/f"narration_{i+1:03}.wav"
            with wave.open(str(source),"rb") as src:
                params=(src.getnchannels(),src.getsampwidth(),src.getframerate(),src.getcomptype())
                if expected_params is None:
                    expected_params=params
                    dst.setnchannels(params[0]);dst.setsampwidth(params[1]);dst.setframerate(params[2])
                elif params!=expected_params:
                    raise RuntimeError(f"Mismatch in narrator PCM format for {source}")
                while True:
                    chunk=src.readframes(65536)
                    if not chunk:break
                    dst.writeframesraw(chunk)
    concatfile=folder/"concat.txt"
    concatfile.write_text("".join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in clips))
    joined=folder/"joined.mp4"
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",concatfile,"-c","copy",joined)
    final=folder.parent/((ident+"_"+short["id"]+"_SHORT_1080x1920.mp4") if vertical else ident+"_DOCUMENTARY_REMASTER_1080p.mp4")
    # Re-encode the final frame sequence to strict CFR 24 (concatenation with
    # stream-copy can otherwise report a spurious 48fps for short outputs).
    # The one-piece WAV, rather than per-shot AAC tracks, is the final sound.
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",joined,"-i",continuous,
        "-map","0:v:0","-map","1:a:0","-vf","fps=24,format=yuv420p",
        "-filter:a","highpass=f=75,acompressor=threshold=0.13:ratio=1.8:attack=15:release=220,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v","libx264","-preset","medium","-crf","17","-r","24",
        "-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709",
        "-colorspace","bt709","-fps_mode","cfr",
        "-c:a","aac","-b:a","224k","-ar","48000","-ac","2",
        "-shortest","-movflags","+faststart",final)
    def srttime(n):
        ms=int(round(n*1000));h,rem=divmod(ms,3600000);m,rem=divmod(rem,60000);s,ms=divmod(rem,1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    (folder.parent/(final.stem+".srt")).write_text("".join(f"{i}\n{srttime(x['start'])} --> {srttime(x['end'])}\n{x['text']}\n\n" for i,x in enumerate(subtitle_lines,1)),encoding="utf8")
    meta=ffprobe(final);v=next((x for x in meta["streams"] if x["codec_type"]=="video"),None);a=next((x for x in meta["streams"] if x["codec_type"]=="audio"),None)
    expected=(1080,1920) if vertical else (1920,1080)
    if not v or not a or (v["width"],v["height"])!=expected or seconds(final)<12:raise RuntimeError("Invalid final master export")
    if float(a.get("sample_rate",0))!=48000:raise RuntimeError("Audio must be 48kHz")
    if v.get("r_frame_rate")!="24/1" or v.get("avg_frame_rate")!="24/1":
        raise RuntimeError("Final video frame-rate must be constant 24fps")
    if abs(seconds(final)-position)>0.85:
        raise RuntimeError(f"Final AV timeline differs from narration by {seconds(final)-position:.3f} seconds")

    report={"episode":ident,"short":short["id"] if short else None,"file":str(final),"sha256":hashlib.sha256(final.read_bytes()).hexdigest(),
      "duration":seconds(final),"video_size":[v["width"],v["height"]],"frame_rate":v.get("r_frame_rate"),"audio_sample_rate":a.get("sample_rate"),
      "total_bitrate":meta["format"].get("bit_rate"),"shots":len(beats),"distinct_image_hashes":len(checks),
      "unique_archival_images_used":len(image_assignments),"human_review_completed":False,
      "publication_approved":False,"editorial_status":"RENDERED_UNREVIEWED_NOT_APPROVED",
      "review_required":["watch all shots with headphones","verify every spoken claim and visual relevance","check all captions against spoken words","review all crop and colour choices","approve music and image credits"]}
    (folder.parent/(final.stem+".qa.json")).write_text(json.dumps(report,indent=2))
    print("FINAL_RENDERED_NOT_APPROVED",final,"DURATION",round(seconds(final),2),"UNIQUE_SHOTS",len(checks),flush=True)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--episode",choices=("molasses","herculaneum","all"),default="all")
    p.add_argument("--only",choices=("main","shorts","all"),default="all")
    args=p.parse_args()
    voice=voice_engine()
    results=[]
    for key in ([args.episode] if args.episode!="all" else ["molasses","herculaneum"]):
        ep=DOC["episodes"][key];ep_root=OUT/key;ep_root.mkdir(exist_ok=True)
        # For a non-repeating film, each archive file is assigned at most once.
        assets=get_wikimedia_assets(key) if args.only in ("main","all") else []
        (ep_root/"RESEARCH_SOURCES.json").write_text(json.dumps(ep["sources"],indent=2))
        if args.only in ("main","all"):results.append(sequence(ep,None,voice,assets,ep_root/"main_shots"))
        if args.only in ("shorts","all"):
            for short in ep["shorts"]:results.append(sequence(ep,short,voice,[],ep_root/(short["id"]+"_shots")))
    (OUT/"RENDER_MANIFEST.json").write_text(json.dumps(results,indent=2))
    print("REMASTERS_RENDERED",len(results),"Masters. Editorial release approval still REQUIRED.",flush=True)

if __name__=="__main__":main()
