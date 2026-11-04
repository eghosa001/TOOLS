#!/usr/bin/env python3
"""Prepare human-composed phonk instrumental for original Joker fan-edit."""
import urllib.request,json,hashlib,subprocess
from pathlib import Path
OUT=Path("delivery/joker_music");OUT.mkdir(parents=True,exist_ok=True)
url="https://cdn.pixabay.com/download/audio/2026/10/14/audio_3d633891cf.mp3?filename=kulakovka-gym-phonk-620567.mp3"
dest=OUT/"Gym_PhonK_Kulakovka.mp3"
req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://pixabay.com/music/phonk-gym-phonk-620567/"})
with urllib.request.urlopen(req,timeout=45) as r,dest.open("wb") as f:
 while True:
  b=r.read(1<<20)
  if not b:break
  f.write(b)
if dest.stat().st_size<500000:raise RuntimeError("No original music downloaded")
info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(dest)]))
dur=float(info["format"]["duration"])
assert 82<=dur<=92,dur
(OUT/"soundtrack_provenance.json").write_text(json.dumps({
"author":"Kulakovka","track":"Gym Phonk","music_page":"https://pixabay.com/music/phonk-gym-phonk-620567/",
"media_file":url,"media_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
"duration":dur,"AI_generated":False,
"right_to_use":"https://pixabay.com/service/license-summary/"
},indent=2))
print("REAL_TRACK_AVAILABLE",dur,dest.stat().st_size,flush=True)
