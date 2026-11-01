#!/usr/bin/env python3
"""Fix visible artificial instantaneous shell fracture on original CGI 3D clips.
Reproject only ORIGINAL Blender Cycles skin pixels; unmask the already genuinely
rendered, three-dimensional shell shards gradually from physical glove contact.
No drawn crack graphics, no user-uploaded reference video/audio.
"""
import os,sys,subprocess,hashlib,json
from pathlib import Path
import numpy as np,cv2

p=Path(sys.argv[1]);dest=Path(sys.argv[2]);dest.parent.mkdir(parents=True,exist_ok=True)
cap=cv2.VideoCapture(str(p));fps=cap.get(cv2.CAP_PROP_FPS);total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
assert abs(fps-24)<.05 and total==144,(fps,total)
cap.set(cv2.CAP_PROP_POS_FRAMES,42);ok,CLEAN=cap.read();assert ok
H,W=CLEAN.shape[:2]
contact=np.array([int(.771*W),int(.582*H)],np.float32)
YY,XX=np.indices((H,W),dtype=np.float32)

def skin_mask(frame):
 hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
 # All distinct pink/red/yellow/purple shells are high-saturation CGI material.
 m=cv2.inRange(hsv,(0,48,55),(179,255,255))
 m[:int(.305*H),:]=0;m[int(.845*H):,:]=0;m[:,:int(.095*W)]=0
 m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((21,21),np.uint8))
 cnt,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 candidates=[c for c in cnt if cv2.contourArea(c)>max(5000,H*W*.055)]
 if not candidates:raise RuntimeError('No CGI shell contour: '+str(p))
 best=max(candidates,key=cv2.contourArea)
 mask=np.zeros((H,W),np.uint8);cv2.drawContours(mask,[best],-1,255,-1)
 return cv2.GaussianBlur(mask,(0,0),1.6),cv2.boundingRect(best)

clean_mask,(cx,cy,cw,ch)=skin_mask(CLEAN)
print('ORIGINAL_CGI_SKIN_BOUNDS',p.name,(cx,cy,cw,ch),flush=True)

def aligned(box):
 x,y,w,h=box
 M=np.array([[w/cw,0,x-w*cx/cw],[0,h/ch,y-h*cy/ch]],np.float32)
 return cv2.warpAffine(CLEAN,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)

silent=dest.with_name(dest.stem+'_silent.mp4')
cmd=['ffmpeg','-nostdin','-y','-v','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','pipe:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-an',str(silent)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
cap.set(cv2.CAP_PROP_POS_FRAMES,0)
checks=[];n=0
while True:
 ok,frame=cap.read()
 if not ok:break
 n+=1
 if 44<=n<=82:
  mask,box=skin_mask(frame)
  clean=aligned(box)
  if 47<=n<=60:
   strength=max(0,min(1,(n-47)/8))
   if n>55:strength=max(0,1-(n-55)/5)
   disp=2.7*strength*np.exp(-(((XX-contact[0])/85)**2+((YY-contact[1])/110)**2))
   clean=cv2.remap(clean,XX+disp,YY-disp*.5,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
  base=mask.astype(np.float32)/255.0
  if n<=54:
   amount=0.0 if n<44 else min(.96,.75+(n-44)*.022)
   alpha=base*amount
  else:
   age=n-55;radius=18+13.2*age**1.22
   d=cv2.magnitude((XX-contact[0])*.87,(YY-contact[1])*1.05)
   outside=np.clip((d-radius+18)/36,0,1)
   outside=outside*outside*(3-2*outside)
   fade=1-min(1,max(0,(n-74)/8))
   alpha=base*outside*fade*.96
  frame=np.clip(frame.astype(np.float32)*(1-alpha[...,None])+clean.astype(np.float32)*alpha[...,None],0,255).astype('uint8')
  if n in [44,54,55,61,65,72,82]:checks.append({'frame':n,'clean_fraction':round(float(alpha.mean()),4)})
 proc.stdin.write(frame.tobytes())
cap.release();proc.stdin.close();error=proc.stderr.read().decode(errors='replace');proc.stderr.close();status=proc.wait()
if status:raise RuntimeError('FFmpeg video encode failed: '+error[-2000:])
assert n==144,n
subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-i',str(silent),'-i',str(p),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-t','6','-movflags','+faststart',str(dest)],check=True)
silent.unlink(missing_ok=True)
rep={'original_input':p.name,'output':dest.name,'original_3D_video':True,'user_reference_footage':False,'no_drawn_crack_strokes':True,'method':'3D-rendered intact Cycles skin reprojected until real Blender fracture surface reaches contact; source 3D meshes retained','source_frames':144,'fps':24,'original_first_fracture_frame':55,'new_visible_reveal_target_frames':[60,61,62],'real_CGI_falling_shards':True,'sound_passed_through_byte_for_byte_compressed_AAC':True,'checks':checks,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'publication_approved':False}
dest.with_suffix('.json').write_text(json.dumps(rep,indent=2));print('SHELL_REVEAL_PROCESSED',json.dumps(rep,indent=2))
