#!/usr/bin/env python3
"""Regenerate the owner-approved soft-fruit ASMR recording as 6s PCM WAV.

Freesound frodeims #812387 (CC0), the authentic tomato-slicing source.
No reference creator footage or audio and no synthesized background noise.
"""
import hashlib,os,subprocess
from pathlib import Path
import numpy as np,soundfile as sf
from scipy.signal import butter,sosfiltfilt
from scipy.ndimage import uniform_filter1d,maximum_filter1d
SRC=Path(os.environ.get('SOFT_FOLEY_SOURCE','/mnt/data/fig_revised_asmr/soft_tomato_cut_CC0.mp3'))
OUT=Path(os.environ.get('SOFT_FOLEY_OUTPUT','/mnt/data/kiwi3d/deliver/Kiwi_Cut_ApprovedFoley_48k24b.wav'))
OUT.parent.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SRC)=='8323de2b393b31d6df1b208fa5339821ce1ab2462dfe1ca2b40c0d10399dc0fa', 'CC0 audio source checksum mismatch'
SR=48000;SAMPLES=SR*6
b=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(SRC),'-ar',str(SR),'-ac','2','-f','f32le','pipe:1'])
src=np.frombuffer(b,dtype='<f4').reshape(-1,2).astype('float64');assert len(src)>SAMPLES
y=src[:SAMPLES].copy()
y=sosfiltfilt(butter(2,[85,3900],btype='bandpass',fs=SR,output='sos'),y,axis=0)
mid=y.mean(axis=1)
energy=uniform_filter1d(mid*mid,size=round(.028*SR),mode='nearest')
env=np.sqrt(np.maximum(energy,1.e-14))
env=maximum_filter1d(env,size=round(.055*SR),mode='nearest')
threshold=10**(-38/20)
gain=np.where(env>threshold,(np.maximum(env,threshold)/threshold)**(-.78),1.)
y*=gain[:,None]
mid=y.mean(axis=1);side=(y[:,0]-y[:,1])/2
y=np.stack([mid+.10*side,mid-.10*side],axis=1)
startfade=int(.055*SR);endfade=int(.070*SR)
y[:startfade,:]*=np.sin(np.linspace(0,np.pi/2,startfade))[:,None]
y[-endfade:,:]*=np.sin(np.linspace(np.pi/2,0,endfade))[:,None]
base_rms=float(np.sqrt((y*y).mean()));target_rms=10**(-29/20)
scale=min(target_rms/max(base_rms,1e-10),.68/max(np.max(np.abs(y)),1e-10))
y=y*scale
sf.write(OUT,y,SR,subtype='PCM_24')
print('OUTPUT',OUT,'SHA256',sha(OUT),'BYTES',OUT.stat().st_size)
