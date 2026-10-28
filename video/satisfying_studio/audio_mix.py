#!/usr/bin/env python3
"""Frame-accurate ASMR mixing from manually chosen licensed Foley recordings.

No automatic sound matching, no synthesizer pretending to be tactile Foley.
The editor must audition every clip and review the completed audiovisual master.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path

EXTENSIONS={".wav",".ogg",".mp3",".flac"}

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(262144),b""):h.update(chunk)
    return h.hexdigest()

def mix(manifest_path,output_path):
    manifest_path=Path(manifest_path).resolve()
    root=manifest_path.parent
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    fps=manifest.get("fps")
    duration=manifest.get("duration_seconds")
    cues=manifest.get("cues")
    if type(fps) not in (int,float) or not 1<=fps<=120:raise ValueError("Invalid fps")
    if type(duration) not in (int,float) or not 1<=duration<=180:raise ValueError("Invalid duration")
    if not isinstance(cues,list) or not cues:raise ValueError("No manually selected Foley cues")
    files=[]
    filters=[f"anullsrc=channel_layout=stereo:sample_rate=48000:d={duration}[bed]"]
    labels=["[bed]"]
    for i,c in enumerate(cues):
        p=Path(c["file"])
        if p.is_absolute() or ".." in p.parts:raise ValueError("Foley paths must be relative to manifest")
        p=(root/p).resolve()
        if not p.is_file() or p.suffix.lower() not in EXTENSIONS:raise ValueError("Missing recorded Foley "+str(p))
        if sha256(p)!=c.get("sha256"):raise ValueError("Foley file changed; its real source must be re-reviewed")
        if c.get("license") not in ("CC0","CC BY 4.0","original"):raise ValueError("License approval missing")
        if not isinstance(c.get("source_url"),str) or len(c["source_url"])<12:raise ValueError("Exact source URL required")
        frame=c.get("frame")
        if type(frame)!=int or not 0<=frame<round(fps*duration):raise ValueError("Invalid impact/contact frame")
        gain=c.get("gain_db",-6)
        if type(gain) not in (int,float) or not -45<=gain<=6:raise ValueError("Gain out of bounds")
        length=c.get("max_length_seconds",3.0)
        if type(length) not in (int,float) or not .02<=length<=10:raise ValueError("Invalid cue length")
        delay=round(frame/fps*1000)
        files+=["-i",str(p)]
        filters.append(
           f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{length},"
           f"asetpts=PTS-STARTPTS,volume={gain}dB,adelay={delay}:all=1[c{i}]")
        labels.append(f"[c{i}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:duration=first:dropout_transition=0,alimiter=limit=0.90[out]")
    out=Path(output_path).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        *files,"-filter_complex",";".join(filters),"-map","[out]","-ac","2",
        "-ar","48000","-c:a","pcm_s24le","-t",str(duration),str(out)],
        check=True,timeout=90)
    print("EDIT-READY 48KHZ FOLEY MIX",str(out))
    print("NOT REVIEWED: listen through headphones and check frame/audio sync before approval")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("manifest")
    p.add_argument("output")
    a=p.parse_args()
    mix(a.manifest,a.output)
