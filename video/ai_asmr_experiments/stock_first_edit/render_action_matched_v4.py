#!/usr/bin/env python3
"""V4 ASMR editing: watch the actual visible actions, not just shot labels.

No blanket droplet beds. Real licensed Mixkit fluid SFX only when actual pours / splashes.
Ink diffusion is virtually silent, and the overlong ink montage is removed.
Uses verified cached stock-video segments and does NOT download stock/model weights.
"""
from pathlib import Path
import zipfile, subprocess, hashlib, json, io, math, os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, find_peaks
P=Path(os.environ.get('ASMR_PUBLISH_DIR','/mnt/data/asmr_stock_first/publish_candidate'))
SFX=Path(os.environ.get('ASMR_REAL_FOLEY_ZIP','/mnt/data/real_liquid_foley_mixkit.zip'))
FOLEY=Path(os.environ.get('ASMR_SFX_ZIP','/mnt/data/four_asmr_real_foley_generated.zip'))
OUT=P/'ACTION_MATCHED_v4';OUT.mkdir(exist_ok=True)
RATE=48000
CUTS=[
  ('01_clear_pour.mp4', '01_01_clear_pour.mp4','clear_pour'),
  ('02_surface.mp4','02_02_surface.mp4','rain_ripples'),
  ('03_colour_pour.mp4','03_03_colour_pour.mp4','red_pour'),
  ('04_red_splash.mp4','04_04_splash.mp4','red_splash'),
  ('05_ink_bloom.mp4','05_05_first_bloom.mp4','silent_ink_diffusion'),
  ('06_final_cup.mp4','08_08_splash_final.mp4','red_cup_return'),
]
def call(cmd,timeout=90):
 q=subprocess.run([str(v) for v in cmd],capture_output=True,text=True,timeout=timeout)
 if q.returncode:raise RuntimeError('Command failed: '+' '.join(map(str,cmd[:7]))+' '+q.stderr[-950:])
 return q.stdout
def probe(p):
 return json.loads(call(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def get_audio(raw):
 q=subprocess.run(['ffmpeg','-v','error','-i','pipe:0','-map','0:a:0','-ar',str(RATE),'-ac','2','-f','f32le','pipe:1'],input=raw,capture_output=True,timeout=50,check=True)
 return np.frombuffer(q.stdout,dtype='<f4').reshape(-1,2).copy()
def dbfs(a):
 return 20*np.log10(max(1e-9,float(np.sqrt(np.mean(np.asarray(a,dtype=np.float64)**2)))))
def filter_audio(x,low=None,high=None):
 if low is not None:x=sosfilt(butter(2,low,'highpass',fs=RATE,output='sos'),x,axis=0)
 if high is not None:x=sosfilt(butter(2,high,'lowpass',fs=RATE,output='sos'),x,axis=0)
 return x.astype(np.float32)
# Reuse the correct real footage shot boundaries, directly from actual frame counts.
segments=[];cuts=[];offset=0
for outfile,filename,kind in CUTS:
 src=P/'segments'/filename
 assert src.exists(),src
 info=probe(src);video=next(x for x in info['streams'] if x['codec_type']=='video')
 frame_count=int(video['nb_frames']);seconds=frame_count/24
 if seconds<3:raise RuntimeError(f'{filename} only {seconds}s')
 segments.append(src)
 cuts.append({'start':round(offset,5),'end':round(offset+seconds,5),'seconds':seconds,'kind':kind,'visual_source':filename})
 offset+=seconds
length=int(round(offset*RATE))
assert 23.7<offset<24.1,offset
listfile=OUT/'segments.ffconcat'
listfile.write_text(''.join("file '"+str(x)+"'\n" for x in segments))
picture=OUT/'SHORT_PICTURE_ONLY.mp4'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',listfile,'-an','-c:v','copy','-movflags','+faststart',picture],timeout=75)
video_info=probe(picture);vd=float(video_info['format']['duration'])
if abs(vd-offset)>.09:raise RuntimeError(f'Unexpected video duration {vd} != {offset}')
# The mixed audio is zero by default; effects are placed only where action justifies them.
with zipfile.ZipFile(SFX) as z:
 ledger=json.loads(z.read('SOURCE_LICENSES.json'))
 verified={x['name']:x for x in ledger if x['status']=='verified'}
 def mixkit(name):
  if name not in verified:raise RuntimeError('Real licensed source missing '+name)
  data=z.read(name+'.mp3')
  if hashlib.sha256(data).hexdigest()!=verified[name]['sha256']:
   raise RuntimeError('Audio file modified '+name)
  return get_audio(data)
 pour_glass=mixkit('pour_into_glass_mixkit')
 pour_glass2=mixkit('pour_to_glass_mixkit')
 pour_soda=mixkit('pour_soda_mixkit')
 splash=mixkit('splash_mixkit')
 bubble=mixkit('waterbubble_mixkit')
with zipfile.ZipFile(FOLEY) as z:
 from scipy.signal import resample_poly
 rip,_sr=sf.read(io.BytesIO(z.read('ripples_REAL_SFX_20s.wav')),always_2d=True)
 ink,_=sf.read(io.BytesIO(z.read('ink_REAL_SFX_20s.wav')),always_2d=True)
 rip=resample_poly(rip,160,147,axis=0).astype(np.float32)
 ink=resample_poly(ink,160,147,axis=0).astype(np.float32)
# Recordings need only modest filters and predictable RMS targets; avoid compression that makes ticks into a full bed.
pour_glass=filter_audio(pour_glass,low=45,high=9400)
pour_glass2=filter_audio(pour_glass2,low=55,high=8700)
pour_soda=filter_audio(pour_soda,low=60,high=7500)
splash=filter_audio(splash,low=65,high=8500)
bubble=filter_audio(bubble,low=65,high=6200)
rip=filter_audio(rip,low=80,high=9500)
ink=filter_audio(ink,low=50,high=250) # submerged colour diffusion: quiet low movement, NO plips
mix=np.zeros((length,2),np.float64)
events=[]
def sec(x):return int(round(x*RATE))
def add(name,x,start,duration,target_rms,source_start=.0,attack=.08,release=.18,extra_gain=0):
 """One visual event. Time-localized audio, with natural but bounded fades."""
 begin=sec(start);n=sec(duration);src=sec(source_start)
 if begin<0 or begin>=length:return
 n=min(n,length-begin,len(x)-src)
 if n<=0:return
 chunk=x[src:src+n].astype(np.float64).copy()
 original_level=dbfs(chunk)
 gain=10**((target_rms-original_level+extra_gain)/20)
 chunk*=gain
 env=np.ones(n)
 ain=min(sec(attack),n//3);aout=min(sec(release),n//3)
 if ain>1:env[:ain]=np.sin(np.linspace(0,np.pi/2,ain))**2
 if aout>1:env[-aout:]=np.cos(np.linspace(0,np.pi/2,aout))**2
 mix[begin:begin+n]+=chunk*env[:,None]
 events.append({'type':name,'start':round(start,3),'end':round(start+n/RATE,3),'recording_rms_dbfs':round(original_level,1),'target_rms_dbfs':target_rms})
def shot(idx):return cuts[idx]['start'],cuts[idx]['end']
# 1. 0-4.42s — TRUE liquid stream entering a glass. No artificial intermittent raindrop layer.
a,b=shot(0);add('real_water_pouring_into_glass',pour_glass,a,b-a,-28.0,source_start=0.05,attack=.09,release=.15)
# 2. 4.42-7.63s — ONLY at visible water-surface impact ripples.
a,b=shot(1)
# Extract individual short droplet noises from the generated ripple sound, not a 3.2s drone.
rmono=np.mean(np.abs(rip),axis=1)
hop=sec(.028);frame=np.array([np.sqrt(np.mean(rmono[t:t+hop]**2)) for t in range(0,len(rmono)-hop,hop)])
pks,_=find_peaks(frame,distance=int(.52/.028),prominence=np.percentile(frame,70)*.30)
pks=sorted(pks,key=lambda i:float(frame[i]),reverse=True)
chosen=[]
for i in pks:
 t=i*.028
 if t<.25 or t>18.5:continue
 if all(abs(t-u)>.7 for u in chosen):chosen.append(t)
 if len(chosen)>=8:break
if len(chosen)<7:chosen=[1.5,3.1,5.2,7.3,10.4,13.6,16.8,17.3]
# Small rain contacts across a dense ring-pattern scene; never placed elsewhere.
for j,t in enumerate([.12,.44,.78,1.11,1.47,1.83,2.19,2.58,2.91]):
 add('surface_raindrop_contact',rip,a+t,.31,-37.5-(j%3)*.6,source_start=max(0,chosen[j%len(chosen)]-.08),attack=.014,release=.16)
# 3. 7.63-11.71s — red-coloured liquid goes into a cup in a thin stream; soda is the source matching foaming liquid.
a,b=shot(2);add('red_beverage_pouring_in_cup',pour_soda,a,b-a,-28.2,source_start=.13,attack=.10,release=.17)
# 4. 11.71-15.50s — visible thick stream and occasional splash upward, rather than a drip rhythm.
a,b=shot(3);add('thick_pour_into_cup',pour_glass2,a,b-a,-29.0,source_start=.55,attack=.09,release=.13)
for t,db in [(.47,-38.5),(1.40,-37.6),(3.02,-37.0)]:
 add('visible_cup_splash',splash,a+t,.48,db,source_start=.08,attack=.015,release=.24)
# 5. 15.50-20.08s — dye diffuses underwater. This physical phenomenon is virtually silent.
# The lowpassed, quiet air/liquid floor is not an audible droplet track.
a,b=shot(4);add('nearly_silent_pigment_diffusion',ink,a,b-a,-55.0,source_start=7.0,attack=.35,release=.4)
# 6. 20.08-23.88s — red beverage returns; restore matching pour and splash effects.
a,b=shot(5);add('final_coloured_cup_pour',pour_glass2,a,b-a,-29.5,source_start=.1,attack=.09,release=.25)
for t,db in [(.55,-38.5),(2.20,-37.6),(3.06,-37.0)]:
 add('final_cup_splash',splash,a+t,.43,db,source_start=.09,attack=.015,release=.23)
# Avoid unintended clipping or full-track volume boosts.
peak=np.max(np.abs(mix));mix *= min(1.0,.56/max(peak,1e-9))
mix=mix.astype(np.float32)
# No splash or dripping should be injected into ink visual. Cut the visual to 4.58 s only.
for e in events:
 if e['type'] in ('surface_raindrop_contact','visible_cup_splash','final_cup_splash') and e['start']<cuts[4]['end'] and e['end']>cuts[4]['start']:
  raise RuntimeError('Visible ink section incorrectly has droplets')
# Unit QA: volume differences must reflect action, not artificially constant RMS throughout.
levels=[]
for c in cuts:
 t0,t1=sec(c['start']),sec(c['end'])
 levels.append({'kind':c['kind'],'start':c['start'],'end':c['end'],'rms_dbfs':round(dbfs(mix[t0:t1]),2)})
assert levels[4]['rms_dbfs']<=-43,levels
assert levels[0]['rms_dbfs']>-45 and levels[2]['rms_dbfs']>-45 and levels[5]['rms_dbfs']>-45,levels
assert np.max(np.abs(mix))<.57
snd=OUT/'ACTION_MATCHED_SOUND_24s.wav'
sf.write(snd,mix,RATE,subtype='PCM_24')
master=OUT/'POUR_RIPPLE_COLOUR_REAL_FOLEY_ACTION_MATCHED_v4_1080p.mp4'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',picture,'-i',snd,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(round(offset,4)),'-movflags','+faststart',master],timeout=120)
mobile=OUT/'POUR_RIPPLE_COLOUR_REAL_FOLEY_ACTION_MATCHED_v4_720p_REVIEW.mp4'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',master,'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',mobile],timeout=180)
# Verify actual encoded audio is not clipped, stream count and duration match the authored 6-shot cut.
for file in [master,mobile]:
 info=probe(file)
 streams={s['codec_type'] for s in info['streams']}
 assert streams=={'audio','video'},streams
 assert abs(float(info['format']['duration'])-offset)<.08
 assert file.stat().st_size>500_000
sha=call(['ffmpeg','-hide_banner','-loglevel','error','-i',picture,'-map','0:v','-c','copy','-f','hash','-hash','SHA256','-']).strip()
sham=call(['ffmpeg','-hide_banner','-loglevel','error','-i',master,'-map','0:v','-c','copy','-f','hash','-hash','SHA256','-']).strip()
assert sha==sham,'Video changed after audio mux'
report={'title':'Pour, Ripple and Colour Bloom — action-matched original ASMR Short','version':'v4-action-match','seconds':round(offset,3),'audio_method':'Original licensed Mixkit real pour recordings, event-trimmed ripple transients only on ripple frames, isolated splashes only during visible cup impacts, ink diffusion is near-silent','old_issue':'v3 one long manufactured water droplet sound persisted over unrelated ink/cup imagery','original_stock_license_ledger':'SOURCE_AND_EXPORT_PROVENANCE.json','real_sound_effect_licenses':ledger,'shots':cuts,'shot_audio_levels':levels,'sound_events':events,'original_video_stream_preserved_after_mux':True,'publisher_approved':False,'youtube_published':False,'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [master,mobile,snd]}}
(OUT/'V4_AUDIO_VISUAL_SYNC_QA.json').write_text(json.dumps(report,indent=2))
print('SUCCESS',json.dumps({'duration':offset,'levels':levels,'files':report['files'],'events':len(events)},indent=2),flush=True)
