#!/usr/bin/env python3
"""Temporary editorial contact sheets of verified licensed Ronaldo goal archive."""
from pathlib import Path
import base64,hashlib,json,subprocess
SRC=Path("football_edit_source/ronaldo_48_goals_2014_15.ogv")
OUT=Path("video/football_edits/reviews")
OUT.mkdir(parents=True,exist_ok=True)
h=hashlib.sha1(SRC.read_bytes()).hexdigest()
if h!="6a75c744421acb76b827441fd9967d778cc19a4a":
    raise RuntimeError("Source rights hash mismatch")
for i,(start,length) in enumerate([(0,54),(54,54),(108,54)]):
    jpg=OUT/f"ronaldo_contact_{i}.jpg"
    vf=("fps=2/3,scale=300:169:flags=bicubic,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "text='%{pts\\:hms}':x=10:y=10:fontsize=22:fontcolor=white:"
        "box=1:boxcolor=black@0.75,"
        "tile=6x6:padding=2:margin=2:color=black")
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-ss",str(start),"-t",str(length),"-i",str(SRC),
                    "-vf",vf,"-frames:v","1","-q:v","6",str(jpg)],check=True,timeout=250)
    (OUT/f"ronaldo_contact_{i}.b64.txt").write_text(base64.b64encode(jpg.read_bytes()).decode("ascii"))
    print("CONTACT",i,"RANGE",start,start+length,"BYTES",jpg.stat().st_size,flush=True)
(OUT/"source_preview_rights.json").write_text(json.dumps({
    "sha1":h,"creator":"Real Madrid","rights":"CC BY 3.0",
    "source":"https://commons.wikimedia.org/wiki/File:All_48_goals_of_Cristiano_Ronaldo,_in_35_league_matches_for_Real_Madrid_(2014-15).ogv",
    "editorial_note":"Timestamp contact sheet is for manually reviewing scene timing; no approval inferred",
},indent=2))
