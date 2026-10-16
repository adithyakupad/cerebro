# Brochier event-aligned population variability

**Observed native recordings; descriptive within-session analysis.** The [protocol](../docs/research/mission_020_protocol.md) was committed as `d792f182b3f9d3f1dab0cf9ff5a5f41f1f1c547d` before these outcomes were computed. Exact source hashes, trial IDs, event ticks, unit IDs, exclusions, numerical outputs and software versions are in the [machine report](mission_020_brochier_population.json). Source: [Brochier et al. native corpus](https://doi.org/10.12751/g-node.f83565); [native-data audit](../docs/datasets/mission_019_brochier.md).

## Eligibility and measurement

All four grip-by-load conditions passed the ≥20 correct-trial threshold. L contributed 135 trials (SGLF 41, SGHF 30, PGLF 31, PGHF 33) and 93 source-designated single units; N contributed 142 (35, 36, 35, 36) and 156 units. Every included `[SR−0.2,+0.4)` second window was inside its source trial and an authentic 30 kHz sampled neural interval. SR is the **recorded table-switch release**, a task marker after the go cue, not a measured muscle or grasp onset. No smoothing or timestamp interpolation was used. Spike counts have shape L `135×30×93`, N `142×30×156`; each half-open bin spans 600 native ticks, or 20 ms. Rates are counts divided by 0.02 s. The 69 L and 19 N other source trials were excluded because they did not meet the correct-four-condition rule; no eligible trial was excluded for coverage or missing event. Within eligible windows, 157,623 L and 180,424 N source spikes were conserved in bins.

| Within-animal statistic | L | N |
|---|---:|---:|
| Mean unit rate, pre-SR `[-200,0)` ms (spikes/s) | 22.550 | 10.924 |
| Mean unit rate, post-SR `[0,400)` ms (spikes/s) | 20.111 | 14.900 |
| Paired whole-trial post − pre (spikes/s) | −2.439 | +3.976 |
| 300-draw stratified whole-trial bootstrap percentile range for paired change (spikes/s) | [−2.666, −2.236] | [3.837, 4.118] |
| Median 400-ms post-count Fano, cells with mean count ≥1 | 0.853 / 363 cells | 0.962 / 548 cells |
| Condition×time mean-vector participation ratio (descriptive) | 5.239 | 3.163 |
| Median absolute signal-like unit-pair correlation | 0.293 / 4,278 pairs | 0.205 / 12,090 pairs |
| Median absolute post-trial residual unit-pair correlation | 0.070 / 4,278 pairs | 0.068 / 12,090 pairs |
| Residual population-mean variance / diagonal-only reference | 1.449 | 2.077 |
| 200 within-condition independent-unit trial shuffles, ratio 2.5–97.5% | [0.783, 1.282] | [0.781, 1.264] |
| Early / late half residual-sharing ratio | 1.923 / 1.060 | 2.232 / 1.586 |

L and N exhibit opposite event-associated mean-rate changes. They have different units, neural populations, and single recording sessions; no cross-animal difference test or common-neuron inference is made. The residual-sharing ratios exceed the central shuffled references, but the early/late sensitivity and limited biological replication leave their stability unresolved. The signal-like correlation pools four condition × 30 event-time means and mixes task condition with event-time structure. Residual vectors first subtract the **matching condition and time mean**, then average 20 post-SR bins within each trial. Unit pairs and event bins are dependent; pair counts are not independent replicates.

The Fano summary excludes 9 of 372 L and 76 of 624 N condition×unit cells whose mean 400-ms post-SR count is below one; all source-designated single units remain in the other analyses. There were no undefined unit-pair correlations in the reported aggregate matrices, but their numerical finiteness does not make individual pairs reliably estimated.

The condition-specific residual covariance rank ceilings are L 29–40 and N 34–35, far below 93 and 156 units. Full covariance estimation, individual pairwise inference, and reliable high-dimensional residual dimensionality are unsupported. The reported participation ratio instead describes the rank concentration of **condition-mean trajectories** (120 vectors); PCA projections of those means and three fixed trials per condition are descriptive, not held-out dynamical models. The first two descriptive PC variance fractions are L 0.315/0.267 and N 0.532/0.158.

The 300 bootstrap draws resample whole trials within condition and quantify conditional trial sensitivity only. For Fano, median absolute correlation and participation ratio, percentile distributions are visibly biased away from the plug-in estimates; their ranges in the machine report **must not be read as calibrated confidence intervals**. The paired rate-change percentile range is shown as a within-recording descriptive uncertainty summary. Neither bootstrap nor shuffle establishes uncertainty across biological subjects, causal connectivity, or a neural mechanism. Fano values are count variability in a 400-ms task epoch, with possible nonstationarity; they are not intrinsic point-process dispersion.

## Figures and reproduction

- [Condition-aligned population rate, PNG](figures/mission_020_brochier_rates.png) ([vector PDF](figures/mission_020_brochier_rates.pdf)): 20-ms rates and conditional whole-trial bootstrap bands.
- [Fano and pair-correlation distributions, PNG](figures/mission_020_brochier_variability.png) ([vector PDF](figures/mission_020_brochier_variability.pdf)): within-session descriptive statistics, with dependent pairs.
- [Descriptive neural trajectories, PNG](figures/mission_020_brochier_trajectories.png) ([vector PDF](figures/mission_020_brochier_trajectories.pdf)): condition-mean PCA and fixed early trials; no claim of validated latent dynamics.

From a clone, install `.[dev,classical,brochier]` in the Python 3.11 Conda environment, obtain the [Mission 019 native assets](../docs/datasets/mission_019_brochier_assets.json) in `data/raw/brochier/`, and run `conda run -n cerebro python -m tools.brochier_population` at the repository root. The command verifies native asset hashes, writes the machine report and figures, and places the exact trial tensors in ignored `data/processed/brochier_population_20.npz`. Compare the report and tensor hashes to the committed machine report. Raw and processed neural arrays are never committed.
