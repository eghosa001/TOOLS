#!/usr/bin/env python3
"""Source higher-fidelity original film trailer/scene footage from Dailymotion streams."""
from pathlib import Path
import subprocess,urllib.request,json,hashlib
P=Path("delivery/hq_dark_knight");P.mkdir(parents=True,exist_ok=True)
exe=P/"yt-dlp"
with urllib.request.urlopen("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp",timeout=60) as r,exe.open("wb") as f:
 while True:
  b=r.read(1<<20)
  if not b:break
  f.write(b)
exe.chmod(0o755)
urls=[
 ("bank_imax","https://www.dailymotion.com/video/x9c10j0"),
 ("wb100_trailer","https://www.dailymotion.com/video/x8oju3i"),
 ("hd_trailer_1080","https://www.dailymotion.com/video/x7pqwh0"),
 ("theatrical_trailer","https://www.dailymotion.com/video/x9sl4no")]
results=[]
for name,url in urls:
 p=P/(name+".mp4")
 cmd=[str(exe),"--no-progress","--no-playlist","--hls-prefer-native",
    "-f","best[height<=1080]/best","--no-warnings","--socket-timeout","15","--retries","1","-o",str(p),url]
 try:
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=220)
  print("HQ_SCAN",name,r.returncode,r.stderr[-250:],r.stdout[-180:],flush=True)
  if r.returncode==0 and p.is_file() and p.stat().st_size>800000:
   results.append({"file":p.name,"source":url,"bytes":p.stat().st_size})
 except Exception as e:print("HQ_FAIL",name,str(e),flush=True)
if not results:raise RuntimeError("No HD film footage acquired")
(P/"SOURCE_LEDGER.json").write_text(json.dumps(results,indent=2))
print("HQ_ORIGINAL_FILM_READY",len(results),flush=True)
