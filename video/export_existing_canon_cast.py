#!/usr/bin/env python3
"""Package the THREE EXISTING canonical cartoon meshes, not new designs.

Reuses original video/studio_world.py and its exact speaker appearances.
Exports native .blend, independent animated GLBs, and a real review still.
No Kaggle story render, no story text edits, no false full lip-sync claims.
"""
import hashlib, importlib, json, math, sys, types
from pathlib import Path
import bpy
from mathutils import Vector

VIDEO=Path(__file__).resolve().parent
pkg=types.ModuleType("cartoon_studio")
pkg.__path__=[str(VIDEO)]
sys.modules["cartoon_studio"]=pkg
studio=importlib.import_module("cartoon_studio.studio_world")
ROLES=[
  ("lelli","turquoise",-2.25,["pear_body","strap_-1","strap_1","curl_1","curl_2","cheek_-1","cheek_1"]),
  ("brin","ochre",0,["torso","flat_head","navy_sash","brow_-1","brow_1"]),
  ("odo","coral",2.25,["round_body","side_flap_-1","side_flap_1","collar"])
]
VISEMES={"viseme_PP","viseme_kk","viseme_E","viseme_aa","viseme_O","viseme_U","viseme_FF","viseme_nn","mouthSmile"}

def descendants(root):
    objects={root}
    stack=list(root.children)
    while stack:
        obj=stack.pop()
        if obj in objects:continue
        objects.add(obj)
        stack.extend(obj.children)
    return objects

def file_sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def cast_animate(actor,mouth):
    head=actor["head"]
    left,right=actor["arms"]
    for frame in (1,13,25,37,49,61,72):
        bpy.context.scene.frame_set(frame)
        head.rotation_euler=(0,0.05*math.sin(frame*.08),0.075*math.cos(frame*.08))
        head.keyframe_insert(data_path="rotation_euler",frame=frame)
        left.rotation_euler=(0,0,-.24 if frame in (13,25) else 0)
        right.rotation_euler=(0,0,.58 if frame in (13,25,37) else 0)
        left.keyframe_insert(data_path="rotation_euler",frame=frame)
        right.keyframe_insert(data_path="rotation_euler",frame=frame)
    for key in VISEMES:
        target=mouth.data.shape_keys.key_blocks[key]
        for frame,value in ((1,0),(18,0.8 if key=="viseme_aa" else 0),
                            (27,0),(42,0.8 if key=="viseme_O" else 0),(54,0),(72,0)):
            target.value=value
            target.keyframe_insert(data_path="value",frame=frame)
    bpy.context.scene.frame_set(1)

def convert_curves(objects):
    for ob in [x for x in objects if x.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target="MESH")
    bpy.ops.object.select_all(action="DESELECT")

def studio_review(actors,png):
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=1280
    scene.render.resolution_y=720
    scene.render.resolution_percentage=100
    scene.render.film_transparent=False
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(png)
    scene.world.color=(.40,.45,.48)
    bpy.ops.object.camera_add(location=(0,-11.5,3.0))
    camera=bpy.context.object
    camera.rotation_euler=(Vector((0,0,1.4))-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=camera
    camera.data.type="ORTHO"
    camera.data.ortho_scale=4.7
    preview_objs=[camera]
    for xyz,power,size in (((-3,-4,6),1700,7),((3,-2,4),750,4),((0,4,5),1200,6)):
        bpy.ops.object.light_add(type="AREA",location=xyz)
        lamp=bpy.context.object
        lamp.data.energy=power
        lamp.data.shape="DISK"
        lamp.data.size=size
        preview_objs.append(lamp)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.09))
    ground=bpy.context.object
    ground.name="REVIEW_FLOOR_NOT_PART_OF_ORIGINAL_CHARACTERS"
    ground.data.materials.append(studio.material("review_floor","#dfe8de",.9))
    preview_objs.append(ground)
    scene.frame_set(1)
    bpy.ops.render.render(write_still=True)
    if not png.exists() or png.stat().st_size<18000:
        raise RuntimeError("Real cast image not rendered")
    for obj in preview_objs:
        bpy.data.objects.remove(obj,do_unlink=True)

def main(directory):
    directory=Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=True)
    story_file=VIDEO/"story.json"
    before=story_file.read_bytes()
    story=json.loads(before)
    if len(story.get("dialogue",[]))!=74 or set(story.get("characters",{}))!={"lelli","brin","odo"}:
        raise RuntimeError("Unexpected canonical story or speaking cast, refusing to alter canon")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=72
    actors={}
    results={}
    for key,color,x,parts in ROLES:
        actor=studio.make_character(key,x,color)
        if not actor:raise RuntimeError("Existing source missing actor "+key)
        actors[key]=actor
        nodes=descendants(actor["root"])
        names={n.name for n in nodes}
        missing=[key+"_"+name for name in parts if key+"_"+name not in names]
        if missing:raise RuntimeError("Canon costume/silhouette details missing: "+str(missing))
        mouth=next((n for n in nodes if n.name==key+"_mouth"),None)
        if not mouth or not mouth.data.shape_keys:
            raise RuntimeError("Existing canonical mouth mesh missing "+key)
        keys=set(mouth.data.shape_keys.key_blocks.keys())
        if not VISEMES.issubset(keys):raise RuntimeError("Existing facial viseme source missing "+key)
        cast_animate(actor,mouth)
        convert_curves(nodes)
        nodes=descendants(actor["root"])
        polygon_count=sum(len(n.data.polygons) for n in nodes if n.type=="MESH")
        if polygon_count<2500:raise RuntimeError("Original mesh too small or broken "+key)
        bpy.ops.object.select_all(action="DESELECT")
        for n in nodes:n.select_set(True)
        bpy.context.view_layer.objects.active=actor["root"]
        glb=directory/(key+"-original-cartoon-character.glb")
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",
            use_selection=True,export_animations=True,export_morph=True)
        if not glb.is_file() or glb.stat().st_size<30000:
            raise RuntimeError("Real canonical GLB export failed for "+key)
        results[key]={"original_source_meshes":len([n for n in nodes if n.type=="MESH"]),
                      "original_mesh_polygons":polygon_count,
                      "original_part_names_verified":sorted(key+"_"+part for part in parts),
                      "facial_visemes":sorted(VISEMES),
                      "node_head_and_hand_pivots":"animated",
                      "source_filename":glb.name,"sha256":file_sha(glb),
                      "exported_bytes":glb.stat().st_size}
    bpy.ops.object.select_all(action="DESELECT")
    png=directory/"Lelli-Brin-Odo-canonical-cast-lineup.png"
    studio_review(actors,png)
    scene.frame_set(1)
    blend=directory/"Lelli-Brin-Odo-original-cast.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True,check_existing=False)
    if not blend.exists() or blend.stat().st_size<100000:
        raise RuntimeError("Actual native Blender cast scene failed")
    if story_file.read_bytes()!=before:raise RuntimeError("Original episode dialogue changed")
    manifest={"status":"EXISTING_THREE_CANON_CHARACTERS_EXPORTED",
        "reused_art_source":"video/studio_world.py — original established character meshes, not newly designed",
        "source_script_sha256":file_sha(VIDEO/"studio_world.py"),
        "unchanged_story_sha256":hashlib.sha256(before).hexdigest(),
        "unchanged_dialogue_entries":74,"cast":results,
        "real_review_image":png.name,"review_image_sha256":file_sha(png),
        "real_blender_cast_scene":blend.name,"real_blend_sha256":file_sha(blend),
        "puppet_node_rig_not_complex_skeletal_rig":True,
        "viseme_morphs_present_but_audio_phoneme_timing_unapproved":True,
        "user_visual_quality_approved":False,"episode_mp4_rendered":False}
    (directory/"EXISTING-CANON-CAST-PACKAGE-EVIDENCE.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("REAL_ORIGINAL_THREE_CHARACTER_PACKAGE_CREATED",json.dumps(
        {"actors":list(results),"polygon_counts":{k:v["original_mesh_polygons"] for k,v in results.items()},
         "dialogue_unchanged":74,"episode_mp4":False}),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=1:raise SystemExit("Blender --python export_existing_canon_cast.py -- OUTPUT_DIR")
    main(args[0])
