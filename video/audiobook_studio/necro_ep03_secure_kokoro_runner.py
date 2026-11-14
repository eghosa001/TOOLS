#!/usr/bin/env python3
"""Ep03 private one-time Kokoro CPU TTS. No owner story is stored in Git."""
import base64, hashlib, json, os, pathlib, subprocess, time, wave, zlib
import numpy as np
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT=pathlib.Path("owner-private-necro-ep03");ROOT.mkdir(exist_ok=True)
API="https://api.github.com/repos/"+os.environ["GH_REPO"]+"/contents/"
HDR={"Authorization":"Bearer "+os.environ["GH_TOKEN"],"Accept":"application/vnd.github+json"}
PUB=".private-audiobook/necro-ep03-session-pub.pem"
INPUT=".private-audiobook/necro-ep03-session-input.json"
def get(path):
    r=requests.get(API+path,headers=HDR,timeout=35)
    if r.status_code==404: return None
    r.raise_for_status()
    return r.json()
def put(path,blob,msg):
    old=get(path)
    obj={"message":msg,"branch":"main","content":base64.b64encode(blob).decode()}
    if old: obj["sha"]=old["sha"]
    r=requests.put(API+path,headers=HDR,json=obj,timeout=45);r.raise_for_status()
def delete(path):
    o=get(path)
    if o:
        r=requests.delete(API+path,headers=HDR,json={"message":"Remove expired private one-time relay","sha":o["sha"],"branch":"main"},timeout=45)
        print("INPUT_CLEANUP",path,r.status_code,flush=True)
def dec_base64(s):return base64.b64decode(s)
private=rsa.generate_private_key(public_exponent=65537,key_size=3072)
pem=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
if get(PUB) is not None or get(INPUT) is not None:
    raise RuntimeError("STALE_PRIVATE_RELAY_INPUT: stop instead of using old source")
put(PUB,pem,"Open short-lived Necromancer E03 encrypted audio intake")
print("NECROMANCER_EP03_OWNER_PUBLIC_KEY_READY",flush=True)
try:
    obj=None
    for index in range(220):
        obj=get(INPUT)
        if obj:break
        time.sleep(3)
    if obj is None:raise RuntimeError("EP03_ENCRYPTED_SOURCE_NOT_RECEIVED")
    bundle=json.loads(dec_base64(obj["content"]))
    key=private.decrypt(dec_base64(bundle["wrapped_key_b64"]),padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    compressed=AESGCM(key).decrypt(dec_base64(bundle["nonce_b64"]),dec_base64(bundle["ciphertext_b64"]),b"necro-ep03-kokoro-v1")
    source=json.loads(zlib.decompress(compressed))
    script=source["script"]
    if hashlib.sha256(script.encode("utf-8")).hexdigest()!=source["source_sha256"]:
        raise RuntimeError("D05_APPROVED_NARRATION_HASH_MISMATCH")
    if len(script)!=15372 or len(source["scene_spans"])!=35:
        raise RuntimeError("BAD_EP03_SCRIPT_OR_SPANS")
    bounds=source["scene_spans"]
    if bounds[0][0]!=0 or bounds[-1][1]!=len(script) or any(bounds[i][1]!=bounds[i+1][0] for i in range(34)):
        raise RuntimeError("EP03_SCENES_NOT_CONTIGUOUS")
    if source["voice"]!="am_michael" or source["speed"]!=1.25:
        raise RuntimeError("UNAPPROVED_VOICE")
    from kokoro import KPipeline
    voice=KPipeline(lang_code="a",device="cpu")
    all_parts=[]
    timeline=[]
    elapsed=0.0
    for i,(a,b) in enumerate(bounds):
        piece=script[a:b]
        chunks=[]
        for res in voice(piece,voice="am_michael",speed=1.25):
            a=res.audio if hasattr(res,"audio") else res[2]
            if hasattr(a,"detach"):a=a.detach().cpu().numpy()
            a=np.asarray(a,dtype=np.float32).reshape(-1)
            if a.size==0 or not np.isfinite(a).all():raise RuntimeError("BAD_KOKORO_AUDIO")
            chunks.append(a)
        if not chunks:raise RuntimeError("NO_VOICE_OUTPUT_SCENE_"+str(i+1))
        joined=np.concatenate(chunks+[np.zeros(int(24000*0.14),dtype=np.float32)])
        all_parts.append(joined)
        sec=len(joined)/24000
        timeline.append({"scene":i+1,"source_start":bounds[i][0],"source_end":bounds[i][1],"start_s":round(elapsed,4),"end_s":round(elapsed+sec,4),"duration_s":round(sec,4)})
        elapsed+=sec
        print("NECRO_EP03_SCENE_SPOKEN",i+1,"of",len(bounds),"duration",round(sec,2),flush=True)
    master=np.concatenate(all_parts)
    wav=ROOT/"narration.wav"
    with wave.open(str(wav),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
        f.writeframes((np.clip(master,-1,1)*32767).astype("<i2").tobytes())
    audio=ROOT/"narration.m4a"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(wav),"-af","loudnorm=I=-16:TP=-1.5:LRA=11","-c:a","aac","-b:a","160k",str(audio)],check=True,timeout=180)
    import io,zipfile
    package=io.BytesIO()
    with zipfile.ZipFile(package,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.write(audio,"narration.m4a")
        z.writestr("scene_timing.json",json.dumps({"source_sha256":source["source_sha256"],"voice":"am_michael","speed":1.25,"duration_s":elapsed,"scenes":timeline},indent=2))
    payload=package.getvalue()
    outpublic=serialization.load_pem_public_key(source["owner_public_pem"].encode())
    k=os.urandom(32);n=os.urandom(12)
    ct=AESGCM(k).encrypt(n,payload,b"necro-ep03-output-v1")
    wk=outpublic.encrypt(k,padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    (ROOT/"encrypted_result.json").write_text(json.dumps({"wrapped_key_b64":base64.b64encode(wk).decode(),"nonce_b64":base64.b64encode(n).decode(),"ciphertext_b64":base64.b64encode(ct).decode(),"sha256":hashlib.sha256(payload).hexdigest()}))
    print("NECRO_EP03_ENCRYPTED_NARRATION_COMPLETE",round(elapsed,3),len(payload),flush=True)
finally:
    delete(INPUT); delete(PUB)
