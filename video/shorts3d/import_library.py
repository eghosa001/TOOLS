#!/usr/bin/env python3
"""Import actual third-party CC0 3D models into Godot without making meshes.

Download once on the cloud runner, validate original GLB bytes, cache them,
record exact provenance, and never synthesize fallback art.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timezone,datetime
import hashlib,json,re,time,sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'godot'/'assets'
KENNEY_PIN='d92c6e923bbef8649d4e5be3ab375a40f88672b0'
HOSTS={'raw.githubusercontent.com','files.innerscene.com'}
MAX_BYTES=28_000_000

def library():
    kenney=json.loads((ROOT/'pack_index.json').read_text())
    extra=json.loads((ROOT/'model_index.json').read_text())
    return kenney,extra

def catalog(kenney,extra):
    data={}
    for row in kenney['assets']:
        key=row['id']
        if key in data:raise ValueError('Duplicate model '+key)
        if not re.fullmatch(r'[a-z0-9_\-]+',key):raise ValueError('Unsafe asset id '+key)
        if row['pack'] not in ('castle-kit','nature-kit','mini-characters','tower-defense-kit','mini-dungeon','blocky-characters'):
            raise ValueError('Unapproved pack')
        if not re.fullmatch(r'[a-z0-9-]+\.glb',row['file']):
            raise ValueError('Unsafe GLB')
        url=f"https://raw.githubusercontent.com/Hidencod/tge-assets/{KENNEY_PIN}/packs/{row['pack']}/{row['file']}"
        data[key]=dict(id=key,url=url,creator='Kenney',license='CC0-1.0',source=kenney['sources'].get(row['pack'].replace('-kit','').replace('-','_'),kenney['source_url']),expected_sha1=row.get('blob_sha'),pack=row['pack'])
    for key,item in extra['models'].items():
        if key in data:raise ValueError('Duplicate external model '+key)
        data[key]=dict(id=key,url=item['download_url'],creator=item['creator'],license='CC0-1.0',source=item['source_url'],pack='external-prebuilt')
    return data

def choices(known,selected=(),packs=(),all_assets=False):
    if all_assets: ids=sorted(known)
    else:ids=list(dict.fromkeys(list(selected)+[id for id,info in known.items() if info['pack'] in packs]))
    if not ids:raise ValueError('Select --ids, --packs, --preset or --all')
    for id in ids:
        if id not in known:raise ValueError('Unknown CC0 model '+id)
    return ids

def safe_url(url):
    u=urlparse(url)
    if u.scheme!='https' or u.hostname not in HOSTS or not u.path.endswith('.glb') or u.username or u.password:
        raise ValueError('Untrusted source URL '+url)
    return url

def verify_glb(data,id):
    if len(data)<20 or data[:4]!=b'glTF':
        raise ValueError(id+': missing glTF binary header')
    if int.from_bytes(data[4:8],'little')!=2 or int.from_bytes(data[8:12],'little')!=len(data):
        raise ValueError(id+': invalid GLB length/version')

def download_one(item,dest):
    id=item['id'];target=dest/(id+'.glb')
    safe_url(item['url'])
    if target.is_file():payload=target.read_bytes()
    else:
        last_error=None
        for attempt in range(3):
            try:
                req=Request(item['url'],headers={'User-Agent':'TOOLS-Godot-3D-Shorts-Free-Assets/1.0'})
                with urlopen(req,timeout=55) as stream:
                    announced=int(stream.headers.get('Content-Length','0') or '0')
                    if announced>MAX_BYTES:raise ValueError('Oversized GLB '+id)
                    payload=stream.read(MAX_BYTES+1)
                if len(payload)>MAX_BYTES:raise ValueError('Oversized asset '+id)
                verify_glb(payload,id)
                tmp=target.with_suffix('.part')
                tmp.write_bytes(payload);tmp.replace(target)
                break
            except Exception as exc:
                last_error=exc
                if attempt==2:raise
                time.sleep(1.2*(attempt+1))
        else:raise RuntimeError(str(last_error))
    verify_glb(payload,id)
    sha=hashlib.sha256(payload).hexdigest()
    return {'asset_id':id,'path':target.name,'bytes':len(payload),'sha256':sha,
        'source_url':item['source'],'exact_download_url':item['url'],'creator':item['creator'],
        'license':item['license'],'rights_checked_on':'2026-10-31','human_visual_review':False}

def import_selected(known,ids,dest,jobs=10,dry_run=False):
    if dry_run:
        return [{'asset_id':id,'source_url':known[id]['source'],'download_url':known[id]['url'],'cache_path':str(dest/(id+'.glb'))} for id in ids]
    dest.mkdir(parents=True,exist_ok=True)
    results=[];failed={}
    with ThreadPoolExecutor(max_workers=max(1,min(jobs,16))) as pool:
        pending={pool.submit(download_one,known[id],dest):id for id in ids}
        for f in as_completed(pending):
            id=pending[f]
            try:results.append(f.result())
            except Exception as exc:failed[id]=str(exc)
    results.sort(key=lambda r:r['asset_id'])
    report={'title':'Imported CC0 3D assets; none generated here','downloaded_or_cached':len(results),
        'requested':len(ids),'bytes':sum(x['bytes'] for x in results),
        'complete':not failed,'failed':failed,'items':results}
    (dest/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    if failed:raise RuntimeError('Import incomplete. No substitutions allowed. '+json.dumps(failed))
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--all',action='store_true',help='Import all 639 Kenney GLB + 6 complete third-party prebuilt models')
    p.add_argument('--ids',nargs='*',default=[])
    p.add_argument('--packs',nargs='*',default=[])
    p.add_argument('--preset',choices=['castle'],default=None)
    p.add_argument('--dest',type=Path,default=DEST)
    p.add_argument('--jobs',type=int,default=10)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    kenney,extras=library();known=catalog(kenney,extras)
    preset=['castle_with_keep','knight','barbarian','nature__ground-grass','nature__grass-large','nature__tree-default','nature__tree-oak','castle__flag'] if a.preset=='castle' else []
    selected=choices(known,a.ids+preset,a.packs,a.all)
    entries=import_selected(known,selected,a.dest,a.jobs,a.dry_run)
    print(json.dumps({'requested':len(selected),'imported_or_cached':len(entries),
        'destination':str(a.dest),'dry_run':a.dry_run,
        'total_mb':round(sum(e.get('bytes',0) for e in entries)/1048576,2)},indent=2))

if __name__=='__main__':main()
