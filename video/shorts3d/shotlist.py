#!/usr/bin/env python3
"""Fail closed on incorrect or automatically filled editor-authored 3D short timelines."""
import argparse,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def validate(spec,catalog,release=False):
    problems=[]
    def check(ok,msg):
        if not ok: problems.append(msg)
    check(spec.get('format')=='vertical_3d_short','Requires vertical_3d_short')
    w=spec.get('width',0);h=spec.get('height',0)
    check(w in (720,1080) and h*9==w*16,'Requires 9:16 720p or 1080p')
    check(spec.get('fps') in (24,30),'Requires 24/30fps')
    total=spec.get('seconds',0)
    check(isinstance(total,(int,float)) and 5<=total<=180,'Require 5-180 seconds')
    shots=spec.get('shots',[])
    check(isinstance(shots,list) and bool(shots),'Each shot must be authored')
    ids=set(catalog['assets'])
    for i,part in enumerate(spec.get('set',[])):
        check(part.get('asset') in ids,'Unregistered CC0 model at set item '+str(i))
        check(bool(part.get('id')) and len(part.get('position',[]))==3,'Invalid set position/name '+str(i))
    previous=0;seen=set()
    for i,shot in enumerate(shots):
        tag='Shot '+str(i+1)
        try:
            start=float(shot['start']);end=float(shot['end'])
            check(abs(start-previous)<.001,tag+': gap or overlap')
            check(end>start,tag+': nonpositive duration');previous=end
        except (KeyError,TypeError,ValueError):problems.append(tag+': invalid timestamp')
        check(shot.get('id') not in seen,tag+': duplicate shot ID');seen.add(shot.get('id'))
        for field in ('intent','spoken','caption'):
            check(bool(str(shot.get(field,'')).strip()),tag+': missing '+field)
        for field in ('camera_from','camera_to','look_at'):
            coords=shot.get(field,[])
            check(isinstance(coords,list) and len(coords)==3 and all(isinstance(v,(int,float)) for v in coords),tag+': invalid '+field)
    check(abs(previous-total)<.001,'Final shot must end at total seconds')
    voice=spec.get('audio',{})
    check(voice.get('backend')=='qwen3-tts','Qwen audio missing')
    check(voice.get('model') in ('Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice','Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'),'Unvetted voice model')
    check(voice.get('speaker') in ('Ryan','Aiden','Vivian','Serena','Uncle_Fu','Dylan','Eric','Ono_Anna','Sohee'),'Unknown Qwen voice')
    if release:
        for field in ('license_reviewed','human_visual_review','audio_reviewed','human_publication_approval'):
            check(spec.get(field) is True,field+' not approved')
        check(spec.get('production_status')=='approved','Production still unapproved')
    return problems
def load_and_validate(path,release=False):
    spec=json.loads(Path(path).read_text(encoding='utf8'))
    catalog=json.loads((ROOT/'assets.json').read_text(encoding='utf8'))
    errs=validate(spec,catalog,release=release)
    if errs:raise ValueError('\n'.join(errs))
    return spec
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file',type=Path);p.add_argument('--release',action='store_true');a=p.parse_args()
    v=load_and_validate(a.file,a.release)
    print('VALID_AUTHORED_3D_SHORT',len(v['shots']),'shots',v['seconds'],'seconds')
