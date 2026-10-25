#!/usr/bin/env python3
"""Export twelve proposed CartoonStudio supporting characters with free Blender.

No Kaggle call, no canon change, no modification of video/story.json.
Usage: blender -b -t 2 --python-exit-code 1 --python video/export_expanded_cast.py -- video/proposed_cast.json OUTPUT
"""
import importlib
import json
import math
import re
import sys
import types
from pathlib import Path

import bpy
from mathutils import Vector


def load_primitives():
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    pkg = types.ModuleType("cartoon_studio")
    pkg.__path__ = [str(here)]
    sys.modules.setdefault("cartoon_studio", pkg)
    sys.modules["cartoon_studio.studio_contract"] = importlib.import_module("studio_contract")
    return importlib.import_module("studio_world")


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def accessory(s, item, head, root, z, face, body, trim):
    name = item["key"]
    style = item["accessory"]
    if style == "cap":
        s.sphere(name+"_cap", (0,0,z+.43), (.38,.32,.18), trim, head)
        s.block(name+"_brim", (0,-.20,z+.29), (.79,.58,.09), trim, head, .03)
    elif style == "apron":
        s.block(name+"_apron",(0,-.40,1.03),(.65,.08,.68),trim,root,.04)
        s.block(name+"_pocket",(0,-.48,.89),(.32,.06,.17),body,root,.03)
    elif style == "scarf":
        s.tube(name+"_scarf",[(-.39,-.31,1.48),(-.10,-.47,1.42),(.40,-.31,1.48)],.09,trim,root)
        s.tube(name+"_scarf_tail",[(.27,-.44,1.46),(.39,-.48,1.13)],.07,trim,root)
    elif style == "glasses":
        # Hollow 3D spectacle rims so the eyes remain clearly visible.
        for side in (-1, 1):
            coords=[]
            for k in range(17):
                a=k*math.tau/16
                coords.append((side*.19+.21*math.cos(a),face-.155,z+.06+.19*math.sin(a)))
            s.tube(name+"_hollow_rim_"+str(side),coords,.026,trim,head)
        s.block(name+"_bridge",(0,face-.155,z+.06),(.18,.045,.036),trim,head,.015)
    elif style == "belt":
        s.tube(name+"_belt",[(-.44,-.22,1.00),(0,-.42,1.00),(.44,-.22,1.00)],.08,trim,root)
        s.block(name+"_buckle",(0,-.49,1.00),(.16,.08,.17),trim,root,.02)
    elif style == "crown":
        s.block(name+"_crown_base",(0,0,z+.39),(.69,.46,.14),trim,head,.03)
        for index in (-1,0,1):
            s.block(name+"_crown_tip_"+str(index),(index*.23,0,z+.54),(.13,.18,.26),trim,head,.02)
    elif style == "bow":
        for side in (-1,1):
            s.sphere(name+"_bow_"+str(side),(side*.17,-.03,z+.40),(.18,.09,.12),trim,head)
        s.sphere(name+"_knot",(0,-.06,z+.40),(.08,.10,.08),body,head)
    elif style == "leaf":
        leaf=s.sphere(name+"_leaf",(0,-.02,z+.42),(.15,.075,.30),trim,head)
        leaf.rotation_euler[1]=.26
        s.tube(name+"_leaf_vein",[(0,-.10,z+.23),(0,-.10,z+.58)],.025,body,head)
    elif style == "vest":
        for side in (-1,1):
            s.tube(name+"_vest_"+str(side),[(side*.29,-.30,1.50),(side*.36,-.39,1.12),(side*.16,-.41,.85)],.065,trim,root)
        s.sphere(name+"_button",(0,-.47,1.10),(.06,.04,.06),trim,root)
    elif style == "antenna":
        for side in (-1,1):
            s.tube(name+"_antenna_"+str(side),[(side*.20,0,z+.26),(side*.30,0,z+.63)],.035,body,head)
            s.sphere(name+"_tip_"+str(side),(side*.30,0,z+.69),(.095,.09,.095),trim,head)
    elif style == "flower":
        for index in range(5):
            angle=index*math.tau/5
            s.sphere(name+"_petal_"+str(index),(.17+math.cos(angle)*.12,-.03,z+.37+math.sin(angle)*.12),(.10,.06,.10),trim,head)
        s.sphere(name+"_flower_center",(.17,-.10,z+.37),(.06,.03,.06),body,head)
    elif style == "tufts":
        for side in (-1,1):
            s.sphere(name+"_tuft_"+str(side),(side*.21,0,z+.37),(.16,.14,.24),trim,head)
    else:
        raise ValueError("Unknown accessory "+style)


def build(s, item, position=(0,0,0)):
    name = item["key"]
    kind = item["shape"]
    shape_map = {
        "teardrop": ((.44,.35,.77),(.46,.35,.46),1.79),
        "barrel": ((.62,.39,.72),(.43,.35,.42),1.82),
        "bean": ((.52,.38,.72),(.45,.36,.43),1.83),
        "wide": ((.68,.40,.63),(.54,.36,.42),1.67),
        "square": ((.49,.35,.66),(.42,.35,.42),1.80),
        "tall": ((.32,.32,.92),(.38,.34,.43),2.12),
        "oval": ((.47,.36,.82),(.42,.35,.47),1.95),
        "compact": ((.59,.40,.52),(.47,.37,.40),1.51),
        "bell": ((.64,.39,.88),(.43,.36,.45),2.03),
        "pear": ((.61,.42,.75),(.43,.36,.44),1.85),
    }
    if kind not in shape_map:
        raise ValueError("Unknown shape "+kind)
    torso, head_size, head_z = shape_map[kind]
    body=s.material(name+"_body",item["body"])
    trim=s.material(name+"_trim",item["trim"])
    root=s.pivot(name,position)
    head=s.pivot(name+"_head_pivot",(0,0,0),root)
    torso_z=.95 if kind in ("wide","compact") else 1.09
    if kind=="square":
        s.block(name+"_square_body",(0,0,torso_z),(1.0,.69,1.26),body,root,.22)
    else:
        s.sphere(name+"_body",(0,0,torso_z),torso,body,root,32,20)
    if kind=="bell":
        s.sphere(name+"_bell_hem",(0,0,.65),(.69,.40,.22),trim,root)
    if kind=="square":
        s.block(name+"_square_head",(0,-.02,head_z),(.82,.67,.76),body,head,.19)
    else:
        s.sphere(name+"_head",(0,-.02,head_z),head_size,body,head,32,20)
    if kind=="teardrop":
        s.sphere(name+"_pointed_top",(0,.09,head_z+.33),(.18,.20,.21),body,head)
    face=-.02-head_size[1]+.008
    eye_z=head_z+.07
    eyes=s._eyes(name,head,eye_z,face,.18,item["trim"],s.material(name+"_eyebrows","#54445a"))
    s._arms(name,root,body,torso[0]*.86,1.64 if kind=="tall" else 1.36,.56)
    s._feet(name,root,body,.23,.79)
    mouth_z=head_z-.19
    mouth=s.sphere(name+"_mouth",(0,face-.02,mouth_z),(.17,.030,.025),s.material(name+"_mouth_dark","#42283b"),head)
    s.sphere(name+"_tongue",(0,face-.045,mouth_z-.053),(.09,.017,.015),s.material(name+"_pink","#e89faf"),head)
    s._facial_shape_keys(mouth,eyes)
    accessory(s,item,head,root,head_z,face,body,trim)
    return root


def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(argv)!=2:
        raise SystemExit("Required: proposed_cast.json OUTPUT_DIR")
    spec=json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    out=Path(argv[1]).resolve()
    out.mkdir(parents=True,exist_ok=True)
    candidates=spec["candidates"]
    if spec["status"]!="proposed_not_canon" or len(candidates)!=12:
        raise ValueError("Expected twelve unapproved supporting proposals")
    names=[item["key"] for item in candidates]
    if len(set(names))!=12 or set(names) & set(spec["existing_original"]):
        raise ValueError("Duplicate character key or overwrite of original heroes")
    if not all(re.fullmatch(r"[a-z][a-z0-9_]{0,31}",name) for name in names):
        raise ValueError("Invalid character key")
    s=load_primitives()
    assets={}
    for item in candidates:
        reset()
        build(s,item)
        meshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]
        morphs={key.name for mesh in meshes if mesh.data.shape_keys for key in mesh.data.shape_keys.key_blocks}
        required={"viseme_aa","viseme_PP","viseme_O","eyeBlinkLeft","eyeBlinkRight"}
        if len(meshes)<18 or not required.issubset(morphs):
            raise RuntimeError(item["key"]+" has insufficient actual geometry or facial morphs")
        path=out/(item["key"]+"_proposed_clay.glb")
        bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB")
        if not path.is_file() or path.stat().st_size<2500:
            raise RuntimeError("GLB export failed for "+item["key"])
        assets[item["key"]]={"filename":path.name,"meshes":len(meshes),"morphs":sorted(morphs),"skeletal_rig":False,"canon":False}
        print("PROPOSED_GLTF",path.name,path.stat().st_size,flush=True)
    reset()
    for index,item in enumerate(candidates):
        x=(index%4-1.5)*2.58
        z=(1-index//4)*3.18
        build(s,item,(x,0,z))
    camera=bpy.data.cameras.new("Cast contact sheet camera")
    camera.type="ORTHO"
    camera.ortho_scale=13.8
    obj=bpy.data.objects.new("Cast contact sheet camera",camera)
    bpy.context.collection.objects.link(obj)
    obj.location=(0,-20,3.9)
    target=Vector((0,0,1.20))
    obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Y").to_euler()
    scene=bpy.context.scene
    scene.camera=obj
    # Use CPU Cycles rather than GPU/EGL-dependent Workbench in GitHub Actions.
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=24
    scene.cycles.use_denoising=False
    scene.render.film_transparent=False
    scene.world.use_nodes=True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.38,.47,.61,1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.45
    for light_name, position, power in (
        ("Key",(-6,-6,10),1100),
        ("Fill",(5,-4,7),700),
    ):
        lamp=bpy.data.lights.new(light_name,"AREA")
        lamp.energy=power
        lamp.size=9
        light=bpy.data.objects.new(light_name,lamp)
        bpy.context.collection.objects.link(light)
        light.location=position
        light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat("-Z","Y").to_euler()
    scene.view_settings.view_transform="Standard"
    scene.view_settings.exposure=-0.5
    for i, item in enumerate(candidates):
        # Separate text objects belong to the static REVIEW SHEET, not 3D models.
        col=i%4
        row=i//4
        tx=(col-1.5)*2.58
        tz=(1-row)*3.18-.46
        font=bpy.data.curves.new("Caption_"+item["key"],"FONT")
        font.body=item["key"].upper()
        font.align_x="CENTER"
        font.size=.32
        name_obj=bpy.data.objects.new("Caption_"+item["key"],font)
        bpy.context.collection.objects.link(name_obj)
        name_obj.location=(tx,-.60,tz)
        name_obj.rotation_euler[0]=math.pi/2
        font.materials.append(s.material("gallery_ink","#24344d"))
    scene.render.resolution_x=1200
    scene.render.resolution_y=900
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(out/"proposed_cast_contact_sheet.png")
    bpy.ops.render.render(write_still=True)
    if not Path(scene.render.filepath).is_file():
        raise RuntimeError("Character gallery did not render")
    report={"status":"proposed_not_canon","count":12,"existing_protected":spec["existing_original"],
            "characters":assets,"rigging":"pivot puppets with facial blendshapes, no humanoid skeletal rig",
            "voices":"unassigned","story_modified":False,"kaggle_render":False}
    (out/"proposed_cast_manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("EXPANDED_CAST_SUCCESS 12 models; proposed only; no Kaggle render",flush=True)


if __name__=="__main__":
    main()
