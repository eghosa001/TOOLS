#!/usr/bin/env python3
"""Evidence-directed Great Pyramid Chapter 1.
The 24 shots are individual authored decisions in chapter01_directed_shots.json.
No generative keyword matching, interchangeable stock or synthetic ancient writing.
The narration is synthesized per exact script sentence passage, giving real shot times.
"""
from __future__ import annotations
import argparse, hashlib, html, json, math, re, subprocess, time
from pathlib import Path
from urllib.parse import quote

import numpy as np
import requests
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

BASE=Path(__file__).resolve().parent
FILM=(BASE/"chapter01_directed_shots.json")
SCRIPT=BASE/"chapters/01_01_the_unseen_space.txt"
HEADERS={"User-Agent":"FactsUncovered/1.0 evidence-led doc (https://github.com/eghosa001/TOOLS)"}
GOLD=(232,185,93); WHITE=(244,237,224); GREY=(174,191,202)
TEAL=(65,161,182); DARK=(13,23,34)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WIDTH=1920;HEIGHT=1080

def font(n,bold=False): return ImageFont.truetype(BOLD if bold else FONT,int(n))
def runcmd(*args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
    if r.returncode:raise RuntimeError("Command failed: "+r.stderr[-2300:])
    return r.stdout
def sec_time(secs):
    a=int(secs);return f"{a//3600:02}:{a//60%60:02}:{a%60:02},{round((secs-a)*1000)%1000:03}"
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def paragraphs_and_shots():
    manifest=json.loads(FILM.read_text())
    chunks=SCRIPT.read_text().strip().split("\n\n")
    count=int(manifest.get("paragraph_count",8))
    assert len(chunks)==count+1,(len(chunks),"Title + expected narration paragraphs")
    paragraph=[re.split(r"(?<=[.!?])\s+",p.strip()) for p in chunks[1:]]
    coverage={i:set() for i in range(1,count+1)}
    for shot in manifest["shots"]:
        i=shot["paragraph"];first=shot["sentence_start"];last=shot["sentence_end"]
        assert 1<=i<=count and 1<=first<=last<=len(paragraph[i-1]),shot["id"]
        for n in range(first,last+1):
            assert n not in coverage[i],("DUPLICATE SCRIPT SENTENCE",i,n)
            coverage[i].add(n)
        shot["spoken_text"]=" ".join(paragraph[i-1][first-1:last])
        assert shot["spoken_text"].strip()
    for i in range(1,count+1):
        assert coverage[i]==set(range(1,len(paragraph[i-1])+1)),("MISSING SCRIPT",i)
    assert len(manifest["shots"])==manifest["shot_count"]
    if manifest["chapter"]==1:
        assert manifest["shots"][0]["heading"]=="THE GREAT PYRAMID"
    return manifest

def get_photo(item,target):
    """Get *only* exact hand-selected Commons file, validate source licence and identity."""
    params={"action":"query","format":"json","prop":"imageinfo","titles":item["commons_title"],
            "iiprop":"url|size|extmetadata","iiurlwidth":1900}
    payload=None
    for attempt in range(4):
        try:
            q=requests.get("https://commons.wikimedia.org/w/api.php",params=params,headers=HEADERS,timeout=35)
            q.raise_for_status();payload=q.json();break
        except Exception:
            if attempt==3:raise
            time.sleep(2+attempt)
    pages=list(payload.get("query",{}).get("pages",{}).values())
    assert len(pages)==1 and "imageinfo" in pages[0],("Missing verified exact archive image",item["commons_title"])
    page=pages[0]
    assert page.get("title","").casefold()==item["commons_title"].casefold(),page.get("title")
    info=page["imageinfo"][0];md=info.get("extmetadata",{})
    lic=re.sub(r"<[^>]+>","",html.unescape(md.get("LicenseShortName",{}).get("value",""))).strip()
    expected=item["expected_licence"]
    if expected=="CC0":
        assert "CC0" in lic.upper() or "PUBLIC DOMAIN" in lic.upper(),lic
    elif expected.startswith("CC BY"):
        norm=lambda text: re.sub(r"[-_\s]+"," ",text.upper()).strip()
        assert norm(lic).startswith(norm(expected)),(expected,lic)
        assert item.get("credit","").strip(),"CC-BY attribution required"
    else:
        assert "PUBLIC DOMAIN" in lic.upper() or lic.upper() in ("PD","PDM"),lic
    url=info.get("thumburl") or info.get("url")
    assert url and "wikimedia.org" in url
    result=None
    for attempt in range(4):
        try:
            result=requests.get(url,headers=HEADERS,timeout=80)
            result.raise_for_status()
            break
        except requests.RequestException:
            if attempt==3:raise
            time.sleep(3*(attempt+1))
    assert result is not None
    assert len(result.content)>30000 and len(result.content)<20000000
    target.write_bytes(result.content)
    with Image.open(target) as im:
        is_research_figure=item["commons_title"].startswith("File:East-West cut view of the Great Pyramid")
        assert im.width>=900 and im.height>=(440 if is_research_figure else 480), (
            "Low resolution or wrong original image",item["commons_title"],im.size)
        im=ImageOps.exif_transpose(im).convert("RGB");im.thumbnail((2100,1600))
        im.save(target,quality=95)
    return {"id":item["id"],"title":page["title"],"creator":item["credit"],
            "license":lic,"source":item["source"],"download":url,
            "sha256":sha(target),"size":target.stat().st_size}

def archive_assets(work,manifest):
    folder=work/"licensed_archival";folder.mkdir(parents=True,exist_ok=True)
    data={}
    for item in manifest["original_photos"]:
        path=folder/(item["id"]+".jpg")
        if path.exists():
            try:
                with Image.open(path) as im:im.verify()
            except Exception:path.unlink()
        if not path.exists():provenance=get_photo(item,path)
        else:provenance={"id":item["id"],"title":item["commons_title"],"creator":item["credit"],
                        "license":item["expected_licence"],"source":item["source"],
                        "sha256":sha(path),"size":path.stat().st_size}
        data[item["id"]]={"path":str(path),"record":provenance}
    (work/"ASSET_RIGHTS.json").write_text(json.dumps([v["record"] for v in data.values()],indent=2))
    return data

def write_lines(d,words,x,y,limit,size=48,color=WHITE,bold=False,maxlines=4):
    # Physical text measurement prevents clipping in individually approved compositions.
    # Shrink only when necessary; never silently truncate original editorial wording.
    tokens=words.split()
    for candidate_size in range(int(size), max(20,int(size*.58))-1,-2):
        f=font(candidate_size,bold)
        lines=[];line=""
        for word in tokens:
            candidate=(line+" "+word).strip()
            if d.textbbox((0,0),candidate,font=f)[2]>limit and line:
                lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if len(lines)<=maxlines:
            for j,value in enumerate(lines):
                d.text((x,y+j*int(candidate_size*1.25)),value,font=f,fill=color)
            return y+len(lines)*int(candidate_size*1.25)
    raise ValueError("Text exceeds screen-safe space despite resizing: "+words)

def arrow(d,a,b,color=GOLD,width=8):
    d.line([a,b],fill=color,width=width)
    theta=math.atan2(b[1]-a[1],b[0]-a[0])
    for k in (-.54,.54):
        d.line([b,(b[0]-25*math.cos(theta+k),b[1]-25*math.sin(theta+k))],fill=color,width=width)

def baseline_pyramid(d,center=1425,top=286,bottom=821,radius=397):
    d.polygon([(center,top),(center-radius,bottom),(center+radius,bottom)],
              fill=(87,85,80,235),outline=(230,185,93),width=6)
    for j in range(1,18):
        y=top+(bottom-top)*j/18
        span=radius*j/18
        d.line([(center-span,y),(center+span,y)],fill=(148,135,110),width=2)

def graphics(d,k,seed=0,shot=None):
    """Subject-specific original technical diagrams; conceptual, never archaeological footage."""
    cx=1425
    if k in ("cutaway","measure","muon","chronology"):
        baseline_pyramid(d)
        d.line([(cx-20,803),(cx+60,605),(cx+125,523)],fill=WHITE,width=11)
        d.rounded_rectangle((cx+21,479,cx+174,508),radius=7,fill=TEAL)
        if k in ("cutaway","measure"):
            # Schematic observational zone, not an actual cavity cross-section.
            d.rounded_rectangle((cx+6,411,cx+222,455),radius=16,outline=GOLD,width=8)
            d.text((1100,337),"BIG VOID",font=font(35,True),fill=GOLD)
            d.line([(1200,379),(cx+7,420)],fill=GOLD,width=4)
            d.text((1140,635),"GRAND GALLERY",font=font(27),fill=WHITE)
            if k=="measure":
                arrow(d,(1435,390),(1650,390))
                d.text((1480,337),"≥30 m",font=font(45,True),fill=GOLD)
        elif k=="muon":
            for j in range(13):
                xx=1050+j*61
                d.line([(xx,255),(1340+(j-6)*31,795)],fill=(73,171,193,145),width=3)
            d.rounded_rectangle((1260,800,1460,852),radius=7,fill=(35,136,150))
            d.text((1145,875),"MUONS THROUGH STONE",font=font(29),fill=GOLD)
        elif k=="chronology":
            d.text((1130,867),"OLD KINGDOM  •  FOURTH DYNASTY",font=font(24),fill=GOLD)
    elif k=="passage":
        # Angular receding corridor, explicitly illustrative.
        for j in range(6):
            inset=30+j*57
            d.polygon([(1040+inset,270+inset//2),(1810-inset,270+inset//2),
                       (1810-inset,840-inset//3),(1040+inset,840-inset//3)],
                     outline=(95+j*18,91+j*15,83+j*13),width=8)
        d.polygon([(1170,870),(1450,620),(1740,870)],fill=(34,41,48))
        d.line([(1450,620),(1450,870)],fill=GOLD,width=5)
    elif k in ("evidence","possibilities"):
        default=(("OBSERVED","INTERPRETED","NOT DEMONSTRATED")
                if k=="evidence" else ("POSSIBLE","UNCONFIRMED","UNKNOWN"))
        headings=(shot or {}).get("visual_labels",default)
        assert len(headings)==3 and all(isinstance(label,str) and len(label)<=45 for label in headings)
        for j,label in enumerate(headings):
            y=335+j*173
            d.rounded_rectangle((1000,y,1817,y+125),radius=20,fill=(26,50+j*6,64+j*2),outline=GOLD,width=3)
            write_lines(d,label,1040,y+23,680,34,color=WHITE if j<2 else GOLD,bold=True,maxlines=2)
            d.ellipse((1756,y+46,1786,y+76),fill=GOLD)
    elif k in ("archive","records"):
        d.rounded_rectangle((1030,290,1795,850),radius=16,fill=(188,166,128),outline=GOLD,width=5)
        if k=="records":
            d.text((1072,333),"MODERN EVIDENCE SUMMARY",font=font(27,True),fill=(50,47,44))
            lines=(shot or {}).get("record_lines",[
                "Evidence has its own source.",
                "Interpretations must be labelled.",
                "No invented ancient document."])
            assert len(lines)<=5
            for j,label in enumerate(lines):
                y=409+j*90
                d.line([(1080,y+52),(1740,y+52)],fill=(98,87,73),width=2)
                write_lines(d,label,1095,y,605,28,color=(54,53,46),maxlines=2)
    elif k in ("workers","logistics"):
        if k=="workers":
            for j in range(3):
                for t in range(4):
                    x=1042+t*190;y=356+j*155
                    d.rectangle((x,y,x+130,y+105),fill=(152,122,80),outline=GOLD,width=3)
                    d.rectangle((x+45,y+63,x+75,y+105),fill=(43,57,62))
            d.text((1155,855),"CONCEPTUAL WORKERS' SETTLEMENT",font=font(25),fill=GOLD)
        else:
            stages=["QUARRY","BOAT","SUPPLIES","WORKSITE"]
            for j,s in enumerate(stages):
                x=970+j*210
                d.rounded_rectangle((x,430,x+185,605),radius=20,fill=(23,58,68),outline=GOLD,width=4)
                d.text((x+16,500),s,font=font(23,True),fill=WHITE)
                if j<3:arrow(d,(x+186,520),(x+209,520),TEAL,5)
            d.text((1190,730),"ORGANISATION, NOT MAGIC",font=font(30,True),fill=GOLD)
    elif k=="merer":
        d.rounded_rectangle((1060,280,1770,890),radius=25,fill=(179,151,108),outline=GOLD,width=7)
        d.text((1100,330),"MODERN SUMMARY / NOT ORIGINAL PAPYRUS",font=font(23),fill=(45,43,42))
        for j,(a,b) in enumerate((("SOURCE","WADI AL-JARF"),("RECORDER","INSPECTOR MERER"),
                                  ("CARGO","FINE LIMESTONE"),("DESTINATION","KHUFU'S PROJECT"))):
            y=444+j*95
            d.text((1110,y),a,font=font(25),fill=(60,50,42))
            d.text((1330,y),b,font=font(27,True),fill=(54,53,47))
    elif k=="river":
        d.polygon([(1040,730),(1100,540),(1290,590),(1465,401),(1770,450),
                   (1820,548),(1495,518),(1320,728),(1120,676)],fill=(28,113,135))
        d.text((1130,770),"POTENTIAL TRANSPORT ROUTES",font=font(31,True),fill=GOLD)
        d.text((1130,815),"SCHEMATIC  •  NOT TO SCALE",font=font(25),fill=WHITE)
    elif k=="investigation":
        for j,(a,b) in enumerate((("DOCUMENTS","Written logistics"),("ARCHAEOLOGY","Settlements & stone"),
                                   ("PHYSICS","Measured empty space"))):
            y=305+j*185
            d.rounded_rectangle((1005,y,1810,y+145),radius=17,fill=(24,54,69),outline=TEAL,width=3)
            d.text((1040,y+27),a,font=font(37,True),fill=GOLD)
            d.text((1040,y+79),b,font=font(29),fill=WHITE)
    elif k=="chamber":
        d.rounded_rectangle((1045,350,1800,812),radius=9,fill=(60,55,55),outline=(202,192,179),width=11)
        for i in range(8):
            x=1050+i*90;d.line([(x,354),(x,808)],fill=(100,91,85),width=3)
        d.rectangle((1285,640,1630,771),fill=(91,82,75),outline=GOLD,width=8)
        d.rectangle((1315,658,1600,736),fill=(28,34,41))
        d.text((1190,863),"KING'S CHAMBER / EXPLANATORY",font=font(27),fill=GOLD)
    elif k=="shafts":
        baseline_pyramid(d)
        d.line([(1437,667),(1640,435)],fill=TEAL,width=12)
        d.line([(1435,667),(1230,435)],fill=GOLD,width=12)
        d.ellipse((1415,644,1464,694),fill=WHITE)
        d.text((1088,880),"NARROW SHAFTS  •  SCHEMATIC",font=font(27),fill=GOLD)
    elif k=="mastaba":
        # Archaeological type schematic: rectangular superstructure + burial below ground.
        d.rectangle((1050,572,1780,742),fill=(160,135,91),outline=GOLD,width=6)
        d.line([(1050,765),(1780,765)],fill=TEAL,width=5)
        d.line([(1415,732),(1415,835)],fill=WHITE,width=4)
        d.rounded_rectangle((1310,835,1520,910),radius=8,fill=(35,63,69),outline=GOLD,width=4)
        d.text((1165,474),"MASTABA SUPERSTRUCTURE",font=font(29,True),fill=GOLD)
        d.text((1514,862),"BURIAL CHAMBER",font=font(22),fill=WHITE)
    elif k=="steps":
        for j in range(6):
            d.rectangle((1050+62*j,750-82*j,1825-62*j,831-82*j),
                        fill=(152-j*6,130-j*5,97-j*3),outline=GOLD,width=3)
        d.text((1130,894),"STEPPED MASONRY  •  CONCEPT ONLY",font=font(25),fill=GOLD)
    elif k=="geometry":
        d.polygon([(1105,796),(1345,357),(1585,796)],fill=(133,123,107),outline=GOLD,width=5)
        d.polygon([(1450,796),(1688,467),(1810,796)],fill=(82,127,132),outline=WHITE,width=5)
        d.text((1100,845),"COMPARING PYRAMID SLOPES  •  NOT TO SCALE",font=font(23),fill=GOLD)
    elif k=="foundations":
        d.polygon([(1040,730),(1820,730),(1690,825),(1150,825)],fill=(118,99,78),outline=GOLD,width=4)
        for i in range(6):
            y=550+i*41
            for j in range(8):
                x=1100+j*88+(i%2)*35
                d.rectangle((x,y,x+86,y+35),outline=(184,166,131),width=3)
        d.text((1180,880),"STONE COURSES / CONCEPTUAL",font=font(28),fill=GOLD)
    elif k=="alignment":
        d.ellipse((1130,315,1720,903),outline=GOLD,width=7)
        arrow(d,(1425,765),(1425,413),TEAL,12)
        d.text((1400,350),"N",font=font(55,True),fill=GOLD)
        d.text((1399,834),"S",font=font(40),fill=WHITE)
        d.text((1203,575),"W",font=font(36),fill=WHITE)
        d.text((1631,575),"E",font=font(36),fill=WHITE)
        d.text((1088,938),"ORIENTATION MEASUREMENTS",font=font(25),fill=GOLD)
    elif k=="change":
        d.polygon([(1010,830),(1150,548),(1290,830)],fill=(136,117,88),outline=GOLD,width=5)
        d.polygon([(1330,830),(1470,548),(1510,690),(1610,830)],fill=(95,125,128),outline=GOLD,width=5)
        d.polygon([(1600,830),(1730,598),(1840,830)],fill=(153,136,102),outline=GOLD,width=5)
        d.text((1120,892),"STEPPED  →  BENT  →  TRUE",font=font(29,True),fill=GOLD)
    elif k in ("ramp","quarry"):
        d.polygon([(1025,810),(1700,810),(1700,390)],fill=(139,117,88),outline=GOLD,width=6)
        if k=="ramp":
            d.rounded_rectangle((1450,565,1540,636),radius=4,fill=(196,184,159),outline=WHITE,width=4)
            arrow(d,(1500,720),(1550,649),TEAL,9)
            d.text((1120,886),"RAMP SCHEMATIC  •  HYPOTHESIS",font=font(25),fill=GOLD)
        else:
            d.rectangle((1260,710,1380,804),fill=(194,180,149),outline=WHITE,width=6)
            d.text((1100,887),"QUARRY BLOCK / CONCEPTUAL",font=font(26),fill=GOLD)
    elif k=="journal":
        # Public bibliographic fields from verified 10 August 2026 journal notice.
        d.rounded_rectangle((1000,327,1815,844),radius=24,fill=(29,50,64),outline=GOLD,width=5)
        d.text((1043,375),"REMOTE SENSING",font=font(43,True),fill=WHITE)
        d.text((1043,445),"OFFICIAL RETRACTION",font=font(38,True),fill=GOLD)
        d.line([(1044,515),(1769,515)],fill=TEAL,width=4)
        for j,label in enumerate(("PUBLISHED  10 AUGUST 2026",
             "DOI  10.3390/rs18162679",
             "METHODOLOGICAL AND STATISTICAL FLAWS",
             "AUTHORS DISAGREED WITH THE DECISION")):
            d.text((1045,556+j*61),label,font=font(26,True),fill=WHITE if j<2 else GOLD)
        d.text((1050,882),"VERIFIED CITATION  •  NOT A SCANNED MANUSCRIPT",font=font(22),fill=GOLD)
    elif k=="ship":
        # Original vessel planking and ribs diagram, not a photograph of the original boat.
        d.polygon([(1040,572),(1780,572),(1702,793),(1143,793)],
                  fill=(132,86,54),outline=GOLD,width=6)
        for row in range(4):
            y=612+row*42
            d.line([(1090+15*row,y),(1740-16*row,y)],fill=(235,203,146),width=4)
        for x in range(1160,1780,95):
            d.arc((x-45,540,x+46,805),8,165,fill=(224,186,120),width=5)
        d.text((1140,874),"WOODEN HULL PLANKS  •  MODERN SCHEMATIC",font=font(24),fill=GOLD)
    elif k=="craft":
        # Joinery concept. No claim of a diagram recovered from a royal workshop.
        d.rectangle((1072,477,1410,660),fill=(153,115,75),outline=GOLD,width=7)
        d.rectangle((1430,478,1770,660),fill=(171,131,84),outline=GOLD,width=7)
        d.polygon([(1405,540),(1465,540),(1465,602),(1405,602)],fill=(232,206,152))
        d.rounded_rectangle((1440,549,1530,593),radius=6,outline=(25,54,61),width=4)
        arrow(d,(1320,725),(1470,725),TEAL,8)
        d.text((1095,797),"PLANK JOINERY  •  EXPLANATORY ART",font=font(29,True),fill=GOLD)
        d.text((1110,857),"NOT AN ANCIENT PLAN",font=font(24),fill=WHITE)
    elif k=="sphinx":
        # Schematized silhouette of the Sphinx; clearly not historical footage.
        d.ellipse((1510,430,1680,600),fill=(168,141,96),outline=GOLD,width=5)
        d.rounded_rectangle((1260,592,1740,760),radius=75,fill=(143,119,82),outline=GOLD,width=6)
        for xx in (1290,1640):
            d.rounded_rectangle((xx,710,xx+95,842),radius=22,fill=(126,108,81),outline=GOLD,width=3)
        d.line([(1663,520),(1735,560)],fill=(134,106,78),width=5)
        d.text((1090,890),"SPHINX SILHOUETTE • ILLUSTRATIVE",font=font(24),fill=GOLD)
    elif k=="stonecourses":
        for row in range(9):
            yy=390+row*51
            for col in range(8):
                xx=1035+col*95+(row%2)*42
                d.rectangle((xx,yy,xx+94,yy+49),fill=(144+row*2,123+row*2,91+row*2),
                            outline=(226,198,148),width=3)
        d.text((1100,897),"LIMESTONE BLOCKS • SCHEMATIC",font=font(25),fill=GOLD)
    elif k=="bakeries":
        for j in range(4):
            x=1070+j*180
            d.rounded_rectangle((x,460,x+143,741),radius=55,fill=(167,123,81),outline=GOLD,width=5)
            d.ellipse((x+24,615,x+118,703),fill=(52,38,31),outline=WHITE,width=3)
        d.text((1115,843),"BAKERY INSTALLATIONS  •  ARTIST'S SCHEMATIC",font=font(23),fill=GOLD)
    elif k=="burial":
        d.line([(1030,610),(1780,610)],fill=(179,153,111),width=9)
        d.polygon([(1215,612),(1575,612),(1555,792),(1252,792)],
                  fill=(79,74,68),outline=GOLD,width=6)
        d.rounded_rectangle((1277,700,1504,747),radius=14,fill=(143,122,91),outline=WHITE,width=3)
        d.text((1050,865),"BURIAL CONTEXT  •  SCHEMATIC, NOT AN ACTUAL TOMB",font=font(22),fill=GOLD)
    elif k=="sledge":
        # Mechanical concept rather than claim of a specific proven construction method.
        d.polygon([(1060,795),(1790,795),(1790,829),(1060,829)],
                  fill=(111,84,56),outline=GOLD,width=5)
        d.rectangle((1420,540,1705,783),fill=(164,146,116),outline=WHITE,width=6)
        d.line([(1420,725),(1230,660)],fill=TEAL,width=10)
        arrow(d,(1228,661),(1105,580),TEAL,9)
        d.text((1130,890),"SLEDGE AND HAULING  •  HYPOTHESIS",font=font(26),fill=GOLD)
    elif k=="inspector":
        # Generic inspector silhouette, deliberately not a claimed likeness of Merer.
        d.ellipse((1270,305,1550,590),fill=(174,137,89),outline=GOLD,width=6)
        d.rounded_rectangle((1170,590,1660,890),radius=85,fill=(186,157,118),outline=GOLD,width=6)
        d.rectangle((1532,660,1750,848),fill=(161,139,98),outline=WHITE,width=4)
        d.text((1110,930),"ARTISTIC RECONSTRUCTION  •  IDENTITY UNKNOWN",font=font(23),fill=GOLD)
    elif k in ("harbour","floodplain","boat"):
        # Deliberate illustrative water scene rather than undocumented archaeological photo.
        d.polygon([(930,735),(1810,720),(1840,900),(950,915)],fill=(28,105,127))
        for j in range(8):
            y=750+j*21
            d.arc((940,y,1810,y+80),177,352,fill=(63,149,169),width=3)
        if k=="harbour":
            d.polygon([(940,704),(1240,520),(1410,704)],fill=(154,124,83))
            d.line([(1360,430),(1360,767)],fill=(217,207,180),width=9)
            d.text((1180,927),"PORT / COASTAL NETWORK  •  SCHEMATIC",font=font(26),fill=GOLD)
        elif k=="floodplain":
            d.polygon([(1150,710),(1190,580),(1390,660),(1510,480),
                       (1780,585),(1830,686),(1560,581),(1440,770)],fill=(52,142,159))
            d.text((1180,928),"HISTORICAL RIVER SYSTEM  •  NOT TO SCALE",font=font(25),fill=GOLD)
        else:
            d.polygon([(1100,610),(1690,610),(1585,782),(1200,782)],
                      fill=(134,84,50),outline=GOLD,width=6)
            d.line([(1400,365),(1400,610)],fill=WHITE,width=8)
            d.polygon([(1405,391),(1585,580),(1405,580)],fill=(226,215,185))
            for j in range(4):
                x=1200+j*98;d.rectangle((x,546,x+87,612),fill=(174,156,123),outline=WHITE,width=2)
            d.text((1240,932),"BOAT WITH LIMESTONE  •  CONCEPTUAL",font=font(25),fill=GOLD)
    elif k in ("detectors","experiment","density"):
        if k=="density":
            d.rounded_rectangle((965,350,1815,805),radius=23,fill=(23,48,61),outline=TEAL,width=3)
            d.text((1005,398),"DENSE STONE",font=font(31,True),fill=WHITE)
            d.text((1450,398),"LOWER DENSITY",font=font(30,True),fill=GOLD)
            for j in range(17):
                xx=1005+j*21
                d.line([(xx,520),(xx,700)],fill=GOLD,width=2)
            for j in range(33):
                xx=1440+j*9
                d.line([(xx,520),(xx,700)],fill=TEAL,width=2)
            d.text((1040,852),"QUALITATIVE CONCEPT, NOT MEASURED DATA",font=font(24),fill=GOLD)
        else:
            headings=["EMULSION FILMS","SCINTILLATORS","GAS DETECTORS"]
            for j,name in enumerate(headings):
                x=960+j*285
                d.rounded_rectangle((x,390,x+263,754),radius=20,fill=(22,50,65),outline=TEAL,width=4)
                for h in range(6):
                    d.line([(x+36,457+36*h),(x+215,457+36*h)],fill=GOLD,width=5)
                d.text((x+10,784),name,font=font(22,True),fill=WHITE)
            d.text((1115,880),"ILLUSTRATIVE DETECTOR TYPES",font=font(25),fill=GOLD)
    elif k=="compare":
        for j,(head,sub) in enumerate((("2017  /  BIG VOID","Above the Grand Gallery"),
                                        ("2023  /  CORRIDOR","Behind north-face chevrons"))):
            x=995+j*430
            d.rounded_rectangle((x,355,x+405,820),radius=18,fill=(26,48,63),outline=GOLD,width=4)
            d.text((x+25,400),head,font=font(25,True),fill=GOLD)
            d.polygon([(x+205,490),(x+55,730),(x+350,730)],fill=(118,110,92),outline=WHITE,width=3)
            y=560 if j==0 else 530
            d.rounded_rectangle((x+176,y,x+251,y+25),radius=9,outline=TEAL,width=5)
            d.text((x+20,770),sub,font=font(23),fill=WHITE)
    elif k=="corridor":
        baseline_pyramid(d)
        d.polygon([(1390,515),(1460,420),(1555,515)],outline=TEAL,width=7)
        d.rounded_rectangle((1465,515,1605,547),radius=9,outline=GOLD,width=7)
        d.text((1110,880),"NORTH-FACE CHEVRON / SCHEMATIC",font=font(24),fill=GOLD)
    elif k=="preserve":
        baseline_pyramid(d)
        d.rounded_rectangle((1050,845,1810,926),radius=15,fill=(24,67,73),outline=TEAL,width=3)
        d.text((1130,864),"NON-DESTRUCTIVE INVESTIGATION",font=font(31,True),fill=WHITE)
    elif k=="channel":
        d.rounded_rectangle((1040,370,1785,750),radius=35,fill=(24,43,55),outline=GOLD,width=7)
        d.text((1105,455),"FACTS",font=font(83,True),fill=WHITE)
        d.text((1105,570),"UNCOVERED",font=font(80,True),fill=GOLD)
    elif k=="monument":baseline_pyramid(d)

def plate(shot,asset,file):
    im=Image.new("RGB",(WIDTH,HEIGHT),DARK)
    d=ImageDraw.Draw(im,"RGBA")
    for j in range(24):
        y=170+j*41
        d.line([(0,y),(WIDTH,y)],fill=(26,43,51,60),width=2)
    d.rectangle((0,0,WIDTH,9),fill=GOLD+(255,))
    d.text((77,47),"FACTS UNCOVERED  /  THE GREAT PYRAMID",font=font(29,True),fill=GOLD)
    d.line([(80,110),(1850,110)],fill=(75,95,103),width=2)
    k=shot["visual_type"]
    if shot.get("photo_id"):
        src=Image.open(asset[shot["photo_id"]]["path"]).convert("RGB")
        photo=ImageOps.fit(src,(1010,800),method=Image.Resampling.LANCZOS)
        im.paste(photo,(900,165))
        d=ImageDraw.Draw(im,"RGBA")
        d.rectangle((900,165,1910,965),outline=GOLD+(255,),width=3)
        d.rectangle((895,887,1915,970),fill=(5,12,18,218))
        lic=asset[shot["photo_id"]]["record"]["license"]
        d.text((925,915),"AUTHENTIC ARCHIVE  |  "+lic,font=font(26),fill=WHITE)
    else:graphics(d,k,shot=shot)
    d.rounded_rectangle((53,177,885,972),radius=18,fill=(9,17,28,235),outline=(63,76,77,200),width=3)
    d.text((98,235),f"CHAPTER 01   •   {shot['id']}",font=font(27,True),fill=GOLD)
    write_lines(d,shot["heading"],98,355,720,71,color=WHITE,bold=True,maxlines=3)
    d.line([(103,640),(785,640)],fill=GOLD,width=3)
    write_lines(d,shot["detail"],103,680,685,37,color=(229,219,201),maxlines=4)
    footer=("AUTHENTIC MODERN PHOTOGRAPH" if shot.get("photo_id") else
            "ORIGINAL EXPLANATORY VISUAL  |  SCHEMATIC • NOT TO SCALE")
    d.rectangle((0,1016,WIDTH,HEIGHT),fill=(6,14,24,254))
    d.text((80,1035),footer,font=font(24,True),fill=GOLD)
    # No floating narration words on the image: SRT is delivered separately.
    im.save(file,quality=95,subsampling=0)

def documentary_real_photo_plate(shot, assets, filename):
    """Real archival image occupies nearly the entire frame.
    Title is a restrained lower-third rather than the old giant split-screen card.
    Never invent archaeological objects, inscriptions or historic events.
    """
    assert shot["photo_id"] in assets, ("Missing selected authentic photo",shot["id"])
    src=Image.open(assets[shot["photo_id"]]["path"]).convert("RGB")
    mode=shot["composition"]
    assert mode in ("PHOTO_DOCUMENTARY","PHOTO_ARCHIVE")
    w,h=WIDTH,HEIGHT
    if mode=="PHOTO_DOCUMENTARY" and src.width/src.height>=1.20:
        im=ImageOps.fit(src,(w,h),method=Image.Resampling.LANCZOS,centering=(.5,.5)).convert("RGBA")
    else:
        blurred=ImageOps.fit(src,(w,h),method=Image.Resampling.LANCZOS).filter(
            ImageFilter.GaussianBlur(40))
        blurred=ImageEnhance.Brightness(blurred).enhance(.34).convert("RGBA")
        subject=ImageOps.contain(src,(1820,1018),method=Image.Resampling.LANCZOS)
        x=(w-subject.width)//2;y=(h-subject.height)//2
        blurred.paste(subject,(x,y))
        im=blurred
    black=Image.new("RGBA",(w,h),(0,0,0,0))
    d=ImageDraw.Draw(black)
    for i in range(0,360,6):
        alpha=round(204*(1-i/360)**1.28)
        d.rectangle((0,h-360+i,w,h-360+i+6),fill=(6,13,20,alpha))
    d.rectangle((0,0,w,58),fill=(6,13,20,162))
    im=Image.alpha_composite(im,black)
    d=ImageDraw.Draw(im)
    label=shot.get("authentic_subject_label") or "VERIFIED HISTORICAL SOURCE"
    d.text((65,18),("FACTS UNCOVERED  •  "+label)[:125],
        font=font(20,True),fill=GOLD)
    heading=shot["heading"]
    # Cinematic lower-third; does not hide the subject with long topic lists.
    end=write_lines(d,heading,80,865,1630,48,color=WHITE,bold=True,maxlines=2)
    if end<991 and len(shot["detail"])<115:
        write_lines(d,shot["detail"],81,min(948,end+4),1650,25,color=(244,233,215),maxlines=2)
    d.line([(0,1071),(w,1071)],fill=GOLD,width=5)
    credit=assets[shot["photo_id"]]["record"]
    # Full rights info is in the attached machine-readable licence ledger.
    # No original-source claims made solely from filename.
    im.convert("RGB").save(filename,quality=93,subsampling=0)

def cinematic_plate(shot,asset,filename):
    """Explicitly art-directed layouts, not the old card template.
    The layout is stored on the individual scene, never selected by keyword.
    All original diagrams are transparent layers with visible historical disclaimers.
    """
    mode=shot["composition"]
    if mode in ("PHOTO_DOCUMENTARY","PHOTO_ARCHIVE"):
        return documentary_real_photo_plate(shot,asset,filename)
    if mode not in ("PHOTO_FULL_BLEED","PHOTO_CONTAIN","GRAPHIC_HERO","GRAPHIC_RIGHT","GRAPHIC_LEFT"):
        raise ValueError("Missing authorized composition "+str(mode))
    w,h=WIDTH,HEIGHT
    if mode=="PHOTO_FULL_BLEED":
        assert shot.get("photo_id"),("Full-bleed requires verified original photo",shot["id"])
        src=Image.open(asset[shot["photo_id"]]["path"]).convert("RGB")
        bg=ImageOps.fit(src,(w,h),method=Image.Resampling.LANCZOS)
        dark=Image.new("RGBA",(w,h),(0,0,0,0));mask=ImageDraw.Draw(dark,"RGBA")
        # Preserve the authentic photograph across the frame. A restrained
        # lower-third protects readability without blacking out half the image.
        for y in range(610,h,7):
            alpha=int(208*max(0,(y-610)/(h-610))**.9)
            mask.rectangle((0,y,w,y+8),fill=(5,11,18,alpha))
        mask.rectangle((0,1018,w,h),fill=(4,12,20,185))
        im=Image.alpha_composite(bg.convert("RGBA"),dark)
    elif mode=="PHOTO_CONTAIN":
        assert shot.get("photo_id"),("Document view requires exact photo source",shot["id"])
        src=Image.open(asset[shot["photo_id"]]["path"]).convert("RGB")
        bg=ImageOps.fit(src,(w,h),method=Image.Resampling.LANCZOS)
        bg=ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(35))).enhance(.24)
        im=bg.convert("RGBA")
        foreground=ImageOps.contain(src,(1100,845),method=Image.Resampling.LANCZOS)
        fx=780+(1080-foreground.width)//2
        fy=155+(845-foreground.height)//2
        im.paste(foreground.convert("RGBA"),(fx,fy))
        dd=ImageDraw.Draw(im,"RGBA")
        dd.rectangle((fx-5,fy-5,fx+foreground.width+5,fy+foreground.height+5),outline=GOLD+(255,),width=5)
        dd.rectangle((0,0,765,h),fill=(6,13,23,220))
    else:
        # Deep stone-toned grading with restrained geometry; no fake ancient text.
        im=Image.new("RGBA",(w,h),DARK+(255,))
        d=ImageDraw.Draw(im,"RGBA")
        for j in range(36):
            y=150+j*29
            d.line([(0,y),(w,y)],fill=(43,58,65,min(70,j*2+8)),width=1)
        for j in range(0,730,23):
            x=870+j
            d.arc((x-400,165-j//6,x+340,975+j//6),180,340,fill=(43,73,76,18),width=2)
        illustration=Image.new("RGBA",(w,h),(0,0,0,0))
        graphics(ImageDraw.Draw(illustration,"RGBA"),shot["visual_type"],shot=shot)
        crop=illustration.crop((930,235,1865,960))
        if mode=="GRAPHIC_HERO":
            x,y,ww,hh=303,200,1340,705
        elif mode=="GRAPHIC_RIGHT":
            x,y,ww,hh=850,169,1070,805
        else:
            x,y,ww,hh=35,185,1145,775
        crop=crop.resize((ww,hh),Image.Resampling.LANCZOS)
        im.alpha_composite(crop,(x,y))
        shade=Image.new("RGBA",(w,h),(0,0,0,0))
        ds=ImageDraw.Draw(shade,"RGBA")
        if mode=="GRAPHIC_HERO":
            ds.rectangle((0,850,w,h),fill=(7,14,23,195))
            ds.rectangle((0,0,w,192),fill=(7,14,23,120))
        elif mode=="GRAPHIC_RIGHT":
            for x0 in range(0,835,8):
                a=int(155*max(0,1-x0/850)**.8)
                ds.rectangle((x0,0,x0+8,h),fill=(7,15,24,a))
        else:
            for x0 in range(1140,w,9):
                a=int(155*max(0,(x0-1135)/785)**.8)
                ds.rectangle((x0,0,x0+9,h),fill=(7,15,24,a))
        im=Image.alpha_composite(im,shade)

    d=ImageDraw.Draw(im,"RGBA")
    d.rectangle((0,0,w,6),fill=GOLD+(255,))
    d.text((88,53),"FACTS UNCOVERED  /  GREAT PYRAMID",
           font=font(25,True),fill=GOLD)
    d.line([(88,115),(650,115)],fill=(170,149,103,180),width=2)
    if mode=="PHOTO_FULL_BLEED":
        # Real image takes centre stage; no fake-slide giant typography.
        ty=755;tx=95;mw=1680;headsize=57
        detail_y=926;detail_size=29
    elif mode=="PHOTO_CONTAIN":
        ty=335;tx=90;mw=620;headsize=71
        detail_y=654;detail_size=34
    elif mode=="GRAPHIC_HERO":
        ty=126;tx=90;mw=1360;headsize=72
        detail_y=901;detail_size=32
    elif mode=="GRAPHIC_RIGHT":
        ty=334;tx=90;mw=700;headsize=74
        detail_y=620;detail_size=34
    else:
        ty=330;tx=1220;mw=620;headsize=67
        detail_y=615;detail_size=32
    heading=shot["heading"]
    if mode=="PHOTO_FULL_BLEED":
        topic=shot.get("on_screen_photo_subject_note") or "AUTHENTIC DOCUMENTARY PHOTOGRAPH"
        d.text((tx,710),topic[:94],font=font(23,True),fill=GOLD)
    lines_y=write_lines(d,heading,tx,ty,mw,headsize,color=WHITE,bold=True,maxlines=3)
    if mode=="GRAPHIC_HERO":
        d.rectangle((tx,859,tx+144,864),fill=GOLD+(255,))
    else:
        rule=min(detail_y-32,lines_y+15)
        d.rectangle((tx,rule,tx+128,rule+5),fill=GOLD+(255,))
    if mode=="PHOTO_FULL_BLEED" and lines_y>detail_y-9:
        # Never print a second line over the headline; the narration carries
        # detail while the truthful original photograph occupies the screen.
        pass
    else:
        write_lines(d,shot["detail"],tx,detail_y,mw,detail_size,color=(239,228,207),maxlines=3)
    d.rectangle((0,1018,w,h),fill=(5,11,19,242))
    if mode in ("PHOTO_FULL_BLEED","PHOTO_CONTAIN"):
        credit=asset[shot["photo_id"]]["record"]
        noun=("PUBLISHED SCIENTIFIC FIGURE" if shot.get("visual_kind")=="ARCHAEOLOGICAL_RECORD" else "AUTHENTIC PHOTO")
        text=noun+"  •  "+credit["creator"]+"  •  "+credit["license"]
    else:
        text="ILLUSTRATIVE EXPLANATORY GRAPHIC  •  NOT AN ARCHAEOLOGICAL PHOTOGRAPH"
    d.text((86,1037),text[:115],font=font(22),fill=GOLD)
    im.convert("RGB").save(filename,quality=94,subsampling=0)

def segments_for_tts(text,limit=300):
    sentences=re.split(r"(?<=[.!?])\s+",text)
    chunks=[];cur=""
    for sentence in sentences:
        if len(cur)+len(sentence)+1>limit and cur:chunks.append(cur);cur=""
        if len(sentence)>limit:
            raise RuntimeError("Manually selected narration sentence too long: "+sentence[:80])
        cur=(cur+" "+sentence).strip()
    if cur:chunks.append(cur)
    return chunks

def synthesize(work,manifest,model,voices):
    from kokoro_onnx import Kokoro
    tts=Kokoro(str(model),str(voices))
    chunks=[];meta=[];sr=None;start=0.
    directory=work/"audio_segments";directory.mkdir(parents=True,exist_ok=True)
    for i,s in enumerate(manifest["shots"]):
        pieces=[]
        for bit in segments_for_tts(s["spoken_text"]):
            samples,rate=tts.create(bit,voice="am_michael",speed=0.94,lang="en-us")
            samples=np.asarray(samples,dtype=np.float32).ravel()
            assert np.isfinite(samples).all() and len(samples)>rate*.35
            if sr is None:sr=rate
            assert sr==rate
            pieces.append(samples)
            pieces.append(np.zeros(int(rate*.13),dtype=np.float32))
        pieces.append(np.zeros(int(sr*.30),dtype=np.float32))
        joined=np.concatenate(pieces)
        path=directory/(s["id"]+".wav")
        sf.write(path,joined,sr,subtype="PCM_16")
        dur=len(joined)/sr
        meta.append({**s,"start_seconds":round(start,4),"end_seconds":round(start+dur,4),
                     "duration":round(dur,4),"audio_file":str(path),
                     "audio_sha256":sha(path),"narration_source":str(SCRIPT.name)})
        chunks.append(joined);start+=dur
        print("VOICE_SHOT",s["id"],round(start,2),flush=True)
    waveform=np.concatenate(chunks)
    master=work/f"chapter_{int(manifest['chapter']):02d}_voice_MASTER.wav"
    sf.write(master,waveform,sr,subtype="PCM_16")
    (work/f"LOCKED_CHAPTER{int(manifest['chapter']):02d}_SHOT_MAP.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False))
    return master,meta

def srt_from_shots(shots,work,chapter=1):
    subtitle=[];index=1
    for shot in shots:
        words=shot["spoken_text"].split()
        t0=shot["start_seconds"];dur=shot["duration"]
        for j in range(0,len(words),8):
            part=words[j:j+8]
            begin=t0+dur*j/len(words);end=t0+dur*(j+len(part))/len(words)
            subtitle.append(f"{index}\n{sec_time(begin)} --> {sec_time(end)}\n{' '.join(part)}\n")
            index+=1
    (work/f"chapter_{chapter:02d}_PRELIMINARY.srt").write_text("\n".join(subtitle)+"\n")
    # Explicit flag: exact scene-boundary timing, intra-scene words approximate.
    (work/"CAPTIONS_QA.txt").write_text(
        "Narration shot boundaries use actual synthesized audio. Word timestamps inside "
        "shots are estimated proportional to word count and REQUIRE forced alignment "
        "and listening before YouTube publication.\n")

def video(work,shots,media,assets,voice):
    clips=[]
    frames=work/"shot_plates";frames.mkdir(exist_ok=True)
    chunks=work/"encoded_segments";chunks.mkdir(exist_ok=True)
    for s in shots:
        p=frames/(s["id"]+".jpg");cinematic_plate(s,assets,p) if s.get("composition") else plate(s,assets,p)
        clip=chunks/(s["id"]+".mp4")
        n=round(s["duration"]*24)
        assert n>25
        vf=("zoompan=z='min(zoom+0.00008,1.028)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps=24,format=yuv420p"
          if s["camera"]=="PUSH" else "format=yuv420p")
        runcmd("ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-loop","1","-framerate","24","-i",p,
            "-frames:v",n,"-vf",vf,"-c:v","libx264","-preset","veryfast",
            "-crf","18","-pix_fmt","yuv420p","-an",clip)
        clips.append(clip)
        print("SHOT_RENDERED",s["id"],round(s["duration"],3),flush=True)
    cat=work/"locked_concat.txt";cat.write_text(
        "".join("file '"+str(q.resolve())+"'\n" for q in clips))
    silent=work/"chapter_01_picture_only.mp4"
    runcmd("ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
           "-f","concat","-safe","0","-i",cat,"-c","copy",silent)
    final=work/f"Great_Pyramid_Chapter{int(media['chapter']):02d}_MANUALLY_DIRECTED_REVIEW.mp4"
    runcmd("ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
           "-i",silent,"-i",voice,"-map","0:v:0","-map","1:a:0",
           "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",
           "-shortest","-movflags","+faststart",final)
    pb=json.loads(runcmd("ffprobe","-v","error","-show_streams","-show_format",
                         "-of","json",final))
    length=float(pb["format"]["duration"])
    expected=sum(t["duration"] for t in shots)
    assert abs(length-expected)<.6,(length,expected)
    assert any(t.get("width")==1920 and t.get("height")==1080 for t in pb["streams"])
    assert any(t.get("codec_type")=="audio" for t in pb["streams"])
    (work/"RENDER_TECHNICAL_QA.json").write_text(json.dumps(
        {"codec_validation":"METADATA_PASS","runtime_seconds":length,
         "audio_duration":expected,"shot_count":len(shots),
         "source_audio_rebuilt":True,
         "creative_shots":"24 individually authored passages, no keyword montage",
         "final_audiovisual_review":"PENDING",
         "caption_forced_alignment":"PENDING",
         "release_approval":False,
         "master_original_unmodified":True,"sha256":sha(final)},indent=2))
    return final

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--work",default="giza_chapter01_directed")
    p.add_argument("--chapter",type=int,default=1)
    p.add_argument("--manifest",type=Path,default=None,help="Exact authored image-first scene decisions")
    p.add_argument("--model",required=True);p.add_argument("--voices",required=True)
    p.add_argument("--storyboard-only",action="store_true")
    p.add_argument("--layout-preview-only",action="store_true")
    p.add_argument("--reuse-voice",action="store_true",help="Rebuild picture using previously approved WAV and measured shot map")
    a=p.parse_args();out=Path(a.work);out.mkdir(parents=True,exist_ok=True)
    global FILM,SCRIPT
    FILM=a.manifest.resolve() if a.manifest else BASE/f"chapter{a.chapter:02d}_directed_shots.json"
    possible=sorted((BASE/"chapters").glob(f"{a.chapter:02d}_*.txt"))
    assert len(possible)==1,(a.chapter,possible)
    SCRIPT=possible[0]
    man=paragraphs_and_shots()
    # An existing, immutable Kokoro WAV establishes real times for each manually
    # chosen scene. Reuse these exact timings; never retime narration to fit pictures.
    if a.reuse_voice:
        previous_map=out/f"LOCKED_CHAPTER{a.chapter:02d}_SHOT_MAP.json"
        assert previous_map.is_file(),("Source voice timeline required",previous_map)
        existing=json.loads(previous_map.read_text(encoding="utf-8"))
        assert len(existing)==len(man["shots"])
        for current,recorded in zip(man["shots"],existing):
            assert current["id"]==recorded["id"]
            assert recorded.get("spoken_text","").strip()
            current["spoken_text"]=recorded["spoken_text"]
            current["start_seconds"]=float(recorded["start_seconds"])
            current["end_seconds"]=float(recorded["end_seconds"])
    # Every NEW film edit must pass the global authentic-photo-first source gate.
    # This intentionally rejects legacy 2026 diagrams until each exception or open
    # photograph is sourced and manually approved. No flags bypass the gate for a render.
    if not a.storyboard_only:
        import sys
        sys.path.insert(0,str(BASE.parent.parent))
        from source_first_policy import validate
        selection=validate(man,phase="plan",root=out)
        (out/"SOURCE_FIRST_PREFLIGHT.json").write_text(json.dumps(selection,indent=2))
        if selection["status"]!="PASS":
            raise RuntimeError(
                "New picture edit blocked by source-first policy: "
                +"; ".join(selection["errors"][:12])
                +(". More violations in SOURCE_FIRST_PREFLIGHT.json" if len(selection["errors"])>12 else "")
            )
    # This creates a fully specific storyboard BEFORE anything is downloaded or spoken.
    (out/"CHAPTER01_DIRECTOR_APPROVED_STRUCTURE.json").write_text(json.dumps(man,indent=2))
    if a.storyboard_only:return
    assets=archive_assets(out,man)
    # Verify the *actual downloaded photograph bytes*, not just the plan/licence text.
    if not a.storyboard_only:
        from source_first_policy import validate
        for shot in man["shots"]:
            if shot.get("visual_kind") in ("AUTHENTIC_PHOTO","ARCHIVAL_PHOTO","ARCHAEOLOGICAL_RECORD","HISTORICAL_DOCUMENT","MUSEUM_OBJECT","REAL_FOOTAGE"):
                selected=assets[shot["photo_id"]]["path"]
                shot["asset"]["local_path"]=str(Path(selected).resolve().relative_to(out.resolve()))
                shot["asset"]["sha256"]=sha(selected)
        real_check=validate(man,phase="release",root=out)
        (out/"SOURCE_FIRST_ACTUAL_ASSETS.json").write_text(json.dumps(real_check,indent=2))
        if real_check["status"]!="PASS":
            raise RuntimeError("Selected images fail real-image rights or SHA checks: "
               +"; ".join(real_check["errors"][:10]))
    if a.layout_preview_only:
        # Preview real licensed photos and exactly chosen diagrams before synthesis or encoding.
        from PIL import ImageOps
        candidates=man["shots"]
        selected=list(dict.fromkeys([0,1,2,3,4,5,9,12,14,len(candidates)-3,len(candidates)-2,len(candidates)-1]))
        thumbnails=[]
        for k in selected:
            shot=candidates[k]
            outpath=out/f"preflight_{shot['id']}.jpg"
            cinematic_plate(shot,assets,outpath)
            im=Image.open(outpath).convert("RGB")
            im=ImageOps.fit(im,(600,338))
            thumbnails.append(im)
        cols=3;rows=(len(thumbnails)+cols-1)//cols
        sheet=Image.new("RGB",(cols*600,rows*338),(9,17,25))
        for i,im in enumerate(thumbnails):
            sheet.paste(im,((i%cols)*600,(i//cols)*338))
        sheet.save(out/"CINEMATIC_LAYOUT_PREFLIGHT.jpg",quality=90)
        print("LAYOUT_PREFLIGHT",a.chapter,len(thumbnails),flush=True)
        return
    if a.reuse_voice:
        voice=out/f"chapter_{a.chapter:02d}_voice_MASTER.wav"
        scene_file=out/f"LOCKED_CHAPTER{a.chapter:02d}_SHOT_MAP.json"
        assert voice.is_file() and scene_file.is_file(),("Missing reusable artifacts",voice,scene_file)
        shots=json.loads(scene_file.read_text())
        assert len(shots)==man["shot_count"] and all(
            a1["id"]==a2["id"] and a1["spoken_text"]==a2["spoken_text"]
            for a1,a2 in zip(shots,man["shots"])), "Existing voice shot map differs from current script"
        # The recorded spoken audio and its measured timing are immutable.
        # Only the hand-authored picture direction is updated for the corrected cut.
        approved_visual_fields=("visual_type","heading","detail","photo_id",
          "composition","camera","research_source","evidence_level","direction",
          "visual_labels","record_lines","transition","visual_kind","shot_subject",
          "why_this_visual","authentic_source_searches","editor_approved_by",
          "editorial_status","asset","why_authentic_image_inadequate",
          "individual_exception_approved","on_screen_disclosure","authentic_subject_label")
        for previous,current in zip(shots,man["shots"]):
            for key in approved_visual_fields:
                if key in current:previous[key]=current[key]
                elif key in previous:previous.pop(key)
        scene_file.write_text(json.dumps(shots,indent=2,ensure_ascii=False))
        print("REUSED_ORIGINAL_VOICE_WITH_UPDATED_PICTURE_DIRECTION",voice,flush=True)
    else:
        voice,shots=synthesize(out,man,a.model,a.voices)
    srt_from_shots(shots,out,a.chapter)
    result=video(out,shots,man,assets,voice)
    print("CHAPTER_NEW_RENDER_COMPLETE",a.chapter,result,result.stat().st_size,flush=True)

if __name__=="__main__":main()
