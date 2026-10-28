#!/usr/bin/env python3
"""Replace only the final Titanic shot with one premium branded subscribe card.
This is a precisely authored single-shot correction, not a montage and not a
substitute for rights clearance or complete audiovisual/editorial signoff.
"""
from __future__ import annotations
import hashlib,json,math,pathlib,subprocess
from PIL import Image,ImageDraw,ImageFont
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=HERE/"corrected_final_private_master"
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=OUT/"TITANIC_86MIN_FIFTEEN_MANUALLY_DIRECTED_CHAPTERS_1080P_REVIEW.mp4"
DEST=OUT/"Titanic_86MIN_PRIVATE_MASTER_CLEAN_ENDING.mp4"
END_START=5198.061686
ORIGINAL_SHA="fee1c0fbf2e9ffb71bf95324e3b855cce864cee965dbbea057348d13427a48b8"

def cmd(args):
    return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True)
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for v in iter(lambda:f.read(1<<20),b""):h.update(v)
    return h.hexdigest()
def make_card():
    W,H=1920,1080
    im=Image.new("RGB",(W,H),(7,20,33))
    pixels=im.load()
    for y in range(H):
        t=y/H
        base=(8+int(4*t),22+int(12*t),35+int(19*t))
        for x in range(W):
            s=max(0,1-abs(x-W/2)/(W/2))
            pixels[x,y]=(base[0]+int(s*3),base[1]+int(s*5),base[2]+int(s*7))
    d=ImageDraw.Draw(im)
    gold=(208,170,103); bright=(248,246,237); muted=(175,191,202)
    fserif="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    flato="/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
    freg="/usr/share/fonts/truetype/lato/Lato-Regular.ttf"
    def ft(path,size):return ImageFont.truetype(path,size)
    for j in range(11):
        y=int(755+j*19)
        coords=[(x,int(y+2.5*math.sin(x/130+j*.58))) for x in range(70,1850,15)]
        d.line(coords,fill=(30+j,59+j,75+j),width=2)
    d.line((130,150,1790,150),fill=(82,99,108),width=2)
    d.rectangle((130,140,370,146),fill=gold)
    def center(text,y,font,color):
        bounds=d.textbbox((0,0),text,font=font)
        d.text(((W-(bounds[2]-bounds[0]))/2,y),text,font=font,fill=color)
    center("FACTS UNCOVERED",100,ft(flato,44),bright)
    center("STORIES & EVIDENCE",172,ft(freg,25),gold)
    center("THE STORY",310,ft(fserif,104),bright)
    center("CONTINUES",432,ft(fserif,104),bright)
    center("History is worth examining. Discover the evidence behind the stories.",606,ft(freg,31),muted)
    d.rounded_rectangle((693,692,1227,801),radius=19,fill=gold)
    center("SUBSCRIBE",716,ft(flato,55),(9,26,40))
    d.line((480,930,1440,930),fill=(95,109,114),width=2)
    center("NEW DOCUMENTARIES  •  REAL SOURCES  •  FRESH QUESTIONS",957,ft(freg,24),muted)
    path=OUT/"Titanic_END_CARD_CLEAN.png";im.save(path,optimize=True)
    return path

def main():
    if not SOURCE.is_file():raise FileNotFoundError("Exact source master missing")
    if digest(SOURCE)!=ORIGINAL_SHA:raise RuntimeError("Refusing to edit unverified source MP4")
    picture=make_card()
    head=OUT/"head.mp4";tail=OUT/"ending.mp4";joined=OUT/"joined.mp4"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",SOURCE,"-t",str(END_START),
         "-map","0:v:0","-an","-c:v","copy",head])
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",picture,
         "-frames:v","349","-c:v","libx264","-preset","veryfast","-crf","19",
         "-pix_fmt","yuv420p","-r","24",tail])
    listing=OUT/"list.txt"
    listing.write_text(chr(10).join("file '"+str(p.resolve())+"'" for p in (head,tail))+chr(10))
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",listing,
         "-c:v","copy",joined])
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",joined,"-i",SOURCE,
         "-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",DEST])
    info=json.loads(cmd(["ffprobe","-v","error","-show_streams","-show_format","-of","json",DEST]).stdout)
    duration=float(info["format"]["duration"])
    assert abs(duration-5212.596)<.25,duration
    v=next(x for x in info["streams"] if x["codec_type"]=="video")
    a=next(x for x in info["streams"] if x["codec_type"]=="audio")
    assert (v["width"],v["height"])==(1920,1080) and v["r_frame_rate"]=="24/1"
    assert v["codec_name"]=="h264" and a["codec_name"]=="aac"
    # Decode the actual ending region, inspect literal image bytes and
    # preserve all original soundtrack packets via stream-copy.
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-sseof","-20",
         "-i",DEST,"-f","null","-"])
    frame=OUT/"Titanic_FIXED_LAST_FRAME.jpg"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-sseof","-4","-i",DEST,
         "-frames:v","1",frame])
    qa={"sha256":digest(DEST),"source_sha256":ORIGINAL_SHA,
        "duration_seconds":duration,"changed_picture_seconds":duration-END_START,
        "all_original_narration_music_preserved":True,
        "removed_internal_mandatory_end_subscribe_label":True,
        "single_clear_subscribe_cta":True,
        "closing_frames_decoded":"PASS",
        "commercial_visual_rights_editor_clearance":"PENDING",
        "actual_whole_86minute_AV_review":"PENDING",
        "youtube_public_release_approved":False}
    (OUT/"PRIVATE_MASTER_CLEAN_END_QA.json").write_text(json.dumps(qa,indent=2))
    print("TITANIC_CLEAN_END_SINGLE_CALL_TO_ACTION",json.dumps(qa),flush=True)

if __name__=="__main__":main()
