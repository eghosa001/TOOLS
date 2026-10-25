# CartoonStudio proposed supporting cast — design review, not canon

The existing three original heroes are Lelli, Brin and Odo. Their designs, voices and the original 74 dialogue lines remain unchanged. The 12 candidates in [proposed_cast.json](proposed_cast.json) are optional original supporting characters. None is an approved canon relationship, age, established voice or recurring cast member.

| Candidate | Silhouette / costume | Suggested story function |
|---|---|---|
| Tavi | Lavender teardrop, golden cap | Kite maker |
| Miko | Sage barrel, orange apron | Gardener |
| Pippa | Apricot bean, teal scarf | Storyteller |
| Nori | Aqua wide body, yellow glasses | Investigator |
| Kolo | Plum square, copper belt | Tinkerer |
| Suri | Tall yellow, purple crown | Musician |
| Marn | Blue oval, rose bow | Organizer |
| Fen | Compact mint, lilac leaf | Nature watcher |
| Rumi | Tall cinnamon bell, cream vest | Older neighbour |
| Bex | Indigo wide body, orange antennae | Competitive friend |
| Luma | Pink pear, teal flower | Painter |
| Zaza | Green teardrop, pink tufts | Dancer |

## Deliverables after workflow success

The separate Blender workflow exports twelve individual character GLB meshes, a static 1200x900 cast-comparison PNG and a capability manifest. A binary GLB verifier checks exported mesh and facial blendshape targets before uploading the artifact. The workflow does not start Kaggle, edit episode story data, assign voice models or change the Series Bible.

These are low-poly concept prototypes with basic pivot gestures and mouth/smile/blink blendshapes, not professional rigged characters. The existing Kenney and Quaternius skeletal motions cannot be directly applied without matching bone structures and retargeting tests. The 2K material/HDRI packs improve scenery and lighting but cannot solve missing rigging.

For a long-running series, use two to four speaking characters per episode and introduce proposed neighbours gradually, only after reviewing their silhouettes and approving the intended lasting identities. Keep the original leads recognizable. High output volume alone cannot guarantee monetization; stories must be original and non-repetitive.

[Optional expanded cast build](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-expanded-cast.yml)
