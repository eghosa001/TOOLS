#!/usr/bin/env python3
"""Bounded statistical inspection of an explicitly selected PNG sequence.

Uses free Pillow if present. No model is installed and this cannot judge art.
A held frame in a drawn cartoon may be intentional: duplicate warnings NEVER
grant/revoke artistic approval.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def sample_frames(folder:Path,max_samples=24)->dict:
    from PIL import Image,ImageStat
    paths=sorted(folder.glob("frame_*.png"))
    if not paths:
        return {"frame_count":0,"sampled_count":0,"near_black_samples":0,
                "constant_sampled_sequence":False,"sampled_frames":[]}
    n=min(max_samples,len(paths))
    samples=[paths[round(i*(len(paths)-1)/(n-1))] for i in range(n)] if n>1 else [paths[0]]
    result=[]
    for path in samples:
        with Image.open(path) as im:
            im=im.convert("RGB")
            size=list(im.size)
            im.thumbnail((160,90))
            pixels=im.tobytes()
            mean=sum(ImageStat.Stat(im).mean)/3/255
            result.append({"name":path.name,"width":size[0],"height":size[1],
                           "mean_brightness":round(mean,4),
                           "visual_hash":hashlib.sha256(pixels).hexdigest()[:16]})
    return {"frame_count":len(paths),"sampled_count":len(samples),
            "near_black_samples":sum(row["mean_brightness"]<0.015 for row in result),
            "constant_sampled_sequence":len(result)>2 and len(set(x["visual_hash"] for x in result))==1,
            "sampled_frames":result,
            "limitations":["Low-resolution statistical checks only; black intentional fades and held 2D frames are valid",
                           "This does not measure camera continuity, mouth sync, physical plausibility, or artistry"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shot",required=True)
    p.add_argument("--frames",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=sample_frames(args.frames)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({"shots":{args.shot:{"frames":report}}},indent=2)+"\n")
    print(json.dumps({"shot":args.shot,"count":report["frame_count"],
                      "sampled":report["sampled_count"]}))

if __name__=="__main__":main()
