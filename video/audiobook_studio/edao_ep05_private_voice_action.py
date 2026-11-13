#!/usr/bin/env python3
"""Owner-private Kokoro Michael audiobook voice relay for existing TOOLS GitHub Actions.

Public repository receives only an ephemeral RSA public key and AES-GCM-encrypted
source payload. Original manuscript and narration are never committed in plaintext.
Generated narration and actual music-first receipt are RSA/AES-encrypted again for
the owner; no YouTube upload or claim of release approval.
"""
from __future__ import annotations
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
import wave
import zipfile

import requests

REPO = os.environ["GITHUB_REPOSITORY"]
GH_TOKEN = os.environ["GITHUB_TOKEN"]
API = f"https://api.github.com/repos/{REPO}/contents/"
PUB = ".private-audiobook/edao-ep05-temporary-public.pem"
INP = ".private-audiobook/edao-ep05-private-input.encrypted.json"
HEADERS = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}
ROOT = Path("edao-ep05-owner-private")
ROOT.mkdir(exist_ok=True)


def get_file(path):
    response = requests.get(API + path, headers=HEADERS, timeout=25)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def put_file(path, data, message):
    old = get_file(path)
    payload = {"message": message, "branch": "main",
               "content": base64.b64encode(data).decode("ascii")}
    if old:
        payload["sha"] = old["sha"]
    response = requests.put(API + path, headers=HEADERS, json=payload, timeout=35)
    response.raise_for_status()


def delete_file(path):
    old = get_file(path)
    if old:
        response = requests.delete(API + path, headers=HEADERS, json={
            "message": "Clear temporary encrypted Episode 05 handoff",
            "branch": "main", "sha": old["sha"]}, timeout=35)
        response.raise_for_status()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import numpy as np
    from video.audiobook_studio.manhua_pipeline.music_bed import (
        prebuild_music_before_voice, require_music_first_preflight)

    if get_file(PUB) or get_file(INP):
        raise RuntimeError("PREEXISTING_PRIVATE_RELAY_INPUT: do not reuse stale keys")
    keypair = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    pub = keypair.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    put_file(PUB, pub, "Open temporary EDAO Episode 05 owner encrypted input relay")
    print("EDAO_EP05_RSA_PUBLIC_KEY_READY", flush=True)

    try:
        input_file = None
        for _ in range(180):
            input_file = get_file(INP)
            if input_file:
                break
            time.sleep(3)
        if not input_file:
            raise RuntimeError("ENCRYPTED_OWNER_SOURCE_NOT_RECEIVED")

        envelope = json.loads(base64.b64decode(input_file["content"]))
        wrapped = base64.b64decode(envelope["wrapped_key_b64"])
        secret = keypair.decrypt(wrapped, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(), label=None))
        raw = AESGCM(secret).decrypt(
            base64.b64decode(envelope["nonce_b64"]),
            base64.b64decode(envelope["ciphertext_b64"]),
            b"edao-ep05-kokoro-r2")
        if sha(raw) != envelope["sha256"]:
            raise RuntimeError("INPUT_SOURCE_HASH_MISMATCH")

        with zipfile.ZipFile(io.BytesIO(raw)) as zin:
            source = zin.read("source.txt").decode("utf-8")
            beats = json.loads(zin.read("beats50.json"))
            owner_pub = serialization.load_pem_public_key(zin.read("owner_output_pub.pem"))
        if len(source.split()) < 5500 or len(beats) != 50:
            raise ValueError("WRONG_SOURCE_OR_SCENE_COUNT")
        if "".join(str(beat["text"]) for beat in beats) != source:
            raise ValueError("APPROVED_SOURCE_NOT_RECONSTRUCTED_VERBATIM")
        if any(beat["scene"] != i or beat["text_sha256"] != sha(beat["text"].encode())
               for i, beat in enumerate(beats, 1)):
            raise ValueError("SCENE_SEQUENCE_OR_TEXT_HASH_MISMATCH")
        print("R2_APPROVED_TEXT_LOCKED", len(source.split()), len(beats), sha(source.encode()), flush=True)

        music_target = ROOT / "E05_NEW_MASTER.mp4"
        prebuild_music_before_voice(music_target, mood="mystery", level=0.10)
        verified_music = require_music_first_preflight(music_target, mood="mystery", level=0.10)
        print("MUSIC_FIRST_BEFORE_SPEECH", verified_music["music_sha256"], flush=True)

        from kokoro import KPipeline
        pipe = KPipeline(lang_code="a", device="cpu")
        wavs, timing = [], []
        for idx, beat in enumerate(beats, 1):
            samples = []
            for result in pipe(beat["text"], voice="am_michael", speed=1.25):
                audio = result.audio if hasattr(result, "audio") else result[2]
                if hasattr(audio, "detach"):
                    audio = audio.detach().cpu().numpy()
                v = np.asarray(audio, dtype=np.float32).reshape(-1)
                if v.size == 0 or not np.isfinite(v).all():
                    raise RuntimeError("NON_FINITE_KOKORO_AUDIO")
                samples.append(v)
            if not samples:
                raise RuntimeError(f"KOKORO_EMPTY_SCENE_{idx:02d}")
            concat = np.concatenate(samples + [
                np.zeros(int(0.14 * 24000), dtype=np.float32)])
            p = ROOT / f"beat_{idx:02d}.wav"
            with wave.open(str(p), "wb") as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000)
                wav.writeframes((np.clip(concat, -1, 1) * 32767).astype("<i2").tobytes())
            wavs.append(p)
            timing.append({"scene": idx, "duration_seconds": round(len(concat)/24000, 6),
                           "text_sha256": beat["text_sha256"]})
            if idx % 5 == 0:
                print("KOKORO_SCENES", idx, "/50", flush=True)
        full = ROOT / "R2_narration.wav"
        with wave.open(str(full), "wb") as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000)
            for part in wavs:
                with wave.open(str(part), "rb") as sourcewav:
                    out.writeframes(sourcewav.readframes(sourcewav.getnframes()))
        m4a = ROOT / "R2_Kokoro_Michael_1p25.m4a"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(full), "-c:a", "aac", "-b:a", "192k", str(m4a)],
            check=True, timeout=600)
        assert m4a.stat().st_size > 10_000_000
        track = verified_music["music_sha256"]
        bed_path = music_target.with_name(
            music_target.stem + ".mythveil_original_melodic_bed_v1.mystery.wav")
        assert bed_path.is_file() and sha(bed_path.read_bytes()) == track
        output_receipt = {"voice": "am_michael", "speed": 1.25,
          "word_count": len(source.split()), "source_sha256": sha(source.encode()),
          "scene_count": len(beats), "scene_timings": timing,
          "music_first_receipt_sha256": verified_music["receipt_sha256"],
          "music_sha256": track, "narration_sha256": sha(m4a.read_bytes()),
          "status": "PRIVATE_NARRATION_ONLY_NOT_FULL_VIDEO_QA_APPROVED"}
        pack = io.BytesIO()
        with zipfile.ZipFile(pack, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=4) as z:
            z.write(m4a, "narration.m4a")
            z.write(bed_path, "original_music_first.wav")
            z.write(music_target.with_name(
                music_target.stem + ".music_preflight.json"), "music_preflight.json")
            z.writestr("voice_scene_timing.json", json.dumps(output_receipt, indent=2))
        actual = pack.getvalue()
        symkey = os.urandom(32);nonce = os.urandom(12)
        cipher = AESGCM(symkey).encrypt(nonce, actual, b"edao-ep05-private-output")
        wrapped_out = owner_pub.encrypt(symkey, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(), label=None))
        result = {"wrapped_key_b64": base64.b64encode(wrapped_out).decode(),
                  "nonce_b64": base64.b64encode(nonce).decode(),
                  "ciphertext_b64": base64.b64encode(cipher).decode(),
                  "sha256": sha(actual)}
        (ROOT/"PRIVATE_ENCRYPTED_NARRATION.json").write_text(json.dumps(result))
        print("EDAO_EP05_ENCRYPTED_NARRATION_READY", len(actual), flush=True)
    finally:
        delete_file(INP)
        delete_file(PUB)


if __name__ == "__main__":
    main()
