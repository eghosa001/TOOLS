#!/usr/bin/env python3
"""Fail closed on incomplete film/editorial/licensing evidence.

This gate checks evidence fields and media metadata; people still need to
confirm citations, period accuracy, character continuity and real quality.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ALLOWED={'CC0-1.0','CC-BY-4.0','public-domain-verified','original-owned'}

def assess(spec,episode_path,mp4,require_10_to_15=True):
    errors=[]
    def need(test,msg):
        if not test:errors.append(msg)
    need(spec.get('kind')=='historical_2d_animation','Wrong production system')
    for flag in ('fact_checked','visual_quality_approved','voices_licensed','music_licensed',
                 'character_identity_consistent','no_unlabelled_generated_archive','human_publication_approval'):
        need(spec.get(flag) is True,flag+' is not approved')
    sources=spec.get('sources',[])
    hosts=set()
    for s in sources:
        parsed=urlparse(s.get('url','') if isinstance(s,dict) else '')
        if parsed.scheme=='https' and parsed.hostname and isinstance(s.get('supports'),str):hosts.add(parsed.hostname)
    need(len(hosts)>=2,'Need two cited independent sources')
    for character_id,character in spec.get('characters',{}).items():
        rig=character.get('rig')
        if not rig:
            need(False,f'Character {character_id} uses a demo-only procedural character, not approved art')
            continue
        file=(episode_path.parent/rig).resolve()
        need(file.is_relative_to(episode_path.parent.resolve()) and file.is_file(),f'Character {character_id} rig missing')
        need(character.get('rig_rights') in ALLOWED,f'Character {character_id} rights not verified')
        need(bool(character.get('rig_creator')) and bool(character.get('rig_source_url')),f'Character {character_id} artist provenance missing')
        if file.is_file():
            need(character.get('rig_sha256')==hashlib.sha256(file.read_bytes()).hexdigest(),f'Character {character_id} rig checksum mismatch')
    scenes=spec.get('scenes',[])
    need(bool(scenes),'No illustrated story scenes')
    backgrounds=set()
    for i,s in enumerate(scenes,1):
        need(bool(s.get('narration')),'Scene '+str(i)+' missing original narration')
        need(bool(s.get('source_refs')),'Scene '+str(i)+' missing historical source references')
        need(s.get('approved_background') is True,'Scene '+str(i)+' lacks approved historical scene artwork')
        if 'background' in s:
            path=(episode_path.parent/s['background']).resolve()
            need(path.is_relative_to(episode_path.parent.resolve()) and path.is_file(),f'Scene {i} background file missing')
            if path.is_file():
                backgrounds.add(str(path))
                need(s.get('background_sha256')==hashlib.sha256(path.read_bytes()).hexdigest(),f'Scene {i} asset checksum mismatch')
        else:need(False,'Scene '+str(i)+' uses placeholder background')
        need(s.get('background_rights') in ALLOWED,f'Scene {i} has unclear background commercial rights')
        if s.get('background_rights')=='CC-BY-4.0':need(bool(s.get('attribution')),f'Scene {i} missing CC BY credit')
        need(bool(s.get('asset_source_url')),f'Scene {i} asset provenance missing')
    if len(scenes)>=10: need(len(backgrounds)>=max(5,len(scenes)//5),'Too few unique visual backgrounds; likely repetitive production')
    try:
        if not mp4.is_file():raise FileNotFoundError(mp4)
        pr=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate',
                           '-of','json',str(mp4)],text=True,capture_output=True,check=True)
        data=json.loads(pr.stdout)
        d=float(data['format']['duration'])
        streams=data.get('streams',[])
        vid=next((v for v in streams if v.get('codec_type')=='video'),{})
        audio=next((a for a in streams if a.get('codec_type')=='audio'),{})
        need(bool(audio),'MP4 has no narration/audio stream')
        need(vid.get('width',0)>=1920 and vid.get('height',0)>=1080,'Video below 1080p')
        frame=vid.get('r_frame_rate','0/1')
        num,den=(int(v) for v in frame.split('/'))
        need(den>0 and num/den>=24,'Video needs 24fps delivery')
        if require_10_to_15:need(600<=d<=930,'Final film not in 10–15-minute range')
    except (FileNotFoundError,KeyError,ValueError,subprocess.CalledProcessError) as e:
        errors.append('Unverified final MP4: '+str(e))
    return errors

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('episode',type=Path);p.add_argument('--mp4',type=Path,required=True);p.add_argument('--allow-short-preview',action='store_true');a=p.parse_args()
    doc=json.loads(a.episode.read_text(encoding='utf8'))
    problems=assess(doc,a.episode.resolve(),a.mp4,not a.allow_short_preview)
    if problems:
        for e in problems:print('BLOCKED:',e)
        raise SystemExit(1)
    print('RELEASE_METADATA_READY — human fact-check and film review remains required')
