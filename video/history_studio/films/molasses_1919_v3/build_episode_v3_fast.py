#!/usr/bin/env python3
"""Fast archival-first Episode 01: retains the mastered Kokoro narration/audio from v2.
No AI model downloads, no torch, and no rerendering narration.
"""
import argparse,hashlib,json,re,subprocess,importlib.util,os
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('archival_v3',HERE/'build_episode_v3.py')
v3=importlib.util.module_from_spec(spec);spec.loader.exec_module(v3)
v1=v3.v1
OUT=v3.OUT
def sh(args):
 print('VIDEO_COMMAND',str(args)[:220],flush=True)
 subprocess.run([str(x) for x in args],check=True,timeout=1500)
def scan(src):
 raw=src.read_text(encoding='utf8')
 blocks=re.split(r'\n\s*\n',raw.strip())
 cues=[]
 for block in blocks:
  ls=block.splitlines()
  at=next((i for i,x in enumerate(ls) if ' --> ' in x),None)
  if at is None:continue
  a,b=ls[at].split(' --> ')
  def sec(s):
   h,m,x=s.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(x)
  text=' '.join(ls[at+1:]).strip()
  cues.append((sec(a),sec(b),text))
 return cues
def segments(cues,total):
 # Subtitle word groups were generated directly from the original story script.
 # Their first timestamps are precisely the start times for each narrated scene.
 cursor=0;frames=[0.]
 for scene in v3.DATA['scenes'][:-1]:
  needed=len(scene['narration'].split());got=0
  while got<needed:
   if cursor>=len(cues):raise RuntimeError('Subtitles do not match historical script')
   got+=len(cues[cursor][2].split());cursor+=1
  if got!=needed:raise RuntimeError('Caption words differ from story script')
  frames.append(cues[cursor][0])
 frames.append(total)
 durations=[frames[i+1]-frames[i] for i in range(22)]
 if len(durations)!=22 or not all(8<x<130 for x in durations):raise RuntimeError('Invalid scene boundaries')
 print('REUSE_FINISHED_KOKORO_NARRATION',len(durations),'chapters',round(sum(durations)/60,2),'min',flush=True)
 return frames,durations
def image_render(image,audio,start,duration,out,seed):
 # Reuses proven FFmpeg Ken Burns camera engine from v3.
 v3.render_segment_image(image,audio,start,duration,out,seed)
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--master',required=True,type=Path)
 ap.add_argument('--captions',required=True,type=Path)
 args=ap.parse_args()
 assert args.master.exists() and args.captions.exists()
 original=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(args.master)]))['format']['duration'])
 cues=scan(args.captions)
 frames,durations=segments(cues,original)
 images,movie=v3.pull_sources()
 plates=OUT/'plates';plates.mkdir(exist_ok=True)
 clips=OUT/'clips';clips.mkdir(exist_ok=True)
 v3.thumbnail(images)
 score=OUT/'complete_v2_soundtrack.wav'
 if not score.exists():sh(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',args.master,'-vn','-ar','48000','-ac','1','-c:a','pcm_s16le',score])
 intro_len=9.
 intro=plates/'intro.jpg'
 v3.intro_plate(intro,images['panorama'])
 intro_clip=clips/'intro.mp4'
 if not intro_clip.exists():sh(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','24','-i',intro,'-f','lavfi','-i','anullsrc=channel_layout=mono:sample_rate=48000','-t',str(intro_len),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',intro_clip])
 pathlist=[intro_clip]
 overlay=plates/'period_1903.png'
 if movie:v3.movie_plate(overlay)
 for i,keys in enumerate(v3.STORYBOARD):
  span=durations[i];offset=frames[i]
  for k,key in enumerate(keys):
   partial=span/3 if k<2 else span/3
   path=clips/f'{i+1:02d}_{k}.mp4'
   if not path.exists():
    if i in v3.FILM_SCENES and k==0 and movie:
     v3.render_segment_movie(movie,overlay,score,offset+k*span/3,partial,path,start=30+i*11)
    else:
     plate=plates/f'{i+1:02d}_{k}.jpg'
     v3.archive_plate(images[key],v3.DATA['scenes'][i],i,key,variant=k).save(plate,quality=90)
     image_render(plate,score,offset+k*span/3,partial,path,seed=i+k)
   pathlist.append(path)
  print('ARCHIVAL_SCENE',i+1,'of',len(v3.STORYBOARD),flush=True)
 concat=OUT/'concat_fast.txt'
 concat.write_text('\n'.join("file '"+str(p.resolve()).replace("'","'\\''")+"'" for p in pathlist)+'\n')
 result=OUT/'Great_Molasses_Flood_1919_v3.mp4'
 sh(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',result])
 new_cues=[(0,intro_len,'Please subscribe to FACTS UNCOVERED. Tap the Subscribe button below.')] + [(intro_len+a,intro_len+b,text) for a,b,text in cues]
 def srt(t):
  h=int(t//3600);m=int(t%3600//60);sec=int(t%60);ms=round((t-int(t))*1000)
  if ms==1000:ms=999
  return f'{h:02d}:{m:02d}:{sec:02d},{ms:03d}'
 (OUT/'subtitles.srt').write_text('\n\n'.join(f'{i}\n{srt(a)} --> {srt(b)}\n{t}' for i,(a,b,t) in enumerate(new_cues,1))+'\n',encoding='utf8')
 entries=v3.DATA['archival_images']
 provenance={'version':3,'channel':v3.CHANNEL,'narrator':'UNCHANGED: same actual 13m47s finished Kokoro am_michael soundtrack from Episode 01 v2, not re-synthesized','opening_subscribe':'On-screen Subscribe message and downward arrow (silent; main original narrator retained intact)','archival_first':True,'ai_reconstruction_count':0,'historically_contextual_film':v3.FILM if movie else None,'shot_source_keys':[list(x) for x in v3.STORYBOARD],'original_photo_sources':[x for x in entries if x['id'] in images],'additional_original_photo_sources':[{**x,'id':k} for k,x in v3.EXTRA.items() if k in images],'authentic_1919_image_count':len(images),'movie_minutes':round(original/60+intro_len/60,3),'sources_sha256':{k:v3.digest(p) for k,p in images.items()},'editorial_review':'REQUIRED before YouTube release'}
 (OUT/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
 (OUT/'SHOT_SOURCES.json').write_text(json.dumps([{'scene':i+1,'photo_ids':list(keys),'period_footage':i in v3.FILM_SCENES} for i,keys in enumerate(v3.STORYBOARD)],indent=2))
 (OUT/'YOUTUBE_DESCRIPTION.txt').write_text('Facts Uncovered: Stories & Evidence — The Great Molasses Flood of 1919. Please subscribe to the channel. Photos are authentic period archive materials. 1903 Boston period footage (if present) is labelled as context, not the 1919 event. See PROVENANCE.json for credits.\n')
 (OUT/'EPISODE_SCRIPT.txt').write_text('FACTS UNCOVERED — SUBSCRIBE OPENING (on screen): Tap the Subscribe button below.\n\n'+'\n\n'.join(x['narration'] for x in v3.DATA['scenes']))
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(result)]))
 length=float(info['format']['duration'])
 assert 750<length<950 and result.stat().st_size>5_000_000
 assert any(s['codec_type']=='video' and s.get('width')==1920 and s.get('height')==1080 for s in info['streams'])
 assert any(s['codec_type']=='audio' for s in info['streams'])
 assert len(pathlist)==67
 print('EPISODE01_V3_FAST_VERIFIED',round(length/60,2),'minutes',round(result.stat().st_size/1048576,2),'MiB','archive_images',len(images),'actual_period_footage',bool(movie),flush=True)
if __name__=='__main__':main()
