"""Resume Eternal Dao D03 Episode 1 from the already uploaded private Kaggle source."""
import base64, json, os, pathlib, re, subprocess, sys, tempfile, time, types

STORY='eternal-dao-of-the-lost-epoch'
DATASET_SLUG='eternal-dao-d03-approved-private-manuscript'
KERNEL_SLUG='manhua-eternal-dao-d03-ep01-private'

def main():
    token=os.environ.get('KAGGLE_API_TOKEN','')
    owner=os.environ.get('KAGGLE_USERNAME','aighewieghosa')
    if len(token)<24 or not re.fullmatch(r'[A-Za-z0-9_-]+',owner):
        raise RuntimeError('Kaggle authorization missing')
    ref=owner+'/'+DATASET_SLUG
    ok=False
    for attempt in range(20):
        p=subprocess.run(['kaggle','datasets','files',ref,'--csv'],capture_output=True,text=True,timeout=70)
        if p.returncode==0 and 'manifest.json' in p.stdout and 'episodes/ep001.txt' in p.stdout:
            ok=True
            break
        if attempt<19:time.sleep(12)
    if not ok:
        raise RuntimeError('Private Kaggle dataset not ready; no GPU submission')
    print('ETERNAL_DAO_PRIVATE_SOURCE_READY',json.dumps({'dataset':ref,'required_package':True}),flush=True)
    with tempfile.TemporaryDirectory(prefix='private-eternal-dao-assets-') as tmp:
        stage=pathlib.Path(tmp)
        runner='import base64,sys,types,subprocess\n'
        for name in ('video','video.audiobook_studio','video.audiobook_studio.manhua_pipeline'):
            runner+='m=types.ModuleType('+repr(name)+');m.__path__=[];sys.modules['+repr(name)+']=m\n'
        srcs={
            'video.audiobook_studio.episode_fastlane':'video/audiobook_studio/episode_fastlane.py',
            'video.audiobook_studio.manhua_pipeline.visual_quality':'video/audiobook_studio/manhua_pipeline/visual_quality.py',
            'video.audiobook_studio.manhua_pipeline.core':'video/audiobook_studio/manhua_pipeline/core.py',
            'video.audiobook_studio.manhua_pipeline.kaggle_runner':'video/audiobook_studio/manhua_pipeline/kaggle_runner.py',
        }
        for name,path in srcs.items():
            payload=base64.b64encode(pathlib.Path(path).read_bytes()).decode()
            runner+=(f'm=types.ModuleType({name!r});m.__package__={name.rpartition(".")[0]!r};'
                     f'sys.modules[{name!r}]=m;'
                     f'exec(compile(base64.b64decode({payload!r}),{path!r},"exec"),m.__dict__)\n')
        runner+="\nimport os,pathlib,zipfile,hashlib,json\nmanifests=list(pathlib.Path('/kaggle/input').rglob('manifest.json'))\nif len(manifests)!=1: raise RuntimeError('Expected one private D03 manifest')\nroot=manifests[0].parent\nraw_manifest=manifests[0].read_bytes()\nmeta=json.loads(raw_manifest)\nif meta.get('story_id')!='eternal-dao-of-the-lost-epoch' or len(meta.get('episodes',[]))!=17: raise RuntimeError('Wrong novel source')\nfiles={}\nfor entry in meta['episodes']:\n    name=entry['file'];data=(root/name).read_bytes()\n    if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise RuntimeError('Episode SHA mismatch')\n    files[name]=data\nfull='\\n\\n'.join(files[e['file']].decode() for e in meta['episodes'])\nif hashlib.sha256(full.encode()).hexdigest()!=meta['full_source_sha256']:raise RuntimeError('Full 40-chapter source SHA mismatch')\nstage=pathlib.Path('/kaggle/working/verified-private-ep1')\nstage.mkdir(parents=True,exist_ok=True)\nwith zipfile.ZipFile(stage/'MANHUA_STORY_PACKAGE.zip','w',compression=zipfile.ZIP_DEFLATED) as z:\n    z.writestr('manifest.json',raw_manifest)\n    for n,b in files.items():z.writestr(n,b)\nos.environ['MANHUA_INPUT_DIR']=str(stage)\ncore=sys.modules['video.audiobook_studio.manhua_pipeline.core']\nkaggle=sys.modules['video.audiobook_studio.manhua_pipeline.kaggle_runner']\nold_split=core.split_chunks;old_plan=core.scene_plan\nkaggle.split_chunks=lambda script:old_split(script,max_words=140)\nkaggle.scene_plan=lambda chunks,**kw:old_plan(chunks,target_words=80,**kw)\nprint('ETERNAL_DAO_PRIVATE_SOURCE_HASH_VERIFIED',{'episodes':17,'scene_chunk_target_words':80,'voice_chunk_max_words':140},flush=True)\n"
        runner+='subprocess.run([sys.executable,"-m","pip","install","-q","qwen-tts","accelerate","soundfile","diffusers","transformers","safetensors","pillow"],check=True)\n'
        runner+='result=sys.modules["video.audiobook_studio.manhua_pipeline.kaggle_runner"].process(story_id='+repr(STORY)+',episode=1,phase="assets",quality="quality")\n'
        runner+='print("ETERNAL_DAO_PRIVATE_GPU_ASSET_RESULT",__import__("json").dumps(result),flush=True)\n'
        (stage/'runner.py').write_text(runner)
        (stage/'kernel-metadata.json').write_text(json.dumps({
            'id':owner+'/'+KERNEL_SLUG,'title':'Private Eternal Dao Episode 1 Manhua Assets',
            'code_file':'runner.py','language':'python','kernel_type':'script',
            'is_private':True,'enable_gpu':True,'enable_internet':True,
            'dataset_sources':[ref],'competition_sources':[],'kernel_sources':[],'model_sources':[]
        },indent=2))
        subprocess.run(['kaggle','kernels','push','-p',str(stage)],check=True,timeout=240)
        print('ETERNAL_DAO_EP01_KAGGLE_GPU_SUBMITTED',json.dumps({
            'private_kernel':owner+'/'+KERNEL_SLUG,'phase':'assets','quality':'quality',
            'voice':'Ryan','public_release_approved':False,'ffmpeg_assembly':False}),flush=True)

if __name__=='__main__':main()
