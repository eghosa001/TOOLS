# ASMR visual-to-audio causal match gate — mandatory

**Introduced 2026-11-02 after explicit user rejection of honey ASMR 30s v1 and v2.**

## What failed (not a speculative cause)

- 0–10s: user-created honeycomb roller source has its own recorded/generated soundtrack, which was preserved.
- 10–20s: licensed Pexels honey jar-to-dipper video is effectively **silent**: its embedded AAC decodes to zeros.
- 20–30s: licensed Pexels thick honey ribbon video contains **no audio stream**.
- Generic *bottle squeeze*, *hands manipulating syrup* and synthetic *honey drizzle* were added at editorial timestamps rather than derived from matched actions in actual original footage. Their textures and transients did not correspond to those visible.
- Technical QA checked codec, frame count, silence, loudness and peak. None proves semantic audio-to-video correspondence. The creative result was explicitly rejected twice.

## Required before creating further ASMR releases

1. **Verify source audio for every shot, not just stream presence.** Decode samples and report whether they contain nonzero signal; a silent AAC track is still a silent source. Do this before committing to a 30-second format.
2. **Source-first sound policy:** Favor video with its own synchronized, commercially usable source sound. Otherwise obtain material- and gesture-matched legally reusable recordings (not only filenames or tags that share a keyword with the pictured substance). If neither is available, mark *not release-ready*; do not disguise absent sound with unrelated Foley.
3. **Explicit sound-event map:** For each shot record the exact visual onset/offset and material contact; classify continuous flow separately from transient impact. Do not schedule a prominent isolated squish when only uninterrupted slow honey flow is visible.
4. **Do not force audio** with invented sound to satisfy a no-silence metric. Physically quiet actions may naturally be quiet. First solve picture/material audio correspondence.
5. **Human listening/visual review gate:** Check headphones while watching the exact master, with scene-by-scene source comparison, alongside user-supplied ASMR references; log any discrepancies and refuse quality approval until resolved. An automated test may support, but cannot replace, this judgment.
6. **Prior rejected sources are blocked:** The second/third shots in `honey_30s_foley_visual_sync_recut_v2_2026_11_02.json` are **NOT PUBLISHABLE** with the earlier honey-bottle/syrup-hand/artificial-drizzle substitutions. Do not repackage or relabel them as approved.
7. **Preserve provenance:** Retain license, source URL, credits and edit/recording facts. Never claim original synchronized location sound from stock footage when there was none.
8. **Delivery language:** State separately (a) technical export status, (b) editorial A/V-sync status and (c) user approval. Never say 'sound is synchronized' merely because continuous audio exists.

## Next acceptable honey production route

Retain the user's first 10-second honeycomb roller shot if desired. Source two different 10-second honey actions that include usable *native* material-correct sound, or arrange newly recorded Foley matching the actions and exact final frames. Reject the composite if no such authentic evidence exists. Do not fabricate a 'premium' 30-second completion with substitute squeaks or splashes.

**This is a hard quality gate, not a plan to perform work later.**
