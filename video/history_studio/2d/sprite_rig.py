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


@lru_cache(maxsize=512)
def _prepared_cutout(rig_file, node_id, scale_milli, angle_quant, mouth_bucket):
    """One quantized sprite pose reused over many shots/frames.

    A 3-degree transform grid is sufficient for 12fps illustrated movement,
    and saves repeated heavyweight Pillow image rotations each loop.
    """
    cfg=_load(rig_file)
    node=next(n for n in cfg['nodes'] if n['id']==node_id)
    scale=scale_milli/1000.0
    sprite=node['image']
    if node_id=='mouth':
        multiplier=.65+mouth_bucket/5.0*1.6
        sprite=sprite.resize((sprite.width,max(2,int(sprite.height*multiplier))),Image.Resampling.BICUBIC)
    scaled=sprite.resize((max(1,int(sprite.width*scale)),max(1,int(sprite.height*scale))),Image.Resampling.BICUBIC)
    px,py=[v*scale for v in node['pivot']]
    # Center exact rotation pivot inside the smallest enclosing square.
    xs=[-px,scaled.width-px];ys=[-py,scaled.height-py]
    r=math.ceil(max(math.hypot(a,b) for a in xs for b in ys))+2
    padded=Image.new('RGBA',(2*r,2*r))
    padded.paste(scaled,(round(r-px),round(r-py)),scaled)
    rotated=padded.rotate(-angle_quant,resample=Image.Resampling.BICUBIC)
    bounds=rotated.getbbox()
    if not bounds:return None
    return rotated.crop(bounds),(-r+bounds[0],-r+bounds[1])

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
    # Sprite frames transform at quantized angles, making 10–15 minute
    # multi-scene productions far cheaper than regenerating every pose.
    scale_milli=round(scale*1000)
    for node in ordered:
        if node.get('hidden') or (node['id']=='mouth' and not speaking):continue
        joint,angle=transforms[node['id']]
        bucket=round(min(1,max(0,amplitude))*5) if node['id']=='mouth' else 0
        pose=_prepared_cutout(str(Path(rig_file).resolve()),node['id'],scale_milli,
                              round(math.degrees(angle)/3)*3,bucket)
        if pose:
            piece,(dx,dy)=pose
            img.paste(piece,(round(joint[0]+dx),round(joint[1]+dy)),piece)
    return transforms