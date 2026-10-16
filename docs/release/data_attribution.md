# Data attribution and redistribution

CEREBRO source code is MIT licensed. This does not relicense recordings. Raw data, large derived arrays, trained checkpoints and archives remain local and are not GitHub release attachments. The release contains code, small aggregate scientific reports and attributed figures.

| Source | Authoritative identity and attribution | Terms / qualification |
|---|---|---|
| MC_Maze Small | Churchland and Kaufman; [DANDI 000140 v0.220113.0408](https://doi.org/10.48324/dandi.000140/0.220113.0408); [manifest](../../configs/mc_maze_small.json) | CC-BY-4.0; cite dataset and NLB |
| MC_Maze standard | [DANDI 000128](https://dandiarchive.org/dandiset/000128); exact release/asset/checksum in [manifest](../../configs/mc_maze.json) | CC-BY-4.0; native/event feasibility use, not Small decoder evidence |
| LINK | Temmar and colleagues; [DANDI 001201 v0.251023.2336](https://dandiarchive.org/dandiset/001201/0.251023.2336); `configs/link_*.json` | CC-BY-4.0; original clocks and labels retained |
| FALCON M1 | [native source and attribution](../datasets/falcon_multisubject.md), `configs/falcon_*.json` | CC-BY-4.0 source metadata; author-preprocessed EMG remains exploratory; draft asset mutation guarded by checksum |
| Perich–Miller | [source audit](../datasets/longitudinal_feasibility.md), `configs/perich_*.json` | Source terms recorded in manifests; audit-only, no neural coverage fabricated |
| Brochier et al. (2018) | [Scientific Data paper](https://doi.org/10.1038/sdata.2018.55), [native data DOI](https://doi.org/10.12751/g-node.f83565), [exact original asset hashes](../datasets/mission_019_brochier_assets.json) | ZIP-root text says CC-BY-4.0; bundled `datasets/LICENSE.txt` contains CC-BY-SA-4.0. Preserve both, seek publisher clarification before raw-data redistribution. Public acquisition is source-hosted; the release redistributes no native files. |

The [native Brochier audit](../datasets/mission_019_brochier.md) pins both license texts. Aggregate reports and figures identify the source and transformations; no recording ownership or permission to redistribute original data is implied. Cite original publications and dataset versions separately from the CEREBRO software citation.
