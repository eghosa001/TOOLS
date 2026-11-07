"""Private D03 source ingestion and approved Kaggle manhua generation.
Manuscripts, art, source archive and working access URL remain private.
"""
import base64, hashlib, json, os, pathlib, re, subprocess, sys, tempfile, types
from urllib.parse import urlsplit

STORY='eternal-dao-of-the-lost-epoch'
PACK_SHA='f544548bb60a958b7440467194e461d92daf5c5cf750be9154b204c649fad21a'
DATASET_SLUG='eternal-dao-d03-approved-private-manuscript'
KERNEL_SLUG='manhua-eternal-dao-d03-ep01-private'

def decrypt_url(blob, token):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    obj=json.loads(blob)
    assert obj['version']==1
    seed=HKDF(algorithm=hashes.SHA256(),length=32,
              salt=b'fiction-studio-2026-private-transport-v1',
              info=b'first-episode-transfer-key').derive(token.encode())
    private=X25519PrivateKey.from_private_bytes(seed)
    public=X25519PublicKey.from_public_bytes(base64.b64decode(obj['ephemeral_pub']))
    key=HKDF(algorithm=hashes.SHA256(),length=32,
             salt=b'audiobook-private-source-transfer-v1',
             info=b'eternal-dao-d03-episode1-data-link').derive(private.exchange(public))
    url=AESGCM(key).decrypt(base64.b64decode(obj['nonce']),
                            base64.b64decode(obj['ciphertext']),
                            b'eternal-dao-d03-private-source-ep01').decode()
    parsed=urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname.endswith('.oaiusercontent.com') or not parsed.path.endswith('/raw'):
        raise RuntimeError('Invalid private transfer host')
    return url

def run(*args):
    subprocess.run(args,check=True,timeout=240)

def main():
    token=os.environ.get('KAGGLE_API_TOKEN','')
    owner=os.environ.get('KAGGLE_USERNAME','aighewieghosa')
    sealed=os.environ.get('SEALED_EP01_SOURCE','')
    if len(token)<24 or not sealed or not re.fullmatch(r'[A-Za-z0-9_-]+',owner):
        raise RuntimeError('Required private credentials/source envelope unavailable')
    import requests
    from video.audiobook_studio.manhua_pipeline.core import open_package, split_chunks
    url=decrypt_url(sealed,token)
    with tempfile.TemporaryDirectory(prefix='private-dao-ep1-') as folder:
        root=pathlib.Path(folder)
        ds=root/'dataset';ds.mkdir()
        package=ds/'MANHUA_STORY_PACKAGE.zip'
        with requests.get(url,stream=True,timeout=(15,90)) as response:
            response.raise_for_status()
            with package.open('wb') as output:
                total=0
                for data in response.iter_content(65536):
                    total+=len(data)
                    if total>5_000_000:raise RuntimeError('Unexpected source package size')
                    output.write(data)
        if hashlib.sha256(package.read_bytes()).hexdigest()!=PACK_SHA:
            raise RuntimeError('Private source hash mismatch; GPU blocked')
        meta,ep1,_=open_package(package,expected_story_id=STORY,episode=1)
        if len(meta['episodes'])!=17 or len(ep1.split())!=3613 or len(meta.get('scene_briefs',{}).get('1',[]))!=24:
            raise RuntimeError('Wrong D03 episode/visual source; GPU blocked')
        print('PRIVATE_D03_EP01_SOURCE_VERIFIED',json.dumps({
            'episode':1,'all_episodes':len(meta['episodes']),
            'words':len(ep1.split()),'scene_briefs':24,
            'qwen_chunks':len(split_chunks(ep1)),
            'sha256':meta['episodes'][0]['sha256']}),flush=True)
        ref=owner+'/'+DATASET_SLUG
        (ds/'dataset-metadata.json').write_text(json.dumps({
            'id':ref,'title':'Private Eternal Dao D03 approved source','isPrivate':True,
            'licenses':[{'name':'copyright-authors'}]
        }))
        check=subprocess.run(['kaggle','datasets','files',ref,'--csv'],capture_output=True,text=True,timeout=90)
        if check.returncode==0:
            if 'MANHUA_STORY_PACKAGE.zip' not in check.stdout:
                raise RuntimeError('Existing dataset is incompatible')
            run('kaggle','datasets','version','-p',str(ds),'-m','Verified D03 source package')
        else:
            run('kaggle','datasets','create','-p',str(ds))
        check=subprocess.run(['kaggle','datasets','files',ref,'--csv'],capture_output=True,text=True,timeout=90)
        if check.returncode!=0 or 'MANHUA_STORY_PACKAGE.zip' not in check.stdout:
            raise RuntimeError('Private source dataset not accessible; GPU blocked')
        print('PRIVATE_MANHUA_SOURCE_INGESTED',json.dumps({'owner':owner,'slug':DATASET_SLUG,'published_in_public_repo':False}),flush=True)
        stage=root/'kernel';stage.mkdir()
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
        runner+='subprocess.run([sys.executable,"-m","pip","install","-q","qwen-tts","accelerate","soundfile","diffusers","transformers","safetensors","pillow"],check=True)\n'
        runner+='result=sys.modules["video.audiobook_studio.manhua_pipeline.kaggle_runner"].process(story_id='+repr(STORY)+',episode=1,phase="assets",quality="quality")\n'
        runner+='print("PRIVATE_EP01_GPU_ASSET_RESULT",__import__("json").dumps(result),flush=True)\n'
        (stage/'runner.py').write_text(runner)
        (stage/'kernel-metadata.json').write_text(json.dumps({
            'id':owner+'/'+KERNEL_SLUG,'title':'Private Eternal Dao Episode 1 Manhua Assets',
            'code_file':'runner.py','language':'python','kernel_type':'script',
            'is_private':True,'enable_gpu':True,'enable_internet':True,
            'dataset_sources':[ref],'competition_sources':[],'kernel_sources':[],'model_sources':[]
        },indent=2))
        run('kaggle','kernels','push','-p',str(stage))
        print('ETERNAL_DAO_EP01_PRIVATE_KAGGLE_ASSETS_SUBMITTED',json.dumps({
            'kernel':owner+'/'+KERNEL_SLUG,'phase':'assets','quality':'Animagine XL 3.1',
            'voice':'Qwen Ryan 1.7B','publication':'BLOCKED','video_assembly':'NOT_YET_DONE'}),flush=True)

if __name__=='__main__':main()
