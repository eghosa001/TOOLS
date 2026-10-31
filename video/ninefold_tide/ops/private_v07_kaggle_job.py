#!/usr/bin/env python3
"""Ninefold v07 private Kaggle source-runner: never invent or publish source art.

The public TOOLS repo contains only this runner. The original archive must
be mounted as a PRIVATE Kaggle dataset, or securely provided at runtime.
This script is safe to run as a private Kaggle script kernel, without touching
any previous notebook, GPU credits or any user-owned data outside its output.
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys, tarfile, time, urllib.request, zipfile
from pathlib import Path

BASE = Path('/kaggle/working') if Path('/kaggle/working').is_dir() else Path('/tmp')
WORK = Path('/tmp/ninefold_v07_runtime_scratch')
WORK.mkdir(parents=True, exist_ok=True)
OUTPUT = BASE / 'ninefold_v07_private_build'
OUTPUT.mkdir(parents=True, exist_ok=True)
REPORT = BASE / 'source_build_report.json'
BUNDLE = 'NINEFOLD_2D_GREASE_PENCIL_KAGGLE_TRANSFER_v07.zip'
V07_HASH = '98c5f655860f53d68019605955f3c5e3951b139eb1570153f9fb1cf1a7655e91'
V05_HASH = '24c0fb2ae611b4ba50792eb20abc6e192df016401dfa94e0b1eef452dfb77d2c'
FILE_ID = '1dSFNAqlswiGU2tAWrZi85T1y9mvdu5x3'
BLENDER_VERSION='4.5.15'
EXTRACTED_TREE_SHA256='485573e3c3faa814c976ad7f0a9436344e24115466cc3f7f048c9427872251eb'
EXTRACTED_FILE_COUNT=38

V07_MEMBERS = {
    'BUILD_2D_GREASE_PENCIL_WORKSPACE_v07.py': 'f2d0f992e56694c3d59dbd0711821fcbc66f5b82910cf1f1d44d1e96d10a538c',
    'PIPELINE_AND_ART_DIRECTION.md': '841fc7eab766e5b6781964b15bc435caf061a7a7551793725a0650fbb45539ad',
    'SHOT_QUALITY_GATE_v07.json': 'ef8577dd62d91e3a39236bfc3b47cc00625e4c7506fe093ee7dacc54426f8f5d',
    'CAST_ASSET_TRACKER.csv': '3409b19fae5fbbbf3526f19fafd52ae93dc9b38fa6a7571f581d832da5a65f04',
    'Ninefold_2D_Characters_3D_Backgrounds_Kaggle_v07.ipynb': 'b581b94dbb8ba4bf2744723dfbffd427631bfb03efc65b38e5fb469c8669f899',
    'NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets.zip': V05_HASH,
}

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as src:
        for b in iter(lambda:src.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def write_state(state, **kw):
    obj={'status':state,'created_by':'TOOLS Ninefold private source runner',
         'original_source_hash':V07_HASH,'is_private_kaggle':True,
         'approved_art':False,'video_created':False,
         'authoritative_story_and_design':'Google Drive series bible v2 / cast bible / EP101 handoff',
         **kw}
    REPORT.write_text(json.dumps(obj,indent=2,default=str)+'\n')
    print('NINEFOLD_V07_KAGGLE_STATE',json.dumps({'status':state,'notes':kw.get('notes',[]),
          'stage':kw.get('stage'),'qa_passed':kw.get('qa_passed',False)}),flush=True)
    return obj

def validate_source(path):
    if path.is_file() and path.stat().st_size<=10_000_000 and digest(path)==V07_HASH:
        with zipfile.ZipFile(path) as z:
            return 'NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets.zip' in z.namelist()
    return False

def validate_expanded_source(folder):
    """Kaggle may expand uploaded ZIPs: authenticate each known original byte file."""
    return folder.is_dir() and all(
        (folder / name).is_file() and (folder / name).stat().st_size <= 20_000_000
        and digest(folder / name) == sha
        for name, sha in V07_MEMBERS.items()
    )

def validate_recursively_expanded_source(folder):
    """Authenticate the 38 exact original source-file bytes after Kaggle recursively unzips both archives."""
    if not folder.is_dir():return False
    paths=sorted((p for p in folder.rglob('*') if p.is_file()
                  and p.name not in ('README.txt','dataset-metadata.json')),
                 key=lambda p:p.relative_to(folder).as_posix())
    if len(paths)!=EXTRACTED_FILE_COUNT:return False
    h=hashlib.sha256()
    for p in paths:
        rel=p.relative_to(folder).as_posix()
        size=p.stat().st_size
        if size>15_000_000:return False
        h.update(rel.encode('utf-8')+b'\\x00'+size.to_bytes(8,'big'))
        with p.open('rb') as src:
            for chunk in iter(lambda:src.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()==EXTRACTED_TREE_SHA256

def find_source():
    matches=[]
    for root in (Path('/kaggle/input'),WORK):
        if root.exists():
            matches += [p for p in root.rglob(BUNDLE) if p.is_file()]
    validated=[p for p in matches if validate_source(p)]
    # Kaggle's dataset importer may expand the original outer ZIP. The expected
    # member hashes establish byte-equivalent source without needing ZIP metadata.
    expanded=[]
    for root in (Path('/kaggle/input'),WORK):
        if root.exists():
            expanded += [p.parent for p in root.rglob('NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets.zip')
                         if p.is_file()]
    validated_expanded=[p for p in set(expanded) if validate_expanded_source(p)]
    if len(validated)>1 or len(validated_expanded)>1:
        raise RuntimeError('Multiple source bundles: refuse ambiguous canon')
    if validated:
        return validated[0], 'mounted_private_kaggle_data'
    if validated_expanded:
        return validated_expanded[0], 'mounted_private_kaggle_expanded_verified'
    # Kaggle indexes the uploaded outer ZIP and nested v05 ZIP as 38 separate
    # files. Verify the canonical filename+length+byte digest before using them.
    recursive=[]
    for root in (Path('/kaggle/input'),WORK):
        if root.exists():
            for gpfile in root.rglob('BUILD_2D_GREASE_PENCIL_WORKSPACE_v07.py'):
                if validate_recursively_expanded_source(gpfile.parent):
                    recursive.append(gpfile.parent)
    if len(recursive)>1:
        raise RuntimeError('Multiple recursively expanded source roots')
    if recursive:
        return recursive[0], 'mounted_private_kaggle_recursively_expanded_verified'
    # Attempt Drive access without modifying permissions. Never save an HTML
    # sign-in page as if it were an archive. Hash MUST match the original.
    target=WORK/BUNDLE
    url=f'https://drive.google.com/uc?export=download&id={FILE_ID}&confirm=t'
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Ninefold-Private-Asset-Intake/1.0'})
        with urllib.request.urlopen(request,timeout=22) as reply:
            if (reply.headers.get('Content-Type') or '').lower().startswith('text/html'):
                return None,'restricted_google_drive'
            with target.open('wb') as out:
                limit=10_000_000
                while limit>0:
                    b=reply.read(min(1<<20,limit))
                    if not b:break
                    out.write(b); limit-=len(b)
        if validate_source(target):return target,'drive_sha256_verified'
        target.unlink(missing_ok=True)
        return None,'restricted_or_hash_mismatch'
    except Exception:
        target.unlink(missing_ok=True)
        return None,'restricted_google_drive'

def extract_zip(path,dest):
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path) as z:
        names=z.infolist()
        if len(names)>150 or sum(m.file_size for m in names)>120_000_000:
            raise ValueError('Source ZIP untrusted size/count')
        for m in names:
            p=Path(m.filename)
            if p.is_absolute() or '..' in p.parts or ':' in m.filename:
                raise ValueError('Unsafe archive member path')
            if m.is_dir():continue
            target=(dest/p).resolve()
            if dest.resolve() not in target.parents:raise ValueError('ZIP path traversal')
            mode=(m.external_attr>>16)&0o170000
            if mode==0o120000:raise ValueError('ZIP symlink forbidden')
        z.extractall(dest)

def installed_blender():
    path=shutil.which('blender')
    if path:
        p=subprocess.run([path,'--version'],capture_output=True,text=True,timeout=35)
        m=re.search(r'Blender\s+(\d+)\.(\d+)',p.stdout)
        if p.returncode==0 and m and (int(m[1]),int(m[2]))>=(4,5):return path
    url='https://download.blender.org/release/Blender4.5/'
    archive=WORK/'blender-4.5.15-linux-x64.tar.xz'
    checksum_name='blender-4.5.15.sha256'
    with urllib.request.urlopen(url+checksum_name,timeout=80) as r:
        checksum=r.read().decode()
    matched=[s for s in checksum.splitlines() if archive.name in s]
    if len(matched)!=1:raise RuntimeError('Official Blender checksum not found')
    wanted=re.search(r'[a-fA-F0-9]{64}',matched[0])
    if wanted is None:raise RuntimeError('Official Blender checksum malformed')
    if not archive.is_file() or digest(archive)!=wanted.group(0).lower():
        archive.unlink(missing_ok=True)
        with urllib.request.urlopen(url+archive.name,timeout=100) as s, archive.open('wb') as w:
            shutil.copyfileobj(s,w,length=1<<20)
    if digest(archive)!=wanted.group(0).lower():raise RuntimeError('Official Blender SHA mismatch')
    root=WORK/'blender_exec'
    root.mkdir(exist_ok=True)
    with tarfile.open(archive,'r:xz') as tar:
        for member in tar.getmembers():
            dest=(root/member.name).resolve()
            if root.resolve() not in dest.parents and dest!=root.resolve():
                raise ValueError('Blender tar path traversal')
            if member.issym() or member.islnk():
                link=(dest.parent/member.linkname).resolve()
                if root.resolve() not in link.parents:raise ValueError('Blender tar unexpected link')
        tar.extractall(root,filter='data')
    bins=list(root.glob('blender-*/blender'))
    if len(bins)!=1:raise RuntimeError('Missing Blender executable')
    return str(bins[0])

def check_graphics():
    import ctypes
    try:ctypes.CDLL('libEGL.so.1');return
    except OSError:pass
    if not shutil.which('apt-get'):raise RuntimeError('Missing libEGL and apt-get')
    subprocess.run(['apt-get','update','-qq'],check=True,timeout=220,stdout=subprocess.DEVNULL)
    subprocess.run(['apt-get','install','-y','-qq','libegl1','libgl1','libgbm1','libxkbcommon0',
        'libxi6','libxrandr2','libxfixes3','libxrender1','libx11-6','libxxf86vm1','libsm6','libice6','libxext6'],
        check=True,timeout=300,stdout=subprocess.DEVNULL)
    ctypes.CDLL('libEGL.so.1')

def invoke(name, command, timeout=450):
    r=subprocess.run(command,capture_output=True,text=True,timeout=timeout,env={**os.environ,'LIBGL_ALWAYS_SOFTWARE':'1'})
    (WORK/f'{name}.log').write_text((r.stdout+'\n'+r.stderr)[-30000:],encoding='utf-8')
    if r.returncode:
        raise RuntimeError(f'{name} exited {r.returncode}; inspect PRIVATE log {name}.log')

def build(source):
    extracted=WORK/'source_original'
    if source.is_file() and validate_source(source):
        extract_zip(source,extracted)
    elif source.is_dir() and validate_expanded_source(source):
        extracted.mkdir(parents=True,exist_ok=True)
        for name in V07_MEMBERS:
            shutil.copy2(source/name,extracted/name)
    elif source.is_dir() and validate_recursively_expanded_source(source):
        extracted.mkdir(parents=True,exist_ok=True)
        for path in source.rglob('*'):
            if not path.is_file() or path.name in ('README.txt','dataset-metadata.json'):
                continue
            destination=extracted/path.relative_to(source)
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,destination)
    else:
        raise RuntimeError('Private v07 source failed original SHA-256/expanded tree verification')
    inner=extracted/'NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets.zip'
    if inner.is_file():
        if digest(inner)!=V05_HASH:raise RuntimeError('v05 inner ZIP checksum mismatch')
        extract_zip(inner,extracted)
        world=extracted/'Ninefold_Production_Foundation_v05'
    else:
        world=extracted/'NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets'/'Ninefold_Production_Foundation_v05'
        if not world.is_dir():raise RuntimeError('Expanded v05 world geometry root missing')
    modules=list((world/'assets_glb').glob('A0[1-7]_*.glb'))
    if len(modules)!=7:raise RuntimeError('Not seven original Blender world modules')
    gp=extracted/'BUILD_2D_GREASE_PENCIL_WORKSPACE_v07.py'
    src=gp.read_text()
    marker="    drawing['narrative_brief'] = actor['notes']\n"
    if src.count(marker)!=1:raise RuntimeError('Unknown Grease Pencil source version')
    patch=marker+'    for previous_layer in tuple(drawing.data.layers):\n        drawing.data.layers.remove(previous_layer)\n'
    gp.write_text(src.replace(marker,patch))
    for p in (gp,world/'blender'/'BUILD_VEYRA_SCENE_BLENDER_45.py'):
        compile(p.read_text(),str(p),'exec')
    check_graphics()
    blender=installed_blender()
    # v05 script saves its .blend to the extracted WORLD root. Never alter the original ZIP.
    invoke('stage_v05',[blender,'-b','--factory-startup','--python',
            str(world/'blender'/'BUILD_VEYRA_SCENE_BLENDER_45.py')],600)
    base=world/'NINEFOLD_EP101_2p5D_WORLD_v05.blend'
    if not base.is_file():raise RuntimeError('Real v05 Blender file not saved')
    out=WORK/'v07_editable';out.mkdir(exist_ok=True)
    invoke('workspace_v07',[blender,'-b',str(base),'--python',str(gp),'--',str(out)],500)
    scene=out/'NINEFOLD_EP101_2D_GP_CHARACTERS_3D_BACKGROUND_v07.blend'
    qa=out/'NINEFOLD_v07_Blender_Runtime_QA.json'
    if not scene.is_file() or not qa.is_file():raise RuntimeError('Missing real v07 .blend or GP report')
    q=json.loads(qa.read_text())
    if len(q.get('characters',[]))!=3 or any(x['layers']!=9 for x in q['characters']):
        raise RuntimeError('Grease Pencil layer count incorrect')
    if len(q.get('world_ropes',[]))<3 or q.get('world_socket_count',0)<5:
        raise RuntimeError('Canonical independent rope sockets missing')
    # Pack source textures and make one low-cost camera inspection still.
    inspection=WORK/'pack_and_render_inspection.py'
    inspection.write_text('''import bpy,json,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
assert bpy.data.objects.get('CAM_03_NAYA_SERVICE_GALLERY_MEDIUM')
assert all(bpy.data.objects.get(f'DRAW_{c}_FRAME_BY_FRAME_2D') and len(bpy.data.objects[f'DRAW_{c}_FRAME_BY_FRAME_2D'].data.layers)==9 for c in ('NAYA','KITO','IRI'))
assert all(o.hide_render for o in bpy.data.objects if o.name.startswith('TEMP_') and '_FRONT_' in o.name)
missing=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.name)
if missing:raise RuntimeError('Missing original textures '+repr(missing[:10]))
bpy.ops.file.pack_all()
scene=out/'NINEFOLD_EP101_2D_GP_CHARACTERS_3D_BACKGROUND_v07.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(scene),compress=True)
s.camera=bpy.data.objects['CAM_03_NAYA_SERVICE_GALLERY_MEDIUM']
s.render.engine='CYCLES';s.cycles.samples=6
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=35
s.render.image_settings.file_format='PNG';s.render.filepath=str(out/'NAYA_CAM03_INTERNAL_UNAPPROVED_LAYOUT.png')
bpy.ops.render.render(write_still=True)
print('V07_PRIVATE_INTERNAL_LAYOUT_RENDERED',s.render.filepath)
''')
    invoke('inspection',[blender,'-b',str(scene),'--python',str(inspection),'--',str(out)],480)
    png=out/'NAYA_CAM03_INTERNAL_UNAPPROVED_LAYOUT.png'
    if not png.is_file() or png.stat().st_size<10000:raise RuntimeError('Missing genuine layout still')
    # Keep huge Blender download/unpacked archive in /tmp; export only finished
    # internal technical outputs from this PRIVATE Kaggle run.
    deliver=OUTPUT
    for artifact in (scene,qa,png):
        shutil.copy2(artifact,deliver/artifact.name)
    return {'qa_passed':True,'stage':'real_v05_v07_source','blender_version':BLENDER_VERSION,
            'grease_pencil_layers':9,'actors':['NAYA','KITO','IRI'],'modules':len(modules),
            'real_v05_blend':'temporary layout generated', 'editable_v07_blend':str(deliver/scene.name),
            'private_runtime_qa':str(deliver/qa.name),'internal_layout':str(deliver/png.name),
            'blend_sha256':digest(scene),'layout_sha256':digest(png),
            'notes':['Character drawings remain empty','Internal layout only, not a finished animation']}

def main():
    try:
        src,location=find_source()
        if src is None:
            write_state('BLOCKED_SOURCE_ACCESS',stage='asset_intake',source_access=location,
                notes=['Original Drive v07 ZIP is not available on a private Kaggle input dataset',
                       'The Drive file is not anonymously downloadable; no public sharing was requested',
                       'No other Kaggle notebooks, source files, or paid GPU credits were changed'])
            return
        write_state('SOURCE_VERIFIED',stage='asset_intake',source_access=location)
        result=build(src)
        write_state('TECHNICAL_BUILD_COMPLETE',**result,source_access=location)
    except Exception as exc:
        write_state('FAILED_BUILD',stage='runtime',error_type=type(exc).__name__,error=str(exc)[:500],
            notes=['See the isolated Kaggle working directory for stage logs; no animation approved'])
        raise
if __name__=='__main__':main()