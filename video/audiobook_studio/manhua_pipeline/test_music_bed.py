"""Regression checks for mandatory melodic audiobook underscoring."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

from video.audiobook_studio.manhua_pipeline.music_bed import (
    MOODS, MUSIC_VERSION, make_original_bed, music_filter, prepare_music,
)


class MythveilMusicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_music_generation_is_original_nonempty_pcm(self):
        p = make_original_bed(self.root / 'new-original.wav', mood='mystery')
        self.assertTrue(p.is_file())
        with wave.open(str(p), 'rb') as f:
            self.assertEqual(f.getframerate(), 24000)
            self.assertEqual(f.getnchannels(), 1)
            self.assertEqual(f.getnframes(), 64 * 24000)
            self.assertNotEqual(f.readframes(25000)[1000:], bytes(25000 * 2 - 1000))

    def test_each_scene_mood_has_distinct_chords(self):
        self.assertGreaterEqual(len(MOODS), 5)
        self.assertNotEqual(MOODS['mystery'], MOODS['tension'])

    def test_music_filter_uses_narration_sidechain_and_preserves_voice(self):
        graph = music_filter(30.0, .10)
        self.assertIn('sidechaincompress=', graph)
        self.assertIn('[voice][ducked]amix=', graph)
        self.assertIn('[aout]', graph)
        # The final AAC encoder can overshoot a limiter's sample peaks.
        # Leave more than 1 dB of headroom before final true-peak measurement.
        self.assertIn('alimiter=limit=', graph)
        import re
        ceiling = float(re.search(r'alimiter=limit=([0-9.]+)', graph).group(1))
        self.assertLessEqual(ceiling, 0.84)
        self.assertIn(':level=0:', graph, 'Disable limiter makeup gain; it can reintroduce digital clipping')
        with self.assertRaises(ValueError):
            music_filter(30.0, 1.0)

    def test_external_music_must_have_provenance(self):
        p = self.root / 'not-cleared.wav'
        p.write_bytes(b'some-music')
        with self.assertRaisesRegex(ValueError, 'rights'):
            prepare_music(self.root / 'episode.mp4', music_file=str(p))

    def test_new_episodes_cannot_silently_disable_music(self):
        with self.assertRaisesRegex(ValueError, 'archived'):
            prepare_music(self.root / 'episode.mp4', legacy_no_music=True,
                          art_policy='full_color_panels')
        path, report = prepare_music(self.root / 'old.mp4',
                                     legacy_no_music=True, art_policy='legacy_dense')
        self.assertIsNone(path)
        self.assertEqual(report['status'], 'ARCHIVAL_ONLY_NO_MUSIC')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),
                         'FFmpeg is required for an actual mix')
    def test_rendered_mix_has_audible_bed_even_in_narration_pause(self):
        from video.audiobook_studio.episode_fastlane import probe_media
        music, proof = prepare_music(self.root / 'review.mp4', mood='mystery')
        self.assertEqual(proof['status'], 'MUSIC_BED_READY')
        self.assertEqual(proof['generator'], MUSIC_VERSION)
        video = self.root / 'mixed.mp4'
        cmd = ['ffmpeg', '-hide_banner', '-nostdin', '-loglevel', 'error', '-y',
               '-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=24:d=3',
               '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
               '-stream_loop', '-1', '-i', str(music),
               '-filter_complex', music_filter(3, .10),
               '-map', '0:v:0', '-map', '[aout]', '-t', '3',
               '-c:v', 'mpeg4', '-c:a', 'aac', '-b:a', '128k', str(video)]
        subprocess.run(cmd, check=True, timeout=30)
        probe = probe_media(video)
        self.assertTrue(any(s.get('codec_type') == 'audio' for s in probe['streams']))
        stats = subprocess.run(
            ['ffmpeg', '-hide_banner', '-v', 'info', '-i', str(video),
             '-map', '0:a:0', '-af', 'volumedetect', '-f', 'null', '-'],
            capture_output=True, text=True, timeout=20, check=True,
        )
        self.assertIn('mean_volume:', stats.stderr)
        self.assertNotIn('mean_volume: -inf', stats.stderr)


if __name__ == '__main__':
    unittest.main()
