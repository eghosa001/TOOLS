#!/usr/bin/env python3
"""Acquire only these eight manually chosen, source-page-verified live-action Pexels clips.
No auto editorial selection, no unlicensed University of Kentucky images or film.
This is a technical acquisition step: downloaded clips are still individually reviewed.
"""
import html,json,os,re,subprocess,urllib.request,urllib.error,hashlib
from pathlib import Path
SOURCES=[
 ("vesuvius","27127738","https://www.pexels.com/video/volcano-vesuvius-27127738/","Wal Vas","actual Mount Vesuvius, filmed present day"),
 ("oldbook","11530045","https://www.pexels.com/video/a-person-flipping-pages-of-an-old-book-11530045/","Attila Pergel","modern staged book handling, illustrative"),
 ("scanner","7089946","https://www.pexels.com/video/a-radiologist-operating-a-ct-scan-machine-7089946/","MART PRODUCTION","modern medical scanner analogy; NOT same technique used on scrolls"),
 ("coding","7534244","https://www.pexels.com/video/person-is-typing-using-computer-keyboard-7534244/","Mikhail Nilov","generic modern computation, illustrative"),
 ("researcher","9573565","https://www.pexels.com/video/a-scientist-looking-through-a-microscope-9573565/","Tima Miroshnichenko","modern unrelated laboratory example, not papyrus team"),
 ("archive","8870177","https://www.pexels.com/video/a-man-looking-at-the-books-on-a-shelves-8870177/","MART PRODUCTION","illustrative archive search, not ancient library"),
 ("paper","6746602","https://www.pexels.com/video/a-person-holding-a-book-6746602/","Gül Işık","paper texture in an unrelated old book, illustrative"),
 ("pages","7235016","https://www.pexels.com/video/flipping-pages-of-a-book-7235016/","Artem Podrez","flipping a modern paper book, deliberately contrasts fragility"),
]
OUT=Path("intake_stock");OUT.mkdir(exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36","Referer":"https://www.pexels.com/"}
def get(u,limit=35_000_000):
 req=urllib.request.Request(u,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=22) as resp:
  data=resp.read(limit+1)
  if len(data)>limit:raise ValueError("Oversized clip")
  return data
def candidates(id,page):
 found=[]
 try:
  d=get(page,3_000_000).decode("utf-8","ignore")
  d=html.unescape(d.replace("\\u002F","/").replace("\\/","/"))
  found=re.findall(r"https?://(?:videos|player).pexels.com/video-files/[A-Za-z0-9_/.-]+?\\.mp4(?:\\?[^\\s\"'<]+)?",d)
  print("PAGE",id,"chars",len(d),"links",len(found),flush=True)
 except Exception as e:print("PAGE_ACCESS",id,str(e)[:180],flush=True)
 urls=[]
 for q in ("hd_1920_1080_25fps","hd_1920_1080_30fps","hd_1920_1080_24fps","hd_1920_1080_60fps","hd_1080_1920_25fps","hd_1080_1920_30fps","hd_1280_720_25fps","hd_1280_720_30fps","hd_720_1280_25fps","sd_640_360_25fps"):
  urls.append(f"https://videos.pexels.com/video-files/{id}/{id}-{q}.mp4")
 return list(dict.fromkeys([*found,*urls]))
report=[]
for key,id,page,creator,reason in SOURCES:
 entry={"key":key,"video_id":id,"source_page_url":page,"creator":creator,"usage":reason,
        "license":"Pexels License","license_url":"https://www.pexels.com/legal-pages/license",
        "source_license_checked_at":"2026-11-05","success":False}
 for u in candidates(id,page):
  try:
   data=get(u,40_000_000)
   if len(data)<100_000 or data[:5].lower().startswith(b"<html") or data[:1]==b"<":continue
   dst=OUT/(key+".mp4");dst.write_bytes(data)
   probe=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(dst)],capture_output=True,text=True,timeout=20)
   if probe.returncode:dst.unlink(missing_ok=True);continue
   j=json.loads(probe.stdout);streams=[s for s in j["streams"] if s.get("codec_type")=="video"]
   if not streams or streams[0].get("width",0)<700 or float(j["format"]["duration"])<4:dst.unlink(missing_ok=True);continue
   entry.update(success=True,actual_file_url=u,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),duration=float(j["format"]["duration"]),width=streams[0]["width"],height=streams[0]["height"])
   print("FOUND",key,round(len(data)/1e6,1),"MB",str(entry["width"])+"x"+str(entry["height"]),entry["duration"],flush=True)
   break
  except Exception as e:
   print("NO",key,u.rsplit("/",1)[-1],str(e)[:110],flush=True)
 print("ACQUISITION",key,entry["success"],flush=True)
 report.append(entry)
(OUT/"LICENSED_SOURCE_DOWNLOAD_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
print("USABLE_FILMED_CLIPS",sum(x["success"] for x in report),flush=True)
if sum(x["success"] for x in report)<4:
 raise RuntimeError("insufficient real licensed clips: no final video should be produced")
