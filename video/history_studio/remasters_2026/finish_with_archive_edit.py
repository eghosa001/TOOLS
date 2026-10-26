#!/usr/bin/env python3
"""One finite, asset-first documentary finishing pass. Existing narration is preserved.

Do not pass off a period-context photograph as imagery of the specific event.
Every physical source is consumed at most once per video.
"""
import argparse, hashlib, html, json, math, os, random, re, subprocess, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageEnhance
ROOT=Path(__file__).resolve().parent;SRC=Path(os.environ.get("REMASTER_INPUT","/tmp/remasters"));OUT=ROOT/"finished";OUT.mkdir(exist_ok=True,parents=True)
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf";SANS="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WIKIMEDIA="https://commons.wikimedia.org/w/api.php"
SAMPLE_QUERIES={
"molasses":[
 "Boston Molasses Flood 1919", "Boston Elevated Railway after the Molasses Flood",
 "Boston Molasses Disaster photographs", "Boston North End Commercial Street 1910",
 "Boston North End harbor 1910 photograph", "Boston Elevated Railway Boston 1910",
 "Boston harbor 1910 1915", "Boston Commercial Street 1900",
 "Boston firefighters 1910 historic", "Boston waterfront 1918 photograph",
 "Boston Massachusetts 1919 newspaper", "Boston Massachusetts Red Cross 1919",
],
"herculaneum":[
 "Herculaneum papyrus roll", "Herculaneum papyri",
 "Herculaneum villa papyri", "Villa of the Papyri Herculaneum",
 "Herculaneum scrolls carbonized", "Papyrus 157 Herculaneum",
 "Herculaneum papyrus unrolling machine", "Herculaneum archaeological ruins",
 "Herculaneum ancient roman ruins", "Herculaneum excavations",
 "Mount Vesuvius 19th century painting eruption",
 "ancient Roman papyrus writing Greek", "X-ray CT scanner synchrotron",
 "digital tomography papyrus ancient scroll"
]}
SCENE_KEYS={
"molasses":{
 "street":("boston","street","harbor","north end"),"tank":("molasses","tank"),
 "archive":("molasses","elevated","wreckage","disaster"),"city":("boston","north end"),
 "map":("north end","boston","harbor"),"leak":("tank","molasses"),
 "blueprint":("tank","molasses","railway"),"diagram":("tank","molasses"),
 "temperature":("boston","harbor"),"clock":("boston","north end"),
 "burst":("molasses","disaster"),"rail":("elevated","railway","tracks"),
 "victims":("molasses","disaster"),"rescue":("molasses","red cross"),
 "aftermath":("molasses","wreckage"),"cleanup":("molasses","aftermath"),
 "court":("molasses","boston"),"trial":("molasses","boston"),
 "engineering":("tank","railway"),"closing":("molasses","boston"),
},
"herculaneum":{
 "sealed":("papyrus","scroll","herculaneum"),"vesuvius":("vesuvius","eruption"),
 "villa":("villa","herculaneum"),"carbon":("carbon","papyrus","roll"),
 "past":("piaggio","unroll","machine"),"scanner":("tomography","scanner","synchrotron"),
 "layers":("papyrus","scroll","roll"),"unwrap":("unroll","machine","papyrus"),
 "ink":("greek","papyrus","writing"),"challenge":("papyrus","research"),
 "pherc1667":("papyrus","herculaneum"),"columns":("greek","papyrus"),
 "themes":("papyrus","greek"),"pherc172":("papyrus","herculaneum"),
 "pherc139":("papyrus","herculaneum"),"philosophy":("greek","roman"),
 "columns2":("papyrus","writing"),"esrf":("tomography","scanner"),
 "evidence":("papyrus","greek","writing"),"limits":("papyrus","scroll"),
 "ethics":("papyrus","roman"),"future":("scanner","papyrus"),
 "archive":("papyrus","villa"),"closing":("papyrus","scroll"),
}}
def sh(*args):
 return subprocess.run([str(v) for v in args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.decode(errors="ignore")
def ffprobe(p):
 return json.loads(sh("ffprobe","-v","error","-show_streams","-show_format","-of","json",p))
def font(sz,bold=False):
 return ImageFont.truetype(BOLD if bold else SANS,int(sz))
def tokenize(s):return set(re.findall(r"[a-z]{3,}",s.lower()))
def strip_html(s):return html.unescape(re.sub("<[^>]+>"," ",s or "")).strip()
def get(url,maxlen=16_000_000):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"FactsUncoveredHistory/2026 (https://github.com/eghosa001/TOOLS)"}),timeout=35) as res:
    raw=res.read(maxlen+1)
   return raw if 500<len(raw)<=maxlen else None
  except Exception as exc:
   print("DOWNLOAD_RETRY",str(exc)[:90],flush=True);time.sleep(attempt+1)
 return None
def permitted(ext):
 z=re.sub(r"[^a-z0-9]","",strip_html(ext.get("LicenseShortName",{}).get("value","")).lower())
 return ("public domain" if "publicdomain" in z or z.startswith("pd") else
         "CC0" if z.startswith("cc0") else
         "CC BY-SA 4.0" if z.startswith("ccbysa40") else
         "CC BY 4.0" if z.startswith("ccby40") else
         "CC BY-SA 3.0" if z.startswith("ccbysa30") else
         "CC BY 3.0" if z.startswith("ccby30") else None)
def search_assets(episode,max_images=53):
 assets=[];seen=set()
 for term in SAMPLE_QUERIES[episode]:
  params={"action":"query","format":"json","generator":"search","gsrsearch":term,"gsrnamespace":6,"gsrlimit":35,
          "prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":2100}
  data=get(WIKIMEDIA+"?"+urllib.parse.urlencode(params),maxlen=3_000_000)
  if not data:continue
  try:pages=json.loads(data).get("query",{}).get("pages",{})
  except Exception:continue
  for page in pages.values():
   name=page.get("title","");info=(page.get("imageinfo") or [{}])[0]
   lic=permitted(info.get("extmetadata",{}))
   url=info.get("thumburl") or info.get("url")
   if not lic or not url or name in seen:continue
   if not re.search(r"\.(png|jpe?g)(\?|$)",url,re.I):continue
   low=name.lower()
   # Avoid fake 'modern flood' photos or modern souvenir/restaurant pictures.
   if episode=="molasses" and any(y in low for y in ["tourist","marker","2023","2024","2025","memorial plaque","superimposed"]):continue
   if episode=="herculaneum" and any(y in low for y in ["ai generated","replica","souvenir","postcard","2025"]):continue
   meta=info.get("extmetadata",{})
   details=strip_html(meta.get("ImageDescription",{}).get("value",""))[:500]
   pageurl="https://commons.wikimedia.org/wiki/"+urllib.parse.quote(name.replace(" ","_"))
   item={"title":name,"url":url,"source":pageurl,"license":lic,
         "author":strip_html(meta.get("Artist",{}).get("value",""))[:170],
         "description":details,"term":term}
   seen.add(name);assets.append(item)
  print("FOUND",episode,term,len(assets),flush=True)
 # Explicit place / period archives first; not all photos are of the exact event.
 dest=OUT/episode/"asset_cache";dest.mkdir(parents=True,exist_ok=True)
 saved=[]
 for candidate in assets:
  if len(saved)>=max_images:break
  raw=get(candidate["url"],maxlen=18_000_000)
  if not raw:continue
  try:
   from io import BytesIO
   im=Image.open(BytesIO(raw));im.load()
   if im.width<710 or im.height<470:continue
   if im.mode!="RGB":im=im.convert("RGB")
   fname=dest/f"photo_{len(saved)+1:02}.jpg";im.save(fname,quality=92,optimize=True)
   candidate["path"]=str(fname);candidate["hash"]=hashlib.sha256(fname.read_bytes()).hexdigest()
   saved.append(candidate)
  except Exception as ex:print("BAD_PHOTO",str(ex)[:100])
 print("LICENSED_ASSETS",episode,len(saved),flush=True)
 return saved
def srt_read(file):
 text=Path(file).read_text(encoding="utf8-sig")
 def sec(s):
  a,b,c,ms=re.split("[:,]",s);return int(a)*3600+int(b)*60+int(c)+int(ms)/1000
 blocks=re.split(r"\n\s*\n",text.strip());out=[]
 for block in blocks:
  lines=[x for x in block.strip().splitlines() if x.strip()]
  if len(lines)<3 or "-->" not in lines[1]:continue
  a,b=[t.strip() for t in lines[1].split("-->")]
  start=sec(a);end=sec(b);out.append({"start":start,"end":end,"spoken":" ".join(lines[2:])})
 return out
def scene_for_beat(episode,index,short=False):
 if short:
  s=min(3,index);lookup={"molasses":["leak","burst","victims","court"],"herculaneum":["sealed","scanner","ink","papyrus"]}
  return lookup[episode][s]
 data=json.loads((ROOT/"episode_research_and_scripts.json").read_text())["episodes"][episode]["scenes"]
 j=min(len(data)-1,index//2)
 return data[j]["type"].replace("_detail","")
def subject_match(episode,scene,item,spoken):
 hay=(item["title"]+" "+item["description"]).lower()
 cues=SCENE_KEYS[episode].get(scene,("papyrus",) if episode=="herculaneum" else ("boston",))
 score=sum(10 for word in cues if word in hay)
 score+=sum(1 for word in tokenize(spoken)&tokenize(item["title"]))
 if episode=="molasses":
  # Don't suggest post-disaster wreckage represents pre-disaster conditions.
  before=any(s in spoken.lower() for s in ("before","constructed in","this was a busy","history of leaking","around midday","mild winter"))
  if before and any(s in hay for s in ("aftermath","wreckage","disaster")):score-=15
  if scene in ("rescue","victims","aftermath","cleanup","rail") and any(s in hay for s in ("1919","molasses","elevated")):score+=12
 if episode=="herculaneum":
  if scene in ("pherc1667","pherc139","pherc172") and any(q in hay for q in ("157-152","1521","papyrus 157")):score-=18
  if scene=="scanner" and any(q in hay for q in ("scanner","synchrotron","x-ray","tomography")):score+=16
 if re.search(r"museum|exhibit|tourist|souvenir",hay):score-=6
 return score
def contextual_label(ep,photo,scene,spoken):
 n=photo["title"].lower()
 if ep=="molasses":
  return "1919 MOLASSES FLOOD • ARCHIVE" if ("molasses" in n or "boston post-january" in n) else "HISTORIC BOSTON • PERIOD CONTEXT"
 return ("HER CULANEUM • CONTEXT ARCHIVE".replace("HER CULANEUM","HERCULANEUM") if any(x in n for x in ("hercul","papy","ercolano")) else "HISTORICAL / SCIENTIFIC CONTEXT")
def pick(assets,used,ep,scene,spoken):
 choices=[(subject_match(ep,scene,v,spoken),i,v) for i,v in enumerate(assets) if v["hash"] not in used]
 if not choices:return None
 choices.sort(key=lambda x:(x[0],-x[1]),reverse=True)
 # Require at least general subject relevance rather than a random photograph.
 match=next((v for score,i,v in choices if score>=5),None)
 if match:used.add(match["hash"])
 return match
def draw_text(draw,xy,word,max_chars,size,fill):
 parts=[];line=""
 for t in word.split():
  if len(line)+len(t)+1>max_chars:parts.append(line);line=t
  else:line=(line+" "+t).strip()
 if line:parts.append(line)
 x,y=xy
 for p in parts[:3]:
  draw.text((x,y),p,font=font(size,True),fill=fill,stroke_width=1,stroke_fill=(18,22,24))
  y+=size+7
def plate(ep,scene,spoken,image,order,total,vertical,filename,kind):
 w,h=(1080,1920) if vertical else (1920,1080)
 base=Image.new("RGB",(w,h),(11,22,31))
 draw=ImageDraw.Draw(base)
 blue=(10,29,39);gold=(228,190,119);white=(246,239,226)
 # Archival photograph fills the majority of screen; high-quality scan retains
 # its original aspect ratio, with a dark blurred edge fill around it.
 if image:
  im=Image.open(image["path"]).convert("RGB")
  cover=ImageOps.fit(im,(w,h),Image.Resampling.LANCZOS,centering=(.5,.45))
  base=Image.blend(cover.filter(ImageFilter.GaussianBlur(42)),Image.new("RGB",(w,h),(5,15,24)),.60)
  # picture-in-picture occupies 80–86% of portrait, 70–91% of landscape
  maxbox=(w-int(w*.08)*2,int(h*.73) if vertical else int(h*.81))
  im.thumbnail(maxbox,Image.Resampling.LANCZOS)
  x=(w-im.width)//2;y=(int(h*.09) if vertical else int(h*.085)) + max(0,(maxbox[1]-im.height)//2)
  base.paste(im,(x,y))
  draw=ImageDraw.Draw(base)
  draw.rectangle((x-4,y-4,x+im.width+4,y+im.height+4),outline=(220,199,163),width=4)
  ident=contextual_label(ep,image,scene,spoken)
 else:
  # Use explicit factual timelines, names and quantities instead of meaningless
  # reused clock/cylinder symbols.
  draw=ImageDraw.Draw(base)
  for row in range(11):
   yy=int(h*.15)+row*int(h*.055)
   draw.line((int(w*.08),yy,int(w*.92),yy),fill=(25+row,48+row,56+row),width=2)
  facts={
   "molasses":{"tank":"2.3 MILLION GALLONS","leak":"LEAKING SEAMS","blueprint":"STEEL & RIVETS",
   "victims":"21 PEOPLE DIED","rescue":"RESCUE UNDERWAY","court":"NEGLIGENCE",
   "trial":"1925 COURT FINDING","map":"BOSTON NORTH END","burst":"THE TANK RUPTURED",
   "temperature":"JANUARY 15, 1919","rail":"ELEVATED RAILWAY"},
   "herculaneum":{"pherc1667":"PHerc. 1667","pherc139":"PHerc. 139","pherc172":"PHerc. 172",
   "scanner":"X-RAY TOMOGRAPHY","unwrap":"VIRTUAL UNWRAPPING","ink":"INK DETECTION",
   "vesuvius":"79 CE","columns":"TEXT COLUMNS","villa":"VILLA OF THE PAPYRI"}
  }
  label=facts[ep].get(scene,scene.upper()[:25])
  draw_text(draw,(int(w*.11),int(h*.30)),label,23,66 if vertical else 84,gold)
  draw_text(draw,(int(w*.11),int(h*.51)),"HISTORICAL EVIDENCE",25,34 if vertical else 47,white)
  ident="EXPLANATORY TITLE CARD"
 # Minimal unobtrusive brand, not another giant title slide.
 draw.rectangle((0,0,w,int(h*.07)),fill=blue)
 draw.text((int(w*.045),int(h*.023)),"FACTS UNCOVERED  /  STORIES & EVIDENCE",font=font(21 if vertical else 27,True),fill=gold)
 if vertical:
  draw.rectangle((0,int(h*.79),w,h),fill=blue)
  draw_text(draw,(int(w*.065),int(h*.815)),ident,38,25,(221,199,151))
 else:
  draw.rectangle((0,int(h*.88),w,h),fill=blue)
  draw.text((int(w*.045),int(h*.910)),ident,font=font(26),fill=gold)
  draw.text((int(w*.91),int(h*.910)),f"{order+1:02d}/{total:02d}",font=font(25),fill=white,anchor="ra")
 base.save(filename,quality=93,subsampling=0)
def caption_srt(beats,path):
 def fmt(s):
  t=int(s*1000);hr,t=divmod(t,3600000);mi,t=divmod(t,60000);se,ms=divmod(t,1000);return f"{hr:02}:{mi:02}:{se:02},{ms:03}"
 out=[];idx=0
 for beat in beats:
  tokens=beat["spoken"].split()
  groups=[" ".join(tokens[j:j+6]) for j in range(0,len(tokens),6)]
  for j,g in enumerate(groups):
   a=beat["start"]+(beat["end"]-beat["start"])*j/len(groups)
   b=beat["start"]+(beat["end"]-beat["start"])*(j+1)/len(groups)
   idx+=1;out.append(f"{idx}\n{fmt(a)} --> {fmt(b)}\n{g}\n")
 Path(path).write_text("\n".join(out))
def edit_one(ep,srcfile,assets,short):
 name=srcfile.stem;vertical=short
 beats=srt_read(srcfile.with_suffix(".srt"));assert len(beats)>=3,name
 temp=OUT/ep/name;temp.mkdir(parents=True,exist_ok=True)
 clipfiles=[];used=set();credits=[]
 for i,beat in enumerate(beats):
  scene=scene_for_beat(ep,i,short)
  photo=pick(assets,used,ep,scene,beat["spoken"])
  image=temp/f"frame_{i:03}.jpg"
  plate(ep,scene,beat["spoken"],photo,i,len(beats),vertical,image,name)
  if photo:credits.append({"beat":i+1,"start":beat["start"],"scene":scene,"title":photo["title"],"license":photo["license"],"author":photo["author"],"source":photo["source"],"context_label":contextual_label(ep,photo,scene,beat["spoken"])})
  duration=beat["end"]-beat["start"]
  part=temp/f"part_{i:03}.mp4"
  x,y=(1080,1920) if vertical else (1920,1080)
  # Animated parallax/push-ins. The images are unique per rendered movie.
  zoom="zoompan=z='min(zoom+0.00019,1.06)':d=1:x='(iw-iw/zoom)*0.5':y='(ih-ih/zoom)*0.5':s=%dx%d:fps=24,format=yuv420p"%(x,y)
  sh("ffmpeg","-nostdin","-y","-v","error","-loop","1","-framerate","24","-i",image,
     "-vf",zoom,"-t",f"{duration:.3f}","-c:v","libx264","-preset","veryfast","-crf","18",
     "-r","24","-an","-pix_fmt","yuv420p",part)
  clipfiles.append(part)
 filelist=temp/"concat.txt"
 filelist.write_text("".join("file '"+str(f.resolve()).replace("'","'\\''")+"'\n" for f in clipfiles))
 linked=temp/"video.mp4"
 sh("ffmpeg","-nostdin","-y","-v","error","-f","concat","-safe","0","-i",filelist,"-r","24",
    "-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p","-an",linked)
 dest=OUT/ep/(name+"_ARCHIVE_EDIT.mp4")
 subtitle=temp/"onscreen.srt";caption_srt(beats,subtitle)
 if vertical:
  # Screen-reader safe mobile captions, proportional to original narrated timing.
  escaped=str(subtitle).replace(":","\\:").replace("'","\\'")
  vf="subtitles="+escaped+":force_style='FontName=DejaVu Sans,FontSize=15,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,BackColour=&H97000000,Alignment=2,MarginV=320'"
  sh("ffmpeg","-nostdin","-y","-v","error","-i",linked,"-i",srcfile,"-map","0:v:0","-map","1:a:0","-vf",vf,
     "-r","24","-c:v","libx264","-preset","fast","-crf","17","-c:a","copy","-shortest","-movflags","+faststart",dest)
 else:
  sh("ffmpeg","-nostdin","-y","-v","error","-i",linked,"-i",srcfile,"-map","0:v:0","-map","1:a:0",
     "-c:v","copy","-c:a","copy","-shortest","-movflags","+faststart",dest)
 meta=ffprobe(dest)
 v=next(s for s in meta["streams"] if s["codec_type"]=="video")
 a=next(s for s in meta["streams"] if s["codec_type"]=="audio")
 expected=(1080,1920) if vertical else (1920,1080)
 assert (v["width"],v["height"])==expected and a["sample_rate"]=="48000"
 assert abs(float(meta["format"]["duration"])-float(ffprobe(srcfile)["format"]["duration"]))<1.2
 assert len({v["source"] for v in credits})==len(credits)
 quality={"status":"NEW_PICTURE_EDIT_REVIEW_REQUIRED","name":name,"output":str(dest),"sources_used":len(credits),
          "unique_shots":len(beats),"source_ratio":round(len(credits)/len(beats),3),
          "source_credits":credits,"duration":meta["format"]["duration"],
          "master_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
          "audio":"ORIGINAL_APPROVED_SCRIPT_NARRATION_PRESERVED","short_captioned":vertical}
 (OUT/ep/(name+"_ARCHIVE_EDIT.qa.json")).write_text(json.dumps(quality,indent=2))
 print("FINISHED_DRAFT",ep,name,len(beats),"sourced_photos",len(credits),flush=True)
 return quality
def main():
 cli=argparse.ArgumentParser();cli.add_argument("--episode",choices=("molasses","herculaneum"),required=True)
 ep=cli.parse_args().episode
 assets=search_assets(ep)
 # Do not silently replace an inadequate archive with same generic illustrations.
 if len(assets)<18:raise RuntimeError(f"Only {len(assets)} licensed source assets could be retrieved; quality job fails rather than generating 48 icons.")
 videos=sorted((SRC/ep).glob("*.mp4"))
 assert len(videos)==4
 result=[]
 for v in videos:result.append(edit_one(ep,v,assets,"SHORT" in v.name))
 (OUT/ep/"FINISHED_EDIT_MANIFEST.json").write_text(json.dumps(result,indent=2))
 print("REMASTER_PICTURE_EDIT_READY_FOR_REVIEW",ep,len(result),flush=True)
if __name__=="__main__":main()
