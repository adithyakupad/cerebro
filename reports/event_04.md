# Mission 004: event-aligned neural population activity

Source: DANDI 000140 v0.220113.0408, asset `7821971e-c6a4-4568-8773-1bfa205c13f8`.
SHA-256 `dcaf3a524e2b2f65f163ee3b07789b8474bdfc6ca66098bc542ab93dff489884`; CC-BY-4.0, Churchland and Kaufman (2022).

## Feasibility and protocol

The [feasibility audit](event_04_feasibility.md) preceded analysis. 75 training
trials form 27 geometry-compatible conditions: 21 × 3 repetitions and 6 × 2.
Grouping maze IDs alone would pool incompatible task variants. All 25 validation
trials are excluded from means, residuals, bootstrap, and covariance calculations.

Human-selected primary event: `go_cue_time`, detected by the source photobox.
Window: **[−0.400, +1.000) s**, 70 half-open **20 ms** bins. Secondary alignment
uses existing `move_onset_time`, calculated offline by the source, not a newly
derived kinematic onset. Its full detection rule and timing uncertainty are absent.
All 75 train trials have complete coverage around both events; no events are missing.

Counts are trial-local; incomplete windows or neural/behavior gaps exclude whole
trials. Original timestamps remain unchanged; derived grid rounding/snap tolerance
is 1 ps. Behavioral endpoints/internal sample gaps use the declared 2 ms policy.
There is no interpolation or smoothing. Center-labeled bins use up to 10 ms of
future observations and are acausal summaries, not an online control protocol.

## Observed tensors and activity

| Tensor | Shape | Scope |
| --- | --- | --- |
| Counts / rates | 75 × 70 × 142 | Complete primary training windows |
| Hand velocity | 75 × 70 × 2 | Bin-mean vx/vy in m/s |
| Condition means | 21 × 70 × 142 | Three repetitions per condition |
| Condition-time residuals | 63 × 70 × 142 | 12 low-repetition trials excluded |
| Secondary counts | 75 × 70 × 142 | Existing source movement marker |

Primary windows retain **53,670 spikes** with per-unit/trial conservation checks.
Mean unit rate: **3.089202 Hz** in [−400,−200) ms,
and **4.319249 Hz** in [+200,+600) ms.
Paired trial-mean change: **1.230047 Hz**; stratified whole-trial
bootstrap percentile band **[1.135440, 1.333333] Hz** (1,000 draws, seed 4).
**74 of 75 trials** have a positive paired population-mean unit-rate change.
Bands resample entire simultaneous trial vectors within compatible conditions,
not bins or neurons. Pointwise bands are not simultaneous intervals; 2–3 repeats
give weak, potentially miscalibrated bootstrap uncertainty. Independent trials are
an assumption; within-session dependence and curated sampling are not ruled out.

Pooled population and hand-speed curves peak at **310 ms**
and **450 ms** after the go cue. These peak bins are descriptive,
not a fitted lag, evidence of neural prediction, or causal ordering. Source movement
onset latency is 243–606 ms (median 322 ms). Target-to-go delays vary 31–999 ms,
so the pre-go baseline does not represent an identical task stage on every trial.

## Correlation and residual limitations

Mean-response ('signal-like') Pearson coefficients compare 21 compatible-condition
mean response-epoch rates. These three-trial means contain substantial sampling
noise; the coefficients are not noise-corrected or validated estimates of shared tuning.
The simultaneous total covariance uses counts across 75 trials in the fixed
+300 to +320 ms bin. It mixes condition-dependent signal and residual variation.
Its rank is at most 74; covariance across 21 condition means has rank at most 20.
Undefined correlations for constant units remain NaN/gray, not zero. Sparse
coincidences can yield extreme coefficients, including 1, without robust coupling.

Expected responses are calculated separately at every condition and event-time bin.
Residuals subtract these in-sample means and sum to zero by construction. With three
repetitions, each condition-time residual covariance has rank at most two for 142 units.
**Residual correlation matrices and reliable noise-correlation claims are withheld.**
No condition meets the declared ≥20-repeat screening policy; even 20 repeats would
not guarantee reliable high-dimensional covariance. Time bins are not independent
trial repetitions. Correlation and covariance do not establish causal connectivity.
See [Cohen and Kohn (2011)](https://www.nature.com/articles/nn.2842) for the distinction
between tuning similarity and trial-to-trial response fluctuations.

## Adequacy and next decision

| Attempted analysis | MC_Maze Small adequacy |
| --- | --- |
| Pooled peri-event profiles / timing | Descriptive, 75 training trials |
| Compatible-condition means / residual illustrations | Limited precision, 3 repeats in 21 conditions |
| Mean-response correlations | Exploratory only, noisy three-trial means |
| Simultaneous total covariance | Descriptive mixture; singular for 142 units |
| Reliable condition-time residual correlations | Unsupported; no condition meets the screening policy |

MC_Maze Small supports software validation, descriptive peri-event profiles,
illustrative condition means and condition-time deviations. It does not support
reliable condition-specific population residual covariance here. Audit repetitions
in [standard MC_Maze 000128](https://dandiarchive.org/dandiset/000128/0.220113.0400)
next, after approval, before selecting an event-time/condition variability analysis.
Do not assume the larger release guarantees sufficient replication or identical fields.
The known 70 M1-prefix/electrode-link inconsistencies remain unchanged. No PCA,
decoder, learned transformation, representation alignment, push, or merge is performed.

## Reproduce and inspect

```sh
conda activate cerebro
python -m cerebro.event_audit configs/mc_maze_small.json
python -m cerebro.event_aligned configs/mc_maze_small.json
python -m cerebro.event_figures
python -m pytest
```

Protocol: `configs/event_04.json`. Results: `event_04_results.json` and Git-ignored
`data/processed/event_04.npz`, including source trial/event IDs, absolute boundaries,
condition means/residuals, covariance/correlation matrices and whole-trial bands.
Array hashes bind the tensor contents to the JSON; no wall-clock field is used.
Results JSON SHA-256: `c2751dd8ee3a8418bc0f9a5097c93831592a710a7817220f7edafce08b01a167`.

## Figures

- [event_04_units](figures/event_04_units.png)
- [event_04_population](figures/event_04_population.png)
- [event_04_conditions](figures/event_04_conditions.png)
- [event_04_residuals](figures/event_04_residuals.png)
- [event_04_correlations](figures/event_04_correlations.png)
- [event_04_timing](figures/event_04_timing.png)
- [event_04_coverage](figures/event_04_coverage.png)
