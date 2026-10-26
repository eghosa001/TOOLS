#!/usr/bin/env python3
"""Synthetic-only regression cases for the CartoonStudio MP4 acceptance gate.

These are intentionally NOT cartoon episode renders; FFmpeg generates
colored technical test patterns to exercise validation failure paths.
"""
import subprocess
import tempfile
from pathlib import Path
from cartoonstudio_video_delivery_gate import verify


def clip(out,seconds=3,width=1280,height=720,*,audio=True,silent=False):
    args=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
          "-f","lavfi","-i",f"color=c=blue:s={width}x{height}:r=24"]
    if audio:
        args+=["-f","lavfi","-i",
               "anullsrc=r=48000:cl=mono" if silent else "sine=frequency=600:sample_rate=48000"]
    args+=["-t",str(seconds),"-c:v","libx264","-threads","2","-pix_fmt","yuv420p"]
    if audio:args+=["-c:a","aac","-b:a","128k","-shortest"]
    else:args+=["-an"]
    args+=[str(out)]
    subprocess.run(args,check=True,timeout=80)


def main():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        correct=root/"correct.mp4"
        clip(correct)
        report=verify(correct,"preview")
        assert report["passed"],report
        assert "FULL_MOVIE_TOO_SHORT" in verify(correct,"full")["errors"]
        wrong_size=root/"wrong-size.mp4"
        clip(wrong_size,width=640,height=360)
        assert "WRONG_1280X720_RESOLUTION" in verify(wrong_size,"preview")["errors"]
        no_audio=root/"no-audio.mp4"
        clip(no_audio,audio=False)
        assert "AUDIO_STREAM_MISSING" in verify(no_audio,"preview")["errors"]
        silence=root/"silence.mp4"
        clip(silence,silent=True)
        assert "AUDIO_IS_SILENT_OR_INAUDIBLE" in verify(silence,"preview")["errors"]
        too_short=root/"too-short.mp4"
        clip(too_short,seconds=2)
        assert "PREVIEW_NOT_THREE_SECONDS" in verify(too_short,"preview")["errors"]
        absent=verify(root/"missing.mp4","preview")
        assert not absent["passed"] and "MISSING_ACTUAL_MP4" in absent["errors"]
    print("PASS: real decoded H264 1280x720/24fps/AAC 3-second technical test pattern")
    print("PASS: missing audio, silence, wrong resolution, duration, absent MP4 and premature full blocked")


if __name__=="__main__":
    main()
