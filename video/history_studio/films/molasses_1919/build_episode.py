#!/usr/bin/env python3
"""One complete narrated archival/illustrated history episode, no fake historical media.
GitHub Actions worker downloads licensed original 1919 images, Piper voice files,
and renders all scenes. End product: MP4, SRT, thumbnail, provenance and script.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, subprocess, sys, textwrap, urllib.parse, urllib.request, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE=Path(__file__).resolve().parent
OUT=HERE/'output'; OUT.mkdir(exist_ok=True)
DATA=json.loads((HERE/'episode.json').read_text(encoding='utf8'))
W,H=1600,900
C={'bg':(14,22,30),'ink':(231,225,207),'gold':(216,170,103),'rust':(157,80,54),'blue':(52,73,84),'brown':(66,39,28)}
FONT1='/usr/share/fonts/truetype/lato/Lato-Heavy.ttf'
FONT2='/usr/share/fonts/truetype/lato/Lato-Regular.ttf'
FONT3='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
for f in (FONT1,FONT2,FONT3):
 if not Path(f).exists(): raise RuntimeError('Missing fonts; use Ubuntu runner with Lato and DejaVu fonts')
F=lambda size,bold=False:ImageFont.truetype(FONT1 if bold else FONT2,size)

def probe(path):
  r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)],text=True,capture_output=True,check=True)
  return float(r.stdout)

def call(args):
 print('RUN', ' '.join(map(str,args))[:400],flush=True)
 subprocess.run(list(map(str,args)),check=True)

def archive_download(dest, filename):
 # Commons' imageinfo returns original exact-upload URL; no page scraping.
 api='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url','iiurlwidth':'1600','titles':'File:'+filename})
 header={'User-Agent':'HistoryStudio2D/0.1 (archival media research; source credited)'}
 for attempt in range(3):
  try:
   req=urllib.request.Request(api,headers=header)
   with urllib.request.urlopen(req,timeout=45) as u: obj=json.load(u)
   pages=list(obj['query']['pages'].values())
   info=pages[0]['imageinfo'][0]; url=info.get('thumburl') or info['url']
   with urllib.request.urlopen(urllib.request.Request(url,headers=header),timeout=90) as u: raw=u.read(16_000_000)
   if len(raw)>15_999_999 or len(raw)<5_000:raise ValueError('Invalid archival image bytes')
   dest.write_bytes(raw)
   with Image.open(dest) as image: image.verify()
   return True
  except Exception as e:
   print('ARCHIVE_LOAD_WARNING',filename,attempt,str(e)[:250],flush=True)
 return False

def archival_assets(download=True):
 paths={}
 folder=OUT/'archives';folder.mkdir(exist_ok=True)
 for item in DATA['archival_images']:
  p=folder/(item['id']+'.'+item['file'].split('.')[-1])
  if not p.exists() and download: archive_download(p,item['file'])
  if p.exists():paths[item['id']]=p
 print('ARCHIVAL_PHOTOS_LOADED',len(paths),'of',len(DATA['archival_images']))
 return paths

def label(draw,text,xy,font,fill,shadow=True):
 x,y=xy
 if shadow: draw.text((x+2,y+3),text,font=font,fill=(0,0,0))
 draw.text(xy,text,font=font,fill=fill)

def grain(im,seed=0):
 rng=np.random.default_rng(seed); pix=np.asarray(im).astype(np.int16)
 noise=rng.integers(-7,8,(H,W,1),dtype=np.int16)
 return Image.fromarray(np.uint8(np.clip(pix+noise,0,255)),'RGB')

def sepia(image):
 im=image.convert('RGB');im=ImageEnhance.Color(im).enhance(0.25)
 arr=np.asarray(im).astype(np.float32)
 arr[:,:,0]=np.clip(arr[:,:,0]*1.08+8,0,255)
 arr[:,:,1]=np.clip(arr[:,:,1]*1.02+3,0,255)
 arr[:,:,2]=np.clip(arr[:,:,2]*0.83,0,255)
 return Image.fromarray(arr.astype(np.uint8),'RGB')

def rounded(draw,bb,r,fill,outline=None,width=1):draw.rounded_rectangle(bb,radius=r,fill=fill,outline=outline,width=width)

def draw_tank(d,x,y,w,h,broken=False):
 d.rectangle((x,y,x+w,y+h),fill=(87,93,92),outline=(195,170,118),width=5)
 d.ellipse((x,y-20,x+w,y+20),fill=(98,104,102),outline=(204,181,127),width=5)
 for dx in range(38,int(w),65):d.line((x+dx,y+15,x+dx,y+h-5),fill=(70,76,77),width=3)
 for dy in range(60,int(h),72):
  d.line((x+8,y+dy,x+w-7,y+dy),fill=(154,155,145),width=3)
  for dx in range(30,int(w),55):d.ellipse((x+dx-2,y+dy-2,x+dx+2,y+dy+2),fill=C['gold'])
 if broken:
  d.polygon([(x+w-10,y+65),(x+w+130,y+20),(x+w+150,y+210),(x+w-8,y+270)],fill=C['bg'])

def art_base(i,kind):
 rng=random.Random(i*131)
 im=Image.new('RGB',(W,H),(25,33,41));d=ImageDraw.Draw(im)
 for y in range(H):
  f=y/H
  d.line([(0,y),(W,y)],fill=(int(17+28*f),int(27+12*f),int(37+4*f)))
 # subtle fog / harbor
 d.ellipse((1080,100,1760,780),fill=(44,56,61))
 for n in range(8):
  x=rng.randint(0,W);d.line((x,0,x-290,H),fill=(35,43,47),width=rng.randint(1,3))
 if kind in ('art_city','art_street','art_cleanup','art_rescue','art_wave','art_court','art_tank'):
  horizon=610
  d.polygon([(0,horizon),(W,horizon-15),(W,H),(0,H)],fill=(43,45,46))
  d.line((0,horizon,1600,horizon-10),fill=(108,94,74),width=6)
  for b in range(14):
   x=int(b*150-100+rng.randint(-25,25));bw=rng.randint(95,195);bh=rng.randint(100,310)
   d.rectangle((x,horizon-bh,x+bw,horizon),fill=(36+rng.randint(0,24),49+rng.randint(0,16),53),outline=(103,91,70),width=3)
   for cx in range(x+20,x+bw-20,29):
    for cy in range(horizon-bh+24,horizon-24,45):d.rectangle((cx,cy,cx+12,cy+21),fill=(122,110,82) if rng.random()<.65 else (31,43,47))
  # waterfront elevated railway
  d.line((0,370,1600,385),fill=(151,141,121),width=15);d.line((0,402,1600,417),fill=(67,74,79),width=12)
  for x in range(0,W,165):
   d.line((x,404,x+15,650),fill=(119,116,104),width=11)
   d.line((x,403,x+168,404),fill=(94,102,106),width=5)
  if kind in ('art_wave','art_tank','art_street'):
   draw_tank(d,830,140,320,470,broken=kind=='art_wave')
  if kind=='art_wave':
   for n in range(7):
    y=650+n*17
    d.polygon([(0,y),(300,y-55),(600,y-37),(940,y-95),(1300,y-47),(1600,y+35),(1600,H),(0,H)],fill=(73+n*3,45+n,34+n))
    d.arc((0,y-120,1600,y+150),5,170,fill=(169,107,65),width=7)
   for x,y in [(470,675),(605,655),(920,683)]:
    d.line((x,y,x+26,y-52),fill=C['ink'],width=8);d.ellipse((x+14,y-69,x+40,y-43),fill=C['ink'])
  if kind=='art_rescue':
   d.rectangle((300,480,700,500),fill=(145,144,132))
   for n in range(7):d.line((310+n*50,500,385+n*50,630),fill=(176,172,153),width=7)
   for x in (480,760,1050):
    d.ellipse((x,470,x+29,503),fill=(206,183,143));d.line((x+15,503,x+15,580),fill=(205,181,132),width=9)
    d.line((x+15,530,x+54,565),fill=(205,181,132),width=8)
    d.line((x+15,580,x-10,618),fill=(205,181,132),width=9)
  if kind=='art_cleanup':
   for x in (500,700,850,1050):d.line((x,680,x+130,780),fill=(177,171,150),width=9)
  if kind=='art_court':
   d.rectangle((80,490,1400,690),fill=(86,66,49));d.rectangle((210,400,500,490),fill=(131,96,66))
 elif kind in ('diagram_flow','diagram_rivets','diagram_pressure','diagram_blueprint','diagram_timeline'):
  draw_tank(d,1070,200,260,430)
  if kind=='diagram_flow':
   for x,t in [(100,'HARBOR'),(520,'STORAGE'),(950,'DISTILLERY')]:
    rounded(d,(x,350,x+340,530),23,(46,66,69),C['gold'],5)
    label(d,t,(x+40,406),F(39,True),C['ink'])
   for x in (440,850):d.line((x,438,x+80,438),fill=C['gold'],width=8);d.polygon([(x+78,415),(x+108,438),(x+78,460)],fill=C['gold'])
  elif kind=='diagram_rivets':
   for y in range(300,620,65):
    d.line((90,y,855,y),fill=(150,160,153),width=14)
    for x in range(120,820,72):d.ellipse((x,y-10,x+20,y+10),fill=C['gold'])
   d.line((570,220,680,600),fill=(215,75,66),width=18)
   label(d,'FATIGUE + WEAK SEAMS',(180,665),F(33,True),C['gold'])
  elif kind=='diagram_pressure':
   for n in range(8):d.line((105,300+n*50,800,300+n*50),fill=(58+n*9,84+n*4,95+n*3),width=35)
   label(d,'PRESSURE INCREASES WITH DEPTH',(95,735),F(31,True),C['gold'])
  elif kind=='diagram_blueprint':
   d.rectangle((0,190,900,750),outline=(96,149,166),width=4)
   for y in range(230,700,35):d.line((0,y,900,y),fill=(43,75,91),width=1)
   for x in range(0,900,35):d.line((x,190,x,750),fill=(43,75,91),width=1)
   label(d,'CHECK • INSPECT • REPAIR',(110,480),F(40,True),C['gold'])
  elif kind=='diagram_timeline':
   dates=[('1915','BUILT'),('1919','COLLAPSED'),('1925','NEGLIGENCE')]
   for k,(year,t) in enumerate(dates):
    x=150+300*k
    d.line((x,365,x+260,365),fill=C['gold'],width=7)
    d.ellipse((x,345,x+36,382),fill=C['rust'],outline=C['gold'],width=4)
    label(d,year,(x-15,415),F(57,True),C['ink'])
    label(d,t,(x-15,505),F(23,True),C['gold'])
 return im

def photo_background(image):
 im=sepia(image)
 # keep photo full (no misleading selective cutting), letterbox if needed
 im.thumbnail((1260,620),Image.Resampling.LANCZOS)
 return im

def plate(i,scene, archives):
 kind=scene['kind']; asset=scene.get('asset')
 im=art_base(i,kind) if kind!='archive' or asset not in archives else Image.new('RGB',(W,H),C['bg'])
 d=ImageDraw.Draw(im)
 if kind=='archive' and asset in archives:
  photo=photo_background(Image.open(archives[asset]))
  px=85+(1260-photo.width)//2;py=188+(620-photo.height)//2
  d.rounded_rectangle((75,170,1430,805),12,fill=(41,45,43),outline=C['gold'],width=3)
  im.paste(photo,(px,py));d=ImageDraw.Draw(im)
  label(d,'AUTHENTIC 1919 ARCHIVE',(100,760),F(25,True),C['ink'])
 else:
  label(d,'ILLUSTRATED RECONSTRUCTION',(95,761),F(22,True),(223,207,176))
 # subtle foreground framing
 d.rectangle((0,0,W,120),fill=(11,20,28))
 d.line((80,120,1520,120),fill=C['gold'],width=4)
 label(d,'HISTORY UNCOVERED',(80,35),F(33,True),C['gold'])
 label(d,'1919  /  BOSTON', (1250,46),F(22,True),(202,194,173))
 # headline behind dark translucent box
 dark=Image.new('RGBA',(W,H),(0,0,0,0));p=ImageDraw.Draw(dark)
 p.rounded_rectangle((68,666,1532,738),radius=14,fill=(9,15,20,215))
 im=Image.alpha_composite(im.convert('RGBA'),dark).convert('RGB');d=ImageDraw.Draw(im)
 headline=scene['headline']
 maxsize=52
 while d.textbbox((0,0),headline,font=F(maxsize,True))[2] >1390 and maxsize>26:maxsize-=2
 label(d,headline,(95,675),F(maxsize,True),C['ink'])
 d.rectangle((0,H-34,W,H),fill=(10,18,26))
 label(d,scene['chapter'],(85,H-27),F(18,True),C['gold'])
 label(d,f'PART {i+1:02d} / {len(DATA["scenes"]):02d}',(1380,H-27),F(18,True),C['ink'])
 return grain(im,i)

def make_plates(archives):
 p=OUT/'plates';p.mkdir(exist_ok=True)
 for i,scene in enumerate(DATA['scenes']):
  file=p/f'scene_{i+1:02}.jpg'
  plate(i,scene,archives).save(file,quality=91,optimize=True)
 return p

def gen_voice_piper(model,config):
 from piper.voice import PiperVoice
 voice=PiperVoice.load(str(model),config_path=str(config))
 folder=OUT/'narration';folder.mkdir(exist_ok=True)
 for i,scene in enumerate(DATA['scenes']):
  name=folder/f'voice_{i+1:02}.wav'
  if not name.exists():
   with wave.open(str(name),'wb') as wav: voice.synthesize_wav(scene['narration'],wav)
  d=probe(name)
  if not (7<d<160):raise RuntimeError('Bad voice duration for scene '+str(i+1)+': '+str(d))
  print('VOICE',i+1,'SECONDS',round(d,2))
 return folder

def gen_voice_espeak():
 folder=OUT/'narration';folder.mkdir(exist_ok=True)
 for i,scene in enumerate(DATA['scenes']):
  file=folder/f'voice_{i+1:02}.wav'
  call(['espeak','-ven-us','-s','145','-p','43','-a','170','-w',file,scene['narration']])
 return folder

def to_srt_time(seconds):
 ms=int(round(seconds*1000));h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02},{ms:03}'

def captions(audio):
 start=0.; records=[]
 for i,scene in enumerate(DATA['scenes']):
  length=probe(audio/f'voice_{i+1:02}.wav')
  sentences=scene['narration'].split('. ')
  weights=[max(1,len(x.split())) for x in sentences];total=sum(weights);loc=start
  for s,w in zip(sentences,weights):
   time=length*w/total
   records.append((loc,loc+time,s.strip().rstrip('.')+'.'))
   loc+=time
  start+=length
 with (OUT/'subtitles.srt').open('w',encoding='utf8') as out:
  for i,(a,b,s) in enumerate(records,1):out.write(f'{i}\n{to_srt_time(a)} --> {to_srt_time(b)}\n{s}\n\n')
 return start

def music(seconds):
 # Original ambient soundtrack made from synthesized tones; fully owner-generated.
 rate=22050;duration=22.;n=int(duration*rate);t=np.arange(n,dtype=np.float32)/rate
 chords=[[110,164.81,220],[98,146.83,196],[130.81,164.81,261.63],[87.31,130.81,174.61]]
 y=np.zeros(n,dtype=np.float32)
 for i,frequencies in enumerate(chords):
  sel=(t>=i*duration/4)&(t<(i+1)*duration/4)
  tr=t[sel]-i*duration/4
  env=np.clip(tr/1.1,0,1)*np.clip((duration/4-tr)/1.3,0,1)
  y[sel]+=env*sum(np.sin(2*math.pi*hz*tr)*.025 for hz in frequencies)/3
 # melodic low piano-like single notes
 for k in range(11):
  begin=k*2;end=min(n,(begin+2)*rate);tr=np.arange(end-begin*rate)/rate
  tone=[220,196,174.61,196,164.81,146.83,130.81,146.83][k%8]
  y[begin*rate:end]+=.015*np.sin(2*math.pi*tone*tr)*np.exp(-2.8*tr)
 y[:rate]=y[:rate]*np.linspace(0,1,rate)
 y[-rate:]=y[-rate:]*np.linspace(1,0,rate)
 with wave.open(str(OUT/'music_loop.wav'),'wb') as wav:
  wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
  wav.writeframes((np.clip(y,-1,1)*32767).astype('<i2').tobytes())

def render(audio,plate_dir,preview=0):
 scene_count=len(DATA['scenes']) if not preview else min(preview,len(DATA['scenes']))
 clips=OUT/'clips';clips.mkdir(exist_ok=True)
 concat=[]
 for i in range(scene_count):
  raw=audio/f'voice_{i+1:02}.wav';d=probe(raw)
  pic=plate_dir/f'scene_{i+1:02}.jpg';dest=clips/f'scene_{i+1:02}.mp4'
  # zoompan updates every frame. Output is rendered at true 1280x720; high-quality 1600px plates.
  drift=['0.20','0.65','0.40','0.80'][i%4]
  zoom="zoompan=z='min(zoom+0.00013,1.12)':d=1:x='(iw-iw/zoom)*"+drift+"':y='(ih-ih/zoom)*0.45':s=1280x720:fps=24,format=yuv420p[v]"
  if not dest.exists():
   call(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','24','-i',pic,'-i',raw,'-filter_complex',zoom,'-map','[v]','-map','1:a','-t',f'{d:.3f}','-r','24','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','44100','-ac','1','-movflags','+faststart',dest])
  concat.append("file '"+str(dest.resolve()).replace("'","'\\''")+"'")
  print('SCENE_RENDERED',i+1,'of',scene_count,'seconds',round(d,1),flush=True)
 (OUT/'concat.txt').write_text('\n'.join(concat)+'\n')
 call(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',OUT/'concat.txt','-c','copy',OUT/'silent_mix.mp4'])
 total=probe(OUT/'silent_mix.mp4');music(total)
 # Repeat original ambience quietly throughout (ducked); narration stays clear.
 call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',OUT/'silent_mix.mp4','-stream_loop','-1','-i',OUT/'music_loop.wav','-filter_complex','[0:a]volume=1.2[n];[1:a]volume=0.25[m];[n][m]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.92[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',OUT/('Great_Molasses_Flood_1919.mp4' if not preview else 'Great_Molasses_Flood_PREVIEW.mp4')])
 print('FINAL_DURATION',total, 'CLIPS',scene_count)
 return total

def make_thumbnail(archive):
 platefile=OUT/'plates/scene_01.jpg'
 im=Image.open(platefile).convert('RGB')
 d=ImageDraw.Draw(im);d.rectangle((0,190,900,565),fill=(15,23,27))
 label(d,'THE DAY BOSTON',(68,225),F(87,True),(243,237,218))
 label(d,'DROWNED IN',(68,323),F(84,True),(243,237,218))
 label(d,'MOLASSES',(68,425),F(111,True),(234,163,95))
 im.resize((1280,720),Image.Resampling.LANCZOS).save(OUT/'thumbnail.jpg',quality=92)

def write_provenance(archives):
 details={'title':DATA['title'],'script_words':sum(len(s['narration'].split()) for s in DATA['scenes']),'editorial_status':'COMPLETE TECHNICAL FILM - requires listening and visual review before publishing','research_sources':DATA['research'],'archival_media':[],'original_graphics':'Programmatically authored artwork and infographics; not historic photographs','background_score':'Original synthesized notes: no third-party recording used','voice':'Piper narrator (MODEL_CARD should be reviewed per model); no cloned voice'}
 for item in DATA['archival_images']:
  if item['id'] in archives:details['archival_media'].append({**item,'sha256':hashlib.sha256(archives[item['id']].read_bytes()).hexdigest()})
 (OUT/'PROVENANCE.json').write_text(json.dumps(details,indent=2)+'\n',encoding='utf8')
 (OUT/'EPISODE_SCRIPT.txt').write_text(DATA['title']+'\n\n'+'\n\n'.join(s['chapter']+'\n'+s['narration'] for s in DATA['scenes'])+'\n',encoding='utf8')
 (OUT/'YOUTUBE_DESCRIPTION.txt').write_text('The Great Molasses Flood of 1919: How an industrial storage tank failed in Boston, causing 21 deaths and forcing a reckoning over safety and accountability.\n\nArchival imagery is clearly labelled. Illustrated scenes are reconstructions, not original footage.\n\nResearch:\n'+'\n'.join(x['source']+': '+x['url'] for x in DATA['research'])+'\n\nArchival photo credits and licenses are in PROVENANCE.json.\n',encoding='utf8')

def main():
 p=argparse.ArgumentParser();p.add_argument('--piper-model');p.add_argument('--piper-config');p.add_argument('--use-espeak',action='store_true');p.add_argument('--preview-scenes',type=int,default=0);p.add_argument('--no-download',action='store_true');args=p.parse_args()
 archive=archival_assets(not args.no_download)
 pictures=make_plates(archive)
 if args.use_espeak:audio=gen_voice_espeak()
 else:
  if not args.piper_model or not args.piper_config:raise ValueError('Piper model and config required')
  audio=gen_voice_piper(Path(args.piper_model),Path(args.piper_config))
 captions(audio);make_thumbnail(archive);write_provenance(archive)
 duration=render(audio,pictures,args.preview_scenes)
 output=OUT/('Great_Molasses_Flood_1919.mp4' if not args.preview_scenes else 'Great_Molasses_Flood_PREVIEW.mp4')
 if output.stat().st_size<100_000:raise RuntimeError('Empty or implausible output')
 print('READY',output,'MB',round(output.stat().st_size/1024/1024,1),'DURATION',round(duration/60,2),'MINUTES')
if __name__=='__main__':main()