#!/usr/bin/env python3
"""Archive-first, original Titanic documentary and 3 bespoke vertical Shorts.

Uses LOC/Wikimedia item metadata, source-vetted Piper voices, Pillow compositing,
FFmpeg AAC/H264 shots and audio-timed subtitles. No unlabelled recreation.
No YouTube upload: human review and source-specific rights assessment required.
"""
import json, re, sys, io, os, time, math, wave, random, hashlib, subprocess, textwrap
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE/'v2'/'renders'
PHOTOS=ROOT/'photos'
SLIDES=ROOT/'slides'
AUDIO=ROOT/'audio'
SHOTS=ROOT/'shots'
for d in (ROOT,PHOTOS,SLIDES,AUDIO,SHOTS): d.mkdir(parents=True,exist_ok=True)
PARTS=[json.loads((HERE/'v2'/f'script_{p}.json').read_text()) for p in ('01_05','06_10','11_15')]
CHAPTERS=[c for part in PARTS for c in part]
assert len(CHAPTERS)==15
PLAN={'long':[(ch['title'],ch['narration']) for ch in CHAPTERS],
      'shorts':json.loads((HERE/'narration.json').read_text())['shorts']}
s=requests.Session()
s.headers.update({'User-Agent':'FactsUncoveredHistoricalResearch/1.0 (educational history documentary; archives)'})
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
GOLD=(240,198,113); WHITE=(249,247,238); MUTED=(184,193,210); BG=(7,16,30)

def font(size,bold=False,serif=False):
    return ImageFont.truetype(SERIF if serif else BOLD if bold else FONT,int(size))
def wrap(draw,t,ft,w):
    words=t.split(); rows=[];line=''
    for word in words:
        test=(line+' '+word).strip()
        if line and draw.textbbox((0,0),test,font=ft)[2]>w:
            rows.append(line);line=word
        else:line=test
    if line:rows.append(line)
    return rows

ASSETS=[
 ('departure_3000','Titanic departure from Southampton 10 April 1912','wiki','1912 Titanic Departure.jpg'),
 ('belfast_drydock','Titanic in Belfast dry dock February 1912','wiki','Titanic at dry dock Thompson in Belfast, February 1912.jpg'),
 ('belfast_photo','Titanic at Belfast April 1912','wiki','Titanic Belfast 1912.jpg'),
 ('passengers_adeck','Passenger and child on Titanic aft promenade','wiki','Passengers of the RMS Titanic.jpg'),
 ('sea_trials','Titanic sea trials April 1912','wiki','RMS Titanic sea trials April 2, 1912.jpg'),
 ('departure_portrait','Titanic leaving Southampton','wiki','Titanic leaving Southampton.png'),
 ('departure_second','Titanic departing Southampton','wiki','Titanic departing Southampton.png'),
 ('titanic_at_dock','Titanic at Southampton dock','wiki','Titanic.jpg'),
 ('belfast_fitout','Titanic under construction at Belfast','wiki','RMS Titanic being fitted out at Harland and Wolff in Belfast, Ireland, with three funnels.jpg'),

 ('titanic_1911','Titanic at dock 1911','loc','2001704335'),
 ('titanic_stern','Stern and rudder in dry dock','loc','2001704333'),
 ('carpathia_dock','Carpathia in New York City','loc','2001704337'),
 ('survivors_carpathia','Survivors aboard Carpathia','loc','2001704332'),
 ('lifeboat_nara','Survivors in lifeboat','loc','93510852'),
 ('survivors_original_neg','Survivors on way to Carpathia','loc','2014690331'),
 ('montage_1912','1912 Titanic photographic montage','loc','96514444'),

 ('ship_southampton','Titanic, Southampton 1912','wiki','RMS Titanic passenger liner in Southampton.jpg'),
 ('dry_dock','Titanic in dry dock','wiki','RMS Titanic in Thompson Graving Dock.jpg'),
 ('dining_room','Titanic dining room','loc','96503966'),
 ('lifeboats','Lifeboats approaching Carpathia','loc','2001704327'),
 ('carpathia','Carpathia and Titanic lifeboats','loc','98509237'),
 ('survivors','Survivors on Carpathia','loc','2014691298'),
 ('charlotte','Charlotte Collyer and daughter','loc','2014699329'),
 ('white_star','White Star Line office in disaster aftermath','loc','2014690335'),
 ('rescue','Survivor rescue photographs','loc','93510852'),
 ('composite','1912 Titanic photographic montage','loc','96514444'),
]
def find_urls(kind,value):
    try:
        if kind=='wiki':
            r=s.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','titles':'File:'+value,'iiurlwidth':2200},timeout=40)
            r.raise_for_status()
            data=r.json()
            pages=data.get('query',{}).get('pages',{}).values()
            out=[]
            for page in pages:
                for ii in page.get('imageinfo',[]):
                    ext=ii.get('extmetadata',{})
                    status=(ext.get('LicenseShortName') or {}).get('value','')
                    if not any(z in status.lower() for z in ['public domain','cc0','cc by','cc-by','pd']):
                        print('UNKNOWN_WIKI_LICENSE',value,status,flush=True);continue
                    out += [ii.get('thumburl'),ii.get('url')]
            return [z for z in out if z]
        r=s.get('https://www.loc.gov/item/'+value+'/',params={'fo':'json'},timeout=40)
        r.raise_for_status()
        data=r.json()
        rec=data.get('item',{})
        rights=str(rec.get('rights_advisory','') or rec.get('rights',''))
        if 'no known restrictions' not in rights.lower():
            print('RIGHTS_NOTICE_UNCLEAR',value,rights[:120],flush=True)
        urls=data.get('image_url',[]) or rec.get('image_url',[])
        resources=data.get('resources',[])
        for resource in resources[:2]:
            for sub in resource.get('files',[]):
                if isinstance(sub,list):
                    urls += [x.get('url') for x in sub if isinstance(x,dict)]
                elif isinstance(sub,dict):urls.append(sub.get('url'))
        return sorted([u for u in urls if isinstance(u,str) and u.lower().split('?')[0].endswith(('.jpg','.jpeg','.png'))],key=lambda x:('v.jpg' in x,'r.jpg' in x),reverse=True)
    except Exception as e:
        print('ASSET_METADATA_ERROR',kind,value,str(e)[:160],flush=True);return []

def get_pic(rec):
    key,label,kind,value=rec;path=PHOTOS/(key+'.jpg')
    if path.exists() and path.stat().st_size>15000:return (key,path,label,kind,value)
    candidates=find_urls(kind,value)
    for u in candidates[:6]:
        try:
            resp=s.get(u,timeout=60)
            resp.raise_for_status()
            if len(resp.content)<12000:continue
            im=Image.open(io.BytesIO(resp.content))
            im.load()
            if min(im.size)<230:continue
            im=ImageOps.exif_transpose(im).convert('RGB')
            im.thumbnail((2500,2500),Image.Resampling.LANCZOS)
            im.save(path,'JPEG',quality=93)
            print('ARCHIVE_OK',key,im.size,len(resp.content),flush=True)
            return (key,path,label,kind,value)
        except Exception as e: print('ASSET_VARIANT_ERROR',key,str(e)[:90],flush=True)
    return None

def fetch_photos():
    with ThreadPoolExecutor(max_workers=5) as ex: rs=list(ex.map(get_pic,ASSETS))
    found=[x for x in rs if x]
    manifest=[{'key':x[0],'title':x[2],'source':('https://www.loc.gov/item/'+x[4]+'/' if x[3]=='loc' else 'https://commons.wikimedia.org/wiki/File:'+x[4].replace(' ','_')),'original_file':x[1].name,'rights_status':'Review individual item before publication','sha256':hashlib.sha256(x[1].read_bytes()).hexdigest()} for x in found]
    (ROOT/'source_provenance.json').write_text(json.dumps(manifest,indent=2))
    if len(found)<6:
        raise RuntimeError('Only '+str(len(found))+' cleared archival media were retrievable; refusing synthetic history film. Retry archives or add individually licensed photos.')
    return {x[0]:x[1] for x in found}

def gradient(size):
    W,H=size;im=Image.new('RGB',size)
    d=ImageDraw.Draw(im)
    for y in range(H):
        q=y/max(H,1)
        d.line((0,y,W,y),fill=(int(7+q*7),int(16+q*11),int(30+q*16)))
    return im

def fit_photo(path,size):
    im=Image.open(path).convert('RGB')
    w,h=size; sw,sh=im.size
    scale=max(w/sw,h/sh)
    im=im.resize((max(w,round(sw*scale)),max(h,round(sh*scale))),Image.Resampling.LANCZOS)
    x=(im.width-w)//2;y=(im.height-h)//2
    im=im.crop((x,y,x+w,y+h))
    im=ImageEnhance.Contrast(im).enhance(1.10)
    return im

def panels(size,heading,label,photo_path=None,mode='archive',index=0):
    W,H=size; vertical=H>W
    im=gradient(size)
    d=ImageDraw.Draw(im,'RGBA')
    padding=58 if not vertical else 48
    header_h=205 if not vertical else 380
    if photo_path:
        ph_y=header_h;ph_h=H-header_h-(180 if not vertical else 320)
        ph=fit_photo(photo_path,(W,ph_h))
        im.paste(ph,(0,ph_y))
        overlay=Image.new('RGBA',size,(0,0,0,0));o=ImageDraw.Draw(overlay)
        o.rectangle((0,ph_y,W,ph_y+ph_h),fill=(7,16,30,55))
        for i in range(170):
            y=ph_y+ph_h-170+i
            if y>=ph_y+ph_h:break
            o.line((0,y,W,y),fill=(7,16,30,int(i/170*225)))
        im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
        d=ImageDraw.Draw(im,'RGBA')
    d.rectangle((0,0,W,header_h),fill=(6,15,28,255))
    d.rectangle((padding,29 if not vertical else 55,padding+78,35 if not vertical else 61),fill=GOLD)
    d.text((padding,45 if not vertical else 73),'FACTS UNCOVERED  /  STORIES & EVIDENCE',font=font(24 if not vertical else 23,True),fill=WHITE)
    hft=font(54 if not vertical else 56,True,True)
    title_lines=wrap(d,heading,hft,W-padding*2)
    if len(title_lines)>(2 if not vertical else 3):
        hft=font(44 if not vertical else 47,True,True)
        title_lines=wrap(d,heading,hft,W-padding*2)
    line_y=112 if not vertical else 145
    for t in title_lines[:(2 if not vertical else 3)]:
        d.text((padding,line_y),t,font=hft,fill=WHITE)
        line_y+=int(hft.size*1.15)
    bottom_start=H-(180 if not vertical else 320)
    d.rectangle((0,bottom_start,W,H),fill=(7,16,30,253))
    d.rectangle((padding,bottom_start+35,padding+45,bottom_start+41),fill=GOLD)
    cap=font(28 if not vertical else 32,True)
    label_lines=wrap(d,label.upper(),cap,W-padding*2)
    y=bottom_start+56
    for line in label_lines[:3]:
        d.text((padding,y),line,font=cap,fill=GOLD);y+=40
    small='ORIGINAL DOCUMENTARY  •  1912'
    small2='ARCHIVAL PHOTOGRAPH' if mode=='archive' else 'ORIGINAL EXPLANATORY GRAPHIC'
    d.text((padding,H-51 if not vertical else H-98),small,font=font(19 if not vertical else 24),fill=MUTED)
    d.text((W-padding-(d.textbbox((0,0),small2,font=font(18 if not vertical else 20))[2]),H-51 if not vertical else H-66),small2,font=font(18 if not vertical else 20),fill=MUTED)
    return im

def diagram(size,subject,label):
    W,H=size;im=panels(size,subject,label,None,'graphic')
    d=ImageDraw.Draw(im)
    vertical=H>W
    top=350 if vertical else 230
    bottom=H-(380 if vertical else 230)
    cx=W//2;cy=(top+bottom)//2
    variant=GRAPHIC_CHAPTERS.get(CURRENT_CHAPTER,'timeline')
    if variant=='survival':
        rows=[('FIRST CLASS',62.46),('SECOND CLASS',41.40),('THIRD CLASS',25.21)]
        for j,(name,pct) in enumerate(rows):
            y=top+20+j*(150 if vertical else 112)
            d.text((110,y),name,font=font(35,True),fill=WHITE)
            d.rectangle((110,y+50,W-115,y+76),fill=(55,67,85))
            d.rectangle((110,y+50,110+int((W-225)*pct/100),y+76),fill=GOLD)
            d.text((W-115,y+10),f'{pct:.1f}%',font=font(36,True),anchor='ra',fill=GOLD)
    elif variant=='inquiry':
        for j,(name,count) in enumerate([('U.S. SENATE','82 WITNESSES'),('BRITISH COMMISSION','97 WITNESSES'),('BRITISH HEARINGS','37 PUBLIC SITTINGS')]):
            y=top+j*(140 if vertical else 105)
            d.rectangle((110,y,W-110,y+85),outline=GOLD,width=3)
            d.text((140,y+10),name,font=font(29 if vertical else 38,True),fill=WHITE)
            d.text((140,y+49),count,font=font(25 if vertical else 30),fill=GOLD)
    elif variant=='wireless':
        for j,(tm,desc) in enumerate([('12:15 AM','CQD DISTRESS'),('12:25 AM','CARPATHIA ANSWERS'),('2:20 AM','SHIP FOUNDERED')]):
            y=top+j*(140 if vertical else 110)
            d.ellipse((110,y+19,143,y+52),fill=GOLD)
            d.text((160,y+5),tm,font=font(40,True),fill=WHITE)
            d.text((160,y+57),desc,font=font(27),fill=GOLD)
    elif variant=='discovery':
        for j,desc in enumerate(['SEPTEMBER 1, 1985','FRENCH & U.S. SCIENTISTS','DEBRIS FIELD → BOILER','WRECK IDENTIFIED']):
            y=top+j*(135 if vertical else 93)
            d.text((W//2,y),desc,font=font(34 if vertical else 42,True),anchor='mt',fill=GOLD if j%2==0 else WHITE)
    elif variant=='modern':
        for j,desc in enumerate(['715,000 PHOTOGRAPHS','DIGITAL WRECK MODEL','SCIENTIFIC SIMULATION','1914 SOLAS LEGACY']):
            y=top+j*(135 if vertical else 93)
            d.text((W//2,y),desc,font=font(32 if vertical else 42,True),anchor='mt',fill=GOLD if j%2==0 else WHITE)
    elif variant in ('turn','breakup','rescue','ship','passengers'):
        for j,desc in enumerate({
            'turn':['11:40 PM','LOOKOUT ALARM','MURDOCH TURNS','ICE STRIKES STARBOARD'],
            'breakup':['BOW DESCENDS','STRUCTURE UNDER STRESS','HULL FRACTURE','2:20 AM • SANK'],
            'rescue':['CQD RECEIVED','CARPATHIA TURNS','LIFEBOATS FOUND','SURVIVORS BROUGHT ABOARD'],
            'ship':['BELFAST • SHIPYARD','WATERTIGHT COMPARTMENTS','PROGRESSIVE FLOODING','DESIGN LIMIT REACHED'],
            'passengers':['1,316 PASSENGERS','885 CREW','2,201 ABOARD','BRITISH INQUIRY COUNT']}[variant]):
            y=top+j*(135 if vertical else 93)
            d.rectangle((108,y,W-108,y+75),outline=GOLD,width=2)
            d.text((W//2,y+16),desc,anchor='mt',font=font(30 if vertical else 37,True),fill=WHITE)
    elif 'lifeboat' in subject.lower() or 'boat' in label.lower():
        count=20;cols=5 if vertical else 10;gap=(W-130)//cols
        rows=math.ceil(count/cols)
        for i in range(count):
            x=66+(i%cols)*gap;y=top+65+(i//cols)*(145 if vertical else 105)
            d.arc((x,y,x+gap-28,y+58),start=0,end=180,fill=GOLD,width=5)
            d.line((x+5,y+29,x+gap-32,y+29),fill=WHITE,width=3)
        d.text((cx,cy+115 if vertical else cy+115),'20 BOATS  /  NOT ENOUGH SEATS',font=font(35 if vertical else 47,True),anchor='mm',fill=WHITE)
    elif 'damage' in subject.lower() or 'compartment' in label.lower():
        left=75;right=W-75;deck=int(cy-45)
        d.polygon([(left,deck),(right,deck),(right-100,deck+220),(left+110,deck+220)],fill=(32,62,82),outline=GOLD,width=5)
        for i in range(1,7):
            x=left+(right-left)*i//7
            d.line((x,deck,x,deck+225),fill=WHITE,width=4)
        for i in range(4):
            x=left+45+i*min(180,(W-150)//7)
            d.rectangle((x,deck+115,x+120,deck+216),fill=(40,130,175))
        d.text((cx,deck+300),'FLOODING CROSS-SECTION  /  SCHEMATIC',font=font(31 if vertical else 34,True),anchor='mm',fill=WHITE)
    elif 'ice' in subject.lower() or 'warning' in label.lower():
        d.line((cx,top+70,cx,bottom-80),fill=GOLD,width=7)
        for i,txt in enumerate(['ICE REPORTED','MESSAGES RECEIVED','11:40 PM  COLLISION']):
            yy=top+110+i*(145 if vertical else 100)
            d.ellipse((cx-14,yy-14,cx+14,yy+14),fill=GOLD)
            d.text((cx-40,yy-20),txt,font=font(32 if vertical else 39,True),anchor='ra',fill=WHITE)
    else:
        d.ellipse((cx-190,cy-190,cx+190,cy+190),outline=GOLD,width=13)
        d.line((cx,cy,cx-100,cy-90),fill=WHITE,width=12)
        d.line((cx,cy,cx+125,cy-70),fill=WHITE,width=10)
        d.text((cx,cy+270 if vertical else cy+240),'11:40 PM  →  2:20 AM',font=font(37 if vertical else 49,True),anchor='mm',fill=WHITE)
    return im

def split_speech(t,word_limit=75):
    sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',t)
    # Abbreviation guard, e.g. p.m. on is lower-case and remains within scene.
    chunks=[];cur=[]
    for v in sentences:
        if cur and len((' '.join(cur)+' '+v).split())>word_limit:
            chunks.append(' '.join(cur));cur=[]
        cur.append(v)
    if cur:chunks.append(' '.join(cur))
    return chunks

def synth_voice():
    from piper.voice import PiperVoice
    sys.path.insert(0,str(HERE.parents[2]))
    from video.production_voice_tracks import voice_files
    model, config, card=voice_files(ROOT/'voice-model','norman')
    print('PIPER_LICENSE_REVIEWED',card,flush=True)
    return PiperVoice.load(str(model),config_path=str(config))

def synth(t,stem,voice):
    out=AUDIO/(stem+'.wav')
    if not out.exists():
        with wave.open(str(out),'wb') as h:voice.synthesize_wav(t,h)
    with wave.open(str(out),'rb') as h:dur=h.getnframes()/h.getframerate()
    if not 0.5<dur<180:raise RuntimeError('Invalid voice duration '+str(dur))
    return out,dur

def sec_stamp(t):
    ms=round(t*1000)
    a,ms=divmod(ms,3600000);b,ms=divmod(ms,60000);c,ms=divmod(ms,1000)
    return f'{a:02}:{b:02}:{c:02},{ms:03}'
def subtitles(text,st,duration,shorts=False):
    words=text.split()
    cap=7 if shorts else 12;parts=[' '.join(words[i:i+cap]) for i in range(0,len(words),cap)]
    total=sum(len(x.split()) for x in parts);clock=st;arr=[]
    for item in parts:
        dt=duration*len(item.split())/total
        arr.append((clock,clock+dt,item));clock+=dt
    return arr
def save_srt(entries,dest):
    dest.write_text('\n'.join(f'{i}\n{sec_stamp(a)} --> {sec_stamp(b)}\n{c}\n' for i,(a,b,c) in enumerate(entries,1)),encoding='utf8')

def image_slide(size,heading,label,path,graphic=False):
    s=diagram(size,heading,label) if graphic else panels(size,heading,label,path)
    return s

def ffmpeg_shot(img,aud,duration,out,size,caption=None):
    w,h=size
    # Each shot gets a small 4-6% photographic push-in. Audio length controls runtime.
    frames=max(1,math.ceil(duration*24))
    vf=(f"zoompan=z='min(zoom+0.00022,1.055)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={w}x{h}:fps=24,format=yuv420p")
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(img),'-i',str(aud),
             '-filter_complex',f'[0:v]{vf}[v]','-map','[v]','-map','1:a','-t',f'{duration:.3f}',
             '-c:v','libx264','-preset','veryfast','-crf','25','-pix_fmt','yuv420p',
             '-r','24','-c:a','aac','-b:a','160k','-ar','44100','-ac','1','-movflags','+faststart',str(out)]
    subprocess.run(command,check=True)
def concat(parts,dest):
    listing=SHOTS/(dest.stem+'_concat.txt')
    listing.write_text(''.join("file '"+str(x.resolve()).replace("'","'\\''")+"'\n" for x in parts))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),
                    '-c','copy','-movflags','+faststart',str(dest)],check=True)

def pick(keys,pics,i):
    # Rotate actual archival plates across scenes; never repeat the first photo throughout a chapter.
    available=[pics[k] for k in keys if k in pics]
    return available[i%len(available)] if available else list(pics.values())[i%len(pics)]

SCENE_KEYS=[
['departure_3000','titanic_1911','ship_southampton','sea_trials'],
['belfast_drydock','belfast_fitout','titanic_stern','dry_dock','belfast_photo'],
['passengers_adeck','departure_second','dining_room','departure_portrait'],
['belfast_drydock','departure_3000','titanic_stern','sea_trials'],
['departure_second','sea_trials','titanic_1911'],
['titanic_1911','sea_trials','departure_3000','titanic_stern'],
['belfast_drydock','titanic_stern','belfast_photo'],
['montage_1912','departure_second','titanic_1911'],
['lifeboats','lifeboat_nara','survivors_original_neg','departure_3000'],
['passengers_adeck','survivors_carpathia','lifeboats','charlotte'],
['montage_1912','sea_trials','titanic_stern','lifeboats'],
['lifeboat_nara','survivors_original_neg','carpathia_dock','survivors_carpathia'],
['montage_1912','survivors','lifeboat_nara'],
['titanic_1911','titanic_stern','belfast_photo','dry_dock'],
['sea_trials','titanic_stern','departure_3000','passengers_adeck']
]
CHAPTER_LABELS=[
'11:40 PM • THE COUNTDOWN','BELFAST • SHIPBUILDING','PASSENGERS AND CREW',
'20 BOATS • 1,178 PLACES','CARONIA • BALTIC','COLLISION • 11:40 PM',
'PROGRESSIVE FLOODING','WIRELESS • CARPATHIA','EVACUATION TIMELINE',
'SURVIVAL BY CLASS','2:20 AM • APRIL 15','RESCUE • CARPATHIA',
'1912 • OFFICIAL INQUIRIES','DISCOVERY • SEPTEMBER 1985',
'2025 DIGITAL SCAN • SAFETY LEGACY'
]
GRAPHIC_CHAPTERS={0:'timeline',1:'ship',2:'passengers',3:'lifeboats',4:'ice',5:'turn',6:'compartments',
7:'wireless',8:'lifeboats',9:'survival',10:'breakup',11:'rescue',12:'inquiry',13:'discovery',14:'modern'}
SHOT_LOG=[]
IMAGE_MANIFEST=[]
CURRENT_CHAPTER=0

def create_long(pics,voice):
    global CURRENT_CHAPTER
    parts=[];srt=[];now=0
    chapter_times=[]
    for chapter,(title,script) in enumerate(PLAN['long']):
        chapter_times.append({'chapter':chapter+1,'title':title,'start_seconds':round(now,2)})
        CURRENT_CHAPTER=chapter
        segments=split_speech(script)
        print('CHAPTER',chapter+1,title,'SCENES',len(segments),flush=True)
        for i,words in enumerate(segments):
            basename=f'L{chapter+1:02}_{i+1:02}'
            wav,dur=synth(words,basename,voice)
            choice=pick(SCENE_KEYS[chapter],pics,i)
            graphic=(i%3==1 or (i%5==4 and chapter in GRAPHIC_CHAPTERS))
            heading=title.upper()
            label=CHAPTER_LABELS[chapter]
            frame=image_slide((1920,1080),heading,label,choice,graphic)
            png=SLIDES/(basename+'.jpg');frame.save(png,quality=91,optimize=True)
            mp4=SHOTS/(basename+'.mp4')
            ffmpeg_shot(png,wav,dur,mp4,(1920,1080))
            parts.append(mp4);srt += subtitles(words,now,dur)
            SHOT_LOG.append({'shot':basename,'chapter':chapter+1,'duration_seconds':round(dur,2),
                'source_refs':CHAPTERS[chapter]['source_refs'],
                'visual': 'ORIGINAL DIAGRAM' if graphic else choice.name,
                'photo_source_url': ('Original artwork' if graphic else next((it['source'] for it in IMAGE_MANIFEST if it['original_file']==choice.name),'See source_provenance.json')),
                'narration_excerpt':words[:200]})
            now+=dur
    final=ROOT/'Titanic_Complete_Story_1080p.mp4'
    concat(parts,final)
    save_srt(srt,ROOT/'Titanic_Complete_Story_1080p.srt')
    (ROOT/'shot_list.json').write_text(json.dumps(SHOT_LOG,indent=2))
    (ROOT/'chapter_times.json').write_text(json.dumps(chapter_times,indent=2))
    def chapter_stamp(seconds):
        mm=int(seconds//60);ss=int(seconds%60)
        return f'{mm:02}:{ss:02}'
    (ROOT/'CHAPTERS_FOR_YOUTUBE.txt').write_text('\n'.join(
        chapter_stamp(ch['start_seconds'])+'  '+ch['title'] for ch in chapter_times)+'\n')
    (ROOT/'chapter_sources.json').write_text(json.dumps([{'title':c['title'],'source_refs':c['source_refs']} for c in CHAPTERS],indent=2))
    print('DOCUMENTARY_SECONDS',round(now,1),'SHOT_COUNT',len(parts),flush=True)
    return final

def create_short(item,pics,voice):
    name=item['key'];script=item['speech'];chunks=split_speech(script,21)
    waveparts=[];captions=[];now=0;parts=[]
    for i,chunk in enumerate(chunks):
        wav,dur=synth(chunk,name+f'_{i:02}',voice)
        lab=item['labels'][min(len(item['labels'])-1, i*len(item['labels'])//max(1,len(chunks)))]
        keys=(['ship_southampton','composite','lifeboats'] if '160_Minutes' in name else
              ['lifeboats','carpathia','survivors'] if 'Lifeboats' in name else
              ['ship_southampton','dining_room','composite'])
        pic=pick(keys,pics,i)
        graphic=(i==1 or (i==3 and len(chunks)>4))
        frame=image_slide((1080,1920),item['title'].upper(),lab,pic,graphic)
        png=SLIDES/(name+f'_{i:02}.jpg');frame.save(png,quality=91)
        mp4=SHOTS/(name+f'_{i:02}.mp4')
        ffmpeg_shot(png,wav,dur,mp4,(1080,1920))
        parts.append(mp4)
        captions+=subtitles(chunk,now,dur,True);now+=dur
    no_cap=ROOT/(name+'_no_caption.mp4')
    concat(parts,no_cap)
    srt=ROOT/(name+'.srt');save_srt(captions,srt)
    dest=ROOT/(name+'.mp4')
    # Burn large smartphone captions over lower-middle safe area.
    caption_dir=ROOT/'caption-text'
    caption_dir.mkdir(exist_ok=True)
    filters=["drawbox=x=36:y=1315:w=1008:h=160:color=0x07101e@0.82:t=fill"]
    for j,(start,end,caption) in enumerate(captions):
        words=caption.split()
        if len(caption)>34:
            mid=max(1,len(words)//2)
            caption=' '.join(words[:mid])+'\n'+' '.join(words[mid:])
        caption_file=caption_dir/(name+f'_{j:02}.txt')
        caption_file.write_text(caption,encoding='utf8')
        filters.append(f"drawtext=fontfile={BOLD}:textfile={caption_file}:fontsize=44:fontcolor=white:bordercolor=black:borderw=3:line_spacing=7:x=(w-text_w)/2:y=1340:enable='between(t,{start:.3f},{end:.3f})'")
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(no_cap),'-vf',','.join(filters),
                    '-c:v','libx264','-preset','veryfast','-crf','20','-c:a','copy','-movflags','+faststart',str(dest)],check=True)
    no_cap.unlink()
    return dest

def thumbnail(pics):
    image=panels((1920,1080),'TITANIC: THE COMPLETE STORY','THE EVIDENCE • 1912–2025',pick(['departure_3000','ship_southampton','titanic_1911'],pics,0))
    image.save(ROOT/'Titanic_Thumbnail_1920x1080.jpg',quality=94)

def verify(files):
    records=[]
    for item in files:
        out=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(item)])
        data=json.loads(out);streams=data['streams']
        types={st['codec_type'] for st in streams}
        assert {'audio','video'}<=types,item
        assert item.stat().st_size>250000,item
        records.append({'name':item.name,'seconds':float(data['format']['duration']),'bytes':item.stat().st_size,
                        'streams':[{'type':v['codec_type'],'codec':v['codec_name'],'width':v.get('width'),'height':v.get('height')} for v in streams]})
    (ROOT/'technical_QA.json').write_text(json.dumps(records,indent=2))
    return records

def main():
    pics=fetch_photos()
    IMAGE_MANIFEST.extend(json.loads((ROOT/'source_provenance.json').read_text()))
    voice=synth_voice()
    files=[create_long(pics,voice)]
    for item in PLAN['shorts']:files.append(create_short(item,pics,voice))
    thumbnail(pics)
    qa=verify(files)
    print('DELIVERABLES_READY',json.dumps(qa),flush=True)
    (ROOT/'RESEARCH_SOURCES.json').write_text((HERE/'v2'/'sources.json').read_text())
    (ROOT/'REVIEW_REQUIRED.txt').write_text('Research-backed draft video: validate each photo right, accuracy, narration quality and visual presentation before publication. Not approved for YouTube upload.\n')
    (ROOT/'PUBLISHING_COPY.md').write_text('''# Facts Uncovered: Stories & Evidence — Titanic
## Main YouTube title
The Titanic: The Complete Story | What Really Happened in 1912?
## Description
What really happened aboard RMS Titanic? This evidence-based documentary traces construction, the Atlantic crossing, ice warnings, the final 160 minutes, survivors, official inquiries, the 1985 wreck discovery and 2025 digital scans.
Research draws on the 1912 British Wreck Commissioner report, U.S. Senate investigation, Woods Hole, NOAA, IMO and UCL. Historical archive photographs are distinguished from original educational diagrams. The investigation reports disagreed on exact passenger/survival totals; context is included.
Subscribe to Facts Uncovered: Stories & Evidence for historical investigations.
All sources: RESEARCH_SOURCES.json. Image-by-image credits: source_provenance.json. Chapter timecodes: CHAPTERS_FOR_YOUTUBE.txt.
#Titanic #TitanicDocumentary #HistoryDocumentary

## Short 1 title
Titanic Sank in Just 160 Minutes #Shorts
## Short 2 title
Why Titanic Had Too Few Lifeboats #Shorts
## Short 3 title
Titanic Was Warned About Ice Before the Collision #Shorts

## Keywords
Titanic history, Titanic complete story, Titanic documentary, Titanic sinking explained, Titanic real footage, Titanic final hours, RMS Titanic, Titanic iceberg, Titanic lifeboats, Titanic passengers, Titanic survivors, Titanic official inquiry, shipwreck discovery, 1912 historical documentary, Titanic wreck scan 2025
''')
    (ROOT/'EDITORIAL_REVIEW_REQUIRED.txt').write_text(
      'Draft exports require human visual/audio review and individual publication rights verification. '
      'Library of Congress notes no known restrictions for several images but does not grant publication rights. '
      'Original explanatory diagrams are marked; no historical sinking footage is claimed. '
      'Narration uses the pre-vetted public-domain LibriVox-derived Piper Norman voice, not the previously '
      'approved Episode 01 narrator, which was unavailable as a reusable file.\n')
if __name__=='__main__':main()
