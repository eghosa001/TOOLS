#!/usr/bin/env python3
"""Pace-authored historical 3D Shorts and original Qwen3-TTS audio.

Six six-second Godot chapters stay semantically aligned. Each chapter gets an
explicit editorial duration. Only the original six Qwen performances are used:
trim their generated dead air, fit their full spoken content with pitch-preserving
atempo, and never omit or truncate words. Set separate event-specific CC0 Foley.
"""
from __future__ import annotations
import argparse,json,subprocess,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf

EDIT_DURATIONS={
 "fire":[4.0,4.0,5.1,4.1,4.1,4.2], # 25.5 s
 "siege":[4.5,4.1,4.3,3.4,4.5,4.2], # 25.0 s
}
def ff(*args):
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",*map(str,args)],check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("topic",choices=EDIT_DURATIONS.keys())
    ap.add_argument("--video",type=Path,required=True,help="36s fully reviewed Godot video master")
    ap.add_argument("--voices",type=Path,required=True,help="Six source Qwen WAVs")
    ap.add_argument("--foley",type=Path,default=None,help="Folder with approved CC0 Foley")
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    slots=EDIT_DURATIONS[a.topic]
    total=sum(slots)
    report=[]
    with tempfile.TemporaryDirectory(prefix="fast-history-") as d:
        root=Path(d)
        parts=[]
        for i,slot in enumerate(slots,1):
            wav=a.voices/f"{a.topic}_{i}.wav"
            data,rate=sf.read(wav,dtype="float32")
            if data.ndim==2:data=data.mean(axis=1)
            hop=max(1,int(rate*0.020))
            peaks=np.array([np.max(np.abs(data[j:j+hop])) for j in range(0,len(data),hop)])
            active=np.flatnonzero(peaks>0.003)
            if len(active)==0:raise ValueError("Silent source narration: "+str(wav))
            start=max(0,int(active[0]*hop-rate*0.09))
            end=min(len(data),int((active[-1]+1)*hop+rate*0.15))
            voice=data[start:end]
            source=root/f"source-{i}.wav"
            sf.write(source,voice,rate)
            tempo=(len(voice)/rate)/(slot-0.15)
            if not (0.95<=tempo<=1.90):raise ValueError("Unnatural voice tempo in chapter "+str(i)+": "+str(tempo))
            dst=root/f"take-{i}.wav"
            ff("-i",source,"-af",f"aresample=48000,atempo={tempo:.6f},apad=whole_dur={slot:.6f},atrim=duration={slot:.6f}",
               "-c:a","pcm_s16le","-ar","48000","-ac","2",dst)
            parts.append(dst)
            report.append({"take":i,"slot":slot,"source_s":round(len(data)/rate,3),
                           "speech_s":round(len(voice)/rate,3),"atempo":round(tempo,4)})
        playlist=root/"takes.txt"
        playlist.write_text("\n".join(f"file '{p}'" for p in parts)+"\n")
        voice=root/"narration.wav"
        ff("-f","concat","-safe","0","-i",playlist,"-af",f"loudnorm=I=-15:TP=-1.5:LRA=9,aresample=48000,atrim=duration={total:.6f}",
           "-ac","2","-ar","48000",voice)
        soundtrack=voice
        if a.foley and a.topic=="fire" and (a.foley/"fire-crackle.ogg").exists():
            out=root/"sound.wav"
            ff("-i",voice,"-stream_loop","-1","-i",a.foley/"fire-crackle.ogg",
               "-filter_complex",f"[1:a]aresample=48000,volume=0.085,lowpass=f=6000,atrim=duration={total},afade=t=out:st={total-0.75}:d=0.75[sfx];"
                                 "[0:a][sfx]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.93[mix]",
               "-map","[mix]","-ar","48000","-ac","2",out)
            soundtrack=out
        if a.foley and a.topic=="siege" and (a.foley/"low-impact-boom.ogg").exists():
            out=root/"sound.wav"
            ff("-i",voice,"-i",a.foley/"low-impact-boom.ogg",
               "-filter_complex","[1:a]asplit=2[boom_src_1][boom_src_2];"
                                 "[boom_src_1]aresample=48000,volume=0.13,adelay=9500:all=1[boom1];"
                                 "[boom_src_2]aresample=48000,volume=0.10,adelay=10900:all=1[boom2];"
                                 "[0:a][boom1][boom2]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.93[mix]",
               "-map","[mix]","-ar","48000","-ac","2",out)
            soundtrack=out
        # Never speed audio without changing the *corresponding visual chapter*.
        vfilters=";".join(
            f"[0:v]trim=start={i*6}:end={(i+1)*6},setpts=(PTS-STARTPTS)*{slot/6:.9f},fps=30,format=yuv420p[v{i}]"
            for i,slot in enumerate(slots)
        )+";"+''.join(f"[v{i}]" for i in range(6))+"concat=n=6:v=1:a=0[video]"
        ff("-i",a.video,"-i",soundtrack,"-filter_complex",vfilters,
           "-map","[video]","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","22",
           "-maxrate","4200k","-bufsize","8400k","-pix_fmt","yuv420p","-r","30",
           "-c:a","aac","-b:a","160k","-ar","48000","-ac","2","-movflags","+faststart",
           "-t",f"{total:.5f}",a.output)
    probe=json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration",
         "-show_entries","stream=codec_type,width,height,r_frame_rate,channels,sample_rate","-of","json",str(a.output)]))
    video=next(x for x in probe["streams"] if x["codec_type"]=="video")
    audio=next(x for x in probe["streams"] if x["codec_type"]=="audio")
    assert (video["width"],video["height"])==(720,1280)
    assert video["r_frame_rate"]=="30/1"
    assert audio["channels"]==2 and int(audio["sample_rate"])==48000
    assert abs(float(probe["format"]["duration"])-total)<0.2
    meter=subprocess.run(["ffmpeg","-hide_banner","-loglevel","info","-i",str(a.output),
        "-af","silencedetect=noise=-37dB:d=0.85","-f","null","-"],
        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,check=True)
    bad=[line.strip() for line in meter.stderr.splitlines() if "silence_duration:" in line]
    if bad:raise RuntimeError("Long dead air in fast history cut: "+"; ".join(bad))
    a.output.with_suffix(".quality.json").write_text(json.dumps(
        {"seconds":total,"shot_chapters":report,"video":video,"audio":audio,
         "status":"review-only—not-approved-for-publication"},indent=2))
    print("FAST_QWEN_PITCH_PRESERVED_SHORT",str(a.output),"seconds",total)
if __name__=="__main__":
    main()
