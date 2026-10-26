#!/usr/bin/env python3
"""Build Episode 1's real, reusable woodland set from Kenney and Poly Haven CC0.
Blender Python (no Kaggle). Only tiny story-specific leaf/cap/twig geometry is authored.
All background scenery must be authentic imported, licence-recorded Kenney art.
Never makes any substitute or newly generated talking character.
"""
import argparse,hashlib,json,math,shutil,sys
from pathlib import Path
import bpy
from mathutils import Vector

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def bbox(objects):
    samples=[o.matrix_world@Vector(v) for o in objects if o.type=="MESH" for v in o.bound_box]
    if not samples:raise ValueError("Imported CC0 object lacks mesh")
    return Vector(tuple(min(q[i] for q in samples) for i in range(3))),Vector(tuple(max(q[i] for q in samples) for i in range(3)))

def get_imported(root,entry):
    relative=Path(entry["file"])
    if relative.is_absolute() or ".." in relative.parts:raise ValueError("Unsafe source path")
    source=(root/relative).resolve()
    if root not in source.parents or not source.exists():raise FileNotFoundError(source)
    before=set(bpy.data.objects)
    if source.suffix.lower() in (".glb",".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(source))
    else:
        raise ValueError("Kenney environment model must be glTF")
    selection=list(set(bpy.data.objects)-before)
    meshes=[o for o in selection if o.type=="MESH"]
    if not meshes:raise ValueError("No real Kenney geometry in "+str(source))
    return selection,meshes

def group_objects(objects, label, position, size):
    lo,hi=bbox(objects)
    span=max(hi.z-lo.z,.005)
    scale=size/span
    root=bpy.data.objects.new(label,None)
    bpy.context.scene.collection.objects.link(root)
    for obj in objects:
        if obj.parent in objects:continue
        world=obj.matrix_world.copy()
        obj.parent=root
        obj.matrix_world=world
    root.scale=(scale,scale,scale)
    center=(lo+hi)*.5
    root.location=Vector(position)-Vector((center.x*scale,center.y*scale,lo.z*scale))
    return root

def material(name,color,rough=.62):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Roughness"].default_value=rough
    return mat

def export(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",
                              export_yup=True,export_materials="EXPORT")
    if path.stat().st_size<3000:raise ValueError("Degenerate asset export "+str(path))
    return {"path":str(path),"sha256":digest(path),"bytes":path.stat().st_size}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def prepare_cc0_woodland(out,import_root,quality_root):
    reset()
    manifest=read(import_root/"asset_manifest.json")
    if not manifest.get("sources") or not all(x.get("license")=="CC0-1.0" for x in manifest["sources"]):
        raise ValueError("Kenney source licence metadata missing")
    quality=read(quality_root/"quality_manifest.json")
    if quality.get("license")!="CC0-1.0" or len(quality.get("materials",[]))<2:
        raise ValueError("Poly Haven CC0 PBR pack missing")
    by_name=[a for a in manifest["assets"] if a["role"]=="environment_prop" and a["license"]=="CC0-1.0"]
    def select(prefixes):
        return [a for a in by_name if Path(a["file"]).stem.lower().startswith(prefixes)]
    tree=select(("tree",))
    grass=select(("grass","flowers","plant","hedge","mushrooms"))
    stones=select(("rocks","stones"))
    if not tree or not grass or not stones:raise ValueError("No real CC0 trees/plants/rocks available")
    # Real imported CC0 props, positioned along a winding central clearing.
    arrangement=[(tree[0],(-3.3,1.4,0),3.7),(tree[-1],(3.25,1.7,0),3.45),
      (tree[0],(-4.0,4.8,0),4.25),(tree[-1],(3.9,4.6,0),4.0),
      (grass[0],(-2.0,1.2,0),.65),(grass[-1],(2.1,1.4,0),.82),
      (grass[len(grass)//2],(-2.4,3.0,0),.6),(grass[0],(2.4,3.6,0),.6),
      (stones[0],(-1.8,2.8,0),.48),(stones[-1],(1.9,2.3,0),.5)]
    sources_used=[]
    for idx,(entry,pos,size) in enumerate(arrangement):
        objects,meshes=get_imported(import_root,entry)
        group_objects(objects,f"CC0_Kenney_{idx:02}",pos,size)
        sources_used.append({"file":entry["file"],"source":entry["source"],"license":entry["license"]})
    # Plain geometric ground is scenery, never a stand-in character.
    bpy.ops.mesh.primitive_plane_add(size=2,location=(0,1.2,-.04))
    plane=bpy.context.object
    plane.name="EP01 Meadow PBR floor"
    plane.scale=(6.0,5.0,1.0)
    grass_mat=material("Meadow existing CC0 Poly Haven PBR",(0.29,.43,.22))
    maps=quality["materials"][0]["maps"]
    shader=grass_mat.node_tree.nodes.get("Principled BSDF")
    nodes=grass_mat.node_tree.nodes
    links=grass_mat.node_tree.links
    for prop,output_socket in (("color","Base Color"),("roughness","Roughness")):
        p=(quality_root/maps[prop]).resolve()
        if quality_root not in p.parents or not p.exists():raise FileNotFoundError(p)
        node=nodes.new("ShaderNodeTexImage")
        node.image=bpy.data.images.load(str(p))
        if prop=="roughness":node.image.colorspace_settings.name="Non-Color"
        links.new(node.outputs["Color"],shader.inputs[output_socket])
    plane.data.materials.append(grass_mat)
    stage=export(out/"stage"/"woodland_clearing.glb")
    return stage,sources_used,quality

def leaf(out):
    reset()
    # Original EPISODE PROP (not a character). Pivot at the attached stem.
    vertices=[(0,0,0),(0,.14,.012),(-.13,.37,.025),(-.24,.66,.02),
              (-.15,.89,.035),(0,1.05,.01),(.15,.89,.035),
              (.24,.66,.02),(.13,.37,.025)]
    faces=[(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8)]
    mesh=bpy.data.meshes.new("Episode leaf curving blade")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new("EP01 genuine authored leaf prop",mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material("Autumn amber leaf",(0.75,.42,.10),.49))
    mod=obj.modifiers.new("Natural visible leaf thickness","SOLIDIFY")
    mod.thickness=.014
    # The leaf is intentionally a lightweight reusable custom prop.
    return export(out/"props"/"hero_leaf.glb")

def acorn(out):
    reset()
    # Hand-authored one-off acorn CAP prop; never a character replacement.
    vertices=[(0,0,.22)]
    rings=8
    n=16
    for j in range(rings):
        r=.32*(1.0-j/rings*.68)
        z=.20*(j/rings)**1.6
        for k in range(n):
            angle=math.tau*k/n
            vertices.append((r*math.cos(angle),r*math.sin(angle),z))
    faces=[]
    for j in range(rings-1):
        for k in range(n):
            a=1+j*n+k
            b=1+j*n+(k+1)%n
            c=b+n
            d=a+n
            faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new("Acorn cup")
    mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new("EP01 Acorn cap",mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material("Warm acorn wood",(0.55,.29,.11),.82))
    mod=obj.modifiers.new("Acorn cap thickness","SOLIDIFY")
    mod.thickness=.025
    return export(out/"props"/"acorn_cap.glb")

def twig(out):
    reset()
    curve=bpy.data.curves.new("A genuine tiny forked twig","CURVE")
    curve.dimensions="3D";curve.bevel_depth=.023;curve.bevel_resolution=3
    for points in (((0,0,0),(0,0,.4),(.07,0,.72)),((.05,0,.52),(.22,0,.72))):
        s=curve.splines.new("POLY");s.points.add(len(points)-1)
        for p,v in zip(s.points,points):p.co=(*v,1)
    ob=bpy.data.objects.new("EP01 forked twig",curve)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material("Soft walnut branch",(.37,.25,.13)))
    return export(out/"props"/"forked_twig.glb")

def pebbles(out,import_root):
    reset()
    m=read(import_root/"asset_manifest.json")
    rocks=[a for a in m["assets"] if a["role"]=="environment_prop"
           and Path(a["file"]).stem.lower().startswith(("rocks","stones"))]
    if not rocks:raise RuntimeError("No real Kenney stones; reject generic stand-in")
    for idx,pos in enumerate(((-.2,0,0),(.12,.07,0),(.36,-.06,0))):
        objects,meshes=get_imported(import_root,rocks[idx%len(rocks)])
        group_objects(objects,f"EP01_CC0_pebble_{idx}",pos,.17)
    return export(out/"props"/"rounded_pebbles.glb")

def main(root,quality,out):
    root=Path(root).resolve();quality=Path(quality).resolve();out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    stage,source_rows,meta=prepare_cc0_woodland(out,root,quality)
    # Copy genuine 1K source HDRI: exported EXR prevents extension mismatch.
    src=(quality/meta["environment"]).resolve()
    if quality not in src.parents or not src.exists():raise ValueError("Wrong HDRI source path")
    lighting=out/"lighting"/"garden_1k.exr"
    lighting.parent.mkdir(parents=True,exist_ok=True)
    image=bpy.data.images.load(str(src))
    image.filepath_raw=str(lighting)
    image.file_format="OPEN_EXR"
    image.save()
    if lighting.stat().st_size<25000:raise ValueError("Converted HDRI invalid")
    props={"hero_leaf":leaf(out),"acorn_cap":acorn(out),"forked_twig":twig(out),
           "rounded_pebbles":pebbles(out,root)}
    report={"stage":stage,"props":props,"hdri":{"path":str(lighting),"sha256":digest(lighting)},
            "kenney_provenance":source_rows,"quality_provenance":meta.get("files",[]),
            "licence":"CC0-1.0 imported scenery; three tiny story-specific props are original",
            "no_character_generated":True,"scene_lighting_camera_placement_reviewed":False,
            "episode_rendered":False}
    (out/"STAGE_BUILD_EVIDENCE.json").write_text(json.dumps(report,indent=2)+"\n")
    print("EP01_CC0_ACTUAL_WOODLAND_STAGE_BUILT",len(source_rows),"Kenney real assets",len(props),"props")

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument("--kenney",required=True)
    p.add_argument("--quality",required=True);p.add_argument("--out",required=True)
    a=p.parse_args(args);main(a.kenney,a.quality,a.out)
