#!/usr/bin/env python3
"""Master 15-chapter Titanic documentary with item-sourced CC0 score, and export credits."""
from pathlib import Path
import subprocess,urllib.request,hashlib,json,math
P=Path(__file__).resolve().parent/'premium_exports'
C=P/'licensed_score';C.mkdir(parents=True,exist_ok=True)
LIB=[
{'id':'after_storm','page':'https://opengameart.org/content/inspirational-cinematic-ambient-after-the-storm',
 'url':'https://opengameart.org/sites/default/files/keyframe_audio-inspirational-cinematic-ambient-after-the-storm-133540.mp3',
 'author':'Eltonthomasmba','license':'CC0','file':'after_storm.mp3'},
{'id':'soul_release','page':'https://opengameart.org/content/soul-release',
 'url':'https://opengameart.org/sites/default/files/ruskerdax_-_soul_release.mp3',
 'author':'Ruskerdax','license':'CC0','file':'soul_release.mp3'},
{'id':'regret_piano','page':'https://opengameart.org/content/regret-short-emotional-piano',
 'url':'https://opengameart.org/sites/default/files/piano_nostalgia_0.mp3',
 'author':'Wolfgang_','license':'CC0','file':'regret_piano.mp3'},
{'id':'first_light','page':'https://opengameart.org/node/182244',
 'url':'https://opengameart.org/sites/default/files/first_light_particles_0.wav',
 'author':'Yoiyami','license':'CC0','file':'first_light.wav'},
]
def sh(cmd):subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
for rec in LIB:
    path=C/rec['file']
    if not path.exists():
        req=urllib.request.Request(rec['url'],headers={'User-Agent':'FactsUncovered-HistoryDocumentary-LicensedSound/1.0'})
        with urllib.request.urlopen(req,timeout=100) as stream,path.open('wb') as f:
            amount=0
            while True:
                buf=stream.read(1024*1024)
                if not buf:break
                amount+=len(buf)
                if amount>45_000_000:raise RuntimeError('Unreasonably large music asset')
                f.write(buf)
    sh(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1',str(path)])
    rec['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    print('CC0_TRACK',rec['id'],path.stat().st_size,flush=True)
qa=json.loads((P/'technical_QA.json').read_text());duration=qa[0]['seconds']
marks=json.loads((P/'chapter_times.json').read_text())
segments=[]
for i,item in enumerate(marks):
    a=float(item['start_seconds'])
    b=float(marks[i+1]['start_seconds'] if i+1<len(marks) else duration)
    sec=max(1,b-a)
    rec=LIB[[0,3,0,1,2,0,1,3,0,1,2,1,3,0,3][i]]
    dest=C/f'score_chapter_{i+1:02}.m4a'
    fadeout=max(0,sec-2.5)
    filters=f'volume=-27dB,afade=t=in:st=0:d=2.5,afade=t=out:st={fadeout:.2f}:d=2.5,aresample=44100'
    sh(['ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','-1','-i',str(C/rec['file']),
         '-t',f'{sec:.3f}','-vn','-af',filters,'-ac','2','-c:a','aac','-b:a','96k',str(dest)])
    segments.append(dest)
playlist=C/'chapter_score_concat.txt'
playlist.write_text(''.join("file '"+str(x.resolve())+"'\n" for x in segments))
song=C/'all_chapters_score.m4a'
sh(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(playlist),'-c','copy',str(song)])
main=P/'Titanic_Complete_Story_1080p.mp4'
final=P/'Titanic_Complete_Story_1080p_SCORED.mp4'
sh(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(main),'-i',str(song),
    '-filter_complex','[0:a]aformat=channel_layouts=stereo[v];[1:a]aformat=channel_layouts=stereo[m];[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9[a]',
    '-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(final)])
sh(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name','-of','json',str(final)])
(P/'MUSIC_RIGHTS.json').write_text(json.dumps({'tracks':LIB,'mix':'voice narration intelligible; background each -27dB and chapter fade',
    'source':'OpenGameArt original CC0 pages; links preserved','status':'requires listening/rights review'},indent=2))
print('SCORED_CANDIDATE',final,final.stat().st_size,flush=True)
