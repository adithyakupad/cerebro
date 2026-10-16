# Mission 003: empirical neural signal characterization

Source: DANDI 000140 v0.220113.0408, asset `7821971e-c6a4-4568-8773-1bfa205c13f8`.
SHA-256: `dcaf3a524e2b2f65f163ee3b07789b8474bdfc6ca66098bc542ab93dff489884`. CC-BY-4.0; Churchland and Kaufman (2022).

All 100 successful source trials (75 train, 25 val) and 142 units are used.
No model selection, fitting, decoding, or inference of an optimal bin width is performed.

## Observed native coverage

| Bin | Bins | Zero cells | Exposure (s) | Mean unit rate (Hz) | Median temporal Fano | Tail spikes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5ms | 57,522 | 98.4000% | 287.610 | 3.222870 | 0.996023 | 45 |
| 20ms | 14,342 | 93.9164% | 286.840 | 3.222634 | 1.009112 | 407 |
| 50ms | 5,710 | 86.3911% | 285.500 | 3.224316 | 1.059366 | 952 |

## Coverage-controlled comparison

Native grids stop at different endpoints. Matched grids use the same per-trial
endpoints on a shared 100 ms grid (LCM of 5/20/50 ms), removing that confound.
Matched exposure is 283.000 s and retains 129,663 spikes,
excluding 2,006 relative to all source trials at every width.
Mean unit rate is 3.226571 Hz; range 0.137809–12.752650 Hz.
Per-unit retained spikes are identical across widths; pooled rates agree to numerical precision.

| Bin | Matched bins | Zero cells | Median temporal Fano | Mean population count/bin | Population count variance |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5ms | 56,600 | 98.3982% | 0.996033 | 2.290866 | 2.584683 |
| 20ms | 14,150 | 93.9098% | 1.009304 | 9.163463 | 13.756796 |
| 50ms | 5,660 | 86.3857% | 1.061139 | 22.908657 | 52.267499 |

## Definitions, interpretation, and limits

Sparsity is the observed zero-count fraction. Mean rate is spikes / observed seconds.
Binwise counts / duration are unsmoothed rate estimates, not continuous latent rates.
Variance uses ddof=1 across temporal bins; Fano is count variance / mean count.
Zero-mean or fewer-than-two-bin Fano values are null, not evidence of zero variability.

Narrower bins have more zeros; rate differences on native coverage arise from different
retained intervals. Matched rates are invariant while count distributions change.
Bins mix task epochs, conditions, and train/val trials. Temporal Fano values therefore
include nonstationarity and are not repeated-trial noise Fano estimates; near-one
values do not establish Poisson spiking. No significance tests or causal claims are made.
[Churchland et al. (2010)](https://www.nature.com/articles/nn.2501) discusses across-trial variability,
a distinct sampling design from the pooled temporal summaries here.

## Metadata audit

72 prefix-1 and 70 prefix-2 IDs all link to PMd-labeled electrode entries in the original NWB.
The [publisher notes](https://neurallatents.github.io/datasets.html) specify prefix 1 = PMd,
prefix 2 = M1, and +96 for erroneous M1 electrode indices. All 70 +96 candidate links
resolve to M1-labeled entries in this file. Original links, IDs, and locations remain unchanged.
This confirms internal consistency with the published rule, not independent anatomical
localization or unit identity. Physical coordinates and spike-sorting quality remain unresolved.

## Reproduce and inspect

```sh
conda activate cerebro
python -m cerebro.characterize configs/mc_maze_small.json
python -m cerebro.characterize_figures
python -m pytest
```

The JSON contains each unit's histogram, rates, variances, Fano statistics, each trial's
complete-bin/exposure statistics, per-unit/per-trial exclusions, all source/matched
intervals and original metadata comparisons. Serialization has no wall-clock timestamp;
unchanged data, code and environment reproduce identical JSON. Source hashes and
the published foundation revision identify the analysis provenance.

Results JSON SHA-256: `7f0214bf69504bdbcdf8b373e2e1e9f8ffb1668e03fc8bcb6ad5b4bab34c12e6`.

Figures:
- [signal_03_statistics](figures/signal_03_statistics.png)
- [signal_03_rates](figures/signal_03_rates.png)
- [signal_03_sensitivity](figures/signal_03_sensitivity.png)
- [signal_03_exclusions](figures/signal_03_exclusions.png)
- [signal_03_metadata](figures/signal_03_metadata.png)

## Recommended next experiment

After human approval, characterize event-aligned counts within repeated maze conditions
and separate task-epoch changes from across-trial variability. Select alignment events,
condition inclusion/minimum trial counts and exposure policy before implementation.
No PCA, decoding or bin-width optimization against prediction accuracy is proposed here.
