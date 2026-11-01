#!/usr/bin/env python3
"""Synchronize previously licensed CC0 recorded crunch to revised 3D fracture.
Original reference creator's audio is not used. Preserve continuous recorded Foley;
shift individual genuine crack bursts rather than globally time-stretching a mix.
"""
import numpy as np,soundfile as sf,json,hashlib,os
from pathlib import Path
p=Path(os.environ.get('MANGO_LICENSED_FOLEY_SOURCE','/mnt/data/crunchy_mango_delivery/Glossy_Mango_Crunch_CC0_Foley_FINAL_BOOST_48k24b.wav'))
out=Path(os.environ.get('MANGO_RETIMED_FOLEY_OUTPUT','/mnt/data/mango_edit/Glossy_Mango_Organic_Crackle_Foley_v3_48k24b.wav'))
a,sr=sf.read(p,dtype='float64'); assert sr==48000 and len(a)==288000 and a.shape[1]==2
b=a.copy()

def envelope_dip(start,end,reduction=.1,feather=.045):
    N=len(a);t=np.arange(N)/sr
    attack=np.clip((t-start)/feather,0,1)
    release=np.clip((end-t)/feather,0,1)
    m=np.minimum(attack,release)
    # sin half window to avoid audible hard edits
    m=np.sin(m*np.pi/2)**2
    return 1-(1-reduction)*m
# Suppress early sharp noises while preserving genuine pre-snap handling,
# because actual shell starts opening only in the later frame sequence.
for t0,t1,db in [(1.85,2.00,.43),(2.08,2.63,.12),(3.41,3.61,.22),(4.76,4.96,.18),(5.02,5.28,.13)]:
    b*=envelope_dip(t0,t1,db)[:,None]

def place_recorded_burst(source_peak,target,pre,post,scale=1):
    start=max(0,int(round((source_peak-pre)*sr)))
    end=min(len(a),int(round((source_peak+post)*sr)))
    piece=a[start:end].copy()
    L=len(piece);fade=int(.014*sr)
    # Smooth but keep recorded attack intact.
    piece[:fade]*=np.linspace(0,1,fade)[:,None]
    piece[-fade:]*=np.linspace(1,0,fade)[:,None]
    at=int(round((target-pre)*sr));tail=min(len(b),at+L)
    assert at>=0 and tail>at
    b[at:tail]+=scale*piece[:tail-at]
    return {'source_peak_s':source_peak,'target_peak_s':target,'source':'existing independently licensed CC0 mango crack mix','source_offset_s':round(target-source_peak,5),'gain':scale}

cue=[]
cue.append(place_recorded_burst(2.20,2.56,.043,.175,.89)) # start of real 3D shell split, around video frame 62
cue.append(place_recorded_burst(2.47,2.88,.038,.125,.60)) # two physical flakes dislodge
cue.append(place_recorded_burst(3.45,3.50,.05,.16,.87))   # fragments tumble/settle
# Loudness: do not normalize the whole bed to artificially strong continuous crunch.
# Peak limit only for safety, preserve microdynamics.
peak=float(np.max(np.abs(b)));b*=min(1.0, .79/max(peak,1e-7))
n=int(.027*sr);b[:n]*=np.sin(np.linspace(0,np.pi/2,n))[:,None];b[-n:]*=np.sin(np.linspace(np.pi/2,0,n))[:,None]
sf.write(out,b,sr,subtype='PCM_24')
# Short window levels for the source-to-visible-frame review.
window=int(.02*sr);levels=[]
for i in range(0,len(b),window):
    part=b[i:i+window];levels.append({'s':round(i/sr,3),'dbfs':round(float(20*np.log10(max(1e-9,np.sqrt(np.mean(part*part))))),2)})
manifest={'kind':'Revised genuine CC0 ASMR audio, onset retimed to actual organic 3D shell reveal','original_cc0_mix_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'render_frame_rate':24,'visual_first_reveal_frames':'60-63','primary_crunch_visual_target_frame':round(2.56*24),'secondary_crumble_visual_target_frame':round(3.50*24),'genuine_recorded_foley_events':cue,'preserves_48khz_pcm_24bit_stereo':True,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'output_peak':float(np.max(np.abs(b))),'twenty_millisecond_audio_dbfs':levels,'user_approved_this_revision':False,'human_headphone_audition_done':False}
(Path(os.environ.get('MANGO_SYNC_REPORT','/mnt/data/mango_edit/CRUNCHY_MANGO_v3_sound_sync_report.json'))).write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:v for k,v in manifest.items() if k!='twenty_millisecond_audio_dbfs'},indent=2))
