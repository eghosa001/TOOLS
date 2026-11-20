#!/usr/bin/env python3
"""Generate validated Kandinsky 6 NATIVE job specs from approved stage references.

Only the native Kandinsky repository supports first+last and video->audio as
of 2026-10-25. Neither mode is exposed by the working Diffusers script.
NOTE: The native just setup explicitly supports SM 8+ GPUs, NOT T4 (SM 7.5).
This module only prepares commands; does not start GPU jobs or download models.
"""
from __future__ import annotations
import argparse,json,shlex
from pathlib import Path
from PIL import Image
from stage_controller import parse_timeline


def safe_image(path:Path)->dict:
    if not path.is_file():raise FileNotFoundError(str(path))
    with Image.open(path) as im:
        w,h=im.size
        if w<256 or h<456 or w%16 or h%16:
            raise ValueError('Frames must have matching dimensions divisible by 16, >=256x456')
    return {'path':str(path.resolve()),'width':w,'height':h}


def gpu_check(major:int, minor:int=0)->None:
    if major<8:
        raise RuntimeError(f'Kandinsky native pipeline unverified for SM {major}.{minor}; official just setup only supports SM 8+; do not download weights on Kaggle T4')


def command(args:list[str])->str:
    return shlex.join([str(x) for x in args])


def make_jobs(stage_plan:Path, frames:Path, output:Path, native_config:str='kandinsky/configs/devices/asmr-lite-distill.yaml') -> dict:
    tl=parse_timeline(stage_plan)
    stage_paths=[frames/f'{i:02d}_{s.name}.png' for i,s in enumerate(tl.stages)]
    checked=[safe_image(p) for p in stage_paths]
    dims={(p['width'],p['height']) for p in checked}
    if len(dims)!=1:raise ValueError('All approved frame guides must have identical geometry')
    # Approval means manually approved: the CLI cannot approve an aesthetic state.
    scene=f'Same sponge and acrylic press; only physically grounded motion. Fixed camera, exact object identities, no zoom or object morph. {tl.kind}.'
    output.mkdir(parents=True,exist_ok=True)
    segments=[]
    for i,(a,b) in enumerate(zip(tl.stages,tl.stages[1:])):
        mp4=output/f'native_pair_{i:02d}_{a.name}_to_{b.name}_UNAPPROVED.mp4'
        args=['just','generate',scene+' Stage transition: '+a.name+' to '+b.name+'.',
              '--config',native_config,'--image',checked[i]['path'],'--last-image',checked[i+1]['path'],
              '--steps','10','--guidance','1.0','--seed',str(20261031+i),
              '--out',str(mp4)]
        segments.append({'from':a.name,'to':b.name,'duration_seconds_native':5,
                         'approved_source_frame':False,'approved_target_frame':False,
                         'first_image':checked[i],'last_image':checked[i+1],
                         'command':command(args),
                         'visual_midframes_guaranteed':False,'needs_manual_qa':True})
    # Audio-after-video is distinct; the native pipeline preserves input frames.
    v=output/'controlled_stage_guide_NOT_AI.mp4'
    v2a=['just','generate',f'Close miked subtle sponge press and elastic pore sounds, timed to visible compression of {tl.kind}, no music or voices.',
         '--config',native_config,'--video-file',str((frames/v.name).resolve()),
         '--steps','10','--guidance','1.0','--out',str(output/'native_video_to_audio_UNAPPROVED.mp4')]
    spec={'schema_version':1,'tested_gpu_compatibility':'NOT_TESTED','validated_gpu_architectures':'SM 8+ per upstream setup script',
          'kaggle_t4_native_support':False,'model':'lite-distill','diffusers_script_unchanged':True,
          'first_last_segments':segments,'single_pair_preview_command':segments[0]['command'],
          'video_to_audio_command':command(v2a),
          'video_to_audio_preserves_input_frames':True,
          'caution':'Native command is a PLANNED RUN only; reviewed stage frames do not imply physics-consistent AI midframes.',
          'cost_control':'Never run 4 model invocations as a batch. Approve first segment first. Native cannot run on Kaggle T4 with official just setup.'}
    (output/'native_kandinsky_jobs.json').write_text(json.dumps(spec,indent=2))
    return spec

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--frames',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--native-config',default='kandinsky/configs/devices/asmr-lite-distill.yaml');p.add_argument('--gpu-sm',type=int,default=None)
    a=p.parse_args()
    if a.gpu_sm is not None:gpu_check(a.gpu_sm)
    data=make_jobs(a.plan,a.frames,a.out,a.native_config)
    print(json.dumps({'job_file':str((a.out/'native_kandinsky_jobs.json').resolve()),'segment_count':len(data['first_last_segments']),
                      'Kaggle_T4':'native_setup_unsupported','safe':'no_GPU_jobs_submitted'},indent=2))