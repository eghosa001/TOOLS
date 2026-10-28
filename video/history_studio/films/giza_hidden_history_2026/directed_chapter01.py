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
    if item["expected_licence"]=="CC0":
        assert "CC0" in lic.upper() or "PUBLIC DOMAIN" in lic.upper(),lic
    else:
        assert "PUBLIC DOMAIN" in lic.upper() or lic.upper() in ("PD","PDM"),lic
    url=info.get("thumburl") or info.get("url")
    assert url and "wikimedia.org" in url
    result=requests.get(url,headers=HEADERS,timeout=80);result.raise_for_status()
    assert len(result.content)>30000 and len(result.content)<20000000
    target.write_bytes(result.content)
    with Image.open(target) as im:
        assert im.width>=900 and im.height>=480
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
    f=font(size,bold);words=words.split()
    lines=[];line=""
    for word in words:
        candidate=(line+" "+word).strip()
        if d.textbbox((0,0),candidate,font=f)[2]>limit and line:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    assert len(lines)<=maxlines,("Unusable on-screen typography",lines)
    for j,line in enumerate(lines):
        d.text((x,y+j*int(size*1.25)),line,font=f,fill=color)
    return y+len(lines)*int(size*1.25)

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

def graphics(d,k,seed=0):
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
        headings=(("OBSERVED","INTERPRETED","NOT DEMONSTRATED")
                if k=="evidence" else ("LOAD MANAGEMENT?","BUILDING SEQUENCE?","ORIGINAL PURPOSE?"))
        for j,s in enumerate(headings):
            y=335+j*173
            d.rounded_rectangle((1000,y,1817,y+125),radius=20,fill=(26,50+j*6,64+j*2),outline=GOLD,width=3)
            d.text((1040,y+33),s,font=font(35,True),fill=WHITE if j<2 else GOLD)
            d.ellipse((1756,y+46,1786,y+76),fill=GOLD)
    elif k in ("archive","records"):
        d.rounded_rectangle((1030,290,1795,850),radius=16,fill=(188,166,128),outline=GOLD,width=5)
        if k=="records":
            for j in range(11):
                y=363+j*43;d.line([(1080,y),(1735,y)],fill=(98,87,73),width=3)
            d.text((1080,317),"MODERN SCIENTIFIC RECORD",font=font(26,True),fill=(50,47,44))
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
    else:graphics(d,k)
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
        p=frames/(s["id"]+".jpg");plate(s,assets,p)
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
    p.add_argument("--model",required=True);p.add_argument("--voices",required=True)
    p.add_argument("--storyboard-only",action="store_true")
    a=p.parse_args();out=Path(a.work);out.mkdir(parents=True,exist_ok=True)
    global FILM,SCRIPT
    FILM=BASE/f"chapter{a.chapter:02d}_directed_shots.json"
    possible=sorted((BASE/"chapters").glob(f"{a.chapter:02d}_*.txt"))
    assert len(possible)==1,(a.chapter,possible)
    SCRIPT=possible[0]
    man=paragraphs_and_shots()
    # This creates a fully specific storyboard BEFORE anything is downloaded or spoken.
    (out/"CHAPTER01_DIRECTOR_APPROVED_STRUCTURE.json").write_text(json.dumps(man,indent=2))
    if a.storyboard_only:return
    assets=archive_assets(out,man)
    voice,shots=synthesize(out,man,a.model,a.voices)
    srt_from_shots(shots,out,a.chapter)
    result=video(out,shots,man,assets,voice)
    print("CHAPTER_NEW_RENDER_COMPLETE",a.chapter,result,result.stat().st_size,flush=True)

if __name__=="__main__":main()
