#!/usr/bin/env python3
"""NAGA FARMS real-footage Instagram/TikTok dog-brand advert."""
import json
import os
import re
import subprocess
from pathlib import Path

import requests
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/tmp/naga-farms-reel")
ROOT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1920
GOLD = (222, 184, 94)
DARK = (13, 51, 30)
WHITE = (255, 250, 235)
USER_AGENT = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125 Safari/537.36"}
BRAND_URL = os.environ.get("NAGA_BRAND_IMAGE_URL", "")
SCENES = [
    ("garden_puppy", 5877808, "Those little paws."),
    ("happy_puppies", 12768734, "The joy they bring."),
    ("playful_retriever", 7515923, "A little playtime."),
    ("garden_playmates", 9159497, "All that personality."),
    ("loving_dog", 7197660, "For the love of dogs."),
]
TEXT = ("Some moments just make you smile. A curious little face. "
        "A tail that never stops. The energy, the loyalty, the companionship. "
        "That's what we love about dogs. Welcome to Naga Farms. "
        "Follow us on Instagram and TikTok, and send us a message to connect.")

def cmd(*args):
    print("RUN", " ".join(map(str,args))[:260],flush=True)
    subprocess.run(list(map(str,args)), check=True)

def download(url, target):
    target=Path(target)
    with requests.get(url, stream=True, timeout=90, headers=USER_AGENT) as r:
        r.raise_for_status()
        with target.open("wb") as out:
            for block in r.iter_content(chunk_size=1024*1024):
                if block: out.write(block)
    if target.stat().st_size < 10000:
        raise ValueError("Downloaded media too small: "+str(target))
    return target

def video_url_candidates(vid):
    out=[]
    try:
        r=requests.get(f"https://www.pexels.com/video/{vid}/",timeout=15,headers=USER_AGENT)
        if r.ok:
            text=r.text.replace("\\/","/")
            out += re.findall(r"https?://videos\.pexels\.com/video-files/"+str(vid)+r"/[^\"'\s<>]+?\.mp4",text)
    except requests.RequestException: pass
    for fps in ["30","24","25","23.976","29.97","60"]:
        for dimensions in ["1080_1920","720_1280","540_960"]:
            out.append(f"https://videos.pexels.com/video-files/{vid}/{vid}-hd_{dimensions}_{fps}fps.mp4")
    for fps in ["30","24","25"]:
        for dimensions in ["1080_1920","720_1280","540_960"]:
            out.append(f"https://videos.pexels.com/video-files/{vid}/{vid}-sd_{dimensions}_{fps}fps.mp4")
    return list(dict.fromkeys(out))

def clip(name,vid):
    dest=ROOT/(name+".mp4")
    for ix,url in enumerate(video_url_candidates(vid)):
        try:
            with requests.get(url,stream=True,timeout=(12,40),headers=USER_AGENT) as r:
                if not r.ok or r.headers.get("Content-Type","").startswith("text/"):
                    continue
                with dest.open("wb") as fh:
                    for chunk in r.iter_content(1024*1024):
                        if chunk: fh.write(chunk)
            if dest.stat().st_size < 120000: continue
            probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                                  "-show_entries","stream=width,height","-of","csv=p=0",str(dest)],
                                 capture_output=True,text=True)
            if probe.returncode==0 and "," in probe.stdout:
                print("Verified filmed dog clip",vid,name,probe.stdout.strip(),"candidate",ix,flush=True)
                return dest
        except (OSError,requests.RequestException) as exc:
            print("Trying alternate resolution",name,str(exc)[:60],flush=True)
        dest.unlink(missing_ok=True)
    raise RuntimeError(f"Cannot obtain verified Pexels footage {vid} ({name})")

def fnt(size):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",size)

def overlay(phrase,ix):
    image=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(image)
    d.rounded_rectangle((70,1496,1010,1726),radius=24,fill=(10,38,24,202))
    d.rounded_rectangle((105,1521,116,1698),radius=3,fill=GOLD+(255,))
    d.text((146,1535),phrase,font=fnt(57),fill=WHITE+(255,))
    d.text((147,1637),"NAGA FARMS",font=fnt(31),fill=GOLD+(255,))
    p=ROOT/f"overlay-{ix}.png"; image.save(p)
    return p

def create_card(photo):
    bg=Image.new("RGB",(W,H),DARK); d=ImageDraw.Draw(bg)
    if photo:
        with Image.open(photo) as im:
            sq=im.convert("RGB").resize((1000,1000),Image.Resampling.LANCZOS)
        bg.paste(sq,(40,347))
    d=ImageDraw.Draw(bg)
    d.rounded_rectangle((40,347,1040,1347),outline=GOLD,width=5,radius=14)
    d.text((W//2,160),"FOR THE LOVE OF DOGS",font=fnt(50),fill=GOLD,anchor="mm")
    d.line((200,227,880,227),fill=GOLD,width=3)
    d.text((W//2,1480),"NAGA FARMS",font=fnt(85),fill=GOLD,anchor="mm")
    d.text((W//2,1603),"FOLLOW ON INSTAGRAM & TIKTOK",font=fnt(34),fill=WHITE,anchor="mm")
    d.rounded_rectangle((217,1694,863,1806),radius=27,outline=GOLD,width=4)
    d.text((W//2,1752),"SEND US A DM",font=fnt(45),fill=GOLD,anchor="mm")
    p=ROOT/"brand_endcard.png"; bg.save(p)
    return p

def synth():
    from kokoro_onnx import Kokoro
    mdl=download("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.int8.onnx",ROOT/"model.onnx")
    v=download("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin",ROOT/"voices.bin")
    tts=Kokoro(str(mdl),str(v))
    samples,sr=tts.create(TEXT,voice="am_michael",speed=1.06,lang="en-us")
    p=ROOT/"natural_male_voice.wav";sf.write(str(p),samples,sr)
    return p

def main():
    sources=[];problems=[]
    for name,vid,title in SCENES:
        try: sources.append((name,vid,title,clip(name,vid)))
        except Exception as exc: problems.append(str(exc));print("SOURCE_WARNING",exc,flush=True)
    if len(sources)<3:
        raise RuntimeError("At least three genuine licensed dog footage sources required: "+str(problems))
    # Only reuse verified real dog material if a particular source is unavailable.
    while len(sources)<5:
        sources.append(sources[len(sources)%len(sources)])
    pieces=[]
    for ix,(name,vid,title,original) in enumerate(sources[:5]):
        stamp=overlay(title,ix); part=ROOT/f"shot-{ix}.mp4"
        cmd("ffmpeg","-hide_banner","-loglevel","error","-y","-ss","0.3",
            "-i",original,"-loop","1","-i",stamp,
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,fps=30,setsar=1[bg];"
            "[bg][1:v]overlay=0:0:shortest=1[out]",
            "-map","[out]","-t","5","-an","-c:v","libx264","-preset","veryfast",
            "-crf","21","-pix_fmt","yuv420p","-r","30",part)
        pieces.append(part)
    brand=None
    if BRAND_URL:
        try: brand=download(BRAND_URL,ROOT/"user_original_naga_farms.jpg")
        except Exception as exc: print("BRAND_WARNING",str(exc),flush=True)
    card=create_card(brand); ending=ROOT/"ending.mp4"
    cmd("ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1",
        "-i",card,"-t","5","-vf","fps=30,format=yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","20",
        "-pix_fmt","yuv420p",ending)
    pieces.append(ending)
    playlist=ROOT/"playlist.txt"
    playlist.write_text("".join("file '"+str(p)+"'\n" for p in pieces),encoding="utf-8")
    silent=ROOT/"silent_master.mp4"
    cmd("ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe",
        "0","-i",playlist,"-c:v","libx264","-preset","veryfast","-crf","21",
        "-pix_fmt","yuv420p","-r","30","-t","30",silent)
    speech=synth()
    music=download("https://assets.mixkit.co/music/1167/1167.mp3",ROOT/"mixkit_music.mp3")
    final=ROOT/"NAGA_FARMS_DOG_AD_30s_1080x1920.mp4"
    cmd("ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",speech,
        "-i",music,"-filter_complex",
        "[1:a]volume=1.25,adelay=450|450[voice];"
        "[2:a]atrim=0:30,volume=0.12,afade=t=in:st=0:d=1,"
        "afade=t=out:st=27:d=3[bed];"
        "[voice][bed]amix=inputs=2:duration=longest:dropout_transition=0,"
        "alimiter=limit=0.95[a]",
        "-map","0:v:0","-map","[a]","-t","30","-c:v","copy","-c:a","aac",
        "-b:a","192k","-movflags","+faststart",final)
    audit=json.loads(subprocess.check_output(["ffprobe","-v","error",
        "-show_format","-show_streams","-of","json",final]))
    assert 29.5<float(audit["format"]["duration"])<30.5
    assert any(s["codec_type"]=="video" and s["width"]==1080 and s["height"]==1920 for s in audit["streams"])
    assert any(s["codec_type"]=="audio" for s in audit["streams"])
    cmd("ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",final,"-f","null","-")
    (ROOT/"SOURCES_AND_LICENSES.txt").write_text(
        "NAGA FARMS - genuine dog footage, 30-second ad\n\n"
        "Pexels License: https://www.pexels.com/license/\n"+
        "".join(f"https://www.pexels.com/video/{id}/ ({name})\n" for name,id,_,_ in sources[:5])+
        "\nMusic: Close Up, Michael Ramir C, Mixkit #1167\n"
        "https://mixkit.co/license/modal/musicFree/\n"
        "https://assets.mixkit.co/music/1167/1167.mp3\n"
        "Narration: Kokoro / am_michael, Kokoro Apache-2.0 model license\n"
        "The uploaded NAGA FARMS image was used for the brand card if accessible.\n"
        "Stock dog footage is illustrative and is not claimed to be the brand's own animals.\n"
    )
    for ix,at in enumerate([2,7,12,17,22,27]):
        cmd("ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(at),
            "-i",final,"-frames:v","1",ROOT/f"review-{ix}.jpg")
    print("COMPLETE:",str(final),final.stat().st_size,flush=True)

if __name__=="__main__":
    main()
