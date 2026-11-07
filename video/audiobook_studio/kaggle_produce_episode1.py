#!/usr/bin/env python3
"""Produce real private Episode 1 media on Kaggle GPU from an encrypted source handoff.

Never commits plaintext, narration, or MP4 to public GitHub. This script runs
only in a private Kaggle kernel with approved Qwen Ryan and old voice archive.
"""
from __future__ import annotations
import gc, hashlib, io, json, math, os, pathlib, re, shutil, subprocess, sys, wave, zipfile

ROOT=pathlib.Path('/kaggle/working/fiction-disciple-ep01')
VOICE_ARCHIVE='AUDIOBOOK_STUDIO_QWEN_VIDEO_PIPELINE_2026-11-06.zip'
VOICE_FILES={
 'male_ryan_original_qwen_audition.mp3':'80485deabb10b8d181603ff82f55fb7b1c2e8ce3e899e077270bef1feb7c3886',
 'male_ryan_original_qwen_audition.wav':'779c5b3a6033a4483fa31d6d7b295c3b9fcddc60dbfc2007af19cfb2ca8b9bfa'
}
MODEL='Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'
INSTRUCT='A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting.'
TITLE='The Disciple Who Lost His Name'
MAX_SEC=26*60+30
MIN_SEC=24*60
TARGET_SEC=25*60

SCENE_PROMPTS=[
 (0,'rainy fantasy city ration queue, a boy holding a basket of six small loaves, uniformed official intimidating him, young dark-haired worker Kai watching, ancient eastern walled city'),
 (220,'close cinematic shot of rough workman fingers holding an examination token and torn ration slip, falling rain, crowded medieval fantasy gateway'),
 (450,'young adult workman Kai running through wet cobbled yard toward majestic Skyhold Sect on a high mountain, white tiered buildings, morning clouds'),
 (680,'severe grey-robed registrar in a small stone office facing a tense young dark-haired workman, official documents, faintly magical registration stone'),
 (900,'ancient ledger stone beside wooden desk in gloomy registrar room, a young man stunned by judgment, soft cold light'),
 (1110,'lonely young worker standing outside massive stone sect gate in rain, broken examination token, mountain monastery in mist'),
 (1340,'foreman Rusk a gruff middle aged stoneworker in a working quarry, supporting dismissed younger worker, tools and dust, late afternoon'),
 (1580,'old collapsed shrine below mountain road, young worker with lantern investigating rubble, forgotten inscriptions and moss'),
 (1820,'strange sealed stone record hidden among cracked masonry, an absent sister mystery, faint blue glow, tense fantasy atmosphere'),
 (2050,'Kai inspecting unstable masonry of old public mill and stone foundation, serious older female engineer Juna nearby'),
 (2300,'stone mill at dusk, scholar craftswoman Juna and Kai repairing dangerous structural crack, old magical channels beneath bricks'),
 (2540,'close shot of strange copper line and faint energy under a stone road, precise chisels and chalk measurements'),
 (2780,'Juna showing young worker how pressure runs through a cracked millstone, laboratory-like workshop in medieval quarry'),
 (3020,'two workers observing hidden force travelling beneath road stones, millstones, mallets and lanterns, grounded fantasy engineering'),
 (3250,'inside an old mill, tired worker Kai in rough dark clothing and experienced craftswoman Juna discuss a discovery under lamplight'),
 (3480,'dark narrow underground spillway below city retaining wall, Juna and Kai carrying lantern and tools, mossy masonry'),
 (3680,'metal tally plate discovered behind worn stone inside dangerous water channel, ominous inscriptions, Kai and Juna studying'),
 (3850,'copper coupling glowing red during magical overload, violent water pressure in a tunnel, young male worker protecting people'),
 (4020,'Skyhold wardkeepers riding through rainy road near outer city wall, woman disciple Serin in blue training coat with long staff'),
 (4180,'blue-robed disciplined young woman with staff interrupts confrontation at damaged spillway, craftspeople watching in rain'),
 (4390,'young worker Kai and woman disciple Serin in tense exchange by a breached old retaining arch, distant sect tower and rainy sky'),
 (4570,'quiet aftermath at quarry workshop, Kai and Juna studying a hidden energy ledger on long wooden table'),
 (4870,'workshop of craftswoman Juna with timber branch-like engineering apparatus, brass fittings and carved stones, Kai observing'),
 (5100,'a labyrinth of mechanical stone supports and copper channels under a quarry, young dark-haired worker learning to redirect energy'),
 (5400,'Juna and Kai inspect secret archive ledger in lamplight, mysterious blue magical residue on a metal tablet'),
 (5700,'the stone structures under city hum with hidden power, two small figures by a dark underground channel, ominous atmospheric fantasy')]
STYLE=', cinematic hand-painted dark fantasy illustration, premium detailed environment concept art, human-scale characters, consistent dark-haired Kai age 20, grounded stone engineering, teal amber palette, realistic painterly lighting, widescreen, no text no watermark no captions'


def run(args,check=True):
    return subprocess.run(args,check=check,capture_output=True,text=True)

def seconds(path):
    r=run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)])
    return float(r.stdout.strip())

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load_source():
    packed=globals().get('PRIVATE_SOURCE_ZIP')
    if not isinstance(packed,bytes):raise RuntimeError('Encrypted private manuscript handoff was not attached')
    with zipfile.ZipFile(io.BytesIO(packed)) as z:
        names=set(z.namelist())
        if names!={'story.txt','metadata.json'}:raise RuntimeError('Wrong private source fields')
        text=z.read('story.txt').decode('utf-8')
        meta=json.loads(z.read('metadata.json'))
    if meta.get('novel')!=TITLE or len(text.split())<4500:
        raise RuntimeError('Missing or wrong complete story segment')
    if sha(text.encode())!=meta.get('private_source_sha256'):
        raise RuntimeError('Manuscript SHA mismatch')
    if not text.startswith('THE DISCIPLE WHO LOST HIS NAME'):
        raise RuntimeError('Source does not begin at episode one')
    return text,meta

def load_voice():
    matches=list(pathlib.Path('/kaggle/input').rglob(VOICE_ARCHIVE))
    if len(matches)!=1:raise RuntimeError('Original PRIVATE Ryan Qwen voice archive missing')
    with zipfile.ZipFile(matches[0]) as z:
        profile=json.loads(z.read('VOICE_REFERENCE/RYAN_VOICE_STANDARD_APPROVED.json'))
        if (profile.get('model')!=MODEL or profile.get('speaker')!='Ryan'
            or profile.get('instruct')!=INSTRUCT or profile.get('language')!='English'):
            raise RuntimeError('Owner-approved narrator settings changed')
        for filename,digest in VOICE_FILES.items():
            if sha(z.read('VOICE_REFERENCE/'+filename))!=digest:
                raise RuntimeError('Ryan audition fingerprint does not match approval')
    return profile['profile_id']

def chunks(text,limit=110):
    # Every chunk ends at a sentence and can be audited against the source.
    pieces=re.split(r'(?<=[.!?])\s+(?=[“"\'‘(]?[A-Z0-9])',text.strip())
    result=[];cur=[];count=0
    for part in pieces:
        n=len(part.split())
        if not n:continue
        if n>limit:raise RuntimeError('Oversized sentence exceeds narrator limit')
        if cur and count+n>limit:
            result.append(' '.join(cur));cur=[];count=0
        cur.append(part.strip());count+=n
    if cur:result.append(' '.join(cur))
    if len(result)<30:raise RuntimeError('Narration script abnormally short')
    return result

def narration(text):
    import numpy as np, soundfile as sf, torch
    from qwen_tts import Qwen3TTSModel
    if not torch.cuda.is_available():raise RuntimeError('Real approved Ryan voice requires Kaggle GPU')
    dtype=torch.bfloat16 if torch.cuda.get_device_capability(0)[0]>=8 else torch.float32
    model=Qwen3TTSModel.from_pretrained(MODEL,device_map='cuda:0',dtype=dtype,attn_implementation='sdpa')
    texts=chunks(text);out=ROOT/'audio_chunks';out.mkdir(parents=True,exist_ok=True)
    records=[];total=0.;cumulative_words=0;last=None
    for i,part in enumerate(texts):
        wavfile=out/(f'{i:04}.wav')
        if not wavfile.is_file():
            generated,rate=model.generate_custom_voice(text=part,speaker='Ryan',language='English',instruct=INSTRUCT)
            arr=np.asarray(generated[0]);
            if arr.size<rate//4 or not np.isfinite(arr).all():
                raise RuntimeError(f'Qwen audio invalid in segment {i}')
            sf.write(str(wavfile),arr,rate,subtype='PCM_16')
        duration=seconds(wavfile)
        cumulative_words+=len(part.split());total+=duration
        records.append(dict(i=i,words=len(part.split()),ending_word=cumulative_words,
                            duration_s=round(duration,3),total_s=round(total,3),
                            text_sha256=sha(part.encode())))
        print('REAL_RYAN_SEGMENT',i,'seconds',round(total,1),'spoken_words',cumulative_words,flush=True)
        # Natural sentence-group boundary, no filler or artificial speed changes.
        if total>=TARGET_SEC-18:
            last=i;break
    del model;gc.collect();torch.cuda.empty_cache()
    if total<MIN_SEC or total>MAX_SEC:
        raise RuntimeError('Actual Qwen audio duration outside 24-26.5min; never pad with silence')
    (ROOT/'timeline.json').write_text(json.dumps(records,indent=2))
    concat=ROOT/'audio_concat.txt'
    concat.write_text(''.join('file '+repr(str((out/(f"{r["i"]:04}.wav")).resolve()))+'\n' for r in records))
    dest=ROOT/'episode1_male_ryan_actual_narration.m4a'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),
         '-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k',str(dest)])
    return dest,records

def procedural_art(index,description,out):
    # Original visual fallback only when licensed image model cannot be loaded.
    # Never pretend this fallback has passed cinematic illustration review.
    from PIL import Image,ImageDraw,ImageFont,ImageFilter
    import numpy as np,random
    w,h=1536,864;rng=random.Random(340+index)
    image=Image.new('RGB',(w,h),(12,25,34));d=ImageDraw.Draw(image)
    for layer in range(6):
        base_y=int(h*.4+layer*62)
        points=[(0,h),(0,base_y)]
        for x in range(0,w+120,75):points.append((x,base_y+rng.randint(-100,100)))
        points.append((w,h))
        d.polygon(points,fill=(16+layer*5,33+layer*5,40+layer*6))
    d.polygon([(1100,165),(1330,165),(1360,620),(1040,620)],fill=(23,38,45))
    for j in range(4):
        y=170+j*98
        d.polygon([(1050,y+40),(1380,y+40),(1340,y),(1090,y)],fill=(49+j*4,67+j*4,68+j*3))
    for j in range(40):
        x,y=rng.randrange(w),rng.randrange(h)
        d.ellipse((x,y,x+3,y+3),fill=(140,144,123))
    d.ellipse((1140,480,1190,535),fill=(8,16,21))
    d.polygon([(1130,540),(1210,540),(1250,h),(1090,h)],fill=(10,19,26))
    # Different visual motifs by event — no unrelated generic stock assets.
    if any(x in description for x in ('tally','ledger','token','slip')):
        d.polygon([(650,420),(900,390),(940,660),(690,680)],fill=(149,119,79))
        for j in range(5):d.line((705,462+j*38,908,450+j*38),fill=(64,58,49),width=3)
    image=image.filter(ImageFilter.GaussianBlur(0.4))
    image.save(out)

def pictures(total_words):
    images=ROOT/'images';images.mkdir(exist_ok=True)
    selected=[(word,prompt) for word,prompt in SCENE_PROMPTS if word<total_words]
    if len(selected)<8:raise RuntimeError('Insufficient actual source-linked story scenes')
    generated=[];kind='procedural_fallback'
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
        pipe=AutoPipelineForText2Image.from_pretrained('stabilityai/sdxl-turbo',torch_dtype=torch.float16,variant='fp16')
        pipe.to('cuda')
        kind='SDXL Turbo painterly illustrations'
        for j,(word,prompt) in enumerate(selected):
            target=images/(f'{j:03}.png')
            if not target.is_file():
                g=torch.Generator(device='cuda').manual_seed(7129+j*79)
                im=pipe(prompt+STYLE,generate_kwargs={} if False else None) if False else pipe(
                    prompt+STYLE,num_inference_steps=3,guidance_scale=0.0,
                    height=576,width=1024,generator=g).images[0]
                im.save(target)
            generated.append((word,target))
        del pipe;gc.collect();torch.cuda.empty_cache()
    except Exception as ex:
        print('ILLUSTRATION_MODEL_FAILED_USING_EXPLICIT_FALLBACK',type(ex).__name__,flush=True)
        for j,(word,prompt) in enumerate(selected):
            target=images/(f'{j:03}.png')
            if not target.is_file():procedural_art(j,prompt,target)
            generated.append((word,target))
    return generated,kind

def video(narration_file,records,illustrations):
    total_words=records[-1]['ending_word'];speech_seconds=seconds(narration_file)
    # Interpolate time by *actual narration segment* lengths, not a fixed WPM.
    def word_time(pos):
        previous_s=0.;previous_words=0
        for entry in records:
            if pos<=entry['ending_word']:
                delta=entry['ending_word']-previous_words
                return previous_s+(pos-previous_words)/max(delta,1)*entry['duration_s']
            previous_s=entry['total_s'];previous_words=entry['ending_word']
        return speech_seconds
    timeline=[]
    for i,(word,image) in enumerate(illustrations):
        start=word_time(word)
        end=word_time(illustrations[i+1][0]) if i+1<len(illustrations) else speech_seconds
        if end-start>=0.5:timeline.append((image,start,end))
    listfile=ROOT/'scene_concat.txt';lines=[]
    for image,start,end in timeline:
        lines.append("file '"+str(image.resolve())+"'")
        lines.append('duration %.6f'%(end-start))
    lines.append("file '"+str(timeline[-1][0].resolve())+"'")
    listfile.write_text('\n'.join(lines)+'\n')
    path=ROOT/'THE_DISCIPLE_WHO_LOST_HIS_NAME_EP01_REVIEW.mp4'
    # 1080p, 24fps. Long-format images are not used as a substitute for speech.
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listfile),
         '-i',str(narration_file),'-vf','scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,format=yuv420p',
         '-c:v','libx264','-preset','veryfast','-crf','22','-c:a','copy','-movflags','+faststart','-t',str(speech_seconds),str(path)])
    return path,len(timeline)

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    text,meta=load_source();voice_id=load_voice()
    print('PRIVATE_SOURCE_VERIFIED',{'novel':TITLE,'episode':1,'available_words':len(text.split()),'voice_profile_verified':True},flush=True)
    subprocess.run([sys.executable,'-m','pip','install','-q','qwen-tts','accelerate','soundfile','diffusers','transformers','safetensors','pillow'],check=True)
    audio,records=narration(text)
    selected_words=records[-1]['ending_word']
    images,kind=pictures(selected_words)
    movie,scene_count=video(audio,records,images)
    report={'book':TITLE,'episode':1,'actual_minutes':round(seconds(movie)/60,2),
            'audio_minutes':round(seconds(audio)/60,2),'spoken_source_words':selected_words,
            'narrator':'Qwen Ryan original approved','voice_profile':voice_id,
            'images':scene_count,'visual_engine':kind,'source_sha256':meta['private_source_sha256'],
            'mp4_sha256':sha(movie.read_bytes()),'file_name':movie.name,
            'real_video_generated':True,'owner_listening_reviewed':False,'publicly_published':False}
    (ROOT/'EPISODE1_RUN_REPORT.json').write_text(json.dumps(report,indent=2))
    print('EPISODE1_GENERATED_REPORT',json.dumps(report),flush=True)

if __name__=='__main__':main()