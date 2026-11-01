#!/usr/bin/env python3
"""Generate Qwen3-TTS narration per hand-directed shot; preserve stereo and timing."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from shotlist import load_and_validate
ROOT=Path(__file__).resolve().parent
def cache_key(model,speaker,language,instruct,text):
    return hashlib.sha256(json.dumps([model,speaker,language,instruct,text],ensure_ascii=False).encode()).hexdigest()[:24]
def generate(spec,dest,cache):
    import torch,soundfile as sf
    from qwen_tts import Qwen3TTSModel
    dest.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    # Qwen3-TTS code predictor can produce NaN sampling probabilities in
    # float16 on pre-Ampere CUDA GPUs (such as the Kaggle Tesla T4).
    # Upstream QwenLM/Qwen3-TTS issue #43 explicitly recommends float32
    # when bfloat16 is unavailable. Never select unstable FP16 here.
    import os
    if os.environ.get('QWEN_FORCE_CPU') == '1' or not torch.cuda.is_available():
        device, dtype = 'cpu', torch.float32
    else:
        major, _ = torch.cuda.get_device_capability(0)
        device = 'cuda:0'
        dtype = torch.bfloat16 if major >= 8 else torch.float32
        if major < 8:
            torch.set_float32_matmul_precision('highest')
    print('QWEN_INFERENCE_BACKEND', device, str(dtype), flush=True)
    voice=spec['audio']
    model=Qwen3TTSModel.from_pretrained(
        voice['model'],device_map=device,dtype=dtype,attn_implementation='sdpa'
    )
    for shot in spec['shots']:
        key=cache_key(voice['model'],voice['speaker'],voice['language'],voice.get('instruct',''),shot['spoken'])
        cached=cache/(key+'.wav')
        if not cached.exists():
            waves,rate=model.generate_custom_voice(text=shot['spoken'],speaker=voice['speaker'],language=voice['language'],instruct=voice.get('instruct',''))
            import numpy as np
            samples = np.asarray(waves[0])
            if samples.size < rate // 4 or not np.isfinite(samples).all():
                raise ValueError('Qwen produced empty or non-finite speech; no silent fallback')
            sf.write(str(cached),samples,rate,subtype='PCM_16')
        shutil.copy2(cached,dest/(shot['id']+'.wav'))
def duration(path):
    raw=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nokey=1:noprint_wrappers=1',str(path)],text=True)
    return float(raw.strip())
def mix_authored_timeline(spec,wav_dir,output):
    files=[];report=[];inputs=[];filters=[]
    for i,shot in enumerate(spec['shots']):
        path=wav_dir/(shot['id']+'.wav')
        if not path.is_file():raise FileNotFoundError('Missing Qwen speech: '+str(path))
        seconds=duration(path);allotted=shot['end']-shot['start']
        # Preserve the entire Qwen performance. Modest pitch-preserving atempo
        # corrects unpredictable TTS pacing without truncating any speech.
        speed=max(1.0,seconds/max(0.5,allotted-0.12))
        if speed>1.75:raise ValueError(f"{shot['id']}: spoken {seconds:.2f}s > {allotted:.2f}s (speed {speed:.2f}); rewrite text, never truncate")
        report.append({'shot':shot['id'],'actual_s':round(seconds,3),'slot_s':allotted,'atempo':round(speed,4),'words_preserved':True})
        inputs.extend(['-i',str(path)])
        delay=round(shot['start']*1000)
        filters.append(f'[{i}:a]aresample=48000,atempo={speed:.6f},adelay={delay}:all=1[a{i}]')
    inputs_count=len(spec['shots'])
    channels=''.join(f'[a{i}]' for i in range(inputs_count))
    filters.append(f'{channels}amix=inputs={inputs_count}:duration=longest:normalize=0,apad=whole_dur={spec["seconds"]},atrim=duration={spec["seconds"]},loudnorm=I=-16:TP=-1.5:LRA=11[voice]')
    output.parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',*inputs,'-filter_complex',';'.join(filters),'-map','[voice]','-ar','48000','-ac','2','-c:a','pcm_s16le',str(output)]
    subprocess.run(cmd,check=True)
    return report
def main():
    p=argparse.ArgumentParser();p.add_argument('short',type=Path);p.add_argument('--audio-only',action='store_true')
    p.add_argument('--wav-dir',type=Path,default=ROOT/'build/voices')
    p.add_argument('--output',type=Path,default=ROOT/'build/narration_stereo.wav')
    a=p.parse_args();spec=load_and_validate(a.short)
    if not a.audio_only:generate(spec,a.wav_dir,ROOT/'build/voice_cache')
    report=mix_authored_timeline(spec,a.wav_dir,a.output)
    a.output.with_suffix('.json').write_text(json.dumps({'voice_model':spec['audio']['model'],'timing':report,'human_audio_approved':False},indent=2))
    print('QWEN_STEREO_SOUNDTRACK',a.output)
if __name__=='__main__':main()
