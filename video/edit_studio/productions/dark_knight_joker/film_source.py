#!/usr/bin/env python3
"""Original unedited The Dark Knight promotional movie trailers and shot contact sheets.
The user's previously uploaded fan-edits are NEVER inputs.
"""
import urllib.request,subprocess,json,hashlib,random,time
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path("delivery/dark_knight_source");OUT.mkdir(parents=True,exist_ok=True)
clips=[
 ("dark_knight_trailer1","https://trailers.apple.com/movies/wb/the_dark_knight/the_dark_knight-tlr1_h1080p.mov","https://trailers.apple.com/movies/wb/the_dark_knight/the_dark_knight-tlr1_h720p.mov"),
 ("dark_knight_trailer2","https://trailers.apple.com/movies/wb/the_dark_knight/the_dark_knight-tlr2_h1080p.mov","https://trailers.apple.com/movies/wb/the_dark_knight/the_dark_knight-tlr2_h720p.mov"),
 ("dark_knight_trailer3","https://trailers.apple.com/movies/wb/the_dark_knight/the_dark_knight-tlr3_h1080p.mov","https://trailers.apple.com/movies/wb/the_dark_knight/the_dark_knight-tlr3_h720p.mov")]
def probe(p):
 return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)],timeout=45))
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def download(url,out):
 req=urllib.request.Request(url,headers={"User-Agent":"QuickTime/7.7.9 (qtver=7.7.9;os=Windows NT 6.1Service Pack 1)","Referer":"https://trailers.apple.com/"})
 with urllib.request.urlopen(req,timeout=50) as resp,out.open("wb") as f:
  while True:
   b=resp.read(1<<20)
   if not b: break
   f.write(b)
 if out.stat().st_size<2_000_000:raise RuntimeError("download too small")
 return probe(out)
available=[]
for name,*urls in clips:
 for url in urls:
  p=OUT/(name+".mov")
  try:
   info=download(url,p)
   dur=float(info["format"]["duration"])
   if dur<30:raise ValueError("invalid trailer duration")
   record={"name":name,"source":url,"filename":p.name,"duration":dur,"sha256":sha(p),
   "size":p.stat().st_size,"video_stream":next(s for s in info["streams"] if s["codec_type"]=="video")}
   available.append(record)
   print("MOVIE_TRAILER_OK",name,round(dur,2),p.stat().st_size,url,flush=True)
   break
  except Exception as exc:
   p.unlink(missing_ok=True)
   print("MOVIE_TRAILER_SOURCE_ERR",name,str(exc)[:200],url,flush=True)
 if len(available)>=2:break
if len(available)<1:
 raise RuntimeError("No original film trailer can be accessed; never substitute reference fan-edits")
w,h=320,180
for rec in available:
 name=rec["name"];p=OUT/rec["filename"]
 times=[2.5+i*(rec["duration"]-7)/54 for i in range(55)]
 img=Image.new("RGB",(5*w,11*(h+23)),(20,20,24));dr=ImageDraw.Draw(img)
 for i,t in enumerate(times):
  q=OUT/f"_{name}_{i}.jpg"
  subprocess.run(["ffmpeg","-v","error","-nostdin","-y","-ss",f"{t:.3f}","-i",str(p),"-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2","-frames:v","1","-q:v","4",str(q)],check=True,timeout=30)
  with Image.open(q) as a:img.paste(a.convert("RGB"),((i%5)*w,(i//5)*(h+23)))
  dr.text(((i%5)*w+5,(i//5)*(h+23)+h+2),f"{t:.1f} sec",fill="white")
  q.unlink()
 img.save(OUT/(name+"_CONTACT.jpg"),quality=86)
recfile={"movie":"The Dark Knight (2008)","source_kind":"unedited official promotional motion picture trailer","references_used_as_footage":False,"footage":available}
(OUT/"SOURCE_MANIFEST.json").write_text(json.dumps(recfile,indent=2,default=str))
print("MOVIE_SOURCE_READY",len(available),flush=True)
