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
    j=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))
    return j,float(j["format"]["duration"])
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
    querylist=list(dict.fromkeys(queries+["Great Pyramid of Giza","Giza pyramids architecture"] ))
    for query in querylist:
        if len(accepted)>=limit:break
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
            if len(accepted)>=limit:break
            title=page.get("title","")
            if title in seen:continue
            seen.add(title)
            if not re.search(r"\.(jpe?g|png|webp)$",title,re.I):continue
            if re.search(r"(midjourney|dall-e|ai.generated|stable.diffusion|fantasy|fictional)",title,re.I):continue
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
def scene_plate(title,phrase,photo,idx,scene_idx,vertical=False):
    w,h=(1080,1920) if vertical else (1920,1080)
    im=Image.new("RGB",(w,h),DARK)
    img=Image.open(photo).convert("RGB")
    blurred=fit_photo(img,w,h).filter(ImageFilter.GaussianBlur(28))
    blurred=ImageEnhance.Brightness(blurred).enhance(.25)
    im.paste(blurred)
    canvas=ImageDraw.Draw(im,"RGBA")
    if vertical:
        rect=(65,470,1015,1430)
        tx=65;ty=165;maxw=940;main_fs=70;sec_fs=37
    else:
        rect=(710,125,1845,955)
        tx=78;ty=208;maxw=560;main_fs=68;sec_fs=31
    ax,ay,bx,by=rect
    cover=fit_photo(img,bx-ax,by-ay)
    im.paste(cover,(ax,ay))
    canvas=ImageDraw.Draw(im,"RGBA")
    canvas.rounded_rectangle((ax-5,ay-5,bx+5,by+5),radius=10,outline=GOLD+(255,),width=4)
    canvas.rectangle((0,0,w,9),fill=GOLD+(255,))
    canvas.text((65,38),"FACTS UNCOVERED / STORIES & EVIDENCE",font=ttf(28 if vertical else 32,True),fill=GOLD)
    canvas.text((65,h-72),"AUTHENTIC LICENSED PHOTOGRAPH • CONTEXT",font=ttf(21 if vertical else 25),fill=(234,234,225,220))
    if vertical:
        canvas.rounded_rectangle((48,150,1025,443),radius=12,fill=(13,20,29,200))
        canvas.rounded_rectangle((48,1487,1025,1760),radius=12,fill=(13,20,29,220))
    else:canvas.rounded_rectangle((49,178,680,845),radius=12,fill=(13,20,29,210))
    f=ttf(main_fs,True)
    for i,line in enumerate(break_lines(canvas,title.upper(),f,maxw,5)):
        canvas.text((tx,ty+i*int(main_fs*1.17)),line,font=f,fill=CREAM,stroke_width=1,stroke_fill=DARK)
    if vertical:dy=1510;piece=phrase[:130]
    else:dy=min(720,ty+len(break_lines(canvas,title.upper(),f,maxw,5))*int(main_fs*1.17)+35);piece=phrase[:160]
    fs=ttf(sec_fs)
    for j,line in enumerate(break_lines(canvas,piece,fs,maxw,4)):
        canvas.text((tx,dy+j*int(sec_fs*1.32)),line,font=fs,fill=(227,216,191))
    return im
def excerpt(text,maxwords=13):
    s=re.split(r"(?<=[.!?])\s+",text.strip())[0]
    words=s.split()
    return " ".join(words[:maxwords]).strip(".") + ("..." if len(words)>maxwords else "")
def make_clips(job,title,paragraphs,secs,queries,voice,vertical=False):
    job=pathlib.Path(job);job.mkdir(parents=True,exist_ok=True)
    assets=get_assets(queries,job/"photos",limit=18)
    pathlist=[]
    steps=[]
    for para_id,(paragraph,span) in enumerate(zip(paragraphs,secs)):
        count=2 if vertical else 3
        for shot in range(count):
            j=len(steps)
            art=job/("plate_%03d.jpg"%j)
            photo=assets[(j*3+para_id+shot)%len(assets)]["local"]
            # For long chapters, alternate original photos without pretending any depict a specific event.
            subject=(title if shot==0 else ["THE EVIDENCE","HOW WE KNOW","WHAT REMAINS UNKNOWN"][shot%3])
            scene_plate(subject,excerpt(paragraph,14),photo,para_id,j,vertical).save(art,quality=88)
            dur=max(.75,span/count)
            clip=job/("scene_%03d.mp4"%j)
            w,h=(1080,1920) if vertical else (1920,1080)
            z="zoompan=z='min(zoom+0.000085,1.06)':x='(iw-iw/zoom)*0.53':y='(ih-ih/zoom)*0.43':d=1:s="+str(w)+"x"+str(h)+":fps=24,format=yuv420p"
            cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",art,
                 "-t",f"{dur:.4f}","-vf",z,"-c:v","libx264","-preset","ultrafast",
                 "-crf","24","-pix_fmt","yuv420p","-an","-movflags","+faststart",clip],timeout=160)
            pathlist.append(clip)
            steps.append({"paragraph":para_id,"shot":shot,"media":assets[(j*3+para_id+shot)%len(assets)]["source"],
                          "duration":round(dur,3)})
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
          "shots":steps,"image_credits":assets,"file":name}
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
def thumbnail(meta,output):
    images=meta["image_credits"]
    first=Image.open(images[0]["local"]).convert("RGB")
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
         "-filter_complex","[0:a]volume=1.00,acompressor=threshold=0.20:ratio=2:attack=25:release=210[v];[1:a]volume=0.48[m];[v][m]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.94[a]",
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
    thumbnail(json.loads((chapterdir/"chapter_01.json").read_text()),final/"thumbnail.jpg")
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
