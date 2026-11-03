#!/usr/bin/env python3
"""Original studio single-take brittle shell fracture, NOT a release or stock edit.

Reuses the studio's free Blender/Cycles + rigid-body workflow. A continuous
pressing gesture causes original watertight shell fragments to separate under
Blender physics. No copied user-reference frames, no loop, no montage.
The lookdev is deliberately gated from motion and YouTube release.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import hashlib

def parse():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--mode", choices=("still","motion"), default="still")
    return p.parse_args(raw)

def material(bpy, name, color, rough=0.23, metallic=0.0, bump=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes; links=m.node_tree.links; s=n.get("Principled BSDF")
    s.inputs["Base Color"].default_value=(*color,1)
    s.inputs["Roughness"].default_value=rough
    s.inputs["Metallic"].default_value=metallic
    if bump:
        noise=n.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=155
        noise.inputs["Detail"].default_value=3.3
        b=n.new("ShaderNodeBump");b.inputs["Strength"].default_value=.14
        b.inputs["Distance"].default_value=bump
        links.new(noise.outputs["Fac"],b.inputs["Height"])
        links.new(b.outputs["Normal"],s.inputs["Normal"])
    return m

def cube(bpy,name,pos,dimensions,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object
    o.name=name;o.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new("Physical polished rounded edges","BEVEL")
        m.width=bevel;m.segments=4
        o.modifiers.new("Weighted true normals","WEIGHTED_NORMAL")
    return o

def cylinders(bpy,name,pos,radius,depth,mat,vertices=112,bevel=.024):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new("Machined bevel catchlight","BEVEL");m.width=bevel;m.segments=4
        o.modifiers.new("Weighted metallic normals","WEIGHTED_NORMAL")
    return o

def rigid(bpy,obj,kind,mass=0.1,shape="CONVEX_HULL"):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type=kind
    obj.rigid_body.collision_shape=shape
    obj.rigid_body.friction=.62
    obj.rigid_body.restitution=.035
    obj.rigid_body.use_margin=True
    obj.rigid_body.collision_margin=.0025
    if kind=="ACTIVE":obj.rigid_body.mass=mass

def surface(theta, phi, radius, center_height):
    texture=1.0+.0038*math.sin(19*theta+11*phi)+.0028*math.sin(27*theta-7*phi)
    r=radius*texture
    return (r*math.sin(theta)*math.cos(phi),
            r*math.sin(theta)*math.sin(phi),
            center_height+r*math.cos(theta))

def shard_mesh(bpy,name,j,i,nlon,theta0,theta1,outer,thickness,height,outer_mat,inner_mat):
    """Volume-bearing watertight curved shard, with its own internal faces."""
    a=i*2*math.pi/nlon;b=(i+1)*2*math.pi/nlon
    # Shared physical boundaries make a closed shell until force releases it.
    nx,ny=8,8;verts=[]
    for rad in (outer,outer-thickness):
        for k in range(ny+1):
            th=theta0+(theta1-theta0)*k/ny
            for n in range(nx+1):
                ph=a+(b-a)*n/nx
                verts.append(surface(th,ph,rad,height))
    stride=nx+1;layer=(ny+1)*stride;faces=[];kinds=[]
    def append_face(indices,mat_index):
        faces.append(indices);kinds.append(mat_index)
    for k in range(ny):
        for n in range(nx):
            q=k*stride+n
            append_face((q,q+1,q+stride+1,q+stride),0)
            p=layer+q
            append_face((p+stride,p+stride+1,p+1,p),1)
    for n in range(nx):
        q=n
        append_face((q,layer+q,layer+q+1,q+1),1)
        q=ny*stride+n
        append_face((q+1,layer+q+1,layer+q,q),1)
    for k in range(ny):
        q=k*stride
        append_face((q+stride,layer+q+stride,layer+q,q),1)
        q=k*stride+nx
        append_face((q,layer+q,layer+q+stride,q+stride),1)
    mesh=bpy.data.meshes.new(name+" actual volume")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(outer_mat);obj.data.materials.append(inner_mat)
    for f,kind in zip(obj.data.polygons,kinds):
        f.material_index=kind
        f.use_smooth=(kind==0)
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(mesh);bm.free()
    return obj

def key(obj, coords):
    for f,z in coords:
        obj.location.z=z
        obj.keyframe_insert("location",frame=f)

def look_at(obj, target):
    from mathutils import Vector
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()

def build(opt):
    import bpy
    from mathutils import Vector
    out=Path(opt.output).resolve();out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.frame_start=1;scene.frame_end=96;scene.render.fps=24
    scene.render.engine="CYCLES"
    scene.cycles.samples=80 if opt.mode=="still" else 30
    scene.cycles.use_denoising=True
    scene.render.resolution_x=720 if opt.mode=="still" else 480
    scene.render.resolution_y=1280 if opt.mode=="still" else 854
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.view_transform="AgX"
    scene.world.color=(.07,.08,.10)
    scene.gravity=(0,0,-9.81)

    slate=material(bpy,"Graphite presentation base",(.065,.073,.085),.35,bump=.003)
    pearl=material(bpy,"PBR glossy turquoise brittle shell",(.012,.42,.46),.12,.19,.0023)
    interior=material(bpy,"Fresh broken pearl shell interior",(.62,.80,.74),.34,.02,.003)
    core=material(bpy,"Matte plum porous core",(.24,.058,.13),.55,.01,.007)
    steel=material(bpy,"Brushed stainless hydraulic ram",(.49,.57,.62),.22,.81,.0009)
    copper=material(bpy,"Polished copper detail",(.55,.24,.075),.16,.91,.001)
    wood=material(bpy,"Satin walnut surface",(.16,.091,.060),.40,.0,.005)

    floor=cube(bpy,"Grounded walnut work surface",(0,0,-.20),(3.5,3.5,.34),wood,.035)
    rigid(bpy,floor,"PASSIVE",shape="BOX")
    base=cylinders(bpy,"Copper plinth",(0,0,.045),1.13,.14,copper)
    rigid(bpy,base,"PASSIVE")
    inset=cylinders(bpy,"Graphite receiving tray",(0,0,.115),1.06,.06,slate)
    rigid(bpy,inset,"PASSIVE")
    orb_center=1.06;rad=.92
    bpy.ops.mesh.primitive_uv_sphere_add(segments=112,ring_count=72,radius=.765,location=(0,0,orb_center))
    inner=bpy.context.object;inner.name="Unbroken porous inner core";inner.data.materials.append(core)
    for f in inner.data.polygons:f.use_smooth=True
    rigid(bpy,inner,"PASSIVE",shape="SPHERE")

    nlon=8;bands=[(.001,.37),(.37,.73),(.73,1.13),(1.13,1.78)]
    releases=[]
    for j,(lo,hi) in enumerate(bands):
        for i in range(nlon):
            shard=shard_mesh(bpy,"Brittle continuous-shell tile %02d-%02d"%(j+1,i+1),
                             j,i,nlon,lo,hi,rad,.065,orb_center,pearl,interior)
            rigid(bpy,shard,"ACTIVE",.025,shape="CONVEX_HULL")
            shard.rigid_body.kinematic=True
            shard.keyframe_insert(data_path="rigid_body.kinematic",frame=1)
            frame=49+j*7+(i%3)*2
            shard.keyframe_insert(data_path="rigid_body.kinematic",frame=frame)
            shard.rigid_body.kinematic=False
            shard.keyframe_insert(data_path="rigid_body.kinematic",frame=frame+1)
            releases.append({"name":shard.name,"release_frame":frame})
    press=cylinders(bpy,"Heavy contact head, no hands",(0,0,2.89),.53,.30,steel)
    rigid(bpy,press,"PASSIVE",shape="CONVEX_HULL")
    press.rigid_body.kinematic=True
    key(press,[(1,2.89),(18,2.68),(36,2.29),(46,2.10),(55,2.085),(66,2.11),(83,2.46),(96,2.84)])
    # Keyframe interpolation defaults stay compatible with Blender 4.5/5.x.
    shaft=cylinders(bpy,"Ram stem",(0,0,3.26),.22,.9,steel,96)
    # Coupled to press location with an explicit location constraint.
    con=shaft.constraints.new("COPY_LOCATION");con.target=press;con.use_x=True;con.use_y=True;con.use_z=True
    shaft.delta_location.z=.37
    # Decorative rings on the press, parented to moving contact head.
    collar=cylinders(bpy,"Copper press collar",(0,0,.18),.555,.04,copper)
    collar.parent=press
    collar.location=(0,0,.09)

    def lamp(name,pos,power,color,size):
        data=bpy.data.lights.new(name,"AREA");o=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(o);o.location=pos
        data.energy=power;data.color=color;data.shape="DISK";data.size=size
        look_at(o,(0,0,1.15))
    lamp("Big cool softbox",(-2.4,-2.7,4.2),540,(.80,.93,1.0),3.0)
    lamp("Warm secondary", (2.0,1.1,3.0),680,(1.0,.79,.58),2.1)
    lamp("Long glossy rim",(.6,2.7,3.1),420,(.66,.91,1.0),1.5)

    camera_data=bpy.data.cameras.new("Macro food-science camera")
    camera=bpy.data.objects.new("Deliberately locked vertical macro shot",camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location=(2.65,-4.55,2.36);look_at(camera,(0,0,1.22))
    camera_data.type="PERSP";camera_data.lens=62
    camera_data.dof.use_dof=True;camera_data.dof.focus_object=inner;camera_data.dof.aperture_fstop=8.0
    scene.camera=camera

    scene.rigidbody_world.substeps_per_frame=160
    scene.rigidbody_world.solver_iterations=35
    cache=scene.rigidbody_world.point_cache
    cache.frame_start=1;cache.frame_end=96
    scene.frame_set(24 if opt.mode=="still" else 1)
    blend=out/"original_brittle_shell_scene.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if opt.mode=="still":
        scene.render.filepath=str(out/"original_shell_lookdev.png")
        bpy.ops.render.render(write_still=True)
    else:
        # Only permit real physical motion from a baked cache, no video retiming.
        bpy.ops.ptcache.bake_all(bake=True)
        scene.render.filepath=str(out/"frames"/"shell_")
        (out/"frames").mkdir(exist_ok=True)
        scene.render.image_settings.file_format="PNG"
        bpy.ops.render.render(animation=True)
    report={
        "status":"ORIGINAL_CGI_TECHNICAL_LOOKDEV_NOT_ARTISTICALLY_APPROVED",
        "continuous_single_shot":True,
        "source_footage_used":False,
        "solver":"Blender native rigid bodies with kinematic release of actual closed mesh shell sections",
        "frame_rate":24,"frames":96,"visual_scene":"One turquoise brittle shell under steel press, revealing a contrasting textured inner core",
        "material_sound":"Brittle shell requires actual licensed sharp layered crack Foley, separated from soft core sound",
        "no_audio_added":True,
        "release_authorized":False,
        "shard_release_log":releases,
        "editable_source":blend.name,
    }
    (out/"ORIGINAL_SCENE_UNAPPROVED.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ORIGINAL_SHELL_ARTIFACT",json.dumps({"scene":str(blend),"still":str(out/"original_shell_lookdev.png")}))
if __name__=="__main__":
    build(parse())
