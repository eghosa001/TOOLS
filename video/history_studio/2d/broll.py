#!/usr/bin/env python3
"""FFmpeg animated 2D illustration shots, with real narration audio.

Avoids redrawing unchanged still art with Pillow at every frame. These are
illustrative reconstructions, never historic images or external licenses.
"""
from __future__ import annotations
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _text_style(scene, size, out_file):
    w, h = size
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas, 'RGBA')
    font_candidates = [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('C:/Windows/Fonts/arial.ttf')]
    fonts = [p for p in font_candidates if p.is_file()]
    try:
        f = ImageFont.truetype(str(fonts[0]), max(14, round(h * .036))) if fonts else ImageFont.load_default()
        small = ImageFont.truetype(str(fonts[0]), max(12, round(h * .022))) if fonts else ImageFont.load_default()
    except OSError:
        f = small = ImageFont.load_default()
    title = scene.get('chapter', 'HISTORICAL RECONSTRUCTION').upper()
    subtitle = scene.get('visual_label', 'ILLUSTRATED RECONSTRUCTION')
    d.rounded_rectangle((int(w*.033), int(h*.06), int(w*.91), int(h*.15)), radius=round(h*.017), fill=(16, 22, 30, 195))
    d.text((round(w*.05), round(h*.076)), title, font=f, fill=(250, 237, 200, 245))
    d.rounded_rectangle((int(w*.032), int(h*.91), int(w*.75), int(h*.97)), radius=round(h*.012),fill=(14, 20, 30, 196))
    d.text((round(w*.045), round(h*.927)), subtitle, font=small, fill=(250,240,212,235))
    canvas.save(out_file)


def render(scene, audio_path, out, size, fps, codec, duration):
    """Create an H264/AAC MP4 with genuine video-camera motion from one image."""
    art = Path(scene['background'])
    if not art.is_file():
        raise FileNotFoundError(art)
    with Image.open(art) as check:
        if min(check.size) < min(size)//2:
            raise ValueError('B-roll illustration too small for output; upscaling not approved')
        check.verify()
    w, h = size
    nframes = max(1, math.ceil(duration * fps))
    overlay = out.with_suffix('.labels.png')
    _text_style(scene, size, overlay)
    overscan = 1.13
    W = (int(math.ceil(w * overscan))//2)*2
    H = (int(math.ceil(h * overscan))//2)*2
    # x/y are evaluated every frame: a real camera move, not repeated stills.
    move = str(scene.get('camera_move', 'right'))
    if move not in ('left','right','up','down','static'):
        raise ValueError('Unrecognized camera movement')
    progress = f'n/{max(1,nframes-1)}'
    x = {'left':f'(in_w-out_w)*(1-{progress})',
         'right':f'(in_w-out_w)*{progress}',
         'up':'(in_w-out_w)/2', 'down':'(in_w-out_w)/2',
         'static':'(in_w-out_w)/2'}[move]
    y = {'left':'(in_h-out_h)/2','right':'(in_h-out_h)/2',
         'up':f'(in_h-out_h)*(1-{progress})',
         'down':f'(in_h-out_h)*{progress}',
         'static':'(in_h-out_h)/2'}[move]
    filter_complex = (
        f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,'
        f'crop={w}:{h}:x={x}:y={y},setsar=1[bg];'
        f'[bg][2:v]overlay=0:0:shortest=1,format=yuv420p[v]'
    )
    out.parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
         '-loop','1','-framerate',str(fps),'-i',str(art),
         '-i',str(audio_path),
         '-loop','1','-framerate',str(fps),'-i',str(overlay),
         '-filter_complex',filter_complex,'-map','[v]','-map','1:a:0',
         '-frames:v',str(nframes),'-c:v',codec]
    if codec == 'libx264':
        cmd+=['-preset','veryfast','-crf','20']
    else:
        cmd+=['-preset','p4','-cq','21','-b:v','0']
    cmd+=['-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',
          '-af','apad','-shortest','-movflags','+faststart',str(out)]
    try:
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=max(60,int(duration*10)))
        if proc.returncode:
            raise RuntimeError('B-roll FFmpeg failed: '+proc.stderr[-2000:])
        if not out.is_file() or out.stat().st_size<1000:
            raise RuntimeError('B-roll MP4 not generated')
    finally:
        overlay.unlink(missing_ok=True)
    return duration