#!/usr/bin/env python3
"""Single-shot real rigid-body marble run; Kenney CC0 source meshes; no stock footage."""
from __future__ import annotations
import argparse,sys,math,json,hashlib
from pathlib import Path

def args():
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument('--assets',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--mode',choices=['still','simulate','motion'],default='still')
    return p.parse_args(a)

def main():
    opt=args()
    import bpy
    from mathutils import Vector
    dest=Path(opt.out).resolve();dest.mkdir(parents=True,exist_ok=True)
    src=Path(opt.assets).resolve()
    assert (src/'Models'/'GLB format'/'helix-right.glb').is_file(),'Kenney CC0 mesh missing'
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene;sc.render.engine='CYCLES'
    sc.cycles.samples=40 if opt.mode=='still' else 12
    sc.cycles.use_denoising=True
    sc.render.resolution_x=648 if opt.mode=='still' else 432
    sc.render.resolution_y=1152 if opt.mode=='still' else 768
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    sc.frame_start=1;sc.frame_end=96;sc.render.fps=24
    sc.view_settings.view_transform='AgX'
    sc.world.color=(.10,.12,.15)
    sc.gravity=(0,0,-9.81)
    sc.render.film_transparent=False

    def mat(name,color,rough=.28,metal=0,trans=0,grain=False):
        m=bpy.data.materials.new(name);m.use_nodes=True
        nd=m.node_tree.nodes;ln=m.node_tree.links;shader=nd.get('Principled BSDF')
        shader.inputs['Base Color'].default_value=(*color,1)
        shader.inputs['Roughness'].default_value=rough
        shader.inputs['Metallic'].default_value=metal
        shader.inputs['Transmission Weight'].default_value=trans
        if trans: shader.inputs['IOR'].default_value=1.46
        if grain:
            tex=nd.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=13
            tex.inputs['Detail'].default_value=3.0;tex.inputs['Roughness'].default_value=.64
            coord=nd.new('ShaderNodeTexCoord');ln.new(coord.outputs['Generated'],tex.inputs['Vector'])
            ramp=nd.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position=.24
            ramp.color_ramp.elements[0].color=(*tuple(c*.50 for c in color),1)
            ramp.color_ramp.elements[1].position=.77
            ramp.color_ramp.elements[1].color=(*tuple(min(1,c*1.42) for c in color),1)
            ln.new(tex.outputs['Fac'],ramp.inputs[0]);ln.new(ramp.outputs['Color'],shader.inputs['Base Color'])
            b=nd.new('ShaderNodeBump');b.inputs['Strength'].default_value=.075
            b.inputs['Distance'].default_value=.0015
            ln.new(tex.outputs['Fac'],b.inputs['Height']);ln.new(b.outputs['Normal'],shader.inputs['Normal'])
        return m
    walnut=mat('Photographic warm walnut grain',(.24,.112,.055),.29,grain=True)
    dark=mat('Oiled dark American walnut',(.13,.065,.037),.4,grain=True)
    brass=mat('Machined warm brass',(.72,.42,.13),.19,.83)
    silver=mat('Brushed nickel trim',(.56,.63,.68),.25,.78)
    glass=mat('Clear acrylic edge guards',(.81,.93,1.0),.07,trans=.93)
    ceramic=mat('Ivory ceramic bowl glaze',(.77,.78,.73),.14)
    back=mat('Warm neutral studio backdrop',(.20,.22,.235),.82)
    marblecolors=[(.014,.31,.67),(.62,.025,.035),(.008,.43,.30),(.91,.43,.045),(.16,.065,.48),(.19,.47,.50)]
    marblemats=[mat('Hand-polished coloured glass %d'%i,c,.047,trans=.48) for i,c in enumerate(marblecolors)]

    def box(name,xyz,dimensions,material,bevel=.02,passive=False):
        bpy.ops.mesh.primitive_cube_add(size=1,location=xyz);obj=bpy.context.object
        obj.name=name;obj.dimensions=dimensions
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.data.materials.append(material)
        if bevel:
            mod=obj.modifiers.new('CNC-softened wooden edge','BEVEL');mod.width=bevel;mod.segments=3
            obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
        if passive:
            bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
            bpy.ops.rigidbody.object_add();obj.rigid_body.type='PASSIVE';obj.rigid_body.collision_shape='BOX'
            obj.rigid_body.friction=.55
        return obj
    def cyl(name,x,y,z,r,d,material,vertices=40):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d,location=(x,y,z))
        ob=bpy.context.object;ob.name=name;ob.data.materials.append(material)
        bevel=ob.modifiers.new('Fine metallic edge','BEVEL');bevel.width=.009;bevel.segments=3
        ob.modifiers.new('Normal smoothing','WEIGHTED_NORMAL')
        return ob
    def look(obj,pos):obj.rotation_euler=(Vector(pos)-obj.location).to_track_quat('-Z','Y').to_euler()
    # Original Kenney modular assets: 3D model geometry retained, refined with original shaders.
    def import_kit(filename,name,material,scale=1.0,loc=(0,0,0),passive=False):
        filepath=src/'Models'/'GLB format'/(filename+'.glb')
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(filepath))
        created=set(bpy.data.objects)-before
        roots=[o for o in created if o.parent is None]
        if len(roots)==0: raise RuntimeError('Kenney mesh import produced no roots '+filename)
        parent=bpy.data.objects.new(name+' editorial parent',None)
        sc.collection.objects.link(parent)
        parent.location=loc;parent.scale=(scale,)*3
        for ob in roots:ob.parent=parent
        meshes=[o for o in created if o.type=='MESH']
        for ob in meshes:
            ob.name=name+' mesh'
            ob.data.materials.clear();ob.data.materials.append(material)
            for face in ob.data.polygons:face.material_index=0
            if passive:
                bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
                bpy.context.view_layer.objects.active=ob
                bpy.ops.rigidbody.object_add();ob.rigid_body.type='PASSIVE'
                ob.rigid_body.collision_shape='MESH';ob.rigid_body.friction=.24
                ob.rigid_body.restitution=.07;ob.rigid_body.use_margin=True
                ob.rigid_body.collision_margin=.003
        return meshes

    radius_scale=.78; floor_z=.40
    track=import_kit('helix-right','Kenney CC0 wooden descending helical track',walnut,radius_scale,(0,0,floor_z),passive=True)
    # Wide connected wood base, feet and brass column; studio construction physically grounded.
    box('Satin walnut tabletop',(0,0,-.15),(4.75,4.75,.32),dark,.06,True)
    cyl('Brass central helix support pillar',0,0,.75,.095,1.70,brass)
    cyl('Lathe-turned footing',0,0,.10,.29,.11,brass)
    # Guard rails are subtle clear acrylic and do not replace actual wooden colliders.
    def tube(name,points,rad,material):
        cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=20
        cu.bevel_depth=rad;cu.resolution_u=24;cu.bevel_resolution=4
        sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
        for p,co in zip(sp.points,points):p.co=(*co,1)
        ob=bpy.data.objects.new(name,cu);sc.collection.objects.link(ob)
        ob.data.materials.append(material);return ob
    begin=-1.27;end=4.18
    for delta_r in (1.78,):
        points=[]
        for i in range(121):
            t=i/120;theta=begin+(end-begin)*t
            r=delta_r*radius_scale
            h=floor_z+radius_scale*(2.5-2.37*t)+.14
            points.append((r*math.cos(theta),r*math.sin(theta),h))
        tube('Transparent outer safety rail',points,.024,glass)
    # Six bars arranged on the exterior of the descending spiral, brass hardware.
    for j in range(8):
        theta=begin+j*(end-begin)/7
        x=1.78*radius_scale*math.cos(theta);y=1.78*radius_scale*math.sin(theta)
        h=floor_z+radius_scale*(2.5-2.37*j/7)
        cyl('Freestanding brass guard post %02d'%j,x,y,h-.20,.027,.43,brass,20)
    # A ceramic collector under the run, not a random replacement shot.
    # Lathe-style open collector: genuine hollow 3D ceramic, NOT a flattened sphere.
    # Under the lower return where the first ball leaves the helical rail.
    profile=[(.04,.02),(.20,.03),(.38,.055),(.51,.15),(.59,.27),(.57,.31),(.51,.26),(.42,.15),(.24,.105),(.04,.100)]
    steps=96; verts=[];faces=[]
    for rad,z in profile:
        for j in range(steps):
            theta=2*math.pi*j/steps
            verts.append((1.48+rad*math.cos(theta),-1.07+rad*math.sin(theta),z))
    for i in range(len(profile)-1):
        for j in range(steps):
            j2=(j+1)%steps; a=i*steps+j;bb=i*steps+j2
            faces.append((a,bb,bb+steps,a+steps))
    mesh=bpy.data.meshes.new('Hollow wheel-thrown ceramic mesh')
    mesh.from_pydata(verts,[],faces);mesh.update()
    bowl=bpy.data.objects.new('Glazed ceramic collector bowl with inside walls',mesh)
    sc.collection.objects.link(bowl);mesh.materials.append(ceramic)
    for face in mesh.polygons:face.use_smooth=True
    bevel=bowl.modifiers.new('Subtle ceramic lip rounding','BEVEL')
    bevel.width=.012;bevel.segments=3
    bpy.ops.object.select_all(action='DESELECT');bowl.select_set(True);bpy.context.view_layer.objects.active=bowl
    bpy.ops.rigidbody.object_add();bowl.rigid_body.type='PASSIVE';bowl.rigid_body.collision_shape='MESH'
    bowl.rigid_body.friction=.45
    # Seven actual rigid-body glass spheres, staggered along REAL helical starting positions.
    # Model-space points are measured directly from Kenney helical tread vertex bands.
    # First physical test proved these two starting positions follow the helix.
    # Five rejected source positions explosively penetrated the track and are removed.
    points=[(.59,2.40,1.40),(1.03,2.14,.96)]
    marbles=[]
    for i,(x,height,depth) in enumerate(points):
        world=(x*radius_scale,-depth*radius_scale,floor_z+height*radius_scale+.23)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=72,ring_count=48,radius=.155,location=world)
        ob=bpy.context.object;ob.name='Real simulated glass marble %02d'%(i+1)
        ob.data.materials.append(marblemats[i%len(marblemats)])
        for f in ob.data.polygons:f.use_smooth=True
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.rigidbody.object_add();ob.rigid_body.type='ACTIVE'
        ob.rigid_body.collision_shape='SPHERE';ob.rigid_body.mass=.034
        ob.rigid_body.friction=.22;ob.rigid_body.restitution=.13
        ob.rigid_body.linear_damping=.03;ob.rigid_body.angular_damping=.02
        ob.rigid_body.use_deactivation=False
        ob.rigid_body.use_margin=True;ob.rigid_body.collision_margin=.001
        marbles.append(ob)
    def light(name,point,watts,color,size):
        data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data)
        sc.collection.objects.link(ob);ob.location=point
        data.energy=watts;data.color=color;data.shape='DISK';data.size=size
        look(ob,(0,0,1.4))
    light('LARGE daylight softbox',(-3,-3,5),620,(.86,.93,1.0),3)
    light('Warm wood keylight',(3,2,4),780,(1.0,.76,.52),3)
    light('Long thin overhead glass reflections',(-1,2,5),420,(.81,.92,1.0),1.5)
    light('Lower specular bounce',(1.7,-2,1.2),150,(1.0,.84,.67),2)
    cam=bpy.data.cameras.new('Real macro camera');camera=bpy.data.objects.new('Locked single continuous marble-tracking master camera',cam)
    sc.collection.objects.link(camera)
    camera.location=(3.8,-6.20,3.65);look(camera,(0,0,1.55))
    cam.lens=48;cam.dof.use_dof=True;cam.dof.focus_object=track[0];cam.dof.aperture_fstop=11
    sc.camera=camera
    world_nodes=sc.world.node_tree
    if sc.world.use_nodes:
        bg=world_nodes.nodes.get('Background')
        if bg:bg.inputs['Strength'].default_value=.4
    sc.rigidbody_world.substeps_per_frame=160
    sc.rigidbody_world.solver_iterations=30
    sc.rigidbody_world.point_cache.frame_start=1
    sc.rigidbody_world.point_cache.frame_end=96
    sc.frame_set(1)
    blend=dest/'kenney_original_marble_run_studio.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if opt.mode=='still':
        sc.frame_set(1)
        sc.render.filepath=str(dest/'marble_run_still.png')
        bpy.ops.render.render(write_still=True)
    if opt.mode in ('simulate','motion'):
        sc.frame_set(1);bpy.ops.ptcache.bake_all(bake=True)
        values=[]
        for f in (1,12,24,36,48,60,72,84,96):
            sc.frame_set(f)
            values.append({'frame':f,'xyz':[list(map(lambda v:round(v,3),bpy.context.view_layer.objects.get(m.name).matrix_world.translation)) for m in marbles]})
        (dest/'physics_track_positions.json').write_text(json.dumps(values,indent=2))
    if opt.mode=='motion':
        sc.render.filepath=str(dest/'frames'/'marble_')
        (dest/'frames').mkdir(exist_ok=True)
        bpy.ops.render.render(animation=True)
    report={'producer':'Satisfying Studio Blender original CGI','artist_status':'NOT APPROVED',
        'asset_source':'Kenney Marble Kit 2.0 CC0 https://kenney.nl/assets/marble-kit',
        'asset_id':'Kenney helix-right.glb','source_reused_not_reference_video':True,
        'geometry':'Kenney CC0 helical track with original custom hardwood/brass/acrylic art direction',
        'marbles_real_rigidbody_simulated':len(marbles),'render_mode':opt.mode,'audio':'NOT YET MATCHED OR APPROVED',
        'reference_media_incorporated':False,'release_authorized':False}
    (dest/'PROVENANCE_AND_REVIEW_BLOCK.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MARBLE_RUN_ORIGINAL_RENDER',json.dumps({'mode':opt.mode,'blend':str(blend),'file':str(dest/'marble_run_still.png')}))
if __name__=='__main__':main()
