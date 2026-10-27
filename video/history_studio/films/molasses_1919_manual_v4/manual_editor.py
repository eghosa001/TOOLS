#!/usr/bin/env python3
"""Editorial-first renderer. The story-to-image choices are explicitly authored.
No fallback media, randomized slides, sentence-to-photo classifiers, or uploads.
The actual final render is blocked if any required image or voice asset is absent.

Workflow:
  python manual_editor.py storyboard --episode /path/to/episode.json
  python manual_editor.py render --episode /path/to/episode.json --model model.onnx --voices voices.bin
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from shot_map import MANUAL_SHOTS

HERE=Path(__file__).resolve().parent
OUT=HERE/'output'
W,H=1920,1080
BG=(16,24,33); WHITE=(239,234,222); GOLD=(205,162,92); MUTED=(173,187,190); AMBER=(171,94,54)
FONT_B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_R='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
for f in (FONT_B,FONT_R,FONT_SERIF):
    if not Path(f).exists(): raise RuntimeError('Font missing; replace FONT_* with an available local font')

ASSETS={
 'panorama':{'filename':'BostonMolassesDisaster.jpg','source':'https://commons.wikimedia.org/wiki/File:BostonMolassesDisaster.jpg','status':'US public-domain historical 1919 photograph'},
 'tank':{'filename':'North End molasses tank.jpg','source':'https://commons.wikimedia.org/wiki/File:North_End_molasses_tank.jpg','status':'US public domain, photo before January 15 1919'},
 'rail':{'filename':'Boston 1919 molasses disaster - el train structure.jpg','source':'https://commons.wikimedia.org/wiki/File:Boston_1919_molasses_disaster_-_el_train_structure.jpg','status':'US public domain, January 1919 damage'},
 'tracks':{'filename':'GreatMolassesFlood 1919-Wreckage under the elevated tracks.jpg','source':'https://commons.wikimedia.org/wiki/File:GreatMolassesFlood_1919-Wreckage_under_the_elevated_tracks.jpg','status':'US public domain, 1919'},
 'loc':{'filename':'Boston, Mass. Boston molasses explosion 14968a.jpg','source':'https://www.loc.gov/item/2017679979/','status':'Library of Congress American Red Cross photo: no known publication restrictions'},
}
GRAPHICS={
 'site':('NORTH END, BOSTON','Commercial Street · Copps Hill Wharf','location'),
 'railway':('THE ELEVATED RAILWAY','The tracks ran beside the storage tank','location'),
 'risk':('AN INDUSTRIAL SITE','Close to workers, homes and public transport','hazard'),
 'dimensions':('A GIANT STEEL CYLINDER','About 50 feet high · 90 feet across','tank'),
 'shipment':('SHIP  →  TANK  →  RAIL','Molasses moved through an industrial supply chain','flow'),
 'molasses':('SUGAR PROCESSING','Molasses was an industrial by-product','flow'),
 'process':('INDUSTRIAL ALCOHOL','Molasses → fermentation → distillation','flow'),
 'pressure':('MORE DEPTH. MORE PRESSURE.','Pressure increases toward the base','pressure'),
 'leak':('LEAKS WERE REPORTED','The steel structure was showing warning signs','hazard'),
 'paint':('PAINT DID NOT REPAIR THE TANK','Historical accounts describe concealing the leaks','hazard'),
 'warning':('VISIBLE DANGER','Repeated warnings require corrective action','hazard'),
 'steel':('INADEQUATE STEEL','Later analysis questioned thickness and strength','steel'),
 'rivets':('RIVETED JOINTS','Vulnerable connections were placed under heavy load','steel'),
 'crack':('STRUCTURAL FAILURE','Stress can concentrate around openings and rivets','steel'),
 'weather':('A MILD WINTER AFTERNOON','Temperature was a possible contributing condition','date'),
 'date':('JANUARY 15, 1919','Commercial Street · Boston North End','date'),
 'rupture':('THE TANK RUPTURED','A sudden loss of containment','tank'),
 'wave':('A MOVING MASS OF MOLASSES','Impact force came from quantity and speed','wave'),
 'speed':('AN ESTIMATED 35 MPH','A reported early speed, not a direct instrument reading','speed'),
 'volume':('2.3 MILLION GALLONS','Approximately 8.7 million litres released','volume'),
 'victims':('21 PEOPLE KILLED','About 150 others were injured','victims'),
 'names':('REMEMBER THE VICTIMS','Pasquale Iantosca · Maria Distasio','victims'),
 'firehouse':('ENGINE 31','Firefighter George Layhe was among the dead','victims'),
 'rescue':('THE RESCUE','Wreckage and sticky syrup made movement difficult','teams'),
 'teams':('EMERGENCY RESPONSE','Police · Firefighters · Navy cadets · Red Cross','teams'),
 'cleanup':('THE CLEANUP','The streets and buildings were coated in molasses','flow'),
 'saltwater':('WATER FROM THE HARBOR','Seawater was used to wash away the residue','flow'),
 'sabotage':('SABOTAGE?','An allegation made without supporting physical evidence','legal'),
 'evidence':('FOLLOW THE EVIDENCE','Design · construction · testing · observed leaks','legal'),
 'legal':('THE CIVIL LAWSUIT','Families and businesses sought accountability','legal'),
 'judgment':('THE 1925 FINDING','Auditor Hugh W. Ogden found company negligence','legal'),
 'inspection':('INSPECT · TEST · VERIFY','Lessons for professional engineering oversight','legal'),
 'headlines':('THE NEXT DAY','Initial casualty reports were incomplete','date'),
 'timeline':('THE CHAIN OF WARNINGS','1915 built  ·  1919 collapsed  ·  1925 finding','timeline'),
 'outro':('FACTS UNCOVERED','Stories & Evidence · Subscribe for more history','outro'),
}
SHORT=[
('People in Boston heard an enormous crash on January fifteenth, nineteen nineteen.','illustration:intro','An ordinary day in Boston'),
('A steel storage tank had ruptured in the North End.','archive:tank','The tank before the flood'),
('Approximately two point three million gallons of molasses poured into the streets.','graphic:volume','2.3 million gallons'),
('The liquid struck buildings and damaged an elevated railway.','archive:rail','Actual 1919 destruction'),
('Twenty-one people died. About one hundred and fifty were injured.','graphic:victims','The human cost'),
('Residents had reported leaks in the tank before it failed.','graphic:leak','Warnings ignored'),
('In nineteen twenty-five, a court-appointed auditor found the tank owner negligent.','graphic:judgment','The investigation'),
('See the full story on Facts Uncovered: Stories and Evidence.','graphic:outro','Watch the documentary')]

def ft(sz,b=False):return ImageFont.truetype(FONT_B if b else FONT_R,sz)
def draw_fit(d,text,xy,maxwidth=1690,size=64,color=WHITE):
    while d.textbbox((0,0),text,font=ft(size,True))[2]>maxwidth and size>31:size-=2
    d.text(xy,text,font=ft(size,True),fill=color,stroke_width=0)

def base(w=W,h=H):
    im=Image.new('RGB',(w,h),BG);d=ImageDraw.Draw(im)
    for y in range(h):
        yy=y/h
        d.line((0,y,w,y),fill=(int(13+22*yy),int(22+24*yy),int(31+22*yy)))
    for x in range(140,w,180):d.line((x,0,x,h),fill=(39,48,54),width=1)
    for y in range(100,h,160):d.line((0,y,w,y),fill=(39,48,54),width=1)
    return im

def graphic(key,caption,wide=True):
    h,w=(H,W) if wide else (1920,1080)
    im=base(w,h);d=ImageDraw.Draw(im)
    headline,detail,kind=GRAPHICS[key]
    left=92 if wide else 67
    d.rectangle((left,115,left+15,218),fill=GOLD)
    d.text((left+38,130),'FACTS UNCOVERED / EVIDENCE FILE',font=ft(28,True) if wide else ft(20,True),fill=GOLD)
    draw_fit(d,headline,(left,264 if wide else 345),maxwidth=w-left*2,size=70 if wide else 58)
    import textwrap
    words=textwrap.wrap(detail,width=48 if wide else 26)
    for i,line in enumerate(words):d.text((left,358+i*52 if wide else 466+i*66),line,font=ft(34) if wide else ft(34),fill=MUTED)
    cy=(730 if wide else 1120);cx=w//2
    # Every graphic is an original, descriptive diagram, not a pseudo-historical photograph.
    if kind in ('tank','pressure','steel'):
        x1=cx-350 if wide else cx-310; x2=cx+350 if wide else cx+310
        y1=cy-170; y2=cy+220
        d.rounded_rectangle((x1,y1,x2,y2),radius=30,fill=(71,81,80),outline=GOLD,width=8)
        for y in range(y1+70,y2,77):d.line((x1+5,y,x2-5,y),fill=(148,152,139),width=4)
        for x in range(x1+80,x2,90):d.line((x,y1+5,x,y2-5),fill=(124,131,123),width=2)
        if kind=='pressure':
            for j in range(4):
                length=35+70*j;y=y1+60+j*90
                d.line((x2-25,y,x2+length,y),fill=AMBER,width=9)
                d.polygon([(x2+length,y-14),(x2+length+29,y),(x2+length,y+14)],fill=AMBER)
        if kind=='steel':
            for j in range(5):
                x=x1+70+j*100;d.ellipse((x,y2-16,x+22,y2+6),fill=GOLD)
    elif kind in ('flow','teams','timeline','location'):
        labels={
          'flow':['SOURCE','STORAGE','INDUSTRY'],
          'teams':['POLICE','NAVY','RED CROSS'],
          'timeline':['1915','1919','1925'],
          'location':['WHARF','TANK','STREETS'],
        }[kind]
        boxw=420 if wide else 270;gap=80 if wide else 20
        total=3*boxw+2*gap
        start=(w-total)//2
        for i,lbl in enumerate(labels):
            x=start+i*(boxw+gap)
            d.rounded_rectangle((x,cy-70,x+boxw,cy+115),radius=23,fill=(54,67,73),outline=GOLD,width=4)
            sz=48 if wide else 32
            bb=d.textbbox((0,0),lbl,font=ft(sz,True))
            d.text((x+(boxw-(bb[2]-bb[0]))//2,cy-1),lbl,font=ft(sz,True),fill=WHITE)
            if i<2:d.polygon([(x+boxw+14,cy+4),(x+boxw+gap-14,cy+4),(x+boxw+gap//2,cy+32)],fill=GOLD)
    elif kind in ('volume','victims','speed','date'):
        number={'volume':'2.3 MILLION','victims':'21','speed':'~35 MPH','date':'1919'}[kind]
        sz=176 if wide else 135
        bb=d.textbbox((0,0),number,font=ft(sz,True))
        d.text(((w-(bb[2]-bb[0]))//2,cy-150),number,font=ft(sz,True),fill=GOLD)
    elif kind=='wave':
        for k in range(6):
            y=cy+220-k*56
            d.arc((cx-580 if wide else 30,y-165,cx+580 if wide else w-30,y+165),180,355,fill=(173-k*11,109-k*6,61-k*3),width=13)
    else:
        d.rounded_rectangle((cx-490 if wide else 90,cy-170,cx+490 if wide else w-90,cy+190),radius=30,outline=GOLD,width=5)
        icon='!' if kind=='hazard' else '§' if kind=='legal' else '✦'
        d.text((cx-75,cy-130),icon,font=ft(230,True),fill=AMBER if kind=='hazard' else GOLD)
    footer='ARTISTIC INFORMATION GRAPHIC  •  NOT HISTORICAL FOOTAGE'
    if wide:d.text((left,h-120),footer,font=ft(23),fill=MUTED)
    else:d.text((left,h-175),'ORIGINAL INFORMATION GRAPHIC',font=ft(21),fill=MUTED)
    d.line((left,h-91,w-left,h-91),fill=GOLD,width=3)
    return im

def graphic_reconstruction(src:Path,wide=True):
    if not src.is_file():raise FileNotFoundError('Approved artistic reconstruction image missing')
    w,h=(W,H) if wide else (1080,1920)
    orig=Image.open(src).convert('RGB')
    im=ImageOps.fit(orig,(w,h),Image.Resampling.LANCZOS,centering=(.50,.42))
    overlay=Image.new('RGBA',(w,h));d=ImageDraw.Draw(overlay)
    d.rectangle((0,h-145,w,h),fill=(8,15,22,222))
    d.text((64,h-122),'ARTISTIC RECONSTRUCTION — NOT A HISTORICAL PHOTOGRAPH',font=ft(27 if wide else 20,True),fill=WHITE)
    d.text((64,60),'BOSTON · JANUARY 15, 1919',font=ft(40 if wide else 25,True),fill=WHITE,stroke_fill=(10,16,24),stroke_width=3)
    return Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')

def photo(key,wide=True):
    path=HERE/'archives'/ASSETS[key]['filename']
    if not path.exists():raise FileNotFoundError(f'Required correct archival image absent: {key}: {ASSETS[key]["source"]}')
    with Image.open(path) as orig:
        orig.verify()
    with Image.open(path) as orig:
        src=orig.convert('RGB')
    w,h=(W,H) if wide else (1080,1920)
    bg=ImageOps.fit(src,(w,h),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(24))
    bg=Image.blend(bg,Image.new('RGB',(w,h),BG),.64)
    fitbox=(w-110,h-360 if wide else h-350)
    src.thumbnail(fitbox,Image.Resampling.LANCZOS)
    bg.paste(src,((w-src.width)//2,(h-src.height)//2))
    d=ImageDraw.Draw(bg)
    d.rectangle((0,h-147,w,h),fill=(10,19,28))
    d.text((60,h-126),'AUTHENTIC ARCHIVAL RECORD · '+('PRE-1919' if key=='tank' else '1919'),font=ft(26 if wide else 22,True),fill=WHITE)
    d.text((60,h-76),key.upper()+'  |  SEE SOURCES AND RIGHTS REGISTER',font=ft(22 if wide else 17),fill=GOLD)
    return bg

def frame(kind,width=1920):
    mode,key=kind.split(':',1);wide=width==1920
    if mode=='graphic':return graphic(key,kind,wide)
    if mode=='archive':return photo(key,wide)
    if mode=='illustration':return graphic_reconstruction(HERE/'reconstruction_boston_waterfront.png',wide)
    raise ValueError('Unhandled visual type: '+kind)

def get_beats(data):
    assert len(data['scenes'])==len(MANUAL_SHOTS)
    beats=[]
    for i,(scene,shots) in enumerate(zip(data['scenes'],MANUAL_SHOTS)):
        sentences=re.split(r'(?<=[.!?])\s+',scene['narration'].strip())
        if len(sentences)!=sum(n for n,_,_ in shots):raise ValueError(f'Manual visual map misses scene {i+1}: {len(sentences)} sentences')
        cursor=0
        for j,(n,visual,label) in enumerate(shots):
            lines=sentences[cursor:cursor+n];cursor+=n
            assert lines
            beats.append({'id':f'{i+1:02d}-{j+1:02d}','chapter':scene['chapter'],'narration':' '.join(lines),'visual':visual,'editorial_intent':label})
    return beats

def ensure_sources(shots):
    for b in shots:
        kind,key=b['visual'].split(':',1)
        if kind=='archive':
            path=HERE/'archives'/ASSETS[key]['filename']
            if not path.is_file():raise RuntimeError(f'MISSING VERIFIED SOURCE {key}: {ASSETS[key]["source"]}')
            with Image.open(path) as im: im.verify()
    return True

def storyboard(beats):
    dest=OUT/'storyboards';dest.mkdir(parents=True,exist_ok=True)
    # Each storyboard frame uses the exact editorially selected source, never a substitute.
    # For unavailable archive pictures, create review-only missing-media slates, never final frames.
    thumb=[]
    for beat in beats:
        try: im=frame(beat['visual'])
        except (FileNotFoundError,KeyError) as e:
            im=graphic('evidence','',True)
            d=ImageDraw.Draw(im)
            d.rectangle((65,495,1850,665),fill=(120,35,28))
            d.text((80,520),'REVIEW ONLY — SOURCE FILE NOT ACQUIRED',font=ft(42,True),fill=WHITE)
        im.thumbnail((960,540),Image.Resampling.LANCZOS)
        draw=ImageDraw.Draw(im)
        draw.rectangle((0,0,960,54),fill=(8,14,22))
        draw.text((18,10),beat['id']+'  ·  '+beat['editorial_intent'],font=ft(20,True),fill=WHITE)
        im.save(dest/(beat['id']+'.jpg'),quality=86)
        thumb.append(im.copy())
    sheet=OUT/'EP01_88_shots_review.jpg'
    from PIL import ImageOps
    tiled=Image.new('RGB',(960*4,540*math.ceil(len(thumb)/4)),BG)
    for i,im in enumerate(thumb):tiled.paste(im,((i%4)*960,(i//4)*540))
    tiled.save(sheet,quality=88)
    return sheet

def synth(beats,model,voices,outdir):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    voice=Kokoro(str(model),str(voices))
    outdir.mkdir(parents=True,exist_ok=True)
    durations=[]
    for index,b in enumerate(beats):
        dest=outdir/f'{index:03d}.wav'
        if not dest.is_file():
            wav,sr=voice.create(b['narration'],voice='am_michael',speed=.94,lang='en-us')
            arr=np.asarray(wav,dtype=np.float32).reshape(-1)
            if sr<22050 or len(arr)<sr*.5 or not np.isfinite(arr).all():raise RuntimeError('TTS failed for '+b['id'])
            rest=np.zeros(int(sr*(.33 if index+1<len(beats) else .75)),dtype=np.float32)
            sf.write(dest,np.r_[arr,rest],sr,subtype='PCM_16')
        durations.append(probe(dest))
    return durations

def probe(src):
    x=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(src)],text=True).strip()
    return float(x)

def call(x):subprocess.run([str(i) for i in x],check=True)
def to_stamp(secs):
    t=int(round(secs*1000));hours,t=divmod(t,3600000);mins,t=divmod(t,60000);s,ms=divmod(t,1000)
    return f'{hours:02}:{mins:02}:{s:02},{ms:03}'

def captions(beats,ds,path):
    lines=[];start=0.;idx=1
    for b,d in zip(beats,ds):
        chunks=[];words=b['narration'].split()
        while words:
            chunks.append(words[:9]);words=words[9:]
        for i,chunk in enumerate(chunks):
            a=start+d*i/len(chunks);z=start+d*(i+1)/len(chunks)
            lines.append(f'{idx}\n{to_stamp(a)} --> {to_stamp(z)}\n{" ".join(chunk)}\n');idx+=1
        start+=d
    path.write_text('\n'.join(lines)+'\n',encoding='utf8')

def render(beats,ds,portrait,outfile,wavdir):
    is_short=portrait
    w,h=(1080,1920) if is_short else (1920,1080)
    dirclips=OUT/('short_clips' if portrait else 'master_clips')
    dirclips.mkdir(parents=True,exist_ok=True)
    seq=[]
    for ix,(b,seconds) in enumerate(zip(beats,ds)):
        dest=dirclips/f'{ix:03d}.mp4'
        if not dest.is_file():
            still=OUT/'plates'/('short' if portrait else 'master')/f'{ix:03d}.png'
            still.parent.mkdir(parents=True,exist_ok=True)
            frame(b['visual'],width=w).save(still,compress_level=5)
            wav=wavdir/f'{ix:03d}.wav'
            call(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','24','-i',still,'-i',wav,'-t',f'{seconds:.3f}','-r','24','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',dest])
        seq.append(dest)
        print('SYNCHRONIZED',b.get('id',f'SHORT-{ix+1}'),b['visual'],round(seconds,2),'sec',flush=True)
    concat=OUT/('short_concat.txt' if portrait else 'master_concat.txt')
    concat.write_text(''.join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in seq))
    call(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',outfile])
    streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(outfile)],text=True))
    assert any(s['codec_type']=='audio' for s in streams['streams'])
    assert any(s.get('width')==w and s.get('height')==h for s in streams['streams'])
    assert abs(float(streams['format']['duration'])-sum(ds))<max(1,1.5*len(ds)/24)
    return outfile

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['storyboard','render']);p.add_argument('--episode',type=Path,required=True);p.add_argument('--model',type=Path);p.add_argument('--voices',type=Path)
    args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads(args.episode.read_text(encoding='utf8'))
    beats=get_beats(data)
    (OUT/'EXPLICIT_SHOT_MANIFEST.json').write_text(json.dumps(beats,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    (OUT/'ASSET_RIGHTS_REGISTER.json').write_text(json.dumps(ASSETS,indent=2)+'\n',encoding='utf8')
    (OUT/'DOCUMENTARY_NARRATION.txt').write_text('\n\n'.join(b['narration'] for b in beats)+'\n',encoding='utf8')
    if args.mode=='storyboard':
        x=storyboard(beats)
        print('REVIEW_BOARD',x,'EDITED_SHOTS',len(beats));return
    assert args.model and args.voices,'Rendering requires the approved narrator model and voices'
    ensure_sources(beats)
    main_audio=OUT/'voice_master';short_audio=OUT/'voice_short'
    ds=synth(beats,args.model,args.voices,main_audio)
    if not 650<sum(ds)<1600:raise RuntimeError('Narration duration requires review')
    captions(beats,ds,OUT/'documentary.srt')
    render(beats,ds,False,OUT/'Great_Molasses_Flood_MANUALLY_EDITED.mp4',main_audio)
    shorts=[{'id':f'S{i+1:02d}','narration':t,'visual':visual,'editorial_intent':intent} for i,(t,visual,intent) in enumerate(SHORT)]
    sd=synth(shorts,args.model,args.voices,short_audio)
    if not 35<sum(sd)<70:raise RuntimeError('Short voice too fast or slow: rewrite the script; do not time-stretch arbitrarily')
    captions(shorts,sd,OUT/'short.srt')
    render(shorts,sd,True,OUT/'Great_Molasses_Flood_SHORT.mp4',short_audio)
    (OUT/'QA_HANDOFF.json').write_text(json.dumps({'main_shots':len(beats),'main_seconds':sum(ds),'short_shots':len(shorts),'short_seconds':sum(sd),'editorial_review':'PENDING: listen to and view 100% before publication','upload_permitted':False},indent=2))
    print('TECHNICAL_RENDER_COMPLETE__NOT_RELEASE_APPROVED')
if __name__=='__main__':main()