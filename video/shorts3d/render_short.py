#!/usr/bin/env python3
"""Render the editor's existing 3D timeline; no automatic storyboarding or image selection."""
import argparse,os,shutil,subprocess
from pathlib import Path
from shotlist import load_and_validate
ROOT=Path(__file__).resolve().parent
def commands(spec,project,audio,output,godot='godot',draft=False):
    fps=spec['fps'];avi=output.parent/'godot_unmixed.avi'
    raw=[godot,'--path',str(project),'--write-movie',str(avi),'--fixed-fps',str(fps),'--quit-after',str(round(spec['seconds']*fps))]
    width,height=(720,1280) if draft else (1080,1920)
    final=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(avi),'-i',str(audio),
         '-map','0:v:0','-map','1:a:0','-vf',f'scale={width}:{height}:flags=lanczos',
         '-c:v','libx264','-preset','veryfast' if draft else 'medium',
         '-crf','23' if draft else '18','-pix_fmt','yuv420p','-r',str(fps),
         '-c:a','aac','-b:a','192k','-t',str(spec['seconds']),
         '-movflags','+faststart',str(output)]
    return raw,final
def main():
    p=argparse.ArgumentParser();p.add_argument('short',type=Path)
    p.add_argument('--audio',type=Path,default=ROOT/'build/narration_stereo.wav')
    p.add_argument('--output',type=Path,default=ROOT/'build/draft.mp4')
    p.add_argument('--godot',default='godot');p.add_argument('--draft',action='store_true')
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    spec=load_and_validate(a.short);commands_g,commands_f=commands(spec,ROOT/'godot',a.audio,a.output,a.godot,a.draft)
    if a.dry_run:
        print('Godot:',' '.join(commands_g));print('Mux:',' '.join(commands_f));return
    if not shutil.which(a.godot):raise RuntimeError('Godot 4.7.2 not found')
    if not shutil.which('ffmpeg'):raise RuntimeError('FFmpeg required')
    if not a.audio.is_file():raise FileNotFoundError('Generate and review Qwen narration first')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['SHORTS3D_SHOTLIST']=str(a.short.resolve())
    # Headless only imports and checks; the actual 3D movie needs a GL/display context.
    subprocess.run([a.godot,'--headless','--path',str(ROOT/'godot'),'--editor','--quit'],check=True,env=env)
    subprocess.run(commands_g,check=True,env=env)
    if not (a.output.parent/'godot_unmixed.avi').exists():raise RuntimeError('No Godot render')
    subprocess.run(commands_f,check=True)
    print('DRAFT_NOT_RELEASE_APPROVED',a.output)
if __name__=='__main__':main()
