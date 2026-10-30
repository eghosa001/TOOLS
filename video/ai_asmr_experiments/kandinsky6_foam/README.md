# Kandinsky 6 Lite — 5-second foam compression test

**Proposed YouTube title (not published):** Turquoise Foam Compression ASMR | Slow Satisfying Rebound (5s Pilot)

- Origin of genre: existing 47-item Satisfying Studio catalogue, format \`foam-squeezing\`.
- This is an ISOLATED **AI video experiment**, not the repository's Blender/CGI production line. Do not change CGI-only manifests, quality gates, published videos, or the history pipeline.
- Uses ONLY \`kandinskylab/Kandinsky-6.0-Lite-distill-5s-Diffusers\` (3B, 10 inference steps, 5s), and the official Diffusers Kandinsky6TI2VAPipeline.
- GPU: free Kaggle Notebook, selected by Kaggle; on T4 GPU FP16 is experimental, since the official benchmarks did not test the T4. Requires >29 GiB free ephemeral scratch and ~25 GiB RAM.
- Output: real 121-frame 480x864, 24fps video with model-generated synced audio, then measured loudness normalization. Do not invent a successful MP4 if inference fails.
- Input: text-to-video by default; image-to-video only when a real foam_reference.png is staged in /kaggle/working, never use a fabricated photo as evidence of a final render.
- Strictly one generation, no looping, no replacements with weak models, no paid provider, no silent CGI fallback, no auto-publish.
- Technical render remains **UNAPPROVED** until an actual visual/audio inspection. Check deformation, original shape recovery, press geometry, image stability, tactile texture, Foley synchrony and dynamics. QA requires the full exact master against original quality criteria.
- Submit and collect via \`.github/workflows/asmr-kandinsky6-foam-kaggle.yml\`, which uses the existing \`KAGGLE_API_TOKEN\` GitHub secret. Check the workflow's artifacts and the Kaggle notebook.
- The Github action may finish before Kaggle generation if model download/offload is slow. If that happens, retrieve the existing Kaggle kernel result, do not submit another run automatically.

Official instructions: https://github.com/huggingface/diffusers/blob/main/docs/source/en/api/pipelines/kandinsky6.md
