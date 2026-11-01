#!/usr/bin/env python3
"""Reuse the project's existing Blender shell-break scene to render REAL per-fruit 3D geometry.
Licensed original footage is not touched. Requires Blender and the sibling crunchy_mango renderer.
"""
from __future__ import annotations
import os
from pathlib import Path

FRUIT = os.environ.get('ASMR_FRUIT_VARIANT', 'strawberry').strip().lower()
PALETTES = {
 'strawberry': {'base': (.72,.022,.062), 'dark': (.42,.008,.026), 'mid': (.75,.04,.07), 'light': (.98,.19,.17), 'core': (.94,.12,.23), 'exposure': -.50},
 'citrus': {'base': (.91,.33,.015), 'dark': (.67,.12,.012), 'mid': (.98,.40,.020), 'light': (1,.72,.08), 'core': (.98,.56,.08), 'exposure': -.48},
 'fig': {'base': (.29,.025,.28), 'dark': (.10,.005,.16), 'mid': (.34,.032,.35), 'light': (.67,.13,.51), 'core': (.91,.20,.43), 'exposure': -.35},
 'dragonfruit': {'base': (.86,.026,.32), 'dark': (.49,.005,.16), 'mid': (.86,.042,.34), 'light': (1,.23,.63), 'core': (.93,.84,.88), 'exposure': -.42},
}
if FRUIT not in PALETTES:
 raise SystemExit('Unknown fruit variant '+FRUIT)
original = Path(__file__).resolve().parents[1] / 'crunchy_mango' / 'render_scene.py'
if 'MULTIFRUIT_BASE_SCRIPT' in os.environ:
 original = Path(os.environ['MULTIFRUIT_BASE_SCRIPT'])
s=original.read_text(encoding='utf-8')

def replace_once(before, after):
 global s
 assert before in s, 'Studio renderer changed; missing exact anchor '+repr(before[:130])
 s=s.replace(before, after, 1)

replace_once('rng=random.Random(20261031)', '''FRUIT = os.environ.get('ASMR_FRUIT_VARIANT','strawberry').lower()
PAL = '''+repr(PALETTES)+'''[FRUIT]
rng=random.Random(20261101+sum((i+1)*ord(x) for i,x in enumerate(FRUIT)))''')
replace_once('scene.view_settings.exposure=-.75', "scene.view_settings.exposure=PAL['exposure']")
replace_once("shell=mat('SUGAR_GLASS | polished ruby-gold lacquer',(.78,.10,.024),.085,.12,.85)", "shell=mat('SUGAR_GLASS | '+FRUIT+' candy glaze',PAL['base'],.085,.12,.85)")
replace_once('ramp.color_ramp.elements[0].color=(.52,.018,.030,1)', "ramp.color_ramp.elements[0].color=(*PAL['dark'],1)")
replace_once('ramp.color_ramp.elements[1].color=(.96,.34,.016,1)', "ramp.color_ramp.elements[1].color=(*PAL['light'],1)")
replace_once('ramp.color_ramp.elements.new(.51).color=(.84,.08,.018,1)', "ramp.color_ramp.elements.new(.51).color=(*PAL['mid'],1)")
replace_once("core=mat('JUICY_FIBROUS_INNER | deep apricot gel',(.97,.28,.023),.17,0,.66,.23,.07)", "core=mat('JUICY_FIBROUS_INNER | '+FRUIT+' gel',PAL['core'],.17,0,.66,.23,.07)")
start=s.index('def surf(theta,phi,inner=1):')
end=s.index('# continuous intact skin;',start)
s=s[:start]+'''def surf(theta,phi,inner=1):
 # DIFFERENT true 3D silhouettes, not identical CGI/color-shifted video frames.
 q=cos(theta);sn=sin(theta)
 if FRUIT=='strawberry':
  rf=1+.31*q+.040*cos(3*phi)*sn
  xx=.94*rf*sn*cos(phi)-.06*q
  yy=.83*rf*sn*sin(phi)
  zz=CZ+.99*q+.015*sin(5*theta)
 elif FRUIT=='citrus':
  rf=1+.025*cos(8*phi)*sn+.018*cos(6*theta)
  xx=.98*rf*sn*cos(phi); yy=.91*rf*sn*sin(phi)
  zz=CZ+.91*q
 elif FRUIT=='fig':
  rf=1-.30*q+.04*cos(3*phi+.8)*sn
  xx=.89*rf*sn*cos(phi)+.06*q
  yy=.83*rf*sn*sin(phi)
  zz=CZ+1.05*q+.045*sn*cos(phi)
 elif FRUIT=='dragonfruit':
  rf=1-.08*q+.065*cos(5*phi+.2)*sn
  xx=.89*rf*sn*cos(phi)-.07*q
  yy=.84*rf*sn*sin(phi)
  zz=CZ+1.10*q
 else: raise RuntimeError('Unknown fruit')
 return Vector((CX+inner*xx,CY+inner*yy,CZ+(zz-CZ)*inner))
''' + s[end:]
replace_once("sites=[(.035+rng.random()*.93,.060+rng.random()*.88) for _ in range(76)]", "sites=[(.035+rng.random()*.93,.060+rng.random()*.88) for _ in range({'strawberry':74,'citrus':85,'fig':68,'dragonfruit':79}[FRUIT])]")
replace_once("'visuals_from_uploaded_reference':False", "'fruit_variant':FRUIT, 'visuals_from_uploaded_reference':False")
decor='''# Licensed photos and ASMR reference footage NEVER enter this 3D scene.
leaf=mat(FRUIT+' green details',(.055,.25,.08),.23,.01,.10)
seedmat=mat(FRUIT+' golden micro seeds',(.68,.48,.16),.20,.36,.24)
if FRUIT=='strawberry':
 for k in range(62):
  th=.19+rng.random()*2.50;ph=-pi+rng.random()*2*pi
  pos=surf(th,ph)*1.017
  bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=6,radius=1,location=pos)
  dot=bpy.context.object;dot.name='strawberry seed '+str(k);dot.scale=(.015,.010,.027)
  dot.data.materials.append(seedmat)
  normal=(pos-Vector((0,0,CZ))).normalized()
  dot.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
  dot.hide_render=False;dot.keyframe_insert(data_path='hide_render',frame=54)
  dot.hide_render=True;dot.keyframe_insert(data_path='hide_render',frame=55)
 for k in range(6):
  ang=2*pi*k/6
  a=Vector((.0,0,CZ+1.02));b=Vector((.19*cos(ang),.19*sin(ang),CZ+.97))
  c=Vector((.31*cos(ang),.31*sin(ang),CZ+.92))
  ob=mesh_obj('strawberry green crown sepal '+str(k),[tuple(a),tuple(b),tuple(c)],[(0,1,2)],leaf)
  ob.modifiers.new('leaf volume','SOLIDIFY').thickness=.018
elif FRUIT=='dragonfruit':
 for k in range(17):
  th=.27+2.52*(k+.2)/17;ph=-pi+2*pi*((k*.61803398875)%1)
  a=surf(th,ph)*1.01;b=surf(th+.16,ph+.15)*1.02
  tip=surf(th+.24,ph+.30)*1.14
  ob=mesh_obj('dragonfruit green scale '+str(k),[tuple(a),tuple(b),tuple(tip)],[(0,1,2)],leaf)
  ob.modifiers.new('bract thickness','SOLIDIFY').thickness=.015
  ob.hide_render=False;ob.keyframe_insert(data_path='hide_render',frame=54)
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=55)
elif FRUIT in ('fig','citrus'):
 bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.085 if FRUIT=='fig' else .042,
                                 radius2=.023,depth=.17 if FRUIT=='fig' else .09,
                                 location=(.04,0,CZ+({'fig':1.06,'citrus':.92}[FRUIT]+.048)))
 ob=bpy.context.object;ob.name=FRUIT+' natural stem';ob.data.materials.append(leaf)
'''
replace_once('# camera, studio HDRI and 3-point calibrated softboxes',decor+'\n# camera, studio HDRI and 3-point calibrated softboxes')
compiled=compile(s,str(original),'exec')
if '--validate-only' in __import__('sys').argv:
 print('VARIANT_VALID',FRUIT,'chars',len(s))
else:
 namespace={'__name__':'__main__','__file__':str(original)}
 exec(compiled,namespace,namespace)
