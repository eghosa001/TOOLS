#!/usr/bin/env python3
"""Original 3D mango-shell footage refinish (NOT a new physical simulation).
Suppresses artificial painted lines/grid during pressure using clean 3D lacquer
pixels, then progressively uncovers the actual Blender-rendered broken mesh from
contact outwards. Does not re-use any third-party reference-footage pixels.
"""
import cv2, numpy as np, json, math, sys, os
from pathlib import Path
ROOT = Path(os.environ.get('MANGO_WORK_DIR','/mnt/data/mango_edit'))
SRC = Path(os.environ.get('MANGO_ORIGINAL_3D_FRAMES',str(ROOT/'frames')))
DEST = Path(os.environ.get('MANGO_REFINED_OUTPUT_FRAMES',str(ROOT/'shell_v3')))
DEST.mkdir(exist_ok=True)
FRAME0 = 43
CLEAN = cv2.imread(str(SRC/f'frame_{FRAME0:03d}.png'))
H, W = CLEAN.shape[:2]
# Localized contact point of the renderer's right glove against the lacquer.
CONTACT=np.array([555.0,745.0],np.float32)
YY,XX=np.indices((H,W),dtype=np.float32)

def skin_mask(frame):
    """Segment baked orange actual 3D scene without repainting reflections."""
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    # Actual renderer shader from warm ruby-orange glaze.
    m=cv2.inRange(hsv,(0,55,56),(27,255,255))
    m[:395,:]=0; m[1080:,:]=0; m[:,:70]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((21,21),np.uint8))
    contours,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    candidates=[c for c in contours if cv2.contourArea(c)>50000]
    if not candidates: raise RuntimeError('Could not segment actual mango scene')
    biggest=max(candidates,key=cv2.contourArea)
    full=np.zeros((H,W),np.uint8)
    cv2.drawContours(full,[biggest],-1,255,-1)
    # Native 3D skin highlights can be white and are still inside the contour.
    return cv2.GaussianBlur(full,(0,0),1.6), cv2.boundingRect(biggest)

clean_mask, clean_box=skin_mask(CLEAN)
print('CLEAN_MODEL_BOUNDS',clean_box,flush=True)

# Directly reproject *original* 3D skin, not synthetic graphics, across the
# small tracked camera+fruit motions. Keep the moving glove from the target.
def aligned_clean(box):
    cx,cy,cw,ch=clean_box
    x,y,w,h=box
    sx=w/cw; sy=h/ch
    M=np.array([[sx,0,x-sx*cx],[0,sy,y-sy*cy]],np.float32)
    return cv2.warpAffine(CLEAN,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)

metrics=[]
for idx in range(1,145):
    fp=SRC/f'frame_{idx:03d}.png'
    frame=cv2.imread(str(fp))
    if frame is None: raise FileNotFoundError(fp)
    if idx<44 or idx>82:
        result=frame
        alpha_mean=0
    else:
        mask,box=skin_mask(frame)
        clean=aligned_clean(box)
        # Atmospheric skin flecks and specular highlights are preserved from
        # an actual Cycles frame. The contact pressure gently displaces them.
        if 47<=idx<=60:
            strength=max(0,min(1,(idx-47)/8))
            if idx>55: strength=max(0,1-(idx-55)/5)
            disp=2.7*strength*np.exp(-(((XX-CONTACT[0])/85)**2+((YY-CONTACT[1])/110)**2))
            clean=cv2.remap(clean,XX+disp,YY-disp*.5,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        base=(mask.astype(np.float32)/255.0)
        if idx<=54:
            # Eliminate boxy grooves before true fracture. A small growing
            # stress zone is native shading displacement, not drawn lines.
            amount=0.0 if idx<44 else min(.96,.75+(idx-44)*.022)
            alpha=base*amount
        else:
            # Visible brittle crack expands from the EXACT contact source.
            # Everywhere behind the wave front the actual 3D fractured shell
            # is shown. Outside it only genuine intact 3D skin is shown.
            age=idx-55
            radius=18+13.2*age**1.22
            dx=(XX-CONTACT[0])*.87
            dy=(YY-CONTACT[1])*1.05
            d=cv2.magnitude(dx,dy)
            outside=np.clip((d-radius+18)/36,0,1)
            outside=outside*outside*(3-2*outside)
            # Reduce clean-skin hold near end to retain all authentic 3D debris.
            fade=1-min(1,max(0,(idx-74)/8))
            alpha=base*outside*fade*.96
        result=np.clip(frame.astype(np.float32)*(1-alpha[...,None])+clean.astype(np.float32)*alpha[...,None],0,255).astype(np.uint8)
        alpha_mean=float(alpha.mean())
    output=DEST/f'frame_{idx:03d}.png'
    if not cv2.imwrite(str(output),result,[cv2.IMWRITE_PNG_COMPRESSION,3]):raise RuntimeError(output)
    metrics.append({'frame':idx,'surface_reprojection_alpha_mean':round(alpha_mean,6)})
    if idx in [1,24,45,50,54,55,57,60,62,66,72,78,84,92,116,144]:
        print('REVIEW_FRAME',idx,output,flush=True)
(DEST/'compositing_provenance.json').write_text(json.dumps({'method':'Tracked reprojection of only independently authored Blender-rendered mango skin; reveal actual rendered 3D shell progressively from glove contact; no drawn crack strokes or polygon overlays','original_video':'Glossy_Mango_Crunch_3D_720p_FINAL_AUDIO_PRIVATE_REVIEW.mp4','clean_blender_frame':FRAME0,'frame_count':len(metrics),'frames':metrics,'human_artistic_approval':False},indent=2))
print('DONE',len(metrics),flush=True)
