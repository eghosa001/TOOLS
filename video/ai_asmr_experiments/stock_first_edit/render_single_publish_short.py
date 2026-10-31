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

# The original eight graded visual segments are ready. V5 is the only production mix.
# Old V3/V4 stages contained continuous drops or silent audio. Do not produce them.
import sys
final_script=pathlib.Path(__file__).with_name('render_action_matched_v5.py')
if not final_script.is_file():raise RuntimeError('Mandatory frame-synced V5 editor missing')
if 'ASMR_REAL_FOLEY_ZIP' not in os.environ:raise RuntimeError('ASMR_REAL_FOLEY_ZIP not configured: use verified Mixkit audio cache')
env=os.environ.copy()
env['ASMR_PUBLISH_DIR']=str(P)
fresh_pic=P/'ACTION_MATCHED_v5'/'SHORT_PICTURE_ONLY.mp4'
fresh_pic.parent.mkdir(parents=True,exist_ok=True)
# Avoid stale picture artefacts when the input footage or in/out points change.
fresh_pic.unlink(missing_ok=True)
env['ASMR_VIDEO_SOURCE']=str(fresh_pic)
subprocess.run([sys.executable,str(final_script)],env=env,check=True,timeout=540)
deliver=P/'ACTION_MATCHED_v5'/'POUR_RIPPLE_COLOUR_ASMR_V5_FRAME_SYNC_1080p.mp4'
qa=P/'ACTION_MATCHED_v5'/'V5_FRAME_MATCH_AUDIO_QA.json'
if not deliver.is_file() or not qa.is_file():raise RuntimeError('V5 master or audio-visual sync evidence missing')
verified=json.loads(qa.read_text())
if verified.get('status')!='RENDERED_TECHNICALLY_VERIFIED_PENDING_HUMAN_LISTENING':
    raise RuntimeError('Unexpected V5 QC status')
print('SUCCESS_ASMR_V5_FRAME_VERIFIED_PENDING_HUMAN_APPROVAL',str(deliver))
