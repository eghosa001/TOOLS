#!/usr/bin/env python3
"""Seven hand-authored visual beats per Short, synchronized to existing SRT cue times.
Mechanical compositing only: no archive image search, no keyword-based image selection.
Drawings are original explanatory graphics; none are photographs or authentic documents.
"""
from __future__ import annotations
import argparse, json, math, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H,FPS=1080,1920,24
BG=(10,19,30); PALE=(240,232,214); GOLD=(230,185,95); TEAL=(78,170,179)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BEATS={
 "01":[
  ("Something at least thirty metres","THE SPACE WE CAN'T ENTER","pyramid","Observed void: at least 30 metres long"),
  ("In twenty seventeen","2017 · A SCIENTIFIC DISCOVERY","section","Above the Grand Gallery"),
  ("Three independent detector techniques","THREE INDEPENDENT METHODS","detectors","Separate measurements strengthened the finding"),
  ("But nobody knows exactly why","WHY WAS IT LEFT THERE?","unknown","Ancient purpose remains unknown"),
  ("And despite what some viral videos say","NO VERIFIED TREASURE","claims","No objects or contents have been identified"),
  ("This is a genuine mystery","THE EVIDENCE IS REAL","evidence","The interpretation remains open"),
  ("Watch our full Great Pyramid","THE GREAT PYRAMID","end","Watch the full evidence-led documentary"),
 ],
 "02":[
  ("The best clue to how Egypt's","THE CLUE CAME FROM PAPER","papyri","Ancient administrative records, not a blueprint"),
  ("It came from ancient papyri","FOUND NEAR THE RED SEA","port","Wadi al-Jarf, Egyptian Red Sea coast"),
  ("An inspector called Merer","THE INSPECTOR: MERER","inspector","Recorded real work movements under Khufu"),
  ("using boats and a carefully organised schedule","LIMESTONE BY BOAT","boat","Tura to the Khufu project, via waterways"),
  ("It's a rare firsthand record","A FOUR-THOUSAND-YEAR RECORD","ledger","Daily operations documented on papyrus"),
  ("It doesn't describe every ramp","WHAT IT DOESN'T TELL US","limits","Delivery is documented; every lifting method is not"),
  ("Watch the full documentary","FOLLOW THE EVIDENCE","end","See the full Great Pyramid investigation"),
 ]
}

def command(argv):
 r=subprocess.run([str(x) for x in argv],capture_output=True,text=True)
 if r.returncode: raise RuntimeError("ffmpeg error "+r.stderr[-2200:])
 return r.stdout.strip()

def duration(file):
 return float(command(["ffprobe","-v","error","-show_entries","format=duration",
                       "-of","default=noprint_wrappers=1:nokey=1",file]))

def seconds(t):
 h,m,s=t.replace(",",".").split(":")
 return int(h)*3600+int(m)*60+float(s)

def tokens(t):
 return re.findall(r"[a-z0-9]+",t.lower().replace("’","'"))

def cue_words(path):
 raw=path.read_text(encoding="utf-8-sig").strip()
 entries=[]
 for block in re.split(r"\r?\n\r?\n",raw):
  m=re.search(r"(\d\d:\d\d:\d\d[,.]\d{3})\s*-->\s*(\d\d:\d\d:\d\d[,.]\d{3})",block)
  if not m: continue
  text=block[m.end():].strip()
  word=tokens(re.sub(r"<[^>]+>","",text))
  if word: entries.append((seconds(m.group(1)),seconds(m.group(2)),word))
 assert len(entries)>=6,("Too few caption cues",path)
 out=[]
 for start,end,word in entries:
  out += [(w,start+(end-start)*(k/len(word))) for k,w in enumerate(word)]
 return out

def anchor_time(wordtimes,phrase):
 needed=tokens(phrase)
 for j in range(len(wordtimes)-len(needed)+1):
  if [wordtimes[j+k][0] for k in range(len(needed))]==needed:
   return wordtimes[j][1]
 raise ValueError("SRT does not contain exact narration anchor: "+phrase)

def text_box(draw,text,x,y,max_width,size=55,bold=True,fill=PALE):
 f=ImageFont.truetype(BOLD if bold else FONT,size)
 words=text.split();lines=[];line=""
 for word in words:
  test=(line+" "+word).strip()
  if draw.textbbox((0,0),test,font=f)[2]>max_width and line:
   lines.append(line);line=word
  else:line=test
 if line:lines.append(line)
 for i,line in enumerate(lines):
  draw.text((x,y+i*int(size*1.28)),line,font=f,fill=fill)
 return y+len(lines)*int(size*1.28)

def arrow(d,pts,color=GOLD,width=10):
 d.line(pts,fill=color,width=width,joint="curve")
 x0,y0=pts[-2];x1,y1=pts[-1];a=math.atan2(y1-y0,x1-x0)
 for delta in (-.55,.55):
  x=x1-32*math.cos(a+delta);y=y1-32*math.sin(a+delta)
  d.line([(x1,y1),(x,y)],fill=color,width=width)

def pyramid(d,center=540,top=525,base=1200):
 left,right=center-390,center+390
 d.polygon([(center,top),(left,base),(right,base)],fill=(136,114,84),outline=GOLD,width=7)
 for k in range(1,19):
  y=top+int((base-top)*k/19)
  span=(y-top)/(base-top)*390
  d.line([(center-span,y),(center+span,y)],fill=(191,159,112),width=2)
 return left,right

def graphic(d,kind):
 if kind in ("pyramid","section","unknown","claims","evidence"):
  pyramid(d)
  d.line([(515,1175),(530,915),(595,810)],fill=PALE,width=10)
  d.line([(565,800),(655,710)],fill=TEAL,width=10)
  if kind=="pyramid":
   d.rounded_rectangle((440,685,700,750),radius=17,fill=(13,31,46),outline=GOLD,width=6)
   text_box(d,"30 m+",471,697,190,41,fill=GOLD)
  if kind=="section":
   d.rounded_rectangle((436,670,710,750),radius=12,outline=GOLD,width=7)
   d.line([(695,690),(830,635)],fill=GOLD,width=5)
   text_box(d,"BIG VOID",735,575,240,30,fill=GOLD)
   text_box(d,"GRAND GALLERY",300,1264,550,38)
  if kind=="unknown":
   d.rounded_rectangle((415,670,730,755),radius=13,outline=GOLD,width=5)
   text_box(d,"?",547,679,80,55,fill=GOLD)
  if kind=="claims":
   d.rectangle((280,760,800,876),fill=(22,34,49),outline=GOLD,width=3)
   text_box(d,"NO CONTENTS",316,780,490,44)
   text_box(d,"CONFIRMED",330,834,470,42,fill=GOLD)
  if kind=="evidence":
   d.rounded_rectangle((205,1230,875,1355),radius=24,fill=(16,49,57),outline=TEAL,width=3)
   text_box(d,"VOID DETECTED  ✓",250,1273,580,43,fill=PALE)
 elif kind=="detectors":
  for x,lab in ((107,"EMULSION"),(395,"SCINTILLATOR"),(685,"GAS")):
   d.rounded_rectangle((x,705,x+285,1055),radius=24,fill=(25,44,61),outline=TEAL,width=5)
   for k in range(6):d.line([(x+30,774+k*31),(x+248,774+k*31)],fill=GOLD,width=4)
   text_box(d,lab,x+28,1090,264,29,fill=PALE)
  for x in (240,535,830):
   arrow(d,[(x,493),(x,665)],GOLD,8)
 elif kind=="papyri":
  d.rounded_rectangle((245,515,820,1295),radius=16,fill=(185,157,112),outline=GOLD,width=10)
  d.line([(300,560),(765,560)],fill=(77,58,44),width=5)
  for k in range(14):
   y=610+k*43
   d.line([(320,y),(690-(k%4)*65,y)],fill=(89,71,54),width=5)
  text_box(d,"MODERN SCHEMATIC",291,1330,510,27,fill=GOLD)
 elif kind=="port":
  d.rectangle((100,923,980,1288),fill=(25,76,91))
  for y in range(960,1260,45):
   d.arc((120,y,990,y+80),180,355,fill=TEAL,width=4)
  d.polygon([(100,920),(100,520),(430,835),(500,920)],fill=(163,126,75))
  text_box(d,"RED SEA",578,1000,340,49,fill=PALE)
  text_box(d,"WADI AL-JARF",222,1288,655,48,fill=GOLD)
  text_box(d,"NOT TO SCALE",340,1360,440,27,fill=PALE)
 elif kind=="inspector":
  d.ellipse((430,540,655,760),fill=(180,137,84),outline=GOLD,width=5)
  d.rounded_rectangle((390,765,700,1255),radius=60,fill=(211,182,137),outline=GOLD,width=5)
  d.rounded_rectangle((535,840,810,1130),radius=12,fill=(158,131,96),outline=PALE,width=6)
  text_box(d,"ILLUSTRATION",340,1320,440,29,fill=GOLD)
 elif kind=="boat":
  d.rectangle((80,1050,990,1295),fill=(26,85,93))
  for k in range(5):
   d.arc((130,1090+k*27,970,1310+k*27),170,340,fill=TEAL,width=4)
  d.polygon([(160,993),(900,993),(775,1163),(330,1163)],fill=(124,83,48),outline=GOLD,width=6)
  d.line([(540,600),(540,990)],fill=PALE,width=9)
  d.polygon([(545,624),(785,935),(545,935)],fill=(232,214,178))
  for x in (290,420,570):
   d.rectangle((x,922,x+115,1000),fill=(179,161,129),outline=PALE,width=3)
  text_box(d,"SCHEMATIC BOAT",295,1318,540,31,fill=GOLD)
 elif kind=="ledger":
  d.rounded_rectangle((90,670,990,1280),radius=25,fill=(47,54,55),outline=GOLD,width=5)
  columns=[(125,"DAY"),(330,"CARGO"),(605,"ROUTE")]
  for x,label in columns:text_box(d,label,x,705,260,39,fill=GOLD)
  for row in range(4):
   yy=788+row*106
   d.line([(115,yy),(960,yy)],fill=(143,131,105),width=3)
   for x in (145,350,635):d.rounded_rectangle((x,yy+28,x+125,yy+43),radius=4,fill=(194,183,160))
  text_box(d,"EXPLANATORY TABLE",285,1350,620,29,fill=GOLD)
 elif kind=="limits":
  d.rounded_rectangle((100,640,980,875),radius=25,fill=(23,61,63),outline=TEAL,width=5)
  text_box(d,"KNOWN: STONE DELIVERIES",145,730,825,46)
  d.rounded_rectangle((100,995,980,1230),radius=25,fill=(64,48,46),outline=GOLD,width=5)
  text_box(d,"UNKNOWN: EVERY LIFT",155,1080,810,45)
 elif kind=="end":
  pyramid(d,top=535,base=1140)
  d.rounded_rectangle((155,1210,920,1345),radius=20,fill=(32,72,78),outline=TEAL,width=5)
  text_box(d,"FACTS UNCOVERED",220,1250,690,51,fill=PALE)

def frame(title,kind,subtitle,label,out):
 im=Image.new("RGB",(W,H),BG)
 d=ImageDraw.Draw(im)
 # Ordered restrained decorative lines, not data or ancient writing
 for k in range(24):
  y=430+k*43
  d.line([(0,y),(W,y)],fill=(18,28,41),width=2)
 d.rectangle((0,0,W,10),fill=GOLD)
 d.text((72,64),"FACTS UNCOVERED",font=ImageFont.truetype(BOLD,36),fill=GOLD)
 d.line([(72,125),(1008,125)],fill=(76,86,96),width=2)
 text_box(d,title,78,192,916,64,bold=True)
 graphic(d,kind)
 d.rounded_rectangle((80,1412,1000,1510),radius=16,fill=(18,39,52),outline=(66,88,96),width=2)
 text_box(d,subtitle,111,1440,850,26,bold=False)
 d.text((80,1775),"ARTISTIC / SCIENTIFIC ILLUSTRATION",font=ImageFont.truetype(FONT,24),fill=(163,174,184))
 im.save(out,quality=94,subsampling=0)

def make(number,indir,outdir):
 beats=BEATS[number]
 src=indir/f"short_{number}.mp4";srt=indir/f"short_{number}.srt"
 assert src.is_file() and srt.is_file()
 length=duration(src)
 w=cue_words(srt)
 start=[anchor_time(w,beat[0]) for beat in beats]
 start[0]=0.
 if not all(start[i+1]>start[i]+.25 for i in range(len(start)-1)):
  raise ValueError("Narration anchor timing out of order: "+str(start))
 spans=[(start[i],start[i+1] if i+1<len(start) else length) for i in range(len(start))]
 assert all(end-begin>.32 for begin,end in spans)
 outdir.mkdir(parents=True,exist_ok=True)
 clips=[];meta=[]
 for i,((anchor,title,kind,sub),(begin,end)) in enumerate(zip(beats,spans)):
  plate=outdir/f"{number}_plate_{i+1:02d}.jpg"
  frame(title,kind,sub,anchor,plate)
  clip=outdir/f"{number}_scene_{i+1:02d}.mp4"
  frames=round((end-begin)*FPS)
  # Purposeful and restrained push into each carefully authored educational frame.
  vf=f"zoompan=z='min(zoom+0.00008,1.04)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s={W}x{H}:fps={FPS},format=yuv420p"
  command(["ffmpeg","-hide_banner","-loglevel","error","-y",
           "-loop","1","-framerate",FPS,"-i",plate,"-frames:v",frames,
           "-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","18","-an",clip])
  clips.append(clip)
  meta.append(dict(shot=i+1,start=round(begin,3),end=round(end,3),
                   narration_anchor=anchor,asset=plate.name,art=kind,
                   evidence_label="ORIGINAL ILLUSTRATION NOT DOCUMENTARY PHOTOGRAPHY",
                   direction="curated static composition with restrained camera push"))
 cat=outdir/f"{number}_concat.txt"
 cat.write_text("".join("file '"+p.name+"'\n" for p in clips))
 edited=outdir/f"giza_short_{number}_DIRECTED_REVIEW.mp4"
 command(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
          "-i",cat,"-i",src,"-map","0:v:0","-map","1:a:0",
          "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000",
          "-ac","2","-t",str(length),"-movflags","+faststart",edited])
 actual=duration(edited)
 assert abs(actual-length)<.2,(actual,length)
 report=dict(source_file=src.name,output=edited.name,voice_reused=True,
             duration=actual,beats=meta,creative_selection="HAND_AUTHORED",
             captions="SOURCE_SRT_AWAITING_AUDIO_FORCED_ALIGNMENT",
             continuous_editorial_listening="NOT PERFORMED",
             final_publication_approval="NOT GRANTED")
 (outdir/f"giza_short_{number}_shot_map.json").write_text(json.dumps(report,indent=2))
 print(json.dumps(dict(short=number,output=edited.name,duration=actual,shots=len(meta))))

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--input",required=True);ap.add_argument("--output",required=True)
 args=ap.parse_args()
 for ident in ("01","02"):make(ident,Path(args.input),Path(args.output))
