"""Original reusable stylized 3D characters and Sunpatch Court Blender set.

Pure Blender Python; assets are authored procedurally (not text-to-3D AI).
The returning cast retains its silhouette and costume colours while the
body colour can use any value accepted by studio_contract.rgba().
"""
from __future__ import annotations

import math
import bpy
from mathutils import Vector
from cartoon_studio.studio_contract import rgba

PROFILES = {
    "lelli": {"kind": "pear", "straps": "#754987", "cheeks": "#fff1d9"},
    "brin": {"kind": "tall", "sash": "#203b72", "brows": "#3498cf"},
    "odo": {"kind": "round", "flaps": "#8750ad", "collar": "#f4cf6a"},
}


def material(name, color, roughness=0.76):
    existing = bpy.data.materials.get("CartoonStudio_" + name)
    if existing:
        return existing
    item = bpy.data.materials.new("CartoonStudio_" + name)
    item.diffuse_color = rgba(color)
    item.use_nodes = True
    bsdf = item.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = item.diffuse_color
        bsdf.inputs["Roughness"].default_value = roughness
    return item


def pivot(name, location, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


def sphere(name, xyz, scale, mat, parent=None, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = xyz
    obj.scale = scale
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def block(name, xyz, size, mat, parent=None, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = xyz
    obj.dimensions = size
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Soft clay corners", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def tube(name, coordinates, radius, mat, parent=None):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(coordinates)-1)
    for point, coords in zip(spline.points, coordinates):
        point.co = (*coords, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    curve.materials.append(mat)
    return obj


def _eyes(name, head, z, face_y, x_distance, iris_color, brow_material, cheek_material=None):
    eyes = []
    white = material("eye_white", "#fffcf5")
    shine = material("eye_shine", "#ffffff", 0.28)
    dark = material("face_dark", "#272334")
    iris = material(name+"_iris", iris_color)
    for side in (-1, 1):
        eye = sphere(f"{name}_eye_{side}", (side*x_distance, face_y, z),
                     (.145,.076,.17), white, head)
        sphere(f"{name}_iris_{side}", (side*x_distance, face_y-.070, z-.012),
               (.081,.035,.10), iris, head)
        sphere(f"{name}_pupil_{side}", (side*x_distance, face_y-.101, z-.012),
               (.046,.015,.066), dark, head)
        sphere(f"{name}_glint_{side}", (side*x_distance-.023,face_y-.120,z+.035),
               (.017,.009,.026), shine, head)
        brow = sphere(f"{name}_brow_{side}", (side*x_distance,face_y-.012,z+.22),
               (.13,.038,.037), brow_material, head)
        brow.rotation_euler[1] = .09*side
        if cheek_material:
            sphere(f"{name}_cheek_{side}", (side*(x_distance+.18),face_y+.03,z-.2),
                   (.092,.032,.074), cheek_material, head)
        eyes.append(eye)
    return eyes


def _arms(name, root, material_body, spread, shoulder_height, length):
    arms = []
    for side in (-1, 1):
        arm = pivot(f"{name}_arm_pivot_{side}", (side*spread,0,shoulder_height),root)
        sphere(f"{name}_arm_{side}", (side*.07,-.015,-length*.45),
               (.15,.14,length*.58), material_body, arm)
        sphere(f"{name}_hand_{side}", (side*.13,-.045,-length*.87),
               (.14,.135,.15), material_body, arm)
        arms.append(arm)
    return arms


def _feet(name, root, body_mat, half_gap, height):
    for side in (-1, 1):
        sphere(f"{name}_leg_{side}", (side*half_gap,0,height*.60),
               (.14,.18,height*.47), body_mat, root)
        sphere(f"{name}_shoe_{side}", (side*half_gap,-.13,.145),
               (.19,.28,.135), material("shoe", "#544353"),root)


def make_character(name, x, colour):
    """Return a drop-in actor rig for legacy speech/gesture keyframing.

    Parent pivots animate head, hands and whole body. These are mesh puppets,
    not skeletal GLBs or advanced facial blend-shape rigs.
    """
    if name not in PROFILES:
        return None
    body = material(name+"_body_"+str(colour), colour)
    root = pivot(name, (x,0,0))
    head = pivot(f"{name}_head_pivot", (0,0,0),root)
    kind = PROFILES[name]["kind"]
    dark = material("dark_mouth", "#44263e")
    pink = material("tongue_pink", "#ed899f")
    if kind == "pear":
        sphere(f"{name}_pear_body", (0,0,1.04),(.56,.39,.74),body,root,32,20)
        sphere(f"{name}_head", (0,-.015,1.91),(.51,.405,.47),body,head,32,20)
        mouth_z,face_y = 1.68,-.402
        brows = material("lelli_brow", "#276d77")
        cheeks = material("cream_cheek", "#fff1d9")
        _eyes(name,head,1.98,face_y,.18,"#4b456b",brows,cheeks)
        purple = material("lelli_plum_straps", PROFILES[name]["straps"])
        for side in (-1,1):
            tube(f"{name}_strap_{side}",[
                (side*.28,-.35,1.51),(side*.24,-.45,1.28),
                (side*.26,-.42,1.04)],.057,purple,root)
        sphere(f"{name}_curl_1",(-.15,-.03,2.33),(.20,.17,.19),body,head)
        sphere(f"{name}_curl_2",(.07,-.05,2.42),(.18,.18,.17),body,head)
        arms = _arms(name,root,body,.48,1.39,.58)
        _feet(name,root,body,.22,.79)
    elif kind == "tall":
        sphere(f"{name}_torso",(0,0,1.37),(.34,.30,.88),body,root,28,20)
        block(f"{name}_flat_head",(0,-.02,2.35),(.72,.59,.59),body,head,.22)
        mouth_z,face_y=2.17,-.338
        _eyes(name,head,2.41,face_y,.17,"#584a2f",
              material("brin_blue_brow","#3498cf"))
        sash=material("brin_navy_sash",PROFILES[name]["sash"])
        tube(f"{name}_navy_sash",[(-.25,-.295,1.99),
             (.25,-.35,1.29),(.19,-.315,.98)],.065,sash,root)
        arms=_arms(name,root,body,.34,1.82,.70)
        _feet(name,root,body,.17,.97)
    else:
        sphere(f"{name}_round_body",(0,0,.97),(.61,.40,.65),body,root,32,20)
        sphere(f"{name}_head",(0,-.02,1.75),(.52,.41,.42),body,head,32,20)
        mouth_z,face_y=1.55,-.409
        _eyes(name,head,1.81,face_y,.18,"#60435f",
              material("odo_brow","#98515d"))
        violet=material("odo_violet_flaps",PROFILES[name]["flaps"])
        for side in (-1,1):
            flap=sphere(f"{name}_side_flap_{side}",(side*.53,.03,1.91),
                        (.17,.14,.33),violet,head)
            flap.rotation_euler[1]=side*.36
        collar=material("odo_yellow_collar",PROFILES[name]["collar"])
        tube(f"{name}_collar",[(-.36,-.27,1.44),(-.21,-.39,1.39),
             (0,-.43,1.37),(.21,-.39,1.39),(.36,-.27,1.44)],.065,collar,root)
        arms=_arms(name,root,body,.53,1.25,.52)
        _feet(name,root,body,.23,.68)
    mouth=sphere(f"{name}_mouth",(0,face_y-.015,mouth_z),
                 (.17,.03,.025),dark,head)
    tongue=sphere(f"{name}_tongue",(0,face_y-.04,mouth_z-.055),
                  (.09,.015,.012),pink,head)
    # A thin curved smile is visible around the dark lip-sync mouth.
    smile=material("smile_line","#563949")
    tube(f"{name}_smile",[
        (-.22,face_y-.032,mouth_z+.01),
        (-.15,face_y-.04,mouth_z-.055),
        (0,face_y-.045,mouth_z-.07),
        (.15,face_y-.04,mouth_z-.055),
        (.22,face_y-.032,mouth_z+.01)],.012,smile,head)
    return {"root":root,"head":head,"mouth":mouth,"tongue":tongue,
            "arms":arms,"profile":kind}


def _potted_daisy():
    clay = material("terracotta", "#cf7850")
    leaf = material("garden_leaf", "#459a56")
    cream = material("daisy_white", "#fff9e4")
    center = material("daisy_center", "#e8b33a")
    bpy.ops.mesh.primitive_cone_add(vertices=18,radius1=.36,radius2=.26,
                                    depth=.42,location=(2.9,1.15,.24))
    pot=bpy.context.object
    pot.name="Court_single_daisy_terracotta_pot"
    pot.data.materials.append(clay)
    sphere("Court_daisy_soil",(2.9,1.15,.445),(.24,.24,.035),
           material("soil","#665141"))
    tube("Court_daisy_stem",[(2.9,1.15,.43),(2.88,1.13,1.09)],.045,leaf)
    for side in (-1,1):
        blade=sphere("Court_daisy_leaf",(2.9+side*.12,1.15, .75),
                     (.16,.065,.06),leaf)
        blade.rotation_euler[1]=side*.45
    for i in range(9):
        angle=i*math.tau/9
        sphere(f"Court_daisy_petal_{i}",
               (2.88+math.cos(angle)*.17,1.05,1.12+math.sin(angle)*.17),
               (.112,.05,.083),cream,segments=14,rings=9)
    sphere("Court_daisy_yellow_middle",(2.88,1.0,1.12),
           (.11,.055,.11),center)


def build_sunpatch_court():
    """Prepare the recurring fixed garden set from original Blender meshes."""
    pale=material("court_sandstone","#e9cda0")
    green=material("court_sage_grass","#7cad75")
    fence=material("court_fence_yellow","#f4cd68")
    hedge=material("court_hedge","#539960")
    gravel=material("court_stones","#e7d9ba")
    block("Court_grass", (0,1,-.13), (14,12,.23),green,None,.07)
    block("Court_path_base",(0,.2,-.007), (2.0,7,.045),
          material("path_soil","#c7ae83"),None,.04)
    for i in range(11):
        y=-2.80+i*.56
        x=.09*math.sin(i*1.7)
        sphere(f"Court_stepping_stone_{i}",(x,y,.024),
               (.56,.28,.067),gravel,None,16,9)
    # The low enclosure reads as a garden, not the generic woodland backdrop.
    for x in [i*.8 for i in range(-7,8)]:
        block("Court_rear_fence_picket",(x,3.53,.67),
              (.18,.14,1.35),fence,None,.04)
    for x in (-5.9,5.9):
        for y in (-2.7,3.5):
            block("Court_corner_fence_post",(x,y,.75),
                  (.21,.24,1.48),fence,None,.06)
    for z in (.42,.92):
        block("Court_rear_fence_rail",(0,3.67,z),(12.1,.14,.12),fence,None,.03)
    for x in (-5.0,-4.2,4.2,5.0):
        for i,y in enumerate((2.45,2.95)):
            sphere("Court_hedge_round",(x+.12*i,y,.37),(.52,.37,.48),
                   hedge,None,18,10)
    for x in (-4.65,4.75):
        tube("Court_little_tree_stem",[(x,2.3,.0),(x,2.3,1.9)],
             .13,material("tree_wood","#866b53"))
        for shift in ((0,0,2.4),(.36,0,2.13),(-.33,0,2.1)):
            sphere("Court_tree_top",(x+shift[0],2.3,shift[2]),
                   (.65,.49,.65),hedge,None,18,10)
    _potted_daisy()
    blue=material("watering_can","#4b94bd",.44)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.28,depth=.42,
                                        location=(-2.95,1.1,.28))
    can=bpy.context.object
    can.name="Court_blue_enamel_watering_can"
    can.data.materials.append(blue)
    tube("Court_watering_can_handle",[(-3.18,1.1,.44),(-3.32,1.1,.62),
         (-3.47,1.1,.50),(-3.45,1.1,.32)],.045,blue)
    tube("Court_watering_can_spout",[(-2.70,1.1,.37),(-2.43,1.1,.45),
         (-2.30,1.1,.61)],.052,blue)
    card=material("route_card","#fdf1cf")
    block("Court_handdrawn_route_card",(3.25,-.62,.15),
          (.54,.72,.028),card,None,.024)
    ink=material("route_ink","#7f6a52")
    for i in range(3):
        tube(f"Court_route_card_mark_{i}",[
            (3.12+i*.07,-.84,.17),(3.12+i*.08,-.38,.17)],.009,ink)
    pole=material("little_flag_pole","#937354")
    tube("Court_parade_flag_pole",[(3.68,.85,0),(3.68,.85,1.75)],.035,pole)
    dots=(material("flag_turquoise","#18aabb"),
          material("flag_ochre","#b86d21"),
          material("flag_coral","#e64048"))
    flag=material("flag_cloth","#f9e5a6")
    block("Court_three_dot_flag",(3.42,.85,1.56),(.49,.034,.28),flag,None,.025)
    for i,dot in enumerate(dots):
        sphere(f"Court_flag_dot_{i}",(3.26+.15*i,.821,1.56),
               (.045,.017,.045),dot,None,12,8)
    # A handful of ground flowers makes the courtyard friendly without clutter.
    flower=material("garden_flower","#f7b7b2")
    for x,y in ((-4.1,-1.7),(-3.4,2.0),(3.85,-2.0),(4.6,.2)):
        sphere("Court_flower",(x,y,.11),(.10,.10,.08),flower,None,12,8)
    print("SUNPATCH_COURT: reusable garden stage created from Blender geometry",flush=True)


def animate_character_polish(actors, events, fps, frames):
    """Subtle independent idle breathing and emotional facial/head acting."""
    for name, actor in actors.items():
        if not actor.get("profile"):
            continue
        root=actor["root"]
        for frame in range(1,frames+1,max(12,round(fps*.8))):
            phase=(frame/fps)*math.tau/3.2+(list(actors).index(name)*.9)
            root.scale=(1.0,1.0,1.0+.012*math.sin(phase))
            root.keyframe_insert(data_path="scale",frame=frame)
        root.scale=(1,1,1)
    for item in events:
        actor=actors.get(item.get("speaker"))
        if not actor or not actor.get("profile"):
            continue
        first=max(1,round(item["start"]*fps)+1)
        last=min(frames,round(item["end"]*fps)+1)
        if first>frames:
            break
        emotion=item.get("emotion","neutral")
        head=actor["head"]
        offset={"happy":-.045,"excited":-.075,"sad":.085,
                "angry":.045,"surprised":-.065}.get(emotion,0)
        for frame,angle in ((first,0),(max(first,(first+last)//2),offset),(last,0)):
            head.rotation_euler[1]=angle
            head.keyframe_insert(data_path="rotation_euler",frame=frame)
    print("CHARACTER_POLISH: idle breathing and keyed emotional head acting",flush=True)
