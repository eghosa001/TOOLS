#!/usr/bin/env python3
"""Safely submit E101's code-only notebook to the user's private Kaggle account.

This public repo contains NO original character art, Drive ZIP content, credentials,
or generated video. Kaggle GPU is deliberately disabled at upload. If there is no
owner-only source dataset, the notebook records STAGED_NEEDS_PRIVATE_SOURCE and
exits successfully without downloading Blender or consuming GPU quota.
"""
from __future__ import annotations
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NOTEBOOK=Path(__file__).resolve().parent/'ninefold_ep101_cam03b_v11_kaggle.ipynb'
SLUG='ninefold-ep101-cam03b-v11-stage'
TITLE='Ninefold EP101 CAM03B v11 Private Blender Stage'
EXACT_ASSET_DATASET_SLUGS={
    'ninefold-s1-private-art-v11',
    'ninefold-s1-private-kaggle-kit-v11',
    'ninefold-tide-s1-private-art-v11',
}


def command(*args: str, timeout=110)->str:
    p=subprocess.run(['kaggle',*args],capture_output=True,text=True,timeout=timeout)
    if p.returncode:
        # Never print Kaggle output or token/header material to public Actions logs.
        raise RuntimeError('Kaggle '+(' '.join(args[:2]))+' failed with code '+str(p.returncode))
    return p.stdout


def parse_csv(output:str)->list[dict]:
    lines=[x for x in output.splitlines() if x.strip()]
    index=next((n for n,line in enumerate(lines) if line.lower().lstrip().startswith('ref,')),None)
    return list(csv.DictReader(io.StringIO('\n'.join(lines[index:])))) if index is not None else []


def owner_from_kernels(records:list[dict])->str:
    refs=[r.get('ref','') for r in records if r.get('ref','')]
    owner=refs[0].split('/',1)[0] if refs else os.environ.get('KAGGLE_USERNAME','').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{2,80}',owner):
        raise RuntimeError('Cannot derive Kaggle owner securely; configure KAGGLE_USERNAME repository variable')
    if any(ref.split('/',1)[0]!=owner for ref in refs):
        raise RuntimeError('Conflicting Kaggle owner identifiers; refusing private submission')
    return owner


def matching_private_dataset(rows:list[dict],owner:str)->str|None:
    matches=[]
    for row in rows:
        ref=row.get('ref','')
        pieces=ref.split('/')
        if len(pieces)!=2 or pieces[0]!=owner:continue
        if pieces[1].lower() in EXACT_ASSET_DATASET_SLUGS:
            matches.append(ref)
    if len(matches)>1:
        raise RuntimeError('Multiple valid private art datasets; refusing accidental selection')
    return matches[0] if matches else None


def validate_notebook()->int:
    data=json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    code=[c for c in data['cells'] if c['cell_type']=='code']
    assert len(code)>=6, 'E101 notebook must keep all original build stages'
    for i,cell in enumerate(code):
        compile(''.join(cell['source']),f'E101 Kaggle code cell {i}','exec')
    assert 'STAGED_NEEDS_PRIVATE_SOURCE' in ''.join(code[0]['source'])
    assert all('if NINEFOLD_SOURCE_READY:' in ''.join(c['source']) for c in code[1:])
    assert NOTEBOOK.stat().st_size<100_000, 'Public repository cannot embed artwork binaries'
    return len(code)


def main()->int:
    count=validate_notebook()
    if not os.environ.get('KAGGLE_API_TOKEN') and not os.environ.get('KAGGLE_KEY'):
        print(json.dumps({'status':'NOT_UPLOADED','reason':'GitHub Actions KAGGLE_API_TOKEN secret unavailable'}))
        return 2
    notebooks=parse_csv(command('kernels','list','--mine','--csv','--page','1','--page-size','100'))
    owner=owner_from_kernels(notebooks)
    ref=owner+'/'+SLUG
    if any(row.get('ref')==ref for row in notebooks):
        status='EXISTING_PRIVATE_NOTEBOOK_PRESERVED'
        print(json.dumps({'status':status,'kaggle_url':'https://www.kaggle.com/code/'+ref,
            'existing_notebooks_changed':False}))
        return 0
    datasets=parse_csv(command('datasets','list','--mine','--csv','--page-size','100'))
    dataset=matching_private_dataset(datasets,owner)
    with tempfile.TemporaryDirectory(prefix='ninefold_private_v11_') as tmp:
        staging=Path(tmp)
        shutil.copyfile(NOTEBOOK,staging/NOTEBOOK.name)
        meta={
            'id':ref,'title':TITLE,'code_file':NOTEBOOK.name,
            'language':'python','kernel_type':'notebook',
            'is_private':True,
            'enable_gpu':False, # Never consume scarce free GPU quota merely to upload code
            'enable_internet':True, # Only used inside Kaggle after verified source is mounted
            'dataset_sources':[dataset] if dataset else [],
            'competition_sources':[],'kernel_sources':[],'model_sources':[],
        }
        (staging/'kernel-metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        command('kernels','push','-p',str(staging),timeout=300)
    result={'status':'PRIVATE_KAGGLE_NOTEBOOK_UPLOADED',
        'kaggle_url':'https://www.kaggle.com/code/'+ref,
        'original_code_cells_verified':count,
        'private_source_dataset_attached':bool(dataset),
        'stage':'TECHNICAL_BUILD_ELIGIBLE' if dataset else 'STAGED_AWAITING_PRIVATE_ART_DATASET',
        'gpu_enabled':False,'public_git_contains_private_art':False,
        'existing_notebooks_changed':False,
        'note':'Upload is NOT proof of a completed Blender render, character acting or a released cartoon.'}
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as dst:
            dst.write('submitted=true\n')
            dst.write('source_attached='+('true' if dataset else 'false')+'\n')
            dst.write('kaggle_url='+result['kaggle_url']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as dst:
            dst.write('### Ninefold Tide E101 private Kaggle upload\n')
            dst.write('Submitted a PRIVATE code-only notebook; no GPU enabled.\n')
            dst.write('Source dataset already present: '+str(bool(dataset))+'\n')
            dst.write('Kaggle notebook: '+result['kaggle_url']+'\n')
    print(json.dumps(result,indent=2))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,ValueError,AssertionError,OSError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status':'NOT_CONFIRMED','reason':str(exc)[:250]}),file=sys.stderr)
        sys.exit(1)