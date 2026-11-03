# Facts Uncovered pilot — San Francisco, April 1906

This project produced one 65.8-second 1080p historical video exclusively from genuine camera footage, without AI-generated images, CGI, synthetic film or animated still-image substitutes.

## Original footage

- **Before the earthquake:** Miles Brothers, *A Trip down Market Street*, shot 14 April 1906. [Library of Congress](https://www.loc.gov/item/00694408/) and [original Wikimedia film record](https://commons.wikimedia.org/wiki/File:A_Trip_down_market_street_(1906).webm).
- **After the earthquake:** *San Francisco Earthquake aftermath, 1906*, genuine archival period camera footage, [Wikimedia film record and public-domain rights](https://commons.wikimedia.org/wiki/File:San_Francisco_Earthquake_aftermath,_1906.ogv).

The script uses original commentary on surviving period footage. Commercial reuse permission must always be rechecked at its item-level source before publication, and YouTube reused-content eligibility is a separate assessment. Both videos passed the motion and source-rights validator during the documented run.

## Production record

- First complete artifact: [successful workflow run 41639188982](https://github.com/eghosa001/TOOLS/actions/runs/41639188982).
- Revised soundtrack and readable captions: [successful workflow run 41640507292](https://github.com/eghosa001/TOOLS/actions/runs/41640507292).
- Revised 1080p H.264 MP4 SHA-256: `998272843c19f68f4c7444dbf2bd1ca26d2d8a2bd8a8ac4b90dacaad16a663eb`.
- Duration 65.8 seconds, eight storyboard beats, 100% authentic moving-image runtime, original Kokoro narration, ~−17 LUFS integrated audio, short readable subtitle cues, actual-film thumbnail and machine-readable rights ledgers.

To render a later variant, run `python video/history_studio/productions/sf1906_real/produce.py --media archive --output delivery --model models/kokoro-v1.0.onnx --voices models/voices-v1.0.bin` in an FFmpeg-equipped environment with Kokoro-onnx, soundfile and NumPy installed. The script downloads real footage only and fails closed if source files cannot be verified. Archive mirrors can be used only with explicit public-domain evidence.

The job that produced this film was a **one-off pilot workflow**, intentionally removed from the active workflow directory after successful export to retain the single canonical historical production entrypoint: `.github/workflows/facts-uncovered-real-only-assembly.yml`. The one-off workflow and logs remain retrievable from Git history and the linked successful Actions run.

The delivered MP4 is a **review copy**, not published on YouTube. The stored source ledgers intentionally mark final public release approval as pending, and no OAuth credentials or ASMR projects were modified.
