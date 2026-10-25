#!/usr/bin/env python3
"""Audit newer Blender Studio CC-BY splash ORIGINAL .blend projects for cast rigs.

Input scenes are first-party Blender.org production artwork. Unlike low-poly
procedural placeholders, the geometry is unchanged. Do not assume a pretty
splash render includes separate, reusable or speaking characters.
Run under a Blender version >= authored project version, with --disable-autoexec.
"""
from __future__ import annotations
import argparse,json,re,sys
from collections import defaultdict
from pathlib import Path
import bpy

def author_audit(source,report):
    source=Path(source).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    rigs=[]
    all_mesh=[o for o in bpy.data.objects if o.type=="MESH" and o.data and getattr(o.data,"vertices",None)]
    matches=defaultdict(list)
    for obj in all_mesh:
        parents=set()
        cur=obj.parent
        for i in range(12):
            if cur is None:break
            if cur.type=="ARMATURE":parents.add(cur.name)
            cur=cur.parent
        for mod in obj.modifiers:
            if mod.type=="ARMATURE" and mod.object:parents.add(mod.object.name)
        for n in parents:
            matches[n].append(obj)
    for rig in bpy.data.objects:
        if rig.type!="ARMATURE":continue
        associated=matches[rig.name]
        faces=sum(len(m.data.polygons) for m in associated)
        shape_keys=sum(len(m.data.shape_keys.key_blocks) for m in associated if m.data.shape_keys)
        unique_mesh_data=len({m.data.name for m in associated})
        meshes_renderable=sum(not m.hide_render for m in associated)
        rigs.append({"name":rig.name,"bones":len(rig.data.bones),
                     "mesh_objects":len(associated),"unique_mesh_data":unique_mesh_data,
                     "render_meshes":meshes_renderable,"faces":faces,
                     "shape_keys":shape_keys,"linked":bool(rig.library)})
    missing=[]
    for image in bpy.data.images:
        if image.users<1 or image.source not in {"FILE","TILED"}:continue
        if image.packed_file or image.packed_files:continue
        f=bpy.path.abspath(image.filepath)
        if image.source=="TILED" and "<UDIM>" in f:f=f.replace("<UDIM>","1001")
        if not Path(f).is_file():
            missing.append({"name":image.name,"path":image.filepath})
    linked_missing=[{"name":x.name,"path":x.filepath} for x in bpy.data.libraries
                    if not Path(bpy.path.abspath(x.filepath)).is_file()]
    candidates=[a for a in rigs if a["bones"]>=30 and a["render_meshes"]>=1 and a["faces"]>=2000]
    # These are *candidates*, not proven distinct original model identities.
    result={"source":source.name,"source_bytes":source.stat().st_size,
            "blender_version":bpy.app.version_string,
            "copyright":"Blender Studio CC BY: confirm attribution from publisher splash page",
            "source_url":"https://download.blender.org/demo/splash/"+source.name,
            "total_armatures":len(rigs),
            "total_mesh_objects":len(all_mesh),
            "candidate_character_rigs":candidates,"all_armatures":rigs,
            "candidate_count":len(candidates),
            "unique_rig_names_after_instance_normalization":len(set(
                re.sub(r"\.\d{3}$","",a["name"]) for a in candidates)),
            "missing_external_image_count":len(missing),
            "missing_images":missing[:120],
            "missing_blend_libraries":linked_missing,
            "material_count":len(bpy.data.materials),
            "image_data_count":len(bpy.data.images),
            "packed_image_count":sum(bool(x.packed_file or x.packed_files) for x in bpy.data.images),
            "actions":len(bpy.data.actions),
            "production_approved":False,
            "movie_render_performed":False,
            "warning":"A scene rig with many bones is not proof of speaking-capable reusable character; inspect facial controls and isolate source mesh first"}
    out=Path(report)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("MODERN_ORIGINAL_STUDIO_RIGS",json.dumps({
       key:result[key] for key in ("source","source_bytes","candidate_count",
                 "unique_rig_names_after_instance_normalization","missing_external_image_count",
                 "packed_image_count","actions")}),flush=True)
    for item in candidates[:40]:
        print("MODERN_STUDIO_REAL_CANDIDATE",json.dumps(item),flush=True)
    if len(all_mesh)==0 or len(bpy.data.materials)==0:
        raise SystemExit("Not a usable studio source file")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("blend")
    parser.add_argument("report")
    a=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:])
    author_audit(a.blend,a.report)
