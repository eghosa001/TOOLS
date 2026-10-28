# Titanic 2026 — sources, footage rights and directorial verification for two Shorts

The two Shorts assembled by `render_two_directed_shorts.py` use **only our original vector/motion-graphic images** and newly synthesized Kokoro narration. No film clips from National Geographic, BBC, British Pathé, 1997 Titanic, commercial galleries, Woods Hole or RMS Titanic, Inc. are reproduced. All original reconstructions are identified as illustrations on screen.

## Short 01 — verified statements

| Narration claim | Evidence | Editorial handling |
|---|---|---|
| Titanic carried twenty lifeboats | 1912 British Wreck Commissioner's Report, Boats | Original 20-boat schematic, not claimed to show exact deck arrangement |
| The British report lists 2,201 aboard | British Wreck Commissioner's Report, survivors/total | Explicitly attribute count to British report; other compilations vary |
| 1,178 rated spaces; 14 lifeboats, 2 emergency, 4 collapsibles | 1912 British Report 'Account of the Saving and Rescue', 14×65, 2×40, 4×47 | Original numerically accurate infographic |
| At least 1,023 lacked rated boat places | 2,201 − 1,178 = 1,023 | Theoretical capacity comparison; do not imply all capacities were practically fillable |
| Several boats left partly empty | British report mentions Boat 1 carrying 12/40, Boat 7 carrying 27/65 | Original explicit bar charts. Do not use photo of boat approaching Carpathia as evidence of launch occupancy |

Verified source: https://www.titanicinquiry.org/BOTInq/BOTReport/BOTRepBoats.php
Survivor counts: https://www.titanicinquiry.org/BOTInq/BOTReport/botRepSaved.php

## Short 02 — verified statements

| Narration claim | Evidence | Editorial handling |
|---|---|---|
| A 15-foot port-side bow railing section was missing in 2024 | RMS Titanic, Inc., Expedition 2024 | Clearly labelled original port-side schematic, **NOT expedition footage** |
| The Diana of Versailles statuette was rediscovered | RMS Titanic, Inc. Expedition 2024 | Original silhouette explicitly labelled illustrative |
| Detailed digital survey 2022; public documentary 2025 | NatGeo / Magellan 2025 press coverage | Timeline only; never reproduce restricted images |
| Wreck continues to change | Expedition 2024 photographs and comparison with prior surveys | Original illustrative before/after panels, no unverified measurements |

Expedition source: https://rmstitanicinc.com/titanic-expeditions/
2025 presentation: https://www.dgepress.com/natgeo/pressrelease/national-geographic-reveals-groundbreaking-underwater-scan-unveiling-titanic-in-unprecedented-detail-challenging-long-held-theories-and-presenting-fresh-insights-in-upcoming-documentary-special-titan/

## Asset and licence

| Asset type | Source | Commercial considerations |
|---|---|---|
| Every graphic and labelled original diagram | Hand-directed original Pillow image drawing in `render_two_directed_shorts.py` | Original production, no third-party photo footage |
| Narration | Kokoro-ONNX / Kokoro-82M `am_michael` | Kokoro model Apache-2.0: https://huggingface.co/hexgrad/Kokoro-82M ; check installed version model card |
| Fonts | DejaVu Sans / Serif from Ubuntu distro | Free licence, separate from film footage |
| Sound | Original generated speech; no background soundtrack | No unlicensed commercial music |
| Captions | Manually authored text grouped at exact individually generated narration segment boundaries | SRT contains actual audio-based shot in/out, NOT claim of word-level forced alignment |

## Final release restrictions

- The MP4(s) are **review candidates** until actual fully viewed and listened to, including every transition, music (if later added), captions and exact final seconds.
- Final verdict on picture sharpness, content, timing, delivery and audio must not be inferred from successful FFmpeg execution.
- Both Shorts have separately written narration, different facts and individualized portrait compositions.
- No YouTube upload before an approved main documentary is available to link.
