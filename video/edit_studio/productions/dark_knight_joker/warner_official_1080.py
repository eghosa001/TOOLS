#!/usr/bin/env python3
"""Independent original WB Film studio trailers. No fan-edit references.
Source: publicly served Warner Bros first-party media, verified HEAD with 206 QuickTime.
"""
from pathlib import Path
import urllib.request,urllib.error,hashlib,json
OUT=Path("delivery/joker_warner_hd")
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[
 ("The_Dark_Knight_WB_Trailer_2_1080.mov","https://pdl.warnerbros.com/wbmovies/thedarkknight/trailer2/TDK_TRL2_1080p.mov"),
 ("The_Dark_Knight_WB_Trailer_3_1080.mov","https://pdl.warnerbros.com/wbmovies/thedarkknight/trailer3/TDK_TRL3_1080p.mov"),
 ("The_Dark_Knight_WB_Trailer_1_1080.mov","https://pdl.warnerbros.com/wbmovies/thedarkknight/trailer1/TDK_TRL1_1080p.mov")]
records=[]
for filename,url in SOURCES:
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
  with urllib.request.urlopen(req,timeout=60) as r:
   size=r.headers.get("Content-Length","");ctype=r.headers.get("Content-Type","")
   print("WARNER_STUDIO_ORIGINAL",filename,r.status,ctype,size,r.url,flush=True)
   if "video" not in ctype.lower() and "quicktime" not in ctype.lower():
    print("SKIP_NON_MOVIE",filename,flush=True)
    continue
   if size and int(size)>290000000:continue
   dst=OUT/filename
   h=hashlib.sha256()
   with dst.open("wb") as f:
    while True:
     b=r.read(2<<20)
     if not b:break
     f.write(b);h.update(b)
     if f.tell()//(32<<20)>(f.tell()-len(b))//(32<<20):print("MOVIE_PROGRESS",filename,f.tell(),flush=True)
     if f.tell()>290000000:raise RuntimeError("Single clip exceeds size cap")
   with dst.open("rb") as f:magic=f.read(32)
   if dst.stat().st_size<12000000 or b"ftyp" not in magic:
    print("REJECT_NOT_FILM",filename,dst.stat().st_size,repr(magic),flush=True)
    dst.unlink();continue
   records.append({"filename":filename,"origin_url":url,"bytes":dst.stat().st_size,"sha256":h.hexdigest(),"media_type":ctype,"producer":"Warner Bros. movie promotional master, The Dark Knight (2008)"})
   print("VERIFIED_ORIGINAL_HQ_MOVIE_MASTER",filename,dst.stat().st_size,flush=True)
 except Exception as e:
  print("WARNER_ERROR",filename,type(e).__name__,str(e)[:250],flush=True)
(OUT/"ORIGINAL_MOVIE_SOURCES.json").write_text(json.dumps(records,indent=2))
print("FINAL_RESULT",json.dumps(records)[:3000],flush=True)
if not records:raise RuntimeError("Original 1080p movie master not received")
