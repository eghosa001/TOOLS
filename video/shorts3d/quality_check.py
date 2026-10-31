#!/usr/bin/env python3
"""Technical MP4 checks, followed by a strict explicit human publication gate."""
import argparse,json,subprocess
from pathlib import Path
from shotlist import load_and_validate
def inspect(mp4,spec,release=False):
    if not mp4.is_file():return ['Missing MP4']
    errors=[]
    try:
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)],text=True))
        tracks=data['streams']
        v=next((s for s in tracks if s.get('codec_type')=='video'),None)
        a=next((s for s in tracks if s.get('codec_type')=='audio'),None)
        if v is None:errors.append('No video')
        else:
            w=v.get('width',0);h=v.get('height',0)
            if w*16!=h*9:errors.append('Not 9:16')
            if release and (w<1080 or h<1920):errors.append('Below 1080x1920')
            rate=v.get('avg_frame_rate','0/1').split('/')
            if len(rate)!=2 or int(rate[1])==0 or abs(int(rate[0])/int(rate[1])-spec['fps'])>.1:errors.append('Wrong frame rate')
        if a is None:errors.append('No audio')
        elif a.get('channels')!=2:errors.append('Expected stereo')
        length=float(data['format']['duration'])
        if abs(length-spec['seconds'])>.4:errors.append('Wrong duration')
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as e:errors.append('Unverified MP4: '+str(e))
    return errors
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('short',type=Path);p.add_argument('mp4',type=Path);p.add_argument('--release',action='store_true');a=p.parse_args()
    spec=load_and_validate(a.short,a.release);issues=inspect(a.mp4,spec,a.release)
    if issues:
        print('BLOCKED:',*issues,sep='\n');raise SystemExit(1)
    print('TECHNICAL_PASS__FULL_EDITOR_REVIEW_REQUIRED')
