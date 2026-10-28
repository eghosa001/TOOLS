#!/usr/bin/env python3
"""TITANIC — two directly edited, source-first Shorts from FIXED 15-shot ledger.

No keyword matching, randomly selected photos, automatic montage, or footage
substitutions. Every archive image used here was individually named and given a
distinct visual purpose in SHORTS_SOURCE_FIRST_15_DIRECTED_SHOTS.json.
Reusable exact-metadata Commons intake is utility-only. Old Kokoro narration,
shot/sentence timing and truthful end subscribe are preserved verbatim.
Output remains review-only until human full viewing and source-first QA PASS.
"""
from __future__ import annotations
import hashlib,io,json,math,pathlib,subprocess,re
import requests
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageEnhance,ImageFilter

ROOT=pathlib.Path(__file__).resolve().parent
EDITOR=ROOT.parent
SOURCES=json.loads((ROOT/"SHORTS_SOURCE_FIRST_15_DIRECTED_SHOTS.json").read_text())
IN=ROOT/"original_short_sources"
OUT=ROOT/"shorts_source_first_review"
OUT.mkdir(parents=True,exist_ok=True)
MEDIA=OUT/"verified_images";MEDIA.mkdir(exist_ok=True)
FRAMES=OUT/"editorial_plates";FRAMES.mkdir(exist_ok=True)
W,H=1080,1920
NAVY=(7,20,33);GOLD=(236,190,110);CREAM=(252,249,241);GREY=(178,199,207)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
def ft(px,bold=False,serif=False):
    return ImageFont.truetype(SERIF if serif else BOLD if bold else FONT,px)
def run(args):
    return subprocess.run([str(x) for x in args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def probe(path):
    return json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",path]).stdout)
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda:file.read(1048576),b""):h.update(block)
    return h.hexdigest()
def draw_wrapped(d,txt,xy,width,font_size=41,color=CREAM,max_lines=5):
    font=ft(font_size,True)
    parts=[];line=""
    for token in txt.split():
        trial=(line+" "+token).strip()
        if line and d.textbbox((0,0),trial,font=font)[2]>width:
            parts.append(line);line=token
        else:line=trial
    if line:parts.append(line)
    if len(parts)>max_lines:raise RuntimeError("Caption text outside safe area "+txt)
    x,y=xy
    for i,line in enumerate(parts):
        d.text((x,y+i*(font_size+15)),line,font=font,fill=color)
def download_exact_commons():
    result={}
    session=requests.Session()
    session.headers.update({"User-Agent":"FactsUncoveredSourceFirstResearch/1.0 (documentary production research; source identity verified)"})
    for x in SOURCES["photo_sources"]:
        assert x["url"].startswith("https://commons.wikimedia.org/wiki/File:")
        filename=x["url"].split("File:",1)[-1].replace("_"," ")
        response=session.get("https://commons.wikimedia.org/w/api.php",params={
           "action":"query","format":"json","prop":"imageinfo",
           "iiprop":"url|extmetadata","iiurlwidth":1800,"titles":"File:"+filename
        },headers={"User-Agent":"FactsUncoveredProductionEditor/1.0 (authentic image review, source-specific)"},
         timeout=60)
        response.raise_for_status();data=response.json()
        info=next((info for p in data.get("query",{}).get("pages",{}).values() for info in p.get("imageinfo",[])),None)
        if info is None:raise RuntimeError("Exact source photo unavailable "+x["id"])
        extra=info.get("extmetadata",{})
        actual=extra.get("LicenseShortName",{}).get("value","").strip().lower()
        allowed=("public domain","cc0")
        if not any(v in actual for v in allowed):raise RuntimeError("Rights unverified for "+x["id"]+" "+actual)
        if "noncommercial" in actual or "no derivatives" in actual:raise RuntimeError("Restricted source "+x["id"])
        u=info.get("thumburl") or info.get("url")
        if not u:raise RuntimeError("No direct file url for "+x["id"])
        # Wikimedia imageinfo may append attribution UTM query parameters that cause
        # 403 responses for anonymous raw upload requests. Use verified URL path
        # and explicit source researcher UA; do not substitute any other image.
        u=u.split("?",1)[0]
        payload=session.get(u,timeout=80)
        payload.raise_for_status()
        if not 12000<len(payload.content)<26000000:raise RuntimeError("Empty or oversized media "+x["id"])
        image=ImageOps.exif_transpose(Image.open(io.BytesIO(payload.content))).convert("RGB")
        if min(image.size)<350:raise RuntimeError("Photo too small for mobile film "+x["id"])
        original=image.size;image.thumbnail((1920,1920),Image.Resampling.LANCZOS)
        file=MEDIA/(x["id"]+".jpg");image.save(file,quality=94,subsampling=0)
        result[x["id"]]={"id":x["id"],"source_page_url":x["url"],
            "file_download_url":u,"file":file.name,"identity":x["name"],"date_caution":x["fact"],
            "creator_credit":x["credit"],"license":actual,"deed_url":x["deed"],
            "sha256":sha(file),"original_dimensions":original,"inspection_dimensions":image.size,
            "source_downloaded":True,"final_manual_editor_reviewed":False}
        print("EXACT_AUTHENTIC_SHORT_SOURCE",x["id"],original,actual,flush=True)
    (OUT/"SOURCE_IMAGE_HASHES_RIGHTS_REVIEW.json").write_text(json.dumps(result,indent=2))
    return result
def hero_blank(kind):
    im=Image.new("RGB",(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        s=y/H
        d.line((0,y,W,y),fill=(int(6+8*s),int(18+14*s),int(31+19*s)))
    for x in (66,1014):
        d.line((x,156,x,1800),fill=(51,78,90),width=2)
    d.text((79,91),"FACTS UNCOVERED",font=ft(38,True),fill=CREAM)
    d.text((80,155),"STORIES & EVIDENCE",font=ft(22),fill=GOLD)
    d.rectangle((80,207,220,213),fill=GOLD)
    return im,d
def accent_title(d,title,sub,narration,islast=False):
    draw_wrapped(d,title,(79,272),906,58,GOLD,max_lines=3)
    d.rectangle((78,1358,1002,1664),fill=(11,32,46),outline=(63,111,128),width=3)
    d.rectangle((105,1380,272,1387),fill=GOLD)
    draw_wrapped(d,narration,(111,1424),854,34,CREAM,max_lines=5)
    d.text((84,1692),sub[:79],font=ft(21),fill=GREY)
    if islast:
        d.rounded_rectangle((279,1772,801,1862),radius=15,fill=(183,52,47))
        d.text((364,1784),"SUBSCRIBE",font=ft(55,True),fill=CREAM)
    else:d.text((84,1803),"THE HISTORICAL RECORD  •  NOT RE-ENACTMENT FOOTAGE",font=ft(19),fill=GREY)
def fit_box(im,box):
    x1,y1,x2,y2=box
    region=(x2-x1,y2-y1)
    src=im.copy()
    src.thumbnail(region,Image.Resampling.LANCZOS)
    return src,(x1+(region[0]-src.width)//2,y1+(region[1]-src.height)//2)
def scene_photo(shot,voice,proof):
    im,d=hero_blank(shot["tag"])
    first=Image.open(MEDIA/(shot["image"]+".jpg")).convert("RGB")
    d.rounded_rectangle((66,526,1014,1322),radius=12,fill=(14,32,43),outline=(94,133,142),width=3)
    if shot.get("image2"):
        second=Image.open(MEDIA/(shot["image2"]+".jpg")).convert("RGB")
        for q,box in ((first,(85,544,995,914)),(second,(85,931,995,1285))):
            fitted,(xx,yy)=fit_box(q,box);im.paste(fitted,(xx,yy))
        d.text((111,908),"1911 • THE SHIP",font=ft(28,True),fill=GOLD)
        d.text((111,1275),"2004 • THE WRECK",font=ft(28,True),fill=GOLD)
    else:
        fitted,(xx,yy)=fit_box(first,(77,549,1003,1289))
        im.paste(fitted,(xx,yy))
        d.rectangle((xx-2,yy-2,xx+fitted.width+2,yy+fitted.height+2),outline=GOLD,width=3)
    accent_title(d,shot["title"],shot["subtitle"],voice,islast=shot["index"]==(8 if shot["tag"].endswith("01") else 7))
    return im
def scene_diagram(shot,voice):
    source=IN/shot["tag"]/f"scene_{shot['index']:02d}.png"
    if not source.is_file():raise FileNotFoundError("Original only-art-directed graph missing: "+str(source))
    im=Image.open(source).convert("RGB")
    if im.size!=(1080,1920):raise RuntimeError("Wrong original diagram size")
    if shot["image"]=="boat_deck_annotated":
        # Actual historically based plan is drawn with its later annotations
        # and labelled as such, not presented as an unmodified 1912 photo.
        photo=Image.open(MEDIA/(shot["image"]+".jpg")).convert("RGB")
        region=(83,875,997,1220)
        fit,(xx,yy)=fit_box(photo,region)
        d=ImageDraw.Draw(im)
        d.rectangle((76,836,1000,1278),fill=(10,28,40))
        im.paste(fit,(xx,yy));d.text((100,1270),"HISTORICAL BLUEPRINT / MODERN ANNOTATIONS",font=ft(20),fill=GOLD)
    return im
def make_shorts(photos):
    by_tag={s["tag"]:[] for s in SOURCES["shots"]}
    for s in SOURCES["shots"]:by_tag[s["tag"]].append(s)
    results=[]
    for tag,shots in by_tag.items():
        assert len(shots)==(8 if tag.endswith("01") else 7)
        manuscript=IN/(tag+"_manual_shot_timeline.json")
        timing=json.loads(manuscript.read_text())["shots"]
        assert len(timing)==len(shots)
        voice_video=IN/(tag+"_mastered.mp4")
        if not voice_video.is_file():raise FileNotFoundError(voice_video)
        duration=float(probe(voice_video)["format"]["duration"])
        outputdir=OUT/tag;outputdir.mkdir(exist_ok=True)
        clipfiles=[];proof_shots=[]
        for i,shot in enumerate(shots):
            ref=timing[i];assert ref["scene"]==shot["index"] and ref["start_seconds"]>=0
            t=ref["narration"]
            if shot["kind"]=="DOCUMENTARY_DIAGRAM":
                image=scene_diagram(shot,t)
            else:image=scene_photo(shot,t,photos)
            still=outputdir/f"shot_{i+1:02d}_{(shot.get('image') or shot.get('legacy'))}.png"
            image.save(still,optimize=True)
            clip=outputdir/f"cut_{i+1:02d}.mp4"
            frames=round((ref["end_seconds"]-ref["start_seconds"])*24)
            if not frames or frames<10:raise RuntimeError("Empty segment "+str(shot["index"]))
            # Pure encoder: picture order explicitly authored in the JSON;
            # no theme/keywords/image source selection occurs in FFmpeg.
            run(["ffmpeg","-hide_banner","-loglevel","error","-y",
              "-loop","1","-framerate","24","-i",still,"-frames:v",frames,
              "-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",clip])
            clipfiles.append(clip)
            proof_shots.append({
              "index":i+1,"spoken_exact_text":t,
              "start_seconds":ref["start_seconds"],"end_seconds":ref["end_seconds"],
              "visual_kind":shot["kind"],
              "selected_asset":shot.get("image") or shot.get("legacy"),
              "real_image_source_page":([next(p["source_page_url"] for p in photos.values() if p["id"]==shot["image"])] if shot.get("image") else []),
              "image_source_sha256":photos[shot["image"]]["sha256"] if shot.get("image") else None,
              "image2_sha256":photos[shot["image2"]]["sha256"] if shot.get("image2") else None,
              "image_to_voice_reason":shot["why"],
              "historically_honest_disclosure":shot["subtitle"],
              "picture_review":"NOT APPROVED",
              "commercial_release_approved":False})
            print("EDITOR_SELECTED_SHORT_SCENE_RENDERED",tag,i+1,len(shots),shot.get("image") or shot.get("legacy"),flush=True)
        concat=outputdir/"EXACT_EDITOR_SHOT_SEQUENCE.txt"
        concat.write_text("".join("file '"+str(x.resolve())+"'\n" for x in clipfiles))
        silent=outputdir/"silent.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",concat,"-c","copy",silent])
        file=OUT/(tag+"_SOURCE_FIRST_REVIEW_1080x1920.mp4")
        # The original voice, already EBU R128 mastered, is never recreated.
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",voice_video,
          "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","copy",
          "-t",f"{duration:.4f}","-movflags","+faststart",file])
        m=probe(file)
        v=next(s for s in m["streams"] if s["codec_type"]=="video")
        a=next(s for s in m["streams"] if s["codec_type"]=="audio")
        secs=float(m["format"]["duration"])
        assert (v["width"],v["height"])==(1080,1920) and v["r_frame_rate"]=="24/1"
        assert a["codec_name"]=="aac" and 45<=secs<=60 and abs(secs-duration)<.5
        run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",file,"-f","null","-"])
        import shutil
        cap=IN/(tag+"_MASTERED_REVIEW.srt")
        if cap.is_file():shutil.copy2(cap,OUT/(tag+"_SOURCE_FIRST_REVIEW.srt"))
        report={"tag":tag,"file":file.name,"seconds":secs,"sha256":sha(file),
          "source_mastered_voice_unchanged":True,"selected_shots":proof_shots,
          "authentic_image_shots":sum(x["visual_kind"]!="DOCUMENTARY_DIAGRAM" for x in shots),
          "original_diagram_exceptions":sum(x["visual_kind"]=="DOCUMENTARY_DIAGRAM" for x in shots),
          "all_visuals_selected_individually":True,"actual_complete_video_decode":"PASS",
          "continuous_human_audiovisual_review":"NOT COMPLETED","source_first_plan_approved":False,
          "source_first_release_approved":False,"public_upload_approved":False}
        (OUT/(tag+"_EDITORIAL_QA.json")).write_text(json.dumps(report,indent=2))
        results.append(report)
        print("IMPROVED_REAL_ARCHIVAL_TITANIC_SHORT_REVIEW_EXPORTED",tag,secs,report["authentic_image_shots"],flush=True)
    (OUT/"DELIVERY_STATUS.json").write_text(json.dumps({
      "revision":"Titanic 2026 Shorts historically photographed first",
      "files":[{k:v for k,v in z.items() if k!="selected_shots"} for z in results],
      "rule":"No simulated sinking footage; real period and 2004 underwater pictures, only necessary disclosed diagrams",
      "both_complete_shorts_exported":True,"publication_approved":False},indent=2))
if __name__=="__main__":make_shorts(download_exact_commons())
