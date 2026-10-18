# Calibration reliability and controlled neural population forecasts in longitudinal intracortical recordings

CEREBRO post-v1.0 research integration · Release-candidate manuscript · October 2026

## Abstract

Low-budget neural-decoder recalibration can degrade prediction, but statistical contributors need not supply reliable prospective warnings. We integrated two prespecified development studies using authentic LINK intracortical recordings from one macaque: one source date and three inspected development dates. Whole-trial calibration subsets showed allocation sensitivity and prediction dispersion that fell from approximately 13–21% of five-trial decoder error to 2% at thirty trials. No mitigation met its frozen practical and consistency gate. Leave-one-session-out calibration-only risk models also failed promotion: the combined model's risk MSE was 1.094×10⁻⁵ flexion⁴ versus 7.202×10⁻⁶ for label-only moments. Source-trained six-dimensional PCA with affine latent autoregression improved one-step neural forecasting 42.36% versus persistence but only 3.59% versus a training mean and 2.40% versus temporally permuted fitting, below the 5% practical gate. Three later recordings passed native eligibility but remained unscored under the stopping rules. The contribution is a reproducible negative case study: calibration variability and observed temporal structure do not, by themselves, establish neural-specific adaptation reliability, practical transfer benefit or physiological drift.

## 1. Neural decoder adaptation problem

An offline decoder trained on one recording may encounter changed task sampling, target statistics, measurement distributions and neural activity in another session. Re-estimating many coefficients from few labeled trials can worsen prediction. We ask which observable statistical contributors explain this degradation, whether calibration-only diagnostics predict its direction on another development date, and whether interpretable population forecasts add information beyond task/label controls. The scientific objective concerns adaptive BCIs; these experiments are same-bin offline decoding and recorded-signal forecasting, not online biological control.

This manuscript integrates Missions 022 and 023 without rerunning hypothesis selection or replacing historical results. The long-term platform thesis and original 33 requirements remain in [the completion matrix](completion_matrix.md); this narrower contribution does not establish the full thesis.

## 2. Relevant neuroscience and prior research

Extracellular threshold crossings summarize local recorded activity; an electrode-contact feature is not a uniquely tracked neuron. Population dimensionality reduction supplies restricted coordinates for observations [Cunningham and Yu, 2014](https://doi.org/10.1038/nn.3776). State-space models distinguish assumptions about observations from assumptions about temporal evolution [Paninski et al., 2010](https://doi.org/10.1007/s10827-009-0179-x). Here we reuse existing PCA/FA and linear estimation, explicitly testing stronger observation and temporal controls. Our static observation projection followed by affine autoregression is not a jointly estimated latent dynamical system, and its coordinates are not identified physiological states.

Data attribution is Temmar and colleagues' LINK corpus, [DANDI 001201 version 0.251023.2336](https://doi.org/10.48324/dandi.001201/0.251023.2336), licensed CC-BY-4.0; [author documentation](https://chesteklab.github.io/LINK_dataset/) provides acquisition and target conventions. Dataset attribution and exact public asset metadata remain attached to the manifests; the software license does not replace dataset terms.

## 3. LINK recordings, coverage and experimental units

Jan 27, 2020 is the source. Its original first 300 trials contain 21,701 bins; the initial 225/75 split selects source ridge alpha, then all 300 fit the frozen source decoder. Development dates Jan 30, Feb 4 and Feb 5 each contribute only their first 75 historically permitted calibration trials: rows 0:45 form a calibration pool; rows 45:75 are development evaluation. Original target evaluation rows 75:375 and previously evaluated Feb 6/11/22 outcomes are excluded from new fitting and selection. Development evaluation is inspected development evidence, not an untouched test.

Each recording provides 96 contact-keyed threshold-crossing count features and two normalized finger-flexion targets, index and middle-ring-pinky coordinates. Exact contact joins support a shared recorded feature space, not neuron identity. The NWB `ElectricalSeries` label `volts` conflicts with the count description and nonnegative integer values; no calibrated voltage interpretation is used. Normalized flexion is not physical displacement or EMG. Native synchronized sample references and timestamps establish observed coverage; continuity is never inferred from first/last spikes. Nominal 20-ms clocks jitter, so sample horizons retain actual elapsed times rather than replacing timestamps. No explicit acquisition-quality mask is supplied.

There is **one biological subject**, one source session and three development sessions, with 30 evaluation trials/date. The 369 calibration allocations and thousands of bins are not independent biological replicates. At each budget, primary reliability analyses use 20 overlapping uniform subsets/date, not 60 independent sessions. Exact asset IDs, sizes, SHA256, sample references and contact joins are in [LINK manifests](../../configs/m023_protocol.json), [M022 lineage](../../reports/m022_calibration_mechanisms.json) and the [native audit](../datasets/m023_native_eligibility.md).

## 4. Calibration sampling and estimation variability

The source-only alpha grid is {1,10,100,1000}; selected alpha is 1000. Source neural standardization is fitted only on source training rows. At budgets B∈{5,15,30}, direct ridge and source-assisted residual ridge fit B whole labeled trials. Comparisons include chronological first-B selection, 20 fixed uniform subsets and 20 condition-balanced subsets; the latter requires all 45 pool command labels and later pool trials, an explicitly larger information budget. Fixed controls include source/target means, intercept correction, alpha multipliers {0.01,1,100}, target-fitted scaling and shrinkage weights {0.1,0.25,0.5} toward frozen predictions.

The exact empirical squared-error identity separates mean subset prediction error into ensemble-mean error and prediction dispersion, using population variance (ddof=0). It is a diagnostic across calibration subsets. The ensemble accesses their union, so is not a deployable B-label decoder; ensemble error includes noise and model mismatch, not identified physiological bias. Coefficients are compared in common raw-count axes after accounting for scaler differences. Trial-mean residual offsets and centered temporal errors are separately reported.

## 5. Neural population and state-space modeling

Static source PCA/FA dimensions 3/6/12 and local first-15/45-trial fits define observation coordinates. The fixed primary model is source PCA dimension six followed by ridge-alpha-1 affine AR1, z[t+1]=Az[t]+b. Inferred current state is propagated one or five sample steps without later teacher forcing, always within trial. Forecasts are reconstructed in common source-standardized count coordinates. Neural MSE therefore has units source-standardized count²; latent error is secondary and coordinate-dependent.

Controls are raw neural persistence, latent persistence, training mean, within-training-trial temporal permutation, independent-channel AR and training-command means. The last control receives evaluation command metadata, with documented fallback for unseen commands. Contemporaneous reconstruction is separate from forecasting. Behavior probes use ridge1000 and training-only latents/labels; they are offline. Principal angles map loadings into common raw-count axes, which weight contacts differently from forecast MSE. Orthogonal relabeling tests invariance. Condition-matched ten-segment phase trajectories require at least two trials in both compared sets; phase normalization is acausal and descriptive, not event synchronization or a forecasting input.

## 6. Competing hypotheses

M022 tests whether chronological task coverage, finite labeled-trial estimation, penalty choice, marginal feature scaling or contact mapping sensitivity contribute to adaptation error. M023 asks whether calibration-only command coverage, within-B bootstrap instability, neural shift or frozen/direct disagreement predict held-out adaptation harm better than simple controls. A secondary comparison asks whether source-neural forecast mismatch adds risk information beyond task/label moments. The null permits statistical associations without useful out-of-session risk prediction and without physiological identification.

## 7. Frozen protocols and information access

M022 [protocol](m022_protocol.md) was committed at `56b0a1c`; M023 [protocol](m023_protocol.md) at `a2861a2`; its pre-execution aggregate-risk clarification at `ca5a0ad`. Owner-confirmed practical gates are 5%, not thresholds selected from outcomes. Configurations and seeds are archived without modification.

Risk labels are equal-trial direct-minus-frozen MSE on the 30 development evaluation trials; positive means harm. Risk predictors use only selected calibration information: B position-label trials; B command labels for coverage; 20 bootstrap resamples within those same B labels; and 45 pool neural trials as an unlabeled probe for instability/disagreement. Label-only controls use calibration target moments relative to source moments. Source-neural forecast mismatch uses only the selected B calibration trials. M022 post-hoc evaluation-label distances and evaluation prediction dispersions are forbidden M023 predictors.

Separate fixed ridge-alpha-1 risk regressors use each diagnostic or all four; controls include training-date constant, majority class, label-only, shift-only and within-training-session outcome permutation. Risk scalers and regressors fit only the other two dates. Leave-one-session-out folds are **nonchronological**: training may include a later development date. They estimate out-of-session development performance, not forward deployment. Budgets are modeled separately; chronological/balanced results are sensitivities without refitting promotion rules.

M022 promotion requires ≥5% mean date-wise relative decoder-MSE reduction against both frozen and direct15, every date improving, and paired conditional intervals below zero. M023 risk promotion requires ≥5% reduction in the ratio of aggregate equal-date risk errors versus constant, label-only and shift controls, every date improving, intervals below zero, and pooled two-class balanced accuracy ≥0.60. Its fixed priority is disagreement, coverage, instability, combined. The temporal gate fixes source PCA6, horizon1, requiring ≥5% mean date-wise neural-MSE improvement, every date improving and intervals below zero against persistence, training mean and permuted AR. No alternate budget, dimension or family replaces a failed primary.

## 8. Controls and uncertainty

Decoder MSE averages time bins and both targets within each trial, then trials within date, then dates equally. It has units flexion²; MSE of predicted direct-minus-frozen risk has units flexion⁴. These endpoints and their percentage aggregation rules are different and must not be interchanged.

Conditional 95% intervals use 1,000 moving-five-trial-block resamples within dates. For reliability, the same trial indices are shared across overlapping subsets before recomputing risk labels, while trained risk parameters remain fixed. Intervals do not include risk-training uncertainty or unseen-session/animal variability; five-trial blocks do not guarantee independence. Training-date-only fits report prediction sensitivity separately. Single-class fold balanced accuracy is undefined; only globally two-class, equal-session-weighted pooled accuracy enters promotion. No biological population significance or multiplicity-adjusted exploratory inference is claimed. Full equations and source-key traceability are in the [statistical appendix](v1_1_statistics_appendix.md).

## 9. Calibration and reliability results

| Development date | Chronological frozen/direct15 MSE, flexion² | Uniform direct dispersion fraction B5→B30 | Balanced15 improvement vs chronological15 |
|---|---:|---:|---:|
| Jan 30 | 0.02841389 / 0.03388667 | 20.7% → 2.2% | 12.17% |
| Feb 4 | 0.02980624 / 0.03257202 | 19.2% → 2.4% | 8.70% |
| Feb 5 | 0.02930611 / 0.02709601 | 13.2% → 2.1% | 1.36% |

Finite-subset variability decreases with budget, and task-balanced allocation changes error, but chronology is not uniformly harmful. Balanced selection has additional information and temporal access. Scaling and regularization effects differ by date. All seven prespecified mitigations fail the gate. Direct25% shrinkage improves mean date-wise MSE 4.33% versus frozen and 9.83% versus direct, with conditional paired intervals [−0.001913,−0.000749] and [−0.004779,−0.001196] flexion²; despite every-date improvement, its frozen contrast misses 5%. These remain negative promotion results.

| B15 risk predictor | Equal-date risk MSE, flexion⁴ | Pooled balanced accuracy |
|---|---:|---:|
| Constant | 1.207965153×10⁻⁵ | 0.5000 |
| Coverage | 1.212426056×10⁻⁵ | 0.4500 |
| Instability | 1.214092923×10⁻⁵ | 0.3875 |
| Shift | 7.276299647×10⁻⁵ | 0.6625 |
| Disagreement | 3.890973094×10⁻⁵ | 0.3375 |
| Combined | 1.093746724×10⁻⁵ | 0.6750 |
| Label-only | 7.202293230×10⁻⁶ | 0.7625 |
| Permuted combined | 1.249747854×10⁻⁵ | 0.6750 |

Combined risk MSE improves 9.46% versus constant but worsens 51.86% versus label-only; its balanced accuracy equals the permutation control. Combined-minus-constant and combined-minus-label-only conditional intervals are [−1.764842×10⁻⁵,2.259096×10⁻⁵] and [−9.755603×10⁻⁶,2.153193×10⁻⁵] flexion⁴. Both cross zero, and date consistency fails. Adding dynamics mismatch to task/label moments changes risk MSE from 7.233054940×10⁻⁶ to 7.313017385×10⁻⁶, a 1.11% worsening. No reliability method passes; this does not prove all possible diagnostics fail.

## 10. Neural dynamics results

| Source PCA6 h1 comparison | Mean date-wise relative improvement | Equal-date paired MSE difference | Conditional 95% interval, standardized count² |
|---|---:|---:|---|
| Raw neural persistence | 42.364% | −1.079553 | [−1.133521,−1.031258] |
| Training mean | 3.594% | −0.058542 | [−0.069887,−0.045812] |
| Temporally permuted AR | 2.398% | −0.038528 | [−0.045734,−0.030474] |

All three contrasts favor the fixed model on every date, yet the latter two miss the practical threshold. The temporal gate fails. Strong persistence gains can reflect suppression of observation variation; they do not alone establish practically useful dynamics. One-step MSE is 1.176594, 1.510297 and 1.785513; five-step is 1.180799, 1.573923 and 1.902846 on Jan 30/Feb 4/Feb 5. Native elapsed ranges are approximately 19–21 ms and 99–101 ms.

Source/pool covariance cosines are 0.710868, 0.535491, 0.420153. Condition-matched phase-trajectory comparisons support only 6,7,7 commands, with mean cosines 0.295525,0.246371,0.293271. Limited task repetitions, observation changes and task mixtures prevent biological-invariance conclusions. Sixty fixed model/session comparisons and all secondary controls are preserved in [the complete dynamics results](../../reports/m023_dynamics.json).

## 11. Negative findings and numerical caveats

No M022 mitigation or M023 reliability/temporal primary passes its frozen gate. Neural dynamics mismatch adds no primary risk benefit beyond task/label controls. Penalty/scaling diagnostics are heterogeneous, not universal remedies. Correlation or statistical decomposition does not demonstrate physiological cause.

FA fitting emitted zero fitting warnings, while held-out library likelihood scoring recorded 2,700 NumPy `slogdet` warnings with finite final values. Independent covariance/Cholesky evaluation reproduced all 900 FA trial-mean likelihoods across 30 comparisons, maximum absolute difference 8.53×10⁻¹⁴. This supports the numerical scores, not the Gaussian approximation to counts. Primary PCA forecast MSE is separate from FA likelihood. All likelihood caveats remain public; no warning is silently discarded.

## 12. Physiological identifiability and alternative explanations

One animal and three inspected development dates cannot support population-level biological generalization. Contact correspondence is not neuron identity. Normalized behavioral targets, unmodeled quality variation, task sampling, correlated bins, unequal condition repetitions and scaling-dependent regularization all constrain interpretation. Trial resampling does not create independent animals. Out-of-session folds are not chronological prediction; descriptive phase matching is acausal. The experiment cannot separate changing underlying computation from changing recorded observations, task behavior and estimator uncertainty. No causal connectivity, physiological drift, subject-invariant representation, general-purpose neural foundation model or live BCI benefit is claimed.

## 13. Implications for adaptive BCIs

The supported contribution is methodological restraint with reproducible evidence. Low-budget estimator variability and allocation sensitivity deserve explicit controls, but deploying a reliability rule requires prospective utility beyond target-label moments and simple shift baselines. Neural forecasts require training-mean and temporal-permutation controls, not persistence alone. A failed practical gate is a completed experiment, not a software failure or proof that adaptive BCIs cannot work.

## 14. Independent validation requirements and availability

Later Feb 24, Feb 25 and Jun 26 recordings passed native within-subject coverage/contact/target checks in Mission 023. They remain **unscored by the prespecified null rules**, not blocked by absent compatible data. M022's earlier metadata-only status is historical, not rewritten. A future hypothesis requires a separately frozen estimand, parameters, calibration access, metrics, uncertainty, exclusion rules and practical gate before consuming these outcomes. No post-failure tuning on these dates is authorized by this release.

Public code/configurations, compact statistics, PDFs and attribution are available; raw data and numerical checkpoints remain Git-ignored and are acquired/recreated from pinned sources. [M022 report](../../reports/m022_calibration_mechanisms.md), [M023 reliability](../../reports/m023_reliability.md), [M023 dynamics](../../reports/m023_dynamics.md), and their immutable JSON companions provide complete ablations. [M022 verification](m022_validation.json) and [M023 verification](m023_validation.json) distinguish software checks from authentic-data checks; current release qualification is documented separately, without implying historical counts are current.

Primary figures: [calibration mechanisms](../../reports/figures/m022_mechanism_comparison.pdf), [reliability](../../reports/figures/m023_reliability.pdf), [population forecasts](../../reports/figures/m023_dynamics_comparison.pdf). [Ten-slide editable presentation](../../reports/m023_research_presentation.pptx) remains a focused companion; its final slide also points to an optional technical interview pack, which is not scientific evidence. Reviewers should use the [checklist](v1_1_reviewer_checklist.md), [statistical appendix](v1_1_statistics_appendix.md), and [reproduction guide](v1_1_reproduction.md).

**Contribution:** Whole-session development tests demonstrate that calibration-subset variability and modest neural temporal structure do not automatically provide reliable adaptation-harm prediction. Strong label-only and temporal controls negate broad positive claims while leaving eligible later-session outcomes unconsumed.
