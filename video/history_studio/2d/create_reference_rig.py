#!/usr/bin/env python3
"""Generate ORIGINAL sample multi-layer artwork; replace for broadcast quality.

No third-party illustrations copied, no generated authenticity claims.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json


def part(out,name,w,h,draw_fn):
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    draw_fn(d); im.save(out/(name+'.png'))


def create(out,style='scholar'):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    palette={'scholar':('#3c5b71','#c29d69','#b58260','#202532'),
             'messenger':('#774c48','#d5b479','#986343','#211d24')}.get(style)
    if not palette:raise ValueError('unknown original sample cast')
    tunic,gold,skin,dark=palette
    part(out,'torso',150,154,lambda d:(d.rounded_rectangle((9,1,142,147),22,fill=dark),d.rounded_rectangle((14,5,137,140),18,fill=tunic),d.polygon([(15,75),(136,75),(135,95),(18,95)],fill=gold),d.line((75,15,75,140),fill=gold,width=4)))
    part(out,'head',126,140,lambda d:(d.ellipse((14,7,113,121),fill=dark),d.ellipse((18,9,109,115),fill=skin),d.pieslice((17,3,110,82),180,360,fill=dark),d.ellipse((43,72,49,78),fill=dark),d.ellipse((78,72,84,78),fill=dark),d.arc((51,82,75,103),0,170,fill=dark,width=3)))
    for side in ('left','right'):
        part(out,'arm_'+side,50,104,lambda d:(d.rounded_rectangle((4,1,47,89),18,fill=dark),d.rounded_rectangle((8,4,43,78),14,fill=tunic),d.ellipse((9,79,42,100),fill=skin)))
        part(out,'forearm_'+side,46,100,lambda d:(d.rounded_rectangle((4,1,42,93),16,fill=dark),d.rounded_rectangle((9,5,39,80),11,fill=tunic),d.ellipse((9,72,40,99),fill=skin)))
        part(out,'thigh_'+side,65,110,lambda d:(d.rounded_rectangle((5,2,59,104),18,fill=dark),d.rounded_rectangle((11,2,54,100),14,fill=tunic)))
        part(out,'shin_'+side,59,109,lambda d:(d.rounded_rectangle((4,1,55,106),16,fill=dark),d.rounded_rectangle((10,2,49,95),14,fill=(85,75,67))))
    part(out,'mouth',33,13,lambda d:d.ellipse((2,2,30,11),fill=(47,28,36)))
    parts=[
        ('thigh_left','root',(-25,-126),(32,4),0),('shin_left','thigh_left',(0,83),(29,3),1),
        ('thigh_right','root',(25,-126),(32,4),2),('shin_right','thigh_right',(0,83),(29,3),3),
        ('arm_left','torso',(-63,14),(23,2),4),('forearm_left','arm_left',(0,74),(23,2),5),
        ('torso','root',(0,-137),(75,135),6),('arm_right','torso',(63,14),(23,2),7),
        ('forearm_right','arm_right',(0,74),(23,2),8),('head','torso',(0,-111),(63,118),9),
        ('mouth','head',(0,-25),(16,6),10),
    ]
    cfg={'format':'historical_layered_rig_v1','name':style+' (original PROTOTYPE NOT PERIOD VERIFIED)','design_height':395,
         'nodes':[{'id':name,'parent':parent,'offset':offs,'pivot':pivot,'z':z,'png':name+'.png'} for name,parent,offs,pivot,z in parts]}
    (out/'rig.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf8')
    print('ORIGINAL_LAYERED_SAMPLE_RIG',out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--style',choices=('scholar','messenger'),default='scholar');a=p.parse_args();create(a.output,a.style)
