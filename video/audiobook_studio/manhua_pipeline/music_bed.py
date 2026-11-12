#!/usr/bin/env python3
"""Original melodic underscore + licensed-track FFmpeg mix for Mythveil.

All music is quietly ducked underneath the approved narration; no narration
speed or content changes. The original generator uses no external samples.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import wave

import numpy as np

MUSIC_VERSION = 'mythveil_original_melodic_bed_v1'
SAMPLE_RATE = 24000
MOODS = {
    'mystery': [(52, 55, 59, 66), (48, 55, 59, 64), (43, 50, 55, 59), (50, 57, 62, 64)],
    'wonder': [(48, 55, 60, 64), (45, 52, 57, 60), (53, 60, 65, 69), (55, 62, 67, 71)],
    'tension': [(50, 53, 57, 62), (46, 53, 58, 62), (48, 55, 60, 63), (45, 52, 57, 60)],
    'reflective': [(45, 52, 57, 60), (53, 57, 60, 64), (48, 55, 60, 64), (52, 56, 59, 64)],
    'action': [(52, 55, 59, 64), (50, 57, 62, 65), (48, 55, 60, 64), (47, 54, 59, 62)],
}


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def make_original_bed(path: Path, *, mood: str = 'mystery') -> Path:
    """Create a 64s original, airy pad + restrained plucked melodic loop."""
    if mood not in MOODS:
        raise ValueError('Unsupported music mood: ' + mood)
    sr = SAMPLE_RATE
    samples = sr * 64
    audio = np.zeros(samples, dtype=np.float32)

    def note(pitch: int, start: float, hold: float, gain: float,
             attack: float, release: float, pluck: bool = False) -> None:
        a, b = max(0, round(start * sr)), min(samples, round((start + hold + release) * sr))
        if b <= a:
            return
        t = np.arange(a, b, dtype=np.float32) / sr - start
        env = np.minimum(np.clip(t / max(attack, .001), 0, 1),
                         np.clip((start + hold + release - np.arange(a, b) / sr)
                                 / max(release, .001), 0, 1)).astype(np.float32)
        hz = 440 * (2 ** ((pitch - 69) / 12))
        tone = (np.sin(2 * np.pi * hz * t)
                + .21 * np.sin(2 * np.pi * 2 * hz * t + .2)
                + .07 * np.sin(2 * np.pi * 3 * hz * t + .5))
        if pluck:
            tone *= np.exp(-np.maximum(t, 0) * 1.35)
        else:
            tone *= .91 + .09 * np.sin(2 * np.pi * .16 * t)
        audio[a:b] += gain * env * tone.astype(np.float32)

    for phrase in range(8):
        chord = MOODS[mood][phrase % 4]
        start = phrase * 8.0
        for pitch in chord:
            note(pitch, start, 7.4, .035, 1.1, .6)
        for idx, pick in enumerate((0, 2, 1, 3, 2, 1, 3)):
            note(chord[pick] + 12, start + .75 + idx * .92, .5,
                 .043 if idx in (0, 4) else .032, .035, .65, pluck=True)
        note(chord[0] - 12, start + .15, 7.0, .016, .8, .8)
    fade = int(sr * .75)
    audio[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    audio[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = float(np.max(np.abs(audio)))
    if peak < .0001:
        raise RuntimeError('Generated original music is silent')
    audio = np.clip(audio * (.6 / peak), -.9, .9)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sr)
        output.writeframes((audio * 32767).astype('<i2').tobytes())
    return path


def prepare_music(output: Path, *, mood: str = 'mystery',
                  music_file: str | None = None,
                  rights_file: str | None = None,
                  level: float = .10,
                  legacy_no_music: bool = False,
                  art_policy: str = 'full_color_panels') -> tuple[Path | None, dict]:
    """Resolve actual audio and rights evidence; enforce new-episode music."""
    if not .02 <= level <= .20:
        raise ValueError('Music level must be between 0.02 and 0.20')
    if legacy_no_music:
        if art_policy != 'legacy_dense' or music_file or rights_file:
            raise ValueError('Music may be disabled only for archived legacy replays')
        return None, {'status': 'ARCHIVAL_ONLY_NO_MUSIC'}
    if music_file:
        if not rights_file:
            raise ValueError('A third-party music track needs --music-rights-file')
        path = Path(music_file).expanduser().resolve(strict=True)
        rights = Path(rights_file).expanduser().resolve(strict=True)
        if not path.is_file() or not rights.is_file() or rights.stat().st_size == 0:
            raise ValueError('Music track or its rights documentation is missing')
        source = {'type': 'licensed_external', 'rights_file': str(rights),
                  'rights_sha256': _hash(rights)}
    else:
        if rights_file:
            raise ValueError('--music-rights-file requires --music-file')
        if mood not in MOODS:
            raise ValueError('Unsupported music mood')
        path = output.with_name(output.stem + '.' + MUSIC_VERSION + '.' + mood + '.wav')
        if not path.is_file() or path.stat().st_size < 50000:
            make_original_bed(path, mood=mood)
        source = {'type': 'new_original_composition', 'generator': MUSIC_VERSION,
                  'mood': mood, 'samples': 'none', 'rights': 'new original instrumental'}
    from video.audiobook_studio.episode_fastlane import probe_media
    info = probe_media(path)
    audio_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
    if len(audio_streams) != 1 or float(info.get('format', {}).get('duration') or 0) < 2:
        raise ValueError('Music must be a decodable, non-silent-length audio file')
    return path, {'status': 'MUSIC_BED_READY', 'file': str(path), 'sha256': _hash(path),
                  'level': level, 'ducking': 'speech_sidechain_v1', **source}


def music_filter(duration: float, level: float) -> str:
    """Return FFmpeg graph for input 1 narrator + input 2 looped music."""
    if duration < 1 or not .02 <= level <= .20:
        raise ValueError('Invalid audio duration or music level')
    fade = min(1.2, duration / 4)
    out_start = max(0, duration - fade)
    return (
        '[1:a]aresample=48000,asplit=2[voice][voicekey];'
        '[2:a]aresample=48000,volume=' + f'{level:.5f}' +
        ',highpass=f=100,lowpass=f=7800,atrim=0:' + f'{duration:.4f}' +
        ',afade=t=in:st=0:d=' + f'{fade:.3f}' +
        ',afade=t=out:st=' + f'{out_start:.4f}' + ':d=' + f'{fade:.3f}' + '[bed];'
        '[bed][voicekey]sidechaincompress=threshold=0.018:ratio=4:attack=50:'
        'release=650[ducked];'
        '[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0:'
        'normalize=0,alimiter=limit=0.82:level=0:attack=5:release=60[aout]'
    )


# Mandatory music-FIRST preflight for NEW Mythveil episodes. Run before Kokoro TTS.
def prebuild_music_before_voice(output: Path, *, mood: str = "mystery",
                                music_file: str | None = None,
                                rights_file: str | None = None,
                                level: float = .10) -> Path:
    """Generate/validate the original or licensed music before any new narration.

    Records immutable music identity for the assembler and the private release
    evidence packet. Reusing already approved narration is allowed.
    """
    import datetime
    import json
    output = Path(output).expanduser().resolve()
    if output.suffix.lower() != ".mp4":
        raise ValueError("MUSIC_FIRST_OUTPUT_MUST_BE_MP4_PATH")
    output.parent.mkdir(parents=True, exist_ok=True)
    bed, evidence = prepare_music(
        output, mood=mood, music_file=music_file,
        rights_file=rights_file, level=level,
        art_policy="full_color_panels", legacy_no_music=False)
    if bed is None or evidence.get("status") != "MUSIC_BED_READY":
        raise ValueError("MUSIC_FIRST_NOT_READY")
    receipt = output.with_name(output.stem + ".music_preflight.json")
    record = {
        "schema_version": 1,
        "stage": "MUSIC_FIRST_BEFORE_NEW_VOICE_RECORDING",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "output": str(output),
        "music_sha256": evidence["sha256"],
        "music_source": evidence,
        "mood": mood,
        "level": level,
        "narration_audio_generated_by_preflight": False,
        "human_audibility_review_completed": False,
    }
    temporary = receipt.with_suffix(".partial.json")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temporary.replace(receipt)
    return receipt


def require_music_first_preflight(output: Path, *, mood: str = "mystery",
                                   level: float = .10,
                                   music_file: str | None = None) -> dict:
    """Fail closed unless this episode's specific music already exists."""
    import json
    output = Path(output).expanduser().resolve()
    receipt = output.with_name(output.stem + ".music_preflight.json")
    if not receipt.is_file():
        raise ValueError("MUSIC_FIRST_REQUIRED: prebuild original/rights-cleared "
                         "background music before narration and full episode assembly")
    doc = json.loads(receipt.read_text(encoding="utf-8"))
    evidence = doc.get("music_source", {})
    source = Path(evidence.get("file", ""))
    if not source.is_file() or source.stat().st_size < 50000:
        raise ValueError("MUSIC_FIRST_MISSING_FILE")
    if (doc.get("schema_version") != 1
            or doc.get("stage") != "MUSIC_FIRST_BEFORE_NEW_VOICE_RECORDING"
            or doc.get("output") != str(output)
            or doc.get("mood") != mood
            or doc.get("level") != level
            or doc.get("music_sha256") != _hash(source)
            or evidence.get("status") != "MUSIC_BED_READY"):
        raise ValueError("MUSIC_FIRST_EVIDENCE_MISMATCH")
    if music_file and Path(music_file).expanduser().resolve() != source.resolve():
        raise ValueError("MUSIC_FIRST_SOURCE_MISMATCH")
    if not music_file and evidence.get("type") != "new_original_composition":
        raise ValueError("MUSIC_FIRST_EXPECTED_ORIGINAL_COMPOSITION")
    return {"receipt": str(receipt), "receipt_sha256": _hash(receipt),
            "music_sha256": doc["music_sha256"],
            "status": "MUSIC_PREPARED_BEFORE_ASSEMBLY",
            "human_audibility_review_completed": False}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="MANDATORY: generate/validate background melody BEFORE new Kokoro speech")
    parser.add_argument("--output", required=True, help="Intended future episode MP4 path")
    parser.add_argument("--music-mood", choices=sorted(MOODS), default="mystery")
    parser.add_argument("--music-file", help="Existing commercially cleared soundtrack")
    parser.add_argument("--music-rights-file", help="Required for external soundtrack")
    parser.add_argument("--music-level", type=float, default=.10)
    args = parser.parse_args()
    receipt = prebuild_music_before_voice(
        Path(args.output), mood=args.music_mood,
        music_file=args.music_file, rights_file=args.music_rights_file,
        level=args.music_level)
    print("MUSIC_FIRST_PREFLIGHT_READY", receipt)


if __name__ == "__main__":
    main()
