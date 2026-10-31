#!/usr/bin/env python3
"""Fetch individual recordings permitted for commercial use. Never synthesize source data."""
import requests,re,os,json,hashlib,subprocess,html
from pathlib import Path
out=Path("/tmp/asmr-real-liquid-sounds");out.mkdir(exist_ok=True)
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"})
candidates=[
 {"name":"splash_mixkit","url":"https://assets.mixkit.co/active_storage/sfx/1311/1311-preview.mp3","page":"https://mixkit.co/free-sound-effects/water/","license":"https://mixkit.co/license/modal/sfxFree/"},
 {"name":"waterbubble_mixkit","url":"https://assets.mixkit.co/active_storage/sfx/1317/1317-preview.mp3","page":"https://mixkit.co/free-sound-effects/glass/","license":"https://mixkit.co/license/modal/sfxFree/"},
 {"name":"pour_pixabay_one","page":"https://pixabay.com/sound-effects/household-slowly-pouring-water-into-a-glass-103858/","license":"https://pixabay.com/service/license-summary/"},
 {"name":"pour_pixabay_two","page":"https://pixabay.com/sound-effects/film-special-effects-pouring-water-191999/","license":"https://pixabay.com/service/license-summary/"},
 {"name":"pour_pixabay_three","page":"https://pixabay.com/sound-effects/household-open-bottle-and-pour-water-into-glass-302352/","license":"https://pixabay.com/service/license-summary/"},
]
ledger=[]
for item in candidates:
 row=item.copy()
 try:
  urls=[row["url"]] if row.get("url") else []
  if not urls:
   page=session.get(row["page"],timeout=25)
   row["page_http"]=page.status_code
   page.raise_for_status()
   raw=html.unescape(page.text).replace("\\/","/")
   guesses=re.findall(r'https?://(?:cdn|media)\.pixabay\.com/(?:download/)?audio/[^"\\\s<>]+?\.(?:mp3|wav)(?:\?[^"\\\s<>]*)?',raw)
   urls=list(dict.fromkeys(guesses))
  row["candidate_urls_found"]=len(urls)
  for u in urls[:6]:
   try:
    r=session.get(u,timeout=35,stream=True,headers={"Referer":row["page"]})
    r.raise_for_status()
    f=out/(row["name"]+".mp3");size=0
    with f.open("wb") as dst:
     for c in r.iter_content(131072):
      if not c:continue
      size+=len(c)
      if size>12_000_000:raise RuntimeError("size guard")
      dst.write(c)
    q=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type","-of","json",str(f)],text=True,capture_output=True,timeout=20,check=True)
    j=json.loads(q.stdout)
    if not any(x["codec_type"]=="audio" for x in j["streams"]) or float(j["format"]["duration"])<.35:raise RuntimeError("invalid sound")
    row.update({"status":"verified","bytes":size,"duration":float(j["format"]["duration"]),"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"url":u})
    print("SUCCESS",row["name"],row["bytes"],row["duration"],flush=True)
    break
   except Exception as e:
    row["last_download_error"]=str(e)
    if (out/(row["name"]+".mp3")).exists():(out/(row["name"]+".mp3")).unlink()
  else:row["status"]="unavailable"
 except Exception as e:
  row["status"]="unavailable";row["error"]=str(e)
 print("RESULT",row["name"],row["status"],row.get("error",row.get("last_download_error")),flush=True)
 ledger.append(row)
(out/"SOURCE_LICENSES.json").write_text(json.dumps(ledger,indent=2))
if not any(a["status"]=="verified" for a in ledger):raise SystemExit("No real audio fetched")
