#!/usr/bin/env python3
"""Seven explicit genuine-photo shots for each Great Pyramid Short.
No keyword search, generated fake papyrus, or automatic picture selection.
"""
import argparse,json,subprocess
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageEnhance,ImageFilter
from directed_chapter01 import get_photo,sha
from directed_shorts import frame,BEATS

BASE=Path(__file__).resolve().parent
DECISIONS={
 "01":["g","-","n","i","g","n","a"],
 "02":["-","-","-","b","-","g","a"]
}
PHOTOS={
 "g":{"id":"g","commons_title":"File:Great Pyramid (Pyramid of Cheops Khufu), Giza, GG, EGY (47113255374).jpg","expected_licence":"CC0","credit":"Warren LeMay","source":"https://commons.wikimedia.org/wiki/File:Great_Pyramid_(Pyramid_of_Cheops_Khufu)%2C_Giza%2C_GG%2C_EGY_(47113255374).jpg"},
 "a":{"id":"a","commons_title":"File:Spelterini Pyramids.jpg","expected_licence":"Public domain","credit":"Eduard Spelterini","source":"https://commons.wikimedia.org/wiki/File:Spelterini_Pyramids.jpg"},
 "n":{"id":"n","commons_title":"File:Detectors installed in the DC and in the MC.png","expected_licence":"CC BY 4.0","credit":"ScanPyramids research authors","source":"https://commons.wikimedia.org/wiki/File:Detectors_installed_in_the_DC_and_in_the_MC.png"},
 "i":{"id":"i","commons_title":"File:By ovedc - Interior of the Great Pyramid - 06.jpg","expected_licence":"CC BY-SA 4.0","credit":"ovedc","source":"https://commons.wikimedia.org/wiki/File:By_ovedc_-_Interior_of_the_Great_Pyramid_-_06.jpg"},
 "b":{"id":"b","commons_title":"File:GEM Khufus Boat front 2025.jpg","expected_licence":"CC0","credit":"Commons photograph creator","source":"https://commons.wikimedia.org/wiki/File:GEM_Khufus_Boat_front_2025.jpg"}
}
NOTES={
 "g":"REAL GREAT PYRAMID, MODERN PHOTO",
 "a":"AUTHENTIC HISTORICAL AERIAL VIEW OF GIZA",
 "n":"ACTUAL PUBLISHED MUON-DETECTOR STUDY FIGURE",
 "i":"REAL PYRAMID INTERIOR, NOT THE BIG VOID",
 "b":"ACTUAL KHUFU SHIP; NOT MERER'S CARGO BOAT"
}
def cmd(*args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-1600:])
 return p.stdout.strip()
def shot_plate(n,j,token,photos,out):
 old=BEATS[n][j]
 if token=="-":
  frame(old[1],old[2],old[3],old[0],out)
  return
 src=Image.open(photos[token]).convert("RGB")
 bg=ImageOps.fit(src,(1080,1920),Image.Resampling.LANCZOS)
 bg=ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(26))).enhance(.32)
 img=bg.convert("RGBA")
 fg=ImageOps.contain(src,(1045,1260),Image.Resampling.LANCZOS)
 x=(1080-fg.width)//2;y=440+(1210-fg.height)//2
 img.paste(fg.convert("RGBA"),(x,y))
 draw=ImageDraw.Draw(img,"RGBA")
 draw.rectangle((0,0,1080,390),fill=(7,17,27,230))
 draw.rectangle((0,1630,1080,1920),fill=(7,17,27,226))
 draw.text((60,65),"FACTS UNCOVERED",font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",34),fill="#e2bf85")
 title=old[1]
 font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",55)
 words=title.split();lines=[];line=""
 for word in words:
  q=(line+" "+word).strip()
  if draw.textbbox((0,0),q,font=font)[2]>955 and line:
   lines.append(line);line=word
  else:line=q
 if line:lines.append(line)
 for k,text in enumerate(lines):draw.text((64,172+k*76),text,font=font,fill="white")
 note=NOTES[token]
 f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",29)
 draw.text((68,1737),note,font=f,fill="#f0c780")
 img.convert("RGB").save(out,quality=93)
def one(n,folder,output):
 clip=folder/f"giza_short_{n}_DIRECTED_REVIEW.mp4"
 srt=folder/f"short_{n}_ALIGNED.srt"
 meta=json.loads((folder/f"giza_short_{n}_shot_map.json").read_text())
 beats=meta["beats"]
 assert len(beats)==len(DECISIONS[n])==7
 duration=float(cmd("ffprobe","-v","error","-show_entries","format=duration",
  "-of","default=noprint_wrappers=1:nokey=1",clip))
 assets={};ledger=[]
 for token in DECISIONS[n]:
  if token!="-" and token not in assets:
   file=output/f"licensed_{token}.jpg"
   record=get_photo(PHOTOS[token],file)
   assets[token]=file
   ledger.append(record)
 chunks=[];root=output/f"short_{n}_frames";root.mkdir(exist_ok=True)
 for i,(beat,token) in enumerate(zip(beats,DECISIONS[n])):
  plate=root/f"frame_{i:02}.jpg"
  shot_plate(n,i,token,assets,plate)
  frames=max(1,round((float(beat["end"])-float(beat["start"]))*24))
  chunk=root/f"clip_{i:02}.mp4"
  cmd("ffmpeg","-v","error","-nostdin","-y","-loop","1","-framerate","24","-i",plate,
      "-frames:v",str(frames),"-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-an",chunk)
  chunks.append(chunk)
 playlist=root/"concat.txt"
 playlist.write_text("".join(f"file '{p.resolve()}'\n" for p in chunks))
 picture=root/"picture.mp4"
 cmd("ffmpeg","-v","error","-nostdin","-y","-f","concat","-safe","0","-i",playlist,"-c","copy",picture)
 merged=root/"with_voice.mp4"
 cmd("ffmpeg","-v","error","-nostdin","-y","-i",picture,"-i",clip,
   "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-t",str(duration),merged)
 final=output/f"Great_Pyramid_Short_{n}_REAL_LICENSED_PHOTOS_1080x1920.mp4"
 cmd("ffmpeg","-v","error","-nostdin","-y","-i",merged,
   "-vf",f"subtitles={srt.resolve()}:force_style='FontName=DejaVu Sans,FontSize=27,Outline=3,Alignment=2,MarginV=240'",
   "-c:v","libx264","-preset","veryfast","-crf","19","-c:a","copy","-movflags","+faststart",final)
 cmd("ffmpeg","-v","error","-xerror","-nostdin","-i",final,"-f","null","-")
 (output/f"short_{n}_REAL_PHOTO_CREDITS.json").write_text(json.dumps(ledger,indent=2))
 (output/f"short_{n}_SHOT_SOURCE_MAP.json").write_text(json.dumps({
   "source_first":True,"scene_codes":DECISIONS[n],"real_photos":sum(x!="-" for x in DECISIONS[n]),
   "original_voice_preserved":True,"real_image_credit_ledger":True,
   "AI_generated_photos":0,"historical_document_identity_fabricated":False},indent=2))
 src_plate=root/("frame_00.jpg" if n=="01" else "frame_03.jpg")
 Image.open(src_plate).save(output/f"Great_Pyramid_Short_{n}_REAL_PHOTO_COVER.jpg",quality=91)
 print("SHORT_COMPLETED",n,final.stat().st_size,flush=True)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 for n in ("01","02"):one(n,a.source,a.out)
if __name__=="__main__":main()
