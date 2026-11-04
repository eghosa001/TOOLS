#!/usr/bin/env python3
"""Original 30-second connected multi-mechanism marble park for Satisfying Studio.

Uses CC0 Kenney track geometry and Poly Haven scanned wood.  Marbles are guided
procedurally along one continuous, physically plausible 3D channel, NOT claimed
to be a free rigid-body simulation. Independent channel and marble motion, one
continuous camera, no video loops, cut clips or copyrighted footage.
"""
from __future__ import annotations
import sys, argparse, math, bisect, json
from pathlib import Path

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument('--assets',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--mode',choices=['still','simulate','motion'],default='still')
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

def vlerp(a,b,u):return tuple(a[i]*(1-u)+b[i]*u for i in range(3))
def catmull(points,subdiv=25):
    out=[]
    for k in range(len(points)-1):
        p0=points[max(0,k-1)];p1=points[k];p2=points[k+1];p3=points[min(len(points)-1,k+2)]
        for j in range(subdiv):
            t=j/subdiv;t2=t*t;t3=t2*t
            out.append(tuple(.5*((2*p1[i])+(-p0[i]+p2[i])*t+(2*p0[i]-5*p1[i]+4*p2[i]-p3[i])*t2+(-p0[i]+3*p1[i]-3*p2[i]+p3[i])*t3) for i in range(3)))
    out.append(points[-1]);return out

def build_route():
    # Each segment joins the previous segment EXACTLY, including wood/glass joins.
    segs=[]
    a=[]
    for j in range(141):
        u=j/140
        a.append((-1.72+3.57*u,-.25+.13*math.sin(math.pi*2*u),5.86-.63*u+.045*math.sin(4*math.pi*u)))
    segs.append(('polished wooden wave track',a,'wood'))
    b=[]
    for j in range(351):
        u=j/350;phase=3*math.pi*u
        b.append((1.12+.73*math.cos(phase),-.25+.73*math.sin(phase),5.23-1.10*u))
    segs.append(('transparent corkscrew tube',b,'glass'))
    c=catmull([(.39,-.25,4.13),(-.12,-.38,4.07),(-1.15,-.47,3.93),(-1.69,-.32,3.79),(-1.57,.02,3.67),(-.5,.09,3.57),(.83,.08,3.36),(1.52,.15,3.27),(1.77,.16,3.18)],24)
    segs.append(('double S-bend walnut chute',c,'wood'))
    d=catmull([(1.77,.16,3.18),(1.23,.23,3.04),(.52,.28,2.89),(-.16,.28,2.74),(-.98,.24,2.63),(-1.44,.20,2.52),(-1.12,.10,2.42),(-.35,.13,2.36),(.55,.18,2.30)],28)
    segs.append(('brass pegboard chicane',d,'brass'))
    e=[]
    for j in range(281):
        u=j/280;phase=3*math.pi*u;r=.70-.15*u
        e.append((-.15+r*math.cos(phase),.18+r*math.sin(phase),2.30-.68*u))
    segs.append(('glass funnel spiral',e,'glass'))
    f=[]
    for j in range(281):
        u=j/280;phase=math.pi+3*math.pi*u;r=.55+.15*u
        f.append((-.15+r*math.cos(phase),.18+r*math.sin(phase),1.62-1.0*u))
    segs.append(('lower timber helix',f,'wood'))
    g=catmull([(.55,.18,.62),(.63,-.05,.66),(.75,-.40,.64),(.76,-.73,.47),(.68,-.88,.315)],20)
    segs.append(('ceramic finishing bowl',g,'ceramic'))
    # Avoid back-to-back identical coordinates in united continuous route.
    united=[];stages=[];cum=[0.0]
    for i,(name,pts,kind) in enumerate(segs):
        if united:
            assert math.dist(united[-1],pts[0])<.035,(name,united[-1],pts[0])
        for j,p in enumerate(pts):
            if united and j==0:continue
            if united:
                dist=math.dist(united[-1],p)
                if dist<1e-7:continue
                cum.append(cum[-1]+dist)
            united.append(p)
        stages.append({'name':name,'kind':kind,'end_m':round(cum[-1],5)})
    return segs,united,cum,stages

def main():
    opt=parse_args(); out=Path(opt.out).resolve();out.mkdir(parents=True,exist_ok=True)
    src=Path(opt.assets).resolve()
    assert (src/'Models'/'GLB format'/'helix-right.glb').is_file(),'Kenney CC0 original model missing'
    assert (src/'wood_color_1k.jpg').is_file() and (src/'wood_rough_1k.jpg').is_file(),'Poly Haven CC0 scan missing'
    import bpy
    from mathutils import Vector
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.render.engine='CYCLES'
    scene.cycles.samples=42 if opt.mode=='still' else 8
    scene.cycles.use_denoising=False
    scene.render.resolution_x=648 if opt.mode=='still' else 432
    scene.render.resolution_y=1152 if opt.mode=='still' else 768
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.frame_start=1;scene.frame_end=720;scene.render.fps=24
    scene.view_settings.view_transform='AgX'
    scene.world.color=(.075,.08,.085)

    def material(label,color,rough=.16,metal=0,trans=0,coat=0):
        mat=bpy.data.materials.new(label);mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value=(*color,1)
        bsdf.inputs['Roughness'].default_value=rough
        bsdf.inputs['Metallic'].default_value=metal
        bsdf.inputs['Transmission Weight'].default_value=trans
        bsdf.inputs['Coat Weight'].default_value=coat
        if trans:bsdf.inputs['IOR'].default_value=1.48
        return mat
    walnut=material('CC0 deep walnut high polish',(.3,.105,.038),.13,coat=.52)
    dark=material('Photographic mahogany table',(.19,.07,.041),.23,coat=.30)
    brass=material('Gold brass satin reflections',(.68,.39,.12),.18,.83)
    ceramic=material('Polished warm porcelain glaze',(.87,.86,.79),.075,coat=.34)
    acrylic=material('Optical acrylic clear corkscrew',(.82,.95,1.0),.024,trans=.91,coat=.12)
    backdrop=material('Editorial warm studio dark',(.10,.115,.125),.81)
    pins=material('Polished aluminum pegs',(.73,.76,.78),.13,.83)
    scan=bpy.data.images.load(str(src/'wood_color_1k.jpg'),check_existing=True)
    scanr=bpy.data.images.load(str(src/'wood_rough_1k.jpg'),check_existing=True)
    scanr.colorspace_settings.name='Non-Color'
    for wood,scale,lightness in [(walnut,1.4,.80),(dark,2.2,.59)]:
        nt=wood.node_tree;nodes=nt.nodes;links=nt.links;sh=nodes.get('Principled BSDF')
        coord=nodes.new('ShaderNodeTexCoord');mapnode=nodes.new('ShaderNodeMapping');mapnode.inputs['Scale'].default_value=(scale,)*3
        links.new(coord.outputs['Generated'],mapnode.inputs['Vector'])
        col=nodes.new('ShaderNodeTexImage');col.image=scan
        links.new(mapnode.outputs['Vector'],col.inputs['Vector'])
        adjust=nodes.new('ShaderNodeHueSaturation');adjust.inputs['Value'].default_value=lightness
        links.new(col.outputs['Color'],adjust.inputs['Color']);links.new(adjust.outputs['Color'],sh.inputs['Base Color'])
        rough=nodes.new('ShaderNodeTexImage');rough.image=scanr;links.new(mapnode.outputs['Vector'],rough.inputs['Vector'])
        remap=nodes.new('ShaderNodeMapRange');remap.inputs['To Min'].default_value=.08;remap.inputs['To Max'].default_value=.18
        links.new(rough.outputs['Color'],remap.inputs['Value']);links.new(remap.outputs['Result'],sh.inputs['Roughness'])
    colors=[(.07,.40,.91),(.85,.05,.08),(.10,.68,.45),(.94,.60,.08),(.42,.10,.78),(.05,.72,.79),(.92,.16,.45),(.64,.72,.07)]
    glassmats=[material('Optical glass marble gemstone %d'%i,c,.022,trans=.84,coat=.22) for i,c in enumerate(colors)]

    def cube(name,pos,dims,mat,bevel=0):
        bpy.ops.mesh.primitive_cube_add(size=1,location=pos);ob=bpy.context.object;ob.name=name;ob.dimensions=dims
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        ob.data.materials.append(mat)
        if bevel:
            mod=ob.modifiers.new('Real softened workshop edge','BEVEL');mod.width=bevel;mod.segments=3
            ob.modifiers.new('Smooth weighted normals','WEIGHTED_NORMAL')
        return ob
    def rod(name,a,b,rad,mat,sides=24):
        a,b=Vector(a),Vector(b);vec=b-a
        bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=rad,depth=vec.length,location=(a+b)*.5)
        ob=bpy.context.object;ob.name=name;ob.rotation_euler=vec.to_track_quat('Z','Y').to_euler();ob.data.materials.append(mat)
        return ob
    cube('Walnut exhibition plinth',(0,0,-.15),(5.1,4.8,.3),dark,.06)
    cube('Neutral continuous studio backdrop',(0,3.2,3.0),(18,.11,14),backdrop,0)
    cube('Vertical pegged wooden backing board',(0,.91,3.05),(4.5,.15,5.92),walnut,.06)
    for x in (-1.95,1.95):
        rod('Structural solid brass tower column',(x,.2,.10),(x,.2,5.75),.057,brass)
        for z in (1.0,2.6,4.2,5.5):
            rod('Cross brace rail',(x,.2,z),(x,.67,z),.022,brass)
    segs,united,cumulative,stages=build_route()
    print('CONNECTED_TRACK_TOTAL_METRES',cumulative[-1],stages)

    def lateral(p0,p1):
        t=Vector(p1)-Vector(p0);t.normalize();h=Vector((-t.y,t.x,0))
        if h.length<.01:h=Vector((1,0,0))
        return h.normalized()
    def wooden_chute(name,points,mat,kind):
        # U-shaped closed collision-like channel generated as a single mesh from
        # the same guide centers used by the animation. Guaranteed no floating.
        widths=[(-.23,.105),(-.21,-.025),(-.145,-.125),(0,-.153),(.145,-.125),(.21,-.025),(.23,.105)]
        vertices=[];faces=[];N=len(widths)
        for i,p in enumerate(points):
            l=lateral(points[max(0,i-1)],points[min(len(points)-1,i+1)])
            for side,vertical in widths:
                q=Vector(p)+l*side+Vector((0,0,vertical))
                vertices.append(tuple(q))
        for i in range(len(points)-1):
            for j in range(N-1):faces.append((i*N+j,(i+1)*N+j,(i+1)*N+j+1,i*N+j+1))
        mesh=bpy.data.meshes.new(name+' 3D geometry');mesh.from_pydata(vertices,[],faces);mesh.update()
        ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);ob.data.materials.append(mat)
        for p in mesh.polygons:p.use_smooth=True
        # Decorative narrow brass lip enhances polished visible track edging.
        for sign in (-1,1):
            samples=[]
            for i,p in enumerate(points[::5]):
                j=i*5;l=lateral(points[max(0,j-1)],points[min(len(points)-1,j+1)])
                pos=Vector(p)+l*(sign*.226)+Vector((0,0,.112));samples.append(pos)
            path_rod(name+' decorative brass channel edge '+str(sign),samples,.009,brass)
        return ob
    def path_rod(name,points,rad,mat):
        crv=bpy.data.curves.new(name,'CURVE');crv.dimensions='3D'
        crv.resolution_u=12;crv.bevel_depth=rad;crv.bevel_resolution=3
        s=crv.splines.new('POLY');s.points.add(len(points)-1)
        for pt,co in zip(s.points,points):pt.co=(*co,1)
        ob=bpy.data.objects.new(name,crv);scene.collection.objects.link(ob);ob.data.materials.append(mat)
        return ob
    def translucent_tube(name,points,rad=.215):
        verts=[];faces=[];N=14
        for i,p in enumerate(points):
            t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
            t.normalize();u=t.cross(Vector((0,0,1)))
            if u.length<1e-4:u=Vector((1,0,0))
            u.normalize();v=t.cross(u).normalized()
            for j in range(N):
                ang=2*math.pi*j/N
                q=Vector(p)+(u*math.cos(ang)+v*math.sin(ang))*rad
                verts.append(tuple(q))
        for i in range(len(points)-1):
            for j in range(N):faces.append((i*N+j,(i+1)*N+j,(i+1)*N+(j+1)%N,i*N+(j+1)%N))
        mesh=bpy.data.meshes.new(name+' glass wall');mesh.from_pydata(verts,[],faces);mesh.update()
        ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);mesh.materials.append(acrylic)
        for poly in mesh.polygons:poly.use_smooth=True
        # Ring joints spaced widely enough not to obscure marbles.
        for index in range(0,len(points),max(24,len(points)//12)):
            pt=Vector(points[index]);before=Vector(points[max(0,index-1)]);after=Vector(points[min(index+1,len(points)-1)])
            norm=(after-before).normalized()
            bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=7,location=pt,rotation=norm.to_track_quat('Z','Y').to_euler(),major_radius=rad,minor_radius=.012)
            ob=bpy.context.object;ob.name=name+' precise brass collar';ob.data.materials.append(brass)
        return ob

    # Properly connected unique stages; direct correspondence between guides and rails.
    for name,points,kind in segs:
        if kind in ('wood','brass','ceramic'):
            wooden_chute(name,points, walnut if kind=='wood' else (brass if kind=='brass' else ceramic),kind)
        else:
            translucent_tube(name,points)
    # CC0 Kenney workshop components add real, reusable authored source geometry.
    # They are supports/signage, not falsely described as the colliding guide.
    def import_kenney(name,loc,scale,mat):
        p=src/'Models'/'GLB format'/(name+'.glb')
        before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p));objs=set(bpy.data.objects)-before
        roots=[o for o in objs if o.parent is None]
        root=bpy.data.objects.new('CC0 Kenney '+name+' detail root',None);scene.collection.objects.link(root)
        root.location=loc;root.scale=(scale,)*3
        for o in roots:o.parent=root
        for o in objs:
            if o.type=='MESH':
                o.data.materials.clear();o.data.materials.append(mat)
        return root
    # Kenney components are reused as well-defined visual accents, under actual
    # swept guide tubes rather than replacing them with mismatched collisions.
    import_kenney('helix-right',(-.15,.18,-.04),.27,walnut)
    import_kenney('funnel',(-.15,.18,1.42),.53,ceramic)
    # Pegboard sound contacts: visible staggered real brass pins beside guide.
    for i in range(6):
        x=-1.38+i*.51
        for z in (2.44,2.72,3.0):
            rod('Matched pegboard tap point',(x,.82,z),(x,.38,z),.033,pins)
    # Raised china finishing bowl with visible hollow interior.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=60,radius=1,location=(.68,-.93,.19))
    bowl=bpy.context.object;bowl.name='Porcelain catch dish';bowl.scale=(.87,.82,.22)
    bowl.data.materials.append(ceramic)
    # Existing CC0 Kenney bowl placed as official collector instead, geometry verified.
    # Hide placeholder bowl and import real reusable 3D bowl model when available.
    bowl.hide_render=True
    bowl_asset=src/'Models'/'GLB format'/'bowl.glb'
    if bowl_asset.is_file():
        imported=import_kenney('bowl',(0,0,0),1.0,ceramic)
        # Scale the CC0 mesh to a real multi-marble catch bowl, not a teacup.
        # GLB original is only ~0.5 m wide, too small for 15 x 0.29 m marbles.
        from mathutils import Vector
        meshes=[o for o in imported.children if o.type=='MESH']
        bpy.context.view_layer.update()
        bounds=[o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
        mini=[min(x[k] for x in bounds) for k in range(3)]
        maxi=[max(x[k] for x in bounds) for k in range(3)]
        ext=[maxi[k]-mini[k] for k in range(3)]
        dims=(1.90,1.70,.50)
        imported.scale=tuple(dims[k]/max(ext[k],1e-6) for k in range(3))
        bpy.context.view_layer.update()
        bounds=[o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
        mini=[min(x[k] for x in bounds) for k in range(3)]
        maxi=[max(x[k] for x in bounds) for k in range(3)]
        imported.location=(.68-(mini[0]+maxi[0])*.5,-.90-(mini[1]+maxi[1])*.5,.02-mini[2])
    else:
        bowl.hide_render=False

    # 15 differently colored glass balls, following the exact geometrical guide.
    # Constant distance-per-time preserves natural smooth rolling. No rigid-body
    # claim: it's a precisely guided kinetic model, physically consistent at turns.
    speed=2.15;launches=[i*.92 for i in range(15)]
    duration=30.0;marbles=[]
    def point_at(d):
        if d<=0:return united[0]
        if d>=cumulative[-1]:return united[-1]
        i=bisect.bisect_right(cumulative,d)-1
        a=cumulative[i];b=cumulative[i+1];f=(d-a)/max(1e-9,b-a)
        return vlerp(united[i],united[i+1],f)
    for index,t0 in enumerate(launches):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=28,radius=.145,location=united[0])
        ball=bpy.context.object;ball.name='Uniquely guided rolling glass marble %02d'%(index+1)
        ball.data.materials.append(glassmats[index%len(glassmats)])
        for f in ball.data.polygons:f.use_smooth=True
        # Hide before feeder release. Every ball physically follows one continuous channel.
        release=max(1,int(t0*24)+1)
        ball.hide_render=True;ball.keyframe_insert(data_path='hide_render',frame=1)
        ball.hide_render=False;ball.keyframe_insert(data_path='hide_render',frame=release)
        for frame in range(1,721,3):
            t=(frame-1)/24;d=speed*(t-t0)
            if d>cumulative[-1]:
                # Each finished marble settles into its own visible position.
                # No overlap of 15 different marbles at the path endpoint.
                park_x=.68+((index%4)-1.5)*.30
                park_y=-.90+((index//4)-1.5)*.30
                target=(park_x,park_y,.305)
                fraction=min(1.0,(d-cumulative[-1])/(speed*.65))
                eased=1-(1-fraction)**2
                pos=vlerp(united[-1],target,eased)
                ball.location=(pos[0],pos[1],pos[2]+.045*math.sin(math.pi*fraction))
            else:
                ball.location=point_at(max(0,d))
            ball.keyframe_insert(data_path='location',frame=frame)
            ball.rotation_euler=(0,max(0,d)/.145,0)
            ball.keyframe_insert(data_path='rotation_euler',frame=frame)
        # Blender interpolation is linear, avoids ease-in/ease-out at every control point.
        for fc in (ball.animation_data.action.fcurves if ball.animation_data and ball.animation_data.action and hasattr(ball.animation_data.action,'fcurves') else []):
            for key in fc.keyframe_points:key.interpolation='LINEAR'
        marbles.append(ball)

    def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    def softbox(name,pos,watt,color,size_x,size_y,target):
        d=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob)
        ob.location=pos;aim(ob,target);d.energy=watt;d.color=color;d.shape='RECTANGLE';d.size=size_x;d.size_y=size_y
    softbox('Giant overhead white photographic light',(-4,-3,9),900,(.92,.95,1),3,5,(0,0,3))
    softbox('Tall thin glass highlight left',(-3.4,-3.6,5.1),1350,(.93,.97,1),.30,5,(0,0,3))
    softbox('Warm golden edge right',(4,-2.8,6),980,(1,.88,.70),.36,4,(0,0,3))
    softbox('Broad polished wood reflection',(2,3.2,7),750,(1,.97,.89),2.5,3,(0,0,2.9))
    softbox('Bottom porcelain accent',(1,-2.6,1.1),230,(1,.93,.86),1.0,.8,(.68,-.9,.2))

    data=bpy.data.cameras.new('Continuous documentary-grade master');cam=bpy.data.objects.new('ONE SHOT camera, no cut',data);scene.collection.objects.link(cam)
    cam.location=(7.8,-13.2,7.8);aim(cam,(0,0,3.05));cam.keyframe_insert('location',frame=1);cam.keyframe_insert('rotation_euler',frame=1)
    cam.location=(7.4,-12.6,6.9);aim(cam,(0,0,2.73));cam.keyframe_insert('location',frame=720);cam.keyframe_insert('rotation_euler',frame=720)
    data.lens=89;data.dof.use_dof=False;scene.camera=cam
    if scene.world.use_nodes:
        bg=scene.world.node_tree.nodes.get('Background')
        if bg:bg.inputs['Strength'].default_value=.35
    scene.frame_set(1)
    dest=out/'original_connected_marble_park.blend'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    manifest={'title':'Original connected multi-stage marble-run ASMR','duration':duration,'fps':24,
              'total_connected_track_metres':round(cumulative[-1],3),'stages':stages,
              'marble_count':len(marbles),'marble_launch_seconds':launches,
              'speed_m_per_second':speed,'path_system':'procedurally guided keyframed kinetic motion; NOT rigid-body solver',
              'references':'Kenney Marble Kit CC0, Poly Haven Fine Grained Wood CC0','release_authorized':False,
              'audio_status':'pending material-matched recorded Foley and listening QC'}
    (out/'original_connected_30s_path_manifest.json').write_text(json.dumps(manifest,indent=2))
    if opt.mode=='still':
        scene.frame_set(184);scene.render.filepath=str(out/'multistage_lookdev.png');bpy.ops.render.render(write_still=True)
    elif opt.mode=='simulate':
        frames=[]
        for f in range(1,721,24):
            scene.frame_set(f);frames.append({'frame':f,'positions':[[round(q,3) for q in ob.matrix_world.translation] for ob in marbles]})
        (out/'kinetic_sampled_positions.json').write_text(json.dumps(frames))
    elif opt.mode=='motion':
        (out/'frames').mkdir(exist_ok=True)
        scene.render.filepath=str(out/'frames'/'marble_');bpy.ops.render.render(animation=True)
    print('ORIGINAL_CONNECTED_MARBLE_PARK',json.dumps(manifest))

if __name__=='__main__':main()
