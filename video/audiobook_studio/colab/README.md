# Eternal Dao — Google Colab illustration generator

Open this notebook in Google Colab; select **Runtime → Change runtime type → T4 GPU**; then **Runtime → Run all**.

It privately reads the owner's approved Episode 1 script and 24-beat storyboard from Google Docs, expands them into roughly 200 source-linked visual shots, and generates each image using the free-tier-friendly [SDXL-Lightning](https://huggingface.co/ByteDance/SDXL-Lightning) 4-step LoRA with Diffusers. Original illustrations are saved directly to the existing private Google Drive Episode 1 folder. No images are shown in the notebook or ChatGPT, and no user approval is needed.

**Free Colab does not guarantee GPU access or a complete session.** Existing correctly saved PNGs are skipped on reruns. The first run downloads the model; initial startup is substantially slower than generating subsequent frames. Actual speed depends on Colab's assigned GPU and runtime availability.

The original 24 storyboard entries are **macro-beats, not a 24-picture limit**. The complete source is split into short ~18-word passages, typically 180–250 different frames, with a 5–8-second visual cadence when timed to narration. This notebook generates an Episode 1 illustration library only. The repository's separate **complete-novel illustration-first gate** must still pass before final video compilation.

No Kaggle. No paid image API. No unpublished manuscript text or images are committed to GitHub.
