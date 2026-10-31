#!/usr/bin/env python3
"""V5: frame-reviewed ASMR Foley; action cues, not blanket scene-labelled loops.

Real Mixkit Free SFX in cached artefact; existing licensed video copied unchanged.
The no-extended-silence rule applies even to quiet visual material; block until repaired.
"""
import os,io,json,hashlib,zipfile,subprocess,math,platform
from pathlib import Path
import cv2
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt,resample_poly,find_peaks

ROOT=Path(os.environ.get('ASMR_PUBLISH_DIR','/mnt/data/asmr_stock_first/publish_candidate'))
SOURCE=Path(os.environ.get('ASMR_VIDEO_SOURCE',str(ROOT/'ACTION_MATCHED_v4'/'SHORT_PICTURE_ONLY.mp4')))
REAL=Path(os.environ.get('ASMR_REAL_FOLEY_ZIP','/mnt/data/real_liquid_foley_mixkit.zip'))
GENERATED=Path(os.environ.get('ASMR_SFX_ZIP','/mnt/data/four_asmr_real_foley_generated.zip'))
OUT=ROOT/'ACTION_MATCHED_v5';OUT.mkdir(parents=True,exist_ok=True)
FPS=24;SR=48000;NFRAMES=573;SECONDS=NFRAMES/FPS
SHOTS=[
 ('clear_water_into_glass',0,106),
 ('rain_making_surface_ripples',106,183),
 ('thin_coloured_pour',183,281),
 ('thicker_coloured_splash',281,372),
 ('underwater_ink_diffusion',372,482),
 ('final_cup_splash',482,573),
]
# Action-event anchors manually checked against actual exported frames; no regular grid.
# Red marks are audio triggers ~0.12s before the measured visible splash fluid maxima;
# the Mixkit SFX transient peaks ~0.12s after its trimmed 0.32s sample offset.
IMPACTS={
 'rain_making_surface_ripples': [4.51,5.06,5.80,6.46,7.19],
 'thin_coloured_pour': [10.505,11.380],
 'thicker_coloured_splash': [11.730,12.700,14.210,14.710,14.920],
 'final_cup_splash': [20.710,21.210,22.630,22.950],
}

def run(args,timeout=150):
 p=subprocess.run([str(v) for v in args],capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(f'Command error {args[:5]} {p.stderr[-1300:]}')
 return p.stdout

def probe(file):
 return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(file)]))

def wav_real(blob):
 p=subprocess.run(['ffmpeg','-v','error','-i','pipe:0','-ar',str(SR),'-ac','2','-f','f32le','pipe:1'],input=blob,capture_output=True,timeout=30,check=True)
 return np.frombuffer(p.stdout,dtype='<f4').reshape(-1,2).copy()

def rms(x):return float(np.sqrt(np.mean(np.asarray(x,dtype=np.float64)**2)))
def db(x):return 20*math.log10(max(1.e-10,rms(x)))
def band(x,lo,hi):return sosfilt(butter(2,[lo,hi],btype='bandpass',fs=SR,output='sos'),x,axis=0).astype(np.float32)

def visual_hash(file):
 return run(['ffmpeg','-hide_banner','-v','error','-i',str(file),'-map','0:v:0','-c','copy','-f','hash','-hash','SHA256','-']).strip()

# Standalone regeneration from the eight cached original licensed picture segments.
# This eliminates redundant V3/V4 audio mix and avoids any network or GPU use.
if not SOURCE.is_file():
 names=['01_01_clear_pour.mp4','02_02_surface.mp4','03_03_colour_pour.mp4',
        '04_04_splash.mp4','05_05_first_bloom.mp4','08_08_splash_final.mp4']
 clips=[ROOT/'segments'/n for n in names]
 if not all(f.is_file() for f in clips):
  raise RuntimeError('Missing cached licensed picture segments: '+str([str(f) for f in clips if not f.exists()]))
 SOURCE.parent.mkdir(parents=True,exist_ok=True)
 manifest=OUT/'picture_segments.ffconcat'
 manifest.write_text(''.join("file '"+str(f)+"'\n" for f in clips))
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(manifest),'-an','-c:v','copy','-movflags','+faststart',SOURCE])
v=probe(SOURCE);duration=float(v['format']['duration']);tracks=[x for x in v['streams'] if x['codec_type']=='video']
assert len(tracks)==1 and 23.7<duration<24.1,(duration,tracks)
frames=int(tracks[0]['nb_frames']);assert frames==NFRAMES,frames
assert SOURCE.is_file() and REAL.is_file() and GENERATED.is_file()
assert sum(b-a for _,a,b in SHOTS)==NFRAMES
with zipfile.ZipFile(REAL) as z:
 ledger=json.loads(z.read('SOURCE_LICENSES.json'))
 rights={row['name']:row for row in ledger if row.get('status')=='verified'}
 def load(key):
  row=rights.get(key)
  if row is None:raise RuntimeError('Missing licensed recording '+key)
  raw=z.read(key+'.mp3')
  if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('SFX hash mismatch: '+key)
  return wav_real(raw)
 sounds={key:load(key) for key in ['pour_into_glass_mixkit','pour_to_glass_mixkit','pour_soda_mixkit','splash_mixkit','waterbubble_mixkit']}
with zipfile.ZipFile(GENERATED) as z:
 rip,sr=sf.read(io.BytesIO(z.read('ripples_REAL_SFX_20s.wav')),always_2d=True,dtype='float32')
assert sr==44100
rip=resample_poly(rip,160,147,axis=0).astype('float32')

sounds['pour_into_glass_mixkit']=band(sounds['pour_into_glass_mixkit'],60,9500)
sounds['pour_to_glass_mixkit']=band(sounds['pour_to_glass_mixkit'],60,9500)
sounds['pour_soda_mixkit']=band(sounds['pour_soda_mixkit'],60,9500)
sounds['splash_mixkit']=band(sounds['splash_mixkit'],80,8500)
sounds['waterbubble_mixkit']=band(sounds['waterbubble_mixkit'],75,6500)
sounds['rip']=band(rip,120,9000)
# Colour diffusion is practically silent, but a -56dB low-frequency underwater bed
# avoids an abrupt digital-audio dropout. Its >300Hz plips are filtered away.
with zipfile.ZipFile(GENERATED) as z:
 ink_raw,sr2=sf.read(io.BytesIO(z.read('ink_REAL_SFX_20s.wav')),always_2d=True,dtype='float32')
assert sr2==44100
ink_raw=resample_poly(ink_raw,160,147,axis=0).astype('float32')
sounds['submerged_room_tone']=band(ink_raw,60,250)


# Measured coloured-splash region from actual video. Converts visible area into a modest
# rolling intensity envelope; keeps big splash moments louder without synthetic drop loops.
def fluid_motion_measure():
 path=os.environ.get('ASMR_ACTION_DATA','/mnt/data/asmr_stock_first/v5_inspection/red_action_metrics.npy')
 if Path(path).exists():
  m=np.load(path);return m[:,0],m[:,2]
 cap=cv2.VideoCapture(str(SOURCE));rows=[];k=0
 while True:
  ok,frame=cap.read()
  if not ok:break
  frame=cv2.resize(frame,(360,640));hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
  mask=(((hsv[:,:,0]<13)|(hsv[:,:,0]>145))&(hsv[:,:,1]>110)&(hsv[:,:,2]>75))
  idx=next((i for i,(_,a,b) in enumerate(SHOTS) if a<=k<b),len(SHOTS)-1)
  lim=.63 if idx==2 else .57
  area=int(mask[int(.31*640):int(lim*640),int(.25*360):int(.83*360)].sum())
  rows.append((k/FPS,area));k+=1
 cap.release();q=np.array(rows,dtype=float);return q[:,0],q[:,1]

vtimes,area=fluid_motion_measure()
assert len(vtimes)>=565
mix=np.zeros((NFRAMES*SR//FPS,2),dtype=np.float64)
events=[]

def cue(kind,source,t0,seconds,src_t0,level,fade_in=.04,fade_out=.13,pan=0.0,driven=False):
 x=sounds[source];pos=int(round(src_t0*SR));n=min(int(round(seconds*SR)),len(x)-pos,len(mix)-int(round(t0*SR)))
 if n<SR*.04:raise RuntimeError('Bad short cue '+kind)
 clip=x[pos:pos+n].astype(np.float64).copy()
 base=db(clip);clip *= 10**((level-base)/20)
 if driven:
  ts=t0+np.arange(n,dtype=float)/SR
  vals=np.interp(ts,vtimes,area)
  low=np.percentile(vals,20);high=np.percentile(vals,88)
  unit=np.clip((vals-low)/max(1,high-low),0,1)
  # 3-dB controlled variation. Avoid obvious pumping or loudness jumps.
  env_loud=10**(((-1.1+2.3*unit)/20))
  clip*=env_loud[:,None]
 fi=min(int(fade_in*SR),n//3);fo=min(int(fade_out*SR),n//3)
 env=np.ones(n)
 if fi>1:env[:fi]=np.sin(np.linspace(0,math.pi/2,fi))**2
 if fo>1:env[-fo:]=np.cos(np.linspace(0,math.pi/2,fo))**2
 clip*=env[:,None]
 if kind=='barely_audible_underwater_room_tone':
  # The generator's near-silent bed contains occasional rogue impulses that can
  # become a noticeable low-frequency THUMP after RMS normalisation.
  clip=.006*np.tanh(clip/.006)
 # Gentle binaural distribution, preserve spatial clarity without unnatural stereo motion.
 if pan:
  clip[:,0]*=math.cos((pan+1)*math.pi/4)*math.sqrt(2)
  clip[:,1]*=math.sin((pan+1)*math.pi/4)*math.sqrt(2)
 i=int(round(t0*SR));mix[i:i+n]+=clip
 events.append(dict(event=kind,start=round(t0,3),end=round(t0+n/SR,3),source=source,source_offset=src_t0,source_rms_dbfs=round(base,2),target_rms_dbfs=level,action_dependent_gain=driven))

# Actual stream is visible for entire initial shot. Use recording's active 0.7–5.1s,
# NOT first half-second of silence in the stock sound. Smooth out smoothly at the cut.
cue('continuous_clear_stream_in_glass','pour_to_glass_mixkit',0.0,106/FPS,.72,-31.0,fade_in=.085,fade_out=.11)
# Only intermittent soft contacts for raindrops making rings; no 3-second drip bed.
# Use different source slices/positions to avoid a repeating same metallic plink.
rain_sources=[2.15,5.01,7.68,10.55,14.35]
for j,(at,src) in enumerate(zip(IMPACTS['rain_making_surface_ripples'],rain_sources)):
 cue('visible_rain_surface_contact','rip',at,.19,src,-40.5+(j%3)*.8,fade_in=.012,fade_out=.075,pan=[-.25,.1,.3,-.2,.2][j])
# Visible continuous stream at colour pour, volume follows measured colour/splash activity.
cue('thin_red_stream_while_visible','pour_soda_mixkit',183/FPS,98/FPS,.18,-33.1,fade_in=.09,fade_out=.14,driven=True)
cue('stronger_red_stream_while_visible','pour_to_glass_mixkit',281/FPS,91/FPS,.76,-32.6,fade_in=.12,fade_out=.11,driven=True)
# Red splash impulses derive from the frame-inspected maxima and are not periodic.
# Start a few frames before peak where splash breaks the liquid surface.
for j,at in enumerate(IMPACTS['thin_coloured_pour']+IMPACTS['thicker_coloured_splash']):
 strength=-39.3 if at<11.71 else (-37.8 if at<14.2 else -34.5)
 if at>=14.7:strength=-34.0
 cue('red_splash_at_visible_impact','splash_mixkit',at,.35,.32,strength,fade_in=.008,fade_out=.13,pan=[-.09,0,.12,.04,-.08,.06,.03][j])
# The underwater pigment cloud has no identifiable acoustic impact. A *faint*,
# low-frequency non-droplet room texture preserves listening continuity.
cue('barely_audible_underwater_room_tone','submerged_room_tone',15.50,110/FPS,7.6,-56.0,fade_in=.5,fade_out=.55)
# Never add rain, splash, bubble or drip during this nearly silent interval.
# Last shot has a running red stream and a handful of stronger visible splashes.
cue('final_red_cup_stream_while_visible','pour_soda_mixkit',482/FPS,91/FPS,.65,-32.4,fade_in=.10,fade_out=.15,driven=True)
for j,at in enumerate(IMPACTS['final_cup_splash']):
 cue('last_cup_splash_at_visible_impact','splash_mixkit',at,.35,.32,(-34.2 if j==1 else -36.7),fade_in=.008,fade_out=.13,pan=[.05,-.10,.12,0][j])
# All events validated against visual action regions; no events in ink.
assert all(not(15.5 <= e['start'] < 20.08) for e in events if e['event']!='barely_audible_underwater_room_tone')
# Any cue overlap crossing the ink cut is forbidden; trim early-event tail if necessary.
assert not any(e['end']>15.5 and e['start']<15.5 for e in events),[e for e in events if e['end']>15.5 and e['start']<15.5]
# Prior V5 enforced a near-silent ink region. That is now a production blocker, not a target.
peak=float(np.max(abs(mix)));limit=10**(-5.0/20)
if peak>limit:mix*=limit/peak
assert np.isfinite(mix).all()
samples=mix.astype(np.float32)

# Distinctive audio transitions at shot boundaries are checked, not continuous sound.
per_scene=[]
for name,st,en in SHOTS:
 a=samples[int(st*SR/FPS):int(en*SR/FPS)];per_scene.append(dict(name=name,start=round(st/FPS,4),end=round(en/FPS,4),rms_dbfs=round(db(a),2),peak_dbfs=round(20*math.log10(max(1.e-10,float(np.max(abs(a))))),2)))
# A quiet shot must still contain believable audible physical texture.
assert all(per_scene[i]['rms_dbfs']>-43 for i in [0,2,3,5]),per_scene
AUDIO=OUT/'ASMR_V5_REAL_FOLEY_ACTION_CUES_24s.wav';sf.write(AUDIO,samples,SR,subtype='PCM_24')
MASTER=OUT/'POUR_RIPPLE_COLOUR_ASMR_V5_FRAME_SYNC_1080p.mp4'
REVIEW=OUT/'POUR_RIPPLE_COLOUR_ASMR_V5_FRAME_SYNC_720p.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',SOURCE,'-i',AUDIO,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(SECONDS),'-movflags','+faststart',MASTER],timeout=120)
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',MASTER,'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',REVIEW],timeout=180)
assert visual_hash(SOURCE)==visual_hash(MASTER),'Original video stream unexpectedly changed'
for f in [MASTER,REVIEW]:
 i=probe(f)
 assert abs(float(i['format']['duration'])-SECONDS)<.08
 assert set(x['codec_type'] for x in i['streams'])=={'audio','video'}
 assert f.stat().st_size>400000
# Decode final AAC audio to ensure no surprise encoder discontinuity / clipping.
aac=subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(MASTER),'-map','0:a:0','-ar',str(SR),'-ac','2','-f','f32le','pipe:1'],capture_output=True,timeout=50,check=True)
dec=np.frombuffer(aac.stdout,dtype='<f4').reshape(-1,2)
assert abs(len(dec)/SR-SECONDS)<.09
assert np.max(abs(dec))<.71
# Do not turn quiet material into a reason to bypass the mandatory silence scan.
# Require the same post-export no-silence gate as the 47-format Satisfying Studio.
# Do not cheat this check with generated constant hiss or unrelated events.
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'satisfying_studio'/'production'))
from audio_continuity_gate import check_audio
continuity=check_audio(MASTER)
preview_continuity=check_audio(REVIEW)
for file,report in [(MASTER,continuity),(REVIEW,preview_continuity)]:
 report["master_sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
 report["frame_sync_artist_approved"]=False
 (OUT/(file.stem+"_AUDIO_CONTINUITY_QA.json")).write_text(json.dumps(report,indent=2))
if not continuity["passed"] or not preview_continuity["passed"]:
 raise RuntimeError("ASMR V5 audio rejected: near-silent intervals detected; find genuine source-appropriate Foley, align it to actual frames, re-export and re-audition. Master="+str(continuity["gaps"])+" preview="+str(preview_continuity["gaps"]))
# Compare shot-level level variations: ink section should be much quieter than pours.
per_sec=[round(db(dec[i*SR:(i+1)*SR]),1) for i in range(math.ceil(SECONDS))]
manifest={
 'version':'v5-frame-reviewed-events-not-blanket-loops','status':'RENDERED_TECHNICALLY_VERIFIED_PENDING_HUMAN_LISTENING',
 'frame_review':'Manual frame contact sheets (12 samples per shot), 24fps source; measured HSV coloured-fluid splash maxima and aligned each real splash SFX peak within a few frames',
 'duration_seconds':SECONDS,'video_frames':frames,'shots':per_scene,'impact_visual_anchors_seconds':IMPACTS,
 'real_audio_sources':[{k:r.get(k) for k in ['name','page','license','sha256','duration']} for r in ledger if r.get('status')=='verified'],
 'events':events,'encoded_audio_rms_by_second_dbfs':per_sec,
 'ink_should_be_silent':False,'ink_has_no_droplet_events':True,'ink_decoded_rms_dbfs':round(db(dec[int(15.7*SR):int(19.9*SR)]),2),
 'video_stream_sha256':visual_hash(MASTER),'sfx_source_hash_verification':True,
 'audio_continuity':continuity,'creator_audio_approval':False,'youtube_published':False,
 'files':{f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [MASTER,REVIEW,AUDIO]}
}
(OUT/'V5_FRAME_MATCH_AUDIO_QA.json').write_text(json.dumps(manifest,indent=2))
(OUT/'V5_YOUTUBE_REVIEW_NOTES.txt').write_text('''V5 — frame-reviewed ASMR Foley, not published.\nSource: original 23.875s Mixkit/Pexels stock composite. No visuals regenerated.\n0–4.417s: true clear stream sound matching visible glass pour.\n4.417–7.625s: only five very soft water-surface impact clicks.\n7.625–15.500s: real drink-pour sound varying with visible splash area; irregular short splash hits linked to actual frames.\n15.500–20.083s: quiet ink motion MUST have a justified audible texture, not fake drops or digital silence.\n20.083–23.875s: real cup pour with isolated visible splash impacts.\nRecordings: Mixkit Free Sound Effects source #2826, #1324, #2833, #1311 plus the earlier independently generated ripple Foley.\nApproval required: watch and listen at phone volume and with headphones before YouTube upload.\n''')
print('SUCCESS V5',json.dumps({'duration':SECONDS,'shots':per_scene,'events':len(events),'peak':float(np.max(abs(dec))),'ink_rms':manifest['ink_decoded_rms_dbfs'],'files':manifest['files']},indent=2),flush=True)
