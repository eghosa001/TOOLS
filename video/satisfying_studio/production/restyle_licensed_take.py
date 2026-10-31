#!/usr/bin/env python3
"""Manually directed, loss-conscious SINGLE-stock-shot retiming and grading.

Requires a real cleared source, source hash, personally approved trim and frame.
This does not select stock, invent movement, loop, assemble a video, generate
contact Foley, or confer YouTube/premium approval. The output is intentionally
PICTURE ONLY; the source action is re-timed so original or recorded Foley must
be hand-aligned again against its exact output frames before release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import subprocess
import sys

STYLES = {
    "natural": (1.00, 1.00, 0.00, 1.00),
    "cinematic": (1.09, 0.90, -0.015, 0.98),
    "glossy_vivid": (1.075, 1.16, 0.004, 1.015),
    "pastel_soft": (0.97, 0.89, 0.012, 1.03),
    "cool_studio": (1.045, 1.10, -0.004, 1.00),
}
LICENSES = {"Pexels License", "Pixabay Content License", "Mixkit Stock Video Free License", "CC0", "CC BY 4.0", "original"}

class ShotBlocked(ValueError):
    pass

def require(condition, why):
    if not condition:
        raise ShotBlocked(why)

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def probe(path):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],check=True,capture_output=True,text=True,timeout=35)
    return json.loads(p.stdout)

def get_video(info):
    streams=[s for s in info.get('streams',[]) if s.get('codec_type')=='video']
    require(len(streams)==1,'Expected exactly one source video stream')
    return streams[0]

def finite_num(value, field, minval, maxval):
    require(type(value) in (int, float) and math.isfinite(value) and minval <= value <= maxval,
            f'{field} must be between {minval} and {maxval}')
    return float(value)

def validate(plan, directory):
    require(plan.get('manually_selected_take') is True and plan.get('visual_framing_approved') is True,
            'Human/editor must approve exact source, crop and intended shot before any edit')
    require(plan.get('source_role') == 'LICENSED_STOCK', 'Never edit a reference-only video')
    require(plan.get('rights_to_modify_verified') is True, 'Actual source licence must have been checked')
    require(plan.get('license') in LICENSES, 'Unknown/restricted stock licence')
    require(isinstance(plan.get('source_page'),str) and plan['source_page'].startswith('https://'),
            'Individual source landing page is required')
    if plan['license']=='CC BY 4.0':
        require(isinstance(plan.get('required_attribution'), str) and len(plan['required_attribution'])>=20,
                'Attribution and modifications statement required')
    src=plan.get('source_file')
    require(isinstance(src,str) and len(src)>0, 'Source file missing')
    path=Path(src)
    require(not path.is_absolute() and '..' not in path.parts, 'Only relative safe source paths are allowed')
    path=(directory/path).resolve()
    require(path.is_relative_to(directory.resolve()) and path.is_file(), 'Licensed source not on disk')
    require(isinstance(plan.get('source_sha256'),str) and sha256(path)==plan['source_sha256'],
            'Original source bytes differ from rights ledger')
    info=probe(path); v=get_video(info)
    fps=Fraction(v.get('avg_frame_rate') or v.get('r_frame_rate') or '0')
    require(fps>0 and fps<=240, 'Invalid or unavailable source frame rate')
    require(v.get('codec_name') not in {'mjpeg'},'Unrecognized source codec for this workflow')
    require(v.get('color_transfer') not in {'smpte2084','arib-std-b67'},
            'HDR source requires a separate reviewed color-management workflow')
    original_duration=float(info['format']['duration'])
    start=finite_num(plan.get('source_start_seconds'),'source_start_seconds',0,72000)
    duration=finite_num(plan.get('source_duration_seconds'),'source_duration_seconds',.5,72000)
    require(start+duration<=original_duration+.005, 'Selected segment exceeds source duration')
    speed=finite_num(plan.get('playback_speed',1),'playback_speed',0.25,2.0)
    target_fps=plan.get('target_fps',24)
    require(type(target_fps) is int and target_fps==24,'Source retime produces native 24fps shots only')
    # No fabricated motion/duplicated frames permitted. Slowing down only spends
    # actual source frames; 30fps -> 24fps allows ~1.25x duration, not 2x.
    require(float(fps)*speed>=target_fps-0.005,
            f'Retime would duplicate/invent movement: source {float(fps):.3f} fps, speed {speed:.4f}. '
            f'Minimum acceptable speed {target_fps/float(fps):.4f}')
    require(plan.get('interpolate_frames',False) is False,
            'Motion interpolation must be a separate manually reviewed experiment')
    target=plan.get('output_size', [720,1280]); require(type(target) is list and len(target)==2 and tuple(target) in {(720,1280),(1080,1920),(1280,720),(1920,1080)},
            'Explicit standard 720p or 1080p composition required')
    w,h=map(int,target); sw,sh=int(v['width']),int(v['height'])
    crop=plan.get('crop_rect')
    if crop is not None:
        require(type(crop) is list and len(crop)==4 and all(type(x) is int for x in crop),
                'Crop rectangle must be four exact integer values x,y,w,h')
        x,y,cw,ch=crop
        require(x>=0 and y>=0 and cw>=w and ch>=h and x+cw<=sw and y+ch<=sh,
                'Crop would be out of bounds or require upscale')
    else:
        x,y,cw,ch=0,0,sw,sh
    require(abs(cw/ch-w/h)<=0.01,'No automatic crop: approve crop_rect with the same output aspect ratio')
    require(cw>=w and ch>=h, 'Upscaling to fake detail prohibited')
    style=plan.get('style','natural'); require(style in STYLES, 'Unknown style preset')
    hue=finite_num(plan.get('global_hue_degrees',0),'global_hue_degrees',-180,180)
    if abs(hue)>5:
        require(plan.get('global_hue_affects_entire_frame_acknowledged') is True,
                'Hue shift changes everything, including hands and reflections; no isolated-object recolor')
    require(not plan.get('claim_subject_only_recolor'),
            'Object-only recolor needs an actual human-reviewed tracked mask, not a global hue filter')
    return {'source':path,'source_probe':v,'source_fps':float(fps),'source_length':original_duration,
            'start':start,'duration':duration,'speed':speed,'target':(w,h),'crop':(x,y,cw,ch),
            'style':style,'hue':hue}

def transform(manifest, output):
    manifest=Path(manifest).resolve(); directory=manifest.parent
    plan=json.loads(manifest.read_text(encoding='utf-8'))
    pre=validate(plan,directory)
    output=Path(output).resolve()
    require(output!=pre['source'] and output!=manifest,'Never overwrite original licensed video or manifest')
    require(output.suffix.lower()=='.mp4','Visual-only shot must be MP4')
    w,h=pre['target']; x,y,cw,ch=pre['crop']
    con,sat,bri,gam=STYLES[pre['style']]
    filters=[f'crop={cw}:{ch}:{x}:{y}', f'setpts=(PTS-STARTPTS)/{pre["speed"]:.8f}',
             'fps=24',f'scale={w}:{h}:flags=lanczos',
             f'eq=contrast={con}:saturation={sat}:brightness={bri}:gamma={gam}']
    if pre['hue']:
        filters.append(f'hue=h={pre["hue"]:.3f}')
    filters.append('format=yuv420p')
    output.parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
         '-ss',str(pre['start']),'-t',str(pre['duration']),'-i',str(pre['source']),
         '-map','0:v:0','-an','-vf',','.join(filters),
         '-c:v','libx264','-preset','slow','-crf','16','-r','24','-pix_fmt','yuv420p',
         '-movflags','+faststart',str(output)]
    subprocess.run(cmd,check=True,timeout=1800)
    actual=probe(output); v=get_video(actual)
    require(int(v['width'])==w and int(v['height'])==h,'Wrong output composition')
    require(Fraction(v['avg_frame_rate'])==Fraction(24,1),'Output no longer 24 fps')
    require(not any(a.get('codec_type')=='audio' for a in actual['streams']),
            'Cannot release before original/recorded Foley is conformally hand-aligned to retimed picture')
    new_duration=float(actual['format']['duration'])
    expected=pre['duration']/pre['speed']
    require(abs(new_duration-expected)<.12,'Unexpected output duration, reject edit')
    report={
        'status':'PICTURE_ONLY_NOT_ASMR_RELEASE_APPROVED',
        'source_file':plan['source_file'],'source_sha256':plan['source_sha256'],
        'source_page':plan['source_page'],'license':plan['license'],
        'editor_selected_range':[pre['start'],pre['start']+pre['duration']],
        'source_frame_rate':pre['source_fps'],'playback_speed':pre['speed'],
        'duration_original_selected_seconds':pre['duration'],
        'duration_new_seconds':new_duration,
        'source_crop_xywh':[x,y,cw,ch],'output_size':[w,h],
        'grade_style':pre['style'],'global_hue_degrees':pre['hue'],
        'visual_output_file':str(output),'visual_output_sha256':sha256(output),
        'source_material_unique_new_duration_seconds':0,
        'approvals':{'new_physical_action_created':False,'audio_remapped':False,
                     'foley_frame_alignment_approved':False,'full_picture_sound_reviewed':False,
                     'premium_quality_approved':False,'publish_approved':False},
        'sound_design_note':'All original tactile audio events must be manually re-timed and independently auditioned to the exact new output frames. No unrelated music/noise, loop filler, or >=0.45s silent passage in finished master.',
    }
    (output.with_suffix('.review.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        result=transform(a.manifest,a.output)
        print(json.dumps(result,indent=2))
    except (ShotBlocked,ValueError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
        p.exit(2, 'RESTYLE_SOURCE_OR_QUALITY_BLOCKED: '+str(e)+'\n')

if __name__=='__main__':
    main()
