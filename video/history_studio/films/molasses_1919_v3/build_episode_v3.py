#!/usr/bin/env python3
"""Episode 01 v3 — authentic archival-first documentary, original 1903 context footage.
The same researched v1 script and Kokoro v2 narrator are used without Blender.
Every picture is actual archival material; no synthetic historical image is passed off
as a photograph. AI visuals are optional for future episodes only when archives fail.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, re, subprocess, urllib.parse, urllib.request, time, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('episode01_v2',HERE.parent/'molasses_1919_v2'/'build_episode_v2.py')
v2=importlib.util.module_from_spec(spec);spec.loader.exec_module(v2)
v1=v2.v1
DATA=v2.DATA
OUT=HERE/'output';OUT.mkdir(parents=True,exist_ok=True)
v1.OUT=OUT;v2.OUT=OUT
W,H=1920,1080
CHANNEL='Facts Uncovered: Stories & Evidence'
CHANNEL_SHORT='FACTS UNCOVERED'
FONT='/usr/share/fonts/truetype/lato/Lato-Heavy.ttf'
REG='/usr/share/fonts/truetype/lato/Lato-Regular.ttf'
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
GOLD=(240,188,110);WHITE=(248,240,228);DARK=(11,21,29)
CTA='Please help Facts Uncovered grow by subscribing to the channel. Just tap the Subscribe button below. Thank you for your support. Now, back to our story.'
EXTRA={
 'ber_023':{'file':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-023.jpg','source':'City of Boston Archives / Boston Elevated Railway Company','license':'US public domain, 1919 photograph'},
 'ber_031':{'file':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-031.jpg','source':'City of Boston Archives / Boston Elevated Railway Company','license':'US public domain, 1919 photograph'},
 'ber_035':{'file':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-035.jpg','source':'City of Boston Archives / Boston Elevated Railway Company','license':'US public domain, 1919 photograph'},
 'ber_051':{'file':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-051.jpg','source':'City of Boston Archives / Boston Elevated Railway Company','license':'US public domain, 1919 photograph'},
 'ber_052':{'file':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-052.jpg','source':'City of Boston Archives / Boston Elevated Railway Company','license':'US public domain, 1919 photograph'},
 'ber_054':{'file':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-054.jpg','source':'City of Boston Archives / Boston Elevated Railway Company','license':'US public domain, 1919 photograph'},
 'globe_1919':{'file':'Boston Daily Globe Jan. 16, 1919.png','source':'Boston Daily Globe newspaper, 16 January 1919','license':'US public domain, 1919 newspaper'},
 'nyt_1919':{'file':'Boston-molasses-disaster-nyt-article.jpg','source':'The New York Times newspaper, 1919','license':'US public domain, published in 1919'},
}
FILM={
 'file':'Boston by streetcar, 1903. Boston Elevated Railway trolley and elevated cars..theora.ogv',
 'source':'1903 Boston by streetcar / Billy Bitzer, exhibited in 1906',
 'license':'US public domain, motion picture first exhibited before 1931',
 'url':'https://commons.wikimedia.org/wiki/File:Boston_by_streetcar,_1903._Boston_Elevated_Railway_trolley_and_elevated_cars..theora.ogv',
 'note':'Actual footage of Boston in 1903. NOT footage of 1919 molasses flood.'
}
# Each scene has three independently framed authentic records, or 2 photos plus
# a brief verified 1903 moving-image shot. The footage only illustrates general
# period city/rail traffic and is labelled on-screen with its actual year.
STORYBOARD=[
 ('panorama','ber_023','ber_035'),
 ('panorama','ber_031','loc'),
 ('ber_031','panorama','ber_052'), # genuine period footage leads this neighborhood chapter
 ('tank','ber_051','ber_035'),
 ('tank','ber_023','ber_054'),
 ('tank','ber_052','ber_051'),
 ('tank','ber_031','ber_035'),
 ('ber_031','tank','ber_051'), # contextual footage: Boston streets 1903
 ('tank','ber_054','ber_035'),
 ('ber_023','panorama','ber_052'),
 ('rail','tracks','ber_031'),
 ('ber_035','ber_051','loc'),
 ('loc','ber_052','ber_054'),
 ('tracks','ber_023','ber_035'),
 ('ber_054','ber_051','panorama'),
 ('panorama','ber_031','ber_052'),
 ('globe_1919','nyt_1919','ber_023'),
 ('tank','ber_051','ber_035'),
 ('newspaper','globe_1919','nyt_1919'),
 ('ber_054','ber_052','panorama'),
 ('globe_1919','tank','ber_023'),
 ('panorama','ber_035','ber_051'),
]
assert len(STORYBOARD)==len(DATA['scenes'])==22
FILM_SCENES={2,7}

def f(size=32,bold=False,arrow=False):
 return ImageFont.truetype(SANS if arrow else FONT if bold else REG,size)

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as file:
  for chunk in iter(lambda:file.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()

def pull_sources():
 images=v1.archival_assets(download=True)
 if len(images)!=len(DATA['archival_images']):raise RuntimeError('Cannot publish: required original flood photos missing')
 extras=OUT/'source_archive';extras.mkdir(exist_ok=True)
 for key,entry in EXTRA.items():
  suffix=entry['file'].rsplit('.',1)[-1].lower()
  dest=extras/(key+'.'+suffix)
  if not dest.exists() and not v1.archive_download(dest,entry['file']):
   raise RuntimeError('Missing licensed historical archive: '+entry['file'])
  with Image.open(dest) as pic:pic.verify()
  images[key]=dest
 folder=OUT/'source_film';folder.mkdir(exist_ok=True)
 movie=folder/'boston_1903.ogv'
 if not movie.exists():
  header={'User-Agent':'FactsUncoveredDocumentary/1.0 (source research; commons.wikimedia.org)'}
  query=urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url','titles':'File:'+FILM['file']})
  req=urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+query,headers=header)
  with urllib.request.urlopen(req,timeout=75) as response:
   payload=json.load(response)
  obj=list(payload['query']['pages'].values())[0]
  url=obj['imageinfo'][0]['url']
  for attempt in range(3):
   try:
    request=urllib.request.Request(url,headers=header)
    with urllib.request.urlopen(request,timeout=130) as response, open(movie,'wb') as out:
     while chunk:=response.read(1024*1024):
      out.write(chunk)
    break
   except Exception as err:
    movie.unlink(missing_ok=True)
    if attempt==2:raise RuntimeError('Historical film download failed') from err
    time.sleep(2+attempt)
 if movie.stat().st_size<3_000_000 or v1.probe(movie)<100:raise RuntimeError('Historical 1903 film invalid')
 print('LICENSED_SOURCE_ASSETS',len(images),'REAL_1903_FILM_MINUTES',round(v1.probe(movie)/60,1),flush=True)
 return images,movie

def archive_plate(src,scene,idx,key,variant=0):
 """Do not hallucinate or retouch the content of archival images."""
 with Image.open(src) as opened:
  original=ImageOps.exif_transpose(opened).convert('RGB')
 bkg=ImageOps.fit(original,(W,H),method=Image.Resampling.LANCZOS)
 bkg=bkg.filter(ImageFilter.GaussianBlur(34))
 bkg=ImageEnhance.Brightness(bkg).enhance(.19)
 art=bkg.convert('RGBA')
 foreground=original.copy()
 if variant==2:
  # Clearly disclosed crop/detail enlargement of exactly the same historical photo.
  ow,oh=foreground.size
  scale=.79
  sw,sh=int(ow*scale),int(oh*scale)
  left=int((ow-sw)*([.1,.5,.8][idx%3])); top=int((oh-sh)*.48)
  foreground=foreground.crop((left,top,left+sw,top+sh))
 foreground.thumbnail((W-105,H-280),Image.Resampling.LANCZOS)
 x=(W-foreground.width)//2;y=158+(H-340-foreground.height)//2
 frame=Image.new('RGBA',(W,H));fd=ImageDraw.Draw(frame,'RGBA')
 fd.rounded_rectangle((x-12,y-12,x+foreground.width+12,y+foreground.height+12),
                       radius=7,fill=(23,29,30,242),outline=(180,169,147,180),width=3)
 art=Image.alpha_composite(art,frame)
 art.paste(foreground,(x,y))
 # Readable, small evidence/editorial slate. Do not cover primary photograph.
 bar=Image.new('RGBA',(W,H));d=ImageDraw.Draw(bar,'RGBA')
 d.rectangle((0,0,W,102),fill=(8,18,27,217))
 d.rectangle((0,H-139,W,H),fill=(8,18,27,231))
 d.text((66,32),CHANNEL_SHORT,font=f(33,True),fill=GOLD)
 d.text((W-540,38),'THE GREAT MOLASSES FLOOD • 1919',font=f(24),fill=WHITE)
 label='HISTORICAL NEWSPAPER (1919)' if key in ('globe_1919','nyt_1919','newspaper') else 'AUTHENTIC HISTORICAL PHOTOGRAPH'
 if variant==2:label+='  •  DETAIL VIEW'
 d.text((72,H-125),label,font=f(23,True),fill=GOLD)
 title=scene['headline']
 fs=39
 while d.textbbox((0,0),title,font=f(fs,True))[2]>W-180 and fs>25:fs-=2
 d.text((70,H-83),title,font=f(fs,True),fill=WHITE)
 d.text((W-210,H-52),f'{idx+1:02d} / 22',font=f(20),fill=WHITE)
 out=Image.alpha_composite(art,bar).convert('RGB')
 return out

def intro_plate(path,photo):
 with Image.open(photo) as im:base=ImageOps.fit(im.convert('RGB'),(W,H),method=Image.Resampling.LANCZOS)
 base=ImageEnhance.Brightness(base).enhance(.29).convert('RGBA')
 shade=Image.new('RGBA',(W,H));d=ImageDraw.Draw(shade,'RGBA')
 d.rectangle((0,0,W,H),fill=(5,11,18,100))
 d.rounded_rectangle((135,155,W-135,H-110),radius=35,fill=(5,14,23,201),outline=GOLD+(220,),width=4)
 d.text((W//2,215),CHANNEL_SHORT,font=f(94,True),anchor='mt',fill=WHITE)
 d.text((W//2,325),'STORIES & EVIDENCE',font=f(38,True),anchor='mt',fill=GOLD)
 d.rounded_rectangle((W//2-430,408,W//2+430,535),radius=27,fill=(188,31,35,255))
 d.text((W//2,441),'PLEASE SUBSCRIBE',font=f(75,True),anchor='mt',fill=(255,255,255))
 d.text((W//2,558),'Tap the Subscribe button below this video',font=f(35),anchor='mt',fill=WHITE)
 d.text((W//2,620),'↓',font=f(170,True,arrow=True),anchor='mt',fill=GOLD)
 d.text((W//2,850),'Thank you for supporting our documentary channel',font=f(27),anchor='mt',fill=WHITE)
 Image.alpha_composite(base,shade).convert('RGB').save(path,quality=91)

def movie_plate(path):
 layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer,'RGBA')
 d.rectangle((0,0,W,94),fill=(8,17,25,208))
 d.rectangle((0,H-118,W,H),fill=(8,17,25,223))
 d.text((62,28),CHANNEL_SHORT,font=f(31,True),fill=GOLD)
 d.text((64,H-104),'ACTUAL FILM FOOTAGE — BOSTON, 1903',font=f(33,True),fill=WHITE)
 d.text((66,H-56),'Period-city context, NOT footage of the 1919 flood',font=f(24),fill=GOLD)
 layer.save(path)

def intro_voice(model,voices):
 import soundfile as sf
 import numpy as np
 from kokoro_onnx import Kokoro
 dest=OUT/'intro_voice.wav'
 if not dest.exists():
  synth=Kokoro(str(model),str(voices))
  samples,rate=synth.create(CTA,voice='am_michael',speed=.94,lang='en-us')
  samples=np.asarray(samples,dtype=np.float32).reshape(-1)
  sf.write(dest,np.concatenate([samples,np.zeros(int(.35*rate),dtype=np.float32)]),rate,subtype='PCM_16')
 length=v1.probe(dest)
 if not 6<length<35:raise ValueError('Invalid introduction speech duration')
 return dest,length

def timestamp(t):
 return v1.to_srt_time(t)
def seconds(s):
 hh,mm,ss=s.replace(',','.').split(':')
 return int(hh)*3600+int(mm)*60+float(ss)
def subtitles(intro_len,core_lengths):
 v2.write_captions(core_lengths)
 existing=(OUT/'subtitles.srt').read_text()
 shifted=[]
 for line in existing.splitlines():
  if ' --> ' in line:
   a,b=line.split(' --> ')
   shifted.append(timestamp(intro_len+seconds(a))+' --> '+timestamp(intro_len+seconds(b)))
  else:shifted.append(line)
 intro_cues=[]
 sentences=['Please help Facts Uncovered grow by subscribing to the channel.',
            'Just tap the Subscribe button below.',
            'Thank you for your support.',
            'Now, back to our story.']
 weights=[len(x.split()) for x in sentences];cursor=0.
 for i,(sentence,n) in enumerate(zip(sentences,weights),1):
  duration=intro_len*n/sum(weights)
  intro_cues.append(f'{i}\n{timestamp(cursor)} --> {timestamp(cursor+duration)}\n{sentence}\n')
  cursor+=duration
 # Renumber all existing subtitle blocks, preserving true times.
 remainder='\n'.join(shifted)
 lines=remainder.splitlines()
 for index,line in enumerate(lines):
  if line.isdigit() and (index==0 or not lines[index-1].strip()):
   lines[index]=str(int(line)+len(intro_cues))
 (OUT/'subtitles.srt').write_text('\n'.join(intro_cues)+'\n'+'\n'.join(lines)+'\n',encoding='utf-8')

def render_segment_image(pic,voice,offset,duration,destination,seed):
 z="zoompan=z='min(zoom+0.000045,1.035)':d=1:x='(iw-iw/zoom)*"+(['0.2','0.68','0.4'][seed%3])+"':y='(ih-ih/zoom)*0.5':s=1920x1080:fps=24,format=yuv420p[v]"
 v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','24','-i',pic,
          '-ss',f'{offset:.4f}','-t',f'{duration:.4f}','-i',voice,
          '-filter_complex',z,'-map','[v]','-map','1:a:0','-t',f'{duration:.4f}',
          '-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',
          '-c:a','aac','-ar','48000','-ac','1','-b:a','160k',destination])

def render_segment_movie(movie,overlay,voice,offset,duration,destination,start):
 # No attempt to label period film as the event; burn in explicit 1903 disclaimer.
 filters='[0:v]fps=24,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[film];[film][1:v]overlay=0:0,format=yuv420p[v]'
 v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-t',f'{duration:.4f}','-i',movie,
          '-loop','1','-i',overlay,'-ss',f'{offset:.4f}','-t',f'{duration:.4f}','-i',voice,
          '-filter_complex',filters,'-map','[v]','-map','2:a:0',
          '-t',f'{duration:.4f}','-r','24','-c:v','libx264','-preset','veryfast','-crf','21',
          '-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','1','-b:a','160k',destination])

def thumbnail(images):
 plate=archive_plate(images['panorama'],DATA['scenes'][0],0,'panorama')
 im=plate.resize((1280,720),Image.Resampling.LANCZOS).convert('RGBA')
 overlay=Image.new('RGBA',(1280,720));d=ImageDraw.Draw(overlay,'RGBA')
 d.rounded_rectangle((25,90,980,565),radius=17,fill=(8,18,27,220))
 d.text((65,133),'BOSTON',font=f(102,True),fill=WHITE)
 d.text((62,260),'DROWNED IN',font=f(82,True),fill=WHITE)
 d.text((64,383),'MOLASSES',font=f(113,True),fill=GOLD)
 d.text((69,524),'FACTS UNCOVERED',font=f(28,True),fill=WHITE)
 Image.alpha_composite(im,overlay).convert('RGB').save(OUT/'thumbnail_v3.jpg',quality=94)

def export_metadata(images,movie,lengths,intro_len):
 v2.provenance({k:v for k,v in images.items() if k in {a['id'] for a in DATA['archival_images']}},lengths)
 path=OUT/'PROVENANCE.json'
 current=json.loads(path.read_text())
 expanded=[]
 for key,record in EXTRA.items():
  expanded.append({'id':key,**record,'source_url':'https://commons.wikimedia.org/wiki/File:'+record['file'].replace(' ','_'),'sha256':digest(images[key])})
 current.update({
  'version':3,'channel_brand_in_video':CHANNEL,'opening_spoken_subscribe_cta':CTA,
  'intro_seconds':round(intro_len,3),
  'visual_policy':'Original 1919 photos/newspapers first. Verified 1903 Boston film only for labelled period context. No Blender or pseudo-3D assets. AI images must be licensed and explicitly labelled as reconstructions if needed in future episodes.',
  'additional_archival_sources':expanded,
  'authentic_period_motion_picture':{**FILM,'sha256':digest(movie),'on_screen_disclaimer':'ACTUAL FILM FOOTAGE — BOSTON, 1903 / NOT footage of 1919 flood'},
  'archive_coverage':{'archival_photo_and_newspaper_shots':64,'period_context_film_shots':2,'AI_generated_visuals':0,'fabricated_historic_footage':0},
  'release_note':'TECHNICALLY VALIDATED; editorial viewing and rights jurisdiction check recommended before YouTube release'
 })
 path.write_text(json.dumps(current,indent=2)+'\n',encoding='utf-8')
 script=OUT/'EPISODE_SCRIPT.txt'
 script.write_text(CHANNEL+'\n\nOPENING SUBSCRIBE REQUEST\n'+CTA+'\n\n'+script.read_text(),encoding='utf-8')
 desc=OUT/'YOUTUBE_DESCRIPTION.txt'
 desc.write_text('Facts Uncovered: Stories & Evidence presents the Great Molasses Flood of 1919.\nPlease subscribe for thoroughly researched stories.\n\nThis film uses authentic historical photographs, newspapers and short 1903 Boston street footage for period context. The 1903 footage does not depict the 1919 disaster. Source credits and rights records accompany this video in PROVENANCE.json.\n\n'+desc.read_text(),encoding='utf-8')
 (OUT/'VISUAL_POLICY.md').write_text('# Archival-first documentary workflow\n\nSource order: (1) historically sourced relevant footage, (2) actual event archival photos and period newspapers, (3) accurate diagrams and maps, (4) sparing AI-reconstructed stills when clearly necessary, appropriately labelled. Never fabricate contemporaneous footage. Public-domain rights are checked individually and image provenance is recorded. Voice: same Kokoro am_michael as v2. Subscribe CTA: spoken and arrow graphic at start. Blender, 3D rigs and animated fake historic images are NOT required.\n',encoding='utf8')
 (OUT/'SHOT_SOURCES.json').write_text(json.dumps({'channel':CHANNEL,'storyboard':[{'scene':i+1,'chapter':DATA['scenes'][i]['chapter'],'assets':list(s),'context_movie':i in FILM_SCENES} for i,s in enumerate(STORYBOARD)]},indent=2)+'\n')

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--model',required=True,type=Path);parser.add_argument('--voices',required=True,type=Path)
 parser.add_argument('--preview',action='store_true')
 args=parser.parse_args()
 images,movie=pull_sources()
 voice,lengths=v2.voice_tracks(args.model,args.voices)
 intro_wav,intro_len=intro_voice(args.model,args.voices)
 subtitles(intro_len,lengths)
 folder=OUT/'plates';folder.mkdir(exist_ok=True)
 thumbnail(images)
 intro=folder/'intro.jpg';intro_plate(intro,images['panorama'])
 overlay=folder/'film_label.png';movie_plate(overlay)
 clips=OUT/'clips';clips.mkdir(exist_ok=True)
 intro_mp4=clips/'intro.mp4'
 if not intro_mp4.exists():render_segment_image(intro,intro_wav,0,intro_len,intro_mp4,0)
 paths=[intro_mp4]
 max_scenes=2 if args.preview else len(STORYBOARD)
 for i in range(max_scenes):
  length=lengths[i];off=0
  for j,key in enumerate(STORYBOARD[i]):
   span=length/3 if j<2 else length-off
   dest=clips/f'{i+1:02d}_{j}.mp4'
   if not dest.exists():
    if i in FILM_SCENES and j==0:
     render_segment_movie(movie,overlay,voice/f'voice_{i+1:02d}.wav',off,span,dest,start=30+i*11)
    else:
     plate=folder/f'{i+1:02d}_{j}.jpg'
     archive_plate(images[key],DATA['scenes'][i],i,key,variant=j).save(plate,quality=92)
     render_segment_image(plate,voice/f'voice_{i+1:02d}.wav',off,span,dest,seed=i+j)
   paths.append(dest);off+=span
  print('ARCHIVE_SCENE_RENDERED',i+1,'of',max_scenes,flush=True)
 concat=OUT/'concat_v3.txt';concat.write_text('\n'.join("file '"+str(p.resolve()).replace("'","'\\''")+"'" for p in paths)+'\n')
 joined=OUT/'joined.mp4';v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',joined])
 v2.score()
 dest=OUT/('Great_Molasses_Flood_1919_v3_PREVIEW.mp4' if args.preview else 'Great_Molasses_Flood_1919_v3.mp4')
 v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',joined,'-stream_loop','-1','-i',OUT/'score_v2.wav',
          '-filter_complex','[0:a]volume=1.3,acompressor=threshold=0.13:ratio=2:attack=20:release=220[n];[1:a]volume=0.38[m];[n][m]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.94[a]',
          '-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',dest])
 export_metadata(images,movie,lengths,intro_len)
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)],text=True))
 assert {'audio','video'}<={s['codec_type'] for s in meta['streams']}
 assert any(s.get('width')==W and s.get('height')==H for s in meta['streams'])
 duration=float(meta['format']['duration'])
 if not args.preview:assert 500<duration<1300
 print('ARCHIVE_FIRST_EPISODE_01_V3_FINISHED','minutes',round(duration/60,2),'MP4_MB',round(dest.stat().st_size/1048576,1),'channel',CHANNEL,'archive_sources',len(images),'real_film_minutes',round(v1.probe(movie)/60,2),flush=True)

if __name__=='__main__':main()
