"""Import layered commercial-rights-cleared PNG art as a reusable 2D skeleton.

Each image is an independent cutout attached at its authored joint. The
hierarchy is animated at run time and respects limb parenting, so a knee
rotation moves the entire lower leg without baking image sequences.
"""
from __future__ import annotations
import json
import math
from functools import lru_cache
from pathlib import Path
from PIL import Image


@lru_cache(maxsize=32)
def _load(path):
    path=Path(path).resolve()
    cfg=json.loads(path.read_text(encoding='utf8'))
    if cfg.get('format')!='historical_layered_rig_v1':raise ValueError('Unsupported rig schema')
    nodes=cfg.get('nodes',[])
    if not isinstance(nodes,list) or not 5<=len(nodes)<=30:raise ValueError('Expect 5–30 rig parts')
    ids={node['id'] for node in nodes}
    if len(ids)!=len(nodes):raise ValueError('Duplicate joint names')
    for node in nodes:
        if node.get('parent') not in ('root',*ids):raise ValueError('Unknown joint parent')
        img=path.parent/node['png']
        if not img.resolve().is_relative_to(path.parent) or img.suffix.lower()!='.png':
            raise ValueError('Unsafe layer asset path')
        if not img.is_file():raise FileNotFoundError(img)
        node['image']=Image.open(img).convert('RGBA')
        if node['image'].width>2048 or node['image'].height>2048:raise ValueError('Layer too large')
        if len(node.get('pivot',[]))!=2 or len(node.get('offset',[]))!=2:raise ValueError('Missing rig pivot/offset')
    return cfg


def _angle(node_id, action, seconds, speaking, energy):
    walk=math.sin(seconds*8.0) if action=='walk' else 0
    idle=math.sin(seconds*1.8)
    rules={
        'head':idle*1.9+(1.5*math.sin(seconds*5) if speaking else 0),
        'arm_left':-walk*24+(4*idle if action=='idle' else 0),
        'arm_right':walk*24+(-38 if action=='point' else 0),
        'forearm_left':-7+walk*9,
        'forearm_right':10+(35 if action=='point' else 0)-walk*8,
        'thigh_left':walk*23,
        'thigh_right':-walk*23,
        'shin_left':max(0,-walk)*-20,
        'shin_right':max(0,walk)*-20,
        'torso':idle*.7,
    }
    return math.radians(rules.get(node_id,0))


def draw_layered(img, rig_file, x, ground_y, height, seconds, action='idle', speaking=False, amplitude=0):
    cfg=_load(str(Path(rig_file).resolve()))
    scale=height/float(cfg.get('design_height',390))
    if scale<=0 or scale>6:raise ValueError('Invalid rig size')
    ordered=sorted(cfg['nodes'],key=lambda n:n.get('z',0))
    pending={n['id']:n for n in ordered}
    transforms={'root':((float(x),float(ground_y)),0.)}
    while pending:
        progressed=False
        for name,node in list(pending.items()):
            if node['parent'] not in transforms:continue
            (px,py),parent_angle=transforms[node['parent']]
            ox,oy=[v*scale for v in node['offset']]
            joint=(px+ox*math.cos(parent_angle)-oy*math.sin(parent_angle),
                   py+ox*math.sin(parent_angle)+oy*math.cos(parent_angle))
            angle=parent_angle+_angle(name,action,seconds,speaking,amplitude)
            transforms[name]=(joint,angle)
            del pending[name]
            progressed=True
        if not progressed:raise ValueError('Cycle in character skeleton')
    # All rotations use a correct joint at the image's pivot, not an entire flat image.
    for node in ordered:
        if node.get('hidden'):continue
        if node.get('id')=='mouth' and not speaking:continue
        sprite=node['image']
        pivot=node['pivot']
        if node.get('id')=='mouth':
            # Real sound-driven vertical opening — approximate viseme, not phoneme map
            sprite=sprite.resize((sprite.width,max(2,int(sprite.height*(.65+amplitude*1.6)))),Image.Resampling.BICUBIC)
        scaled=sprite.resize((max(1,int(sprite.width*scale)),max(1,int(sprite.height*scale))),Image.Resampling.BICUBIC)
        p=[v*scale for v in pivot]
        rad=int(math.ceil(math.hypot(scaled.width,scaled.height)+max(abs(p[0]),abs(p[1]))))
        padded=Image.new('RGBA',(2*rad,2*rad))
        padded.paste(scaled,(int(rad-p[0]),int(rad-p[1])),scaled)
        joint,angle=transforms[node['id']]
        rotated=padded.rotate(-math.degrees(angle),resample=Image.Resampling.BICUBIC)
        # pre-cut transparency to reduce composite cost
        bounds=rotated.getbbox()
        if bounds:
            piece=rotated.crop(bounds)
            pos=(int(joint[0]-rad+bounds[0]),int(joint[1]-rad+bounds[1]))
            img.paste(piece,pos,piece)
    return transforms
