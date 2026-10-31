#!/usr/bin/env python3
"""One-time encrypted URL bridge from user's authenticated Drive to PRIVATE Kaggle.

An ephemeral signed download URL is sealed using public-key encryption. Archive bytes are saved with an opaque .bin extension to prevent Kaggle auto-unpacking nested source ZIPs. The
public GitHub repo contains neither source art nor URL plaintext. Only this
GitHub Actions runner, with the preexisting authorized Kaggle token secret,
can decrypt it. The KAGGLE_API_TOKEN is not logged and not included in files.
Datasets are PRIVATE by default; we never pass --public.
"""
from __future__ import annotations
import argparse,base64,csv,hashlib,io,json,os,pathlib,subprocess,sys,tempfile,urllib.request
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes,serialization

PROJECT="ninefold-v09r1-original-archive-bytes"
OWNER="aighewieghosa"
FILENAME="Ninefold_S1_Private_Kaggle_Kit_v09r1.zip"
OPAQUE_FILENAME="Ninefold_S1_Private_Kaggle_Kit_v09r1.bin"
RELPATH=pathlib.Path(__file__).parent/"private_v09r1_transfer_seal.json"
AAD=b"ninefold-private-v09r1-art-transfer-v1"

def b64decode(value):
    return base64.b64decode(value,validate=True)

def derive_receiver():
    secret=os.environ.get("KAGGLE_API_TOKEN")
    if not secret:
        raise RuntimeError("Missing existing authorized Kaggle token secret")
    seed=HKDF(algorithm=hashes.SHA256(),length=32,
              salt=b"ninefold-2026-private-art-bridge-not-token",
              info=b"X25519-v09r1-art-ref-download").derive(secret.encode("utf8"))
    return X25519PrivateKey.from_private_bytes(seed)

def public_key_b64(private):
    return base64.b64encode(private.public_key().public_bytes(
        serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode("ascii")

def safe_cli(*args):
    proc=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=130)
    if proc.returncode:
        # Avoid Kaggle responses showing private account or auth details in logs.
        raise RuntimeError("Kaggle CLI request failed (exit="+str(proc.returncode)+")")
    return proc.stdout

def run(mode):
    key=derive_receiver()
    print("NINEFOLD_PRIVATE_BRIDGE_RECEIVER_PUBLIC_KEY",public_key_b64(key),flush=True)
    if mode=="public-key":
        return 0
    if not RELPATH.exists():
        print("SEALED_SOURCE_URL_NOT_YET_ATTACHED",flush=True)
        return 0
    seal=json.loads(RELPATH.read_text(encoding="utf8"))
    if seal.get("filename")!=FILENAME:
        raise ValueError("Private source name mismatch")
    expected=seal.get("source_sha256","")
    if len(expected)!=64 or not all(v in "0123456789abcdef" for v in expected):
        raise ValueError("Missing source ZIP hash")
    eph=X25519PublicKey.from_public_bytes(b64decode(seal["ephemeral_pub"]))
    shared=key.exchange(eph)
    aes=HKDF(algorithm=hashes.SHA256(),length=32,
             salt=b"ninefold-v09r1-ciphertext",
             info=b"sealed-signed-url-aes-gcm").derive(shared)
    url=AESGCM(aes).decrypt(b64decode(seal["nonce"]),
                            b64decode(seal["ciphertext"]),AAD).decode("utf8")
    # Be strict about the origin to prevent URL exfiltration; do not log URL.
    from urllib.parse import urlparse
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in ("sdmntpritalynorth.oaiusercontent.com","sdmntprnortheu.oaiusercontent.com"):
        raise ValueError("Signed Drive relay URL is not an approved private file gateway")
    ref=f"{OWNER}/{PROJECT}"
    existing=safe_cli("datasets","list","--mine","--csv")
    data_lines=[x for x in existing.splitlines() if x.strip()]
    header=next((i for i,x in enumerate(data_lines) if x.lower().startswith("ref,")),0)
    rows=list(csv.DictReader(io.StringIO("\n".join(data_lines[header:]))))
    if any(row.get("ref")==ref for row in rows):
        print("PRIVATE_KAGGLE_SOURCE_DATASET_ALREADY_EXISTS_NO_OVERWRITE",ref,flush=True)
        return 0
    with tempfile.TemporaryDirectory(prefix="ninefold_private_v09r1_") as tmp:
        folder=pathlib.Path(tmp)
        dest=folder/OPAQUE_FILENAME
        digest=hashlib.sha256()
        with urllib.request.urlopen(urllib.request.Request(url,headers={
              "User-Agent":"NinefoldPrivateArtifactBridge/1.0"}),timeout=115) as response:
            content_length=response.headers.get("Content-Length")
            if content_length and int(content_length)>8_000_000:
                raise RuntimeError("Unexpectedly large private Drive transfer")
            with dest.open("wb") as out:
                total=0
                while True:
                    block=response.read(1024*512)
                    if not block: break
                    total+=len(block)
                    if total>8_000_000:raise RuntimeError("Drive source file exceeded 8MB")
                    digest.update(block);out.write(block)
        if digest.hexdigest()!=expected:
            dest.unlink(missing_ok=True)
            raise RuntimeError("SECURITY: private Drive ZIP hash did not match locally verified content")
        if not 1_000_000<dest.stat().st_size<8_000_000:
            raise RuntimeError("Unexpected size for canonical original v09r1 kit")
        import zipfile
        if not zipfile.is_zipfile(dest):
            raise RuntimeError("Corrupted Drive source is not a ZIP")
        metadata={
          "title":"Ninefold V09R1 Original Archive Bytes",
          "id":ref,
          "licenses":[{"name":"other"}]
        }
        (folder/"dataset-metadata.json").write_text(json.dumps(metadata),encoding="utf8")
        # kaggle datasets create --public is NEVER used. Kaggle CLI defaults private.
        safe_cli("datasets","create","-p",str(folder),"-q","-t","-r","skip")
        print("PRIVATE_KAGGLE_ART_DATASET_CREATED",ref,
              "source_bytes",dest.stat().st_size,
              "private_default_public_flag_not_used",True,
              "file_sha256",expected,flush=True)
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["public-key","transfer"],required=True)
    args=p.parse_args()
    try:sys.exit(run(args.mode))
    except Exception as exc:
        print("PRIVATE_ART_BRIDGE_FAILED",type(exc).__name__,
              str(exc)[:240],file=sys.stderr)
        sys.exit(1)
