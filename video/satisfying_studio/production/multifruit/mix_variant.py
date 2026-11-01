#!/usr/bin/env python3
"""Independently licensed, non-looped fruit-specific soft handling and sharp CC0 candy cracks.
Reuses the existing Satisfying Studio verified Freesound recordings; never reference-creator audio.
"""
from __future__ import annotations
import os
from pathlib import Path
FRUIT=os.environ.get('ASMR_FRUIT_VARIANT','strawberry').lower()
SETTINGS={
 'strawberry': {'starts':[.45,2.35,4.55,6.10,8.28,11.05], 'events':[("candy_shell_snap",61,-25.0,.74),("candy_bar_crunch",85,-30.0,.54)],'bed':-42.0},
 'citrus': {'starts':[1.20,3.42,5.48,7.31,9.55,11.52], 'events':[("candy_bar_crunch",61,-25.2,.64),("candy_shell_snap",85,-29.3,.58)],'bed':-40.9},
 'fig': {'starts':[.30,2.21,4.16,6.32,8.11,10.55], 'events':[("candy_shell_snap",61,-27.2,.68),("candy_bar_crunch",85,-32.0,.50)],'bed':-42.1},
 'dragonfruit': {'starts':[1.77,3.81,5.85,7.59,9.62,11.87], 'events':[("candy_bar_crunch",61,-24.7,.81),("candy_shell_snap",85,-28.5,.60)],'bed':-40.5},
}
if FRUIT not in SETTINGS:raise SystemExit('Unknown fruit '+FRUIT)
cfg=SETTINGS[FRUIT]
original=Path(__file__).resolve().parents[1]/'crunchy_mango'/'mix_audio.py'
if 'MULTIFRUIT_BASE_AUDIO' in os.environ:original=Path(os.environ['MULTIFRUIT_BASE_AUDIO'])
s=original.read_text(encoding='utf-8')

def once(before,after):
 global s
 assert before in s, 'Mix source changed: missing '+before
 s=s.replace(before,after,1)

once('from scipy.signal import butter,sosfiltfilt','from scipy.signal import butter,sosfiltfilt\nfrom scipy.ndimage import uniform_filter1d')
if 'starts=[1.10,3.10,5.15,7.35,8.52,11.15]' in s:
 once('starts=[1.10,3.10,5.15,7.35,8.52,11.15]','starts='+repr(cfg['starts']))
once('add_snap(\'candy_shell_snap\',55,-26.0,.84)\nadd_snap(\'candy_bar_crunch\',85,-29.0,.75)',
     '\n'.join(f'add_snap({role!r},{frame},{db},{length})' for role,frame,db,length in cfg['events']))
if 'center=round((frame/24-0.070)*SR)' in s: once('center=round((frame/24-0.070)*SR)', 'center=round(((frame-1)/24)*SR)')
elif 'center=round(frame/24*SR)' in s: once('center=round(frame/24*SR)', 'center=round(((frame-1)/24)*SR)')
else: raise RuntimeError('Original audio peak placement changed')
once('source_peak=int(np.argmax(np.mean(segment**2,axis=1)))',
     'source_peak=int(np.argmax(uniform_filter1d(np.mean(segment**2,axis=1),size=int(.015*SR))))')
once("'actual_mix_duration_s':len(y)/SR", "'fruit_variant':"+repr(FRUIT)+",'actual_mix_duration_s':len(y)/SR")
once("background=level(background,-42.2)", "background=level(background,"+str(cfg['bed'])+")")
compiled=compile(s,str(original),'exec')
if '--validate-only' in __import__('sys').argv:
 print('AUDIO_VARIANT_VALID',FRUIT,len(s))
else:
 context={'__name__':'__main__','__file__':str(original)}
 exec(compiled,context,context)
