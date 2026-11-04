#!/usr/bin/env python3
"""Live-action Warner/DC movie scene downloads, NOT preedited fan edits."""
import subprocess,shutil,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path("delivery/joker_scenes");OUT.mkdir(parents=True,exist_ok=True)
VIDEOS=[
 ("interrogation_dc","https://www.youtube.com/watch?v=co2bs_OjLG8"),
 ("joker_bank_heist","https://www.youtube.com/watch?v=Dbvj1prhdr8"),
 ("interrogation_alt","https://www.youtube.com/watch?v=K7ZUy7eKK70")]
def info(path):return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)]))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dl(name,url):
 for client in ["default","android","web"]:
  try:
   dest=OUT/(name+".mp4")
   for f in OUT.glob(name+".*"):
    if f.suffix.lower() not in (".jpg",):f.unlink()
   args=["yt-dlp","--no-playlist","--no-progress","--no-warnings","--retries","2","--socket-timeout","20",
      "--format","bv*[height<=1080]+ba/b[height<=1080]/best","--merge-output-format","mp4",
      "-o",str(dest)]
   if client!="default":args.extend(["--extractor-args",f"youtube:player_client={client}"])
   args.append(url)
   p=subprocess.run(args,capture_output=True,text=True,timeout=190)
   if p.returncode==0 and dest.is_file() and dest.stat().st_size>2000000:
    return str(dest),client
   print("YT_SOURCE_ATTEMPT",name,client,p.returncode,p.stderr[-600:],flush=True)
  except Exception as exc:print("YT_SOURCE_ERROR",name,client,str(exc),flush=True)
 return None,None
items=[]
for name,url in VIDEOS:
 file,client=dl(name,url)
 if file:
  i=info(file);duration=float(i["format"]["duration"])
  items.append({"file":file,"url":url,"name":name,"duration":duration,"sha256":digest(Path(file)),"client":client})
  print("SOURCE_OK",name,duration,flush=True)
if not items:raise RuntimeError("No original film clips downloaded; do not substitute user references")
w,h=300,170
for item in items:
 i=item["name"];p=Path(item["file"]);dur=item["duration"];cnt=40
 sheet=Image.new("RGB",(5*w,8*(h+25)),(20,20,24));d=ImageDraw.Draw(sheet)
 for n in range(cnt):
  t=2+n*(max(0,dur-4)/(cnt-1))
  dst=OUT/(f"_{i}_{n}.jpg")
  subprocess.run(["ffmpeg","-v","error","-nostdin","-y","-ss",str(round(t,2)),"-i",str(p),"-frames:v","1","-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2","-q:v","4",str(dst)],check=True,timeout=20)
  with Image.open(dst) as im:sheet.paste(im.convert("RGB"),((n%5)*w,(n//5)*(h+25)))
  d.text(((n%5)*w+7,(n//5)*(h+25)+h+4),f"{t:05.1f}s",fill="white")
  dst.unlink()
 sheet.save(OUT/(i+"_CONTACT.jpg"),quality=83)
(OUT/"SOURCES.json").write_text(json.dumps(items,indent=2))
print("FILM_CLIPS_READY",len(items),flush=True)
