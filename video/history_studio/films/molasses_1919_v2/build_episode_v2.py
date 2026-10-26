#!/usr/bin/env python3
"""History Uncovered EP01 v2: preserve v1 research/script, upgrade voice, image direction and editing.
Original v1 episode remains untouched. This is an illustrative documentary, not archival film.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, re, subprocess, wave
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'molasses_1919'
spec = importlib.util.spec_from_file_location('molasses_v1', BASE / 'build_episode.py')
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
DATA = v1.DATA
OUT = HERE / 'output'; OUT.mkdir(parents=True, exist_ok=True)
v1.OUT = OUT
W,H = 1920,1080
GOLD=(236,186,112); CREAM=(247,235,210); DARK=(12,21,29)
FONT='/usr/share/fonts/truetype/lato/Lato-Heavy.ttf'
FONTREG='/usr/share/fonts/truetype/lato/Lato-Regular.ttf'
TIMELINE=[]

def font(n,bold=False): return ImageFont.truetype(FONT if bold else FONTREG,n)

def vignette(im,weight=.42):
    w,h=im.size
    yy,xx=np.ogrid[-1:1:complex(0,h),-1:1:complex(0,w)]
    dist=(xx/1.2)**2+(yy/1.15)**2
    mask=np.uint8(np.clip((dist-.11)*weight*240,0,150))
    black=Image.new('RGB',im.size,(7,11,19))
    return Image.composite(black,im,Image.fromarray(mask,'L'))

def lower_title(im,scene,i,archive=False):
    layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer,'RGBA')
    d.rectangle((0,0,W,116),fill=(9,17,24,192))
    d.rectangle((84,112,600,116),fill=GOLD+(255,))
    d.rounded_rectangle((56,H-225,W-56,H-55),radius=18,fill=(8,15,21,200))
    d.text((84,45),'H I S T O R Y   U N C O V E R E D',font=font(28,True),fill=GOLD)
    d.text((W-400,48),'BOSTON  /  1919',font=font(25),fill=CREAM)
    headline=scene['headline'].replace(' • ','  /  ')
    s=62
    while d.textbbox((0,0),headline,font=font(s,True))[2]>W-190 and s>32:s-=2
    d.text((86,H-207),headline,font=font(s,True),fill=CREAM,stroke_width=1,stroke_fill=(10,10,10))
    d.text((89,H-119),scene['chapter'],font=font(24,True),fill=GOLD)
    label='ARCHIVAL PHOTOGRAPH' if archive else 'ARTISTIC RECONSTRUCTION'
    d.text((W-470,H-110),label,font=font(23),fill=(200,209,208))
    d.text((W-158,76),f'{i+1:02d} / 22',font=font(19),fill=CREAM)
    return Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')

def make_plate(i,scene,archives):
    kind=scene['kind'];archive=kind=='archive'
    if archive:
        asset=archives.get(scene.get('asset'))
        if not asset: raise RuntimeError('Historical photo missing; never substitute a fake archive for '+str(scene.get('asset')))
        with Image.open(asset) as source: photo=source.convert('RGB')
        bg=ImageOps.fit(photo,(W,H),method=Image.Resampling.LANCZOS)
        bg=ImageEnhance.Color(bg).enhance(.20).filter(ImageFilter.GaussianBlur(25))
        bg=ImageEnhance.Brightness(bg).enhance(.36)
        art=bg.copy()
        sized=photo.copy();sized.thumbnail((W-220,H-310),Image.Resampling.LANCZOS)
        x=(W-sized.width)//2;y=(H-sized.height)//2-2
        shadow=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shadow)
        sd.rounded_rectangle((x-12,y-12,x+sized.width+12,y+sized.height+12),radius=6,fill=(20,23,23,255),outline=GOLD,width=4)
        art.paste(shadow,(0,0),shadow);art.paste(sized,(x,y))
        art=ImageEnhance.Contrast(art).enhance(1.08)
    else:
        # Preserve the established visual assets while directing each shot individually.
        base=v1.art_base(i,kind).resize((W,H),Image.Resampling.LANCZOS)
        base=ImageEnhance.Color(base).enhance(.78)
        base=ImageEnhance.Contrast(base).enhance(1.27)
        highlights=Image.new('RGBA',(W,H));p=ImageDraw.Draw(highlights,'RGBA')
        # Distinct cinematic shafts of atmospheric light and human-scale foreground.
        cx=[320,1250,600,1460,380,1100][i%6]
        p.polygon([(cx-90,-30),(cx+75,-30),(cx+730,H),(cx-230,H)],fill=(250,182,99,18+(i%4)*3))
        if kind.startswith('art_'):
            for k in range(3):
                px=[240,1080,1550][k]+(i%3)*30;py=H-172+(k%2)*22
                p.ellipse((px-16,py-112,px+16,py-77),fill=(8,15,19,165))
                p.polygon([(px-14,py-81),(px+21,py-79),(px+30,py),(px-30,py)],fill=(8,15,19,165))
                p.line((px-10,py,px-27,py+58),fill=(8,15,19,165),width=13)
                p.line((px+10,py,px+27,py+58),fill=(8,15,19,165),width=13)
        if kind in ('art_wave','art_rescue','art_cleanup'):
            for j in range(40):
                x=(j*331+i*107)%W;y=620+(j*37)%320
                p.ellipse((x,y,x+6,y+3),fill=(232,174,111,110))
        art=Image.alpha_composite(base.convert('RGBA'),highlights).convert('RGB')
        art=art.filter(ImageFilter.GaussianBlur(.45))
    art=vignette(art)
    return lower_title(art,scene,i,archive)

def plates(archives):
    folder=OUT/'plates';folder.mkdir(exist_ok=True)
    for i,scene in enumerate(DATA['scenes']):
        im=make_plate(i,scene,archives)
        im.save(folder/f'scene_{i+1:02d}.jpg',quality=93,optimize=True,subsampling=0)
        # Close-ups are separately reframed shots, not a static slide held for 30 seconds.
        focus=[.36,.62,.50,.70][i%4]
        scale=0.79 if scene['kind']!='archive' else 0.87
        nw,nh=int(W*scale),int(H*scale)
        x=int((W-nw)*focus/0.80);y=int((H-nh)*.44)
        x=max(0,min(x,W-nw))
        im.crop((x,y,x+nw,y+nh)).resize((W,H),Image.Resampling.LANCZOS).save(folder/f'scene_{i+1:02d}_detail.jpg',quality=91,subsampling=0)
    return folder

def voice_tracks(model,voices):
    from kokoro_onnx import Kokoro
    tts=Kokoro(str(model),str(voices))
    folder=OUT/'narration';folder.mkdir(exist_ok=True)
    lengths=[]
    for i,scene in enumerate(DATA['scenes']):
        path=folder/f'voice_{i+1:02d}.wav'
        # Whole-scene synthesis retains prosody across sentences (80-110 words on average).
        if not path.exists():
            wav,sr=tts.create(scene['narration'],voice='am_michael',speed=.94,lang='en-us')
            wav=np.asarray(wav,dtype=np.float32).reshape(-1)
            if wav.size<sr*8 or not np.isfinite(wav).all():raise RuntimeError(f'Invalid neural speech scene {i+1}')
            is_chapter_end=(i+1==len(DATA['scenes']) or scene['chapter']!=DATA['scenes'][i+1]['chapter'])
            end_pause=.80 if is_chapter_end else .34
            wav=np.concatenate((wav,np.zeros(round(sr*end_pause),dtype=np.float32)))
            sf.write(path,wav,sr,subtype='PCM_16')
        duration=v1.probe(path)
        if not 8<duration<130:raise RuntimeError(f'Bad narration length {i+1}: {duration}')
        lengths.append(duration)
        print('KOKORO_V2_NARRATION',i+1,'seconds',round(duration,2),flush=True)
    return folder,lengths

def subtitle(s,start,end,number):
    return f'{number}\n{v1.to_srt_time(start)} --> {v1.to_srt_time(end)}\n{s}\n\n'

def write_captions(lengths):
    blocks=[];cursor=0.;counter=1
    for i,(scene,length) in enumerate(zip(DATA['scenes'],lengths)):
        is_end=(i+1==len(DATA['scenes']) or scene['chapter']!=DATA['scenes'][i+1]['chapter'])
        effective=max(1,length-(.8 if is_end else .34))
        words=scene['narration'].split()
        # Short, readable 4-9-word caption groups; actual scene WAV durations anchor the scene.
        groups=[];k=0
        while k<len(words):
            n=min(9,len(words)-k)
            groups.append(' '.join(words[k:k+n]));k+=n
        weights=[max(1,len(g.split())) for g in groups];total=sum(weights)
        loc=cursor
        for g,weight in zip(groups,weights):
            d=effective*weight/total
            blocks.append(subtitle(g,loc,loc+d,counter));loc+=d;counter+=1
        cursor+=length
    (OUT/'subtitles.srt').write_text(''.join(blocks),encoding='utf-8')
    return cursor

def score():
    # Original 64-second evolving, low-key score; no third-party recordings.
    rate=22050;seconds=64;n=rate*seconds;t=np.arange(n,dtype=np.float32)/rate
    chords=((65.41,98.0,130.81),(55,82.41,110),(73.42,110,146.83),(49,73.42,98))
    sound=np.zeros(n,dtype=np.float32)
    for ix,triad in enumerate(chords):
        mask=(t>=16*ix)&(t<16*(ix+1));st=t[mask]-16*ix
        fade=np.minimum(1,st/2)*np.minimum(1,(16-st)/2)
        pad=sum(np.sin(2*math.pi*f*st)+.20*np.sin(2*math.pi*f*2*st) for f in triad)
        sound[mask]+=.013*pad/3*fade
    for k in range(32):
        beginning=k*2*rate;stop=min(n,beginning+int(1.8*rate))
        tt=np.arange(stop-beginning,dtype=np.float32)/rate
        f=(146.83,130.81,164.81,110,98,130.81,146.83,110)[k%8]
        sound[beginning:stop]+=.012*np.sin(2*math.pi*f*tt)*np.exp(-2.8*tt)
    sf.write(OUT/'score_v2.wav',sound,rate,subtype='PCM_16')

def render(audio,plate_dir,lengths,quick=False):
    clips=OUT/'clips';clips.mkdir(exist_ok=True)
    files=[]
    count=min(2,len(lengths)) if quick else len(lengths)
    for i in range(count):
        d=lengths[i]
        cuts=[d*.52,d*.48]
        off=0.
        for shot,part in enumerate(cuts):
            img=plate_dir/f'scene_{i+1:02d}{"_detail" if shot else ""}.jpg'
            dest=clips/f'{i+1:02d}_{shot}.mp4'
            zoom="zoompan=z='min(zoom+0.000075,1.055)':d=1:x='(iw-iw/zoom)*"+('.18' if shot else '.73')+"':y='(ih-ih/zoom)*0.5':s=1920x1080:fps=24,format=yuv420p[v]"
            if not dest.exists():
                v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','24','-i',img,'-ss',f'{off:.4f}','-t',f'{part:.4f}','-i',audio/f'voice_{i+1:02d}.wav','-filter_complex',zoom,'-map','[v]','-map','1:a:0','-t',f'{part:.4f}','-r','24','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart',dest])
            files.append("file '"+str(dest.resolve()).replace("'","'\\''")+"'")
            off+=part
        print('V2_SHOTS_RENDERED',i+1,'of',count,flush=True)
    (OUT/'concat_v2.txt').write_text('\n'.join(files)+'\n')
    v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',OUT/'concat_v2.txt','-c','copy',OUT/'assembled_v2.mp4'])
    score()
    # Mix score below narration, gently compress peaks, true peak ceiling for upload.
    path=OUT/('Great_Molasses_Flood_1919_v2_PREVIEW.mp4' if quick else 'Great_Molasses_Flood_1919_v2.mp4')
    v1.call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',OUT/'assembled_v2.mp4','-stream_loop','-1','-i',OUT/'score_v2.wav','-filter_complex','[0:a]volume=1.3,acompressor=threshold=0.13:ratio=2:attack=20:release=220[n];[1:a]volume=0.40[m];[n][m]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.94[a]','-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',path])
    return path

def thumbnail(plate_dir):
    # YouTube thumbnail safe margins, bold readable words, no misleading archive labeling.
    im=Image.open(plate_dir/'scene_01.jpg').convert('RGB').resize((1280,720),Image.Resampling.LANCZOS)
    mask=Image.new('RGBA',(1280,720));d=ImageDraw.Draw(mask,'RGBA')
    for x in range(0,850,4):
        alpha=int(240*(1-x/850))
        d.rectangle((x,0,x+4,720),fill=(6,13,20,alpha))
    d.rectangle((45,112,54,613),fill=GOLD+(255,))
    overlay=Image.alpha_composite(im.convert('RGBA'),mask)
    d=ImageDraw.Draw(overlay)
    d.text((80,131),'BOSTON',font=font(103,True),fill=CREAM,stroke_width=2,stroke_fill=(7,7,8))
    d.text((78,258),'DROWNED IN',font=font(75,True),fill=CREAM,stroke_width=2,stroke_fill=(7,7,8))
    d.text((77,365),'MOLASSES',font=font(98,True),fill=GOLD,stroke_width=2,stroke_fill=(7,7,8))
    d.text((83,538),'THE DISASTER OF 1919',font=font(36,True),fill=CREAM)
    overlay.convert('RGB').save(OUT/'thumbnail_v2.jpg',quality=93,optimize=True)

def provenance(archives,lengths):
    v1.write_provenance(archives)
    filename=OUT/'PROVENANCE.json';p=json.loads(filename.read_text())
    p.update({'version':2,'script':'Unchanged 22 scenes from molasses_1919/episode.json','voice':'Kokoro-82M v1.0 / am_michael, Apache-2.0 weights; kokoro-onnx MIT; not a human recording or voice clone','voice_model_source':'https://huggingface.co/hexgrad/Kokoro-82M','voice_runtime_source':'https://github.com/thewh1teagle/kokoro-onnx','voice_seconds':[round(x,3) for x in lengths],'art':'Original programmatic 2D illustration with cinematic color direction; historic photographs are unaltered content inside archival frames','captions':'Word-group approximate timing anchored to real per-scene WAV durations; manual editorial timing review required','editorial_status':'TECHNICAL VIDEO ONLY: manual voice/listen and picture inspection required before publishing'})
    filename.write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
    (OUT/'V2_CHANGELOG.txt').write_text('EPISODE 01 v2 / same researched script\nNeural documentary narrator Kokoro am_michael; paced 0.94 with chapter breathing room.\n22 repolished plates + 22 cinematic close-ups; two moving camera angles per scene.\n1920x1080, 24fps; remixed original soundtrack; short caption groups; new thumbnail.\nV1 unchanged. Archival photos remain authentic; recreated images are visibly identified.\nEditorial listening and visual inspection still required before YouTube publication.\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True,type=Path);parser.add_argument('--voices',required=True,type=Path);parser.add_argument('--quick',action='store_true');args=parser.parse_args()
    archives=v1.archival_assets(download=True)
    if len(archives)!=len(DATA['archival_images']): raise RuntimeError('Required public-domain archival photographs missing')
    folder=plates(archives)
    narration,lengths=voice_tracks(args.model,args.voices)
    total=write_captions(lengths)
    thumbnail(folder);provenance(archives,lengths)
    mp4=render(narration,folder,lengths,args.quick)
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)],text=True))
    streams={s['codec_type'] for s in meta['streams']}
    assert streams>={'video','audio'}
    assert any(s.get('width')==1920 and s.get('height')==1080 for s in meta['streams'])
    if not args.quick:assert 480<float(meta['format']['duration'])<1200
    print('V2_REAL_VIDEO_READY',mp4,'size_MB',round(mp4.stat().st_size/1048576,1),'duration_min',round(float(meta['format']['duration'])/60,2),'full_script_minutes',round(total/60,2),flush=True)

if __name__=='__main__':main()
