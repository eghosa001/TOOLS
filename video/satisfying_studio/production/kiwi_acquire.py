#!/usr/bin/env python3
"""Fetch Poly Haven Kiwi 01 photogrammetry model, CC0; maintain per-file SHA provenance."""
import os,json,hashlib,requests
from pathlib import Path
D=Path(os.environ.get('ASMR_ASSETS','/tmp/asmr_kiwi_assets'));D.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({'User-Agent':'SatisfyingTextureASMR/1.0 (licensed 3D asset intake)'})
info=s.get('https://api.polyhaven.com/files/food_kiwi_01',timeout=35).json()
print('API_KEYS',list(info),flush=True);print('GLTF_KEYS',list(info.get('gltf',{})),flush=True)
if 'gltf' not in info:raise RuntimeError('No public glTF model listing')
byres=info['gltf'].get('2k') or info['gltf'].get('1k')
print('MODEL_SUBKEYS',list(byres),flush=True)
f=byres.get('gltf') or byres.get('glb')
if not f:raise RuntimeError('glTF not found')
print('ROOT',f.get('url'),list(f),flush=True)
files={Path(f['url'].split('?')[0]).name:f}
for k,item in (f.get('include') or {}).items():
 if isinstance(item,dict):files[k]=item
print('FILES',list(files),flush=True)
rows=[]
for p,meta in files.items():
 if not meta.get('url'):raise RuntimeError('Missing file URL '+p)
 path=D/p;path.parent.mkdir(parents=True,exist_ok=True)
 with s.get(meta['url'],stream=True,timeout=150) as r:
  r.raise_for_status();n=0
  with path.open('wb') as o:
   for ch in r.iter_content(1<<20):
    if not ch:continue
    n+=len(ch)
    if n>45_000_000:raise RuntimeError('individual file too large')
    o.write(ch)
 if meta.get('size') and n!=meta['size']:raise RuntimeError('Size mismatch '+p)
 rows.append({'path':p,'url':meta['url'],'size':n,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
print('ACQUIRED',json.dumps(rows),flush=True)
(D/'SOURCE_LEDGER.json').write_text(json.dumps({'origin':'https://polyhaven.com/a/food_kiwi_01','license':'https://polyhaven.com/license','author':'Oliver Harries','asset_id':'food_kiwi_01','source_api':'https://api.polyhaven.com/files/food_kiwi_01','credit_note':'Powered by Poly Haven','assets':rows},indent=2))
