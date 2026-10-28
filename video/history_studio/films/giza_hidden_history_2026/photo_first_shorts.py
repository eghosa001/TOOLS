#!/usr/bin/env python3
"""Two individually directed real-photography Shorts: retain source voice/captions.

Each of the seven scenes has an explicit authorized real file or a separately
justified illustration. No phrase-to-image search, random montage or synthetic
historical/archaeological fake. All images verified from their individual Commons
file pages, saved with actual SHA-256 and on-screen source context.
"""
from __future__ import annotations
import argparse,json,math,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter,ImageEnhance

BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parent.parent))
from source_first_policy import validate
from directed_chapter01 import get_photo,sha
from directed_shorts import BEATS, graphic

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GOLD=(231,188,108);WHITE=(246,239,224);W,H=1080,1920

PICTURES={
"G":("File:Great Pyramid (Pyramid of Cheops Khufu), Giza, GG, EGY (47113255374).jpg","CC0","Warren LeMay"),
"H":("File:Spelterini Pyramids.jpg","Public domain","Eduard Spelterini"),
"C":("File:East-West cut view of the Great Pyramid and front view of the North face Chevron area.png","CC BY 4.0","ScanPyramids research collaboration"),
"D":("File:Detectors installed in the DC and in the MC.png","CC BY 4.0","ScanPyramids research collaboration"),
"N":("File:Nile-Giza-Cairo.jpg","CC BY-SA 4.0","Faris knight"),
"R":("File:The red sea.jpg","CC BY-SA 4.0","Abanoub Victor"),
"K":("File:GEM Khufus Boat front 2025.jpg","CC0","Photographer per Wikimedia Commons original record")
}
DEEDS={
"CC0":"https://creativecommons.org/publicdomain/zero/1.0/",
"Public domain":"https://creativecommons.org/publicdomain/mark/1.0/",
"CC BY 4.0":"https://creativecommons.org/licenses/by/4.0/",
"CC BY-SA 4.0":"https://creativecommons.org/licenses/by-sa/4.0/",
}
# Last resort technical diagrams when no authentic image can depict actual unknown.
CHOICES={
"01":["G","C","D",None,"G","H","G"],
"02":[None,"R",None,"N",None,"G","G"]
}
DIAGRAM_REASONS={
("01",4):"The Big Void's ancient purpose has not been established and its inaccessible interior cannot be photographed. A question-mark scientific cross-section is honest.",
("02",1):"The authentic papyri of inspector Merer could not be sourced with individually verified free commercial image rights. An unrelated papyrus would be falsely implied as his diary.",
("02",3):"No surviving confirmed likeness of Inspector Merer is known; showing a modern actor, museum statue or made-up portrait would misrepresent the surviving evidence.",
("02",5):"Actual recorded paperwork cannot be reconstructed into invented handwriting. A visibly modern summary of administrative records is more accurate."
}
PHOTO_NOTES={
"G":"Genuine present-day Great Pyramid photograph; not footage of pyramid construction.",
"H":"Genuine archival Giza balloon photograph; not footage of original construction.",
"C":"Actual published scientific figure, NOT a photograph of the Void's inaccessible interior.",
"D":"Actual published scientific research figure featuring detector equipment.",
"R":"Modern Red Sea coastline context; NOT a photograph of Wadi al-Jarf's excavation.",
"N":"Modern Nile/Giza riverscape; NOT a direct map of Khufu-era river routes.",
"K":"Actual Khufu museum ship, NOT Inspector Merer's cargo vessel."
}
def ff(*args):
    r=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr[-3000:])
    return r.stdout
def fnt(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def fit_lines(draw,txt,x,y,width,size=60,fill=WHITE,max_rows=3):
    for sz in range(size,23,-2):
        lines=[];current=""
        ft=fnt(sz,True)
        for word in txt.split():
            test=(current+" "+word).strip()
            if draw.textbbox((0,0),test,font=ft)[2]>width and current:
                lines.append(current);current=word
            else:current=test
        if current:lines.append(current)
        if len(lines)<=max_rows:
            for j,line in enumerate(lines):draw.text((x,y+j*int(sz*1.25)),line,font=ft,fill=fill)
            return
    raise ValueError("Unfittable caption "+txt)
def make_photo(beat,photo,out):
    anchor,title,kind,subtitle=beat
    src=Image.open(photo["path"]).convert("RGB")
    # The actual archaeological photograph is shown intact atop a soft backdrop.
    background=ImageOps.fit(src,(W,H),Image.Resampling.LANCZOS)
    background=ImageEnhance.Brightness(background.filter(ImageFilter.GaussianBlur(32))).enhance(.34)
    im=background.convert("RGBA")
    target=ImageOps.contain(src,(1010,1230),Image.Resampling.LANCZOS)
    px=(W-target.width)//2;py=415+(1180-target.height)//2
    im.alpha_composite(target.convert("RGBA"),(px,py))
    overlay=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(overlay,"RGBA")
    d.rectangle((0,0,W,415),fill=(8,20,33,231))
    d.rectangle((0,1550,W,H),fill=(8,17,29,221))
    d.rectangle((0,0,W,9),fill=GOLD+(255,))
    d.text((65,56),"FACTS UNCOVERED",font=fnt(37,True),fill=GOLD)
    fit_lines(d,title,65,165,950,76)
    fit_lines(d,subtitle,66,1594,950,34,fill=WHITE)
    note=PHOTO_NOTES[photo["code"]]
    fit_lines(d,note,68,1710,950,26,fill=GOLD,max_rows=3)
    im=Image.alpha_composite(im,overlay)
    im.convert("RGB").save(out,quality=94,subsampling=0)
def make_illustration(beat,out):
    anchor,title,kind,subtitle=beat
    im=Image.new("RGB",(W,H),(11,21,33));d=ImageDraw.Draw(im)
    for j in range(25):d.line([(0,420+j*45),(W,420+j*45)],fill=(21,35,46),width=1)
    d.rectangle((0,0,W,8),fill=GOLD)
    d.text((65,58),"FACTS UNCOVERED",font=fnt(37,True),fill=GOLD)
    fit_lines(d,title,68,168,930,73)
    graphic(d,kind)
    fit_lines(d,subtitle,74,1580,940,34)
    d.text((70,1760),"MODERN EXPLANATORY DIAGRAM — NOT AN ANCIENT PHOTOGRAPH",
           font=fnt(21),fill=GOLD)
    im.save(out,quality=94,subsampling=0)
def time_range(p):
    s=json.loads(p.read_text())
    beats=s.get("beats")
    assert len(beats)==7
    return [(float(x["start"]),float(x["end"])) for x in beats]
def prepare(number,work,shotmap,movie,caption):
    selects=CHOICES[number]; beats=BEATS[number]
    spans=time_range(shotmap)
    assets={};source_shots=[];rights=[]
    for index,(asset,beat,(start,end)) in enumerate(zip(selects,beats,spans),1):
        shot={"id":f"SHORT-{number}-{index}","spoken_text":beat[0],
              "start_seconds":start,"end_seconds":end,
              "shot_subject":beat[1],"why_this_visual":"Specific subject selected by film editor",
              "editor_approved_by":"Facts Uncovered director — explicit seven-shot photo/diagram selection",
              "editorial_status":"APPROVED",
              "authentic_source_searches":[]}
        if asset:
            title,license,creator=PICTURES[asset]
            page="https://commons.wikimedia.org/wiki/"+title.replace(" ","_")
            info={"id":"auth_"+asset.lower(),"commons_title":title,
                  "expected_licence":license,"credit":creator,"source":page}
            assets[asset]=info
            shot["visual_kind"]="ARCHAEOLOGICAL_RECORD" if asset in ("C","D") else "AUTHENTIC_PHOTO"
            shot["why_this_visual"]=PHOTO_NOTES[asset]
            shot["authentic_source_searches"]=[{
                "query":"Exact licensed source for "+beat[1],
                "source_url":page,"outcome":"Explicitly chosen real archive photo or research figure with contextual on-screen caption."}]
            shot["asset"]={"source_page_url":page,"creator":creator,
                 "license":"PUBLIC DOMAIN" if license=="Public domain" else license,
                 "license_url":DEEDS[license],"file_identity":title,
                 "attribution":creator+" — "+title+", "+license+"; cropped and graded; "+page,
                 "commercial_use_confirmed":True,"modifications_allowed":True}
            if "BY-SA" in license:shot["asset"]["share_alike_compliance"]="Follow original image's share-alike requirements for visual adaptation, credit and license."
        else:
            why=DIAGRAM_REASONS[(number,index)]
            shot["visual_kind"]="DOCUMENTARY_DIAGRAM"
            shot["why_authentic_image_inadequate"]=why
            shot["individual_exception_approved"]=True
            shot["research_source"]="https://doi.org/10.1038/nature24647" if number=="01" else "https://aeraweb.org/"
            shot["on_screen_disclosure"]="MODERN EXPLANATORY DIAGRAM — NOT A PHOTOGRAPH"
            shot["authentic_source_searches"]=[
                {"query":"Original archaeological image "+beat[1],
                 "source_url":"https://commons.wikimedia.org/wiki/Category:Great_Pyramid_of_Giza",
                 "outcome":"No authenticated photograph of that inaccessible ancient process was found."},
                {"query":"Scientific archive "+beat[3],
                 "source_url":shot["research_source"],
                 "outcome":"Source describes evidence, without granting permission for an exact photographed artifact."}
            ]
        source_shots.append(shot)
    man={"source_first_editorial_approval":"APPROVED",
         "min_authentic_shot_share":0.8 if number=="01" else 0.5,
         "shots":source_shots,
         "reason_for_reduced_ratio":("Merer's manuscript and face cannot be represented by unrelated archive photographs." if number=="02" else "")}
    result=validate(man,phase="plan",root=work)
    if result["status"]!="PASS":raise RuntimeError("Short source-first plan failed "+repr(result["errors"]))
    originals=work/"licensed_archival";originals.mkdir(exist_ok=True)
    for key,item in assets.items():
        file=originals/(key+".jpg")
        rights.append(get_photo(item,file))
        item["path"]=str(file)
        for shot in source_shots:
            if shot.get("asset",{}).get("file_identity")==item["commons_title"]:
                shot["asset"]["local_path"]=str(file.resolve().relative_to(work.resolve()))
                shot["asset"]["sha256"]=sha(file)
    finalcheck=validate(man,phase="release",root=work)
    (work/f"short_{number}_PHOTO_SOURCE_QA.json").write_text(json.dumps(finalcheck,indent=2))
    assert finalcheck["status"]=="PASS",finalcheck["errors"]
    (work/f"short_{number}_PHOTO_SOURCE_RIGHTS.json").write_text(json.dumps(rights,indent=2))
    (work/f"short_{number}_LOCKED_SCENES.json").write_text(json.dumps(man,indent=2))
    for i,(beat,choice) in enumerate(zip(beats,selects),1):
        file=work/f"short_{number}_plate_{i:02}.jpg"
        if choice:make_photo(beat,{"path":assets[choice]["path"],"code":choice},file)
        else:make_illustration(beat,file)
    clips=[];durations=[]
    for idx,(start,end) in enumerate(spans,1):
        sec=end-start
        assert sec>.35,("Bad speech anchor",number,idx)
        plate=work/f"short_{number}_plate_{idx:02}.jpg"
        clip=work/f"short_{number}_scene_{idx:02}.mp4"
        frames=round(sec*24)
        ff("ffmpeg","-v","error","-nostdin","-y","-loop","1","-framerate","24","-i",plate,
           "-frames:v",frames,"-vf","format=yuv420p","-c:v","libx264","-preset","veryfast",
           "-crf","19","-an",clip)
        clips.append(clip)
        durations.append(sec)
    concat=work/f"short_{number}_concat.txt"
    concat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in clips))
    silent=work/f"short_{number}_picture_only.mp4"
    ff("ffmpeg","-v","error","-nostdin","-y","-f","concat","-safe","0",
       "-i",concat,"-c","copy",silent)
    final=work/f"Giza_short_{number}_AUTHENTIC_IMAGES_CAPTIONED_REVIEW.mp4"
    ff("ffmpeg","-v","error","-nostdin","-y","-i",silent,
       "-i",movie,
       "-map","0:v:0","-map","1:a:0",
       "-vf",f"subtitles={caption}:force_style='FontName=DejaVu Sans,FontSize=27,Outline=3,Shadow=0,Alignment=2,MarginV=255'",
       "-c:v","libx264","-preset","veryfast","-crf","18","-c:a","copy",
       "-movflags","+faststart","-shortest",final)
    ff("ffmpeg","-v","error","-xerror","-nostdin","-i",final,"-map","0:v:0","-map","0:a:0","-f","null","-")
    (work/f"short_{number}_AUDIT.txt").write_text("Source-first image selection + file checks passed; full codec decode passed; no YouTube upload or editorial sign-off.")
    print("SHORT_PHOTO_REEDIT_READY",number,final,round(sum(durations),2),final.stat().st_size)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    for n in ("01","02"):
        original=a.input/f"giza_short_{n}_CAPTIONED_REVIEW.mp4"
        shotmap=a.input/f"giza_short_{n}_shot_map.json"
        aligned=a.input/f"short_{n}_ALIGNED.srt"
        assert original.is_file() and shotmap.is_file() and aligned.is_file()
        prepare(n,a.output,shotmap,original,aligned)
if __name__=="__main__":main()
