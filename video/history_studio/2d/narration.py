#!/usr/bin/env python3
"""Fast offline Piper narration for every 2D scene, with per-character voices.

No default model is downloaded without the owner reviewing commercial
rights of BOTH the engine distribution and the exact voice weights.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def synthesize(script, voices_config, output):
    src=json.loads(script.read_text(encoding='utf8'))
    voices=json.loads(voices_config.read_text(encoding='utf8')).get('voices',{})
    if not shutil.which('piper'):raise RuntimeError('Install Piper CLI first; not bundled')
    if not voices:raise ValueError('No actual verified voice models configured')
    prepared={}
    for id,record in voices.items():
        model=Path(record['model']).expanduser().resolve()
        meta=Path(str(model)+'.json')
        if not model.is_file() or not meta.is_file():raise FileNotFoundError('Missing Piper .onnx/.onnx.json for '+id)
        if record.get('commercial_use_permitted') is not True:
            raise ValueError('Commercial rights not verified for voice '+id)
        if not record.get('model_card_url') or not str(record['model_card_url']).startswith('https://'):
            raise ValueError('Voice model-card link required for '+id)
        if record.get('sha256')!=sha256(model):raise ValueError('Voice SHA256 mismatch: '+id)
        prepared[id]=model
    output.mkdir(parents=True,exist_ok=True)
    for index,scene in enumerate(src['scenes'],1):
        speaker=scene.get('speaker','narrator')
        voice=prepared.get(speaker,prepared.get('narrator'))
        if voice is None:raise ValueError('No verified narrator/character voice for '+speaker)
        text=scene.get('narration','').strip()
        if len(text)<10:raise ValueError(f'Scene {index}: original narration text required')
        outfile=output/f'line_{index:03}.wav'
        process=subprocess.run(['piper','--model',str(voice),'--output_file',str(outfile)],input=text+'\n',text=True,capture_output=True)
        if process.returncode!=0 or not outfile.is_file() or outfile.stat().st_size<256:
            raise RuntimeError(f'Piper failure scene {index}: {process.stderr[-1500:]}')
        scene['audio']=outfile.name
    # Move/rewrite relative reference paths to assets. Use output inside same
    # episode directory to avoid copying potentially large licensed rigs.
    if output.parent.resolve()!=script.parent.resolve():
        raise ValueError('Output should be a direct subdirectory of episode source folder')
    for character in src['characters'].values():
        if character.get('rig'):character['rig']='../'+character['rig']
    for scene in src['scenes']:
        if scene.get('background'):scene['background']='../'+scene['background']
    # Rig/background parent references are intentionally prevented by renderer.
    # Instead store generated episode next to the original script with audio/
    # paths, so asset path contracts remain rooted in the original episode dir.
    for character in src['characters'].values():
        if character.get('rig'):character['rig']=character['rig'][3:]
    for scene in src['scenes']:
        if scene.get('background'):scene['background']=scene['background'][3:]
        scene['audio']=output.name+'/'+scene['audio']
    dest=script.with_name(script.stem+'.voiced.json')
    dest.write_text(json.dumps(src,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PIPER_TRACKS_SYNTHESIZED',len(src['scenes']),'EDITABLE_MANIFEST',dest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('episode',type=Path);p.add_argument('--voices',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    synthesize(a.episode.resolve(),a.voices.resolve(),a.output.resolve())
