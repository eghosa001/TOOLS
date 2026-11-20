# Qwen AudioGen — four ASMR natural Foley tests

Isolated audio-only experimental tool for **embers, candle, ripples, and ink**; separate from history/CGI pipelines. Source visuals are locally animated references, **not Qwen video**.

## Model and why

Use Qwen's hosted `qwen-audio-3.1-tts-next` (AudioGen). Qwen3-TTS standard models primarily generate **speech**; do not substitute one for environmental Foley. API documentation: https://docs.qwencloud.com/api-reference/audio-generation

Output: original provider **48 kHz stereo WAV**, retained alongside review MP4. The provider's generated duration may vary. Reject WAVs shorter than 5.75 s rather than loop weak audio to fit six seconds; videos are copied without video re-encode. Each scene has a different target sound level. No music or speech requested. The candle and ink clips are intentionally near-silent because those processes are almost inaudible in reality.

## Access / cost

This specific model is an API service; it **requires an API key**, and usage may be billable. Some eligible Model Studio accounts have introductory free tokens, but that must be confirmed in the account before generation. No key has been provided here; therefore **no real Qwen audio has yet been created**. Never paste API keys into public code, chat, or artifacts.

For the optional GitHub Actions workflow, add `DASHSCOPE_API_KEY` to **eghosa001/TOOLS → Settings → Secrets and variables → Actions**. Run the workflow manually, selecting `YES` **only after verifying remaining free Qwen audio-generation quota**. There is intentionally no push/scheduled trigger.

## Cloud audio-only (does not require video files or GPU)

```bash
python video/ai_asmr_experiments/qwen_audio_f4/qwen_asmr_audio.py --audio-only --generate --out-dir ./out/qwen
```

The result is four Qwen WAV recordings as a GitHub Actions artifact. GitHub runner's `ffmpeg` and Python standard library are sufficient. Later download the WAV files and review their content. Model-generated sounds can be inappropriate even when technically valid.

## Combine Qwen WAVs with the existing four MP4s

With the MP4s in a directory (named `embers_asmr_motion_test_720p.mp4`, `candle_...`, `ripples_...`, `ink_...`), and the four original Qwen WAVs in a second directory:

```bash
python qwen_asmr_audio.py --mux-only --source-dir ./asmr_four_tests --out-dir ./out/qwen
```

Alternatively `--generate --source-dir ... --out-dir ...` both generates and muxes in one run, where Qwen API access is available. To inspect planned sounds with zero API calls: `python qwen_asmr_audio.py`.

**Approval gate:** listening check for acoustic realism, no speech/music hallucinations, consistency with visual events, no clicks/clipping and appropriate low level in nearly silent scenes. No auto-publishing. Do not label procedural audio as Qwen-generated.
