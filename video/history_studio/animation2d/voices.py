#!/usr/bin/env python3
"""Original 2D documentary voice builder with per-speaker timing.

Uses cached Piper public-domain audition voices after checking their model cards.
Produces aligned PCM16 mono scene WAVs and preserves all licensed artwork
references when moving an episode to a new build folder.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import wave

DEFAULT_VOICES = {"narrator":"norman", "historian":"john", "worker":"kristin"}


def import_legacy_voice():
    source = Path(__file__).resolve().parents[2]/"production_voice_tracks.py"
    spec = importlib.util.spec_from_file_location("history_legacy_voice_license",source)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load existing licensed Piper voice source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wav_bytes(path:Path):
    with wave.open(str(path),"rb") as reader:
        if reader.getnchannels()!=1 or reader.getsampwidth()!=2:
            raise ValueError("Use only signed 16-bit mono PCM WAV")
        if reader.getframerate()<=0:raise ValueError("Invalid sampling rate")
        return reader.getframerate(),reader.readframes(reader.getnframes())


def assemble_speech(lines, destination, pause=.20):
    """Return (audio duration, speaker ranges) using real decoded sample counts."""
    if not 0<=pause<=2:raise ValueError("Unsupported pause")
    if not lines:raise ValueError("No narrated lines supplied")
    destination.parent.mkdir(parents=True,exist_ok=True)
    sampling_rate=None
    cursor=0
    intervals=[]
    data=[]
    for speaker,filename in lines:
        rate,raw=wav_bytes(filename)
        if sampling_rate is not None and sampling_rate!=rate:
            raise ValueError("Voice WAV sample rates differ; resample explicitly")
        sampling_rate=rate
        n=len(raw)//2
        if not n:raise ValueError("Empty narration WAV")
        start=cursor/rate
        end=(cursor+n)/rate
        intervals.append({"speaker":speaker,"start":round(start,5),"end":round(end,5)})
        data.append(raw)
        pad=b"\0\0"*round(rate*pause)
        data.append(pad)
        cursor+=n+len(pad)//2
    with wave.open(str(destination),"wb") as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(sampling_rate)
        out.writeframes(b"".join(data))
    return cursor/sampling_rate,intervals


def rebase_media(episode,source_root,dest_root):
    """Copy only source-local visual/audio assets used by the episode.

    Never carry unsafe references or remote URLs into the output, and do not
    inadvertently discard copyrighted/artwork provenance metadata.
    """
    if source_root.resolve()==dest_root.resolve():return
    references=[]
    for cfg in episode.get("characters",{}).values():
        references.extend((cfg.get("sprites") or {}).values())
    for scene in episode.get("scenes",[]):
        references.extend(scene.get(k) for k in ("background_image","mouth_cues","audio_file") if scene.get(k))
    rewritten={}
    for rel in references:
        if rel in rewritten:continue
        original=(source_root/rel).resolve()
        if not original.is_relative_to(source_root.resolve()) or not original.is_file():
            raise ValueError("Unsafe or missing input media asset: "+str(rel))
        digest=hashlib.sha256(original.read_bytes()).hexdigest()[:12]
        target=dest_root/"assets"/(digest+"_"+original.name)
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(original.read_bytes()).digest():
            shutil.copy2(original,target)
        rewritten[rel]=str(target.relative_to(dest_root).as_posix())
    for cfg in episode.get("characters",{}).values():
        cfg["sprites"]={k:rewritten[v] for k,v in (cfg.get("sprites") or {}).items()}
    old_rights=episode.get("asset_rights",{})
    if isinstance(old_rights,dict):
        episode["asset_rights"]={rewritten.get(key,key):row for key,row in old_rights.items()}
    for scene in episode.get("scenes",[]):
        for key in ("background_image","mouth_cues","audio_file"):
            if scene.get(key):scene[key]=rewritten[scene[key]]


def srt_time(seconds):
    millis=max(0,round(seconds*1000))
    hh,remainder=divmod(millis,3600000)
    mm,remainder=divmod(remainder,60000)
    ss,ms=divmod(remainder,1000)
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def subtitle_text(episode):
    """Subtitle timeline from actual timed speech, including silent scene offsets."""
    offset=0.0;records=[]
    for scene in episode["scenes"]:
        lines=scene.get("lines",[])
        timings=scene.get("speech_timing",[])
        if lines and len(lines)!=len(timings):
            raise ValueError("Cannot subtitle speech with mismatched timeline")
        for row,interval in zip(lines,timings):
            sentence=row["text"].strip().replace("\r"," ").replace("\n"," ")
            if sentence:
                records.append(f"{len(records)+1}\n{srt_time(offset+interval['start'])} --> {srt_time(offset+interval['end'])}\n{sentence}\n")
        offset+=float(scene["duration"])
    return "\n".join(records)+"\n" if records else ""


def produce(episode_path,output_path,model_cache,speech_cache,padding=.4,pause=.2):
    if not .0<=padding<=3:raise ValueError("Invalid scene padding")
    episode_path=episode_path.resolve()
    output_path=output_path.resolve()
    episode=json.loads(episode_path.read_text(encoding="utf8"))
    if episode.get("format")!="history_2d_cartoon":raise ValueError("Wrong episode format")
    rebase_media(episode,episode_path.parent,output_path.parent)
    need_tts=any(scene.get("lines") for scene in episode["scenes"])
    if need_tts:
        try:
            from piper.voice import PiperVoice
        except ImportError as exc:
            raise RuntimeError("Install piper-tts for offline narration") from exc
        legacy=import_legacy_voice()
        loaded={}
        speech_cache.mkdir(parents=True,exist_ok=True)
    for scene_number,scene in enumerate(episode["scenes"],1):
        lines=scene.get("lines",[])
        if not lines:continue
        rendered=[]
        for row in lines:
            speaker=row.get("speaker","narrator")
            model_name=episode.get("voice_cast",{}).get(speaker,DEFAULT_VOICES.get(speaker))
            if model_name is None:raise ValueError("Unapproved voice for speaker: "+speaker)
            txt=row.get("text","").strip()
            if not 1<=len(txt)<=900:raise ValueError("Speech line length out of range")
            if model_name not in loaded:
                model,config,card=legacy.voice_files(model_cache,model_name)
                loaded[model_name]=(PiperVoice.load(str(model),config_path=str(config)),model)
                print("VOICE_SOURCE_CHECKED",model_name,card,flush=True)
            voice,model=loaded[model_name]
            key=hashlib.sha256((model_name+"\0"+txt).encode()).hexdigest()[:24]
            wav=speech_cache/(key+".wav")
            if not wav.exists():
                with wave.open(str(wav),"wb") as f:voice.synthesize_wav(txt,f)
            rendered.append((speaker,wav))
        target=output_path.parent/"audio"/f"scene_{scene_number:03}.wav"
        seconds,intervals=assemble_speech(rendered,target,pause=pause)
        scene["speech_timing"]=intervals
        scene["audio_file"]=str(target.relative_to(output_path.parent).as_posix())
        scene["duration"]=round(seconds+padding,3)
        print("SCENE_VOICED",scene_number,f"{seconds:.2f}s",flush=True)
    episode["voice_status"]="Piper generated; per-model dataset licensing reviewed. Manual pronunciation and sound-quality review required."
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(episode,indent=2)+"\n",encoding="utf8")
    captions=subtitle_text(episode)
    if captions:
        output_path.with_suffix(".srt").write_text(captions,encoding="utf8")
        print("SUBTITLES_CREATED",output_path.with_suffix(".srt"),flush=True)
    return episode


def main():
    p=argparse.ArgumentParser()
    p.add_argument("episode",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--model-cache",type=Path,default=Path.home()/".cache/history-studio/piper-models")
    p.add_argument("--speech-cache",type=Path,default=Path.home()/".cache/history-studio/tts")
    p.add_argument("--padding",type=float,default=.4)
    args=p.parse_args()
    produce(args.episode,args.output,args.model_cache,args.speech_cache,args.padding)
if __name__=="__main__":main()