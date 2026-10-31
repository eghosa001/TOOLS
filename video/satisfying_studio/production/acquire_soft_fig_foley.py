#!/usr/bin/env python3
"""Fetch HQ CC0 soft tomato cutting Foley for a realistic FIG-cutting film.
Never source any audio from user-supplied creator reference video.
"""
import re,os,json,hashlib,requests,subprocess
from pathlib import Path
D=Path(os.environ.get("ASMR_SOFT_FOLEY_DIR","/tmp/asmr-natural-fig"));D.mkdir(parents=True,exist_ok=True)
page="https://freesound.org/people/frodeims/sounds/812387/"
r=requests.get(page,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) Chrome/128.0.0.0 Safari/537.36"},timeout=25)
r.raise_for_status()
h=r.text.replace("\\/","/")
if not ("creativecommons.org/publicdomain/zero" in h.lower() or "creative commons 0" in h.lower()):
 raise SystemExit("CC0 was NOT verified from original Freesound source; refuse production")
urls=re.findall(r'https?://cdn\.freesound\.org/previews/812/812387_[0-9]+-hq\.(?:mp3|ogg)',h)
urls=list(dict.fromkeys(urls))
print("candidate urls",urls)
if not urls: raise SystemExit("No Freesound HQ preview URL found")
valid=None
for url in urls:
 try:
  x=requests.get(url,timeout=50);x.raise_for_status()
  if len(x.content)<150000 or len(x.content)>10000000:raise ValueError("unexpected size")
  p=D/("soft_tomato_cut_CC0."+url.split(".")[-1]);p.write_bytes(x.content)
  q=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)],text=True))
  duration=float(q["format"]["duration"])
  if not 17<=duration<=19:raise ValueError(f"bad recording duration {duration}")
  valid={"page":page,"source_author":"frodeims","license":"https://creativecommons.org/publicdomain/zero/1.0/","license_verified_from_original_freesound_html":True,"download_url":url,"artifact_name":p.name,"sha256":hashlib.sha256(x.content).hexdigest(),"duration":duration,"media_type":"HQ public Freesound compressed preview, NOT original studio master","bytes":len(x.content)}
  print("ACQUIRED",json.dumps(valid));break
 except Exception as e:print("candidate failed",str(e)[:250]);p.unlink(missing_ok=True)
if not valid:raise SystemExit("No playable HQ licensed fruit Foley")
(D/"SOUND_RIGHTS.json").write_text(json.dumps(valid,indent=2))
