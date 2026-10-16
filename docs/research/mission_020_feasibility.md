# Mission 020 Brochier population-analysis feasibility

This audit precedes any Mission 020 population outcome. It uses the SHA-256-pinned [native assets](../datasets/mission_019_brochier_assets.json), [Mission 019 native coverage report](../../reports/mission_019_brochier_native.json), and source odML trial/event metadata. The [primary data paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5892370/) defines `SR` as release of the table switch after the go cue: a recorded movement-related event, not exact muscle or grasp onset.

| Animal/session | Correct trials by SGLF, SGHF, PGLF, PGHF | Source SUAs | `SR`-aligned [−200,+400) ms neural coverage | `SR−GO-ON` range/median |
|---|---|---:|---:|---|
| L `l101210-001` | 41, 30, 31, 33 | 93 | 135/135; source trial start/stop also contain window | 45.3–411.3 ms / 155.4 ms |
| N `i140703-001` | 35, 36, 35, 36 | 156 | 142/142; source trial start/stop also contain window | 21.7–478.5 ms / 251.6 ms |

The source odML event ticks match digital events in the sorted NEVs, and complete 30 kHz NS5/NS6 sampled blocks establish coverage. The proposed window has thirty complete 20-ms bins. It is event-locked to a table-switch release; the 400-ms post-event window may include different reaches or grasp phases across trials. Sensor calibration is unnecessary for a neural-count description, but no claim about physical force or continuous behavior follows. Condition labels are instructed grip-by-load categories.

All four conditions pass a minimum 20-trial descriptive screen in each animal. At a single condition and time bin, sample residual covariance rank is at most `n−1`: 29–40 for L and 34–35 for N, below the respective 93/156 neural dimensions. Thus pairwise/full high-dimensional residual covariance and intrinsic dimension are **not reliably identified**. The feasible estimands are condition/time mean responses, across-trial count variability, trial-level aggregate correlation and shared-fluctuation summaries, and *descriptive* signal-trajectory dimensionality. Trial-level stratified bootstrap intervals can describe sampling variability conditional on these recordings; they cannot quantify uncertainty across biological subjects or remove trial drift. The analysis must report rank limits and avoid causal connectivity claims.

The native N metadata list 142 correct trials versus 141 in the paper summary; the analysis retains the exact pinned source file and identifies the discrepancy. Source root and bundled dataset license text also conflict; raw files remain local and ignored.
