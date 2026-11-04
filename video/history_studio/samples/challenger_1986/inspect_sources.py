#!/usr/bin/env python3
"""Source-only editorial contact sheets, no synthetic footage."""
import importlib.util, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("candidate",HERE/"produce.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
OUT=Path("delivery/challenger_1986/source_review")
OUT.mkdir(parents=True,exist_ok=True)
for key,meta in mod.SOURCES.items():
    film=mod.download(meta)
    duration=mod.duration(film)
    stamps=list(range(0,int(duration),8))
    grid=Image.new("RGB",(8*256,((len(stamps)+7)//8)*173),(17,17,18))
    for i,t in enumerate(stamps):
        shot=OUT/f"{key}_{i:02}.jpg"
        subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",str(film),
                        "-frames:v","1","-vf","scale=256:144:force_original_aspect_ratio=decrease",
                        str(shot)],check=True,timeout=90)
        im=Image.open(shot).convert("RGB")
        x=(i%8)*256; y=(i//8)*173
        grid.paste(im,(x,y))
        ImageDraw.Draw(grid).text((x+8,y+146),f"{key} | {t}s",fill="white")
        shot.unlink()
    grid.save(OUT/f"{key}_timeline.jpg",quality=88)
    print("SOURCE_CONTACT_SHEET",key,duration)
