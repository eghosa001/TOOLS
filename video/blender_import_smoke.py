"""Headless Blender proof that imported CC0 rigs and Poly Haven shaders load."""
import os
import sys
from pathlib import Path
import bpy

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)!=1:
    raise SystemExit("blender_import_smoke.py expects unpacked CartoonStudio source root")
source=Path(argv[0]).resolve()
sys.path.insert(0,str(source))
from cartoon_studio.studio_world import make_character,build_sunpatch_court

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for i,(name,color) in enumerate((("lelli","#16b2ba"),("brin","#bf7f30"),("odo","#e76579"))):
    if not make_character(name,(i-1)*1.7,color):
        raise RuntimeError("Cannot build returning actor: "+name)
build_sunpatch_court()
rigs=[o for o in bpy.data.objects if o.name.startswith("cc0_extra_")]
if len(rigs)<1:
    raise RuntimeError("No actual imported Kenney rig was loaded")
pbr=[m for m in bpy.data.materials if m.name.startswith("CC0_PBR_")]
if len(pbr)<2:
    raise RuntimeError("Poly Haven PBR materials were not applied")
world=bpy.context.scene.world
if not world or not any(node.type=="TEX_ENVIRONMENT" for node in world.node_tree.nodes):
    raise RuntimeError("Poly Haven HDRI environment was not loaded")
rigged=[o for o in bpy.data.objects if o.type=="ARMATURE"]
if not rigged:
    raise RuntimeError("Kenney FBX source rigs were not imported")
print("BLENDER_CC0_INTEGRATION_PASS",len(rigs),"extras",
      len(rigged),"armatures",len(pbr),"PBR materials",flush=True)
