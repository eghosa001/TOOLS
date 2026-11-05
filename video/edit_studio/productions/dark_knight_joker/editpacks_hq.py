#!/usr/bin/env python3
"""Follow the public site's own free 15-second download flow. No paid bypass."""
import urllib.request,urllib.parse,html,http.cookiejar,re,os,hashlib,json,time
from pathlib import Path
BASE="https://editpacks.org";OUT=Path("delivery/joker_native_hd");OUT.mkdir(parents=True,exist_ok=True)
jar=http.cookiejar.CookieJar()
openurl=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36"}
items=[("joker_mob_1080",1176,"joker-scenepack"),("joker_interrogation_4k",4190,"joker-vs-batman-prison-clip"),("joker_explosion_4k",4195,"joker-the-explosion-clip")]
results=[]
for name,num,slug in items:
 try:
  page=f"{BASE}/i/{num}/{slug}"
  with openurl.open(urllib.request.Request(page,headers=headers),timeout=40) as r:
   body=r.read().decode("utf8","ignore")
  link=re.search(r'/dl/'+str(num)+r'\?s=[0-9a-f]+(?:&amp;|&)t=\d+',body)
  if not link:raise RuntimeError("Free download entry not found")
  entry=BASE+html.unescape(link.group(0))
  with openurl.open(urllib.request.Request(entry,headers={**headers,"Referer":page}),timeout=40) as r:
   gate=r.read().decode("utf8","ignore")
  print("GATE_PAGE",name,len(gate),flush=True)
  # The 15-second page delivers an official public URL in its Next.js payload.
  match=re.search(r'/api/dl/'+str(num)+r'\?s=[a-f0-9]+\\u0026t=\d+\\u0026g=[a-f0-9]+',gate)
  if not match:
   match=re.search(r'/api/dl/'+str(num)+r'\?s=[a-f0-9]+&amp;t=\d+&amp;g=[a-f0-9]+',gate)
  if not match:
   snippets=[gate[max(0,m.start()-30):m.start()+250] for m in list(re.finditer("/api/dl",gate))[:2]]
   raise RuntimeError("Timed endpoint unavailable "+repr(snippets))
  endpoint=BASE+html.unescape(match.group(0).replace("\\u0026","&"))
  print("GATE_WAIT_BEGIN",name,flush=True)
  time.sleep(16)
  req=urllib.request.Request(endpoint,headers={**headers,"Referer":entry})
  with openurl.open(req,timeout=120) as response:
   print("DOWNLOAD_HTTP",name,response.status,response.headers.get("Content-Type"),response.headers.get("Content-Length"),response.url[:350],flush=True)
   target=OUT/(name+".mp4")
   with target.open("wb") as f:
    while True:
     b=response.read(2<<20)
     if not b:break
     f.write(b)
     if f.tell()>900_000_000:raise RuntimeError("Source exceeds 900 MB cap")
   size=target.stat().st_size
   with target.open("rb") as f:magic=f.read(256)
   if not (b"ftyp" in magic or magic[:4]==b"\x1aE\xdf\xa3") or size<3_000_000:
    raise RuntimeError("Response is not actual high-resolution video; size "+str(size)+" head "+repr(magic[:85]))
   sha=hashlib.sha256(target.read_bytes()).hexdigest()
   results.append({"name":name,"status":"ACTUAL_VIDEO","size":size,"sha256":sha,"source":page,"file":target.name})
   print("ACTUAL_MOVIE_CLIP_RECEIVED",name,size,sha,flush=True)
 except Exception as err:
  print("SOURCE_ERR",name,repr(err),flush=True)
  results.append({"name":name,"status":"ERR","reason":str(err)[:500]})
(OUT/"SOURCES.json").write_text(json.dumps(results,indent=2))
if not any(i["status"]=="ACTUAL_VIDEO" for i in results):raise RuntimeError("No native-HD scene video could be retrieved")
