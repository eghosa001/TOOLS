#!/usr/bin/env python3
"""Export real distinct Blender Studio Sprite Fright actor rigs, no new geometry.

Asset master is a first-party Blender movie scene. Select ONLY mesh objects
actually skinned to a named character armature. Reuse identical source assets
once, not dozens of instance clones. Preserve original original copyright/
artist and CC-BY attribution in the companion manifest.
"""
import json,sys,traceback
from pathlib import Path
import bpy

ACTORS={
    "sprite":"RIG-Sprite",
    "butterfly":"RIG-butterfly",
    "ladybug":"RIG-ladybug",
    "snail":"RIG-snail",
    "spider":"RIG-spider",
}
def belongs_to_actor(mesh,rig):
    x=mesh
    for _ in range(12):
        if x.parent==rig:
            return True
        if x.parent is None:break
        x=x.parent
    return any(mod.type=="ARMATURE" and mod.object==rig for mod in mesh.modifiers)

def main(source,out,requested="all"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()),load_ui=False)
    output=Path(out).resolve()
    output.mkdir(parents=True,exist_ok=True)
    manifest={"source":"https://download.blender.org/demo/sprite_fright_030_0020_A.zip",
              "artist":"Blender Studio; Sprite Fright open movie",
              "license":"CC-BY-4.0 attribution required",
              "no_procedural_or_low_poly_replacements":True,
              "characters":{}}
    if requested not in ACTORS:
        raise ValueError("Provide one actor key per export; each source .blend needs its own scene purge")
    names=(requested,)
    for key in names:
        named=ACTORS[key]
        rigs=[o for o in bpy.context.view_layer.objects if o.type=="ARMATURE" and o.name==named]
        if len(rigs)!=1:
            raise RuntimeError("Expected exactly one original source "+named+", found "+str(len(rigs)))
        rig=rigs[0]
        meshes=[o for o in bpy.context.view_layer.objects
                if o.type=="MESH" and o.data.vertices and not o.hide_render and belongs_to_actor(o,rig)]
        if len(meshes)<1:
            raise RuntimeError("Source character has no renderable skin mesh: "+key)
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        rig.hide_set(False)
        rig.select_set(True)
        for mesh in meshes:
            mesh.hide_set(False)
            mesh.select_set(True)
        bpy.context.view_layer.objects.active=rig
        # The original shot contains thousands of unrelated meshes and dozens
        # of duplicated crowd rigs. Keep only this actor in export memory.
        # Without this purge, glTF may try to evaluate the entire 250 MB
        # cinematographic scene and appear to hang for many minutes.
        keep={rig,*meshes}
        removed=0
        for other in list(bpy.data.objects):
            if other not in keep:
                bpy.data.objects.remove(other,do_unlink=True)
                removed+=1
        bpy.context.view_layer.update()
        print("SINGLE_ORIGINAL_RIG_EXPORT_SCENE",key,
              "removed_irrelevant_scene_objects",removed,
              "retained",len(keep),flush=True)
        target=output/(key+"_blender_studio.glb")
        try:
            bpy.ops.export_scene.gltf(
                filepath=str(target),export_format="GLB",use_selection=True,
                export_skins=True,export_morph=True,
                export_apply=False,export_animations=False,
                export_materials="EXPORT")
        except Exception as e:
            print("DISTINCT_CHARACTER_EXPORT_ERROR",key,repr(e),flush=True)
            raise
        if target.stat().st_size<200_000:
            raise RuntimeError("Unexpectedly small exported 3D character "+key)
        manifest["characters"][key]={
            "source_rig":rig.name,"original_bones":len(rig.data.bones),
            "selected_skin_meshes":len(meshes),
            "original_mesh_faces":sum(len(mesh.data.polygons) for mesh in meshes),
            "original_shape_keys":sum(len(mesh.data.shape_keys.key_blocks) if mesh.data.shape_keys else 0 for mesh in meshes),
            "filename":target.name,"bytes":target.stat().st_size,
            "note":"Renderer and face controls require separate validation; Blender driver behaviours do not automatically transfer to glTF",
            "canon":False,
        }
        print("AUTHENTIC_SPRITE_FRIGHT_EXPORTED",json.dumps(manifest["characters"][key]),flush=True)
    (output/"STUDIO_CAST_PROVENANCE.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("SPRITE_FRGHT_DISTINCT_RIGS_EXPORT_COUNT",len(names),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)<2 or len(args)>3:
        raise SystemExit("Usage blender --python this.py -- SCENE.blend OUTPUT_DIR [name]")
    main(*args)
