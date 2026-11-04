#!/usr/bin/env python3
import urllib.request, urllib.parse, pathlib, json, subprocess, time
out=pathlib.Path("delivery/joker_hf_trailer");out.mkdir(parents=True,exist_ok=True)
base="https://huggingface.co/datasets/DanBenAmi/HERBench/resolve/main/videos/trailers/"
names=["The Dark Knight 2008 Official Trailer 1 - Christopher Nolan Movie HD.mp4","The Dark Knight - Official Trailer 2 HD.mp4"]
records=[]
for name in names:
 url=base+urllib.parse.quote(name)+"?download=true"
 try:
  print("SOURCE",url,flush=True)
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
  with urllib.request.urlopen(req,timeout=70) as r:
   data_len=r.headers.get("content-length");typ=r.headers.get("content-type")
   print("HTTP_RESOLVED",r.status,typ,data_len,r.url,flush=True)
   dst=out/("Trailer1.mp4" if "2008 Official" in name else "Trailer2.mp4")
   if data_len and int(data_len)>250000000:continue
   with dst.open("wb") as f:
    while True:
     b=r.read(2<<20)
     if not b:break
     f.write(b)
   print("DOWNLOADED",dst.stat().st_size,flush=True)
   if dst.stat().st_size<3000000:continue
   meta={"source_bytes":dst.stat().st_size,"resolution":"verify after authenticated file transfer"}
   records.append({"file":dst.name,"url":url,"metadata":meta})
 except Exception as exc:print("DOWNLOAD_FAILED",repr(exc)[:1000],flush=True)
(out/"ledger.json").write_text(json.dumps(records,indent=2))
if not records:raise RuntimeError("No HD movie trailer could be downloaded")
