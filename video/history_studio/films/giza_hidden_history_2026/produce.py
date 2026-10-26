#!/usr/bin/env python3
"""Evidence-first Giza documentary studio: licensed Wikimedia assets, original motion
graphics, Kokoro licensed TTS, chapter render, Shorts, captions, final QC.
No museum images without rights; no simulated archaeology passed off as photography.
"""
from __future__ import annotations
import argparse, hashlib, html, json, math, os, pathlib, random, re, shutil, subprocess, sys, time, urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import requests
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
CFG=json.loads((ROOT/"production.json").read_text(encoding="utf-8"))
FILES=sorted((ROOT/"chapters").glob("*.txt"))
assert len(FILES)==15,"Expected all 15 complete chapters"
F="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HEAD={"User-Agent":"FactsUncoveredEvidenceFilm/1.0 (educational research; https://github.com/eghosa001/TOOLS)"}
GOLD=(231,181,95); CREAM=(251,242,227); DARK=(13,21,30)
def cmd(args,timeout=900):
    try:subprocess.run([str(i) for i in args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=timeout)
    except subprocess.CalledProcessError as e:raise RuntimeError("ffmpeg: "+e.stderr.decode("utf8",errors="replace")[-1800:]) from e
def probe(path):
    if shutil.which("ffprobe"):
        j=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))
        return j,float(j["format"]["duration"])
    # Portable FFmpeg metadata fallback for lightweight GitHub runners with no ffprobe.
    proc=subprocess.run(["ffmpeg","-hide_banner","-i",str(path)],capture_output=True,text=True)
    info=proc.stderr
    mt=re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)",info)
    if not mt:
        raise RuntimeError("Unable to identify video runtime from genuine FFmpeg metadata: "+info[-750:])
    seconds=int(mt.group(1))*3600+int(mt.group(2))*60+float(mt.group(3))
    streams=[]
    for line in info.splitlines():
        if "Stream #" in line and "Video:" in line:
            dims=re.search(r"(?<!\d)(\d{3,5})x(\d{3,5})(?!\d)",line)
            if dims:
                streams.append({"codec_type":"video","width":int(dims.group(1)),"height":int(dims.group(2))})
        if "Stream #" in line and "Audio:" in line:
            streams.append({"codec_type":"audio"})
    if not streams:raise RuntimeError("Media streams missing in FFmpeg metadata: "+info[-750:])
    return {"format":{"duration":str(seconds)},"streams":streams}, seconds
def ttf(size,bold=False):return ImageFont.truetype(B if bold else F,int(size))
def split_speech(text,limit=320):
    # Kokoro prosody is better over sentences; small, safe chunks prevent token truncation.
    sentences=re.split(r"(?<=[.!?])\s+",text.strip())
    out=[];buf=""
    for sentence in sentences:
        if not sentence:continue
        for piece in ([sentence] if len(sentence)<=limit else re.findall(r".{1,245}(?:\s|$)",sentence) or [sentence]):
            if len(buf)+len(piece)+1>limit and buf:out.append(buf.strip());buf=""
            buf=(buf+" "+piece).strip()
    if buf:out.append(buf)
    return out
def chapter_paragraphs(idx):
    s=FILES[idx-1].read_text(encoding="utf-8").strip()
    ps=s.split("\n\n")
    assert len(ps)>=7,("No chapter paragraphs",idx)
    return ps[0],ps[1:]
def synthesize(outdir,model,voices):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    tts=Kokoro(str(model),str(voices))
    outdir.mkdir(parents=True,exist_ok=True)
    def speak(paragraphs,prefix):
        xs=[];seconds=[];sr=None
        for i,paragraph in enumerate(paragraphs):
            if not paragraph.strip():continue
            parts=[]
            for chunk in split_speech(paragraph):
                waveform,rate=tts.create(chunk,voice=CFG["voice"],speed=float(CFG["voice_speed"]),lang="en-us")
                sig=np.asarray(waveform,dtype=np.float32).reshape(-1)
                if not np.isfinite(sig).all() or len(sig)<rate*.3:
                    raise RuntimeError("Invalid voice chunk "+prefix+" "+chunk[:60])
                if sr is None:sr=rate
                assert sr==rate
                parts.extend([sig,np.zeros(int(rate*.13),dtype=np.float32)])
            pause=.48 if i<len(paragraphs)-1 else .70
            parts.append(np.zeros(int(sr*pause),dtype=np.float32))
            block=np.concatenate(parts)
            xs.append(block);seconds.append(round(len(block)/sr,5))
        audio=np.concatenate(xs)
        audio=np.clip(audio*.92,-.98,.98)
        wav=outdir/(prefix+".wav")
        sf.write(wav,audio,sr,subtype="PCM_16")
        meta={"duration":len(audio)/sr,"paragraph_seconds":seconds,"paragraphs":paragraphs,
              "sample_rate":sr,"words":sum(len(p.split()) for p in paragraphs)}
        (outdir/(prefix+".json")).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        print("NARRATION_READY",prefix,round(meta["duration"]/60,2),"minutes",meta["words"],flush=True)
    for i in range(1,16):
        title,ps=chapter_paragraphs(i)
        if i==1:ps[0]="Welcome to Facts Uncovered: Stories and Evidence. Please subscribe to the channel and tap the button below for more extraordinary true stories. "+ps[0]
        speak(ps,"chapter_%02d"%i)
    for i,short in enumerate(CFG["short_scripts"],1):
        speak([short["script"]],"short_%02d"%i)
    (outdir/"VOICE_LICENSE.txt").write_text(
      "Kokoro-82M weights Apache-2.0, kokoro-onnx MIT, am_michael stock voice. "
      "Machine-generated narration, not a human voice clone. Sources: "
      "https://huggingface.co/hexgrad/Kokoro-82M ; "
      "https://github.com/thewh1teagle/kokoro-onnx\n")
def download_photo(url,path):
    error=None
    for attempt in range(3):
        try:
            with requests.get(url,headers=HEAD,timeout=35,stream=True) as r:
                r.raise_for_status();n=0
                with path.open("wb") as f:
                    for chunk in r.iter_content(128*1024):
                        if not chunk:continue
                        n+=len(chunk)
                        if n>17_000_000:raise RuntimeError("Oversized image")
                        f.write(chunk)
            with Image.open(path) as p:
                if min(p.size)<480:raise RuntimeError("Insufficient source size")
                p.verify()
            return
        except Exception as e:
            error=e;path.unlink(missing_ok=True);time.sleep(.5+attempt)
    raise RuntimeError(str(error))
def clean_html(x):return html.unescape(re.sub(r"<[^>]*>"," ",x)).strip()
def get_assets(queries,folder,limit=20):
    """Query by chapter; accept only verifiable commercially usable licenses."""
    folder.mkdir(parents=True,exist_ok=True)
    accepted=[];seen=set()
    querylist=list(dict.fromkeys(queries+["Great Pyramid of Giza","Pyramid of Khufu Giza","Giza pyramids architecture"] ))
    # Spread archival selections across subjects rather than taking a batch of near-identical files.
    accepted_per_query=0
    for query in querylist:
        if len(accepted)>=limit:break
        accepted_per_query=0
        try:
            params={"action":"query","format":"json","generator":"search",
                    "gsrsearch":query,"gsrnamespace":6,"gsrlimit":35,
                    "prop":"imageinfo","iiprop":"url|size|extmetadata","iiurlwidth":1600}
            payload=requests.get("https://commons.wikimedia.org/w/api.php",
                params=params,headers=HEAD,timeout=36).json()
            pages=payload.get("query",{}).get("pages",{})
            print("COMMONS_RESULTS",query,len(pages),flush=True)
        except Exception as exc:
            print("COMMONS_SEARCH_ERROR",query,str(exc)[:120],flush=True);continue
        pool=sorted(pages.values(),key=lambda x:x.get("index",999))
        for page in pool:
            if len(accepted)>=limit or accepted_per_query>=7:break
            title=page.get("title","")
            if title in seen:continue
            seen.add(title)
            if not re.search(r"\.(jpe?g|png|webp)$",title,re.I):continue
            if re.search(r"(midjourney|dall-e|ai.generated|stable.diffusion|fantasy|fictional|tour.eiffel|hauteur.compar|las.vegas|minecraft|louvre|teotihuacan|chichen.itza|pisa.tower|replica.of.pyramid|christmas|wishes|anathoth|anâta|jerusalem|bethlehem|pyramid.souvenir|christmas.greeting)",title,re.I):continue
            if not re.search(r"(giza|egypt|pyramid|sphinx|khufu|khafre|cheops|kheops|dahshur|saqqara|nile|merer|papyr|boat|aswan|tura|granite|stone|masonry|hatnub|djedi|quarry|mastaba|pharaoh|sneferu)",title,re.I):continue
            ii=(page.get("imageinfo") or [{}])[0];md=ii.get("extmetadata",{})
            lic=clean_html(md.get("LicenseShortName",{}).get("value",""))
            licenseurl=md.get("LicenseUrl",{}).get("value","")
            lower=(lic+" "+licenseurl).lower()
            good=("cc by" in lower or "cc0" in lower or "public domain" in lower or
                  "pd-old" in lower or lic.lower() in ("pd","pdm"))
            if not good or "noncommercial" in lower or "by-nc" in lower or "no derivatives" in lower:continue
            # Direct sources must be documented for monetized reuse.
            raw=ii.get("thumburl") or ii.get("url")
            if not raw:continue
            target=folder/("photo_%02d.jpg"%len(accepted))
            try:
                temp=target.with_suffix(".part")
                download_photo(raw,temp)
                with Image.open(temp) as source:
                    im=ImageOps.exif_transpose(source).convert("RGB")
                    im.thumbnail((2200,1800))
                    im.save(target,quality=88)
                temp.unlink(missing_ok=True)
                artist=clean_html(md.get("Artist",{}).get("value",""))[:300]
                accepted_per_query+=1
                accepted.append({"name":title,"source":"https://commons.wikimedia.org/wiki/"+
                        urllib.parse.quote(title.replace(" ","_"),safe=":/_()"),
                        "creator":artist,"license":lic,"license_url":licenseurl,"local":str(target),
                        "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
            except Exception as e:
                target.unlink(missing_ok=True)
                print("MEDIA_SKIPPED",title,str(e)[:80],flush=True)
    (folder/"CREDITS.json").write_text(json.dumps(accepted,ensure_ascii=False,indent=2))
    if len(accepted)<3:
        raise RuntimeError("Only "+str(len(accepted))+" licensed images retrieved; no misleading unlabeled substitutes")
    print("LICENSED_IMAGES",len(accepted),"queries",queries,flush=True)
    return accepted
def fit_photo(im,w,h):
    return ImageOps.fit(im,(w,h),method=Image.Resampling.LANCZOS,centering=(.5,.5))
def break_lines(d,text,f,maxwidth,maxlines=4):
    lines=[];buf=""
    for word in text.split():
        cand=(buf+" "+word).strip()
        if d.textbbox((0,0),cand,font=f)[2]>maxwidth and buf:
            lines.append(buf);buf=word
        else:buf=cand
    if buf:lines.append(buf)
    return lines[:maxlines]
def scene_plate(title,phrase,photo,idx,scene_idx,vertical=False,source_type="LIBRARY SOURCE"):
    w,h=(1080,1920) if vertical else (1920,1080)
    im=Image.new("RGB",(w,h),(12,20,29))
    d=ImageDraw.Draw(im)
    asset=Image.open(photo).convert("RGB") if photo else None
    if asset:
        background=fit_photo(asset,w,h)
        background=ImageEnhance.Brightness(background).enhance(.40)
        background=background.filter(ImageFilter.GaussianBlur(17))
        im.paste(background)
    else:
        # Original, labelled educational infographic. No invented archaeology.
        for j in range(60):
            x=int(w*(.5+.4*math.sin(j*2.23)));y=int(h*(.5+.35*math.cos(j*.7)))
            r=15+j*3
            d.ellipse((x-r,y-r,x+r,y+r),outline=(31+j%22,52+j%28,59+j%15),width=4)
    overlay=Image.new("RGBA",(w,h),(0,0,0,0))
    d=ImageDraw.Draw(overlay,"RGBA")
    pad=62 if vertical else 78
    d.rectangle((0,0,w,112 if vertical else 115),fill=(9,16,24,229))
    d.rectangle((0,0,w,8),fill=(*GOLD,255))
    d.text((pad,36),"FACTS UNCOVERED  |  STORIES & EVIDENCE",font=ttf(31 if vertical else 33,True),fill=(*GOLD,255))
    layout=scene_idx%5
    if vertical:
        ar=(65,450,1015,1450)
        texts=(68,158,945,62)
        detail=(68,1490,945,45)
    elif layout in (0,3):
        ar=(728,135,1820,980)
        texts=(72,210,590,67)
        detail=(72,790,600,38)
    elif layout==1:
        ar=(90,138,1830,790)
        texts=(82,830,1740,53)
        detail=(82,965,1700,25)
    elif layout==2:
        ar=(960,135,1840,980)
        texts=(70,245,820,59)
        detail=(70,810,800,36)
    else:
        ar=(85,135,1845,845)
        texts=(85,880,1700,51)
        detail=(85,982,1620,25)
    ax,ay,bx,by=ar
    if asset:
        target=fit_photo(asset,bx-ax,by-ay)
        # The renderer must not stretch images or cut away an entire archival document.
        iw,ih=asset.size
        if max(iw/ih,ih/iw)>2.25:target=ImageOps.contain(asset,(bx-ax,by-ay),Image.Resampling.LANCZOS)
        im.paste(target,(ax+(bx-ax-target.width)//2,ay+(by-ay-target.height)//2))
    else:
        # Actual educational scale graphic (schematic, not to scale).
        d0=ImageDraw.Draw(im,"RGBA")
        mid=(ax+bx)//2
        d0.polygon([(mid,ay+125),(ax+115,by-110),(bx-115,by-110)],fill=(173,146,93,125),outline=(*GOLD,255),width=9)
        d0.line((mid,ay+125,mid,by-110),fill=(250,236,205,220),width=5)
        d0.ellipse((mid-50,ay+int((by-ay)*.62)-50,mid+50,ay+int((by-ay)*.62)+50),fill=(245,198,117,255))
        d0.text((ax+120,by-100),"ILLUSTRATIVE DIAGRAM - NOT TO SCALE",font=ttf(25),fill=CREAM)
    d=ImageDraw.Draw(im,"RGBA")
    d.rounded_rectangle((ax-4,ay-4,bx+4,by+4),radius=13,outline=(*GOLD,240),width=5)
    tx,ty,mw,fs=texts
    df=ttf(fs,True)
    short=' '.join(title.split()[:15])
    tl=break_lines(d,short,df,mw,4)
    if not vertical and layout not in (0,2,3):
        d.rounded_rectangle((tx-18,ty-10,min(w-40,tx+mw+14),min(h-110,ty+120)),radius=12,fill=(5,13,19,195))
    else:
        rect_h=min(700,max(150,len(tl)*int(fs*1.18)+38))
        if vertical:d.rounded_rectangle((55,140,1025,140+rect_h),radius=10,fill=(5,13,19,221))
        else:d.rounded_rectangle((tx-16,ty-20,tx+mw+22,ty+rect_h),radius=10,fill=(5,13,19,202))
    for j,line in enumerate(tl):
        y=ty+j*int(fs*1.14)
        d.text((tx,y),line,font=df,fill=CREAM,stroke_width=1,stroke_fill=(4,9,15))
    dx,dy,dmax,dfs=detail
    sec=ttf(dfs)
    if vertical:d.rounded_rectangle((55,1475,1025,1712),radius=11,fill=(6,13,20,235))
    for j,line in enumerate(break_lines(d,phrase,sec,dmax,3)):
        d.text((dx,dy+j*int(dfs*1.25)),line,font=sec,fill=(239,218,185),stroke_width=1,stroke_fill=(1,1,1))
    d.rectangle((0,h-70,w,h),fill=(7,14,23,235))
    d.text((pad,h-52),source_type+"  |  EVIDENCE-LED HISTORY",font=ttf(23 if vertical else 27),fill=(219,215,207))
    return im
def excerpt(text,maxwords=13):
    s=re.split(r"(?<=[.!?])\s+",text.strip())[0]
    words=s.split()
    return " ".join(words[:maxwords]).strip(".") + ("..." if len(words)>maxwords else "")

# Release-quality editorial source matching: no irrelevant placeholder archaeology.
STOP_BEAT={'about','after','again','which','there','where','would','these','their','those','until','using','another','could','still','thing','things','stone','ancient','pyramid','egypt','great','inside','within','that','this','from','have','while'}
TOPIC_BEATS={
 'chapter_03':['mastaba','djoser','saqqara','sneferu','bent','red','pyramid'],
 'chapter_04':['limestone','quarry','tura','aswan','granite','haul','ramp'],
 'chapter_05':['merer','wadi','j arf','papyrus','papyri','tura','boat'],
 'chapter_06':['ahrāmat','ahramat','nile','river','channel','water','port'],
 'chapter_07':['worker','labor','labour','bread','settlement','tomb','bakery'],
 'chapter_08':['ramp','haul','sledge','quarry','rope','construction'],
 'chapter_09':['gallery','chamber','corridor','interior','section','passage'],
 'chapter_10':['muon','void','scanner','scan','detector','chamber'],
 'chapter_11':['shaft','djedi','robot','corridor','north','chevron'],
 'chapter_12':['boat','barque','ship','pit','vessel'],
 'chapter_13':['sphinx','khafre','statue','temple','lion'],
 'chapter_14':['radar','science','retraction','pyramid','geology'],
}
def lexical_words(st):
    return {p for p in re.findall(r'[a-z]{4,}',st.lower()) if p not in STOP_BEAT}
def rank_archive(asset,phrase,chapter):
    name=asset['name'].lower()
    target=lexical_words(phrase)
    priority=TOPIC_BEATS.get(chapter,[])
    return 8*len(target & lexical_words(name))+3*sum(1 for p in priority if p in name and p in phrase.lower())
def source_is_relevant(asset,phrase,chapter):
    name=asset['name'].lower()
    if any(bad in name for bad in ('christmas','wishes','anathoth','anâta','jerusalem','bethlehem','pisa','eiffel','teotihuacan')):return False
    if chapter=='chapter_05' and not any(t in name for t in ('merer','papy','tura','wadi','nile','boat','giza','pyramid')):return False
    if chapter=='chapter_06' and not any(t in name for t in ('giza','pyramid','nile','river','ahr','water','egypt','boat')):return False
    if chapter=='chapter_12' and not any(t in name for t in ('boat','barque','ship','khufu','pyramid','giza','egypt')):return False
    return True
def evidence_diagram(header,chapter,vertical=False):
    # An explicitly labelled editorial diagram, never a fake photo of a historic find.
    w,h=(1080,1920) if vertical else (1920,1080)
    im=Image.new('RGB',(w,h),(14,23,35));d=ImageDraw.Draw(im,'RGBA')
    for y in range(130,h-100,38):d.line((52,y,w-52,y),fill=(38,55,68,130),width=1)
    d.rectangle((0,0,w,11),fill=GOLD+(255,))
    d.text((62,40),'FACTS UNCOVERED  /  STORIES & EVIDENCE',font=ttf(30,True),fill=GOLD)
    f=ttf(64 if not vertical else 53,True)
    for j,line in enumerate(break_lines(d,header.upper(),f,w-150,3)):
        d.text((75,153+j*(75 if not vertical else 65)),line,font=f,fill=CREAM)
    upper=int(h*.38);low=int(h*.77);cx=w//2
    if chapter in ('chapter_05','chapter_06','chapter_04','chapter_12'):
        # Conceptual route: quarry, water movement, worksite.
        dx=int(w*.20);dy=int(w*.80)
        d.line((dx,upper+120,cx,upper+60,dy,upper+160),fill=(80,175,194,255),width=17)
        for x,label in zip((dx,cx,dy),('STONE / SOURCE','WATER ROUTE','GIZA')):
            d.ellipse((x-20,upper+75,x+20,upper+115),fill=GOLD+(255,))
            d.text((x-65,upper+186),label,font=ttf(23,True),fill=CREAM)
        d.text((75,low),'CONCEPTUAL ROUTE  •  NOT TO SCALE',font=ttf(27),fill=GOLD)
    elif chapter in ('chapter_09','chapter_10','chapter_11'):
        d.polygon(((cx,upper-60),(int(w*.22),low),(int(w*.78),low)),fill=(152,135,103,180),outline=GOLD+(255,),width=5)
        d.rounded_rectangle((cx-int(w*.09),upper+120,cx+int(w*.09),upper+177),radius=9,fill=(8,14,24,255),outline=(248,231,188,255),width=3)
        d.line((cx,upper+177,cx,low),fill=(247,225,188,255),width=5)
        d.text((75,low+25),'SIMPLIFIED CROSS-SECTION  •  NOT TO SCALE',font=ttf(25),fill=GOLD)
    else:
        for k,label in enumerate(('OBSERVED EVIDENCE','PROPOSED EXPLANATION','LIMITS OF KNOWLEDGE')):
            y=upper+55+k*125
            d.rounded_rectangle((int(w*.2),y,int(w*.8),y+85),radius=16,fill=(28+k*9,48+k*8,68+k*6,245),outline=GOLD+(255,),width=2)
            d.text((int(w*.23),y+23),label,font=ttf(30,True),fill=CREAM)
    d.rectangle((0,h-98,w,h),fill=(6,14,22,255))
    d.text((60,h-72),'ORIGINAL EDUCATIONAL SCHEMATIC  /  NOT ARCHAEOLOGICAL FOOTAGE',font=ttf(24),fill=GOLD)
    return im

def make_clips(job,title,paragraphs,secs,queries,voice,vertical=False):
    job=pathlib.Path(job);job.mkdir(parents=True,exist_ok=True)
    assets=get_assets(queries,job/"photos",limit=45)
    pathlist=[]
    steps=[]
    used_media=set()
    chapter=job.name
    for para_id,(paragraph,span) in enumerate(zip(paragraphs,secs)):
        count=8 if vertical else 3
        for shot in range(count):
            j=len(steps)
            art=job/("plate_%03d.jpg"%j)
            segment=paragraph if not vertical else ' '.join(paragraph.split()[int(shot*len(paragraph.split())/count):int((shot+1)*len(paragraph.split())/count)])
            eligible=[a for a in assets if a['source'] not in used_media and source_is_relevant(a,segment,chapter)]
            eligible.sort(key=lambda a:rank_archive(a,segment,chapter),reverse=True)
            asset=eligible[0] if eligible else None
            # Alternate archival evidence with precisely marked conceptual diagrams;
            # this avoids using unrelated scenic imagery for technical explanations.
            if (not vertical and shot==1 and chapter in TOPIC_BEATS) or (vertical and shot in (2,6)):
                asset=None
            if asset:used_media.add(asset['source'])
            photo=asset["local"] if asset else None
            words=paragraph.split()
            if vertical:
                a=min(len(words)-1,int(len(words)*shot/count))
                b=min(len(words),int(len(words)*(shot+1)/count))
                segment=" ".join(words[a:b]) or " ".join(words[-10:])
                subject=title if shot==0 else excerpt(segment,11)
                beat=" ".join(words[b:min(len(words),b+10)])
            else:
                subject=title if shot==0 and para_id==0 else excerpt(paragraph,11)
                beat=excerpt(" ".join(paragraph.split()[12:]),14)
            if asset:
                scene_plate(subject,beat,photo,para_id,j,vertical,source_type="LICENSED ARCHIVAL IMAGE / CONTEXT").save(art,quality=93)
            else:
                evidence_diagram(subject,chapter,vertical).save(art,quality=94)
            dur=max(.75,span/count)
            clip=job/("scene_%03d.mp4"%j)
            w,h=(1080,1920) if vertical else (1920,1080)
            z="zoompan=z='min(zoom+0.000085,1.06)':x='(iw-iw/zoom)*0.53':y='(ih-ih/zoom)*0.43':d=1:s="+str(w)+"x"+str(h)+":fps=24,format=yuv420p"
            cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",art,
                 "-t",f"{dur:.4f}","-vf",z,"-c:v","libx264","-preset","veryfast",
                 "-crf","18","-pix_fmt","yuv420p","-an","-movflags","+faststart",clip],timeout=160)
            pathlist.append(clip)
            steps.append({"paragraph":para_id,"shot":shot,"media":asset["source"] if asset else "original_programmatic_diagram",
                          "duration":round(dur,3),"beat":excerpt(paragraph,12),
                          "source_title":asset["name"] if asset else "Illustrative schematic (not to scale)"})
        print("RENDER_PARAGRAPH",title,para_id+1,"of",len(paragraphs),flush=True)
    concat=job/"clips.txt"
    concat.write_text("".join("file '"+p.name+"'\n" for p in pathlist))
    silent=job/"silent.mp4"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",concat,"-c","copy",silent],timeout=280)
    name="short_%02d.mp4"%int(job.name.split("_")[-1]) if vertical else "chapter_%02d.mp4"%int(job.name.split("_")[-1])
    dest=pathlib.Path(os.environ.get("RENDER_OUTPUT","rendered"));dest.mkdir(exist_ok=True)
    result=dest/name
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",voice,
         "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k",
         "-ar","48000","-shortest","-movflags","+faststart",result],timeout=280)
    _,actual=probe(result)
    assert abs(actual-sum(secs))<3.0,("A/V drift",actual,sum(secs))
    assert result.stat().st_size>500_000
    meta={"title":title,"duration_seconds":actual,"paragraph_seconds":secs,"paragraphs":paragraphs,
          "shots":steps,"image_credits":[a for a in assets if a["source"] in used_media],"file":name}
    if not vertical:
        shutil.copyfile(assets[0]["local"],dest/name.replace(".mp4","_cover.jpg"))
    (dest/name.replace(".mp4",".json")).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print("CHAPTER_OR_SHORT_RENDERED",result,round(actual/60,2),"minutes",result.stat().st_size,flush=True)
def render_one(index,voices,work,output):
    global ROOT
    title,ps=chapter_paragraphs(index)
    m=json.loads((pathlib.Path(voices)/("chapter_%02d.json"%index)).read_text())
    make_clips(pathlib.Path(work)/("chapter_%02d"%index),title,m["paragraphs"],m["paragraph_seconds"],
               CFG["image_queries"][index-1],pathlib.Path(voices)/("chapter_%02d.wav"%index),False)
def render_short(index,voices,work,output):
    short=CFG["short_scripts"][index-1]
    m=json.loads((pathlib.Path(voices)/("short_%02d.json"%index)).read_text())
    make_clips(pathlib.Path(work)/("short_%02d"%index),short["title"].replace("#Shorts",""),
               m["paragraphs"],m["paragraph_seconds"],short["queries"],
               pathlib.Path(voices)/("short_%02d.wav"%index),True)
def ts(t):
    s=int(t);milli=max(0,min(999,round((t-s)*1000)))
    return f"{s//3600:02d}:{s//60%60:02d}:{s%60:02d},{milli:03d}"
def caption_blocks(meta,start,index):
    out=[];tm=start
    for text,seconds in zip(meta["paragraphs"],meta["paragraph_seconds"]):
        words=text.split()
        step=8
        for j in range(0,len(words),step):
            group=words[j:j+step]
            d=seconds*len(group)/len(words)
            out.append(f"{index}\n{ts(tm)} --> {ts(tm+d)}\n{' '.join(group)}\n")
            index+=1;tm+=d
    return out,index,tm
def soundtrack(path):
    import soundfile as sf
    rate=22050;dur=96;t=np.arange(rate*dur,dtype=np.float32)/rate
    signal=np.zeros(len(t),dtype=np.float32)
    chords=[[55.0,82.41,110.0],[65.41,98.0,130.81],[49,73.42,98],[61.74,92.5,123.47]]
    for i,chord in enumerate(chords):
        mask=(t>=i*24)&(t<(i+1)*24)
        u=t[mask]-i*24
        envelope=np.minimum(1.0,u/3)*np.minimum(1.0,(24-u)/4)
        for freq in chord:
            signal[mask]+=.0044*envelope*np.sin(2*np.pi*freq*u)
    sf.write(path,signal,rate)
def thumbnail(cover,output):
    first=Image.open(cover).convert("RGB")
    base=fit_photo(first,1280,720)
    overlay=Image.new("RGBA",(1280,720))
    d=ImageDraw.Draw(overlay,"RGBA")
    for x in range(0,880,5):d.rectangle((x,0,x+5,720),fill=(8,13,21,int(245*(1-x/900))))
    out=Image.alpha_composite(base.convert("RGBA"),overlay);draw=ImageDraw.Draw(out)
    draw.text((55,90),"FACTS UNCOVERED",font=ttf(38,True),fill=GOLD)
    draw.text((58,225),"INSIDE THE",font=ttf(95,True),fill=CREAM,stroke_width=2,stroke_fill=(10,12,16))
    draw.text((54,335),"GREAT PYRAMID",font=ttf(76,True),fill=GOLD,stroke_width=2,stroke_fill=(10,12,16))
    draw.text((60,455),"WHAT'S REALLY HIDDEN?",font=ttf(44,True),fill=CREAM,stroke_width=2,stroke_fill=(10,12,16))
    out.convert("RGB").save(output,quality=92)
def assemble(chapters,shorts,final):
    final=pathlib.Path(final);final.mkdir(exist_ok=True)
    chapterdir=pathlib.Path(chapters)
    files=[chapterdir/("chapter_%02d.mp4"%i) for i in range(1,16)]
    assert all(x.exists() for x in files),"Missing rendered chapter"
    ff=final/"all_chapters.txt";ff.write_text("\n".join("file '"+str(x.resolve())+"'" for x in files)+"\n")
    assembled=final/"all_chapters.mp4"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",ff,"-c","copy",assembled],timeout=1200)
    score=final/"Original_Ambient_Score.wav";soundtrack(score)
    master=final/"Great_Pyramid_Secrets_2026_Facts_Uncovered.mp4"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",assembled,"-stream_loop","-1","-i",score,
         "-filter_complex","[0:a]acompressor=threshold=0.14:ratio=2:attack=25:release=210[v];[1:a]volume=0.32[m];[v][m]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=10[a]",
         "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",
         "-movflags","+faststart",master],timeout=1200)
    credits=[];blocks=[];cursor=0.;idx=1;chaptertimes=[]
    for i in range(1,16):
        meta=json.loads((chapterdir/("chapter_%02d.json"%i)).read_text())
        chaptertimes.append({"title":meta["title"],"start_seconds":round(cursor)})
        new,idx,_=caption_blocks(meta,cursor,idx)
        blocks+=new;cursor+=meta["duration_seconds"]
        credits.extend(meta["image_credits"])
    (final/"subtitles.srt").write_text("\n".join(blocks)+"\n",encoding="utf-8")
    (final/"CHAPTERS.json").write_text(json.dumps(chaptertimes,indent=2))
    uniq={x["sha256"]:x for x in credits}
    (final/"IMAGE_CREDITS.json").write_text(json.dumps(list(uniq.values()),indent=2,ensure_ascii=False))
    shortdir=pathlib.Path(shorts)
    for i in range(1,8):
        mp=shortdir/("short_%02d.mp4"%i)
        assert mp.exists(),str(mp)
        shutil.copy2(mp,final/mp.name)
        src=shortdir/("short_%02d.json"%i)
        if src.exists():
            m=json.loads(src.read_text());scaps,_,_=caption_blocks(m,0,1)
            (final/("short_%02d.srt"%i)).write_text("\n".join(scaps)+"\n")
    thumbnail(chapterdir/"chapter_01_cover.jpg",final/"thumbnail.jpg")
    video,seconds=probe(master)
    assert 3000<seconds<12000 and master.stat().st_size>10_000_000
    assert any(s.get("width")==1920 and s.get("height")==1080 for s in video["streams"])
    assert any(s.get("codec_type")=="audio" for s in video["streams"])
    manifest={"verified_video_minutes":round(seconds/60,2),"chapter_count":15,"short_count":7,
              "photo_count":len(uniq),"chapters":chaptertimes,"voice":"Kokoro-82M am_michael",
              "manual_review_required":True,
              "edit_policy":"Archival context photography is identified, not falsely labeled as ancient evidence."}
    (final/"QC_REPORT.json").write_text(json.dumps(manifest,indent=2))
    print("COMPLETE_MASTER",master,master.stat().st_size,round(seconds/60,2),"minutes",flush=True)
def cli():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["synth","chapter","short","assemble"])
    p.add_argument("--model",default="")
    p.add_argument("--voices-file",default="")
    p.add_argument("--voice-dir",default="voices")
    p.add_argument("--index",type=int,default=1)
    p.add_argument("--work",default="scratch")
    p.add_argument("--output",default="rendered")
    p.add_argument("--chapters",default="chapter_output")
    p.add_argument("--shorts",default="short_output")
    args=p.parse_args()
    os.environ["RENDER_OUTPUT"]=args.output
    if args.command=="synth":synthesize(pathlib.Path(args.voice_dir),args.model,args.voices_file)
    elif args.command=="chapter":render_one(args.index,args.voice_dir,args.work,args.output)
    elif args.command=="short":render_short(args.index,args.voice_dir,args.work,args.output)
    else:assemble(args.chapters,args.shorts,args.output)
if __name__=="__main__":cli()
