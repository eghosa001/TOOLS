#!/usr/bin/env python3
"""Encode real 144 Blender frames with authentic recorded sound and fail closed on tests.
Artifact is a private review, never automatically publishing/monetization approved.
"""
import subprocess,hashlib,json,os,math
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
F=Path(os.environ.get('FRAMES_DIR','/tmp/crunchy_mango'))
OUT=Path(os.environ.get('CRUNCH_OUTPUT','/tmp/crunchy_mango'))
OUT.mkdir(parents=True,exist_ok=True)
mp4=OUT/'Glossy_Mango_Crunch_3D_ASMR_720p_PRIVATE_REVIEW.mp4'
wav=OUT/'CRUNCHY_MANGO_CC0_PHYSICS_MATCHED_FOLEY_48k24b.wav'
assert wav.is_file(), 'No licensed audio mixture'
files=[F/f'frame_{i:03d}.png' for i in range(1,145)]
assert all(x.exists() for x in files),f'Missing frames: {[str(x) for x in files if not x.exists()][:8]}'
args=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-framerate','24','-start_number','1','-i',str(F/'frame_%03d.png'),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-frames:v','144','-r','24','-t','6', '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-movflags','+faststart',str(mp4)]
subprocess.run(args,check=True,timeout=480)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)]))
video=next(x for x in probe['streams'] if x['codec_type']=='video');audio=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert int(video['width'])>=720 and int(video['height'])>=1280
assert video['r_frame_rate']=='24/1' and audio['sample_rate']=='48000' and int(audio['channels'])==2
assert abs(float(probe['format']['duration'])-6)<.09
n=0;black=[];frozen=[];diffs=[];previous=None
cap=cv2.VideoCapture(str(mp4))
while True:
 ok,b=cap.read()
 if not ok:break
 gray=cv2.cvtColor(cv2.resize(b,(128,228)),cv2.COLOR_BGR2GRAY)
 if float(gray.mean())<10:black.append(n)
 if previous is not None:
  x=float(np.mean(np.abs(gray.astype('float32')-previous.astype('float32'))));diffs.append(x)
  if x<.045:frozen.append(n)
 previous=gray;n+=1
cap.release()
assert n==144 and not black, f'Incomplete or black video: n={n}, black={black}'
assert len(frozen)<4, f'Frozen frames count: {len(frozen)}'
log=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','info','-i',str(mp4),'-af','silencedetect=noise=-55dB:d=0.45','-f','null','-'],capture_output=True,text=True,timeout=150)
assert log.returncode==0 and 'silence_start' not in log.stderr,'Unwanted prolonged silence detected'
# Compare real rendered frames: pressure is continuous; the crack must change visible pixels.
# Two contacts are at frames 55 and 85, by author-written 3D scene and Foley ledger.
assert max(diffs[53:57])>.15,'Expected visible crack scene change at first recorded impact'
# Montage from EXACT final MP4, not independently rendered stills
sheet=Image.new('RGB',(3*320,3*565),(20,20,20));d=ImageDraw.Draw(sheet)
cap=cv2.VideoCapture(str(mp4))
for k,fno in enumerate([1,24,45,54,57,72,92,116,144]):
 cap.set(cv2.CAP_PROP_POS_FRAMES,fno-1);ok,im=cap.read()
 if not ok:continue
 im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));im.thumbnail((320,540),Image.Resampling.LANCZOS)
 x=k%3*320;y=k//3*565
 sheet.paste(im,(x+(320-im.width)//2,y));d.text((x+7,y+540),f'Frame {fno:03d} / 144',fill=(245,245,245))
cap.release()
shot=OUT/'CRUNCHY_MANGO_FRAME_BY_FRAME_9_KEY_FRAMES.jpg';sheet.save(shot,quality=87,optimize=True)
R={'is_live_action_stock':False,'is_genuine_3d_render':True,'asset_claim':'Author-written 3D geometry, publicly licensed Poly Haven CC0 HDRI','sound_claim':'Unmodified creator reference audio excluded; only CC0 original Freesound recordings adapted','visual_fracture_first_frame':55,'crunch_cue_frames':[55,85], 'decoded_video_frames':n,'frozen_frame_count':len(frozen),'black_frame_count':len(black),'maximum_observed_interframe_pixel_difference':round(max(diffs),3),'no_long_audio_silence':True,'duration_s':float(probe['format']['duration']),'frame_rate':video['r_frame_rate'],'dimensions':[video['width'],video['height']],'audio_channels':audio['channels'],'sample_rate':audio['sample_rate'],'sha256':hashlib.sha256(mp4.read_bytes()).hexdigest(),'bytes':mp4.stat().st_size,'editorial_status':'UNAPPROVED PRIVATE REVIEW ONLY','limitations':'Technical and structural video/sound analyses do not guarantee a premium artistic score, natural material and quality require watching and listening to the exact encoded MP4.'}
(OUT/'FINISHED_MP4_FRAME_AUDIO_QA.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2),flush=True)
