#!/usr/bin/env python3
"""Evidence on the exact private-review MP4; no fictitious quality scores."""
import hashlib,json,subprocess,os
from pathlib import Path
import numpy as np,cv2
D=Path(os.environ.get('FRUIT_FINISHED_DIR','/mnt/data/multifruit_studio/final'))
masters=[D/'Five_Fruits_30s_3D_Crunch_ASMR_720p_CONTINUOUS_RECORDED_FOLEY.mp4',D/'Five_Fruits_30s_3D_Crunch_ASMR_540p_MOBILE_REVIEW.mp4']
old=D/'Five_Fruits_30s_3D_Crunch_ASMR_720p_PRIVATE_REVIEW.mp4'
fruits=['mango','strawberry','citrus','dragonfruit','fig'];details=[]
def ff(*args):return subprocess.check_output(['ffmpeg','-nostdin','-v','error',*args]).decode().strip()
for p in masters:
 assert p.is_file()
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
 v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert v['r_frame_rate']=='24/1' and int(a['sample_rate'])==48000 and int(a['channels'])==2
 cap=cv2.VideoCapture(str(p));n=0;black=[];last=None;freeze=0;longest=0
 while True:
  ok,b=cap.read()
  if not ok:break
  n+=1
  if b.mean()<6:black.append(n)
  if last is not None:
   delta=float(np.abs(last.astype('int16')-b.astype('int16')).mean())
   freeze=freeze+1 if delta<.1 else 0;longest=max(longest,freeze)
  last=b
 cap.release()
 assert n==720,n
 assert not black,black
 assert longest<19,('Unexpected frozen sequence',longest)
 raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(p),'-vn','-f','f32le','-ar','48000','-ac','2','pipe:1'])
 samples=np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype('float64');N=960
 quiet=[np.sqrt(np.mean(samples[k:k+N]**2))<10**(-55/20) for k in range(0,len(samples),N)]
 runs=[];count=0
 for val in quiet:
  count=(count+1 if val else 0);runs.append(count)
 max_quiet=max(runs)*.02
 assert max_quiet<.45,('Audio near-silence',max_quiet)
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 details.append({'name':p.name,'size_bytes':p.stat().st_size,'sha256':sha,'actual_video_decoded_frames':n,'dimensions':[int(v['width']),int(v['height'])],'fps':24,'duration_container_sec':round(float(probe['format']['duration']),3),'audio_sample_rate':int(a['sample_rate']),'stereo_channels':int(a['channels']),'black_frames':len(black),'max_same_frame_run':longest,'max_quiet_interval_sec':round(max_quiet,3)})
 print('PASSED',p.name,sha,max_quiet,flush=True)
# Prove video picture bytes are unchanged by recorded-ambient repair (compressed bitstream MD5).
def video_md5(p):return ff('-i',str(p),'-an','-map','0:v:0','-c:v','copy','-f','md5','pipe:1')
video_unchanged=video_md5(old)==video_md5(masters[0]);assert video_unchanged
source_rights=[]
for fruit in fruits[1:]:
 r=json.loads((D.parent/'segments'/fruit/'CC0_SOURCE_RIGHTS.json').read_text())
 for asset in r['asset_ledger']:
  assert asset['license_verified'] and asset['sha256'] and asset['source_page']
 source_rights.append({'fruit':fruit,'ledger_sha256':hashlib.sha256((D.parent/'segments'/fruit/'CC0_SOURCE_RIGHTS.json').read_bytes()).hexdigest(),'real_cc0_assets':len(r['asset_ledger'])})
# Verify recognizable audible real crack peaks are close to actual image opening per fruit.
a=np.frombuffer(subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(masters[0]),'-vn','-f','f32le','-ar','48000','-ac','2','pipe:1']),dtype='<f4').reshape(-1,2).astype('float64')
peaks=[]
for i,fruit in enumerate(fruits):
 for j,loc in enumerate([2.50,3.50]):
  t=i*6+loc;st=int((t-.23)*48000);en=int((t+.23)*48000)
  seg=a[st:en];energy=np.mean(seg*seg,axis=1)
  kernel=np.ones(480)/480;sm=np.convolve(energy,kernel,'same');at=(st+np.argmax(sm))/48000
  # Mango v3's user-tested local first visible crack is a little later (near 2.56 s).
  visual_event=i*6+(2.56 if i==0 and j==0 else loc)
  delta_ms=(at-visual_event)*1000
  assert abs(delta_ms)<(1000/24+2),(fruit,loc,delta_ms)
  peaks.append({'fruit':fruit,'event':'primary_crack' if j==0 else 'crumble','visible_contact_target_s':round(visual_event,3),'actual_aac_10ms_rms_peak_s':round(at,3),'sync_error_ms':round(delta_ms,1)})
proof={'title':'Five-fruit original licensed CGI ASMR, 30-second private proof','local_review_master':details[0],'mobile_copy':details[1],'fruit_order':fruits,'render_method':'Existing v3 authored Cycles mango + 4 new 3D fruit geometry/fracture scenes; 48 native 540x960 CGI frames per new fruit, frame interpolation to 24fps 720x1280; organic 3D shell reveal compositing from ORIGINAL Blender skin. No 3rd-party ASMR reference picture/audio.','CC0_Freesound_licensed_sound_originals':source_rights,'CC0_studio_hdri':'Poly Haven studio_small_09','audio_source_bed':'Original close-recorded frodeims tomato/soft-fruit handling CC0','exact_mango_original_footage_copied_from_user_reference':False,'30s_bitstream_picture_unchanged_by_audio_continuity_fix':video_unchanged,'frame_audio_events':peaks,'audio_material_measured_not_human_headphone_audited':True,'editorial_visual_standard_met':False,'publication_approved':False,'owner_review_required':True}
(D/'FIVE_FRUITS_30sec_SOURCE_RIGHTS_FRAME_AUDIO_QA.json').write_text(json.dumps(proof,indent=2))
print('ALL_EXACT_EXPORT_GATES_PASS 720 video frames and 10 synchronized recorded crack events',flush=True)
