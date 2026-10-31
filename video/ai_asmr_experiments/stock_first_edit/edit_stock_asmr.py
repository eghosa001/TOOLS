#!/usr/bin/env python3
"""Substantial original stock+Foley ASMR edits; combines only rights-logged licensed footage."""
from __future__ import annotations
import hashlib,json,subprocess,zipfile,os,sys,math,shutil
from pathlib import Path

ROOT=Path(os.environ.get('ASMR_STOCK_ROOT','/mnt/data/asmr_stock_first'));STOCK=ROOT/'stock';OUT=ROOT/'final';SEG=ROOT/'segments'
OUT.mkdir(exist_ok=True,parents=True);SEG.mkdir(exist_ok=True,parents=True)
SOUNDS=Path(os.environ.get('ASMR_SFX_ZIP','/mnt/data/four_asmr_real_foley_generated.zip'))
FPS=24;W=1080;H=1920;DUR=18.0;SHOT=3.6

def require_no_silent_gaps(master):
    """Fail closed on the exact exported AAC, not the candidate source WAV."""
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'satisfying_studio'/'production'))
    from audio_continuity_gate import check_audio
    report=check_audio(master)
    report["master_sha256"]=hashlib.sha256(master.read_bytes()).hexdigest()
    report["human_frame_sync_approved"]=False
    report["scope"]="Technical silence floor only; separate material/contact/force audition mandatory"
    (master.parent/(master.stem+'_AUDIO_CONTINUITY_QA.json')).write_text(json.dumps(report,indent=2))
    if not report["passed"]:
        raise RuntimeError("UNAPPROVED ASMR silence in final encoded audio: "+str(report["gaps"]))
    return report
SETTINGS={
 'embers':dict(choices=['fire','coal'],name='EMBER STUDY',caption='FIRE / CRACKLE',target=-23,eq='eq=contrast=1.07:saturation=1.10:brightness=-0.008'),
 'candle':dict(choices=['candle','candles'],name='FLAME STUDY',caption='STILL / FLICKER',target=-38,eq='eq=contrast=1.05:saturation=1.05:brightness=-0.012'),
 'ripples':dict(choices=['jets','ripple'],name='SURFACE STUDY',caption='DROP / RIPPLE',target=-27,eq='eq=contrast=1.04:saturation=1.06:brightness=0.0'),
 'ink':dict(choices=['ink','inkmono'],name='PIGMENT STUDY',caption='COLOUR / FLOW',target=-35,eq='eq=contrast=1.04:saturation=1.13:brightness=-0.005')
}

def run(args):
    subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

def probe(path):
    x=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate','-of','json',str(path)],capture_output=True,text=True,check=True)
    return json.loads(x.stdout)

def wav_audio():
    with zipfile.ZipFile(SOUNDS) as z:
        for n in SETTINGS:
            member=n+'_REAL_SFX_20s.wav'
            if member not in z.namelist():raise RuntimeError('Missing generated original audio '+member)
            dest=ROOT/member
            if not dest.exists():
                with z.open(member) as src,open(dest,'wb') as dst:shutil.copyfileobj(src,dst)

def segments(scene,assets):
    cfg=SETTINGS[scene]
    choices=[name for name in cfg['choices'] if name in assets and (STOCK/(name+'.mp4')).exists()]
    if not choices:return None
    clips=[]
    # An editorial structure, not a continuous stock replay: alternating sources, five deliberately
    # distinct temporal extracts, measured reframes, tonal continuity and short opening typography.
    for j in range(5):
        name=choices[j%len(choices)];source=STOCK/(name+'.mp4')
        inf=probe(source);length=float(inf['format']['duration'])
        if length<3.9:raise RuntimeError(f'{name}: source too short for honest temporal shots: {length}')
        available=max(0,length-SHOT-.1)
        pos=round(available*([.02,.38,.69,.23,.86][j]),2)
        pan=[.50,.18,.78,.62,.30][j]
        zoom=[1.0,1.075,1.032,1.11,1.0][j]
        sw=round(W*zoom/2)*2;sh=round(H*zoom/2)*2
        # Width may be much greater than frame; composition is always crop-centred on action.
        visual=(f'scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,'
                f'crop={W}:{H}:x=(iw-{W})*{pan}:y=(ih-{H})*0.50,'
                f'{cfg["eq"]},unsharp=5:5:0.38:3:3:0.0,format=yuv420p')
        if j==0:
            title=cfg['name'].replace("'",'')
            # Brief authored graphic and restrained line treatment; invisible after the first second.
            visual+=(f",drawbox=x=54:y=159:h=2:w=220:color=white@0.48:t=fill:enable='lt(t,1.5)'"
                     f",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{title}':"
                     f"fontcolor=white@0.90:fontsize=30:x=54:y=108:enable='lt(t,1.5)'")
        fname=SEG/f'{scene}_{j:02d}_{name}.mp4'
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(pos),'-i',str(source),
             '-t',str(SHOT),'-vf',visual,'-an','-r',str(FPS),'-frames:v',str(int(SHOT*FPS)),
             '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',
             '-profile:v','high','-level','4.2','-video_track_timescale','12288','-movflags','+faststart',str(fname)]
        run(cmd)
        clips.append((fname,name,pos,j,pan,zoom))
        print('SHOT',scene,j,name,'source=',pos,'sec','zoom=',zoom,flush=True)
    return clips

def render(scene,assets):
    shots=segments(scene,assets)
    if not shots:return {'status':'SKIPPED_NO_VERIFIED_STOCK'}
    manifest=SEG/f'{scene}_concat.txt'
    manifest.write_text('\n'.join("file '"+str(f)+"'" for f,*_ in shots)+'\n')
    picture=SEG/f'{scene}_picture.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(manifest),
         '-c:v','copy','-an','-movflags','+faststart',str(picture)])
    cfg=SETTINGS[scene]
    output=OUT/f'{scene}_REAL_FOOTAGE_ORIGINAL_EDIT_1080p.mp4'
    sound=ROOT/f'{scene}_REAL_SFX_20s.wav'
    audiofx=f'atrim=0:{DUR},asetpts=N/SR/TB,highpass=f=30,loudnorm=I={cfg["target"]}:TP=-3.0:LRA=11,afade=t=in:st=0:d=0.10,afade=t=out:st=17.90:d=0.10'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(picture),'-i',str(sound),
         '-map','0:v:0','-map','1:a:0','-c:v','copy','-af',audiofx,'-c:a','aac','-b:a','160k',
         '-ar','48000','-ac','2','-t',str(DUR),'-movflags','+faststart',str(output)])
    audio_qa=require_no_silent_gaps(output)
    status=probe(output);v=next(s for s in status['streams'] if s['codec_type']=='video')
    a=next(s for s in status['streams'] if s['codec_type']=='audio')
    assert v['width']==W and v['height']==H
    assert 17.8<float(status['format']['duration'])<18.4
    return {'status':'RENDERED_UNREVIEWED','file':output.name,'bytes':output.stat().st_size,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'duration':status['format']['duration'],'frame':f'{W}x{H}',
            'source_shots':[{'asset':name,'source_start_seconds':pos,'pan':pan,'scale':zoom} for _,name,pos,_,pan,zoom in shots],
            'sound':sound.name,'sound_model':'Stable Audio 3 Small-SFX, NOT Qwen3-TTS',
            'audio_continuity_report':output.stem+'_AUDIO_CONTINUITY_QA.json',
            'audio_continuity_passed':audio_qa['passed'],
            'audible_frame_contact_sync_approved':False}

def main():
    ledger=json.loads((STOCK/'SOURCE_LICENSES.json').read_text());wav_audio()
    sources={a['name']:a for a in ledger['assets'] if (STOCK/(a['name']+'.mp4')).exists()}
    reports={'license_manifest':'SOURCE_LICENSES.json','source_assets':sources,'outputs':{},
             'editing':'Original five-shot temporal recut per scene; reframing, motion/tonal consistency, restrained authored titles, natural 20s sound cues mixed with fades',
             'published':False,'human_listening_approved':False,
             'monetization_note':'Even substantively edited licensed footage needs manual originality review before monetized publishing.'}
    for scene in SETTINGS:
        try:reports['outputs'][scene]=render(scene,sources)
        except Exception as e:reports['outputs'][scene]={'status':'ERROR','error':str(e)};print('ERROR',scene,str(e),flush=True)
    (OUT/'RENDER_PROVENANCE.json').write_text(json.dumps(reports,indent=2))
    for scene in SETTINGS:
        if reports['outputs'][scene]['status']!='RENDERED_UNREVIEWED':print('INCOMPLETE',scene,reports['outputs'][scene]);
    if any(reports['outputs'][scene]['status'] != 'RENDERED_UNREVIEWED' for scene in SETTINGS):
        raise RuntimeError("No delivery bundle: at least one shot failed silence/rights/encode checks")
    with zipfile.ZipFile(OUT/'REAL_STOCK_ASMR_SUBSTANTIVE_EDITS.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=2) as z:
        for f in OUT.glob('*'):
            if f.suffix in ('.json','.mp4'):z.write(f,arcname=f.name)
    print('PRODUCTION SUMMARY',json.dumps({k:v['status'] for k,v in reports['outputs'].items()}),flush=True)
if __name__=='__main__':main()
