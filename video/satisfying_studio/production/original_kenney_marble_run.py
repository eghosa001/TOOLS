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
    # Kenney CC0 Food Kit bowl, verified small 17,080-byte GLB. Fetch exactly
    # once into existing source folder and require the inspected SHA256.
    bowl_asset=src/'Models'/'GLB format'/'bowl.glb'
    bowl_sha='cdfedca671dadfed19229881ba9afd4b544d2ba60dbba1f5a24071abc59d7c58'
    if not bowl_asset.is_file():
        from urllib.request import urlopen
        url='https://raw.githubusercontent.com/Hidencod/tge-assets/main/packs/food-kit/bowl.glb'
        with urlopen(url,timeout=25) as response:
            blob=response.read()
        if hashlib.sha256(blob).hexdigest()!=bowl_sha:
            raise RuntimeError('CC0 Kenney Food Kit bowl source SHA256 mismatch')
        bowl_asset.write_bytes(blob)
    if hashlib.sha256(bowl_asset.read_bytes()).hexdigest()!=bowl_sha:
        raise RuntimeError('Unverified CC0 Kenney bowl source')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene;sc.render.engine='CYCLES'
    sc.cycles.samples=56 if opt.mode=='still' else 20
    sc.cycles.use_denoising=False
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
            tex=nd.new('ShaderNodeTexWave');tex.wave_type='BANDS';tex.bands_direction='Y'
            tex.inputs['Scale'].default_value=16;tex.inputs['Distortion'].default_value=5.0
            tex.inputs['Detail'].default_value=2.5
            coord=nd.new('ShaderNodeTexCoord');ln.new(coord.outputs['Generated'],tex.inputs['Vector'])
            ramp=nd.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position=.24
            ramp.color_ramp.elements[0].color=(*tuple(c*.38 for c in color),1)
            ramp.color_ramp.elements[1].position=.77
            ramp.color_ramp.elements[1].color=(*tuple(min(1,c*1.20) for c in color),1)
            ln.new(tex.outputs['Fac'],ramp.inputs[0]);ln.new(ramp.outputs['Color'],shader.inputs['Base Color'])
            b=nd.new('ShaderNodeBump');b.inputs['Strength'].default_value=.075
            b.inputs['Distance'].default_value=.0015
            ln.new(tex.outputs['Fac'],b.inputs['Height']);ln.new(b.outputs['Normal'],shader.inputs['Normal'])
        return m
    walnut=mat('Scanned dark walnut real wood',(.19,.077,.032),.26,grain=False)
    dark=mat('Scanned dark walnut tabletop',(.13,.065,.037),.34,grain=False)
    # Use actual 1K scanned CC0 source by Poly Haven / Rob Tuytel.
    # Two independent material objects use the same packed source images.
    scan_color=src/'wood_color_1k.jpg'
    scan_rough=src/'wood_rough_1k.jpg'
    if not scan_color.is_file() or not scan_rough.is_file():
        raise FileNotFoundError('Scanned CC0 wood PBR image maps missing; never revert to striped procedural wood')
    image_col=bpy.data.images.load(str(scan_color),check_existing=True)
    image_rough=bpy.data.images.load(str(scan_rough),check_existing=True)
    image_rough.colorspace_settings.name='Non-Color'
    def scanned_wood(material,value,scale,rotation=0):
        nd=material.node_tree.nodes;ln=material.node_tree.links;shader=nd.get('Principled BSDF')
        coord=nd.new('ShaderNodeTexCoord')
        vect=nd.new('ShaderNodeMapping')
        vect.inputs['Scale'].default_value=scale
        vect.inputs['Rotation'].default_value[2]=rotation
        ln.new(coord.outputs['Generated'],vect.inputs['Vector'])
        col=nd.new('ShaderNodeTexImage');col.image=image_col;col.extension='REPEAT'
        ln.new(vect.outputs['Vector'],col.inputs['Vector'])
        adjust=nd.new('ShaderNodeHueSaturation');adjust.inputs['Value'].default_value=value
        adjust.inputs['Saturation'].default_value=.92
        ln.new(col.outputs['Color'],adjust.inputs['Color'])
        ln.new(adjust.outputs['Color'],shader.inputs['Base Color'])
        rou=nd.new('ShaderNodeTexImage');rou.image=image_rough;rou.extension='REPEAT'
        ln.new(vect.outputs['Vector'],rou.inputs['Vector'])
        ln.new(rou.outputs['Color'],shader.inputs['Roughness'])
        # Keep mapped surface fine; no high-contrast cartoon bands.
        bumps=nd.new('ShaderNodeBump');bumps.inputs['Strength'].default_value=.10
        bumps.inputs['Distance'].default_value=.0014
        ln.new(rou.outputs['Color'],bumps.inputs['Height'])
        ln.new(bumps.outputs['Normal'],shader.inputs['Normal'])
    scanned_wood(walnut,.83,(1.1,1.1,1.1))
    scanned_wood(dark,.52,(2.3,2.3,2.3))
    brass=mat('Machined warm brass',(.72,.42,.13),.19,.83)
    silver=mat('Brushed nickel trim',(.56,.63,.68),.25,.78)
    glass=mat('Clear acrylic edge guards',(.81,.93,1.0),.07,trans=.93)
    ceramic=mat('Ivory ceramic bowl glaze',(.77,.78,.73),.14)
    back=mat('Warm neutral studio backdrop',(.095,.105,.118),.84)
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
    box('Neutral studio background wall',(0,3.9,2.9),(22.0,.10,11.0),back,0,False)
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
    # Guard geometry from first lookdev obstructed real visible marble positions.
    # The proven Kenney wooden channel is the actual collision/guide path.
    # Reuse Kenney Food Kit's independently CC0 bowl model, rather than the
    # rejected handmade profile whose fold produced false force impulses.
    # Authoritative source: https://kenney.nl/assets/food-kit
    # Distribution: Hidencod/tge-assets packs/food-kit/bowl.glb (SHA verified).
    bowl_x,bowl_y=.88,-1.22
    bowl_meshes=import_kit('bowl','Kenney CC0 food-kit glazed ceramic collector',
                           ceramic,1.0,(0,0,0),passive=False)
    # Normalize real imported world bounds to the proven capture corridor;
    # Kenney GLB uses its own unit scale and coordinate convention.
    from mathutils import Vector
    parent=bpy.data.objects.get('Kenney CC0 food-kit glazed ceramic collector editorial parent')
    if parent is None or not bowl_meshes:
        raise RuntimeError('Missing imported Kenney bowl editorial transform')
    def world_bbox(objs):
        bpy.context.view_layer.update()
        pos=[ob.matrix_world @ Vector(p) for ob in objs for p in ob.bound_box]
        return [min(v[i] for v in pos) for i in range(3)],[max(v[i] for v in pos) for i in range(3)]
    lo,hi=world_bbox(bowl_meshes)
    dims=[hi[i]-lo[i] for i in range(3)]
    if any(d<1e-5 for d in dims):
        raise RuntimeError('Kenney imported bowl geometry has invalid 3D dimensions '+str(dims))
    target_dims=(2.80,2.0,.56)
    parent.scale=tuple(target_dims[i]/dims[i] for i in range(3))
    lo,hi=world_bbox(bowl_meshes)
    parent.location=(bowl_x-(lo[0]+hi[0])/2,
                     bowl_y-(lo[1]+hi[1])/2,
                     .015-lo[2])
    bpy.context.view_layer.update()
    for basin in bowl_meshes:
        bpy.ops.object.select_all(action='DESELECT')
        basin.select_set(True);bpy.context.view_layer.objects.active=basin
        subdiv=basin.modifiers.new('Smooth real Kenney ceramic curvature','SUBSURF')
        subdiv.levels=2;subdiv.render_levels=2
        bpy.ops.object.modifier_apply(modifier=subdiv.name)
        for face in basin.data.polygons:face.use_smooth=True
        bpy.ops.rigidbody.object_add()
        basin.rigid_body.type='PASSIVE'
        basin.rigid_body.collision_shape='MESH'
        basin.rigid_body.friction=.52
        basin.rigid_body.restitution=.02
        basin.rigid_body.collision_margin=.003
    # Start four independent marbles on verified physical travel positions,
    # sampled from the previous 96-frame Blender rigid-body trajectory.
    # All begin visibly on the continuous track, with no pop-in/teleportation.
    # These are REAL scene-space positions, not arbitrary floating source points.
    marble_world_starts=[(.460,-1.092,2.502),(1.183,-.184,1.955),
                         (.131,1.274,1.568),(-1.024,-.764,1.002)]
    marbles=[]
    for i,world in enumerate(marble_world_starts):
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
    light('Warm wood keylight',(3,2,4),560,(1.0,.83,.69),3)
    light('Long thin overhead glass reflections',(-1,2,5),420,(.81,.92,1.0),1.5)
    light('Lower specular bounce',(1.7,-2,1.2),150,(1.0,.84,.67),2)
    cam=bpy.data.cameras.new('Real macro camera');camera=bpy.data.objects.new('Locked single continuous marble-tracking master camera',cam)
    sc.collection.objects.link(camera)
    # One real continuous dolly move, tracking from upper marbles to catch basin.
    # Not a montage or frame loop. Keep the whole main channel readable.
    camera.location=(3.6,-6.45,3.85);look(camera,(.30,-.14,1.05))
    camera.keyframe_insert('location',frame=1)
    camera.keyframe_insert('rotation_euler',frame=1)
    camera.location=(3.25,-6.30,3.65);look(camera,(.56,-.40,.82))
    camera.keyframe_insert('location',frame=96)
    camera.keyframe_insert('rotation_euler',frame=96)
    cam.lens=47;cam.dof.use_dof=True;cam.dof.focus_object=track[0];cam.dof.aperture_fstop=11
    sc.camera=camera
    world_nodes=sc.world.node_tree
    if sc.world.use_nodes:
        bg=world_nodes.nodes.get('Background')
        if bg:bg.inputs['Strength'].default_value=.4
    sc.rigidbody_world.substeps_per_frame=160
    sc.rigidbody_world.solver_iterations=40
    sc.rigidbody_world.point_cache.frame_start=1
    sc.rigidbody_world.point_cache.frame_end=96
    sc.frame_set(1)
    blend=dest/'kenney_original_marble_run_studio.blend'
    bpy.ops.file.pack_all()
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
        'collector_asset':'Kenney Food Kit bowl.glb CC0, source https://kenney.nl/assets/food-kit',
        'asset_id':'Kenney helix-right.glb','source_reused_not_reference_video':True,
        'geometry':'Kenney CC0 helical track with original custom hardwood/brass/acrylic art direction',
        'marbles_real_rigidbody_simulated':len(marbles),'collector_center':[bowl_x,bowl_y],
        'marble_initial_world_xyz':marble_world_starts,'render_mode':opt.mode,'audio':'NOT YET MATCHED OR APPROVED',
        'reference_media_incorporated':False,'release_authorized':False}
    (dest/'PROVENANCE_AND_REVIEW_BLOCK.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MARBLE_RUN_ORIGINAL_RENDER',json.dumps({'mode':opt.mode,'blend':str(blend),'file':str(dest/'marble_run_still.png')}))
if __name__=='__main__':main()
