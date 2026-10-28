#!/usr/bin/env python3
"""Render ONLY five exact manually authored 2026 Titanic REVIEW shot maps.

No automatic image selection, topic matching, fallback montage, generic stock,
AI photos, or automated approval. This intentionally cannot publish anything.
Source filenames, page URLs, per-shot narration and A/B cuts are editorially fixed.
Every rendered source retains SHA-256 and status=NOT COMMERCIAL RIGHTS APPROVED.
"""
from __future__ import annotations
import argparse,hashlib,io,json,os,pathlib,re,subprocess,sys,time
from urllib.parse import unquote
import numpy as np
import requests
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter,ImageEnhance

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
W,H=1920,1080
PALETTE={"cream":(246,241,228),"gold":(225,189,119),"muted":(161,192,206)}
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GOVINFO="https://www.govinfo.gov/content/pkg/SERIALSET-06179_00_00-019-0933-0000/pdf/SERIALSET-06179_00_00-019-0933-0000.pdf"
PAGES="https://www.loc.gov/item/2025847774/"
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"FactsUncovered/1.0 (research-only exact historical asset verification)"})
CACHE=HERE/"fixed_five_source_cache"
CACHE.mkdir(parents=True,exist_ok=True)

def run(a):
    return subprocess.run([str(x) for x in a],check=True,capture_output=True,text=True)
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def plain(s):return re.sub(r"<[^>]+>"," ",str(s or "")).strip()
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def stream(url):
    for pause in (0,8,20,35):
        if pause:time.sleep(pause)
        r=SESSION.get(url,timeout=75)
        if r.status_code in (429,500,502,503,504):continue
        r.raise_for_status()
        return r.content
    raise RuntimeError("Exact selected source cannot download: "+url)
def record(name,page,source_bytes,creator,licence):
    image=ImageOps.exif_transpose(Image.open(io.BytesIO(source_bytes))).convert("RGB")
    if min(image.size)<240:raise RuntimeError("Authentic photo too low resolution "+name)
    image.thumbnail((1800,1500),Image.Resampling.LANCZOS)
    output=CACHE/(hashlib.sha256((page+name).encode()).hexdigest()[:20]+".jpg")
    image.save(output,quality=92,optimize=True)
    return {"path":output,"source_page_url":page,"source_asset_name":name,
            "licence_metadata":licence,"creator":creator,"sha256":sha(output),
            "dimensions":image.size,"commercial_rights_approved":False}
def commons(title,page):
    name=title if title and title.endswith((".jpg",".jpeg",".png",".webp")) else unquote(page.split("/wiki/File:",1)[-1]).replace("_"," ")
    url="https://commons.wikimedia.org/w/api.php"
    data=SESSION.get(url,params={"action":"query","format":"json","prop":"imageinfo",
             "iiprop":"url|extmetadata","titles":"File:"+name,"iiurlwidth":1800},timeout=50)
    data.raise_for_status()
    result=data.json()["query"]["pages"]
    info=next((r for v in result.values() for r in v.get("imageinfo",[])),None)
    if not info:raise RuntimeError("Specifically selected Commons item missing "+name)
    ext=info.get("extmetadata",{})
    rights=plain(ext.get("LicenseShortName",{}).get("value",""))
    creator=plain(ext.get("Artist",{}).get("value",""))[:250]
    lower=rights.lower()
    # Screening only, NOT definitive copyright approval. No arbitrary free assets.
    if not (("public domain" in lower) or lower in ("cc0","pd-us","pd-old","cc by 4.0","cc by 3.0","cc by-sa 4.0","cc by-sa 3.0","gfdl")):
        raise RuntimeError("Unverified/restricted Commons licence "+rights+" for "+name)
    uri=info.get("thumburl") or info.get("url")
    if not uri:raise RuntimeError("No actual source media URL "+name)
    return record(name,page,stream(uri),creator,rights)
def report():
    page_jpg=CACHE/"GOVINFO_1912_BRITISH_INQUIRY_COVER.jpg"
    if not page_jpg.exists():
        pdf=CACHE/"1912_british_government_report.pdf"
        if not pdf.exists():
            with SESSION.get(GOVINFO,stream=True,timeout=100) as response:
                response.raise_for_status()
                with pdf.open("wb") as f:
                    for chunk in response.iter_content(1<<20):
                        if chunk:f.write(chunk)
        if pdf.stat().st_size<100_000:raise RuntimeError("Malformed exact 1912 government facsimile")
        run(["pdftoppm","-f","1","-l","1","-singlefile","-scale-to","1600","-jpeg",str(pdf),str(page_jpg.with_suffix(""))])
    return {"path":page_jpg,"source_page_url":PAGES,
        "source_asset_name":"1912 British report, U.S. Senate Doc 933, front facsimile",
        "licence_metadata":"U.S. Government Printing Office 1912 facsimile; individual inserted illustrations need verification",
        "creator":"1912 United States Government Printing Office / Great Britain",
        "sha256":sha(page_jpg),"dimensions":Image.open(page_jpg).size,
        "commercial_rights_approved":False}
def loc_photo(item_id,page):
    res=SESSION.get(page.rstrip("/")+"/",params={"fo":"json"},timeout=60)
    res.raise_for_status();j=res.json();item=j.get("item",{})
    title=plain(item.get("title",""))
    primary=j.get("image_url") or item.get("image_url") or []
    urls=primary if isinstance(primary,list) else [primary]
    urls=list(urls)
    for node in j.get("resources",[]):
        for batch in node.get("files",[]):
            if isinstance(batch,list):
                urls.extend(v.get("url") for v in batch if isinstance(v,dict))
    urls=[u for u in urls if isinstance(u,str) and u.split("?")[0].lower().endswith((".jpg",".jpeg",".png"))]
    if not urls or not title:raise RuntimeError("LOC item has no independently identified media "+page)
    # File choices here must match the explicitly named LOC catalog item.
    u=next((u for u in urls if "1024" in u or "medium" in u),urls[0])
    return record(item_id,page,stream(u),plain(item.get("creator",""))[:200],
                  plain(item.get("rights_advisory") or item.get("rights") or "LOC copyright not certified"))
def source(row,prepared):
    page=row["source_page_url"]
    asset=row["source_asset_id"]
    if not page or not page.startswith("https://"):raise RuntimeError("No exact source landing page "+row["scene_id"])
    key=(asset,page)
    if key in prepared:return prepared[key]
    if page==PAGES:src=report()
    elif "commons.wikimedia.org/wiki/File:" in page:src=commons(row.get("exact_original_asset_name"),page)
    elif page.startswith("https://www.loc.gov/item/"):src=loc_photo(asset,page)
    else:raise RuntimeError("Unsupported exact file source "+page)
    prepared[key]=src
    return src
def wrap(draw,text,x,y,max_width,size,color):
    f=font(size,True);line=""
    for word in text.upper().split():
        nxt=(line+" "+word).strip()
        if line and draw.textbbox((0,0),nxt,font=f)[2]>max_width:
            draw.text((x,y),line,font=f,fill=color)
            y+=size+12;line=word
        else:line=nxt
    if line:draw.text((x,y),line,font=f,fill=color)
def photo_plate(shot,src,n,idx,total):
    img=Image.open(src["path"]).convert("RGB")
    background=ImageOps.fit(img,(W,H),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(38))
    bg=ImageEnhance.Brightness(background).enhance(.15)
    draw=ImageDraw.Draw(bg)
    draw.rectangle((45,42,1875,1040),outline=(89,124,151),width=3)
    draw.text((100,80),"FACTS UNCOVERED  /  STORIES & EVIDENCE",font=font(27,True),fill=PALETTE["cream"])
    draw.text((1535,82),f"TITANIC   {n:02d}/15",font=font(26,True),fill=PALETTE["gold"])
    framed=img.copy();framed.thumbnail((1370,690),Image.Resampling.LANCZOS)
    x=92+(1370-framed.width)//2;y=180+(690-framed.height)//2
    draw.rectangle((75,162,1510,888),fill=(11,29,43),outline=PALETTE["gold"],width=3)
    bg.paste(framed,(x,y))
    draw=ImageDraw.Draw(bg)
    draw.rectangle((1532,164,1852,876),fill=(13,35,50),outline=(87,127,149),width=2)
    draw.text((1550,198),"DOCUMENTED",font=font(29,True),fill=PALETTE["gold"])
    wrap(draw,shot["onscreen_label"],1551,270,282,24,PALETTE["cream"])
    draw.text((92,928),"ARCHIVAL SOURCE · ACTUAL DATE IDENTIFIED IN CAPTION",font=font(21),fill=PALETTE["muted"])
    draw.text((1686,958),f"{idx:02d}/{total:02d}",font=font(25,True),fill=PALETTE["gold"])
    return bg
def chapter_voice(ch,output):
    manifest=json.loads((ROOT/"recorded_longform"/"NARRATION_TIME_LEDGER.json").read_text())
    paragraphs=[r for r in manifest["records"] if r["chapter"]==ch]
    if not paragraphs:raise RuntimeError("Original narrator recording missing "+str(ch))
    with sf.SoundFile(output,"w",samplerate=24000,channels=1,subtype="PCM_24") as w:
        for item in paragraphs:
            p=ROOT/"recorded_longform"/f"T{ch:02d}_P{item['paragraph']:02d}.flac"
            s,sr=sf.read(p,dtype="float32")
            if sr!=24000 or s.ndim!=1:raise RuntimeError("Incorrect original voice format")
            w.write(s)
            w.write(np.zeros(round(item["pause_after_seconds"]*sr),dtype=np.float32))
    return paragraphs[-1]["end_seconds"]-paragraphs[0]["start_seconds"]
def process(ch):
    if ch not in (6,7,11,14,15):raise ValueError(ch)
    os.environ["TITANIC_CHAPTER"]=str(ch)
    import direct_chapter05_to15_art as diagrams
    if diagrams.CHAPTER!=ch:raise RuntimeError("Do not reuse art module across chapters")
    location=HERE/f"CHAPTER{ch:02d}_EXPLICIT_HISTORICAL_PICTURE_EDIT.json"
    doc=json.loads(location.read_text())
    rows=doc["shots"];expected={6:18,7:20,11:22,14:20,15:26}[ch]
    if len(rows)!=expected:raise RuntimeError("Editor shot-count mismatch")
    aligned=json.loads((ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json").read_text())
    original=json.loads((ROOT/"MANUAL_SCENE_LEDGER_DRAFT.json").read_text())
    spoken={s["scene_id"]:s for s in original["scenes"] if s["chapter"]==ch}
    times={s["scene_id"]:s for s in aligned["scenes"] if s["chapter"]==ch}
    if len(spoken)!=expected or len(times)!=expected:raise RuntimeError("Measured chapter timings missing")
    out=HERE/f"chapter{ch:02d}_source_first_cut";out.mkdir(exist_ok=True)
    plates=out/"plates";plates.mkdir(exist_ok=True)
    clips=out/"clips";clips.mkdir(exist_ok=True)
    prepared={};sources=[];all_clips=[];records=[]
    for idx,row in enumerate(rows,1):
        scene=row["scene_id"]
        if scene not in spoken or scene not in times:raise RuntimeError("Unrecognized user/editor shot "+scene)
        if row.get("original_spoken_paragraph",row.get("narration_paragraph"))!=spoken[scene]["narration_paragraph"]:
            raise RuntimeError("Source does not match exactly unchanged spoken paragraph "+scene)
        cue=times[scene];seconds=float(cue["duration_seconds"])
        if seconds<.3:raise RuntimeError("Unresolved narration time "+scene)
        isreal=row.get("visual_kind") in ("photo","authentic_source_candidate")
        if isreal:
            src=source(row,prepared)
            # Every photo is the exact editor-chosen source. No generic fallback.
            im=photo_plate(row,src,ch,idx,len(rows))
            sources.append(scene)
        else:
            original_id=row.get("source_asset_id")
            if original_id not in diagrams.APPROVED_ASSETS:
                raise RuntimeError("Unapproved/hallucinated diagram identifier "+str(original_id))
            im=diagrams.draw_scene(original_id)
            src=None
            if scene=="T15_P13_B":
                # Manually directed final frame; existing recorded audio already
                # contains the named channel subscription invitation.
                d=ImageDraw.Draw(im)
                d.rounded_rectangle((500,710,1420,875),radius=20,fill=(6,25,39),outline=PALETTE["gold"],width=4)
                d.text((745,752),"SUBSCRIBE",font=font(58,True),fill=PALETTE["cream"])
                d.text((570,827),"FACTS UNCOVERED: STORIES & EVIDENCE",font=font(26,True),fill=PALETTE["gold"])
        if im.size!=(W,H):raise RuntimeError("Picture output dimension mismatch")
        plate=plates/f"cut_{idx:02d}.png";im.save(plate,optimize=True)
        clip=clips/f"cut_{idx:02d}.mp4";num_frames=round(seconds*24)
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",plate,
             "-frames:v",num_frames,"-c:v","libx264","-preset","veryfast","-crf","19",
             "-pix_fmt","yuv420p","-r","24",clip])
        all_clips.append(clip)
        records.append({"id":scene,"cue_start_seconds":cue["start_seconds"],"cue_end_seconds":cue["end_seconds"],
            "media":row["source_asset_id"],"kind":"authentic" if isreal else "diagram",
            "exact_source_page":src["source_page_url"] if src else None,
            "image_file_sha256":src["sha256"] if src else None,
            "creator_from_source":src["creator"] if src else None,
            "licence_as_published":src["licence_metadata"] if src else "original reconstruction",
            "subject_reason":row["editorial_why"],"commercial_reuse_approved":False,
            "narration_shot_match_reviewed":False})
        print("EDITOR_SELECTED_SHOT",ch,idx,len(rows),scene,flush=True)
    listing=out/"FIXED_EDITOR_ORDER.txt"
    listing.write_text(chr(10).join("file '"+str(p.absolute())+"'" for p in all_clips)+chr(10))
    picture=out/"picture.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",listing,
         "-c","copy","-movflags","+faststart",picture])
    voice=out/"original_kokoro_voice.wav";original_seconds=chapter_voice(ch,voice)
    film=out/f"TITANIC_CHAPTER{ch:02d}_AUTHENTIC_FIRST_1080p_REVIEW.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",picture,"-i",voice,
         "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","224k",
         "-ar","48000","-ac","2","-af","loudnorm=I=-16:TP=-1:LRA=9",
         "-shortest","-movflags","+faststart",film])
    info=json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",film]).stdout)
    length=float(info["format"]["duration"])
    if abs(length-original_seconds)>1.6:raise RuntimeError("Audio/picture drift "+str((length,original_seconds)))
    run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",film,"-f","null","-"])
    qa={"chapter":ch,"file":film.name,"sha256":sha(film),"duration_seconds":length,
        "original_voice":True,"shots":len(rows),"nominal_archival_candidates":len(sources),
        "original_24fps_1080p":True,"complete_stream_decode":"PASS",
        "individual_source_rights_approved":False,
        "full_actual_video_watched_and_listened_to":False,
        "global_60_percent_authentic_and_contextual_gate":"NOT_VERIFIED",
        "release_approved":False,"source_metadata":records}
    (out/f"CHAPTER{ch:02d}_TECHNICAL_REVIEW.json").write_text(json.dumps(qa,indent=2))
    print("CHAPTER_REVIEW_EXPORTED_NOT_RELEASE_APPROVED",ch,length,qa["sha256"],flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--chapter",type=int,required=True)
    args=p.parse_args();process(args.chapter)
