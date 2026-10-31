from pathlib import Path
import subprocess,zipfile,json,hashlib
ROOT=Path('/mnt/data/asmr_stock_first/final');SCENES=['embers','candle','ripples','ink']
def run(args):
 subprocess.run([str(x) for x in args],check=True)
for s in SCENES:
 src=ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_1080p.mp4'
 dst=ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_MOBILE_720p.mp4'
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',src,'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',dst])
 print('MOBILE',s,dst.stat().st_size,flush=True)
# Original 4-movement edition, 10.8 seconds each; audio fades to silence at scene boundaries.
segs=[]
for s in SCENES:
 p=ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_MOBILE_720p.mp4'
 t=ROOT/f'chapter_{s}.mp4'
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',p,'-t','10.8','-c:v','copy',
     '-af','afade=t=out:st=10.35:d=0.45','-c:a','aac','-b:a','128k','-movflags','+faststart',t])
 segs.append(t)
concat=ROOT/'chapters.txt';concat.write_text(''.join("file '"+str(x)+"'\n" for x in segs))
out=ROOT/'FOUR_TEXTURE_MOVEMENTS_43_SECONDS_MOBILE.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',out])
print('COMPILATION',out.stat().st_size,flush=True)
# Low-data preview bundle, no full HD files unless explicitly downloaded individually.
with zipfile.ZipFile(ROOT/'FOUR_ASMR_STOCK_EDIT_MOBILE_BUNDLE.zip','w',compression=zipfile.ZIP_STORED) as z:
 for s in SCENES:z.write(ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_MOBILE_720p.mp4',arcname=f'{s}_REAL_STOCK_EDIT_MOBILE.mp4')
 z.write(out,arcname=out.name)
 z.write(ROOT/'RENDER_PROVENANCE.json',arcname='RENDER_PROVENANCE.json')
print('DONE',flush=True)
