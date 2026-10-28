#!/usr/bin/env python3
"""15 individually assigned original Titanic ambience cues, not third-party music.

Generate low-level harmonic atmospheric score with distinct thematic moods for
each researched chapter. Original sine/additive composition is not historical
recording. Keep music subordinate to documentary voice, preserve picture pixels.
"""
from __future__ import annotations
import pathlib,math,json,hashlib,subprocess
import numpy as np
import soundfile as sf
ROOT=pathlib.Path(__file__).resolve().parent
TIMING=ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json"
FILMS=ROOT/"master_review_export"
OUT=ROOT/"scored_master_review";OUT.mkdir(exist_ok=True)
# Director-selected sonorities; frequencies are new original generative tone-bed,
# not a transcription, recording or adaptation of existing commercial music.
CUES=[
 ("silent-horizon",55.00, [1.,1.2,1.5],.0080),
 ("industrial-belfast",65.41,[1.,1.25,1.5],.0072),
 ("people-and-journeys",58.27,[1.,1.25,1.498],.0070),
 ("lifeboat-warning",55.0,[1.,1.20,1.498],.0070),
 ("ice-messages",61.74,[1.,1.2,1.5],.0080),
 ("impact",51.91,[1.,1.189,1.498],.0090),
 ("progressive-flooding",55.0,[1.,1.189,1.5],.0080),
 ("wireless-call",65.41,[1.,1.25,1.5],.0067),
 ("lifeboat-launch",58.27,[1.,1.20,1.498],.0070),
 ("the-human-cost",55,[1.,1.189,1.5],.0061),
 ("final-minutes",51.91,[1.,1.20,1.498],.0092),
 ("rescue",65.41,[1.,1.25,1.498],.0070),
 ("inquiry",58.27,[1.,1.25,1.5],.0060),
 ("1985-discovery",69.30,[1.,1.25,1.5],.0062),
 ("meaning-and-memorial",55.0,[1.,1.25,1.498],.0063)
]
def run(args):
    return subprocess.run([str(x) for x in args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def info(path):
    return json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",path]).stdout)
def synthesize(chapter_lengths,rate=24000):
    audio=OUT/"original_titanic_atmospheric_score.wav"
    with sf.SoundFile(audio,"w",samplerate=rate,channels=1,subtype="PCM_16") as wav:
        for i,seconds in enumerate(chapter_lengths):
            title,root,ratios,volume=CUES[i]
            count=round(seconds*rate);written=0
            while written<count:
                n=min(2*rate,count-written)
                time=(written+np.arange(n,dtype=np.float64))/rate
                amp=np.minimum(1.0,np.minimum(time/6,np.maximum(0,(seconds-time)/7)))
                # Restrained pad with slight moving harmonics; no fabricated environmental SFX.
                mix=np.zeros(n,dtype=np.float64)
                for j,multiple in enumerate(ratios):
                    freq=root*multiple
                    phase=2*np.pi*freq*time+math.sin(i*2.2+j)*.4
                    mix+=np.sin(phase)*(0.53 if j==0 else (0.26 if j==1 else .16))
                    mix+=.09*np.sin(phase*2.01)
                slow=.86+.14*np.sin(2*np.pi*time/31+i)
                chunk=(mix*amp*slow*volume).astype(np.float32)
                wav.write(chunk)
                written+=n
            print("ORIGINAL_AMBIENCE_CHAPTER",i+1,title,round(seconds,2),flush=True)
    return audio
def main():
    timing=json.loads(TIMING.read_text())
    film=FILMS/"TITANIC_COMPLETE_15_CHAPTERS_1080P_24FPS_EDITORIAL_REVIEW.mp4"
    original_info=info(film)
    duration=float(original_info["format"]["duration"])
    keys=[timing["chapters"][str(i)] for i in range(1,16)]
    lengths=[float(k["end_seconds"])-float(k["start_seconds"]) for k in keys]
    assert abs(sum(lengths)-timing["runtime_seconds"])<.1
    ambient=synthesize(lengths)
    scored=OUT/"TITANIC_15CHAPTERS_1080P_24FPS_ORIGINAL_SCORE_REVIEW.mp4"
    filt="[1:a]volume=1.0[score];[0:a][score]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1:LRA=9[mixed]"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",film,"-i",ambient,
      "-filter_complex",filt,"-map","0:v:0","-map","[mixed]","-c:v","copy",
      "-c:a","aac","-b:a","256k","-ar","48000","-ac","2",
      "-movflags","+faststart",scored])
    ff=info(scored)
    assert abs(float(ff["format"]["duration"])-duration)<.3
    v=next(q for q in ff["streams"] if q["codec_type"]=="video")
    a=next(q for q in ff["streams"] if q["codec_type"]=="audio")
    assert (v["width"],v["height"])==(1920,1080) and v["codec_name"]=="h264"
    assert a["codec_name"]=="aac"
    run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",scored,"-f","null","-"])
    hash=hashlib.sha256()
    with scored.open("rb") as f:
        while block:=f.read(1048576):hash.update(block)
    report={"filename":scored.name,"bytes":scored.stat().st_size,
       "duration_seconds":float(ff["format"]["duration"]),
       "sha256":hash.hexdigest(),"audio": "original additive low-level per-chapter score + Kokoro dialogue, normalized to target -16 LUFS",
       "score_cues":[{"chapter":i+1,"name":a[0],"seconds":round(lengths[i],2)} for i,a in enumerate(CUES)],
       "original_score_composed_in_repository":True,
       "third_party_music":False,"picture_stream_reencoded":False,
       "full_decode":"PASS","subjective_music_and_dialogue_listening_review":"PENDING",
       "exact_loudness_measurement":"PENDING separate EBU R128 scan",
       "commercial_archival_photograph_final_editor_clearance":"PENDING",
       "publication_approved":False,"published_to_youtube":False}
    (OUT/"ORIGINAL_SCORE_AUDIO_QA.json").write_text(json.dumps(report,indent=2))
    print("ORIGINAL_SCORED_TITANIC_86MIN_FILM_EXPORTED_REVIEW_ONLY",json.dumps({"duration":report["duration_seconds"],"bytes":report["bytes"],"sha256":report["sha256"]}),flush=True)
if __name__=="__main__":main()
