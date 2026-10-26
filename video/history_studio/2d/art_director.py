#!/usr/bin/env python3
"""Create ORIGINAL historic-inspired *illustrative* matte scene plates.

These scenes are creative studies, NOT accurate depictions of a known site,
period or event. Commercially reusable original procedural artwork; creators
must replace or verify site-specific details prior to documentary release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

PALETTES={
 'sahel_market':((27,35,51),(202,143,97),(238,188,114),(77,59,55)),
 'ancient_port':((26,54,70),(183,127,103),(244,189,112),(42,58,65)),
 'royal_court':((24,39,58),(126,101,117),(211,155,102),(39,44,58)),
}

def rgba(t,a): return tuple(t)+(a,)
def blend(a,b,t): return tuple(round(a[i]*(1-t)+b[i]*t) for i in range(3))

def draw_plate(style, path, width=1920, height=1080, seed=17):
    if style not in PALETTES:raise ValueError('Unknown illustrative set')
    if (width,height) not in ((960,540),(1280,720),(1920,1080)):
        raise ValueError('Use approved video plate sizes')
    rng=random.Random(seed)
    sky,mid,sun,ink=PALETTES[style]
    im=Image.new('RGB',(width,height))
    px=im.load()
    for y in range(height):
        s=y/height
        color=blend(sky,mid,(s**.74)*.86)
        # High-end matte grade: gradual amber lift rather than flat fill.
        light=max(0,1-abs(s-.54)*2.4)*.12
        color=blend(color,sun,light)
        ImageDraw.Draw(im).line((0,y,width,y),fill=color)
    glow=Image.new('RGBA',im.size)
    gd=ImageDraw.Draw(glow)
    cx=int(width*.72) if style!='royal_court' else int(width*.52)
    cy=int(height*.33)
    for radius in range(int(height*.36),int(height*.085),-18):
        alpha=int(4+16*(1-radius/(height*.36)))
        gd.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=rgba(sun,alpha))
    glow=glow.filter(ImageFilter.GaussianBlur(width*.012))
    im=Image.alpha_composite(im.convert('RGBA'),glow)
    d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((cx-height*.086,cy-height*.086,cx+height*.086,cy+height*.086),fill=rgba(sun,245))
    # Cloud ribbons and distance haze (five staggered painterly layers).
    for n in range(19):
        x=int(rng.uniform(-.12,1.12)*width)
        y=int(rng.uniform(.06,.55)*height)
        w=int(rng.uniform(.035,.16)*width)
        d.ellipse((x,y,x+w,y+height*.015),fill=(255,223,179,rng.randint(7,19)))
    for n in range(5):
        baseline=height*(.63+n*.062)
        pts=[(0,height)]
        for i in range(26):
            x=(i/25)*width
            yy=baseline+math.sin(x/(130+n*15)+n*2.25)*(17+n*7)+math.sin(x/340+n)*12
            pts.append((x,yy))
        pts += [(width,height)]
        c=blend(mid,ink,n*.16)
        d.polygon(pts,fill=rgba(c,215))
    floor=int(height*.78)
    if style=='sahel_market':
        # Stylized Sahel-inspired mud-brick marketplace silhouette, not a specific city.
        for i in range(12):
            x=int(width*(i/11-.04))
            building_w=int(width*rng.uniform(.085,.16))
            bh=int(height*rng.uniform(.20,.40))
            y=floor-bh
            front=blend(mid,(75,51,48),rng.uniform(.2,.6))
            d.polygon([(x,y+14),(x+building_w*.15,y),(x+building_w,y+9),(x+building_w,floor),(x,floor)],fill=rgba(front,250),outline=rgba((80,54,47),160))
            for j in range(2,10):
                xp=x+j*building_w/10
                d.line([(xp,y+8),(xp,floor)],fill=rgba((25,29,35),12),width=3)
            for j in range(3):
                xp=x+building_w*(.18+j*.27)
                d.rectangle((xp,y+bh*.42,xp+building_w*.10,y+bh*.57),fill=(24,30,35,210))
            if i%3==1:
                tower_x=x+building_w*.24
                d.rectangle((tower_x,y-bh*.29,tower_x+building_w*.23,y+bh*.05),fill=rgba(front,240))
                d.polygon([(tower_x-10,y-bh*.29),(tower_x+building_w*.1,y-bh*.43),(tower_x+building_w*.23+10,y-bh*.29)],fill=(69,47,44,235))
                for spike in range(4):
                    xp=tower_x+building_w*.04+spike*building_w*.056
                    d.line((xp,y-bh*.38,xp,y-bh*.46),fill=(40,31,35,240),width=3)
        # Textile shade canopies and stall shapes in the foreground.
        for i in range(6):
            x=width*(.03+i*.19)
            y=height*(.69+rng.random()*.06)
            w=width*.105
            d.polygon([(x,y),(x+w*.5,y-height*.09),(x+w,y)],fill=rgba((136,54,54) if i%2 else (207,151,83),225))
            d.line((x+w*.5,y-height*.09,x+w*.5,floor+height*.09),fill=(61,47,48,210),width=6)
    elif style=='ancient_port':
        # Generic antiquity-inspired harbor, no claim to a specific civilization.
        for i in range(10):
            x=int(width*(i/9-.02))
            h=int(height*rng.uniform(.16,.39))
            roof_y=floor-h
            stone=blend((128,117,101),mid,i*.01)
            d.rectangle((x,roof_y,x+width*.11,floor),fill=rgba(stone,250),outline=(37,52,58,190),width=3)
            d.polygon([(x-12,roof_y),(x+width*.055,roof_y-height*.05),(x+width*.12,roof_y)],fill=(82,67,64,242))
            for j in range(3):
                d.arc((x+j*width*.03,roof_y+h*.3,x+j*width*.03+width*.02,roof_y+h*.7),0,180,fill=(44,52,56,220),width=5)
        d.rectangle((0,floor,width,height),fill=(39,80,92,230))
        for row in range(14):
            y=floor+row*height*.016
            for i in range(11):
                x=(i/10)*width+rng.uniform(-14,14)
                d.line((x,y,x+width*.055,y+1),fill=(229,198,147,rng.randint(50,130)),width=2)
        for bx in (.18,.76):
            x=int(width*bx)
            by=int(height*.81)
            d.polygon([(x-width*.12,by),(x+width*.11,by),(x+width*.077,by+height*.055),(x-width*.088,by+height*.055)],fill=(45,38,40,255))
            d.line((x,by-height*.33,x,by+height*.014),fill=(31,36,43,255),width=6)
            d.polygon([(x,by-height*.32),(x+width*.07,by-height*.14),(x,by-height*.14)],fill=(218,193,156,245))
    else:
        # Stylized palace court view: pillars, stairs and layered silhouette.
        d.rectangle((width*.10,height*.23,width*.9,floor+height*.12),fill=(86,65,67,230))
        d.polygon([(width*.07,height*.23),(width*.5,height*.065),(width*.93,height*.23)],fill=(48,52,64,235))
        d.rectangle((width*.12,height*.28,width*.88,floor),fill=(139,113,105,255))
        for i in range(8):
            x=width*(.15+i*.096)
            d.rectangle((x,height*.28,x+width*.047,floor),fill=(86,68,71,250))
            d.ellipse((x-width*.004,height*.255,x+width*.05,height*.29),fill=(204,168,127,225))
            d.line((x+width*.009,height*.32,x+width*.009,floor),fill=(214,167,124,145),width=5)
        d.rectangle((width*.365,height*.42,width*.635,floor),fill=(37,38,52,255))
        for i in range(5):
            d.polygon([(width*.3-i*width*.024,height*.80+i*height*.025),(width*.7+i*width*.024,height*.80+i*height*.025),(width*.75+i*width*.033,height*.85+i*height*.025),(width*.25-i*width*.033,height*.85+i*height*.025)],fill=(72+i*15,65+i*10,65+i*8,245))
    # Filmic vignette + organic grain/noise. Deterministic for reproducibility.
    overlay=Image.new('RGBA',im.size)
    od=ImageDraw.Draw(overlay)
    for k in range(42):
        left=width*.02*k/42
        od.rectangle((left,0,left+width*.003,height),fill=(19,20,32,int(35*(1-k/42))))
        od.rectangle((width-left-width*.003,0,width-left,height),fill=(19,20,32,int(35*(1-k/42))))
    for i in range(int(width*height*.002)):
        x=rng.randrange(width); y=rng.randrange(height)
        od.point((x,y),fill=(245,217,171,rng.randint(20,90)))
    im=Image.alpha_composite(im,overlay).convert('RGB')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,optimize=True)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'filename':path.name,'sha256':digest,'creator':'TOOLS History Studio procedural illustration','rights':'original-owned','purpose':'illustrative matte; unverified historical design, not archival or site-specific','style':style,'size':[width,height]}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',required=True,type=Path);a.add_argument('--size',choices=('960x540','1280x720','1920x1080'),default='1280x720');args=a.parse_args()
    w,h=map(int,args.size.split('x'))
    args.output.mkdir(parents=True,exist_ok=True)
    entries=[draw_plate(k,args.output/f'{k}.png',w,h) for k in PALETTES]
    (args.output/'manifest.json').write_text(json.dumps({'not_historical_evidence':True,'assets':entries},indent=2)+'\n')
    print('ILLUSTRATIVE_SETS_PREPARED',len(entries),'not archival footage')