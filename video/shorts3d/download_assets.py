#!/usr/bin/env python3
"""Fetch precisely selected CC0 Kenney GLBs with local caching and rights provenance."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.request import urlopen,Request
ROOT=Path(__file__).resolve().parent
BASE='https://raw.githubusercontent.com/Hidencod/tge-assets/main/packs'
def asset_url(row):
    pack,name=row['pack'],row['file']
    if not re.fullmatch(r'[a-z0-9-]+',pack) or not re.fullmatch(r'[a-z0-9-]+\.glb',name):
        raise ValueError('Unsafe source path')
    return f'{BASE}/{pack}/{name}'
def chosen_ids(catalog,ids):
    if not ids:raise ValueError('Choose assets explicitly by --ids or --all')
    for id in ids:
        if id not in catalog['assets']:raise ValueError('Unknown selected asset: '+id)
    return list(dict.fromkeys(ids))
def fetch(ids,dest,catalog,dry_run=False):
    dest.mkdir(parents=True,exist_ok=True)
    records=[]
    for id in chosen_ids(catalog,ids):
        row=catalog['assets'][id];url=asset_url(row);path=dest/(id+'.glb')
        if dry_run:
            records.append({'id':id,'url':url,'cached_path':str(path)});continue
        if path.exists():data=path.read_bytes()
        else:
            with urlopen(Request(url,headers={'User-Agent':'TOOLS-Shorts3D-CC0/1.0'}),timeout=40) as stream:
                data=stream.read(4_000_001)
            if len(data)>4_000_000:raise ValueError('Too-large unreviewed asset: '+id)
            if len(data)<20 or data[:4]!=b'glTF':raise ValueError('Invalid GLB: '+id)
            path.write_bytes(data)
        if len(data)<20 or data[:4]!=b'glTF' or int.from_bytes(data[8:12],'little')!=len(data):
            raise ValueError('Invalid/corrupt cached GLB: '+id)
        records.append({'id':id,'path':path.name,'source_url':url,'original_creator':'Kenney','mirror':'Hidencod/tge-assets',
            'license':'CC0-1.0','license_url':catalog['license_url'],
            'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),'editor_approved':False})
    if not dry_run:
        (dest/'provenance.json').write_text(json.dumps({'assets':records},indent=2)+'\n')
    return records
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ids',nargs='*',default=[]);p.add_argument('--all',action='store_true');p.add_argument('--dry-run',action='store_true')
    p.add_argument('--dest',type=Path,default=ROOT/'godot/assets')
    a=p.parse_args();cat=json.loads((ROOT/'assets.json').read_text())
    print(json.dumps(fetch(list(cat['assets']) if a.all else a.ids,a.dest,cat,a.dry_run),indent=2))
