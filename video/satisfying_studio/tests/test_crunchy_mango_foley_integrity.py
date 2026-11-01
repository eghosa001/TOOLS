#!/usr/bin/env python3
"""Quick synthetic-fixture regression ONLY. All test audio is fake and never deliverable.

Checks the real mix_audio.py for silence, allowed cue timing and technical format.
Commercial final outputs use only independently verified CC0 source files.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
import numpy as np
import soundfile as sf

HERE=Path(__file__).resolve().parent
MIX=HERE.parent/'production'/'crunchy_mango'/'mix_audio.py'
SR=48000
def source(p,seconds,role):
 n=round(seconds*SR);t=np.arange(n)/SR
 if role=='soft_fruit_inner':
  # Continuous low-level movement with independent contact transients.
  v=(.006*np.sin(2*np.pi*213*t)+.002*np.sin(2*np.pi*403*t))*(.6+.25*np.sin(2*np.pi*.75*t))
 else:
  v=np.zeros(n)
  for center in [0.16,0.42]:
   idx=np.arange(n)
   v+=.12*np.exp(-np.maximum(0,idx-round(center*SR))/(SR*.024))*(idx>=round(center*SR))*np.sin(2*np.pi*1100*t)
 samples=np.stack([v,v*.98],axis=1).astype('float32')
 sf.write(p,samples,SR,subtype='PCM_16')
 return {'role':role,'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'license':'TEST-FIXTURE-NOT-REAL-CC0'}

with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);assets=root/'assets';out=root/'out';assets.mkdir();out.mkdir()
 ledger={'asset_ledger':[
   source(assets/'candy_shell_snap.wav',1.15,'candy_shell_snap'),
   source(assets/'candy_bar_crunch.wav',1.15,'candy_bar_crunch'),
   source(assets/'soft_fruit_inner.wav',17.8,'soft_fruit_inner')
 ],'test_fixture_only':True}
 (assets/'RIGHTS_SOURCE_LEDGER.json').write_text(json.dumps(ledger))
 env=dict(os.environ,CRUNCH_ASSETS=str(assets),CRUNCH_OUTPUT=str(out))
 subprocess.run([sys.executable,str(MIX)],env=env,check=True,timeout=90,capture_output=True,text=True)
 wav=out/'CRUNCHY_MANGO_CC0_PHYSICS_MATCHED_FOLEY_48k24b.wav'
 assert wav.exists(), 'No output WAV'
 y,sr=sf.read(wav,always_2d=True)
 assert sr==SR and len(y)==6*SR and y.shape[1]==2,(sr,y.shape)
 assert np.max(np.abs(y))<.94,'Audio may clip'
 p=subprocess.run(['ffmpeg','-v','info','-i',str(wav),'-af','silencedetect=noise=-55dB:d=0.45','-f','null','-'],capture_output=True,text=True,timeout=40)
 assert p.returncode==0 and 'silence_start' not in p.stderr,p.stderr[-700:]
 qa=json.loads((out/'FOLEY_FRAME_ALIGNMENT_AND_SOURCE_RIGHTS.json').read_text())
 assert len(qa['primary_crunch_events'])==2
 for e in qa['primary_crunch_events']:
  assert abs(e['recorded_peak_alignment_offset_s']) < 1/24, e
 print('PASS: 6s, 48k stereo, no >=0.45s silence, two independently time-aligned contacts (test-only fixtures)')
