"""Low-data previews only after exact encoded masters pass the ASMR audio continuity gate."""
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'satisfying_studio'/'production'))
from audio_continuity_gate import check_audio
from pathlib import Path
import subprocess,zipfile,json,hashlib
ROOT=Path('/mnt/data/asmr_stock_first/final');SCENES=['embers','candle','ripples','ink']
def run(args):
 subprocess.run([str(x) for x in args],check=True)
for s in SCENES:
 src=ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_1080p.mp4'
 dst=ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_MOBILE_720p.mp4'
 prior=src.parent/(src.stem+'_AUDIO_CONTINUITY_QA.json')
 if not prior.is_file():raise RuntimeError(f"Missing source final-audio check: {prior}")
 src_qa=json.loads(prior.read_text())
 if src_qa.get('master_sha256')!=hashlib.sha256(src.read_bytes()).hexdigest() or not src_qa.get('passed'):
  raise RuntimeError("Source master audio changed or has unacceptable gaps: "+str(src))
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',src,'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',dst])
 report=check_audio(dst)
 if not report['passed']:raise RuntimeError('Mobile ASMR audio silence: '+str(report['gaps']))
 print('MOBILE',s,dst.stat().st_size,flush=True)
# Four-movement review only; avoid the old 0.45s fade-to-silence at every scene cut.
segs=[]
for s in SCENES:
 p=ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_MOBILE_720p.mp4'
 t=ROOT/f'chapter_{s}.mp4'
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',p,'-t','10.8','-c:v','copy',
     '-af','afade=t=out:st=10.72:d=0.08','-c:a','aac','-b:a','128k','-movflags','+faststart',t])
 segs.append(t)
concat=ROOT/'chapters.txt';concat.write_text(''.join("file '"+str(x)+"'\n" for x in segs))
out=ROOT/'FOUR_TEXTURE_MOVEMENTS_43_SECONDS_MOBILE.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',out])
comp_qa=check_audio(out)
if not comp_qa['passed']:raise RuntimeError('Compilation has unwanted audio gaps: '+str(comp_qa['gaps']))
print('COMPILATION',out.stat().st_size,flush=True)
# Low-data preview bundle, no full HD files unless explicitly downloaded individually.
with zipfile.ZipFile(ROOT/'FOUR_ASMR_STOCK_EDIT_MOBILE_BUNDLE.zip','w',compression=zipfile.ZIP_STORED) as z:
 for s in SCENES:z.write(ROOT/f'{s}_REAL_FOOTAGE_ORIGINAL_EDIT_MOBILE_720p.mp4',arcname=f'{s}_REAL_STOCK_EDIT_MOBILE.mp4')
 z.write(out,arcname=out.name)
 z.write(ROOT/'RENDER_PROVENANCE.json',arcname='RENDER_PROVENANCE.json')
print('DONE',flush=True)
