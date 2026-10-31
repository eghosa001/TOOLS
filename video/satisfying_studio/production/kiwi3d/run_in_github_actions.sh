#!/usr/bin/env bash
set -euo pipefail
# Manually triggered cloud-only ASMR technical review render. NOT publish-approved.
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
TMP="${RUNNER_TEMP:-/tmp}"
export ASMR_ASSETS="$ROOT/video/satisfying_studio/production/kiwi3d/assets"
export ASMR_SOFT_FOLEY_DIR="$TMP/asmr-natural-fig"
export SOFT_FOLEY_SOURCE="$ASMR_SOFT_FOLEY_DIR/soft_tomato_cut_CC0.mp3"
export SOFT_FOLEY_OUTPUT="$TMP/asmr-kiwi/approved.wav"
export FRAMES_DIR="$TMP/asmr-kiwi/frames"
export RENDER_W=720 RENDER_H=1280 FRAMES=144
OUT="$TMP/asmr-kiwi/review"
mkdir -p "$ASMR_ASSETS" "$ASMR_SOFT_FOLEY_DIR" "$FRAMES_DIR" "$OUT"
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg xvfb >/dev/null
python -m pip install -q requests numpy scipy soundfile pillow trimesh vtk opencv-python-headless
python "$ROOT/video/satisfying_studio/production/kiwi_acquire.py"
python "$ROOT/video/satisfying_studio/production/acquire_soft_fig_foley.py"
python "$ROOT/video/satisfying_studio/production/kiwi3d/prepare_approved_soft_foley.py"
# Regenerated audio may differ at the PCM LSB under a different SciPy/FFmpeg build.
# Its source input SHA256 and signal transform are checked by the Python script.
sha256sum "$SOFT_FOLEY_OUTPUT" > "$OUT/approved_foley_master.sha256"
xvfb-run -a python "$ROOT/video/satisfying_studio/production/kiwi3d/render_kiwi_3d.py"
count="$(find "$FRAMES_DIR" -maxdepth 1 -name 'frame_*.png' | wc -l)"
[ "$count" -eq 144 ] || { echo "REJECT: $count/144 frames" >&2; exit 2; }
MP4="$OUT/Kiwi_Cut_3D_ASMR_720p_PRIVATE_REVIEW.mp4"
ffmpeg -nostdin -hide_banner -loglevel error -y -framerate 24 \
  -i "$FRAMES_DIR/frame_%03d.png" -i "$SOFT_FOLEY_OUTPUT" \
  -map 0:v:0 -map 1:a:0 -frames:v 144 \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 256k -ar 48000 -ac 2 -t 6 -movflags +faststart "$MP4"
python - "$MP4" <<'PY'
import json,subprocess,sys
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',sys.argv[1]]))
v=next(s for s in p['streams'] if s['codec_type']=='video')
a=next(s for s in p['streams'] if s['codec_type']=='audio')
assert int(v['width'])==720 and int(v['height'])==1280
assert v['r_frame_rate']=='24/1' and int(v.get('nb_frames','144'))==144
assert a['sample_rate']=='48000' and int(a['channels'])==2
assert abs(float(p['format']['duration'])-6.0)<.1
PY
ffmpeg -nostdin -hide_banner -v info -i "$MP4" \
  -af silencedetect=noise=-55dB:d=0.45 -f null - 2>"$OUT/silence_scan.log"
if grep -q silence_start "$OUT/silence_scan.log"; then
  echo 'REJECT: audible silence >0.45 s' >&2;exit 2
fi
sha256sum "$MP4" > "$OUT/master.sha256"
cp "$ASMR_ASSETS/SOURCE_LEDGER.json" "$OUT/POLY_HAVEN_CC0_PROVENANCE.json"
echo 'GENUINE 3D RENDER FINISHED â EDITORIAL/USER VISUAL APPROVAL STILL REQUIRED'
