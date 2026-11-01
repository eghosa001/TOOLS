"""Water-only, normal-speed picture bed for Crystal Garden 10-minute revision.
8 individually licensed Pexels source clips. Never publish automatically.
"""
import hashlib,json,subprocess
from pathlib import Path
R=Path('artifacts/crystal_water_recut').resolve();S=R/'sources';D=R/'scenes'
S.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
# name, Pexels video ID, page slug, actual 720p media filename, 24fps output frames, author
SCENES=[
 ('close_water','6499047','close-up-shot-of-flowing-water','6499047-hd_1280_720_24fps.mp4',2784,'Brixiv'),
 ('calm_river','5120396','calm-water','5120396-hd_1280_720_50fps.mp4',2784,'Mike Stranks'),
 ('reflections','29824263','glistening-water-reflections-with-moving-light','12809871_1280_720_30fps.mp4',792,'Sini Ko'),
 ('river_surface','5120401','flowing-water-on-the-river','5120401-hd_1280_720_50fps.mp4',2784,'Mike Stranks'),
 ('stream','7151641','flowing-water-in-a-river','7151641-hd_1280_720_30fps.mp4',1392,'I Am Sorin'),
 ('clear_falls','856895','clear-water-footage','856895-hd_1280_720_30fps.mp4',1392,'Pixabay'),
 ('waterfall','32992145','serene-waterfall-with-flowing-stream-in-forest','14061797_1280_720_30fps.mp4',1368,'Engin Akyurt'),
 ('shimmer','5909598','reflection-of-light-in-the-flowing-water','5909598-hd_1280_720_24fps.mp4',344,'Yaroslav Shuraev'),
]
assert sum(x[4] for x in SCENES)==13640
def run(*c):subprocess.run(list(map(str,c)),check=True)
def value(*c):return subprocess.check_output(list(map(str,c)),text=True).strip()
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 manifest=[];parts=[]
 for i,(name,id,slug,filename,frames,creator) in enumerate(SCENES):
  page=f'https://www.pexels.com/video/{slug}-{id}/'
  url=f'https://videos.pexels.com/video-files/{id}/{filename}'
  src=S/f'{name}.mp4';target=D/f'{i:02d}_{name}.mp4'
  if not src.exists():run('curl','-fsSL','--retry','3','--max-time','360','-A','Mozilla/5.0',url,'-o',src)
  dur=float(value('ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',src))
  if dur<frames/24+0.05:raise RuntimeError(f'{name}: actual {dur:.3f}s shorter than {frames/24:.3f}s')
  run('ffmpeg','-y','-nostdin','-hide_banner','-loglevel','error','-i',src,
      '-vf','fps=24,scale=1280:720:flags=lanczos,format=yuv420p',
      '-frames:v',str(frames),'-an','-r','24','-c:v','libx264','-preset','veryfast','-crf','21','-g','48',
      '-pix_fmt','yuv420p','-movflags','+faststart',target)
  got=int(value('ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','default=noprint_wrappers=1:nokey=1',target))
  if got!=frames:raise RuntimeError(f'{name}: rendered {got} frames instead of {frames}')
  manifest.append({'name':name,'page':page,'creator':creator,'license':'https://www.pexels.com/license/','url':url,'original_duration':dur,'trim_duration':frames/24,'frames':frames,'source_sha256':digest(src),'render_sha256':digest(target),'normal_speed':True,'visible_material':'actual water'})
  parts.append(target)
  print(f'{name}: {frames} frames from {dur:.3f}s source',flush=True)
 concat=R/'concat.txt';concat.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
 bed=R/'Crystal_Water_Stock_Bed_568s_720p.mp4'
 run('ffmpeg','-y','-nostdin','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',bed)
 got=int(value('ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','default=noprint_wrappers=1:nokey=1',bed))
 if got!=13640:raise RuntimeError(f'Bed wrong frame count {got}')
 report={'title':'Crystal Garden — water-only recut','frames':got,'fps':24,'duration_seconds':13640/24,'sources':manifest,'sha256':digest(bed),'original_flow_insertions_frames':[190,190,190,190],'planned_master_seconds':600,'rejected_paint_marbling':True,'rejected_rapid_repeats':True,'publication_approved':False,'sound_parity_review_required':True}
 (R/'PROVENANCE.json').write_text(json.dumps(report,indent=2)+'\n')
 t=R/'thumbnails';t.mkdir(exist_ok=True)
 for i,p in enumerate(parts):
  for j,fraction in enumerate((.2,.8)):
   sec=manifest[i]['trim_duration']*fraction
   run('ffmpeg','-y','-hide_banner','-loglevel','error','-ss',str(sec),'-i',p,'-frames:v','1','-vf','scale=640:-1',t/f'{i:02d}-{j}.jpg')
 print(json.dumps({'bed':str(bed),'sha256':digest(bed),'frames':got}),flush=True)
if __name__=='__main__':main()
