#!/usr/bin/env python3
"""Readable YouTube Shorts captions without FFmpeg/libass dependency.
Run after rendering silent-of-captions vertical Shorts. Keeps 1080x1920 layout.
"""
import argparse, pathlib, re, subprocess
from PIL import Image,ImageDraw,ImageFont
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def second(value):
    h,m,s=value.replace(",",".").split(":")
    return int(h)*3600+int(m)*60+float(s)
def parse(path):
    txt=pathlib.Path(path).read_text(encoding="utf-8-sig")
    cues=[]
    for block in re.split(r"\n\s*\n",txt.strip()):
        lines=block.strip().splitlines()
        i=next((j for j,v in enumerate(lines) if " --> " in v),None)
        if i is None:continue
        a,b=lines[i].split(" --> ",1)
        words=" ".join(lines[i+1:]).strip()
        if words:cues.append((second(a),second(b),words))
    if not cues:raise RuntimeError("Empty captions")
    for i,(start,end,_) in enumerate(cues):
        assert 0<=start<end and (i==0 or start>=cues[i-1][0]),"Captions out of order"
    return cues
def plate(text,path):
    w,h=1080,320
    im=Image.new("RGBA",(w,h),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((42,4,1038,308),radius=20,fill=(4,12,22,242))
    size=41
    while True:
        f=ImageFont.truetype(FONT,size);lines=[];chunk=""
        for word in text.split():
            candidate=(chunk+" "+word).strip()
            if d.textbbox((0,0),candidate,font=f)[2]>930 and chunk:
                lines.append(chunk);chunk=word
            else:chunk=candidate
        if chunk:lines.append(chunk)
        if len(lines)<=3 or size<=27:break
        size-=2
    assert len(lines)<=3,lines
    top=max(22,(h-len(lines)*(size+14))//2)
    for j,line in enumerate(lines):
        length=d.textbbox((0,0),line,font=f)[2]
        d.text(((w-length)//2,top+j*(size+14)),line,font=f,fill=(253,253,253,255),stroke_width=2,stroke_fill=(0,0,0,255))
    im.save(path,optimize=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("video");p.add_argument("subtitles");p.add_argument("output");p.add_argument("--work",default=None)
    a=p.parse_args()
    dest=pathlib.Path(a.output);work=pathlib.Path(a.work or str(dest)+".overlays");work.mkdir(parents=True,exist_ok=True)
    cues=parse(a.subtitles)
    for i,(_,_,t) in enumerate(cues):plate(t,work/f"subtitle_{i:03d}.png")
    ins=["-i",a.video]
    filters=[];previous="[0:v]"
    for i,(start,end,_) in enumerate(cues):
        ins.extend(["-loop","1","-framerate","24","-i",str(work/f"subtitle_{i:03d}.png")])
        following=f"[out{i+1}]"
        filters.append(f"{previous}[{i+1}:v]overlay=x=0:y=1510:enable='between(t,{start:.3f},{end:.3f})':eof_action=repeat{following}")
        previous=following
    args=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",*ins,
          "-filter_complex",";".join(filters),"-map",previous,"-map","0:a:0",
          "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
          "-c:a","copy","-shortest","-movflags","+faststart",str(dest)]
    subprocess.run(args,check=True,timeout=700)
    assert dest.stat().st_size>600000
    print("CAPTIONS_RENDERED",len(cues),dest.stat().st_size,flush=True)
if __name__=="__main__":main()
