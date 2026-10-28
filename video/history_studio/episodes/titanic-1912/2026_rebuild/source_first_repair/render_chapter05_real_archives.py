#!/usr/bin/env python3
"""Titanic April 14 ice warnings: twenty fixed editor-specific visuals,
ten actual period photographs/documents and ten evidence-essential diagrams. Voice/audio timestamps are EXACT original Kokoro recording.

No text-to-photo matching or automatic editorial image selection.
This chapter is a REVIEW CUT until visual identities/commercial rights,
historical interpretation and full audiovisual viewing are signed off.
"""
from __future__ import annotations
import os,sys,json,pathlib,hashlib,subprocess
import numpy as np,soundfile as sf
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter,ImageEnhance
ROOT=pathlib.Path(__file__).resolve().parent.parent
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.environ["TITANIC_CHAPTER"]="5"
import direct_chapter05_to15_art as diagrams
SCRIPT=json.loads((HERE/"CHAPTER05_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())
NARR=ROOT/"recorded_longform"
TIMES=json.loads((ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json").read_text())
OLD=ROOT/"archive_intake"
NEW=HERE/"intake_chapter05"
OUT=HERE/"chapter05_source_first_cut";OUT.mkdir(parents=True,exist_ok=True)
PLATES=OUT/"plates";PLATES.mkdir(exist_ok=True)
CLIPS=OUT/"clips";CLIPS.mkdir(exist_ok=True)
CREAM=(244,241,231);GOLD=(222,188,120);MUTED=(160,194,211)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def ft(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def run(args):return subprocess.run([str(x) for x in args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def hashfile(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    return h.hexdigest()
def get_photos():
    original=json.loads((OLD/"ARCHIVE_ASSET_LEDGER.json").read_text())["images"]
    extra=json.loads((NEW/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").read_text())["source_specific_metadata"]
    out={}
    for r in original:
        if r.get("file"):out[r["asset_id"]]={"path":OLD/r["file"],"source_url":r["source_url"],"title":r.get("metadata_caption",r.get("requested_description","")),"rights":r.get("license_notice",""),"creator":r.get("author","")}
    for r in extra:
        if r.get("file"):out[r["id"]]={"path":NEW/r["file"],"source_url":r["exact_item_url"],"title":r.get("actual_metadata_title"),"rights":r.get("actual_metadata_rights"),"creator":r.get("actual_metadata_creator",""),"sha":r["sha256"]}
    needed={x["source_asset_id"] for x in SCRIPT["shots"] if x["visual_kind"]!="graphic"}
    missing=needed-set(out)
    if missing:raise FileNotFoundError("Source-first chapter missing exact historical images; NO FALLBACK: "+str(sorted(missing)))
    for key in needed:
        d=out[key]
        if not d["path"].is_file():raise FileNotFoundError(d["path"])
        actual=hashfile(d["path"])
        if d.get("sha") and actual!=d["sha"]:raise RuntimeError("Historic image hash mismatch "+key)
        d["sha256"]=actual
        if not d["rights"]:raise RuntimeError("Image has no individually verifiable rights notice "+key)
        # A Library of Congress 'no known restrictions' notice is a promising
        # candidate, not conclusive global commercial copyright clearance.
        d["commercial_clearance_editor_approved"]=False
    return out
def wrap(d,text,xy,maxwidth,fontsize,color):
    f=ft(fontsize,True);x,y=xy;line=""
    for w in text.upper().split():
        next=(line+" "+w).strip()
        if line and d.textbbox((0,0),next,font=f)[2]>maxwidth:
            d.text((x,y),line,font=f,fill=color);y+=fontsize+11;line=w
        else:line=next
    if line:d.text((x,y),line,font=f,fill=color)
def photo_art(row,source,number):
    original=Image.open(source["path"]).convert("RGB")
    original=ImageOps.exif_transpose(original)
    # Archival photograph is never stretched or colorized. Blurred same-image
    # margin only, central authentic pixels remain original.
    bg=ImageOps.fit(original,(1920,1080),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(48))
    bg=ImageEnhance.Brightness(bg).enhance(.20)
    im=bg.copy();d=ImageDraw.Draw(im)
    d.rectangle((41,35,1879,1041),outline=(89,128,142),width=2)
    d.rectangle((78,78,282,85),fill=GOLD)
    d.text((79,102),"FACTS UNCOVERED / STORIES & EVIDENCE",font=ft(27,True),fill=CREAM)
    d.text((1511,102),"TITANIC  /  05 OF 15",font=ft(25,True),fill=MUTED)
    width,height=1320,632
    clean=original.copy()
    clean.thumbnail((width,height),Image.Resampling.LANCZOS)
    px=91+(width-clean.width)//2
    py=224+(height-clean.height)//2
    d.rounded_rectangle((82,214,1434,863),radius=9,fill=(7,24,34),outline=GOLD,width=3)
    im.paste(clean,(px,py))
    d=ImageDraw.Draw(im)
    d.rectangle((1485,218,1846,838),fill=(10,29,43),outline=(94,128,138),width=3)
    d.text((1522,253),"ARCHIVE",font=ft(27,True),fill=GOLD)
    wrap(d,row["onscreen_label"],(1513,319),317,30,CREAM)
    d.line((1522,688,1814,688),fill=GOLD,width=4)
    wrap(d,"DOCUMENTED • NOT RECREATED", (1520,721),288,19,MUTED)
    d.rectangle((78,903,1845,968),fill=(12,30,43))
    source_name="Library of Congress" if "loc.gov" in source["source_url"] else "Wikimedia Commons / original collection"
    foot=source_name+" • individual file source and rights recorded"
    d.text((111,921),foot,font=ft(22),fill=CREAM)
    d.text((1664,1010),f"{number:02d} / 20",font=ft(22),fill=GOLD)
    return im
def voice_audio():
    records=json.loads((NARR/"NARRATION_TIME_LEDGER.json").read_text())["records"]
    chosen=[x for x in records if x["chapter"]==5]
    assert len(chosen)==10
    output=OUT/"original_chapter05_voice.wav"
    with sf.SoundFile(output,"w",samplerate=24000,channels=1,subtype="PCM_24") as result:
        for item in chosen:
            p=NARR/f"T05_P{item['paragraph']:02d}.flac"
            samples,sr=sf.read(p,dtype="float32")
            assert sr==24000 and samples.ndim==1
            result.write(samples)
            result.write(np.zeros(round(item["pause_after_seconds"]*24000),dtype=np.float32))
    return output,float(chosen[-1]["end_seconds"]-chosen[0]["start_seconds"])
def main():
    assert SCRIPT["chapter"]==5 and len(SCRIPT["shots"])==20
    reference=[x for x in TIMES["scenes"] if x["chapter"]==5]
    assert len(reference)==20
    lookup={x["scene_id"]:x for x in reference}
    sourced=get_photos()
    clips=[];report=[]
    for index,row in enumerate(SCRIPT["shots"],1):
        beat=lookup[row["scene_id"]]
        duration=beat["duration_seconds"]
        if row["visual_kind"]=="graphic":
            image=diagrams.draw_scene(row["source_asset_id"])
            source_info=None
        else:
            source_info=sourced[row["source_asset_id"]]
            image=photo_art(row,source_info,index)
        if image.size!=(1920,1080):raise RuntimeError("Unexpected 1080p plate "+row["scene_id"])
        plate=PLATES/f"chapter05_{index:02d}_{row['source_asset_id']}.png"
        image.save(plate,optimize=True)
        out=CLIPS/f"cut_{index:02d}.mp4"
        frames=round(duration*24)
        assert frames>=24,(row["scene_id"],duration)
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",plate,
             "-frames:v",frames,"-c:v","libx264","-preset","veryfast","-crf","19",
             "-pix_fmt","yuv420p","-r","24",out])
        clips.append(out)
        report.append({"scene_id":row["scene_id"],"start_seconds":beat["start_seconds"],
          "end_seconds":beat["end_seconds"],"asset_kind":row["visual_kind"],
          "asset_id":row["source_asset_id"],"editor_why":row["editorial_why"],
          "source_url":source_info["source_url"] if source_info else None,
          "actual_source_file_sha256":source_info["sha256"] if source_info else None,
          "photo_identity_and_commercial_rights_editor_signoff":False,
          "source_first_release_approved":False})
        print("FIXED_AUTHENTIC_CHAPTER05_SHOT_RENDERED",index,20,row["scene_id"],row["source_asset_id"],flush=True)
    lst=OUT/"EXACT_FIXED_SEQUENCE.txt";lst.write_text("".join("file '"+str(x.resolve())+"'\n" for x in clips))
    silent=OUT/"picture.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",lst,
         "-c","copy","-movflags","+faststart",silent])
    voice,expected=voice_audio()
    film=OUT/"TITANIC_CHAPTER05_AUTHENTIC_FIRST_1080p_REVIEW.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",voice,
      "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","224k",
      "-ar","48000","-ac","2","-af","loudnorm=I=-16:TP=-1:LRA=9","-shortest",
      "-movflags","+faststart",film])
    x=json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",film]).stdout)
    duration=float(x["format"]["duration"])
    assert abs(duration-expected)<1.5,(duration,expected)
    video=next(z for z in x["streams"] if z["codec_type"]=="video")
    assert (video["width"],video["height"])==(1920,1080) and video["r_frame_rate"]=="24/1"
    run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",film,"-f","null","-"])
    status={"file":film.name,"seconds":duration,"shots":20,"authentic_photos":10,"necessary_diagrams":10,
       "authentic_fraction":.5,"original_narration_preserved":True,
       "complete_h264_aac_decode":"PASS","editor_shot_map":report,
       "historical_photograph_licence_editor_final_review":"PENDING",
       "original_1912_berg_identity_not_verified":True,
       "no_2024_or_proprietary_footage":True,
       "continuous_real_audio_visual_review":"PENDING",
       "other_14_chapters_modified":False,"source_first_release_approved":False}
    (OUT/"CHAPTER05_SOURCE_FIRST_QA.json").write_text(json.dumps(status,indent=2))
    print("AUTHENTIC_FIRST_TITANIC_CHAPTER05_VIDEO_EXPORTED",duration,10,10,hashfile(film),flush=True)
if __name__=="__main__":main()
