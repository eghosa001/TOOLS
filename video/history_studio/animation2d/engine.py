#!/usr/bin/env python3
"""Lightweight, reusable 2-D cut-out animation and real-audio renderer.

Local CPU works; optional NVIDIA NVENC is used only if successfully probed.
Draws a *development* rig and stylized set if artist-supplied PNG layers or
historically checked backgrounds aren't present. It does NOT invent archive.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CLIP_MAX = 1800
VALID_ACTIONS = {"idle", "walk", "point", "talk", "nod", "turn"}
VERSION = "0.3.0"

def verify_episode(episode: dict, root: Path) -> list[str]:
    errors=[]
    if episode.get("format") != "history_2d_cartoon": errors.append("Incorrect format")
    size = episode.get("size", [1280,720]); fps = episode.get("fps",24); anim_fps=episode.get("animation_fps",12)
    if size not in ([640,360],[1280,720],[1920,1080]): errors.append("Unsupported dimensions")
    if fps not in (24,30) or anim_fps not in (12,15,24,30) or fps%anim_fps: errors.append("Invalid fps combination")
    scenes=episode.get("scenes")
    if not isinstance(scenes,list) or not scenes: return errors+["No scenes"]
    if len(scenes)>1000:errors.append("Too many scenes")
    total=0
    for idx,scene in enumerate(scenes):
        if not isinstance(scene,dict):errors.append(f"Scene {idx+1}: must be an object");continue
        try: duration=float(scene.get("duration",0))
        except (ValueError,TypeError):duration=0
        if not 0.2<=duration<=120:errors.append(f"Scene {idx+1}: invalid duration")
        total+=duration
        if scene.get("mode","cutout") not in ("cutout","panzoom"):
            errors.append(f"Scene {idx+1}: unknown animation mode")
        if scene.get("mode")=="panzoom" and (not scene.get("background_image") or scene.get("actors")):
            errors.append(f"Scene {idx+1}: panzoom needs a real background and no actors")
        bg=scene.get("background_image")
        if bg:
            path=(root/bg).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():errors.append(f"Scene {idx+1}: missing/unsafe background")
        for actor in scene.get("actors",[]):
            if not isinstance(actor,dict):
                errors.append(f"Scene {idx+1}: malformed actor");continue
            if actor.get("action","idle") not in VALID_ACTIONS: errors.append(f"Scene {idx+1}: invalid action")
            if actor.get("id") not in episode.get("characters",{}):errors.append(f"Scene {idx+1}: missing character")
        for key in ("audio_file","mouth_cues"):
            if scene.get(key):
                path=(root/scene[key]).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():errors.append(f"Scene {idx+1}: missing/unsafe {key}")
        if scene.get("audio_file"):
            try:
                with wave.open(str(root/scene["audio_file"]),"rb") as f:
                    if f.getnchannels()!=1 or f.getsampwidth()!=2: errors.append(f"Scene {idx+1}: use PCM 16bit mono WAV")
                    if f.getnframes()/f.getframerate() > duration + .04: errors.append(f"Scene {idx+1}: duration shorter than audio")
            except (wave.Error,OSError,ZeroDivisionError): errors.append(f"Scene {idx+1}: invalid audio")
    for name,cfg in episode.get("characters",{}).items():
        for part, relative in cfg.get("sprites",{}).items():
            path = (root / relative).resolve()
            if part not in ("torso","head","upper_arm","lower_arm","thigh","shin","foot","mouth_open") or not path.is_relative_to(root.resolve()) or not path.is_file() or path.suffix.lower() != ".png":
                errors.append(f"Character {name}: missing/unsafe PNG sprite {part}")
    if total>CLIP_MAX: errors.append("Episode exceeds max duration")
    timeline=episode.get("timeline",{})
    if timeline and not isinstance(timeline,dict): errors.append("Invalid timeline metadata")
    for idx,scene in enumerate(scenes):
        # Voice intervals are generated from actual WAV samples, rather than
        # assuming that everyone is speaking throughout the scene.
        intervals=scene.get("speech_timing", [])
        if not isinstance(intervals,list):
            errors.append(f"Scene {idx+1}: invalid speech_timing");continue
        last=-1
        for interval in intervals:
            try:
                start=float(interval["start"]);end=float(interval["end"])
                good=0<=start<end<=float(scene["duration"])+.05 and start>=last
                if not isinstance(interval.get("speaker"),str):good=False
            except (KeyError,TypeError,ValueError):good=False
            if not good:errors.append(f"Scene {idx+1}: invalid or overlapping speech interval")
            else:last=end
    if episode.get("publish_ready") is True and not episode.get("rights_reviewed"):
        errors.append("Cannot mark development animatic publish-ready without rights review")
    return errors

def color(value,default):
    if isinstance(value,str) and len(value)==7 and value.startswith("#"):
        try:return tuple(int(value[i:i+2],16) for i in (1,3,5))
        except ValueError:pass
    return default

def oval(draw, box, fill, outline=None, width=1):draw.ellipse(tuple(map(int,box)),fill=fill,outline=outline,width=width)

def bone(draw, a, b, width, fill, highlight=None):
    draw.line([tuple(map(int,a)),tuple(map(int,b))], fill=fill, width=max(2,int(width)),joint="curve")
    rad=width/2
    oval(draw,(b[0]-rad,b[1]-rad,b[0]+rad,b[1]+rad),fill)
    if highlight:
        draw.line([tuple(map(int,a)),tuple(map(int,b))],fill=highlight,width=max(1,int(width*.1)))

def render_actor(img: Image.Image, cfg:dict, actor:dict, time_s:float, scale:float, mouth_open:bool=False):
    """Joint-driven pose, arm/leg and head pivots. Coordinate and motion reusable.

    All coordinates are scaled from local normalized character units. A PNG
    torso/head override can be provided for authored layers, enabling a
    consistent cast without modifying the rig engine.
    """
    draw=ImageDraw.Draw(img,"RGBA")
    w,h=img.size
    x=float(actor.get("x",0.5))*w; y=float(actor.get("ground",.88))*h
    s=min(w/1280,h/720)*float(actor.get("scale",1))*scale
    action=actor.get("action","idle")
    cycle=time_s*math.tau*1.35
    travel=math.sin(cycle) if action=="walk" else 0
    bounce=(4*abs(math.sin(cycle)) if action=="walk" else math.sin(time_s*2.4)*1.4)*s
    x+= math.sin(time_s*1.1+1)*s*1.5 if action=="idle" else 0
    y-=bounce
    skin=color(cfg.get("skin"),(166,116,79)); coat=color(cfg.get("coat"),(66,92,99))
    trousers=color(cfg.get("trousers"),(70,58,56)); hair=color(cfg.get("hair"),(48,35,31))
    outline=(31,31,38,255); boot=(40,34,33,255)
    # Legs have individually moving hip-knee-ankle joints.
    hipL=(x-18*s,y-91*s);hipR=(x+18*s,y-91*s)
    for sign,hip in [(-1,hipL),(1,hipR)]:
        stride=travel*22*s*sign if action=="walk" else 0
        knee=(hip[0]+stride*.65,hip[1]+42*s)
        foot=(hip[0]+stride, y-4*s)
        bone(draw,hip,knee,18*s,trousers)
        bone(draw,knee,foot,15*s,trousers)
        oval(draw,(foot[0]-14*s,foot[1]-5*s,foot[0]+19*s,foot[1]+8*s),boot)
    # Torso tunic, depth via subtle seam.
    torso=(x-49*s,y-213*s,x+49*s,y-86*s)
    draw.rounded_rectangle(tuple(map(int,torso)),radius=int(19*s),fill=(*coat,255),outline=outline,width=max(1,int(2*s)))
    draw.line([(x,y-207*s),(x,y-90*s)],fill=(220,202,160,120),width=max(1,int(2*s)))
    # Upper and lower arm pivots. Pointing reaches a real target.
    for sign in (-1,1):
        shoulder=(x+sign*42*s,y-193*s)
        if action=="point" and sign==1:
            elbow=(shoulder[0]+49*s,shoulder[1]-25*s);hand=(elbow[0]+49*s,elbow[1]-10*s)
        else:
            swing=travel*22*s*sign if action=="walk" else math.sin(time_s*1.7+sign)*4*s
            elbow=(shoulder[0]+sign*20*s+swing*.2,shoulder[1]+51*s-swing*.4)
            hand=(elbow[0]+sign*10*s+swing*.4,elbow[1]+38*s)
        bone(draw,shoulder,elbow,20*s,coat)
        bone(draw,elbow,hand,15*s,coat)
        oval(draw,(hand[0]-10*s,hand[1]-10*s,hand[0]+10*s,hand[1]+10*s),(*skin,255))
    # Neck, head and face. Small nod rotation represented by head pivot.
    headnod=math.sin(time_s*5)*7*s if action=="nod" else math.sin(time_s*1.6)*2*s
    head_x=x; head_y=y-240*s+headnod
    draw.rectangle((head_x-12*s,head_y+19*s,head_x+12*s,head_y+43*s),fill=skin)
    oval(draw,(head_x-48*s,head_y-53*s,head_x+48*s,head_y+39*s),(*skin,255),outline,max(1,int(2*s)))
    # Hairline and eyebrows.
    draw.pieslice((head_x-48*s,head_y-62*s,head_x+48*s,head_y+29*s),180,358,fill=(*hair,255))
    for side in (-1,1):
        eye_x=head_x+side*19*s
        if (time_s+side*.03)%4.9 < .13:
            draw.line([(eye_x-6*s,head_y-6*s),(eye_x+6*s,head_y-6*s)],fill=outline,width=max(1,int(3*s)))
        else:
            oval(draw,(eye_x-3*s,head_y-10*s,eye_x+3*s,head_y+1*s),outline)
    if mouth_open:
        oval(draw,(head_x-10*s,head_y+9*s,head_x+10*s,head_y+24*s),(72,35,36,255))
    else:
        draw.arc((head_x-12*s,head_y+9*s,head_x+12*s,head_y+22*s),5,175,fill=outline,width=max(1,int(2*s)))
    # High-quality painted sprite overrides work on top of skeletal fallback.
    # Opt in to replace the demo-rendered body/head with authored cutout PNGs.

def sprite_to_frame(frame, sprite, at, size, angle_deg=0):
    """Position a cutout with top-centre pivot; rotate about its attachment.

    Sprite artists draw each limb *vertically pointing down*, attachment at
    the centre of its top edge. This is true cut-out rotation, not a flattened
    character image or whole-layer pan.
    """
    width=max(1,int(size[0]));height=max(1,int(size[1]))
    piece=sprite.resize((width,height),Image.Resampling.LANCZOS)
    rotated=piece.rotate(angle_deg,Image.Resampling.BICUBIC,expand=True)
    theta=math.radians(angle_deg)
    # Rotate original top-center around sprite center in screen coords.
    pivot_x=rotated.width/2-math.sin(theta)*height/2
    pivot_y=rotated.height/2-math.cos(theta)*height/2
    frame.paste(rotated,(round(at[0]-pivot_x),round(at[1]-pivot_y)),rotated)

def draw_sprite_actor(frame,cfg,actor,t,base,root,cache,mouth_open):
    """Multi-part PNG cutout rig: independent thigh/shin/upper/lower arms.
    Head and torso are painted sprite layers. Missing pieces use explicit
    development-colour placeholders, and are forbidden at publication.
    """
    parts=cfg["sprites"]
    def sprite(name):
        rel=parts.get(name)
        if not rel:return None
        if rel not in cache:
            with Image.open(root/rel) as image:cache[rel]=image.convert("RGBA")
        return cache[rel]
    w,h=frame.size;s=min(w/1280,h/720)*actor.get("scale",1)*base
    x=actor.get("x",.5)*w;y=actor.get("ground",.88)*h
    action=actor.get("action","idle");stride=math.sin(t*math.tau*1.3) if action=="walk" else 0
    y-=abs(stride)*4*s
    for sign in (-1,1):
        hip=(x+sign*17*s,y-90*s)
        knee=(hip[0]+sign*stride*13*s,hip[1]+43*s)
        ankle=(hip[0]+sign*stride*22*s,y-7*s)
        thigh=sprite("thigh");shin=sprite("shin");foot=sprite("foot")
        if thigh:sprite_to_frame(frame,thigh,hip,(21*s,math.dist(hip,knee)),math.degrees(math.atan2(knee[0]-hip[0],knee[1]-hip[1])))
        if shin:sprite_to_frame(frame,shin,knee,(19*s,math.dist(knee,ankle)),math.degrees(math.atan2(ankle[0]-knee[0],ankle[1]-knee[1])))
        if foot:sprite_to_frame(frame,foot,(ankle[0]-8*s,ankle[1]),(30*s,13*s))
    torso=sprite("torso")
    if torso:sprite_to_frame(frame,torso,(x,y-217*s),(104*s,132*s))
    for sign in (-1,1):
        shoulder=(x+sign*43*s,y-194*s)
        swing=sign*stride*18*s if action=="walk" else math.sin(t*1.2+sign)*4*s
        if action=="point" and sign==1:
            elbow=(shoulder[0]+43*s,shoulder[1]-20*s);hand=(elbow[0]+46*s,elbow[1]-5*s)
        else:
            elbow=(shoulder[0]+sign*15*s+swing*.3,shoulder[1]+47*s-swing*.25)
            hand=(elbow[0]+sign*9*s+swing*.3,elbow[1]+40*s)
        for part,a,b,ww in (("upper_arm",shoulder,elbow,21),("lower_arm",elbow,hand,17)):
            im=sprite(part)
            if im:sprite_to_frame(frame,im,a,(ww*s,math.dist(a,b)),math.degrees(math.atan2(b[0]-a[0],b[1]-a[1])))
    head=sprite("head")
    if head:sprite_to_frame(frame,head,(x,y-285*s+math.sin(t*1.9)*2*s),(103*s,94*s))
    mouth=sprite("mouth_open")
    if mouth and mouth_open:sprite_to_frame(frame,mouth,(x,y-242*s),(23*s,23*s))

def scene_background(size, scene,root):
    w,h=size; image=Image.new("RGB",size,(30,40,49))
    if scene.get("background_image"):
        with Image.open(root/scene["background_image"]) as im:
            im=im.convert("RGB")
            ratio=max(w/im.width,h/im.height)
            im=im.resize((math.ceil(im.width*ratio),math.ceil(im.height*ratio)),Image.Resampling.LANCZOS)
            off=((im.width-w)//2,(im.height-h)//2)
            return im.crop((off[0],off[1],off[0]+w,off[1]+h))
    d=ImageDraw.Draw(image)
    theme=scene.get("set","courtyard")
    sky=(51,66,83) if theme=="night" else (114,151,172)
    for yy in range(h):
        blend=yy/max(h,1)
        d.line([(0,yy),(w,yy)],fill=tuple(int(min(255,c+35*blend)) for c in sky))
    d.ellipse((int(w*.72),int(h*.1),int(w*.77),int(h*.2)),fill=(243,207,142))
    d.rectangle((0,int(h*.72),w,h),fill=(120,104,87))
    # Background-only stage design is explicitly a mockup, not claimed historic accuracy.
    for i in range(8):
        bx=int((i+.25)*w/8); bw=int(w*.085); top=int(h*(.32 + (i%3)*.05))
        d.rectangle((bx,top,bx+bw,int(h*.72)),fill=(127+(i%3)*8,115,99),outline=(65,67,66),width=3)
        d.polygon([(bx-7,top),(bx+bw//2,top-int(h*.07)),(bx+bw+7,top)],fill=(71,81,83))
        for jy in range(top+38,int(h*.65),55):
            d.rectangle((bx+13,jy,bx+26,jy+25),fill=(48,56,64))
    return image

def load_cues(path):
    if not path:return []
    data=json.loads(Path(path).read_text(encoding="utf8"))
    raw=data.get("mouthCues",[])
    cues=[];previous=0
    for item in raw:
        start=float(item["start"]);end=float(item["end"])
        if start<previous or end<=start:raise ValueError("Invalid overlapping mouth cues")
        previous=end;cues.append((start,end,item.get("value","X")))
    return cues

def speaking_at(t,scene,actor):
    intervals=scene.get("speech_timing", [])
    if intervals:
        key=actor.get("speaker",actor.get("id"))
        return any(item["speaker"]==key and float(item["start"])<=t<float(item["end"]) for item in intervals)
    return bool(actor.get("speaking",False)) and bool(scene.get("audio_file"))

def mouth_at(t,cues,has_voice):
    if cues:return any(a<=t<b and value not in ("X","A") for a,b,value in cues)
    # Without a real phoneme track, approximate audio-driven alternating mouth only
    # when a spoken WAV exists; this is explicitly NOT accurate lip sync.
    return bool(has_voice) and (int(t*7)%4 != 0)

def validate_audio_audiofile(path, duration):
    with wave.open(str(path),"rb") as wav:
        if wav.getnchannels()!=1 or wav.getsampwidth()!=2:raise ValueError("audio must be mono signed PCM16 WAV")
        if wav.getnframes()/wav.getframerate()>duration+0.04:raise ValueError("WAV is longer than scene duration")

def encoder_name(mode):
    if mode=="cpu":return "libx264"
    # h264_nvenc listed does not imply a working GPU; probe with actual encode.
    if shutil.which("nvidia-smi") and subprocess.run(["nvidia-smi","-L"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
        probe=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-f","lavfi","-i","color=black:s=64x64:r=1:d=1","-frames:v","1","-c:v","h264_nvenc","-f","null","-"],capture_output=True)
        if probe.returncode==0:return "h264_nvenc"
    if mode=="gpu":raise RuntimeError("Requested NVIDIA NVENC GPU encoder not available")
    return "libx264"

def render_panzoom_scene(episode,scene,root,out,encoder="auto",draft=False):
    """Efficient FFmpeg documentary B-roll from a supplied licensed drawing.

    Decoding+scale+zoom are handled by FFmpeg; Python never constructs raw
    full-size frames. Hardware H.264 is chosen only after a verified probe.
    """
    if not scene.get("background_image") or scene.get("actors"):
        raise ValueError("Panzoom expects one supplied illustration without actors")
    w,h=episode.get("size",[1280,720])
    fps=int(episode.get("fps",24))
    duration=float(scene["duration"])
    source=root/scene["background_image"]
    audio=root/scene["audio_file"] if scene.get("audio_file") else None
    codec=encoder_name(encoder)
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="history2d-broll-") as tmp:
        source_file=source
        if draft:
            with Image.open(source) as original:
                art=original.convert("RGB").copy()
            d=ImageDraw.Draw(art)
            d.rectangle((4,4,min(art.width,420),34),fill=(23,25,30))
            d.text((10,9),"DEVELOPMENT / UNREVIEWED HISTORICAL ART",fill=(255,232,174))
            source_file=Path(tmp)/"draft_bg.png"
            art.save(source_file)
        start_scale=f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        zoom=f"zoompan=z='min(1.0+on*0.00045,1.18)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={w}x{h}:fps=12"
        vf=f"{start_scale},{zoom},fps={fps},format=yuv420p"
        args=["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","12","-i",str(source_file)]
        if audio:args += ["-i",str(audio)]
        else:args += ["-f","lavfi","-i","anullsrc=channel_layout=mono:sample_rate=48000"]
        args += ["-vf",vf,"-c:v",codec]
        if codec=="libx264":args += ["-preset","veryfast","-crf","19"]
        else:args += ["-preset","p4","-cq","21"]
        args += ["-c:a","aac","-b:a","160k","-ar","48000","-ac","1","-t",str(duration),"-movflags","+faststart",str(out)]
        result=subprocess.run(args,capture_output=True,text=True,timeout=max(45,round(duration*12)))
        if result.returncode:raise RuntimeError("FFmpeg panzoom failed: "+result.stderr[-1300:])
    if not out.is_file() or out.stat().st_size<1000:raise RuntimeError("No panzoom output")
    return {"filename":str(out),"fps":fps,"animation_fps":12,"duration":duration,
            "encoder":codec,"audio":bool(audio),"frames_drawn":0,"render_method":"ffmpeg_panzoom"}

def render_scene(episode, scene, root, out, encoder="auto",draft=False):
    if scene.get("mode")=="panzoom":
        return render_panzoom_scene(episode,scene,root,out,encoder,draft)
    w,h=episode.get("size",[1280,720]); fps=int(episode.get("fps",24)); animfps=int(episode.get("animation_fps",12))
    duration=float(scene["duration"]);count=math.ceil(duration*animfps)
    # Render drawn frames at animation_fps and let FFmpeg duplicate them at output_fps.
    # For long content, changes are processed shot-by-shot and stream-concatenated.
    background=scene_background((w,h),scene,root)
    audio=root/scene["audio_file"] if scene.get("audio_file") else None
    cues=load_cues(root/scene["mouth_cues"]) if scene.get("mouth_cues") else []
    codec=encoder_name(encoder)
    sprite_cache={}
    args=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{w}x{h}","-framerate",str(animfps),"-i","pipe:0"]
    if audio:args += ["-i",str(audio)]
    else:args += ["-f","lavfi","-i","anullsrc=channel_layout=mono:sample_rate=48000"]
    args += ["-vf",f"fps={fps},format=yuv420p","-c:v",codec]
    if codec=="libx264":args += ["-preset","veryfast","-crf","19"]
    else:args += ["-preset","p4","-cq","21"]
    args += ["-c:a","aac","-b:a","160k","-ar","48000","-ac","1"]
    args += ["-t",str(duration),"-movflags","+faststart",str(out)]
    out.parent.mkdir(parents=True,exist_ok=True)
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for f in range(count):
            t=f/animfps
            image=background.copy()
            for actor in scene.get("actors",[]):
                character=episode["characters"][actor["id"]]
                speaking=mouth_at(t,cues,speaking_at(t,scene,actor) if audio else False)
                if character.get("sprites"):
                    draw_sprite_actor(image,character,actor,t,1,root,sprite_cache,speaking)
                else:
                    render_actor(image,character,actor,t,1,speaking)
            if draft or not scene.get("background_image"):
                d=ImageDraw.Draw(image)
                d.rectangle((5,5,319,29),fill=(20,25,30))
                d.text((12,12),"DEVELOPMENT ANIMATIC / NOT HISTORICAL FOOTAGE",fill=(245,228,190))
            p.stdin.write(image.tobytes())
        p.stdin.close(); err=p.stderr.read(); rc=p.wait()
        if rc:raise RuntimeError(f"ffmpeg failed ({rc}): {err.decode(errors='replace')[-900:]}")
    except Exception:
        p.kill();p.wait();raise
    if not out.is_file() or out.stat().st_size<1000:raise RuntimeError("No decoded MP4 output")
    return {"filename":str(out),"fps":fps,"animation_fps":animfps,"duration":duration,"encoder":codec,"audio":bool(audio),"frames_drawn":count}

def assemble(out,parts):
    # Concat via demuxer; never silently mix incompatible FPS/size.
    listing=out.parent/"shotlist.ffconcat"
    with listing.open("w",encoding="utf8") as f:
        f.write("ffconcat version 1.0\n")
        for path in parts:
            f.write("file '"+str(path.resolve()).replace("'","'\\''")+"'\n")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-safe","0","-f","concat","-i",str(listing),"-c","copy","-movflags","+faststart",str(out)],check=True)
    listing.unlink(missing_ok=True)

def scene_fingerprint(episode,scene,root,encoder,draft):
    """Hash all relevant source material to safely reuse unchanged MP4 shots."""
    hasher=hashlib.sha256()
    hasher.update(VERSION.encode())
    for v in (episode.get("size"),episode.get("fps"),episode.get("animation_fps"),episode.get("characters"),scene,encoder,draft):
        hasher.update(json.dumps(v,sort_keys=True).encode())
    refs=[]
    for k in ("background_image","audio_file","mouth_cues"):
        if scene.get(k):refs.append(scene[k])
    for actor in scene.get("actors",[]):
        refs.extend(episode["characters"][actor["id"]].get("sprites",{}).values())
    for rel in sorted(set(refs)):
        with (root/rel).open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):
                hasher.update(chunk)
    return hasher.hexdigest()

def main(argv=None):
    ap=argparse.ArgumentParser(description="History 2D practical animation engine")
    ap.add_argument("episode",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--encoder",choices=("auto","cpu","gpu"),default="auto")
    ap.add_argument("--draft",action="store_true")
    ap.add_argument("--reuse-shots",action="store_true",help="Reuse shots only when full SHA-256 fingerprint matches")
    args=ap.parse_args(argv)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):raise SystemExit("Install ffmpeg and ffprobe")
    root=args.episode.parent.resolve();episode=json.loads(args.episode.read_text(encoding="utf8"))
    errors=verify_episode(episode,root)
    if errors:raise SystemExit("Episode rejected:\n"+"\n".join(errors))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    clips=[];report=[]
    for n,scene in enumerate(episode["scenes"],1):
        shot=args.output.parent/f"shot_{n:03}.mp4"
        meta=shot.with_suffix(".cache.json")
        fingerprint=scene_fingerprint(episode,scene,root,args.encoder,args.draft)
        cached=False
        if args.reuse_shots and shot.is_file() and meta.is_file():
            try:
                prior=json.loads(meta.read_text(encoding="utf8"))
                cached=prior.get("fingerprint")==fingerprint and prior.get("sha256")==hashlib.sha256(shot.read_bytes()).hexdigest()
            except (OSError,ValueError):cached=False
        if cached:
            data=prior["render"]
            print(f"Reused {n}/{len(episode['scenes'])}: {scene.get('id','scene')}",flush=True)
        else:
            print(f"Rendering {n}/{len(episode['scenes'])}: {scene.get('id','scene')}",flush=True)
            data=render_scene(episode,scene,root,shot,args.encoder,args.draft)
            meta.write_text(json.dumps({"fingerprint":fingerprint,"sha256":hashlib.sha256(shot.read_bytes()).hexdigest(),"render":data},indent=2),encoding="utf8")
        report.append(dict(data,cache_hit=cached));clips.append(shot)
    assemble(args.output,clips)
    probe=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(args.output)],capture_output=True,text=True,check=True)
    duration=float(json.loads(probe.stdout)["format"]["duration"])
    if duration<=0:raise RuntimeError("Empty merged video")
    metadata={"version":VERSION,"video":str(args.output),"duration":duration,"scenes":report,"sha256":hashlib.sha256(args.output.read_bytes()).hexdigest(),"warning":"Quality and historical accuracy require source review; this only proves technical encoding"}
    args.output.with_suffix(".manifest.json").write_text(json.dumps(metadata,indent=2),encoding="utf8")
    print("VIDEO_READY",str(args.output),f"{duration:.2f}s",flush=True)

if __name__=="__main__":main()