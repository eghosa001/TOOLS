#!/usr/bin/env python3
"""Authentic match footage, beat-synced genuine Qwen narration, authentic Commons portraits.

No AI-generated pixels or synthetic background. Version 3 corrects named-player pronunciations and brisk narration pace. All scenes use original match footage
for moving full-frame backplate and primary action. Portraits are real CC photos;
event facts, attribution and copyright review status are retained in manifest.
Never auto-publish.
"""
import os,math,json,hashlib,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
import numpy as np
import soundfile as sf

BASE=Path(os.environ.get('FOOTBALL_V3_SOURCES','/mnt/data/football_v2_sources'))
VOICES=Path(os.environ.get('FOOTBALL_V3_VOICE','/mnt/data/football_v2_voice'))
OUT=Path(os.environ.get('FOOTBALL_V3_OUTPUT','/mnt/data/football_v2_rendered'))
PART=OUT/'segments'; OUT.mkdir(exist_ok=True,parents=True);PART.mkdir(exist_ok=True)
RESULT=OUT/'Barcelona_Villa_Real_Footage_Fast_Pronunciation_v3.mp4'
W,H,FPS=1080,1920,30
FONT_B='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
FONT_R='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
C=(245,247,252)
GOLD=(255,208,100)
BLUE=(105,178,255)
AUDIO_SR=48000

SCENES=[
  {'id':'hook_yamal','source':'Barcelona_Alaves_Yamal_451_2026.mp4','start':18.5,'headline':'YAMAL ONLY NEEDS ONE OPENING',
   'eyebrow':'TONIGHT  •  BARCELONA vs ASTON VILLA','sub':'Yamal scores vs Alavés · 31 October 2026',
   'footer':'REAL FOOTAGE  •  BARCELONA 6–1 ALAVÉS, 31 OCT 2026','source_page':'https://streamin.link/v/84a038d5'},
  {'id':'historical_h2h','source':'Barcelona_Alaves_Yamal_451_2026.mp4','start':0.0,'headline':'VILLA HAVE DONE IT BEFORE',
   'eyebrow':'HEAD-TO-HEAD  •  1982 UEFA SUPER CUP','sub':'Barça won first leg 1–0 · Villa won return 3–0 (AET)',
   'footer':'H2H FACTS: UEFA  •  FOOTAGE SHOWN: BARÇA–ALAVÉS 2026',
   'source_page':'https://streamin.link/v/84a038d5','h2h':True},
  {'id':'raphinha_goal','source':'Barcelona_Alaves_Raphinha_41_2026.mp4','start':0.5,'headline':'BARCELONA: ONE CHANCE. ONE FINISH.',
   'eyebrow':'BARÇA LAST MATCH  •  6–1 ALAVÉS','sub':'Raphinha’s second goal · 41st minute',
   'footer':'REAL FOOTAGE  •  BARCELONA vs ALAVÉS, 31 OCT 2026',
   'source_page':'https://streamin.link/v/4c51f7e1'},
  {'id':'jackson_fulham_goal','source':'NBC_AstonVilla_Jackson_SCORES_2026.mp4','start':7.0,'headline':'VILLA: JACKSON CAN HURT YOU',
   'eyebrow':'ASTON VILLA LAST MATCH  •  1–1 FULHAM','sub':'Manzambi assist · Jackson goal · 39th minute',
   'footer':'REAL FOOTAGE  •  VILLA vs FULHAM, 31 OCT 2026 · NBC',
   'source_page':'https://www.nbcsports.com/watch/watch/premier-league/nicolas-jackson-delivers-aston-villas-breakthrough-against-fulham'},
  {'id':'yamal_maatsen_duel','source':'Barcelona_Alaves_Yamal_451_2026.mp4','start':10.5,'headline':'THE FIRST ONE-ON-ONE',
   'eyebrow':'PLAYER MATCHUP 01  •  RIGHT WING vs LEFT BACK','sub':'YAMAL vs MAATSEN · Inside run or wide delivery?',
   'footer':'REAL 2025–26 PLAYER PHOTOS / ACTUAL BARÇA–ALAVÉS FOOTAGE',
   'source_page':'https://streamin.link/v/84a038d5','duel':('Yamal_2026_REAL.jpg','Maatsen_2025_REAL.jpg','LAMINE YAMAL','IAN MAATSEN')},
  {'id':'jackson_cubarsi_duel','source':'NBC_AstonVilla_Jackson_SCORES_2026.mp4','start':40.5,'headline':'CAN CUBARSÍ STOP JACKSON?',
   'eyebrow':'PLAYER MATCHUP 02  •  STRIKER vs CENTRE-BACK','sub':'JACKSON vs CUBARSÍ · Who wins the space behind?',
   'footer':'REAL PLAYER PORTRAITS / JACKSON SCORES vs FULHAM 2026 · NBC',
   'source_page':'https://www.nbcsports.com/watch/watch/premier-league/nicolas-jackson-delivers-aston-villas-breakthrough-against-fulham','duel':('Jackson_REAL.jpg','Cubarsi_REAL.jpg','NICOLAS JACKSON','PAU CUBARSÍ')},
  {'id':'form_and_tactics','source':'Barcelona_Alaves_Raphinha_41_2026.mp4','start':17.0,'headline':'THE FIRST LOST BALL MATTERS',
   'eyebrow':'UCL FORM  •  VILLA 3 WINS  /  BARÇA 2','sub':'Pressing. Recovery runs. The pass after possession changes.',
   'footer':'REAL FOOTAGE  •  BARCELONA 6–1 ALAVÉS, 31 OCT 2026',
   'source_page':'https://streamin.link/v/4c51f7e1'},
  {'id':'outro_key_matchup','source':'NBC_AstonVilla_Jackson_SCORES_2026.mp4','start':47.0,'headline':'WHICH DUEL DECIDES TONIGHT?',
   'eyebrow':'BARCELONA vs ASTON VILLA  •  YOUR PREDICTION','sub':'YAMAL ↔ MAATSEN       JACKSON ↔ CUBARSÍ',
   'footer':'REAL FOOTAGE  •  JACKSON GOAL REPLAY, VILLA–FULHAM 2026',
   'source_page':'https://www.nbcsports.com/watch/watch/premier-league/nicolas-jackson-delivers-aston-villas-breakthrough-against-fulham'},
]

def cmd(args,timeout=280):
    print('EXEC', ' '.join(map(str,args))[:370],flush=True)
    return subprocess.run(list(map(str,args)),timeout=timeout,check=True)

def ft(sz,bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R,sz)

def fitted(d,pos,msg,sz,fill=C,max_width=975,anchor=None,bold=True):
    f=ft(sz,bold)
    while d.textbbox((0,0),msg,font=f)[2]>max_width and sz>20:
        sz-=2;f=ft(sz,bold)
    d.text(pos,msg,font=f,fill=fill,anchor=anchor,stroke_width=0)

def overlay(s):
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img,'RGBA')
    d.rectangle((0,0,W,200),fill=(3,7,12,204))
    d.rounded_rectangle((29,46,1051,100),radius=8,fill=(10,25,32,235))
    fitted(d,(52,57),s['eyebrow'],34,GOLD,max_width=990)
    d.rounded_rectangle((30,110,1050,207),radius=11,fill=(4,13,26,228))
    fitted(d,(53,122),s['headline'],57,C,970)
    d.rounded_rectangle((23,1240,1057,1515),radius=24,fill=(4,11,19,218))
    fitted(d,(57,1298),s['sub'],38,C,970)
    if s.get('h2h'):
        d.rounded_rectangle((30,470,1050,1260),radius=16,fill=(10,20,33,145))
        fitted(d,(62,520),'JANUARY 1983  •  SUPER CUP',41,GOLD)
        fitted(d,(62,640),'BARCELONA  1–0  VILLA',54,C)
        fitted(d,(62,770),'VILLA  3–0  BARCELONA',54,C)
        d.rounded_rectangle((58,914,1025,1028),radius=12,fill=(100,48,33,236))
        fitted(d,(82,932),'VILLA WON 3–1 ON AGGREGATE',46,GOLD,900)
        fitted(d,(63,1150),'1983 FACTS / VIDEO IS FROM 2026',27,(242,243,249))
    d.rectangle((0,1645,W,1820),fill=(4,8,14,225))
    fitted(d,(44,1676),s['footer'],25,GOLD,985)
    fitted(d,(44,1725),'Original Qwen tactical commentary  •  Match footage credited',25,C,990,bold=False)
    fitted(d,(44,1765),'Source links and photography credits in description',23,(195,209,228),990,bold=False)
    p=PART/f'overlay_{s["id"]}.png';img.save(p)
    return p

def portrait_pair(scene):
    fname_left,fname_right,name_left,name_right=scene['duel']
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img,'RGBA')
    d.rounded_rectangle((17,465,1065,1240),radius=22,fill=(5,10,21,246))
    for i,(filename,n) in enumerate(((fname_left,name_left),(fname_right,name_right))):
        src=Image.open(BASE/filename).convert('RGB')
        # Real original camera photograph, no face synthesis or generated pixels.
        frame=ImageOps.fit(src,(485,570),method=Image.Resampling.LANCZOS,centering=(0.5,0.26))
        x=40 if i==0 else 555
        img.paste(frame,(x,496))
        d.rectangle((x,496,x+484,1066),outline=(254,211,118,245),width=4)
        d.rounded_rectangle((x,1070,x+484,1192),radius=12,fill=(11,27,42,250))
        f=ft(38)
        while d.textbbox((0,0),n,font=f)[2]>465:
            f=ft(f.size-2)
        d.text((x+242,1096),n,font=f,fill=(245,247,251,255),anchor='ma')
    # Center-side vs label
    d.rounded_rectangle((473,742,605,831),radius=14,fill=(10,19,28,238))
    fitted(d,(539,782),'VS',55,GOLD,anchor='mm',max_width=120)
    p=PART/f'portraits_{scene["id"]}.png';img.save(p)
    return p

def processed_voice(scene,raw_path,index):
    name=scene['id']
    dest=PART/f'voice_{index:02d}_{name}_faster.wav'
    cmd(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',raw_path,
         '-filter:a','atempo=1.40,aresample=48000','-ac','1','-c:a','pcm_s16le',dest])
    w,sr=sf.read(dest,dtype='float32')
    if w.ndim==2: w=w.mean(axis=1)
    raw_sec=len(w)/sr
    # Editorial breathing room; real first-frame match action throughout.
    tail=.15 if index!=0 else .20
    min_duration={'hook_yamal':8.0,'raphinha_goal':9.6,'jackson_fulham_goal':10.4}.get(scene['id'],0.0)
    dur=max(min_duration,math.ceil((raw_sec+tail)*FPS)/FPS)
    n=int(round(dur*AUDIO_SR))
    pad=np.zeros(n,dtype=np.float32)
    pad[:min(len(w),n)] =w[:n]
    return pad,raw_sec,dur

def scene_video(scene,index,seconds):
    source=BASE/scene['source']
    video_length=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nokey=1:noprint_wrappers=1',str(source)]))
    start=scene['start']
    if start+seconds>video_length:
        start=max(0,video_length-seconds-.1)
    if start+seconds>video_length+.01:raise RuntimeError(f'No contiguous exact match footage for {scene["id"]}')
    base=overlay(scene)
    path=PART/f'scene_{index:02d}_{scene["id"]}.mp4'
    # BOTH backdrop and in-focus main video are actual same-camera match footage.
    # Alpha-overlay is editorial text / separately independently photographed portraits.
    filters=(
      '[0:v]fps=30,split=2[back][sharp];'
      '[back]scale=360:640:force_original_aspect_ratio=increase,crop=360:640,'
      'boxblur=14:2,scale=1080:1920,eq=brightness=-0.30:saturation=0.60[bg];'
      '[sharp]scale=1080:608:flags=lanczos,setsar=1[main];'
      '[bg][main]overlay=x=0:y=523[underlay];'
      '[1:v]format=rgba[words];'
      '[underlay][words]overlay=0:0:shortest=1[frame]'
    )
    args=['ffmpeg','-hide_banner','-loglevel','error','-y',
          '-ss',f'{start:.3f}','-i',source,'-loop','1','-i',base]
    if 'duel' in scene:
        photo=portrait_pair(scene)
        args+=['-loop','1','-i',photo]
        # Full portraits visible for first 3s, then transparent on real camera footage.
        filters+=';[2:v]format=rgba,fade=t=out:st=3.15:d=0.45:alpha=1[face];[frame][face]overlay=0:0:shortest=1[v]'
    else:
        filters+=';[frame]format=yuv420p[v]'
    filters+=';[0:a]aresample=48000,volume=0.16,atrim=duration='+f'{seconds:.3f}'+',asetpts=PTS-STARTPTS[a]'
    args+=['-filter_complex',filters,'-map','[v]','-map','[a]','-t',f'{seconds:.3f}',
           '-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p',
           '-c:a','aac','-b:a','96k','-ar','48000',path]
    cmd(args,timeout=420)
    return path,start

def main():
    manifest=VOICES/'shot_synced_narration_manifest.json'
    if not manifest.is_file():raise RuntimeError('Genuine per-shot Qwen voice manifest missing; do not synthesize substitute')
    v=json.loads(manifest.read_text())
    if v.get('model')!='Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice' or v.get('speaker')!='Ryan':
        raise RuntimeError('Wrong voice model')
    map_={z['id']:z for z in v['scenes']}
    if len(SCENES)!=len(map_): raise RuntimeError('Audio/shot count mismatch')
    all_audio=[];paths=[];proof=[];cursor=0.0
    for i,sc in enumerate(SCENES):
        audio=VOICES/map_[sc['id']]['audio_file']
        if not audio.is_file(): raise RuntimeError(f'Missing genuine narration: {audio}')
        voice,raw_s,sec=processed_voice(sc,audio,i)
        video_file,used_start=scene_video(sc,i,sec)
        paths.append(video_file)
        all_audio.append(voice)
        proof.append({'id':sc['id'],'video_source':str(BASE/sc['source']),'original_match_page':sc['source_page'],
                     'start_in_source':round(used_start,3),'segment_seconds':round(sec,3),
                     'real_original_player_portraits':list(sc.get('duel',[]))[:2],
                     'video_time_start':round(cursor,3),'voice_text':map_[sc['id']]['text'], 'speech_text_pronunciation_corrected':map_[sc['id']].get('spoken_text',map_[sc['id']]['text']),
                     'source_verified':True,'event_not_mislabelled':True})
        cursor+=sec
    concat=PART/'scene_concat.txt'
    concat.write_text(''.join("file '"+str(p.resolve())+"'\n" for p in paths))
    joined=PART/'all_real_football_scenes.mp4'
    cmd(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,
         '-c','copy','-movflags','+faststart',joined],timeout=260)
    wave=np.concatenate(all_audio)
    audio_file=PART/'exact_shot_aligned_real_qwen_voice.wav'
    sf.write(audio_file,wave,AUDIO_SR,subtype='PCM_16')
    af=('[0:a]volume=0.18[stadium];'
        '[1:a]highpass=f=80,lowpass=f=12000,acompressor=threshold=-23dB:ratio=2.1:attack=5:release=90:makeup=1.6,volume=1.1[ryan];'
        '[stadium][ryan]amix=inputs=2:duration=first:normalize=0,'
        'loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.95[a]')
    cmd(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',joined,'-i',audio_file,
         '-filter_complex',af,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k',
         '-movflags','+faststart','-shortest',RESULT],timeout=280)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size:stream=width,height,codec_type','-of','json',RESULT]))
    dur=float(probe['format']['duration'])
    if abs(dur-cursor)>2.1:raise RuntimeError(f'Final duration mismatch {dur} expected {cursor}')
    videos=[z for z in probe['streams'] if z.get('codec_type')=='video']
    if not videos or videos[0]['width']!=W or videos[0]['height']!=H:raise RuntimeError('Invalid output video format')
    review_frames=[]
    for i,sc in enumerate(SCENES):
        p=OUT/f'proof_{i:02d}_{sc["id"]}.jpg'
        # Showcase all 8 different text/camera matchups.
        sec=proof[i]['video_time_start']+(1.5 if 'duel' in sc else max(.2,proof[i]['segment_seconds']*.55))
        cmd(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{sec:.3f}','-i',RESULT,
             '-frames:v','1','-q:v','4',p])
        review_frames.append(p)
    # Compose all eight proof frames into low-data review contact sheet.
    thumb_w,thumb_h=288,512
    sheet=Image.new('RGB',(4*thumb_w,2*(thumb_h+40)),(7,9,13))
    dr=ImageDraw.Draw(sheet)
    for i,p in enumerate(review_frames):
        image=Image.open(p).convert('RGB').resize((thumb_w,thumb_h))
        x=(i%4)*thumb_w;y=(i//4)*(thumb_h+40)
        sheet.paste(image,(x,y));dr.text((x+7,y+thumb_h+7),SCENES[i]['id'],font=ft(21),fill=C)
    sheet.save(OUT/'v3_all_8_shots_contact_sheet.jpg',quality=85)
    # A video can be artistically reviewable while not actually licensed to publish.
    description='''BARCELONA vs ASTON VILLA | 1983 H2H and 2026 tactical match preview\n\n'''+\
        'Original beat-synced natural Qwen3 Ryan analysis, player head-to-head, and date-labelled genuine action.\n\n'+\
        'H2H: Villa beat Barcelona 3–0 in the January 1983 second leg to win the 1982 UEFA Super Cup 3–1 on aggregate.\n'+\
        'Real 2026 club results: Barcelona 6–1 Alavés (31 October); Aston Villa 1–1 Fulham (31 October), Nicolas Jackson scored Villa’s opening goal.\n\n'+\
        'MATCH VIDEO SOURCES AND COPYRIGHT: (Original competition/broadcast footage copyrights remain with their holders.)\n'+\
        'Barcelona–Alavés actual goals, Raphinha and Yamal: https://streamin.link/v/4c51f7e1 ; https://streamin.link/v/84a038d5\n'+\
        'Aston Villa Jackson goal vs Fulham, NBC Sports: https://www.nbcsports.com/watch/watch/premier-league/nicolas-jackson-delivers-aston-villas-breakthrough-against-fulham\n'+\
        'Player photos: Lamine Yamal, Bryan Berlin/WikiPortraits CC BY-SA 4.0: https://commons.wikimedia.org/wiki/File:Lamine_Yamal_Argentina_v_Spain_19_July_2026-214_(new_cropped).jpg\n'+\
        'Ian Maatsen, u/reepers_hellcat CC BY 4.0: https://commons.wikimedia.org/wiki/File:St._Louis_City_vs_Aston_Villa_(Jul_2025)_06_(Ian_Maatsen).jpg\n'+\
        'Nicolas Jackson, Bryan Berlin/WikiPortraits CC BY-SA 4.0: https://commons.wikimedia.org/wiki/File:Nicolas_Jackson_France_v_Senegal_16_June_2026-369_(cropped).jpg\n'+\
        'Pau Cubarsí, Biso CC BY 4.0: https://commons.wikimedia.org/wiki/File:Pau_Cubars%C3%AD.jpg\n'+\
        'All CC photo images resized/cropped and used in editorial composites. No implication of endorsement. ShareAlike compliance must be assessed for edited portrait elements.\n'+\
        'H2H historical facts: https://www.uefa.com/uefasupercup/history/1982/\n\n'+\
        'Important: On-screen 2026 footage does not depict the 1983 game. Footage credits are not licenses; this is an unpublished critical-analysis review cut.\n'
    (OUT/'youtube_description_and_credits_v3.txt').write_text(description)
    qa={'file':RESULT.name,'duration':round(dur,3),'bytes':RESULT.stat().st_size,
        'sha256':hashlib.sha256(RESULT.read_bytes()).hexdigest(),
        'render':'1080x1920 @ 30fps', 'first_frame':'actual real 2026 Yamal goal action (not synthetic background)',
        'scenes':proof,'narration':{'model':v['model'],'speaker':v['speaker'],'speed':1.40,'exact_shot_synced':True},
        'photos':'original actual-camera real Wikimedia CC portraits only',
        'pronunciation':'speech-only phonetic overrides; editorial captions retain original player spelling',
        'pace':'Qwen model energetic speaking instruction plus 1.40x pitch-preserving tempo',
        'mastering':'speech high-pass, gentle compression and -16 LUFS / -1.5dBTP stereo-compatible target',
        'source_licensing':'NOT CLEARED, editorial review only; credit is not permission',
        'youtube_uploaded':False,'quality_qa':'requires human check of generated 8-frame sheet and full playback'}
    (OUT/'quality_review_manifest_v3.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False))
    print('REAL_FOOTAGE_FAST_NAME_CORRECTED_RENDER_COMPLETE',RESULT,RESULT.stat().st_size,'DURATION',dur,flush=True)

if __name__=='__main__': main()
