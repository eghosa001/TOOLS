#!/usr/bin/env python3
"""Deterministic stage controls for reusable ASMR clip preparation.

This is a geometry/continuity guide, NOT a claim that Kandinsky obeys physics.
Renders in seconds on CPU; optional OpenCV/Pillow deps, no AI weights/downloads.
An approved high-quality first frame becomes the appearance source for each state.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class Stage:
    name: str
    time_s: float
    compression: float
    press_contact: bool


@dataclass(frozen=True)
class Timeline:
    kind: str
    fps: int
    duration_s: float
    stages: tuple[Stage, ...]
    allowed_actions: tuple[str, ...]


def parse_timeline(path: Path) -> Timeline:
    cfg = json.loads(path.read_text())
    if cfg.get('schema_version') != 1:
        raise ValueError('Unsupported stage controller schema')
    fps, duration = int(cfg['fps']), float(cfg['duration_seconds'])
    if fps < 1 or fps > 60 or duration <= 0 or duration > 30:
        raise ValueError('Unsafe clip timing')
    stages = tuple(Stage(str(x['name']), float(x['time_s']), float(x['compression']), bool(x['press_contact'])) for x in cfg['stages'])
    if len(stages) < 2 or abs(stages[0].time_s) > 1e-8 or abs(stages[-1].time_s-duration) > 1e-8:
        raise ValueError('Stages must span entire clip')
    if any(stages[i].time_s >= stages[i+1].time_s for i in range(len(stages)-1)):
        raise ValueError('Stages must have strictly ascending times')
    if any(not 0 <= s.compression <= .6 for s in stages):
        raise ValueError('Compression outside physical-safe guide limits')
    if any(s.compression > 0 and not s.press_contact for s in stages):
        raise ValueError('Cannot compress before tool contact')
    names = [s.name for s in stages]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate stage names')
    return Timeline(str(cfg['format_id']),fps,duration,stages,tuple(cfg.get('allowed_actions', ['press'])))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t*t*(3.0-2.0*t)


def get_state(tl: Timeline, t: float) -> dict:
    t = max(0.0, min(tl.duration_s, t))
    stages=tl.stages
    for i in range(len(stages)-1):
        p,n = stages[i],stages[i+1]
        if t <= n.time_s + 1e-7:
            phase=ease((t-p.time_s)/(n.time_s-p.time_s))
            compression=p.compression+(n.compression-p.compression)*phase
            # Before first contact, the press moves from offset to a fixed touch point.
            idx = next((i for i,x in enumerate(stages) if x.press_contact), len(stages)-1)
            contact_time=stages[idx].time_s
            contact_fraction=ease(t/max(contact_time,1e-5)) if contact_time>0 else 1.0
            return {'t':round(t,5),'stage':n.name if phase>=.999 else p.name,
                    'compression':compression,'contact_fraction':contact_fraction,
                    'contact':t>=contact_time-1e-5}
    return {'t':tl.duration_s, 'stage':stages[-1].name, 'compression':stages[-1].compression, 'contact_fraction':1.0,'contact':True}


def stable_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()


def clean_background(src: np.ndarray) -> np.ndarray:
    """Remove the source actor/press from the guide background; no generative inpaint.

    Deliberately plain backdrop; these geometry state guides must never be
    published as photoreal final ASMR or confused with a Kandinsky render.
    """
    h,w=src.shape[:2]
    result=np.zeros_like(src)
    # Approximate studio's soft teal/pink gradients using source side rows.
    ys,xs=np.mgrid[:h,:w].astype(np.float32)
    left=np.exp(-((xs+55.0)/100.0)**2)*np.exp(-((ys-h*.54)/(h*.40))**2)
    right=np.exp(-((xs-w-55.0)/110.0)**2)*np.exp(-((ys-h*.54)/(h*.42))**2)
    base=(3+5*np.sin(ys/h*np.pi)).astype(np.float32)
    for k in range(3):result[:,:,k]=np.clip(base + left*[30,40,0][k]+right*[25,0,32][k],0,255)
    # Preserve a subtle dark tabletop base, no simulated reflection masking errors.
    floor=int(h*.76)
    result[floor:]=np.clip(result[floor:].astype(np.float32)*.7+9,0,255).astype(np.uint8)
    cv2.line(result,(0,floor),(w,floor),(29,33,34),1,cv2.LINE_AA)
    return result


def source_polygon(w: int, h: int) -> np.ndarray:
    # Geometry anchor fitted to the approved original 480x864 reference image.
    # 6-point silhouette captures cube top, two side walls, fixed ground contact.
    unit=np.array([[.055,.338],[.49,.285],[.94,.338],[.948,.67],[.50,.764],[.072,.69]],dtype=np.float32)
    return np.rint(unit*np.array([w,h])).astype(np.int32)


def extract_foam(src: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    h,w=src.shape[:2]
    polygon=source_polygon(w,h)
    mask=np.zeros((h,w),np.uint8)
    cv2.fillPoly(mask,[polygon],255)
    # Include most true foam content; feather only 1.5px to avoid visible hard cut.
    mask=cv2.GaussianBlur(mask,(5,5),.65)
    return src,mask


def vertical_foam_warp(src: np.ndarray, mask: np.ndarray, compress: float) -> tuple[np.ndarray,np.ndarray,dict]:
    h,w=src.shape[:2]
    # A rigged deformation. The foam bottom is fixed (no sliding); the top moves
    # downward with axial compression; sides bulge modestly, not randomly.
    # This is a 2D approximation, not volumetric FEM/soft-body physics.
    bottom=.764*h;top=.285*h
    actual_height=bottom-top
    scale_y=1-compress
    dest_top=top+actual_height*compress
    yy,xx=np.mgrid[:h,:w].astype(np.float32)
    # Inverse y map of y_dest=bottom-(bottom-y_src)*(1-compression)
    src_y=bottom-(bottom-yy)/scale_y
    midx=.5*w
    z=np.clip((bottom-src_y)/actual_height,0,1)
    bulge=1+.18*compress*(1-z*z) # biggest at sides near the mid/low foam
    src_x=midx+(xx-midx)/bulge
    warped=cv2.remap(src,src_x,src_y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    alpha=cv2.remap(mask,src_x,src_y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    # Remove potential stray pixels below the floor and above the new upper surface.
    alpha[yy<(dest_top-2)]=0
    alpha[yy>(bottom+5)]=0
    return warped,alpha,{'foam_top_y':float(dest_top),'foam_bottom_y':float(bottom),
                         'foam_height_px':float(actual_height*scale_y),'compression':compress}


def paste_alpha(dst: np.ndarray, src: np.ndarray, mask: np.ndarray) -> np.ndarray:
    a=(mask.astype(np.float32)/255.0)[:,:,None]
    return np.clip(dst*(1-a)+src*a,0,255).astype('uint8')


def draw_press(dst: np.ndarray, state: dict, metrics: dict) -> tuple[np.ndarray,dict]:
    # Reproducible geometry: shaft & clear plate, constant width and x coordinate.
    h,w=dst.shape[:2]
    top_y=metrics['foam_top_y']
    gap_px=round(.027*h*(1-state['contact_fraction']))
    bottom_y=int(round(top_y-gap_px))
    plate_h=max(12,round(.065*h));p_top=bottom_y-plate_h
    # Transparent acrylic with fixed polygon and specular edge; no disappearing tool.
    overlay=dst.copy()
    plate_x1,plate_x2=int(.038*w),int(.966*w)
    cv2.rectangle(overlay,(plate_x1,p_top),(plate_x2,bottom_y),(205,213,221),-1)
    dst=cv2.addWeighted(dst,.76,overlay,.24,0)
    for y,opacity in [(p_top,.92),(bottom_y,.91)]:
        cv2.line(dst,(plate_x1,y),(plate_x2,y),(210,236,248),2,cv2.LINE_AA)
    cv2.line(dst,(plate_x1,p_top+2),(plate_x1,bottom_y-2),(183,221,237),2,cv2.LINE_AA)
    cv2.line(dst,(plate_x2,p_top+2),(plate_x2,bottom_y-2),(233,196,224),2,cv2.LINE_AA)
    # Stationary center shaft moves only vertically; centered on press, no perspective jumps.
    sx1,sx2=int(w*.403),int(w*.60)
    shaft_top=0
    cv2.rectangle(dst,(sx1,shaft_top),(sx2,p_top),(72,79,80),-1)
    cv2.line(dst,(sx1+5,shaft_top),(sx1+5,p_top),(225,218,207),3,cv2.LINE_AA)
    cv2.line(dst,(sx2-5,shaft_top),(sx2-5,p_top),(180,187,207),2,cv2.LINE_AA)
    return dst,{'press_bottom_y':bottom_y,'press_width_px':plate_x2-plate_x1,
                'press_x_center':(plate_x1+plate_x2)/2,'gap_px':gap_px,
                'contact':state['contact'],'press_stays_visible':True}


def render(src: np.ndarray, state: dict) -> tuple[np.ndarray,dict]:
    orig,mask=extract_foam(src)
    warped,alpha,metrics=vertical_foam_warp(orig,mask,state['compression'])
    canvas=clean_background(src)
    canvas=paste_alpha(canvas,warped,alpha)
    canvas,press=draw_press(canvas,state,metrics)
    combined={**state,**metrics,**press,'camera_scale':1.0,'camera_pan_x':0.0,'camera_pan_y':0.0,
              'object_identity_sha256':hashlib.sha256(orig.tobytes()).hexdigest()[:16]}
    if combined['contact'] and abs(combined['gap_px'])>1:
        raise ValueError('Contact requires zero geometric separation')
    if abs(combined['press_bottom_y']-combined['foam_top_y'])>2 and combined['contact']:
        raise ValueError('Tool must touch foam when contact is active')
    return canvas,combined


def make_contact_sheet(images: list[tuple[str,Path]], out: Path) -> None:
    thumb_w,thumb_h=240,465
    s=Image.new('RGB',(len(images)*thumb_w,thumb_h),(20,20,22))
    d=ImageDraw.Draw(s)
    for i,(name,path) in enumerate(images):
        img=Image.open(path).convert('RGB'); img.thumbnail((thumb_w,425))
        s.paste(img,(i*thumb_w+(thumb_w-img.width)//2,5))
        d.text((i*thumb_w+7,436),name,fill=(239,239,239))
    s.save(out)


def render_all(timeline_path: Path, image_path: Path, output_dir: Path, preview: bool=True) -> dict:
    tl=parse_timeline(timeline_path)
    if not image_path.is_file():raise FileNotFoundError(str(image_path))
    # Pillow supports the repo's compact AVIF reference; OpenCV builds often don't.
    with Image.open(image_path) as original:
        src=cv2.cvtColor(np.asarray(original.convert('RGB')),cv2.COLOR_RGB2BGR)
    h,w=src.shape[:2]
    if w<256 or h<456 or not h>w:raise ValueError('Expected portrait reference image at least 256x456')
    output_dir.mkdir(parents=True,exist_ok=True)
    states=[]
    stage_images=[]
    for stage in tl.stages:
        state=get_state(tl,stage.time_s)
        frame,meta=render(src,state)
        stage_file=output_dir/f'{len(stage_images):02d}_{stage.name}.png'
        cv2.imwrite(str(stage_file),frame)
        states.append(meta)
        stage_images.append((f'{stage.name}\n{100*state["compression"]:.0f}% compression',stage_file))
    make_contact_sheet(stage_images,output_dir/'stage_contact_sheet.jpg')
    events={'schema_version':1,'format_id':tl.kind,'fps':tl.fps,'duration_seconds':tl.duration_s,
            'source_sha256':stable_hash(image_path),'stages':states,
            'audio_cues':{'contact_seconds':next(x.time_s for x in tl.stages if x.press_contact),
                          'squish_intervals':[[a.time_s,b.time_s] for a,b in zip(tl.stages,tl.stages[1:]) if b.compression>a.compression],
                          'hold_seconds':tl.stages[-1].time_s},
            'intended_model':'Kandinsky6 native first-and-last-frame only if GPU compatible',
            'production_approval':'STAGE_GUIDE_ONLY_NOT_A_PUBLISHED_AI_VIDEO',
            'rendering_method':'deterministic_2d_pixel_warp_and_rig'}
    if preview:
        p=output_dir/'controlled_stage_guide_NOT_AI.mp4'
        frames=round(tl.duration_s*tl.fps)+1
        writer=cv2.VideoWriter(str(p),cv2.VideoWriter_fourcc(*'mp4v'),tl.fps,(w,h))
        if not writer.isOpened():raise RuntimeError('OpenCV cannot encode preview MP4')
        for i in range(frames):
            st=get_state(tl,min(i/tl.fps,tl.duration_s))
            image,_=render(src,st)
            writer.write(image)
        writer.release()
    (output_dir/'stage_metrics.json').write_text(json.dumps(events,indent=2))
    return events


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--first-frame',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--no-preview',action='store_true')
    a=p.parse_args()
    info=render_all(a.config,a.first_frame,a.out,not a.no_preview)
    print(json.dumps({'result':'stage_guides_generated','output':str(a.out),
                      'states':len(info['stages']),'audio_cues':info['audio_cues'],
                      'quality_status':info['production_approval']},indent=2))