#!/usr/bin/env python3
"""Join five separately rendered 3D fruit ASMR cuts into 30-second continuous stereo Short.
No imported benchmark footage; each clip's provenance is recorded. No scene looping.
"""
import os,sys,json,subprocess,hashlib,shutil
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw

OUT=Path(os.environ.get('FRUIT_FINISHED_DIR','/mnt/data/multifruit_studio/final'));OUT.mkdir(parents=True,exist_ok=True)
root=Path(os.environ.get('FRUIT_SEGMENT_DIR','/mnt/data/multifruit_studio/segments'))
# Lead with the approved mango visual; four independent original 3D fruits follow.
order=['mango','strawberry','citrus','dragonfruit','fig']
paths=[]
for fruit in order:
 if fruit=='mango':p=Path(os.environ.get('FRUIT_MANGO_CLIP','/mnt/data/mango_edit/Glossy_Mango_Organic_ShellBreak_v3_720p_PRIVATE_REVIEW.mp4'))
 else:p=root/fruit/f'{fruit}_3D_candy_break_720p_review.mp4'
 if not p.is_file():raise SystemExit(f'Missing real independently rendered scene: {fruit}: {p}')
 paths.append(p)

def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
for fruit,p in zip(order,paths):
 q=probe(p);v=next(x for x in q['streams'] if x['codec_type']=='video');a=next(x for x in q['streams'] if x['codec_type']=='audio')
 assert int(v['width'])==720 and int(v['height'])==1280,(fruit,'resolution')
 assert v['r_frame_rate']=='24/1',(fruit,'fps')
 assert int(a['sample_rate'])==48000 and int(a['channels'])==2,(fruit,'audio')
 assert float(q['format']['duration'])>=5.9,(fruit,'short')
 print('VERIFIED_INPUT',fruit,p.stat().st_size,flush=True)

# Exact six-second video and audio per fruit. 40ms audio cross-boundary fade prevents clicks.
filters=[]
for i in range(len(paths)):
 filters.append(f'[{i}:v]trim=duration=6,fps=24,scale=720:1280,setsar=1,setpts=PTS-STARTPTS,format=yuv420p[v{i}]')
 filters.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration=6,apad=pad_dur=0.10,atrim=duration=6,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.035,afade=t=out:st=5.965:d=0.035[a{i}]')
filters.append(''.join(f'[v{i}][a{i}]' for i in range(len(paths)))+'concat=n=5:v=1:a=1[v][a]')

movie=OUT/'Five_Fruits_30s_3D_Crunch_ASMR_720p_PRIVATE_REVIEW.mp4'
args=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y']
for p in paths:args+=['-i',str(p)]
args+=['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','24','-c:a','aac','-b:a','224k','-ar','48000','-ac','2','-t','30','-movflags','+faststart',str(movie)]
print('RENDER_30_SEC',flush=True)
subprocess.run(args,check=True)
mobile=OUT/'Five_Fruits_30s_3D_Crunch_ASMR_540p_LOW_DATA.mp4'
subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(movie),'-vf','scale=540:960:flags=lanczos','-c:v','libx264','-preset','fast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(mobile)],check=True)

def verify_movie(p,expected_size):
 q=probe(p);v=next(x for x in q['streams'] if x['codec_type']=='video');a=next(x for x in q['streams'] if x['codec_type']=='audio')
 assert (int(v['width']),int(v['height']))==expected_size
 assert v['r_frame_rate']=='24/1';assert int(a['sample_rate'])==48000 and int(a['channels'])==2
 cap=cv2.VideoCapture(str(p));last=None;black=[];streak=0;maxstreak=0;count=0
 frames=[];review_indices={1,48,61,85,144,145,192,205,229,288,289,336,349,373,432,433,480,493,517,576,577,624,637,661,720}
 while True:
  ok,b=cap.read()
  if not ok:break
  count+=1
  if b.mean()<6.5:black.append(count)
  if last is not None:
   delta=float(np.abs(b.astype(np.int16)-last.astype(np.int16)).mean());streak=streak+1 if delta<.09 else 0;maxstreak=max(maxstreak,streak)
  last=b
  if count in review_indices:
   im=Image.fromarray(cv2.cvtColor(b,cv2.COLOR_BGR2RGB));im.thumbnail((120,214));frames.append((count,im))
 cap.release()
 assert count==720,('Unexpected frame count',count)
 assert not black,black
 assert maxstreak<19,('extended frozen picture',maxstreak)
 # Extract 20 ms RMS audio: no 0.45-second muted intervals at threshold -55 dBFS.
 raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(p),'-vn','-f','f32le','-ar','48000','-ac','2','pipe:1'])
 samples=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
 levels=np.array([np.sqrt(np.mean(samples[i:i+960].astype(np.float64)**2)) for i in range(0,len(samples),960)])
 quiet=levels<10**(-55/20)
 cur=0;maxquiet=0
 for x in quiet:
  cur=cur+1 if x else 0;maxquiet=max(maxquiet,cur)
 assert maxquiet*0.02<0.45,('Unexpected prolonged audio silence',maxquiet*0.02)
 report={'path':str(p),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'width':int(v['width']),'height':int(v['height']),'fps':24,'video_frames':count,'audio_sample_rate':48000,'audio_channels':2,'video_duration_s':float(q['format']['duration']),'longest_still_frame_run':maxstreak,'black_frames':len(black),'longest_quiet_audio_window_s':round(maxquiet*.02,3),'fruit_order':order,'five_separately_rendered_real_cgi_scenes':True,'separately_verified_cc0_freesound_foley':True,'artistic_approval':False,'publication_approved':False}
 return report,frames
rep,frames=verify_movie(movie,(720,1280));low,_=verify_movie(mobile,(540,960))
contact=Image.new('RGB',(5*120,5*240),(15,15,17));draw=ImageDraw.Draw(contact)
for k,(f,im) in enumerate(frames[:25]):
 x=(k%5)*120;y=(k//5)*240
 contact.paste(im,(x,y));fruit=order[min((f-1)//144,len(order)-1)]
 draw.text((x+4,y+215),f'{f/24:.2f}s {fruit}',fill=(240,240,240))
contact.save(OUT/'Five_Fruits_30s_25_FRAME_AV_REVIEW.jpg',quality=82)
release={'master':rep,'mobile':low,'source_provenance':'Independent user-owned Blender 3D source frames; new 4 candy fruit variants plus older original mango; CC0 Freesound and Poly Haven HDRI. No user reference footage or audio.','note':'No premium quality or human headphone review has been certified; 24 fps from motion-interpolated 8 fps original 540p Blender frames in new scenes.','audio_sync_target_global_frames':{f: [i*144+61,i*144+85] for i,f in enumerate(order)}}
(OUT/'FIVE_FRUITS_30s_SOURCE_AUDIO_FRAME_QA.json').write_text(json.dumps(release,indent=2))
print('DONE_30S',json.dumps({'main_size':movie.stat().st_size,'mobile_size':mobile.stat().st_size,'frames':rep['video_frames'],'max_quiet_s':rep['longest_quiet_audio_window_s']},indent=2))
