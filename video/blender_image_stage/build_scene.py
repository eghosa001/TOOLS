#!/usr/bin/env python3
"""Manually directed image-layer -> editable Blender 2.5D scene.

Use ONLY artist-selected PNGs in an explicit manifest. No automatic media
selection, prompt-to-video assembly, publishing or artificial quality approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

PNG_MAGIC = bytes.fromhex("89504e470d0a1a0a")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-]{0,63}$")
ROLES = {"sky","distant","environment","midground","ground","character","prop",
         "foreground","shadow","vfx"}

def number(v,name,lo,hi):
    if type(v) not in (float,int) or not math.isfinite(v) or not lo <= v <= hi:
        raise ValueError(f"{name}: finite number in [{lo}, {hi}] required")
    return float(v)

def point(v,name,lo=-100000,hi=100000):
    if not isinstance(v,list) or len(v)!=2:raise ValueError(f"{name}: expected [x,y]")
    return number(v[0],name+" x",lo,hi),number(v[1],name+" y",lo,hi)

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def secure_png(root,relative):
    if not isinstance(relative,str) or not relative.lower().endswith(".png"):
        raise ValueError("Only relative PNG sources allowed")
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Source path escapes scene folder")
    if not path.is_file():raise FileNotFoundError(f"Missing selected art: {path}")
    if path.stat().st_size>60*1024*1024:raise ValueError("Source image over 60 MiB")
    with path.open("rb") as f:header=f.read(24)
    if header[:8]!=PNG_MAGIC or header[12:16]!=b"IHDR":
        raise ValueError(f"Invalid PNG signature: {relative}")
    dimensions=(int.from_bytes(header[16:20],"big"),int.from_bytes(header[20:24],"big"))
    if not all(1<=n<=8192 for n in dimensions):
        raise ValueError("Invalid PNG dimensions")
    return path,dimensions

def validate(file):
    file=Path(file).resolve()
    source=json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(source,dict) or source.get("schema_version")!=1:
        raise ValueError("schema_version 1 required")
    size=source.get("resolution")
    if not isinstance(size,list) or len(size)!=2:
        raise ValueError("resolution must be [width,height]")
    width=int(number(size[0],"width",360,4096))
    height=int(number(size[1],"height",360,4096))
    if [width,height]!=size:raise ValueError("Resolution must be integer pixels")
    fps=int(number(source.get("fps",24),"fps",12,60))
    frames=int(number(source.get("frames",144),"frames",1,3600))
    camera=source.get("camera",{})
    if not isinstance(camera,dict):raise ValueError("camera must be object")
    pan=point(camera.get("pan_px",[0,0]),"camera.pan_px",-5000,5000)
    layers=source.get("layers")
    if not isinstance(layers,list) or not 1<=len(layers)<=80:
        raise ValueError("1..80 explicitly chosen image layers required")
    validated=[]
    names=set()
    for layer in layers:
        if not isinstance(layer,dict):raise ValueError("Layer must be object")
        name=layer.get("name")
        if not isinstance(name,str) or not NAME_RE.fullmatch(name) or name in names:
            raise ValueError("Missing, invalid or duplicate layer name")
        names.add(name)
        if layer.get("role") not in ROLES:raise ValueError(f"{name}: unknown role")
        rights=layer.get("rights")
        if not isinstance(rights,dict) or rights.get("status") not in (
            "original","ai_generated","CC0","CC_BY"):
            raise ValueError(f"{name}: explicit commercial-use provenance required")
        if rights["status"] in ("CC0","CC_BY") and (
            not rights.get("source_url") or not rights.get("creator")):
            raise ValueError(f"{name}: CC licensed source requires author and URL")
        path,dimensions=secure_png(file.parent,layer.get("image"))
        digest=sha256(path)
        if layer.get("sha256") and layer["sha256"].lower()!=digest:
            raise ValueError(f"{name}: source hash differs from approved image")
        pos=point(layer.get("position_px",[width/2,height/2]),name+".position_px")
        pivot=point(layer.get("pivot_px",[dimensions[0]/2,dimensions[1]/2]),name+".pivot_px",0,8192)
        if pivot[0]>dimensions[0] or pivot[1]>dimensions[1]:
            raise ValueError(f"{name}: pivot outside asset")
        depth=number(layer.get("depth",0),name+".depth",-9,9)
        parallax=number(layer.get("parallax",1),name+".parallax",0,2)
        scale=number(layer.get("scale",1),name+".scale",.01,20)
        keys=layer.get("keys",[])
        if not isinstance(keys,list) or len(keys)>1000:
            raise ValueError(f"{name}: invalid animation keys")
        seen=set()
        for key in keys:
            if not isinstance(key,dict):raise ValueError(f"{name}: key must be object")
            frame=int(number(key.get("frame"),name+" frame",1,frames))
            if frame in seen:raise ValueError(f"{name}: duplicate frame")
            seen.add(frame)
            if "position_px" in key:point(key["position_px"],name+" position")
            if "rotation_deg" in key:number(key["rotation_deg"],name+" rotation",-1080,1080)
            if "scale" in key:number(key["scale"],name+" scale",.01,20)
        validated.append(dict(layer,absolute_image=str(path),dimensions=dimensions,
            source_sha256=digest,position_px=pos,pivot_px=pivot,depth=depth,
            parallax=parallax,scale=scale))
    return dict(source,resolution=[width,height],fps=fps,frames=frames,
                camera_pan=pan,layers=validated,manifest_sha256=sha256(file))

def material(bpy,image,name):
    mat=bpy.data.materials.new(name+"_alpha_material")
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear()
    tex=nodes.new("ShaderNodeTexImage")
    tex.image=image
    tex.interpolation="Linear"
    trans=nodes.new("ShaderNodeBsdfTransparent")
    em=nodes.new("ShaderNodeEmission")
    mix=nodes.new("ShaderNodeMixShader")
    output=nodes.new("ShaderNodeOutputMaterial")
    links=mat.node_tree.links
    links.new(tex.outputs["Color"],em.inputs["Color"])
    links.new(tex.outputs["Alpha"],mix.inputs[0])
    links.new(trans.outputs[0],mix.inputs[1])
    links.new(em.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs["Surface"])
    if hasattr(mat,"surface_render_method"):
        mat.surface_render_method="DITHERED"
    elif hasattr(mat,"blend_method"):
        mat.blend_method="BLEND"
    return mat

def build(manifest,output_path):
    import bpy
    out=Path(output_path).resolve()
    if out.suffix.lower()!=".blend":raise ValueError("Output must end in .blend")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    w,h=manifest["resolution"]
    scene.render.resolution_x=w;scene.render.resolution_y=h
    scene.render.resolution_percentage=100
    scene.render.fps=manifest["fps"]
    scene.frame_start=1;scene.frame_end=manifest["frames"]
    scene.render.image_settings.file_format="PNG"
    options={item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    engine=next((e for e in ("BLENDER_EEVEE_NEXT","BLENDER_EEVEE","CYCLES") if e in options),None)
    if not engine:raise RuntimeError("No compatible Blender render engine")
    scene.render.engine=engine
    if engine=="CYCLES":scene.cycles.samples=16
    scene.world.color=(.05,.06,.08)
    unit=10/h
    bpy.ops.object.camera_add(location=(0,-20,0),rotation=(math.pi/2,0,0))
    cam=bpy.context.object;cam.name="CAMERA__portrait_2p5d"
    cam.data.type="ORTHO";cam.data.ortho_scale=10.0
    scene.camera=cam
    dx,dz=manifest["camera_pan"][0]*unit,-manifest["camera_pan"][1]*unit
    cam.location=(0,-20,0)
    cam.keyframe_insert(data_path="location",frame=1)
    cam.location=(dx,-20,dz)
    cam.keyframe_insert(data_path="location",frame=manifest["frames"])
    for layer in manifest["layers"]:
        name=layer["name"]
        img=bpy.data.images.load(layer["absolute_image"],check_existing=True)
        img.pack()
        pw,ph=layer["dimensions"];px,py=layer["pivot_px"]
        sf=unit*layer["scale"]
        x0,x1=-px*sf,(pw-px)*sf
        z0,z1=-(ph-py)*sf,py*sf
        mesh=bpy.data.meshes.new(name+"_quad")
        mesh.from_pydata([(x0,0,z0),(x1,0,z0),(x1,0,z1),(x0,0,z1)],[],[(0,1,2,3)])
        mesh.update()
        uv=mesh.uv_layers.new(name="UV")
        uv_coords=((0,0),(1,0),(1,1),(0,1))
        for poly in mesh.polygons:
            for idx in poly.loop_indices:
                uv.data[idx].uv=uv_coords[mesh.loops[idx].vertex_index]
        obj=bpy.data.objects.new(name,mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material(bpy,img,name))
        obj["role"]=layer["role"]
        obj["source_sha256"]=layer["source_sha256"]
        obj["rights"]=layer["rights"]["status"]
        obj["editor_approval_required"]=True
        x,y=layer["position_px"]
        bx,bz=(x-w/2)*unit,(h/2-y)*unit
        comp=1-layer["parallax"]
        obj.location=(bx,layer["depth"],bz)
        obj.keyframe_insert(data_path="location",frame=1)
        obj.location=(bx+dx*comp,layer["depth"],bz+dz*comp)
        obj.keyframe_insert(data_path="location",frame=manifest["frames"])
        for key in layer.get("keys",[]):
            frame=int(key["frame"]);t=0 if manifest["frames"]==1 else (frame-1)/(manifest["frames"]-1)
            kx,ky=key.get("position_px",layer["position_px"])
            obj.location=((kx-w/2)*unit+dx*comp*t,layer["depth"],(h/2-ky)*unit+dz*comp*t)
            obj.keyframe_insert(data_path="location",frame=frame)
            if "rotation_deg" in key:
                obj.rotation_euler[1]=math.radians(key["rotation_deg"])
                obj.keyframe_insert(data_path="rotation_euler",frame=frame)
            if "scale" in key:
                s=key["scale"];obj.scale=(s,s,s)
                obj.keyframe_insert(data_path="scale",frame=frame)
    try:scene.view_settings.view_transform="Standard"
    except (TypeError,ValueError):pass
    out.parent.mkdir(parents=True,exist_ok=True)
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print("EDITABLE_IMAGE_FIRST_BLENDER_STAGE",out,"NOT_QUALITY_APPROVED",flush=True)

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",required=True)
    parser.add_argument("--output")
    parser.add_argument("--validate",action="store_true")
    flags=parser.parse_args(args)
    manifest=validate(flags.manifest)
    if flags.validate:
        print(json.dumps({"valid":True,"layers":len(manifest["layers"]),
          "frames":manifest["frames"],"resolution":manifest["resolution"],
          "manifest_sha256":manifest["manifest_sha256"],
          "source_hashes":{l["name"]:l["source_sha256"] for l in manifest["layers"]},
          "quality_approved":False},indent=2))
    else:
        if not flags.output:raise SystemExit("--output .blend required when building")
        build(manifest,flags.output)

if __name__=="__main__":main()
