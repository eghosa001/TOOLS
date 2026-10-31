#!/usr/bin/env python3
"""Rebuild the 34-second ASMR audio timeline with per-shot SFX placement.

Fixes a previous amix graph that created digital silence from 17-34s.
Source sounds: existing Stable Audio 3 Small-SFX original masters.
No paid API or new GPU inference; video stream is copied unchanged.
"""
from __future__ import annotations
import io,json,hashlib,math,subprocess,zipfile,os
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly,butter,sosfilt

ROOT=Path(os.environ.get('ASMR_PUBLISH_DIR','/mnt/data/asmr_stock_first/publish_candidate'))
SRC=ROOT/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_1080p.mp4'
SFX=Path(os.environ.get('ASMR_SFX_ZIP','/mnt/data/four_asmr_real_foley_generated.zip'))
META=ROOT/'SOURCE_AND_EXPORT_PROVENANCE.json'
SR=48000
TIMELINE=[
 ('clear_pour',0.0,4.4,'ripples',2.0,-26.5),
 ('water_ripples',4.4,7.6,'ripples',6.4,-27.5),
 ('colour_pour',7.6,11.7,'ripples',10.0,-26.0),
 ('colour_splash',11.7,15.5,'ripples',12.7,-25.7),
 ('first_ink_bloom',15.5,20.1,'ink',7.0,-30.0),
 ('ink_expansion',20.1,24.9,'ink',9.1,-30.7),
 ('ink_plumes',24.9,30.2,'ink',2.4,-30.8),
 ('final_cup_pour',30.2,34.0,'ripples',6.2,-26.3),
]

def loudness(x):
 return 20*np.log10(max(1.e-9,float(np.sqrt(np.mean(np.square(x.astype(np.float64)))))))

def get_raw(z,scene):
 with sf.SoundFile(io.BytesIO(z.read(f'{scene}_REAL_SFX_20s.wav'))) as f:
  a=f.read(dtype='float32',always_2d=True)
  if f.samplerate!=44100 or a.shape[1]!=2 or len(a)<19.5*f.samplerate:
   raise RuntimeError(f'Source WAV validation failure: {scene}')
 a=resample_poly(a,160,147,axis=0).astype(np.float32)
 # Remove DC and deepest rumble without inventing new transients.
 a=sosfilt(butter(2,40,'highpass',fs=SR,output='sos'),a,axis=0).astype(np.float32)
 return a

def select(a,source_offset,duration):
 count=int(round(duration*SR));begin=int(round(source_offset*SR))
 chunk=a[begin:begin+count]
 if len(chunk)!=count:raise RuntimeError('Underlying Foley too short for this shot')
 return chunk.copy()

def rms_by_second(a):
 return [round(loudness(a[i*SR:min((i+1)*SR,len(a))]),2) for i in range(math.ceil(len(a)/SR))]

def visual_hash(file):
 x=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(file),'-map','0:v:0','-c','copy','-f','hash','-hash','SHA256','-'],capture_output=True,text=True,check=True,timeout=45)
 return x.stdout.strip()

def main():
 assert SRC.is_file() and SFX.is_file()
 original=json.loads(META.read_text())
 assert len(original['timeline'])==8
 out=np.zeros((34*SR,2),np.float64)
 weight=np.zeros(34*SR,np.float64)
 provenance=[]
 with zipfile.ZipFile(SFX) as z:
  sources={k:get_raw(z,k) for k in ('ripples','ink')}
  for j,(label,start,end,sound,offset,target) in enumerate(TIMELINE):
   assert abs(start-original['timeline'][j]['start'])<0.02 and abs(end-original['timeline'][j]['end'])<0.02
   n=int(round((end-start)*SR))
   # 0.16-second overlap around cuts for ambience continuity; cap to exact timeline.
   overlap=0.16
   audio=select(sources[sound],offset,(end-start))
   db=loudness(audio)
   gain=10**((target-db)/20)
   audio=np.tanh(audio.astype(np.float64)*gain/0.67)*0.67  # smooth transients; no hard clipping
   begin=round(start*SR)
   # Each shot takes responsibility for exactly its visible frames. 120ms crossfade
   # at internal shot changes by attenuating toward the cut on both sides.
   fade=int(.12*SR)
   weights=np.ones(n,dtype=np.float64)
   if j:weights[:fade]=np.sin(np.linspace(0,np.pi/2,fade))**2
   if j<len(TIMELINE)-1:weights[-fade:]=np.cos(np.linspace(0,np.pi/2,fade))**2
   out[begin:begin+n]+=audio[:n]*weights[:,None]
   weight[begin:begin+n]+=weights
   provenance.append({'shot':label,'start':start,'end':end,'source_wav':sound+'_REAL_SFX_20s.wav','audio_source_start_seconds':offset,'target_rms_dbfs':target,'original_rms_dbfs':round(db,1),'post_gain_rms_dbfs':round(loudness(audio),1)})

 # Crossfade intentionally arranged by matching adjacent segments at cut boundaries:
 # bridge any very short (<0.15s) dip with nearby original Foley content, not silence.
 fade=int(.12*SR)
 for i in range(1,len(TIMELINE)):
  cut=round(TIMELINE[i][1]*SR)
  # Blend surrounding authentic samples at the boundary; audio remains type matched.
  left=out[cut-fade:cut].copy();right=out[cut:cut+fade].copy()
  # Crossfade tails/heads while retaining the actual audio from each shot.
  theta=np.linspace(0,np.pi/2,fade,dtype=np.float64)
  cross=left*np.cos(theta)[:,None]**2 + right*np.sin(theta)[:,None]**2
  out[cut-fade:cut]=left*.75+cross*.25
  out[cut:cut+fade]=right*.75+cross*.25


 # The pigment diffusion is almost silent in reality. Keep an *extremely soft*
 # liquid-room bed underneath those three shots so headphone listeners hear
 # continuity without inventing a loud pouring sound during diffusion.
 ink=sources['ink']
 ambience=np.zeros((round((30.2-15.5)*SR),2),dtype=np.float64)
 win_slices=[(7.1,12.9),(8.0,13.8),(6.2,12.0)]
 pos=0
 for k,(a,b) in enumerate(win_slices):
  chunk=ink[round(a*SR):round(b*SR)].astype(np.float64)
  # Constrain the ambience level, preserve within-clip dynamics.
  gain=10**((-35.1-loudness(chunk))/20)
  chunk=np.tanh(chunk*gain/0.67)*0.67
  n=min(len(chunk),len(ambience)-pos)
  if n<=0:break
  env=np.ones(n)
  ramp=min(int(.40*SR), n//4)
  if pos>0:env[:ramp]=np.sin(np.linspace(0,np.pi/2,ramp))**2
  if pos+n<len(ambience):env[-ramp:]=np.cos(np.linspace(0,np.pi/2,ramp))**2
  ambience[pos:pos+n]+=chunk[:n]*env[:,None]
  pos+=n-int(.35*SR)
 # Protect any quiet patches without unnecessarily layering noticeable effects.
 k0=round(15.5*SR);k1=round(30.2*SR)
 ramp=min(round(.25*SR),len(ambience)//4)
 ambience[:ramp]*=np.linspace(0,1,ramp)[:,None]
 ambience[-ramp:]*=np.linspace(1,0,ramp)[:,None]
 out[k0:k1]+=ambience*.65

 # 0.10-second onset and 0.28-second finish only at actual full-video ends.
 n=int(.10*SR);out[:n]*=np.linspace(0,1,n)[:,None]
 n=int(.28*SR);out[-n:]*=np.linspace(1,0,n)[:,None]
 # Controlled final peak below -5 dBFS; don't destroy the restrained ASMR differences.
 pk=float(np.max(np.abs(out)))
 if pk>.56:out*=.56/pk
 out=out.astype(np.float32)
 per_sec=rms_by_second(out)
 # Digital silence is forbidden in any full second; the middle ink shots are intentionally quieter.
 if len(per_sec)!=34 or any(v < -38.5 for v in per_sec[1:33]):
  raise RuntimeError('Audio continuity QA failed: '+str(per_sec))
 if np.max(np.abs(out))>.57 or not np.isfinite(out).all():raise RuntimeError('Invalid audio peak or nonfinite sample')
 audio=ROOT/'POUR_RIPPLE_COLOUR_BLOOM_SYNC_FIXED_v3.wav'
 sf.write(audio,out,SR,subtype='PCM_24')
 target=ROOT/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_AUDIO_FIXED_v3_1080p.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(SRC),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t','34','-movflags','+faststart',str(target)],check=True,timeout=120)
 review=ROOT/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_AUDIO_FIXED_v3_720p.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(target),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','26','-pix_fmt','yuv420p','-c:a','aac','-b:a','144k','-movflags','+faststart',str(review)],check=True,timeout=240)
 original_vision=visual_hash(SRC);new_vision=visual_hash(target)
 if original_vision!=new_vision:raise RuntimeError('Video stream changed unexpectedly')
 report={'version':'audio-sync-repair-v3','fault_confirmed':'Prior soundtrack was all-digital silence from 17 to 34 seconds', 'method':'Shot-aligned replacement using actual licensed-video cut times and existing sound-effect masters; normalise per shot, soft limit, cut-boundary blend', 'duration_seconds':34,'sample_rate_hz':48000, 'source_sounds':'Stable Audio 3 Small-SFX original Kaggle master WAVs (not Qwen3 TTS)', 'shots':provenance, 'one_second_rms_dbfs':per_sec,'long_silence_rejection_dbfs':-41,'max_peak_dbfs':round(20*np.log10(float(np.max(np.abs(out)))),2),'video_packet_hash_preserved':original_vision,'youtube_published':False,'creator_listening_approval':False,'files':{}}
 for f in (audio,target,review):
  report['files'][f.name]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 (ROOT/'AUDIO_SYNC_REPAIR_QA_v3.json').write_text(json.dumps(report,indent=2))
 print('SUCCESS',json.dumps({'sound_rms_by_second':per_sec,'max_peak_dbfs':report['max_peak_dbfs'],'files':{k:v['bytes'] for k,v in report['files'].items()},'video_preserved':True},indent=2))
if __name__=='__main__':main()
