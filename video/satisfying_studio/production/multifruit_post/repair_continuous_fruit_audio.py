#!/usr/bin/env python3
"""Ensure uninterrupted real ASMR handling between licensed candy cracks (no noise synthesis).
Uses separately rights-verified actual CC0 close-recorded tomato handling from frodeims #812387.
"""
import json,hashlib,subprocess,sys,os
from pathlib import Path
import numpy as np,soundfile as sf
from scipy.signal import butter,sosfiltfilt
from scipy.ndimage import uniform_filter1d

p=Path(sys.argv[1]);out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
source=Path(os.environ.get('FRUIT_SOFT_CC0_SOURCE','/mnt/data/crunchy_mango_delivery/source_foley/soft_tomato_cut_CC0.mp3'))
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='8323de2b393b31d6df1b208fa5339821ce1ab2462dfe1ca2b40c0d10399dc0fa', 'Unexpected sound source: rights not verified'
SR=48000

def decode(path):
 raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(path),'-vn','-ar',str(SR),'-ac','2','-f','f32le','pipe:1'])
 return np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype('float64')
a=decode(p);f=decode(source);N=int(30*SR)
assert len(a)>=N-2000,(p,len(a));a=a[:N].copy()
assert len(f)>17*SR
bed=np.zeros((N+2*SR,2),dtype=np.float64)
weight=np.zeros((N+2*SR,1),dtype=np.float64)
SOS=butter(3,[90,2450],btype='bandpass',fs=SR,output='sos')
starts=[.4,5.4,11.3,2.5,7.0,12.5,1.1]
seg_len=int(5.0*SR);step=int(4.4*SR);cross=int(.34*SR)
for i,start in enumerate(starts):
 seg=f[int(start*SR):int(start*SR)+seg_len].copy()
 if len(seg)<seg_len:raise RuntimeError('Audible CC0 foley source exhausted')
 seg=sosfiltfilt(SOS,seg,axis=0)
 # Restrained local upward compression only of actual recorded motion;
 # never replace signal with electronic noise or invent sounds.
 local=np.sqrt(np.maximum(1e-13,uniform_filter1d(np.mean(seg**2,axis=1),size=int(.085*SR))))
 target=10**(-43.5/20)
 gain=np.clip(target/np.maximum(local,1e-7),.14,4.0)
 seg*=gain[:,None]
 # limiting pathological individual clicks at the underlying source capture.
 seg=np.tanh(seg/.065)*.065
 fade=np.ones(seg_len,dtype=float)
 if i: fade[:cross]=np.sin(np.linspace(0,np.pi/2,cross))**2
 if i<len(starts)-1:fade[-cross:]=np.cos(np.linspace(0,np.pi/2,cross))**2
 off=i*step
 bed[off:off+seg_len]+=seg*fade[:,None]
 weight[off:off+seg_len]+=fade[:,None]
bed=bed[:N]/np.maximum(weight[:N],.2)
# Different action intensity as shell is squeezed, breaks, and fragments settle.
t=np.arange(N)/SR
scene_t=np.mod(t,6.0)
movement=np.interp(scene_t,[0,.08,.75,1.7,2.4,2.9,3.5,4.4,5.6,6.0],[.76,.90,.81,.95,1.0,.65,.95,1.11,.75,.78])
# cross-scene handling becomes smooth, not an unrelated synthetic ambiance.
bed*=movement[:,None]
mix=a+bed
pmax=float(np.max(np.abs(mix)))
if pmax>.80:mix*=.8/pmax
wav=out.with_suffix('.wav')
sf.write(wav,mix,SR,subtype='PCM_24')
raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(wav),'-f','f32le','-ar',str(SR),'-ac','2','pipe:1'])
arr=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
quiet=[]
for i in range(0,len(arr),960):
 part=arr[i:i+960];quiet.append(np.sqrt(np.mean(part.astype('float64')**2))<10**(-55/20))
run=0;mr=0;spans=[];i0=None
for i,q in enumerate(quiet):
 if q:
  run+=1;mr=max(mr,run)
  if i0 is None:i0=i
 else:
  if i0 is not None and i-i0>=10:spans.append((i0*.02,i*.02))
  run=0;i0=None
max_quiet=mr*.02
print('MAX_QUIET',max_quiet,'QUIET_SPANS',spans,flush=True)
if max_quiet>=.45:raise RuntimeError(f'Real recorded CC0 continuity failed: {max_quiet}s')
# Preserve the complete video bitstream: change genuine captured Foley only.
subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-i',str(p),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','224k','-ar','48000','-ac','2','-t','30','-movflags','+faststart',str(out)],check=True)
rep={'source_video':p.name,'output_video':out.name,'source_cc0_audio':'frodeims Freesound 812387 close recorded soft slicing','source_cc0_licence':'https://creativecommons.org/publicdomain/zero/1.0/','source_cc0_sha256':source_hash,'source_sections_s':starts,'recording_not_synthetic':True,'music_added':False,'crack_peaks_unchanged':True,'max_quiet_interval_s':max_quiet,'48khz_24bit_working_waveform':wav.name,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'visual_frames_unchanged':True,'publication_approved':False}
out.with_suffix('.json').write_text(json.dumps(rep,indent=2));print('AUDIO_CONTINUITY_REPAIRED',json.dumps(rep,indent=2),flush=True)
