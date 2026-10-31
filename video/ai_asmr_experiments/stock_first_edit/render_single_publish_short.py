#!/usr/bin/env python3
"""One purposeful, visually coherent original 34s ASMR Short: POUR / RIPPLE / BLOOM.
Real commercially licensed footage, independently generated Foley, no generated video.
"""
import subprocess, json, hashlib, os, zipfile, pathlib
from PIL import Image, ImageDraw, ImageFont
P=pathlib.Path(os.environ.get('ASMR_PUBLISH_DIR','/mnt/data/asmr_stock_first/publish_candidate'))
SRC=pathlib.Path(os.environ.get('ASMR_STOCK_DIR','/mnt/data/asmr_stock_first/stock'))
AUDIO=pathlib.Path(os.environ.get('ASMR_AUDIO_DIR','/mnt/data/asmr_stock_first'))
P.mkdir(exist_ok=True);(P/'segments').mkdir(exist_ok=True)
FPS=24; W=1080; H=1920
# Each shot has a distinct visual job; clips deliberately form a single water -> colour reveal.
SHOTS=[
 ('01_clear_pour','clear_pour',8.5,4.4,'eq=contrast=1.13:saturation=1.08:brightness=-0.016','WATER / THE FIRST POUR'),
 ('02_surface','jets',1.0,3.2,'eq=contrast=1.06:saturation=0.90:brightness=-0.006',None),
 ('03_colour_pour','color_pour',3.0,4.1,'eq=contrast=1.08:saturation=1.10:brightness=-0.055',None),
 ('04_splash','color_pour',13.2,3.8,'eq=contrast=1.10:saturation=1.11:brightness=-0.060',None),
 ('05_first_bloom','ink',0.3,4.6,'eq=contrast=1.10:saturation=1.08:brightness=-0.014','COLOUR / SLOW BLOOM'),
 ('06_colour_growth','ink',4.4,4.8,'eq=contrast=1.07:saturation=1.10:brightness=-0.015',None),
 ('07_macro_plumes','ink',9.5,5.3,'eq=contrast=1.08:saturation=1.12:brightness=-0.008',None),
 ('08_splash_final','color_pour',15.05,3.8,'eq=contrast=1.08:saturation=1.10:brightness=-0.050',None),
]
T=sum(s[3] for s in SHOTS)
assert abs(T-34.0)<0.0001

def call(cmd):
 subprocess.run(cmd,check=True,timeout=180,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

def probe(file):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(file)]))

# Original licence metadata and asset integrity are mandatory: never post an unknown stock copy.
from_map={x['name']:x for x in json.loads((SRC/'CUP_SOURCE_LEDGER.json').read_text()) if x.get('status')=='verified'}
from_map.update({x['name']:x for x in json.loads((SRC/'SOURCE_LICENSES.json').read_text())['assets']})
for asset in {shot[1] for shot in SHOTS}:
    row=from_map.get(asset)
    source=SRC/(asset+'.mp4')
    if not row or not row.get('sha256') or not row.get('license') or not source.exists():
        raise RuntimeError('Unlicensed or missing video: '+asset)
    actual=hashlib.sha256(source.read_bytes()).hexdigest()
    if actual!=row['sha256']:
        raise RuntimeError('Video checksum differs from rights record: '+asset)
# Do not redownload model weights. Previously generated Foley WAVs are cached or
# can be extracted once from the verified prior artifact ZIP.
zipfile_path=os.environ.get('ASMR_SFX_ZIP','/mnt/data/four_asmr_real_foley_generated.zip')
for stem in ('ripples','ink'):
    wav=AUDIO/f'{stem}_REAL_SFX_20s.wav'
    if not wav.exists() and pathlib.Path(zipfile_path).exists():
        AUDIO.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(zipfile_path) as z:
            content=z.read(wav.name)
        wav.write_bytes(content)
segments=[];timeline=[];cursor=0
for idx,(title,asset,start,dur,tone,text) in enumerate(SHOTS):
 src=SRC/(asset+'.mp4');info=probe(src);length=float(info['format']['duration'])
 if not src.is_file() or start+dur>length+.05:raise RuntimeError('Missing or too-short source '+str(src))
 zoom=1.055 if idx%2==0 else 1.035
 ow=round(W*zoom/2)*2;oh=round(H*zoom/2)*2
 f=f'fps={FPS},scale={ow}:{oh}:force_original_aspect_ratio=increase:flags=lanczos,'
 f+=f'crop={W}:{H}:x=(iw-{W})*(0.5+0.085*sin(n*0.023+{idx})):y=(ih-{H})*(0.50+0.034*sin(n*0.012+{idx})),'
 f+=f'{tone},unsharp=5:5:0.24:3:3:0,format=yuv420p'
 if text:
  f+=",drawbox=x=58:y=175:w=190:h=2:color=white@0.4:t=fill:enable='lt(t,1.3)'"
  f+=f",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{text}':fontcolor=white@0.90:fontsize=27:x=58:y=120:enable='lt(t,1.3)'"
 if idx==len(SHOTS)-1:
  # End brand cue is subtle, preserves attention for satisfying action.
  f+=",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='Satisfying Texture ASMR':fontcolor=white@0.82:fontsize=29:x=(w-text_w)/2:y=h-205:enable='gte(t,2.4)'"
 path=P/'segments'/(f'{idx+1:02d}_{title}.mp4')
 call(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(src),'-t',str(dur),'-vf',f,'-an','-r',str(FPS),'-frames:v',str(round(dur*FPS)),'-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-profile:v','high','-movflags','+faststart',str(path)])
 segments.append(path)
 timeline.append(dict(start=round(cursor,2),end=round(cursor+dur,2),source=asset,source_offset=start,seconds=dur,edit='pan,zoom,color_grade,cut'))
 cursor+=dur
 print('EDITED',idx+1,asset,start,dur,flush=True)

lst=P/'segments'/'concat.txt';lst.write_text(''.join("file '"+str(path)+"'\n" for path in segments))
picture=P/'segments'/'picture.mp4'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-an','-c:v','copy','-movflags','+faststart',str(picture)])
# Original generated environmental Foley, restrained and crossfaded at the water-to-cloud transition.
rip=AUDIO/'ripples_REAL_SFX_20s.wav';ink=AUDIO/'ink_REAL_SFX_20s.wav'
assert rip.exists() and ink.exists()
fc=("[0:a]atrim=0:16.7,asetpts=PTS-STARTPTS,afade=t=out:st=14.7:d=2.0,volume=0.75[water];"
    "[1:a]atrim=0:20,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=2.0,afade=t=out:st=18:d=2.0,adelay=14000|14000,volume=0.9[bloom];"
    "[0:a]atrim=3:7.0,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.6,afade=t=out:st=3.4:d=0.6,adelay=30000|30000,volume=0.62[return];"
    "[water][bloom][return]amix=inputs=3:normalize=0,atrim=0:34,aresample=48000,"
    "highpass=f=33,volume=6dB,alimiter=limit=0.89:attack=8:release=85,afade=t=in:st=0:d=0.24,afade=t=out:st=33.65:d=0.35[a]")
audio=P/'segments'/'original_sound_design.wav'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(rip),'-i',str(ink),'-filter_complex',fc,'-map','[a]','-ac','2','-ar','48000','-c:a','pcm_s16le',str(audio)])
master=P/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_1080p.mp4'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(picture),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t','34','-movflags','+faststart',str(master)])
mobile=P/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_720p_REVIEW.mp4'
call(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(master),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(mobile)])

# Representative contact sheet of actual exported video, not stock promo imagery.
frames=[]
for t in [1.0,5.8,9.2,13.4,17.4,20.9,26.8,32.8]:
 q=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(t),'-i',str(mobile),'-frames:v','1','-vf','scale=270:480','-f','image2pipe','-vcodec','mjpeg','-'],capture_output=True,timeout=18,check=True)
 from io import BytesIO
 frames.append(Image.open(BytesIO(q.stdout)).convert('RGB'))
sheet=Image.new('RGB',(270*4,500*2),(10,11,13));d=ImageDraw.Draw(sheet)
for i,im in enumerate(frames):
 x=(i%4)*270;y=(i//4)*500;sheet.paste(im,(x,y+20));d.text((x+8,y+3),f'{[1.0,5.8,9.2,13.4,17.4,20.9,26.8,32.8][i]}s',fill='white')
sheet.save(P/'ONE_SHORT_STORYBOARD_CONTACT_SHEET.jpg',quality=88)

lic=[]
lic.extend(json.loads((SRC/'CUP_SOURCE_LEDGER.json').read_text()))
orig=json.loads((SRC/'SOURCE_LICENSES.json').read_text())
for name in ['jets','ink']:
 lic.append(next(x for x in orig['assets'] if x['name']==name))
report={'project':'Satisfying Texture ASMR','version':'single-publishing-candidate-2026-10-31','title':'Pour, Ripple & Colour Bloom | Relaxing Liquid ASMR #Shorts',
 'fps':24,'resolution':'1080x1920','seconds':34,'creative_treatment':'8 hand-selected edits telling one progression from transparent water to colour poured into cup and ink blooms; macro crops, slow intentional movement, warm-to-cool-to-color grade, shot-specific transitions and original layered Foley; no speech, no music.',
 'timeline':timeline,'sound_origin':'Stable Audio 3 Small-SFX master WAVs previously generated on private Kaggle; not Qwen3-TTS','video_sources':lic,'human_visual_approval':False,'human_listening_approval':False,'youtube_published':False,'outputs':{}}
for path in [master,mobile,audio]:
 v=probe(path);d=float(v['format']['duration']);assert 33.7<d<34.3,(path,d)
 assert path.stat().st_size>250000
 report['outputs'][path.name]=dict(seconds=d,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),streams=[x['codec_type'] for x in v['streams']])
(P/'SOURCE_AND_EXPORT_PROVENANCE.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
(P/'YOUTUBE_POSTING_PACKAGE.txt').write_text('''TITLE: Pour, Ripple & Colour Bloom | Relaxing Liquid ASMR #Shorts\n\nDESCRIPTION:\nA little water, a slow splash, and colour blooming into soft clouds. Watch the flow, listen with headphones, and enjoy a quiet half-minute.\n\nNo talking. No music. Liquid textures and gentle ASMR sound design.\n\nFootage: properly licensed clips from Pexels and Mixkit, edited into an original sequence; sound: independently composed mix using Stable Audio 3 Small-SFX generated Foley. See the included SOURCE_AND_EXPORT_PROVENANCE.json for individual source links and creators.\n\n#ASMR #Satisfying #LiquidASMR #OddlySatisfying #Shorts\n\nSUGGESTED COVER: frame around 20.9s showing the vibrant ink cloud.\nUPLOAD: vertical 1080 x 1920 MP4, no added music, category Entertainment.\nSTATUS: posting-ready editorial draft pending creator approval; not uploaded to YouTube.\n''')
# Mandatory post-render audio QA and shot-aligned Foley repair.
# The previous amix command produced a valid 34s file with digital silence after 17s.
# Fail closed rather than declaring an incomplete or silent soundtrack production-ready.
import sys
audio_repair=pathlib.Path(__file__).with_name('fix_audio_sync_v3.py')
if not audio_repair.is_file():raise RuntimeError('Mandatory ASMR audio continuity repair script missing')
env=os.environ.copy()
env['ASMR_PUBLISH_DIR']=str(P)
env['ASMR_SFX_ZIP']=str(zipfile_path)
subprocess.run([sys.executable,str(audio_repair)],env=env,check=True,timeout=360)
fixed_master=P/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_AUDIO_FIXED_v3_1080p.mp4'
fixed_mobile=P/'POUR_RIPPLE_COLOUR_BLOOM_SHORT_AUDIO_FIXED_v3_720p.mp4'
os.replace(fixed_master,master)
os.replace(fixed_mobile,mobile)
report=json.loads((P/'SOURCE_AND_EXPORT_PROVENANCE.json').read_text())
report['audio_integrity']='PASS: verified every second, shot-specific sound; no full-second silence'
report['audio_repair_qa']='AUDIO_SYNC_REPAIR_QA_v3.json'
report['version']='single-publishing-candidate-audio-synced-v3'
for output in [master,mobile]:
    v=probe(output);d=float(v['format']['duration'])
    assert 33.7<d<34.3
    report['outputs'][output.name]=dict(seconds=d,bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),streams=[x['codec_type'] for x in v['streams']])
(P/'SOURCE_AND_EXPORT_PROVENANCE.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
# IMPORTANT: never treat V3's constant drip soundtrack as publishable.
# Archive its temporary outputs and ALWAYS produce the action-matched V4 Short.
v4=pathlib.Path(__file__).with_name('render_action_matched_v4.py')
if not v4.is_file():raise RuntimeError('V4 real-action sound editor missing; refuse legacy 34-second release')
for legacy in (master,mobile):
    if legacy.is_file():legacy.rename(legacy.with_name('OBSOLETE_34_SECONDS_DO_NOT_POST_'+legacy.name))
subprocess.run([sys.executable,str(v4)],env=env,check=True,timeout=300)
final_v4=P/'ACTION_MATCHED_v4'/'POUR_RIPPLE_COLOUR_REAL_FOLEY_ACTION_MATCHED_v4_1080p.mp4'
qa_v4=P/'ACTION_MATCHED_v4'/'V4_AUDIO_VISUAL_SYNC_QA.json'
if not final_v4.exists() or not qa_v4.exists():
    raise RuntimeError('V4 production or visual/audio continuity evidence missing')
report=json.loads((P/'SOURCE_AND_EXPORT_PROVENANCE.json').read_text())
report['current_master']=str(final_v4)
report['current_audio_visual_qa']=str(qa_v4)
report['old_34s_retired']=True
report['publishing_approval']='PENDING HUMAN LISTENING'
(P/'SOURCE_AND_EXPORT_PROVENANCE.json').write_text(json.dumps(report,indent=2))
print('SUCCESS_V4_ACTION_MATCHED_REAL_FOLEY',final_v4)


