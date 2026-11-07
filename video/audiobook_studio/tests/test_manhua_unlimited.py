"""Public-safe, offline tests for unlimited original-story manhua workflow."""
import json
from pathlib import Path
import tempfile
import unittest
import wave
import zipfile
from unittest import mock

from video.audiobook_studio.manhua_pipeline import core
from video.audiobook_studio.manhua_pipeline import kaggle_runner as runner


class UnlimitedManhuaTests(unittest.TestCase):
    def test_35_unrelated_stories_are_not_restricted_to_initial_20(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for idx in range(35):
                slug=f'new-story-{idx:02}'
                words=f'An original scene {idx}. The end came after the choice.'
                book=root/f'{slug}.txt'; book.write_text(words)
                result=core.create_package(story_id=slug,title=f'New Story {idx}',
                    manuscript=book,episodes={1:book},output=root/f'{slug}.zip',
                    source_approved=True,style='generic')
                self.assertEqual(result['story_id'],slug)
                meta,script,refs=core.open_package(root/f'{slug}.zip',expected_story_id=slug,episode=1)
                self.assertEqual(script,words)
                self.assertFalse(refs)
                self.assertEqual(meta['episodes'][0]['number'],1)

    def test_approved_story_exact_episode_order_and_no_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            part1=root/'ep1.txt';part1.write_text('The door opened. A stranger entered.')
            part2=root/'ep2.txt';part2.write_text('The stranger told the truth. They left.')
            full=root/'novel.md';full.write_text(part1.read_text()+'\n\n'+part2.read_text())
            result=core.create_package(story_id='valid-fantasy',title='Valid Fantasy',
                manuscript=full,episodes={1:part1,2:part2},output=root/'private.zip',
                source_approved=True)
            self.assertEqual(len(result['episodes']),2)
            part2.write_text('Different last ending.')
            with self.assertRaises(ValueError):
                core.create_package(story_id='valid-fantasy',title='Valid Fantasy',
                    manuscript=full,episodes={1:part1,2:part2},output=root/'invalid.zip',
                    source_approved=True)

    def test_source_and_reference_sha_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            book=root/'book.txt';book.write_text('A sword lay on the wet stone.')
            ref=root/'kai.png';ref.write_bytes(b'original visual reference bytes')
            archive=root/'book.zip'
            core.create_package(story_id='another-story',title='Another Story',
                manuscript=book,episodes={1:book},output=archive,source_approved=True,
                references={'kai':ref},characters=[{'id':'kai','name':'Kai',
                'visual_description':'Young dark-haired worker, simple brown robes'}])
            _,_,refs=core.open_package(archive,expected_story_id='another-story',episode=1)
            self.assertEqual(len(refs),1)
            with zipfile.ZipFile(archive) as z:
                files={name:z.read(name) for name in z.namelist()}
            files['episodes/ep001.txt']=b'Wrong substitution.'
            with zipfile.ZipFile(archive,'w') as z:
                for name,data in files.items():z.writestr(name,data)
            with self.assertRaises(ValueError):
                core.open_package(archive,expected_story_id='another-story',episode=1)
            with self.assertRaises(ValueError):
                core.open_package(archive,expected_story_id='wrong-title',episode=1)

    def test_path_traversal_is_blocked_even_in_private_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('../outside.txt','private prose')
                z.writestr('manifest.json','{}')
            with self.assertRaises(ValueError):
                core.open_package(path,expected_story_id='new-story',episode=1)

    def test_source_preservation_and_dynamic_scene_budget(self):
        lines=['Kai noticed the old stone bridge and decided to cross. ']*320
        paragraphs='\n\n'.join(lines)
        chunks=core.split_chunks(paragraphs,max_words=110)
        self.assertEqual(' '.join(' '.join(c['text'] for c in chunks).split()),
                         ' '.join(paragraphs.split()))
        beats=core.scene_plan(chunks,style='cultivation',target_words=35)
        self.assertGreater(len(beats),20)
        self.assertEqual(beats[0]['start_chunk'],0)
        self.assertEqual(beats[-1]['end_chunk'],len(chunks))
        self.assertFalse(any('3d render' in b['prompt'] for b in beats))
        self.assertTrue(all(b['needs_editorial_visual_review'] for b in beats))

    def test_explicit_scene_briefs_and_character_identity(self):
        text=('The rain fell. Kai walked to the sect gate. ')*18
        chunks=core.split_chunks(text,max_words=110)
        beats=core.scene_plan(chunks,style='dark_fantasy',target_words=120,
             characters=[{'id':'kai','visual_description':'Young dark-haired worker, brown eyes'}],
             briefs=['Kai standing under a rainy sect archway'])
        self.assertIn('Kai standing under a rainy sect archway',beats[0]['prompt'])
        self.assertIn('Young dark-haired worker',beats[0]['prompt'])
        # Approved scene briefs help prompts but never certify generated pixels.
        self.assertTrue(beats[0]['needs_editorial_visual_review'])

    def test_source_approval_cannot_be_faked(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'test.txt';file.write_text('A real story.')
            with self.assertRaises(ValueError):
                core.create_package(story_id='sample-story',title='Sample Story',
                    manuscript=file,episodes={1:file},output=Path(directory)/'bad.zip')

    def test_scene_timing_matches_real_chunk_durations_without_gaps(self):
        scenes=[{'start_chunk':0,'end_chunk':2}, {'start_chunk':2,'end_chunk':4}]
        self.assertEqual(runner.scene_timeline(scenes,[2.5,4,3,1]),[6.5,4])
        with self.assertRaises(ValueError):
            runner.scene_timeline([{'start_chunk':0,'end_chunk':1}], [3,2])

    def test_no_dummy_picture_or_missing_audio_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            with self.assertRaises(ValueError):
                runner.render_review([p/'nonexistent.png'],[8.0],p/'audio.m4a',p/'review.mp4')

    def test_end_to_end_cpu_preflight_never_requests_gpu(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            text='\n\n'.join(['Kai saw the heavy gate and held the forged key.']*55)
            book=root/'novel.txt';book.write_text(text)
            input_dir=root/'input';input_dir.mkdir()
            core.create_package(story_id='new-cultivation-story',title='New Cultivation Story',
                manuscript=book,episodes={1:book},output=input_dir/core.BUNDLE,
                source_approved=True)
            with mock.patch.object(runner,'WORK',root/'working'), mock.patch.dict('os.environ',{'MANHUA_INPUT_DIR':str(input_dir)}):
                report=runner.process(story_id='new-cultivation-story',episode=1,
                                      phase='preflight',quality='fast')
            self.assertTrue(report['no_gpu_used'])
            self.assertFalse(report['release_approved'])
            self.assertGreater(report['panels'],0)
            self.assertTrue((root/'working'/'PRIVATE_PREFLIGHT_REPORT.json').is_file())

    def test_cached_narration_chunks_do_not_import_gpu(self):
        from video.audiobook_studio.episode_fastlane import chunk_key
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            part={'index':0,'text':'The gate was locked. Kai held the forged key.', 'words':9}
            key=chunk_key(part['text'],model=runner.MODEL,speaker=runner.SPEAKER,
                          instruction=runner.INSTRUCTION)
            target=root/'narration'/f'0000-{key}.wav'
            target.parent.mkdir(parents=True)
            with wave.open(str(target),'wb') as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
                f.writeframes(b'\0'*48000)
            wavs,durations=runner.voice_chunks([part],root)
            self.assertEqual(wavs,[target])
            self.assertAlmostEqual(durations[0],1.0)

    def test_narration_profile_not_substituted(self):
        self.assertEqual(runner.MODEL,'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice')
        self.assertEqual(runner.SPEAKER,'Ryan')
        self.assertEqual(runner.LANGUAGE,'English')
        self.assertEqual(runner.INSTRUCTION,
            'A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting.')
        self.assertFalse('3d' in core.STYLES['cultivation'].lower())

    def test_image_modes_real_2d_model_profiles(self):
        self.assertIn('sdxl-turbo',runner.IMAGE_MODELS['fast']['id'])
        self.assertIn('animagine',runner.IMAGE_MODELS['quality']['id'])
        self.assertLess(runner.IMAGE_MODELS['fast']['steps'],runner.IMAGE_MODELS['quality']['steps'])


if __name__=='__main__':
    unittest.main()