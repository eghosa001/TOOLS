#!/usr/bin/env python3
"""Per-shot genuine Qwen3 Ryan V4: fluent names and fast natural football delivery.

Explicitly prevents old mismatched one-take narration being laid blindly across footage.
Created for real 2026 Barcelona–Alavés / Aston Villa–Fulham action,
and genuine licensed CC player portraits. REVIEW AUDIO ONLY.
"""
import json,os
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

OUT=Path("football_edit_output/qwen_barca_villa_shot_synced_v4")
OUT.mkdir(parents=True,exist_ok=True)
MODEL="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER="Ryan"

SCENES=[
 {"id":"hook_yamal","visual":"Yamal actual goal vs Alaves, real 2026 goal action",
  "text":"Watch Yamal here. One opening, one touch, and Villa could be in trouble."},
 {"id":"historical_h2h","visual":"Real 2026 game motion and explicitly dated 1983 Super Cup result graphic",
  "text":"Villa have done it before. Back in 1983, they overturned a one nil defeat with a three nil win. They took the Super Cup."},
 {"id":"raphinha_goal","visual":"Barcelona actual Raphinha goal vs Alaves in October 2026",
  "text":"And Barcelona are dangerous. Six against Alavés. Watch Raphinha arrive, and finish. No room for hesitation."},
 {"id":"jackson_fulham_goal","visual":"Actual Nicolas Jackson scoring for Villa vs Fulham, not Villa conceding",
  "text":"But look at Villa's answer. Manzambi releases Jackson. He beats the challenge, picks his corner, and scores."},
 {"id":"yamal_maatsen_duel","visual":"Real Yamal and Maatsen CC author photos over actual Barcelona match",
  "text":"Yamal against Maatsen. Let Yamal cut inside, he can shoot. Stand off, he can create. Maatsen has to get that distance right."},
 {"id":"jackson_cubarsi_duel","visual":"Real Jackson and Cubarsi CC author photos over actual Villa match",
  "text":"Jackson against Pau Cubarsí. If Villa beat Barcelona's first press, Cubarsí has to defend the space in behind."},
 {"id":"form_and_tactics","visual":"Real Barcelona match clips, honest Champions League form stats",
  "text":"Villa have won all three Champions League games. Barcelona have won two of three. Watch that first pass after a turnover."},
 {"id":"outro_key_matchup","visual":"Genuine Villa goal replay with an interactive prediction question",
  "text":"Which matchup decides it? Yamal or Jackson? Maatsen or Cubarsí? Tell me your score prediction."}
]
torch.set_num_threads(max(1,min(4,os.cpu_count() or 4)))
torch.set_num_interop_threads(2)
from qwen_tts import Qwen3TTSModel
print("LOADING_REAL_QWEN",MODEL,flush=True)
model=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
results=[]
# Critically, keep personal names in NORMAL orthography. V3's hyphenated
# phonetic cues caused artificial elongation of syllables even at 1.40x tempo.
# No syllabification, no IPA-as-text, and no emphasized uppercase name fragments.
# If further name repairs are needed, assess actual waveform before narrow edits.
def spoken_text(original):
    return original

for i,scene in enumerate(SCENES):
    print("VOICE_BEAT_START",i,scene["id"],flush=True)
    wavs,sr=model.generate_custom_voice(text=spoken_text(scene["text"]),speaker=SPEAKER,language="English",instruct="Speak like a naturally quick, conversational football creator talking to a friend. Flow smoothly through names without separating or stressing their syllables. No dramatic pauses, no announcer voice, no deliberate enunciation. Lively, relaxed, fluent.")
    sound=np.asarray(wavs[0],dtype=np.float32).flatten()
    peak=float(np.max(np.abs(sound))) if sound.size else 0.0
    rms=float(np.sqrt(np.mean(sound*sound))) if sound.size else 0.0
    if sound.size<0.8*sr or not np.isfinite(sound).all() or rms<.004:
        raise RuntimeError("ACTUAL QWEN segment missing or invalid: "+scene["id"])
    filename=f'{i:02d}_{scene["id"]}_Qwen3_Ryan.wav'
    sf.write(OUT/filename,sound,sr,subtype="PCM_16")
    sec=sound.size/sr
    results.append({**scene,"spoken_text":spoken_text(scene["text"]),"pronunciation_source":"Natural canonical player-name spellings; no phonetic syllable splitting","audio_file":filename,"seconds_raw":round(sec,3),"sample_rate":sr,"rms":round(rms,4),"peak":round(peak,4)})
    print("VOICE_BEAT_COMPLETE",scene["id"],round(sec,2),"RMS",round(rms,3),flush=True)
manifest={"model":MODEL,"speaker":SPEAKER,"language":"English","speed_final_edit":"1.48x pitch-preserving",
          "kind":"REAL QWEN PER SHOT - NATURAL UNSPLIT PLAYER NAMES","generated_background_images":False,
          "note":"Canonical names in actual Qwen speech, no hyphens or artificial stress. Natural rapid conversational rhythm. Each beat syncs to authentic match action.",
          "scenes":results,"total_raw_s":round(sum(s["seconds_raw"] for s in results),2)}
(OUT/"shot_synced_narration_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print("ALL_SHOT_VOICES_RENDERED",manifest["total_raw_s"],flush=True)
