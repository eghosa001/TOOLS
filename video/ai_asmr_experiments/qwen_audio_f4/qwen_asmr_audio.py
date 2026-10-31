#!/usr/bin/env python3
"""Qwen AudioGen environmental Foley for four six-second ASMR pilots.

The Qwen-Audio-3.1-TTS-Next hosted model explicitly supports sound effects.
No synthetic fallback. No API call unless --generate is explicitly supplied.
Set DASHSCOPE_API_KEY in the environment; never hardcode a credential.

Official API: https://docs.qwencloud.com/api-reference/audio-generation
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

MODEL = 'qwen-audio-3.1-tts-next'
ENDPOINTS = {
    'singapore': 'https://ap-southeast-1.maas.qwencloudapi.com/api/v1/services/audio/tts/SpeechSynthesizer',
    'beijing': 'https://cn-beijing.maas.qwencloudapi.com/api/v1/services/audio/tts/SpeechSynthesizer',
}
DURATION = 6.0
SCENES = {
 'embers': {
    'prompt': ('A realistic intimate close-microphone recording of a small bed of glowing charcoal embers. '
        'A continuous low delicate fire crackle with individually distinct tiny dry pops, slight woody hiss, '
        'occasional soft ember ticks, subtle changes in activity over six seconds. '
        'Gentle stereo sound, minimal background, no giant bonfire roar, no whooshes, '
        'no people, no voice, no narration, no music. Exactly six seconds of environmental sound only.'),
    'target_lufs': -23,
 },
 'candle': {
    'prompt': ('A natural close-up room recording of one small steady candle burning in a quiet interior. '
        'The wick is almost silent, with an exceptionally subtle whisper of moving indoor air and '
        'barely perceptible intermittent wick ticks. Extremely gentle low-level realistic room tone. '
        'No roaring flame, no fireplace, no clicks from other objects, no speech, no music, no melody. '
        'Six seconds, quiet ambient recording only.'),
    'target_lufs': -39,
 },
 'ripples': {
    'prompt': ('An authentic field recording of a tiny droplet touching a calm shallow water surface '
        'and several delicate circular ripples spreading out. Very close small wet plink at the beginning, '
        'a soft realistic short trickle and tiny subsequent water lapping sounds with gentle decay, '
        'calm surrounding air. Small scale, no waves crashing, no river torrent, no music or voices. '
        'Exactly six seconds, realistic spatially gentle stereo water sounds.'),
    'target_lufs': -26,
 },
 'ink': {
    'prompt': ('Very quiet realistic studio ambience around a clear tank of still water into which '
        'liquid pigments gently spread. The pigment dispersal itself is virtually silent. '
        'Only extremely faint close-up liquid movement and a subtle occasional bubble tick, '
        'gentle natural low-level water room tone. No magical or sci-fi effects, no rushing water, '
        'no underwater motors, no voices, no music. Exactly six seconds, restrained true-to-life audio.'),
    'target_lufs': -37,
 },
}


def cmd(args):
    return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)


def probe(path: Path):
    return json.loads(cmd(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def duration(path: Path):
    return float(probe(path)['format']['duration'])


def generate(prompt: str, key: str, region: str, seed: int, out: Path):
    payload = {'model': MODEL, 'input': {'text_prompt': prompt, 'format': 'wav',
                'sample_rate': 48000, 'channels': 2, 'seed': seed}}
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(ENDPOINTS[region], data=body, headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            obj = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        error_body = exc.read(1000).decode('utf8', 'replace')
        raise RuntimeError(f'Qwen returned HTTP {exc.code}: {error_body}') from None
    url = ((obj.get('output') or {}).get('audio') or {}).get('url')
    if not isinstance(url, str) or not url.startswith('https://'):
        raise RuntimeError('Qwen returned no authenticated audio download URL; no audio generated')
    # URL is a short-lived provider output. Download immediately, then retain local WAV.
    with urllib.request.urlopen(url, timeout=120) as resp, out.open('wb') as f:
        shutil.copyfileobj(resp, f)
    if out.stat().st_size < 25000:
        raise RuntimeError('Audio file unexpectedly small: ' + str(out))
    p=probe(out)
    if not any(x.get('codec_type') == 'audio' for x in p.get('streams', [])):
        raise RuntimeError('Qwen output has no decodable audio stream')
    return {'request_id': obj.get('request_id'), 'returned_seconds': obj['output']['audio'].get('duration'),
            'downloaded_seconds': duration(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest()}


def mux(video: Path, wav: Path, output: Path, scene: str):
    if not video.is_file() or not wav.is_file():
        raise FileNotFoundError('Both original video and actual Qwen WAV must exist')
    actual = duration(wav)
    if actual < DURATION - .25:
        raise RuntimeError(f'Qwen WAV too short ({actual:.2f}s); refusing repeated short audio loops')
    # Treat generated audio as source, not as proof that its sound matches imagery.
    filters = (
        f'atrim=0:{DURATION},asetpts=N/SR/TB,aresample=48000,'
        f'highpass=f=32,loudnorm=I={SCENES[scene]["target_lufs"]}:TP=-3:LRA=12,'
        f'afade=t=in:st=0:d=0.08,afade=t=out:st=5.65:d=0.35'
    )
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-i', str(video), '-i',str(wav),'-map','0:v:0','-map','1:a:0',
        '-c:v','copy','-af',filters,'-c:a','aac','-b:a','192k','-ar','48000',
        '-ac','2','-t',str(DURATION),'-movflags','+faststart',str(output)], check=True)
    st=probe(output)['streams']
    if not {'audio','video'}.issubset({s['codec_type'] for s in st}):
        raise RuntimeError('Mux did not produce video + audio')
    return {'bytes': output.stat().st_size, 'duration_seconds': duration(output),
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-dir',type=Path, default=Path('/mnt/data/asmr_four_tests'))
    ap.add_argument('--out-dir',type=Path,default=Path('/mnt/data/asmr_qwen_audio'))
    ap.add_argument('--region', choices=ENDPOINTS, default='singapore')
    ap.add_argument('--generate', action='store_true', help='Explicitly allow Qwen API calls: may incur charges')
    ap.add_argument('--scene',choices=[*SCENES,'all'],default='all')
    a=ap.parse_args()
    a.out_dir.mkdir(parents=True,exist_ok=True)
    chosen=list(SCENES) if a.scene=='all' else [a.scene]
    plan={'model':MODEL,'region':a.region,'generated':False,'scenes':{}}
    for i,name in enumerate(chosen):
        vid=a.source_dir/f'{name}_asmr_motion_test_720p.mp4'
        plan['scenes'][name]={'video':str(vid),'video_exists':vid.is_file(),
            'prompt':SCENES[name]['prompt'],'wav':str(a.out_dir/f'{name}_qwen_original.wav')}
    (a.out_dir/'qwen_generation_plan.json').write_text(json.dumps(plan,indent=2))
    if not a.generate:
        print('PLAN ONLY: no Qwen audio was generated; use --generate with a valid DASHSCOPE_API_KEY.')
        print(json.dumps(plan,indent=2))
        return
    key=os.environ.get('DASHSCOPE_API_KEY','')
    if not key:
        raise RuntimeError('DASHSCOPE_API_KEY is not set. No audio generated, and no source files changed.')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise RuntimeError('ffmpeg/ffprobe must be installed')
    for i,name in enumerate(chosen):
        video=a.source_dir/f'{name}_asmr_motion_test_720p.mp4'
        if not video.is_file():
            raise FileNotFoundError(video)
    results={}
    for i,name in enumerate(chosen):
        wav=a.out_dir/f'{name}_qwen_original.wav'
        video=a.source_dir/f'{name}_asmr_motion_test_720p.mp4'
        out=a.out_dir/f'{name}_QWEN_AUDIO_REVIEW_720p.mp4'
        gen=generate(SCENES[name]['prompt'],key,a.region,20261031+i,wav)
        combined=mux(video,wav,out,name)
        results[name]={'qwen':gen,'video':combined,'path':str(out),'status':'TECHNICAL_PREVIEW_UNAPPROVED'}
        (a.out_dir/'qwen_results.json').write_text(json.dumps(results,indent=2))
        print('COMPLETED QWEN PREVIEW:',name, out,flush=True)
    print('COMPLETE, subject to listening and scene-sync review.')

if __name__=='__main__':
    main()
