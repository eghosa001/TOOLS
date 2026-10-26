#!/usr/bin/env python3
"""Deterministic CPU cut-out cartoon renderer, GPU H.264 encoding when usable.

Draws independent 2D puppet joints at 12 or 24 animation poses/s; duplicates
frames to delivery 24fps. Streams raw frames to ffmpeg; keeps no full frame
sequences on disk. Per-scene audio is always externally supplied or genuinely
synthesized, never silent fake dialogue.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from rig2d import draw_actor
from sprite_rig import draw_layered

SIZES={'preview':(640,360),'standard':(1280,720),'premium':(1920,1080)}

def _font(n, bold=False):
    candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf']
    for f in candidates:
        if Path(f).is_file(): return ImageFont.truetype(f,n)
    return ImageFont.load_default()

def _duration(file):
    probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(file)],capture_output=True,text=True,check=True)
    secs=float(probe.stdout.strip())
    if not (secs>0 and secs<3600): raise ValueError('Invalid audio duration')
    return secs

def _energy(file, positions):
    """RMS mouth animation from genuine 16-bit WAV samples (Python 3.13 safe)."""
    from array import array
    with wave.open(str(file),'rb') as w:
        if w.getcomptype()!='NONE' or w.getsampwidth()!=2:return [0.0]*len(positions)
        channels=w.getnchannels();rate=w.getframerate()
        raw=w.readframes(w.getnframes())
    data=array('h');data.frombytes(raw)
    if sys.byteorder!='little':data.byteswap()
    levels=[]
    for t in positions:
        start=max(0,int((t-.05)*rate))*channels
        end=min(len(data),int((t+.05)*rate)*channels)
        # Sample every 4th PCM frame for speed. Speech/lip animation isn't
        # claiming phoneme-level alignment.
        subset=data[start:end:max(1,channels*4)]
        if not subset: levels.append(0.0);continue
        rms=math.sqrt(sum(v*v for v in subset)/len(subset))
        levels.append(min(1.0,rms/32768*11))
    return levels

def _rhubarb_levels(file, positions):
    """Use validated genuine Rhubarb mouthCues from recorded WAV file."""
    data=json.loads(Path(file).read_text(encoding='utf8'))
    cues=data.get('mouthCues')
    if not isinstance(cues,list) or not cues:raise ValueError('No valid mouthCues')
    openness={'A':.08,'B':.28,'C':.58,'D':.90,'E':.65,'F':.38,'G':.55,'H':.24,'X':.05}
    last=0.
    for cue in cues:
        if cue.get('value') not in openness or not (0<=float(cue['start'])<float(cue['end'])) or float(cue['start'])<last:
            raise ValueError('Invalid or overlapping Rhubarb mouth cue')
        last=float(cue['end'])
    return [next((openness[c['value']] for c in cues if float(c['start'])<=t<float(c['end'])),.04) for t in positions]

def _plate(width,height,stage,seed=1):
    """Original editable 2D stage draft; replace with licensed illustrated art."""
    import random
    rng=random.Random(str(stage)+str(seed))
    top={'waterfront':(33,53,75),'medieval':(64,63,79),'palace':(46,49,65),'archive':(70,60,50),'village':(51,68,72)}.get(stage,(35,55,74))
    im=Image.new('RGB',(width,height)); pix=im.load()
    for y in range(height):
        r=y/max(1,height-1)
        color=tuple(int(max(0,min(255,c*(1-r*.46)+r*46))) for c in top)
        # scanline fill
        ImageDraw.Draw(im).line((0,y,width,y),fill=color)
    d=ImageDraw.Draw(im)
    floor=int(height*.75)
    d.rectangle((0,floor,width,height),fill=(55,59,54))
    if stage=='archive':
        for i in range(9):
            x=int(i*width/8)
            d.rectangle((x,floor*.16,x+width//20,floor),fill=(53,45,43))
            d.line((x+width//40,floor*.16,x+width//40,floor),fill=(142,115,81),width=max(2,width//200))
    else:
        for n in range(12):
            x=int(n*width/11.0)-width//15
            h=int(height*(.16+.26*rng.random()))
            w=int(width*(.06+.055*rng.random()))
            c=(27,37,43) if stage=='waterfront' else (36,43,49)
            d.rectangle((x,floor-h,x+w,floor),fill=c)
            if stage!='waterfront':
                d.polygon([(x-8,floor-h),(x+w/2,floor-h-height*.06),(x+w+8,floor-h)],fill=(62,43,43))
            for wx in range(x+8,x+w-5,max(14,w//4)):
                for wy in range(floor-h+14,floor-10,max(20,height//24)):
                    d.rectangle((wx,wy,wx+max(2,width//150),wy+max(3,height//70)),fill=(177,130,80))
    # Atmospheric drawing layers: not a 3D model and not period-specific evidence.
    d.ellipse((width*.64,-height*.32,width*1.2,height*.59),fill=(108,94,82)) if stage=='archive' else None
    return im

def _encoder(gpu):
    if gpu=='off':return 'libx264'
    has_nvidia=shutil.which('nvidia-smi') and subprocess.run(['nvidia-smi','-L'],capture_output=True).returncode==0
    if not has_nvidia:
        if gpu=='on':raise RuntimeError('GPU required, but NVIDIA runtime not detected')
        return 'libx264'
    p=subprocess.run(['ffmpeg','-loglevel','error','-f','lavfi','-i','color=c=black:s=64x64:r=1:d=1','-frames:v','1','-c:v','h264_nvenc','-f','null','-'],capture_output=True)
    if p.returncode==0:return 'h264_nvenc'
    if gpu=='on':raise RuntimeError('GPU present but FFmpeg NVENC encoding unavailable')
    return 'libx264'

def _draw_frame(bg, scene, chars, t, dur, energy, size):
    w,h=size
    im=bg.copy()
    d=ImageDraw.Draw(im,'RGBA')
    # Camera move over pre-built illustrated environment, subtle 2D parallax layer.
    movement=math.sin((t/dur)*math.pi*2) if dur else 0
    d.polygon([(0,h*.74),(w,h*.72),(w,h)],fill=(38,46,47,130))
    for actor in scene.get('actors',[]):
        ch=chars[actor['id']]
        xpos=w*float(actor.get('x',.5))+movement*w*.012
        action=actor.get('action','idle')
        if action=='walk': xpos+=w*.045*min(1,t/max(2,dur))
        if ch.get('rig'):
            draw_layered(im,ch['rig'],xpos,h*.85,h*float(actor.get('scale',.62)),t,action,
                         speaking=scene.get('speaker')==actor['id'],amplitude=energy)
        else:
            draw_actor(im,ch,xpos,h*.85,h*float(actor.get('scale',.62)),t,action,
                       speaking=scene.get('speaker')==actor['id'],amplitude=energy)
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle((0,0,w,int(h*.13)),fill=(10,12,20,177))
    margin=int(w*.034)
    d.text((margin,int(h*.02)),scene.get('chapter','HISTORICAL RECONSTRUCTION').upper(),font=_font(max(14,int(h*.036)),True),fill=(245,235,201))
    # Label is mandatory for illustrative scenes (not archival footage).
    label=scene.get('visual_label','ILLUSTRATED RECONSTRUCTION')
    d.rectangle((margin,h-int(h*.085),min(w-8,margin+int(w*.43)),h-int(h*.025)),fill=(10,12,18,175))
    d.text((margin+10,h-int(h*.073)),label,font=_font(max(11,int(h*.025))),fill=(242,231,206))
    # soft shot fade at start/end
    fade=min(1,t/.28,(dur-t)/.28) if dur>.55 else 1
    if fade<1:
        layer=Image.new('RGBA',(w,h),(4,6,11,round(255*(1-max(0,fade)))))
        im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
    return im

def _make_scene(scene, chars, audio_path, out, size, animation_fps, video_fps, codec):
    dur=_duration(audio_path)
    if dur>180: raise ValueError('Scene exceeds 3m; split scenes for unique visual direction')
    w,h=size
    count=math.ceil(dur*animation_fps)
    positions=[i/animation_fps for i in range(count)]
    energies=(_rhubarb_levels(scene['rhubarb'],positions) if scene.get('rhubarb')
              else (_energy(audio_path,positions) if audio_path.suffix.lower()=='.wav' else [0.0]*count))
    bg_path=scene.get('background')
    if bg_path:
        source=Path(bg_path)
        if not source.is_file():raise FileNotFoundError('Backdrop missing: '+str(source))
        bg=Image.open(source).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
    else: bg=_plate(w,h,scene.get('stage','village'))
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(animation_fps),'-i','pipe:0','-i',str(audio_path),'-vf',f'fps={video_fps}', '-c:v',codec,'-threads','2']
    if codec=='libx264':cmd+=['-preset','veryfast','-crf','20']
    else:cmd+=['-preset','p4','-cq','21','-b:v','0']
    cmd+=['-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','apad','-t',str(count/animation_fps),'-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i,t in enumerate(positions):
            proc.stdin.write(_draw_frame(bg,scene,chars,t,dur,energies[i],size).tobytes())
        proc.stdin.close()
        errors=proc.stderr.read().decode(errors='replace')
        if proc.wait()!=0:raise RuntimeError('ffmpeg scene render failed: '+errors[-1600:])
    except Exception:
        proc.kill();proc.wait()
        raise
    if not out.is_file() or out.stat().st_size<1000:raise RuntimeError('Scene MP4 is absent or empty')
    return dur

def validate(doc, basedir):
    if doc.get('kind')!='historical_2d_animation':raise ValueError('Expected historical_2d_animation schema')
    cast=doc.get('characters')
    if not isinstance(cast,dict) or not cast:raise ValueError('Character roster missing')
    for key,palette in cast.items():
        if not key.isidentifier():raise ValueError('Invalid character key')
        if palette.get('rig'):
            rig=Path(palette['rig'])
            if rig.is_absolute() or not (basedir/rig).resolve().is_relative_to(basedir.resolve()):raise ValueError('Rig must be inside episode directory')
            if not (basedir/rig).is_file():raise FileNotFoundError('Missing rig metadata: '+str(rig))
        else:
            for col in ('skin','tunic','hair','sash'):_ = _hex_check(palette.get(col,''))
    scenes=doc.get('scenes',[])
    if not isinstance(scenes,list) or not scenes:raise ValueError('At least one scene required')
    for n,scene in enumerate(scenes,1):
        path=scene.get('audio')
        if not isinstance(path,str) or not path:raise ValueError(f'Scene {n} has no real recorded/synthesized audio')
        if not (basedir/path).resolve().is_relative_to(basedir.resolve()):raise ValueError('Audio path escapes project')
        if not (basedir/path).is_file():raise FileNotFoundError('Missing speech audio: '+str(basedir/path))
        if not scene.get('chapter') or len(scene.get('chapter',''))<4:raise ValueError(f'Chapter label missing {n}')
        if not scene.get('visual_label'):raise ValueError('Must distinguish illustrations from archival footage')
        if scene.get('speaker') not in (None,'narrator') and scene['speaker'] not in cast:raise ValueError('Unknown speaker')
        for a in scene.get('actors',[]):
            if a['id'] not in cast:raise ValueError('Unknown animated actor '+str(a['id']))
            if a.get('action','idle') not in ('idle','walk','point'):raise ValueError('Unsupported action')
        if 'rhubarb' in scene:
            r=Path(scene['rhubarb'])
            if r.is_absolute() or not (basedir/r).resolve().is_relative_to(basedir.resolve()) or not (basedir/r).is_file():
                raise ValueError('Rhubarb cue JSON must exist within episode directory')
        if 'background' in scene:
            b=Path(scene['background'])
            if b.is_absolute() or not (basedir/b).resolve().is_relative_to(basedir.resolve()):raise ValueError('Background must be local approved file')
    return True

def _hex_check(x):
    from rig2d import _rgb
    return _rgb(x)

def _file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def _one_task(job):
    index,scene,cast,audio,out,size,afps,ofps,codec,cache,version=job
    keydata={'scene':scene,'cast':cast,'voice_sha':_file_sha(audio),'size':size,
             'afps':afps,'ofps':ofps,'encoder':codec,'engine_version':version}
    for item in cast.values():
        if item.get('rig'):
            p=Path(item['rig'])
            keydata['rig_sha_'+p.stem]=_file_sha(p)
            keydata['rig_parts_'+p.stem]=[_file_sha(part) for part in sorted(p.parent.glob('*.png'))]
    if scene.get('background'):keydata['background_sha']=_file_sha(scene['background'])
    if scene.get('rhubarb'):keydata['rhubarb_sha']=_file_sha(scene['rhubarb'])
    key=hashlib.sha256(json.dumps(keydata,sort_keys=True).encode()).hexdigest()
    cached=Path(cache)/f'{key}.mp4' if cache else None
    dur=_duration(audio)
    if cached and cached.is_file() and cached.stat().st_size>1000:
        shutil.copyfile(cached,out)
        return index,dur,'CACHE_HIT'
    actual=_make_scene(scene,cast,audio,out,size,afps,ofps,codec)
    if cached:
        cached.parent.mkdir(parents=True,exist_ok=True)
        # Constructed video is verified technically; still needs human QC.
        temp=Path(str(cached)+f'.{os.getpid()}.part')
        shutil.copyfile(out,temp)
        temp.replace(cached)
    return index,actual,'RENDERED'


def run(args):
    docpath=args.episode.resolve()
    doc=json.loads(docpath.read_text(encoding='utf8'))
    base=docpath.parent
    validate(doc,base)
    if args.max_scenes is not None:
        if args.max_scenes<1:raise ValueError('--max-scenes must be >= 1')
        doc['scenes']=doc['scenes'][:args.max_scenes]
    if args.target_minutes is not None and args.max_scenes is None:
        narration_seconds=sum(_duration(base/sc['audio']) for sc in doc['scenes'])
        if not args.target_minutes-.8<=narration_seconds/60<=args.target_minutes+1.0:
            raise ValueError(f'Preflight: {narration_seconds/60:.1f} narrated minutes; target {args.target_minutes}. Add real voiced content before costly rendering.')
    size=SIZES[args.quality]
    codec=_encoder(args.gpu)
    for cast in doc['characters'].values():
        if cast.get('rig'):cast['rig']=str((base/cast['rig']).resolve())
    out=args.output.resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    version=':'.join(_file_sha(Path(__file__).parent/name) for name in ('render2d.py','rig2d.py','sprite_rig.py'))
    workers=min(max(1,args.workers),min(8,len(doc['scenes'])))
    with tempfile.TemporaryDirectory(prefix='historical2d_') as folder:
        folder=Path(folder)
        jobs=[];paths=[]
        for i,sc in enumerate(doc['scenes']):
            scene=dict(sc)
            if scene.get('background'):scene['background']=str((base/scene['background']).resolve())
            if scene.get('rhubarb'):scene['rhubarb']=str((base/scene['rhubarb']).resolve())
            dst=folder/f'scene_{i:04}.mp4';paths.append(dst)
            jobs.append((i,scene,doc['characters'],base/sc['audio'],dst,size,args.animation_fps,args.output_fps,codec,args.cache_dir,version))
        if workers==1:results=[_one_task(j) for j in jobs]
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
                results=list(pool.map(_one_task,jobs))
        seconds=sum(d for _,d,_ in results)
        for i,d,status in sorted(results):print(f'{status}: SCENE {i+1}/{len(paths)} {d:.2f}s {paths[i].stat().st_size} bytes',flush=True)
        concat=folder/'concat.txt'
        concat.write_text(''.join(f"file '{p.as_posix()}'\n" for p in paths),encoding='utf8')
        p=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)],capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr[-2000:])
    actual=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(out)],capture_output=True,text=True,check=True)
    runtime=float(actual.stdout)
    if abs(runtime-seconds)>max(1.5,.01*seconds):raise RuntimeError(f'Duration desync: expected {seconds}, got {runtime}')
    print(json.dumps({'status':'technical_mp4_created_not_editorially_approved','mp4':str(out),'duration_seconds':runtime,'scenes':len(paths),'workers':workers,'video_encoder':codec,'rigged_animation_fps':args.animation_fps,'delivery_fps':args.output_fps,'quality':args.quality}))
    if args.target_minutes and not args.target_minutes-.8<=runtime/60<=args.target_minutes+1.0:
        raise ValueError('Video assembled but narrated runtime is not near target_minutes. Add genuine researched scenes and voice; do not pad loops.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Render actual 2D moving historical cartoon scenes with WAV speech')
    p.add_argument('episode',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--quality',choices=SIZES,default='standard')
    p.add_argument('--gpu',choices=('auto','on','off'),default='auto')
    p.add_argument('--animation-fps',type=int,choices=(8,12,24),default=12)
    p.add_argument('--output-fps',type=int,choices=(24,30),default=24)
    p.add_argument('--target-minutes',type=float)
    p.add_argument('--max-scenes',type=int,help='Only animate first N scenes for rapid preview/review')
    p.add_argument('--workers',type=int,default=2,help='Parallel independently rendered scenes; try 2–4 depending on RAM')
    p.add_argument('--cache-dir',type=Path,help='Persistent exact-scene render cache; speeds up future revisions')
    args=p.parse_args()
    run(args)
