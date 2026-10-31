#!/usr/bin/env python3
"""Source acquisition, license evidence, original video inspection. No benchmark footage."""
import requests,os,re,subprocess,json,hashlib,base64
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np
D=Path(os.environ.get('ASMR_DRAGON_ROOT','/tmp/dragonfruit_asmr'));D.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36'})
page='https://www.pexels.com/video/slicing-exotic-fruits-on-wooden-cutting-board-35213988/'
sound='https://freesound.org/people/Vrymaa/sounds/807394/'
q={'video_page':page,'video_author':'Zakaria HANIF','video_license':'https://www.pexels.com/license/','foley_page':sound,'foley_author':'Vrymaa','foley_license':'https://creativecommons.org/publicdomain/zero/1.0/','approved':False,'published':False}
try:
 r=s.get(page,timeout=22);q['video_http']=r.status_code;q['video_author_in_page']='Zakaria HANIF' in r.text
except Exception as e:q['page_error']=str(e)[:300]
try:
 r=s.get(sound,timeout=22);q['foley_http']=r.status_code;h=r.text
 q['foley_cc0_in_page']=('creativecommons.org/publicdomain/zero' in h.lower() or 'creative commons 0' in h.lower())
 q['audio_page_matches']=[x.replace('\\/','/') for x in re.findall(r'[^"\s<>]{0,40}(?:807394_[0-9]+|previews/807)[^"\s<>]{0,110}',h)][:20]
except Exception as e:q['foley_error']=str(e)[:300]
v=D/'dragonfruit_original_pexels.mp4'
for url in ['https://www.pexels.com/download/video/35213988/','https://www.pexels.com/video/35213988/download/']:
 if v.exists():break
 try:
  with s.get(url,stream=True,timeout=85,headers={'Referer':page}) as r:
   r.raise_for_status()
   if 'text/html' in r.headers.get('content-type',''):raise ValueError('HTML instead of mp4')
   n=0
   with v.open('wb') as f:
    for c in r.iter_content(262144):
     if not c:continue
     n+=len(c)
     if n>140000000:raise ValueError('source exceeds cloud guard')
     f.write(c)
   with v.open('rb') as f:f.seek(4);ok=(f.read(4)==b'ftyp')
   if n<150000 or not ok:raise ValueError('not an mp4')
   q['original_video_download']=r.url
 except Exception as e:q.setdefault('video_failures',[]).append(str(e)[:250]);v.unlink(missing_ok=True)
if v.exists():
 p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(v)]))
 q['video_probe']=p;q['video_sha256']=hashlib.sha256(v.read_bytes()).hexdigest()
 cap=cv2.VideoCapture(str(v));fps=cap.get(cv2.CAP_PROP_FPS);num=cap.get(cv2.CAP_PROP_FRAME_COUNT);duration=num/fps if fps else float(p['format']['duration'])
 q.update(duration_seconds=duration,native_fps=fps,native_frames=int(num))
 sheet=Image.new('RGB',(1100,600),'#000000')
 for i,t in enumerate(np.linspace(0,max(0.1,min(29,duration)-0.3),20)):
  cap.set(cv2.CAP_PROP_POS_MSEC,float(t)*1000);ok,frame=cap.read()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));im.thumbnail((215,123))
  tile=Image.new('RGB',(220,150),'#151515');tile.paste(im,((220-im.width)//2,0));ImageDraw.Draw(tile).text((7,130),f'{t:.2f}s, f{round(t*fps)}',fill='white')
  sheet.paste(tile,((i%5)*220,(i//5)*150))
 cap.release()
 sheet.save(D/'dragonfruit_contact_sheet.jpg',quality=60,optimize=True)
 b64=base64.b64encode((D/'dragonfruit_contact_sheet.jpg').read_bytes()).decode()
 print('CONTACT_SHEET_B64_START'+b64+'CONTACT_SHEET_B64_END',flush=True)
(D/'rights_and_intake.json').write_text(json.dumps(q,indent=2,default=str))
print('SOURCE_INSPECTION_JSON_START'+json.dumps({k:v for k,v in q.items() if k!='video_probe'})+'SOURCE_INSPECTION_JSON_END',flush=True)
if not v.exists():raise SystemExit('FAILED: original licensed source download unavailable')
