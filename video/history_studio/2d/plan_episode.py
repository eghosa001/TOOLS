#!/usr/bin/env python3
"""Turn a researched 10–15-minute chapter plan into reusable 2D scene slots.

This generates structure, NOT historical claims or missing artwork. Empty
artwork must be replaced with period-checked originals before distribution.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path


def make_plan(source, min_words_per_scene=35, max_words_per_scene=65):
    if not isinstance(source.get('chapters'),list) or not source['chapters']:
        raise ValueError('Provide chapters with original narration')
    if not 15<=min_words_per_scene<=max_words_per_scene<=90:raise ValueError('Invalid word budget')
    words=sum(len(c.get('narration','').split()) for c in source['chapters'])
    # A broad indicative range, NOT a promise of exact voice duration.
    if words<950 or words>2400:raise ValueError(f'{words} original narration words: target 10–15 min normally requires ~1250–2100; check voice timing')
    if len(source.get('sources',[]))<2:raise ValueError('Require at least two research references')
    if not source.get('characters'):raise ValueError('Reusable character rig catalog required')
    roster=source['characters']
    first_actor=next(iter(roster))
    scenes=[]
    for chap in source['chapters']:
        visual_mode=chap.get('visual_mode', 'character')
        if visual_mode not in ('character','illustrated_broll'):
            raise ValueError('Unknown chapter visual_mode')
        art=chap.get('backgrounds', [])
        if visual_mode=='illustrated_broll' and (not isinstance(art,list) or not art or not all(isinstance(x,str) and x.strip() for x in art)):
            raise ValueError('Illustrated b-roll chapter requires explicit local source artwork paths')
        text=chap.get('narration','').strip()
        if not text:raise ValueError('Empty chapter narration')
        sentences=re.split(r'(?<=[.!?])\s+',text)
        parts=[];batch=[];count=0
        for sentence in sentences:
            if not sentence.strip():continue
            wc=len(sentence.split())
            if batch and count+wc>max_words_per_scene:
                parts.append(' '.join(batch));batch=[];count=0
            batch.append(sentence);count+=wc
        if batch:parts.append(' '.join(batch))
        for j, part in enumerate(parts):
            visual_is_broll = visual_mode=='illustrated_broll'
            scenes.append({'chapter':chap.get('title','Historical chapter'),
                           'narration':part,'speaker':chap.get('speaker','narrator'),
                           'stage':chap.get('stage','archive'),
                           'visual_label':('AI-GENERATED ILLUSTRATION • NOT HISTORICAL RECORD' if chap.get('ai_generated_art') else 'ILLUSTRATED RECONSTRUCTION'),
                           **({'shot_type':'illustrated_broll','background':art[j%len(art)],'camera_move':('left','right','up','down')[j%4]} if visual_is_broll else {}),
                           'actors':([{'id':first_actor,'action':('walk' if j%4==0 else 'idle'), 'x':.5,'scale':.64}] if chap.get('on_screen',True) and not visual_is_broll else []),
                           'visual_brief':f'UNREVIEWED — author historical artwork for {chap.get("title","chapter")} shot {j+1}',
                           'source_refs':chap.get('sources',[]),
                           'approved_background':False})
    return {'kind':'historical_2d_animation','title':source.get('title','Untitled historical study'),
            'era':source.get('era'),'location':source.get('location'),
            'sources':source.get('sources'), 'characters':roster,
            'production_state':'storyboard_not_approved',
            'target_minutes':source.get('target_minutes',12),
            'scenes':scenes,'estimated_words':words}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    src=json.loads(a.source.read_text(encoding='utf8'))
    plan=make_plan(src)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('SCENES_PLANNED',len(plan['scenes']),'ORIGINAL_WORDS',plan['estimated_words'],'NOT_A_RELEASE')