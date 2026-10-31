#!/usr/bin/env python3
"""Independent 3D macro kiwi slicing scene; PBR CC0 photogrammetry exterior from Poly Haven.
The interior and cut motion are original procedural geometry. 6s x 24fps.
"""
import os,sys,math,json,hashlib,subprocess
from pathlib import Path
import numpy as np
import trimesh, vtk
from vtk.util.numpy_support import numpy_to_vtk
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).parent
FPS=24; FRAMES=int(os.environ.get("FRAMES","144"))
SCALE=34.5
asset=ROOT/'assets'/'food_kiwi_01_2k.gltf'
source=trimesh.load(str(asset),force='scene')
mesh=next(iter(source.geometry.values()))
# input Y-axis is the original natural longitudinal kiwi axis.
pts=np.asarray(mesh.vertices)
P=np.column_stack([(pts[:,1]-.045)*SCALE,pts[:,2]*SCALE,pts[:,0]*SCALE+1.34]).astype(np.float32)
F=np.asarray(mesh.faces,dtype=np.int64)
UV=np.asarray(mesh.visual.uv,dtype=np.float32)
print('mesh source bounds',np.min(P,axis=0),np.max(P,axis=0),'triangles',len(F),flush=True)

def vtkmesh(P,F,uv=None):
 poly=vtk.vtkPolyData(); points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.ascontiguousarray(P),deep=True));poly.SetPoints(points)
 cells=vtk.vtkCellArray();faces=np.hstack([np.full((len(F),1),3,dtype=np.int64),F]).flatten(); cells.SetCells(len(F),numpy_to_vtk(np.ascontiguousarray(faces),deep=True,array_type=vtk.VTK_ID_TYPE));poly.SetPolys(cells)
 if uv is not None:
  arr=numpy_to_vtk(np.ascontiguousarray(uv),deep=True);arr.SetName('Texture Coordinates');arr.SetNumberOfComponents(2);poly.GetPointData().SetTCoords(arr)
 return poly

poly=vtkmesh(P,F,UV)
# Bake Poly Haven photoscan appearance to true 3D vertex colors, avoiding UV-atlas black seams.
scan_rgb=np.asarray(mesh.visual.to_color().vertex_colors[:,:3],dtype=np.uint8)
scan_rgb=np.maximum(scan_rgb,np.array([83,50,29],dtype=np.uint8))
skincol=numpy_to_vtk(np.ascontiguousarray(scan_rgb),deep=True,array_type=vtk.VTK_UNSIGNED_CHAR)
skincol.SetName("photoscan_skin_rgb");skincol.SetNumberOfComponents(3);poly.GetPointData().SetScalars(skincol)
# Preserve photogrammetry mesh smooth vertex normals across the slicing plane.
Nsrc=mesh.vertex_normals
Normals=np.ascontiguousarray(np.column_stack([Nsrc[:,1],Nsrc[:,2],Nsrc[:,0]]).astype(np.float32))
normals=numpy_to_vtk(Normals,deep=True);normals.SetName("Normals");poly.GetPointData().SetNormals(normals)
# Gentle scan clean-up; preserves photoscan colour while removing low-poly faceting.
sm=vtk.vtkWindowedSincPolyDataFilter();sm.SetInputData(poly);sm.SetNumberOfIterations(24);sm.SetPassBand(.048);sm.BoundarySmoothingOff();sm.FeatureEdgeSmoothingOff();sm.NormalizeCoordinatesOn();sm.Update()
no=vtk.vtkPolyDataNormals();no.SetInputConnection(sm.GetOutputPort());no.ComputePointNormalsOn();no.SplittingOff();no.ConsistencyOn();no.Update();poly=no.GetOutput()
pl=vtk.vtkPlane();pl.SetOrigin(0,0,0);pl.SetNormal(1,0,0)
clipped=[]
for sign in [False,True]:
 cl=vtk.vtkClipPolyData();cl.SetClipFunction(pl);cl.SetInputData(poly);cl.SetInsideOut(sign);cl.SetValue(0);cl.Update()
 p=vtk.vtkPolyData();p.DeepCopy(cl.GetOutput());clipped.append(p)
 print('clip',sign,'verts',p.GetNumberOfPoints(),'faces',p.GetNumberOfPolys(),'bounds',p.GetBounds(),flush=True)

# Original source model's 2k albedo and roughness, no repainted skin.
# Prepad black UV-atlas background with nearest authentic scanned skin pixels.
# Texture seams otherwise bleed black outside the islands under bilinear sampling.
from scipy.ndimage import distance_transform_edt
skin_src=np.asarray(Image.open(ROOT/'assets'/'textures'/'food_kiwi_01_diff_2k.jpg').convert('RGB'))
mask=np.max(skin_src,axis=2)<28
ix=distance_transform_edt(mask,return_distances=False,return_indices=True)
skin_fixed=np.maximum(skin_src[ix[0],ix[1]],np.array([83,50,32],dtype=np.uint8))
Image.fromarray(skin_fixed).save(ROOT/'assets'/'padded_kiwi_skin.jpg',quality=92)
read=vtk.vtkJPEGReader();read.SetFileName(str(ROOT/'assets'/'padded_kiwi_skin.jpg'));read.Update()
tex=vtk.vtkTexture();tex.SetInputConnection(read.GetOutputPort());tex.InterpolateOn();tex.RepeatOff();tex.EdgeClampOn();tex.SetColorModeToDirectScalars()

# Detailed cross section: 2048 green fruit flesh with wet radial vascular spokes and dark seeds.
SZ=1536
rng=np.random.default_rng(8019)
yy,xx=np.mgrid[0:SZ,0:SZ].astype(np.float32)
ux=(xx-SZ/2)/(SZ*.47);uy=(yy-SZ/2)/(SZ*.47)
r=np.sqrt(ux**2+uy**2);theta=np.arctan2(uy,ux)
# flesh structure and radial veins, gently mottled as kiwi rather than neon artificial jelly
fibres=(np.sin(theta*151 + (r*28))*.035+np.cos(theta*91-r*17)*.025+np.sin(theta*215+r*22)*.017)
cores=np.exp(-(r/.25)**4)
noise=rng.normal(0,5,(SZ,SZ)).astype(np.float32)
base=np.zeros((SZ,SZ,3),dtype=np.float32)
base[:,:,0]=100+43*(1-r)+fibres*250+noise*0.35
base[:,:,1]=173+23*(1-r)+fibres*140+noise*0.45
base[:,:,2]=48+13*(1-r)+fibres*42+noise*0.3
# pale center and milky near outer margin
center=(.88*cores)[:,:,None]
base=base*(1-center)+center*np.array([211,223,133],dtype=np.float32)
edge=np.clip((r-.78)/.15,0,1)[:,:,None]
base=base*(1-edge*.89)+edge*.89*np.array([218,217,145])
base=np.clip(base,0,255).astype('uint8')
im=Image.fromarray(base,'RGB')
d=ImageDraw.Draw(im,'RGBA')
# fine translucent radial stipples
for i in range(560):
 angle=rng.uniform(0,2*math.pi);rad=rng.uniform(.13,.86)
 x=SZ/2+math.cos(angle)*rad*.47*SZ;y=SZ/2+math.sin(angle)*rad*.47*SZ
 width=rng.uniform(.4,2.3)
 d.line((SZ/2+math.cos(angle)*(rad-.035)*.47*SZ,SZ/2+math.sin(angle)*(rad-.035)*.47*SZ,x,y),fill=(226,246,138,38),width=max(1,int(width)))
# ring of real proportion individual small kiwi seeds with light hilites; angular aligned
for i in range(92):
 a=2*math.pi*i/92+rng.normal(0,.03)
 rad=rng.uniform(.40,.60)
 x=SZ/2+math.cos(a)*rad*.47*SZ;y=SZ/2+math.sin(a)*rad*.47*SZ
 w=rng.uniform(2,3.8);h=rng.uniform(5,8)
 # seed shapes actually radial -- rotate the path
 dx=math.cos(a);dy=math.sin(a);px=-dy;py=dx
 corners=[(x-dx*h+px*w,y-dy*h+py*w),(x+dx*h+px*w,y+dy*h+py*w),(x+dx*h-px*w,y+dy*h-py*w),(x-dx*h-px*w,y-dy*h-py*w)]
 d.polygon(corners,fill=(23,28,16,255))
 d.line([(x-dx*h*.55+px*w*.3,y-dy*h*.55+py*w*.3),(x+dx*h*.5+px*w*.2,y+dy*h*.5+py*w*.2)],fill=(125,118,52,180),width=1)
# moist translucency on interior, angular gradient baked at mesh
im.save(ROOT/'kiwi_flesh_texture.png',quality=95)
rd=vtk.vtkPNGReader();rd.SetFileName(str(ROOT/'kiwi_flesh_texture.png'));rd.Update()
int_tex=vtk.vtkTexture();int_tex.SetInputConnection(rd.GetOutputPort());int_tex.SetColorModeToDirectScalars();int_tex.InterpolateOn();int_tex.RepeatOff()

# 3d cross-section plane geometry (real cap with 2 concentric rings and texture)
def cap_poly(side=1):
 n=128;radial=20;v=[];uv=[];faces=[]
 # kiwi model scanned cross-section at X=0: elliptical radius Y~1.05 Z~1.12
 for j in range(radial+1):
  rr=j/radial
  for i in range(n):
   a=2*math.pi*i/n
   # edge perturbation subtle irregular texture in actual cut geometry
   mod=1 + .016*math.sin(5*a+1) + .011*math.sin(9*a+2)
   Y=1.10*rr*math.cos(a)*mod
   Z=1.34+1.12*rr*math.sin(a)*mod
   X=0.008*side + .019*(1-rr*rr)*side
   v.append([X,Y,Z]);uv.append([(math.cos(a)*rr+1)*.5,(math.sin(a)*rr+1)*.5])
 for j in range(radial):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n;c=(j+1)*n+i;e=(j+1)*n+(i+1)%n
   if side==1:faces.extend([[a,c,e],[a,e,b]])
   else:faces.extend([[a,e,c],[a,b,e]])
 return vtkmesh(np.array(v,np.float32),np.array(faces,np.int64),np.array(uv,np.float32))
cap0=cap_poly(1);cap1=cap_poly(-1)

ren=vtk.vtkRenderer()
ren.SetBackground(0.023,0.042,0.046)
ren.SetBackground2(0.10,0.14,0.135)
ren.GradientBackgroundOn()
win=vtk.vtkRenderWindow();win.SetSize(int(os.environ.get('RENDER_W',540)),int(os.environ.get('RENDER_H',960)))
win.SetOffScreenRendering(1);win.AddRenderer(ren)
ren.SetUseDepthPeeling(False)
ren.SetTwoSidedLighting(True)
actors=[];caps=[]
for i,(pd,cap) in enumerate(zip(clipped,[cap0,cap1])):
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(pd);mapper.SetScalarModeToUsePointData();mapper.SetColorModeToDirectScalars();mapper.ScalarVisibilityOn()
 act=vtk.vtkActor();act.SetMapper(mapper);act.SetTexture(None)
 prop=act.GetProperty();prop.SetInterpolationToPhong();prop.SetColor(.97,.95,.94);prop.SetAmbient(.22);prop.SetDiffuse(.76);prop.SetSpecular(.055);prop.SetSpecularPower(12)
 act.GetProperty().LightingOff() if os.environ.get("TEST_UNLIT")=="1" else None
 ren.AddActor(act);actors.append(act)
 ma=vtk.vtkPolyDataMapper();ma.SetInputData(cap)
 ac=vtk.vtkActor();ac.SetMapper(ma);ac.SetTexture(int_tex)
 ap=ac.GetProperty();ap.SetInterpolationToPhong();ap.SetColor(1,1,1);ap.SetAmbient(.30);ap.SetDiffuse(.68);ap.SetSpecular(.37);ap.SetSpecularPower(62);ap.BackfaceCullingOff()
 ren.AddActor(ac);caps.append(ac)

# wooden board and studio plinth under kiwi. Organic wood grain via colour-scalars on plane.
N=100
xgrid, ygrid=np.meshgrid(np.linspace(-5.2,5.2,N),np.linspace(-3.5,3.5,N));zz=.02+.018*np.sin(xgrid*15+ygrid*2)+.013*np.cos(xgrid*41-ygrid*3)
woodpts=np.column_stack([xgrid.ravel(),ygrid.ravel(),zz.ravel()]);faces=[]
for j in range(N-1):
 for i in range(N-1):
  a=j*N+i;faces.extend([[a,a+1,a+N+1],[a,a+N+1,a+N]])
# Aligned dark walnut wood grain: continuous scanned-style planks, no flat stripes.
Ntex=1024
wy,wx=np.mgrid[0:Ntex,0:Ntex].astype(np.float32)
np_rng=np.random.default_rng(4242)
phase=wx*0.23 + 9*np.sin(wy*.016)+4*np.sin(wy*.044+wx*.003)
line=np.sin(phase) + .35*np.sin(phase*2.45) + .2*np.sin(phase*5.1)
noise=np_rng.normal(0,3,(Ntex,Ntex))
wood_image=np.clip(np.stack([89+3.9*line+noise*.7,58+3.1*line+noise*.6,40+2.4*line+noise*.5],axis=2),0,255).astype('uint8')
Image.fromarray(wood_image).save(ROOT/'walnut_board.png',compress_level=5)
br=vtk.vtkPNGReader();br.SetFileName(str(ROOT/'walnut_board.png'));br.Update()
boardtex=vtk.vtkTexture();boardtex.SetInputConnection(br.GetOutputPort());boardtex.InterpolateOn();boardtex.RepeatOn()
wood_uv=np.column_stack([(xgrid.ravel()+5.2)/10.4,(ygrid.ravel()+3.5)/7.0]).astype('float32')
wp=vtkmesh(woodpts,np.array(faces,dtype=np.int64),wood_uv);cols=vtk.vtkUnsignedCharArray();cols.SetNumberOfComponents(3);cols.SetName('wood')
for y,x in zip(ygrid.ravel(),xgrid.ravel()):
 value=0.14*math.sin(x*39+y*2)+0.09*math.sin(x*102+y*3)+0.10*math.cos(x*16+y)
 c=np.clip(np.array([107,67,42])*(1+value),0,255).astype(int)
 cols.InsertNextTuple3(*c)
wp.GetPointData().SetScalars(cols)
mp=vtk.vtkPolyDataMapper();mp.SetInputData(wp);mp.SetScalarModeToUsePointData();mp.ScalarVisibilityOff()
wood=vtk.vtkActor();wood.SetMapper(mp);wood.SetTexture(boardtex);wood.GetProperty().SetColor(1,1,1);wood.GetProperty().SetInterpolationToPhong();wood.GetProperty().SetAmbient(.26);wood.GetProperty().SetDiffuse(.77);wood.GetProperty().SetSpecular(.10);wood.GetProperty().SetSpecularPower(18);ren.AddActor(wood)

# slim chrome knife actual bevelled prism with subtle metal handle
knife_poly=None
# x horizontal thickness, y length, z height; edge on bottom with bevel
# long blade profile across world y with rounded tip.
profile=[(-1.65,0.60),(-1.65,-.72),(-1.35,-.80),(1.75,-.80),(1.92,-.65),(1.92,.22),(1.7,.40)]
vertices=[]
for xx in [-.055,.055]:
 for y,z in profile:vertices.append([xx,y,z])
n=len(profile);ff=[]
for i in range(1,n-1):ff.extend([[0,i,i+1],[n,n+i+1,n+i]])
for i in range(n):ff.extend([[i,(i+1)%n,n+(i+1)%n],[i,n+(i+1)%n,n+i]])
# Metallic brushed sheet uses a PBR-like baked steel gradient instead of flat grey.
metal_uv=np.array([[(yy+1.65)/3.58,(zz+.8)/1.45] for xx in [-.055,.055] for yy,zz in profile],dtype=np.float32)
knife_mesh=vtkmesh(np.array(vertices,dtype=np.float32),np.array(ff,dtype=np.int64),metal_uv)
metal_n=1024
mi,mj=np.mgrid[0:metal_n,0:metal_n].astype(np.float32)
rg=np.random.default_rng(711)
brush=3*np.sin(mj*0.67)+2*np.sin(mj*1.41)+rg.normal(0,1.4,(metal_n,metal_n))
blade_tone=172+35*np.exp(-((mi-805)/60)**2)-24*np.exp(-((mi-130)/135)**2)
metal=np.stack([blade_tone+brush-8,blade_tone+brush+1,blade_tone+brush+6],axis=2).clip(0,255).astype('uint8')
Image.fromarray(metal).save(ROOT/'brushed_stainless.png')
mr=vtk.vtkPNGReader();mr.SetFileName(str(ROOT/'brushed_stainless.png'));mr.Update()
metex=vtk.vtkTexture();metex.SetInputConnection(mr.GetOutputPort());metex.InterpolateOn()
m=vtk.vtkPolyDataMapper();m.SetInputData(knife_mesh)
knife=vtk.vtkActor();knife.SetMapper(m);knife.SetTexture(metex);knife.GetProperty().SetInterpolationToPhong();knife.GetProperty().SetAmbient(.4);knife.GetProperty().SetDiffuse(.5);knife.GetProperty().SetSpecular(.65);knife.GetProperty().SetSpecularPower(85);knife.GetProperty().SetColor(.95,.98,1.0);ren.AddActor(knife)
# knife thin bright cutting edge (tube) with aligned blade
line=vtk.vtkLineSource();line.SetPoint1(0,-1.55,-.795);line.SetPoint2(0,1.74,-.795)
tub=vtk.vtkTubeFilter();tub.SetInputConnection(line.GetOutputPort());tub.SetRadius(.021);tub.SetNumberOfSides(10);tub.Update();ee=vtk.vtkActor();mm=vtk.vtkPolyDataMapper();mm.SetInputConnection(tub.GetOutputPort());ee.SetMapper(mm);ee.GetProperty().SetColor(.8,.93,.93);ee.GetProperty().SetInterpolationToPhong();ee.GetProperty().SetAmbient(.3);ee.GetProperty().SetSpecular(.7);ee.GetProperty().SetSpecularPower(90);ren.AddActor(ee)
# premium dark handle blade extension facing camera
hs=vtk.vtkCubeSource();hs.SetXLength(.27);hs.SetYLength(1.35);hs.SetZLength(.35);hs.SetCenter(0,2.38,.33)
hm=vtk.vtkPolyDataMapper();hm.SetInputConnection(hs.GetOutputPort());handle=vtk.vtkActor();handle.SetMapper(hm);handle.GetProperty().SetColor(.09,.095,.085);handle.GetProperty().SetInterpolationToPBR();handle.GetProperty().SetRoughness(.25);handle.GetProperty().SetMetallic(.05);ren.AddActor(handle)

# Original studio camera 3D parallax, macro framing with calibrated lens.
camera=ren.GetActiveCamera()
camera.SetPosition(5.6,-9.0,6.0);camera.SetFocalPoint(0,0,1.28);camera.SetViewUp(0,0,1)
camera.SetViewAngle(28);camera.ParallelProjectionOff()
# volumetric-like 3-point studio illumination
for pos,col,intensity in [((0,-5,9),(1,.91,.77),1.45),((-5,2,6),(.44,.75,1.0),.92),((4,5,5),(1,.53,.29),.75)]:
 light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*pos);light.SetFocalPoint(0,0,1);light.SetColor(*col);light.SetIntensity(intensity);light.SetPositional(True);light.SetConeAngle(70);ren.AddLight(light)
ren.SetAmbient(.17,.18,.20)

# Camera focus and tone map: soft studio with readable contrast, not flat CGI spheres.
try: ren.UseFXAAOff()
except Exception: pass

trans=vtk.vtkTransform()

def update(t):
 # One knife cut. 0-0.6 hovering, 0.7-4.2 down through kiwi, 4.2-4.8 held, then withdraws.
 def smooth(a,b,x):
  u=max(0,min(1,(x-a)/(b-a)));return u*u*(3-2*u)
 down=smooth(0.0,5.28,t)
 lift=smooth(5.30,5.95,t)
 blade_z=3.33-2.45*down+2.96*lift
 # Major position: the reflective blade front, aligned with middle of kiwi
 for piece in [knife,ee,handle]:piece.SetPosition(0,0,blade_z)
 # Once blade edge passes the core, seeded flesh starts to reveal.
 cut=smooth(2.65,5.25,t);separate=smooth(4.70,5.95,t)
 for i,(piece,cap) in enumerate(zip(actors,caps)):
  cap.SetVisibility(t>=2.60)
  sign=1 if i==0 else -1
  # Physical force yields few mm separation during the cut and a final open reveal.
  displ=sign*(.03*cut+.84*separate)
  for act in (piece,cap):
   act.SetPosition(displ,0,0)
   act.SetOrigin(0,0,1.35)
   act.SetOrientation(0,0,sign*(1.2*cut+7*separate))
 # gentle 3D camera arc rather than a 2D crop pan.
 camera.SetPosition(5.6-.3*smooth(4.6,6,t),-9+.4*smooth(4.6,6,t),6+.15*smooth(4.6,6,t))

out=Path(os.environ.get('FRAMES_DIR',str(ROOT/'frames')));out.mkdir(exist_ok=True)
from vtk.util.numpy_support import vtk_to_numpy
window_capture=vtk.vtkWindowToImageFilter();window_capture.SetInput(win);window_capture.ReadFrontBufferOn()
for i in range(int(os.environ.get("START_FRAME","0")),FRAMES):
 t=float(os.environ.get("TEST_T",i/FPS));update(t);ren.ResetCameraClippingRange();win.Render();window_capture.Modified();window_capture.Update()
 data=vtk_to_numpy(window_capture.GetOutput().GetPointData().GetScalars());print("CAP",i,"range",data.min(),data.max(),"mean",data.mean(),"cams",camera.GetPosition(),camera.GetClippingRange(),flush=True) if i==0 else None
 w,h=win.GetSize();im=Image.fromarray(data.reshape(h,w,-1)[::-1,:,:3].astype(np.uint8),'RGB')
 im.save(out/f'frame_{i:03d}.png',compress_level=3)
 if i==0:
  writer=vtk.vtkPNGWriter();writer.SetFileName(str(ROOT/"writer_raw.png"));writer.SetInputConnection(window_capture.GetOutputPort());writer.Write()
 if i in [0,23,47,71,95,119,143]:
  im.save(ROOT/f'preview_{i:03d}.jpg',quality=88)
 print('RENDER',i,'/',FRAMES,flush=True) if i%24==0 else None
print('render complete',flush=True)
