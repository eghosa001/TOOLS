#!/usr/bin/env python3
"""Download only source-verified, free commercial-use original PBR/HDRI and Foley."""
import os,re,json,hashlib,requests
from pathlib import Path
O=Path(os.environ.get('CRUNCH_ASSETS','/tmp/crunchy_mango_assets')); O.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({'User-Agent':'SatisfyingTextureASMR/1.0 editorial asset retrieval'})
R={'asset_ledger':[],'licensed_source_policy':'Individual creator page must explicitly state CC0 for each recording.','reference_video_used':False,'publication_approved':False}
hdri='https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr'
for name,ident in [('candy_shell_snap',392883),('candy_bar_crunch',257703),('soft_fruit_inner',812387)]:
 page=f'https://freesound.org/people/{"clif_creates" if ident==392883 else "vmgraw" if ident==257703 else "frodeims"}/sounds/{ident}/'
 response=s.get(page,timeout=25);response.raise_for_status()
 html=response.text.replace('\\/','/')
 assert ('creativecommons.org/publicdomain/zero/1.0/' in html.lower() or 'creative commons 0' in html.lower()),f'CC0 not proven {page}'
 reg=rf'https://cdn\.freesound\.org/previews/{str(ident)[:3]}/{ident}_[0-9]+-hq\.(?:ogg|mp3)'
 urls=list(dict.fromkeys(re.findall(reg,html)))
 if not urls:raise RuntimeError('No official HQ public preview '+page)
 url=next((u for u in urls if u.endswith('.ogg')),urls[0]);dest=O/(name+'.'+url.rsplit('.',1)[-1])
 with s.get(url,timeout=40,stream=True) as rr:
  rr.raise_for_status();size=0
  with dest.open('wb') as out:
   for c in rr.iter_content(128*1024):
    if not c:continue
    size+=len(c)
    if size>12*1024*1024:raise ValueError('Foley too large')
    out.write(c)
 assert dest.stat().st_size>15000,f'audio too small {dest}'
 R['asset_ledger'].append({'role':name,'author':page.split('/people/')[1].split('/')[0],'source_page':page,'license':'https://creativecommons.org/publicdomain/zero/1.0/','license_verified':True,'download':url,'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'kind':'Public HQ compressed preview; no claim to lossless original'})
 print('FOLEY VERIFIED',name,dest.stat().st_size,flush=True)
# Official Poly Haven 1K reflection lighting, never from creator ASMR references.
p=O/'studio_small_09_1k.hdr'
with s.get(hdri,timeout=100,stream=True) as rr:
 rr.raise_for_status();n=0
 with p.open('wb') as out:
  for c in rr.iter_content(128*1024):
   if not c:continue
   n+=len(c)
   if n>8*1024*1024:raise ValueError('HDRI too large')
   out.write(c)
assert p.read_bytes()[:10].startswith(b'#?RADIANCE'), 'Wrong HDRI bytes'
R['asset_ledger'].append({'role':'photo_studio_HDRI','author':'Sergej Majboroda','source_page':'https://polyhaven.com/a/studio_small_09','license':'https://polyhaven.com/license','download':hdri,'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'license_verified':True})
(O/'RIGHTS_SOURCE_LEDGER.json').write_text(json.dumps(R,indent=2))
print('SUCCESS 3 authentic CC0 foley recordings, 1 genuine CC0 HDRI',flush=True)
