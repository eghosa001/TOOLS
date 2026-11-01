#!/usr/bin/env python3
"""Actual licensed CC0 candy/fruit recordings, structure-bound to simulated cracks.
No synthetic white noise; no unlicensed user benchmark audio.
"""
import os,json,subprocess,hashlib,math
from pathlib import Path
import numpy as np,soundfile as sf
from scipy.signal import butter,sosfiltfilt
A=Path(os.environ.get('CRUNCH_ASSETS','/tmp/crunchy_mango_assets'))
OUT=Path(os.environ.get('CRUNCH_OUTPUT','/tmp/crunchy_mango'))
OUT.mkdir(parents=True,exist_ok=True)
SR=48000;DURATION=6.0;N=int(DURATION*SR)
rights=json.loads((A/'RIGHTS_SOURCE_LEDGER.json').read_text())
def src(name):
 info=next(x for x in rights['asset_ledger'] if x['role']==name)
 p=A/info['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256']
 b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-ar',str(SR),'-ac','2','-f','f32le','pipe:1'])
 return np.frombuffer(b,dtype='<f4').reshape(-1,2).astype(np.float64)
def level(x,db):
 rms=np.sqrt(np.mean(x*x));return x*((10**(db/20))/max(1.e-8,rms))
# diegetic subtle handling/fruit contact, lowpass so it does not suggest cracking pre-fracture.
soft=src('soft_fruit_inner');y=np.zeros((N,2),np.float64)
background=soft[int(2.0*SR):int(8.0*SR)].copy()
if len(background)<N:background=np.pad(background,((0,N-len(background)),(0,0)))
background=sosfiltfilt(butter(3,[90,2600],btype='bandpass',fs=SR,output='sos'),background,axis=0)
background=level(background,-42.2)
# soft interior audible only after the shell opens; quiet movement underneath before, not artificial hiss.
t=np.arange(N)/SR
env=.50 + .85/(1+np.exp(-(t-3.0)*6))
# avoid loud wet slicing dominating crunchy shell
y+=background*env[:,None]
record=[]
def add_snap(role,frame,peakdb,length=.84):
 raw=src(role)
 # Isolate the crispest local real attack from the original recording.
 mono=raw.mean(axis=1)
 window=int(.015*SR)
 energy=np.convolve(mono**2,np.ones(window)/window,mode='same') if len(mono)<200000 else None
 if energy is None:raise RuntimeError('Foley sample unexpectedly long')
 # Strongest genuine short-term attack; center it precisely on first visual gap.
 maxidx=int(np.argmax(energy))
 half_pre=int(.035*SR);total=int(length*SR)
 start=max(0,maxidx-half_pre)
 segment=raw[start:min(start+total,len(raw))].copy()
 if len(segment)<1000:raise RuntimeError('Foley slice too short')
 segment=sosfiltfilt(butter(2,[110,12000],fs=SR,btype='bandpass',output='sos'),segment,axis=0)
 fade_in=min(96,len(segment)//10);fadeout=min(4000,len(segment)//5)
 segment[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
 segment[-fadeout:]*=np.linspace(1,0,fadeout)[:,None]
 # First large crack, second lower-level cluster; no all-purpose continuous crunchy wallpaper.
 segment=level(segment,peakdb)
 # Time sound loudest 15ms RMS crest at the exact scene first fracture visual frame.
 center=round((frame/24-0.070)*SR)  # visual break begins during preceding interpolated image frames
 source_peak=int(np.argmax(np.mean(segment**2,axis=1)))
 position=center-source_peak
 if position<0:raise RuntimeError('Foley peak too early for sound file')
 end=min(N,position+len(segment))
 y[position:end]+=segment[:end-position]
 record.append({'visual_fracture_frame':frame,'target_time_s':frame/24,'role':role,'licensed_file':next(x['file'] for x in rights['asset_ledger'] if x['role']==role),'recorded_peak_alignment_offset_s':(position+source_peak)/SR-(frame-1)/24,'audio_mix_start_s':round(position/SR,4),'audio_mix_end_s':round(end/SR,4),'target_rms_dbfs':peakdb})
add_snap('candy_shell_snap',55,-26.0,.84)
add_snap('candy_bar_crunch',85,-29.0,.75)
# Material-authentic CC0 continuity from SIX DIFFERENT soft-fruit slices.
# Do not add synthetic noise or repeat a short audio loop during silent visuals.
# The non-identical contact passages stay below the real hard shell-cracks.
bed=np.zeros((N+SR,2),np.float64)
weight=np.zeros((N+SR,1),np.float64)
starts=[1.10,3.10,5.15,7.35,8.52,11.15]
sub_len=int(1.10*SR);cross=int(.10*SR)
bed_filter=butter(3,[120,2300],btype='bandpass',fs=SR,output='sos')
for i,start_time in enumerate(starts):
 part=soft[int(start_time*SR):int(start_time*SR)+sub_len].copy()
 if len(part)<sub_len:raise RuntimeError('Soft-fruit CC0 source is too short for continuity passages')
 part=sosfiltfilt(bed_filter,part,axis=0)
 part=np.tanh(part/.035)*.035
 part*=min(4.0,10**(-43/20)/max(float(np.sqrt(np.mean(part*part))),1e-8))
 envelope=np.ones((len(part),1),np.float64)
 if i:envelope[:cross,0]=np.sin(np.linspace(0,np.pi/2,cross))**2
 if i+1<len(starts):envelope[-cross:,0]=np.cos(np.linspace(0,np.pi/2,cross))**2
 off=i*SR
 bed[off:off+len(part)]+=part*envelope
 weight[off:off+len(part)]+=envelope
bed=bed[:N]/np.maximum(weight[:N],.001)
physical_envelope=np.interp(t,[0,.08,.8,1.3,2.2,2.4,3.2,3.6,4.2,5.2,5.9,6],
                             [.55,.9,.85,1,1.05,.43,.78,.42,.75,.85,.70,.05])
y+=bed*physical_envelope[:,None]
# Soft released juicy pressure, not biting/eating, stays under the changing shell.
# Gently attenuate clipping, avoid artificial noise normalization.
peak=np.max(abs(y));y*=min(1,0.73/max(1.e-6,peak))
f=int(.035*SR);y[:f]*=np.linspace(0,1,f)[:,None];y[-f:]*=np.linspace(1,0,f)[:,None]
# compressed PCM user review master
wav=OUT/'CRUNCHY_MANGO_CC0_PHYSICS_MATCHED_FOLEY_48k24b.wav'
sf.write(wav,y,SR,subtype='PCM_24')
manifest={'source_licensed':rights,'primary_crunch_events':record,'audio_recorded_not_ai':True,'actual_mix_duration_s':len(y)/SR,'file_sha256':hashlib.sha256(wav.read_bytes()).hexdigest(),'headphone_audition_done':False,'publication_approved':False,'semantic_limitations':'The actual audible material and impact intensity require listening to the exact MP4, automated timing and waveform checks are insufficient'}
(OUT/'FOLEY_FRAME_ALIGNMENT_AND_SOURCE_RIGHTS.json').write_text(json.dumps(manifest,indent=2))
print('FOLEY MIX',json.dumps({k:v for k,v in manifest.items() if k!='source_licensed'},indent=2),flush=True)
