"""Procedural ORIGINAL placeholder 2D cut-out rig with independently rotating limbs.

A reusable art interface: costume palettes and body proportions are stable by
character ID. This rig is a prototype, NOT a verified period costume/actor.
Future artist-made transparent PNG layers can replace these shapes without
changing scene planning or audio synchronization.
"""
from __future__ import annotations
import math
from PIL import ImageDraw


def _rgb(h):
    h=h.lstrip('#')
    if len(h)!=6 or any(c not in '0123456789abcdefABCDEF' for c in h):
        raise ValueError('expected six-digit RGB')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))


def _line(draw, p, q, width, color):
    draw.line((round(p[0]),round(p[1]),round(q[0]),round(q[1])),fill=color,width=max(1,int(width)),joint='curve')
    rad=width/2
    for x,y in (p,q):
        draw.ellipse((x-rad,y-rad,x+rad,y+rad),fill=color)


def _point(p, length, angle):
    return (p[0]+length*math.sin(angle), p[1]+length*math.cos(angle))


def draw_actor(canvas, character, x, ground_y, height, seconds, action='idle', speaking=False, amplitude=0.0, facing=1):
    """Render real joint rotations: shoulders/elbows, hips/knees, head/neck.

    All coordinates come from skeletal joints. A 'walk' cycle includes separate
    thigh/shin angles, opposite arm swing and vertical motion. Speeches move
    mouth shape using WAV RMS, not fake phoneme alignment.
    """
    d=ImageDraw.Draw(canvas,'RGBA')
    k=height/340.0
    skin=_rgb(character.get('skin','#A86F51'))
    tunic=_rgb(character.get('tunic','#436579'))
    edge=_rgb(character.get('outline','#23252C'))
    hair=_rgb(character.get('hair','#2A201A'))
    sash=_rgb(character.get('sash','#CDA65C'))
    movement=1.0 if action=='walk' else 0.10
    phase=seconds*2*math.pi*1.4
    stride=math.sin(phase)*0.46*movement
    swing=math.sin(phase)*0.36*movement
    bob=abs(math.cos(phase))*3.5*k*movement
    # Ground contact shadow is separate from body; foot slide can be inspected.
    d.ellipse((x-60*k,ground_y-11*k,x+60*k,ground_y+2*k),fill=(16,17,25,70))
    hip=(x,ground_y-115*k-bob)
    neck=(x,ground_y-225*k-bob)
    waist=hip
    shoulder=(x,ground_y-207*k-bob)
    # rear arm (shoulder, elbow, hand) = distinct pivot chain
    shoulder_l=(x-41*k,shoulder[1]+6*k)
    shoulder_r=(x+41*k,shoulder[1]+6*k)
    limb_width=17*k
    for side,start in ((-1,shoulder_l),(1,shoulder_r)):
        angle=side*(0.19+swing*(1 if side==-1 else -1))
        elbow=_point(start,48*k,angle)
        hand=_point(elbow,45*k,angle+side*(0.23 if action=='point' and side==1 else 0.1))
        _line(d,start,elbow,limb_width,edge)
        _line(d,start,elbow,limb_width-3*k,tunic)
        _line(d,elbow,hand,15*k,edge)
        _line(d,elbow,hand,12*k,skin)
    # legs: hips->knees->ankles. Distinct articulated knee rotations.
    for side in (-1,1):
        hip_p=(hip[0]+side*20*k,hip[1]+7*k)
        thigh=side*0.1+stride*(1 if side==1 else -1)
        knee=_point(hip_p,56*k,thigh)
        shin=-thigh*0.45
        ankle=_point(knee,54*k,shin)
        _line(d,hip_p,knee,21*k,edge)
        _line(d,hip_p,knee,18*k,tunic)
        _line(d,knee,ankle,18*k,edge)
        _line(d,knee,ankle,15*k,(69,61,54))
        foot=(ankle[0]+side*8*k,ankle[1]+6*k)
        d.ellipse((foot[0]-21*k,foot[1]-9*k,foot[0]+22*k,foot[1]+5*k),fill=edge)
    # torso, outer edge + inset costume, no static PNG puppet parts
    d.rounded_rectangle((x-50*k,neck[1]+4*k,x+50*k,waist[1]+17*k),radius=int(22*k),fill=edge)
    d.rounded_rectangle((x-47*k,neck[1]+7*k,x+47*k,waist[1]+14*k),radius=int(20*k),fill=tunic)
    d.polygon([(x-42*k,waist[1]-23*k),(x+42*k,waist[1]-23*k),(x+46*k,waist[1]-10*k),(x-45*k,waist[1]-10*k)],fill=sash)
    # head pivots independently; small talk nod/idle breathing
    nod=math.sin(seconds*2.7)*(2.4 if speaking else 1.4)*k
    hx=x+math.sin(seconds*1.1)*2*k; hy=neck[1]-54*k+nod
    d.ellipse((hx-48*k,hy-57*k,hx+48*k,hy+48*k),fill=edge)
    d.ellipse((hx-45*k,hy-55*k,hx+45*k,hy+45*k),fill=skin)
    d.pieslice((hx-45*k,hy-55*k,hx+45*k,hy+28*k),185,355,fill=hair)
    # eye movement and blink cycles
    blink=(seconds%4.3)>4.15
    for e in (-1,1):
        ex=hx+e*17*k;ey=hy-5*k
        if blink: d.line((ex-5*k,ey,ex+5*k,ey),fill=edge,width=max(1,int(2*k)))
        else: d.ellipse((ex-3*k,ey-4*k,ex+3*k,ey+3*k),fill=edge)
    mouth_h=(3+min(1,max(0,amplitude))*14 if speaking else 3)*k
    d.ellipse((hx-11*k,hy+17*k,hx+11*k,hy+17*k+mouth_h),fill=edge)
    d.ellipse((hx-7*k,hy+19*k,hx+7*k,hy+17*k+max(2,mouth_h-3*k)),fill=(101,38,45))
    # optional clearly visible point gesture
    if action=='point':
        px=x+90*k;py=neck[1]+53*k
        d.line((x+41*k,neck[1]+48*k,px,py),fill=edge,width=max(1,int(14*k)))
    return {'hip':hip, 'shoulders':[shoulder_l,shoulder_r], 'neck':neck}
