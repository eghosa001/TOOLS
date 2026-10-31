# 3D Shorts — catalogued free assets and sound engine

The uploaded examples are **3D** castle explainer Shorts (not 2D). They contain moving perspective views of walls, towers, a moat, soldiers and castle defenses, with vertical text overlays and stereo narration. This project uses their **visual language only**.

| Resource | Direct original source | License / application |
| --- | --- | --- |
| **Kenney Castle Kit** | https://kenney.nl/assets/castle-kit | CC0-1.0; modular castle walls, gate, towers, drawbridge, flag, siege engines. Exact individual GLB mirrors at https://github.com/Hidencod/tge-assets |
| **Kenney Nature Kit** | https://kenney.nl/assets/nature-kit | CC0; isolated trees, grass and rocks |
| **Kenney Mini Characters** | https://kenney.nl/assets/mini-characters | CC0; static stylized GLB characters, **not** usable as animated rigs without further work |
| **Quaternius Medieval Village Pack** | https://quaternius.com/packs/medievalvillage.html | CC0; optional buildings/props |
| **Quaternius Medieval Village MegaKit** | https://quaternius.itch.io/medieval-village-megakit | CC0 base pack; optional ~153 MB (not downloaded by default) |
| **Poly Haven** | https://polyhaven.com/ | CC0; optional stone, grass, sky/HDRI, one reviewed asset at a time |
| **ambientCG** | https://ambientcg.com/ | CC0; optional PBR stone and masonry textures |
| **Rhubarb Lip Sync** | https://github.com/DanielSWolf/rhubarb-lip-sync | MIT code; optional only after actual talking character rigs exist |
| **Qwen3-TTS** | https://github.com/QwenLM/Qwen3-TTS | Apache-2.0 implementation; free on a self-managed GPU or CPU |
| **Qwen3-TTS 0.6B CustomVoice** | https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice | Model card states Apache-2.0; pre-defined speakers incl. English Ryan/Aiden; first download is large (~2.5 GB) |

The Python importer is limited to specifically catalogued Kenney models. It validates the GLB magic and length, caches by asset ID, and writes a SHA256/creator/source/license provenance JSON. It does not pick any model for the director. `assets.json` is the complete selected pack listing; the script downloads only requested IDs unless the user **explicitly** selects `--all`.

License of a **source pack**, model weights, code, sound, and original reference video are different. Do not copy scenes, voices or sound directly from reference videos. CC0 free commercial use does not prove historical accuracy. Any third-party asset added to a real Short needs individual source verification, and publication needs manual image-to-voice matching and sound review.
