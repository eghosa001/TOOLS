#!/usr/bin/env python3
"""Generate *real* environmental sound effects on free Kaggle CPU.

Important: this is NOT Qwen3-TTS output (Qwen3-TTS handles speech).
Uses Stable Audio 3 Small-SFX, and the same GitHub -> Kaggle -> WAV -> artifact
orchestration used for the Ninefold Tide Qwen3-TTS voice project.
No audio is synthesized, faked, or marked complete on an inference failure.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time, traceback, wave

ROOT = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path(os.environ.get('ASMR_OUTPUT_DIR', '/tmp/asmr-foley-output'))
ROOT.mkdir(parents=True, exist_ok=True)
MODEL = 'stabilityai/stable-audio-3-small-sfx'
REPO = 'https://github.com/Stability-AI/stable-audio-3.git'
# Sound design: natural environments only. Qwen3-TTS remains the separate speech engine.
SCENES = {
    'embers': {
        'seed': 26063101,
        'prompt': 'An intimate close microphone field recording of small glowing charcoal embers. Gentle, varied crackling with tiny individual woody ticks and subtle dry pops; faint steady fireplace hiss underneath. Small warm fire, not a bonfire. No voices, no music, no roaring, no synthesized whooshes.',
        'lufs': -23,
    },
    'candle': {
        'seed': 26063102,
        'prompt': 'A quiet indoor room with one small burning wax candle. Nearly silent candle wick with faint natural room tone and occasional subtle whisper of air movement, extremely soft and unobtrusive. No fireplace, no crackling logs, no footsteps, no music or voices.',
        'lufs': -38,
    },
    'ripples': {
        'seed': 26063103,
        'prompt': 'Delicate real water Foley close-miked: a single tiny droplet lands on a perfectly still shallow pool, followed by two or three gentle water plinks, thin soft lapping ripples and decaying surface tension sounds. Very small scale, no ocean surf, no river rushing, no music, no speech.',
        'lufs': -27,
    },
    'ink': {
        'seed': 26063104,
        'prompt': 'A very quiet laboratory studio with a still glass vessel of water. A faint liquid pour, almost inaudible pigment diffusion and one tiny soft bubble tick in nearby water. Natural soft close mic ambience only, not magical sci-fi effects, no electronic tones, no voices, no music.',
        'lufs': -36,
    },
}
STATUS = ROOT / 'four_foley_generation_status.json'

def log(stage, **extra):
    global state
    state['stage'] = stage
    state.update(extra)
    STATUS.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n')
    print('ASMR_FOLEY', stage, json.dumps(extra, ensure_ascii=False), flush=True)

def sh(*argv, timeout=600, cwd=None):
    print('RUN', ' '.join(map(str, argv))[:900], flush=True)
    subprocess.run([str(x) for x in argv], check=True, cwd=cwd, timeout=timeout)

def analyze_wav(path):
    with wave.open(str(path), 'rb') as f:
        frames=f.getnframes(); rate=f.getframerate();channels=f.getnchannels();bits=f.getsampwidth()*8
        if rate != 44100 or channels != 2 or bits != 16:
            raise RuntimeError(f'Unexpected WAV format {rate} Hz/{channels}ch/{bits}bit for {path.name}')
        seconds=frames/rate
        if seconds < 19.5:
            raise RuntimeError(f'WAV too short: {seconds:.2f}s')
    dig=hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(duration=round(seconds, 3), rate=rate, channels=channels, pcm_bits=bits, bytes=path.stat().st_size, sha256=dig)

def main():
    global state
    state={'engine':'Stable Audio 3 Small-SFX (not Qwen3-TTS)', 'model':MODEL,
           'workflow':'same GitHub Actions -> private Kaggle notebook -> WAV artifacts as Ninefold Tide',
           'status':'UNAPPROVED', 'scenes':{}, 'stage':'initialized'}
    log('initialized')
    if '--dry-run' in sys.argv:
        log('dry_run_validated', planned_scenes=list(SCENES), real_inference=False)
        return
    try:
        if not shutil.which('git'):
            raise RuntimeError('git missing')
        if shutil.disk_usage(ROOT).free < 5*1024**3:
            raise RuntimeError('Need >=5GiB free disk for model weights and generated WAVs')
        # CPU model, no Kaggle GPU quota or credit consumption required.
        os.environ['HF_HOME']='/kaggle/temp/asmr_sa3_cache'
        os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
        model_dir=Path('/kaggle/temp/stable_audio_3')
        log('installing_upstream', gpu_required=False)
        if not model_dir.exists():
            sh('git','clone','--depth','1',REPO,model_dir,timeout=260)
        tflite=model_dir/'optimized'/'tflite'
        if not tflite.is_dir():
            raise RuntimeError('Missing official Stable Audio 3 TFLite inference directory')
        # Use the official lightweight CPU requirements NON-INTERACTIVELY (install.sh prompts).
        # The upstream script downloads exact model weights from Hugging Face on first use.
        sh(sys.executable,'-m','pip','install','--disable-pip-version-check','-q','-r',tflite/'requirements.txt',timeout=650,cwd=tflite)
        log('upstream_installed', checkpoint=MODEL)
        for name,item in SCENES.items():
            raw=ROOT/f'{name}_REAL_SFX_20s.wav'
            # Small-SFX official recommendation: >=20s even for 6s video snippets.
            log('generating', current_scene=name, seconds=20)
            sh(sys.executable,'scripts/sa3_tflite.py','--prompt',item['prompt'], '--dit','sm-sfx', '--decoder','same-s',
               '--seconds','20','--steps','8','--seed',str(item['seed']),
               '--threads','4','--out',str(raw),timeout=900,cwd=tflite)
            properties=analyze_wav(raw)
            # Preserve master untouched. Make a 6s review trim with restrained levels.
            review=ROOT/f'{name}_REAL_SFX_REVIEW_6s.wav'
            sh('ffmpeg','-hide_banner','-loglevel','error','-y','-i',raw,
               '-af',f'atrim=0:6,asetpts=N/SR/TB,highpass=f=28,loudnorm=I={item["lufs"]}:TP=-3:LRA=10,afade=t=in:st=0:d=0.07,afade=t=out:st=5.7:d=0.3',
               '-ac','2','-ar','48000','-c:a','pcm_s16le',review,timeout=120)
            if not review.is_file() or review.stat().st_size < 500000:
                raise RuntimeError('Missing or undersized review WAV '+str(review))
            state['scenes'][name]={'master':str(raw),'master_meta':properties,'review':str(review),
                                   'review_bytes':review.stat().st_size,'prompt':item['prompt'],
                                   'status':'GENERATED_UNAPPROVED'}
            log('scene_complete', current_scene=name, completed_count=len(state['scenes']))
        log('all_generated_unapproved', completed_count=len(state['scenes']), final=True)
    except BaseException as exc:
        log('FAILED', error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc()[-2500:])
        raise

if __name__=='__main__':
    main()
