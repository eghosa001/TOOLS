# Four natural ASMR Foley scenes — reuse Ninefold Kaggle automation

**Scope:** Four existing six-second video previews (embers, candle, water ripples, ink clouds); environmental audio only. No soundtrack, no speech, no unrelated render pipelines.

This uses the same **GitHub Actions → Kaggle → verified WAV artifacts** infrastructure as Ninefold Tide's successful open-source Qwen3-TTS voice casting, but **not the Qwen3-TTS weights**. Qwen3-TTS is a voice/speech model and does not correctly model charcoal crackling or liquid. For truthful, commercially usable environmental audio, the open-source `Stable Audio 3 Small-SFX` model from `Stability-AI/stable-audio-3` is used. Small-SFX can run on CPU and requires no paid API key or Kaggle GPU quota. The Community License permits qualifying commercial use under the $1M revenue rule; check rights before publishing.

The model-generated 20s 44.1kHz stereo PCM master is retained without edits; 6s 48kHz mastered review WAVs are derived for the matching videos. Original MP4 visuals do not need re-rendering. The candle and ink scenes intentionally stay nearly silent. Machine checks do not constitute human acoustic approval. No output is claimed until actual Kaggle logs, status, hashes, and WAV files verify.

**Source:** https://github.com/Stability-AI/stable-audio-3 (see optimized/tflite; `./sa3 --dit sm-sfx --decoder same-s`). The model files are retrieved inside Kaggle; users do not download model weights to their phones.

**Private Kaggle kernel:** `aighewieghosa/asmr-real-foley-four-20261031`. The GitHub workflow submits once using the existing `KAGGLE_API_TOKEN` secret and collects actual outputs. If Kaggle finishes after the workflow polling horizon, retrieve that same kernel's outputs rather than resubmitting and redownloading weights.
