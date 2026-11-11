#!/usr/bin/env python3
"""Low-cost preliminary QA for real ASMR video against a stage contract.

Heuristic visual segmentation is imperfect; results require human review.
A technical MP4 pass NEVER equals premium physics approval.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
import cv2
import numpy as np
from stage_controller import parse_timeline


def probe_media(path: Path)->dict:
    if not path.is_file():raise FileNotFoundError(str(path))
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate','-show_entries','format=duration,size','-of','json',str(path)],text=True))
    streams=data['streams'];v=next((s for s in streams if s['codec_type']=='video'),None);a=next((s for s in streams if s['codec_type']=='audio'),None)
    if v is None:raise ValueError('Missing video stream')
    return {'duration':float(data['format']['duration']),'bytes':int(data['format']['size']),
            'width':v['width'],'height':v['height'],'video_codec':v['codec_name'],
            'audio_codec':a['codec_name'] if a else None}


def approximate_foam_height(frame: np.ndarray) -> tuple[float,dict]:
    h,w=frame.shape[:2]
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    mask=cv2.inRange(hsv,np.array([78,48,60]),np.array([104,255,255]))
    mask[:int(h*.26)]=0;mask[int(h*.79):]=0
    mask[:,:int(w*.06)]=0;mask[:,int(w*.95):]=0
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    n,labels,stats,cent=cv2.connectedComponentsWithStats(mask)
    components=[(int(stats[i,4]),list(map(int,stats[i,:4]))) for i in range(1,n)]
    if not components: return float('nan'),{'reason':'No turquoise-like object detected'}
    area,(x,y,width,height)=max(components,key=lambda a:a[0]);
    if area<1000:return float('nan'),{'reason':'Foam segmentation area too small'}
    return float(height),{'bbox':[x,y,width,height],'mask_area_px':area,
                           'method':'coarse turquoise connected component; affected by reflections/camera/transparent press'}


def inspect(path:Path, plan:Path)->dict:
    tl=parse_timeline(plan)
    media=probe_media(path)
    capture=cv2.VideoCapture(str(path))
    if not capture.isOpened():raise RuntimeError('OpenCV cannot decode output video')
    bbox=[]
    for t in [0., min(tl.duration_s*.5,media['duration']-.1),min(tl.duration_s,media['duration']-.1)]:
        capture.set(cv2.CAP_PROP_POS_MSEC,max(t,0)*1000)
        ok,f=capture.read()
        if not ok:raise ValueError(f'Cannot read frame at t={t}')
        height,metrics=approximate_foam_height(f)
        bbox.append({'t':t,'height_px':height,**metrics})
    capture.release()
    base,last=bbox[0]['height_px'],bbox[-1]['height_px']
    observed=(base-last)/base if np.isfinite(base) and np.isfinite(last) and base>0 else None
    target=tl.stages[-1].compression
    flags=[]
    if media['audio_codec'] is None:flags.append('FAIL_MISSING_AUDIO_STREAM')
    if abs(media['duration']-tl.duration_s)>.4:flags.append('FAIL_DURATION_OUTSIDE_TOLERANCE')
    if observed is None:flags.append('REVIEW_FOAM_SEGMENTATION_UNAVAILABLE')
    elif observed < target*.5:flags.append('FAIL_LITTLE_MEASURABLE_FOAM_SHRINKAGE')
    else:flags.append('REVIEW_GEOMETRY_PLAUSIBLE_BUT_NOT_PHYSICS_VERIFIED')
    return {'format_id':tl.kind,'media':media,'target_compression_fraction':target,
            'approx_observed_shrink_fraction':observed,'sampled_frame_metrics':bbox,
            'flags':flags,'publish_approved':False,
            'human_review_required':['press remains present','tool-to-object contact','camera pan/zoom','consistent object material','audio events synchronized']}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--video',type=Path,required=True);a.add_argument('--plan',type=Path,required=True);a.add_argument('--output',type=Path,required=True);ns=a.parse_args()
    out=inspect(ns.video,ns.plan)
    ns.output.parent.mkdir(parents=True,exist_ok=True)
    ns.output.write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))