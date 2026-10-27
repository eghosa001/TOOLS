#!/usr/bin/env python3
"""Make a source-linked 90-paragraph, up-to-180-shot editorial manifest.
The visual choices are individually written by the editor below. This is not a
semantic image picker. Some assets remain unacquired and must fail release.
"""
from __future__ import annotations
import json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent
SRC=BASE/'EP01_Longform_Research_Script_DRAFT.md'
OUT=BASE/'EP01_Longform_90_Paragraph_Visual_Manifest.json'

# Each tuple is (primary picture, next picture). Where unavailable, asset stays PENDING.
PAIRINGS=[
 [ ('archive:panorama','archive:rail'),('graphic:rupture','graphic:volume'),('graphic:victims','archive:loc'),('archive:tracks','graphic:evidence'),('graphic:outro','illustration:intro'),('archive:tank','graphic:warning') ],
 [ ('illustration:intro','graphic:site'),('graphic:site','graphic:railway'),('graphic:risk','archive:rail'),('archive:tank','archive:ber_023'),('archive:tank','graphic:warning'),('graphic:molasses','graphic:shipment') ],
 [ ('graphic:molasses','graphic:process'),('graphic:date','graphic:process'),('graphic:shipment','graphic:shipment'),('graphic:volume','graphic:pressure'),('graphic:steel','graphic:rivets'),('graphic:risk','graphic:warning') ],
 [ ('archive:tank','graphic:dimensions'),('graphic:pressure','graphic:steel'),('graphic:rivets','archive:ber_031'),('graphic:steel','graphic:inspection'),('graphic:crack','graphic:rivets'),('graphic:evidence','archive:tank') ],
 [ ('archive:tank','graphic:leak'),('graphic:paint','graphic:leak'),('graphic:steel','graphic:warning'),('graphic:leak','graphic:inspection'),('archive:tank','graphic:warning'),('graphic:evidence','graphic:legal') ],
 [ ('graphic:date','graphic:shipment'),('graphic:shipment','graphic:weather'),('graphic:pressure','graphic:crack'),('archive:tank','graphic:leak'),('illustration:intro','graphic:site'),('graphic:rupture','archive:panorama') ],
 [ ('graphic:date','graphic:rupture'),('graphic:volume','graphic:wave'),('archive:rail','archive:ber_035'),('archive:tracks','graphic:railway'),('graphic:rescue','archive:ber_023'),('archive:panorama','graphic:victims') ],
 [ ('graphic:victims','archive:loc'),('graphic:names','graphic:firehouse'),('graphic:evidence','graphic:victims'),('graphic:headlines','archive:loc'),('graphic:rescue','archive:ber_051'),('archive:panorama','graphic:victims') ],
 [ ('graphic:teams','archive:ber_023'),('archive:loc','graphic:rescue'),('graphic:rescue','archive:ber_035'),('archive:tracks','graphic:teams'),('graphic:weather','graphic:molasses'),('archive:ber_052','graphic:cleanup'),('archive:panorama','graphic:victims') ],
 [ ('graphic:cleanup','archive:ber_054'),('archive:tracks','graphic:cleanup'),('graphic:saltwater','graphic:teams'),('archive:ber_051','archive:ber_052'),('archive:panorama','graphic:evidence'),('graphic:legal','archive:ber_035') ],
 [ ('graphic:sabotage','graphic:evidence'),('archive:tank','graphic:rivets'),('graphic:judgment','graphic:legal'),('graphic:evidence','graphic:steel'),('graphic:warning','graphic:crack'),('graphic:legal','graphic:evidence') ],
 [ ('graphic:victims','graphic:legal'),('graphic:legal','graphic:evidence'),('graphic:judgment','graphic:timeline'),('graphic:names','graphic:victims'),('graphic:inspection','graphic:steel'),('archive:tank','graphic:warning'),('graphic:legal','archive:panorama') ],
 [ ('archive:tracks','graphic:steel'),('graphic:pressure','graphic:dimensions'),('graphic:steel','graphic:rivets'),('graphic:crack','graphic:steel'),('graphic:wave','graphic:speed'),('graphic:weather','graphic:molasses'),('graphic:pressure','graphic:wave'),('graphic:timeline','graphic:evidence') ],
 [ ('graphic:timeline','archive:panorama'),('graphic:inspection','graphic:warning'),('graphic:legal','graphic:inspection'),('graphic:headlines','archive:loc'),('graphic:victims','graphic:names'),('archive:rail','archive:tracks'),('graphic:outro',None),('graphic:outro',None) ],
]
EXTRA={
 'ber_023':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-023.jpg',
 'ber_031':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-031.jpg',
 'ber_035':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-035.jpg',
 'ber_051':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-051.jpg',
 'ber_052':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-052.jpg',
 'ber_054':'Boston Elevated Railway after the Molasses Flood, January 1919, from the City of Boston Archives - 9800-018-054.jpg',
}
text=SRC.read_text(encoding='utf-8')
parts=re.split(r'\n## Chapter \d+ — ',text)[1:]
assert len(parts)==len(PAIRINGS)==14
manifest=[]
for c,(raw,pairs) in enumerate(zip(parts,PAIRINGS),1):
    raw=raw.split('\n---')[0]
    title,*paras=raw.split('\n\n')
    paras=[p.strip() for p in paras if p.strip()]
    assert len(paras)==len(pairs),(c,len(paras),len(pairs))
    for p,(paragraph,(visual_a,visual_b)) in enumerate(zip(paras,pairs),1):
        sentences=re.split(r'(?<=[.!?])\s+',paragraph)
        if visual_b and len(sentences)>1:
            cut=max(1,min(len(sentences)-1,int(len(sentences)*.5)))
            sections=[' '.join(sentences[:cut]),' '.join(sentences[cut:])]
        else:
            visual_b=None;sections=[paragraph]
        tracks=[{'visual':vis,'narration':line,'status':('needs_verified_original' if vis.startswith('archive:ber_') else 'reuse_existing_checked_asset_or_graphic')}
            for vis,line in zip((visual_a,visual_b),sections) if vis]
        assert all(t['narration'].strip() for t in tracks)
        manifest.append({'chapter':c,'chapter_title':title,'paragraph':p,'id':f'{c:02d}-{p:02d}',
           'narration_word_count':len(paragraph.split()),'editorial_scenes':tracks,
           'historical_relevance':'needs individual final review before acquisition and cut approval'})
assert len(manifest)==90
assert sum(len(x['editorial_scenes']) for x in manifest)>=175
OUT.write_text(json.dumps({'version':'longform-research-draft','release_approved':False,
  'note':'Human-authored visual pairings; exact narration WAVs to be produced separately per shot. No automatic media fallback.',
  'additional_archive_originals':EXTRA,'paragraphs':manifest},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PARAGRAPHS',len(manifest),'INDIVIDUAL_PICTURE_VOICES',sum(len(x['editorial_scenes']) for x in manifest),
      'TOTAL_WORDS',sum(x['narration_word_count'] for x in manifest),'JSON_BYTES',OUT.stat().st_size)