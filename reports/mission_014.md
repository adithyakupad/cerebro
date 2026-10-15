# Mission 014: observed extensions and reproducibility

The new LINK date and FALCON recording extend empirical coverage. Results remain exploratory: calibration helps in some settings; broad representation-learning benefit is not established. Historical reports are preserved.

## LINK Jan27 → Feb05: full referenced trials

Source300 fit/75 evaluation; target75 calibration/300 evaluation;96 matched contacts. Source-only selection chooses ridge alpha1000.0. Native index/MRS positions are measured in flexion units.

| Control | Target label trials | Mean trial MSE (flexion²) |
|---|---:|---:|
| frozen_source | 0 | 0.03340539 |
| source_mean | 0 | 0.02606807 |
| target_calibration_mean_1 | 1 | 0.03018033 |
| direct_recalibration_1 | 1 | 0.02954400 |
| source_plus_residual_1 | 1 | 0.03017930 |
| target_calibration_mean_5 | 5 | 0.04465479 |
| direct_recalibration_5 | 5 | 0.04500851 |
| source_plus_residual_5 | 5 | 0.04294100 |
| target_calibration_mean_15 | 15 | 0.02725018 |
| direct_recalibration_15 | 15 | 0.02758294 |
| source_plus_residual_15 | 15 | 0.02767892 |
| target_calibration_mean_50 | 50 | 0.02717066 |
| direct_recalibration_50 | 50 | 0.02576537 |
| source_plus_residual_50 | 50 | 0.02589903 |
| target_calibration_mean_75 | 75 | 0.02632579 |
| direct_recalibration_75 | 75 | 0.02482701 |
| source_plus_residual_75 | 75 | 0.02494256 |

Frozen source exceeds the source mean by 0.00733732 flexion². At75 labels, direct ridge improves over the budget-matched calibration mean by -0.00149878; residual transfer is 0.00011555 worse than direct ridge. One/five/fifteen-label outcomes are mixed or poor; report the full curve rather than selecting a favorable budget.

## LINK representation: Jan27+Jan30 → Feb05

Three source-only SSL fits and42 decoder fits use seeds0/1/2. The two source sessions supply600 SSL trials;150 reserved source trials support six identity diagnostics. Target75 calibration/300 evaluation; all trials are restricted to their first40 native samples. This outcome differs from the full referenced-trial classical result above.

| Comparison | Target label trials | Pretrained MSE | Matched random MSE | Difference (flexion²) |
|---|---:|---:|---:|---:|
| pretrained_zero_shot vs random_zero_shot | 0 | 0.02439402 | 0.02442170 | -0.00002768 |
| pretrained_frozen_ridge vs random_frozen_ridge | 5 | 0.04467983 | 0.04447695 | 0.00020287 |
| pretrained_frozen_ridge vs random_frozen_ridge | 15 | 0.02822393 | 0.02817184 | 0.00005209 |
| pretrained_frozen_ridge vs random_frozen_ridge | 75 | 0.02314409 | 0.02315151 | -0.00000741 |
| pretrained_finetuned vs random_supervised_only | 5 | 0.03800501 | 0.03800536 | -0.00000034 |
| pretrained_finetuned vs random_supervised_only | 15 | 0.02597135 | 0.02604395 | -0.00007260 |
| pretrained_finetuned vs random_supervised_only | 75 | 0.02431516 | 0.02438485 | -0.00006969 |

Differences are small and mixed. Frozen pretrained probes are slightly worse at5/15 labels;75-label and fine-tuned results show small numerical differences. This does not establish a general SSL benefit. Session identity remains readily decodable: pretrained98.0%; random97.33–98.0% across seeds.

## FALCON MonkeyL → MonkeyX (new target recording)

Seven anonymous count moments predict16 exact shared muscle-name coordinates. Source300 fit/112 evaluation; target75 calibration-pool/371 eligible evaluation trials. This is a custom chronological analysis of author-normalized EMG, not an official FALCON score or calibrated absolute amplitude.

| Target control | Label trials | Mean trial MSE (normalized EMG²) |
|---|---:|---:|
| source_frozen | 0 | 0.18574543 |
| source_mean | 0 | 0.19012762 |
| target_calibration_mean | 5 | 0.12917018 |
| target_direct | 5 | 0.08043794 |
| source_plus_residual | 5 | 0.07993973 |
| target_calibration_mean | 15 | 0.12860984 |
| target_direct | 15 | 0.07838997 |
| source_plus_residual | 15 | 0.07832202 |
| target_calibration_mean | 75 | 0.12855570 |
| target_direct | 75 | 0.07758839 |
| source_plus_residual | 75 | 0.07761732 |

source_frozen minus source_mean (0 labels): -0.00438219; five-trial paired block band [-0.00661792, -0.00234746].

target_direct minus target_calibration_mean (75 labels): -0.05096732; five-trial paired block band [-0.05333711, -0.04898398].

source_plus_residual minus target_calibration_mean (75 labels): -0.05093838; five-trial paired block band [-0.05329705, -0.04893704].

source_plus_residual minus target_direct (75 labels): 0.00002894; five-trial paired block band [-0.00002854, 0.00007885].

Residual transfer does not improve over direct target ridge at75 labels. The measured neural-feature benefit over the target mean does not remove upstream preprocessing and subject/session confounds. See [complete cross-subject protocol](cross_subject_14.md) and its existing calibration figure.

## Fresh-clone numerical comparison

PASS across 11 experiments: 100,827 scientific numeric values and 526 shared arrays (44,367,047 elements). Maximum observed numerical difference is0, stricter than the declared rtol1e-8/atol1e-10. All46 logged fresh workflow commands exited0. The fresh longitudinal_08 run adds five calibration-mean metric groups and ten arrays; its shared historical outputs remain exact.

Bytewise report/checkpoint identity is not required: revisions, provenance hashes, and serialization metadata can differ. The comparison checks stored outputs; fresh execution evidence is in [mission_014_reproduction.json](../docs/development/mission_014_reproduction.json). It does not establish platform-independent determinism or scientific validity.

## Limits and artifacts

Paired differences and descriptive five-trial block bands for every named contrast are in [mission_014.json](mission_014.json). Negative differences favor the first method. Seeds are averaged within trial; bands are not calibrated population confidence intervals, significance tests, or independent biological replication. No model reruns, tuning, or test-based selection were performed while preparing this report.

Raw/checkpoint/prediction files remain ignored. New complete report snapshots: [longitudinal_14.json](longitudinal_14.json), [representation_14.json](representation_14.json), [cross_subject_14.json](cross_subject_14.json).

Key limits: one LINK animal and contact mapping without neuron identity; count-unit ambiguity, jittered native clocks and excluded reference endpoints; FALCON full-recording author filtering/quantile normalization predating our splits; mutable draft target pinned by UUID/checksum; one recording per animal confounding subject/session/date. No neural foundation-model or real-time biological-control claim follows from these results.
