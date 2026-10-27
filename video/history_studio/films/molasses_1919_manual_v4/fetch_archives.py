#!/usr/bin/env python3
"""Acquire only the five explicitly approved archival sources.
No replacements. Abort if any image is missing or corrupt.
"""
from pathlib import Path
import hashlib,json,time,urllib.parse,urllib.request
from PIL import Image

ROOT=Path(__file__).resolve().parent
from manual_editor import ASSETS
OUT=ROOT/'archives'
OUT.mkdir(exist_ok=True)
INDEX={}
for key,meta in ASSETS.items():
    filename=meta['filename']
    display=filename.replace(' ','_')
    hash_=hashlib.md5(display.encode('utf-8')).hexdigest()
    url='https://upload.wikimedia.org/wikipedia/commons/'+hash_[0]+'/'+hash_[:2]+'/'+urllib.parse.quote(display,safe='')
    target=OUT/filename
    if not target.exists():
        err=None
        for retry in range(3):
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'FactsUncoveredArchiveResearch/1.0 (history documentary editorial acquisition)'})
                with urllib.request.urlopen(req,timeout=120) as remote, target.open('wb') as dest:
                    while True:
                        chunk=remote.read(1_048_576)
                        if not chunk:break
                        dest.write(chunk)
                if not 5000<target.stat().st_size<25_000_000:
                    raise ValueError('Image size outside expected bounds')
                break
            except Exception as e:
                err=e
                target.unlink(missing_ok=True)
                time.sleep(retry+2)
        if not target.exists():
            raise RuntimeError('REQUIRED ARCHIVE MISSING '+key+' '+meta['source']) from err
    with Image.open(target) as image:
        image.verify()
    with Image.open(target) as image:
        dimensions=list(image.size)
        if min(dimensions)<300:raise RuntimeError('Archive below min resolution: '+key)
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    INDEX[key]={'file':filename,'source_record':meta['source'],'rights':meta['status'],
                'download_url':url,'sha256':sha,'pixel_dimensions':dimensions,
                'used_as':'historic archival photograph, never reenactment'}
    print('APPROVED_ASSET_PRESENT',key,dimensions,sha[:16],flush=True)
    time.sleep(0.5)
(OUT/'RIGHTS_AND_CHECKSUMS.json').write_text(json.dumps(INDEX,indent=2)+'\n')
assert len(INDEX)==len(ASSETS)==5
print('EXACT_SOURCE_ACQUISITION_COMPLETE',len(INDEX))
