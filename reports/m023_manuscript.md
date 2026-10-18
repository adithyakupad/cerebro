# Calibration-only reliability diagnostics and controlled population forecasts in longitudinal intracortical recordings

Research manuscript candidate · CEREBRO Mission 023 · October 18, 2026

## Abstract

Low-budget recalibration can degrade a previously fitted neural decoder. We examined whether information available during calibration predicts this harm, and whether interpretable population dynamics add explanatory information. Using authentic LINK threshold-crossing recordings from one macaque, we confined development to previously permitted calibration partitions on three dates. Ridge risk models were evaluated by leaving out entire sessions, with coverage, bootstrap instability, neural shift and decoder disagreement compared against label-only and permutation controls. At 15 labeled trials, the combined model achieved balanced harm accuracy 0.675 but risk-prediction MSE 1.094×10⁻⁵ flexion⁴, worse than the label-only control's 7.202×10⁻⁶. Separately, source-trained six-dimensional PCA/AR forecasts reduced one-step neural MSE 42.36% versus persistence, but only 3.59% versus a training mean and 2.40% versus time-permuted fitting. Neither workstream passed its prespecified practical and consistency gate. Three later sessions passed native eligibility but remained unscored under the null rules. These reproducible negative controls limit claims of neural-specific adaptation reliability and show why strong persistence improvements alone do not establish practically useful latent dynamics.

## Introduction and related work

CEREBRO's adaptive neural intelligence thesis concerns useful neural representations under recording and behavioral changes. The platform's implemented workflows and earlier results are described in the [integrated platform report](../docs/research/mission_020_technical_report.md). That thesis is a research objective, not an established general capability. Mission 022 found calibration allocation sensitivity and finite-subset prediction variability, but no prespecified mitigation met its promotion gate. The present study asks whether these descriptive effects provide **calibration-only predictions** of adaptation harm on another development date.

Dimensionality reduction describes neural population observations through restricted coordinates [Cunningham and Yu, 2014](https://doi.org/10.1038/nn.3776). State-space methods separate latent evolution and observation assumptions [Paninski et al., 2010](https://doi.org/10.1007/s10827-009-0179-x). We use the existing CEREBRO PCA/FA estimators and linear regression infrastructure, rather than introducing an architecture. Our population model is explicitly two-stage: static observation coordinates followed by a fitted affine autoregression. We do not jointly estimate a full latent dynamical system, identify physiological state variables, or infer causal connectivity.

The intended contribution is an auditable test of whether modest reliability and dynamics diagnostics survive simple task/label controls. It is not a claim of positive transfer or validated prospective deployment.

## Data, provenance and experimental units

Data are Temmar and colleagues' LINK corpus, [DANDI 001201 v0.251023.2336](https://doi.org/10.48324/dandi.001201/0.251023.2336), CC-BY-4.0, with [author acquisition documentation](https://chesteklab.github.io/LINK_dataset/). Source Jan 27 uses original rows 0:300. Jan 30/Feb 4/Feb 5 development uses **only first 75 historically permitted calibration trials**, subdivided into pool0:45 and evaluation 45:75. Original target evaluation rows 75:375 and Mission 016 Feb 6/11/22 outcomes are excluded from new fitting and selection. These are inspected development dates, not untouched tests. Unique trial identities are qualified by session.

Each recording supplies 96 electrode-contact threshold-crossing features and two normalized finger-flexion targets: index and middle-ring-pinky coordinates. Exact contact mapping supports a shared recording-feature space, not stable neuron identity. Native nominal 20-ms clocks jitter; original synchronized timestamps and sample references are preserved. Counts are interpreted from the source description and nonnegative integer values, despite the NWB ElectricalSeries unit label `volts`. Targets describe normalized flexion rather than physical displacement or EMG. No explicit recording-quality mask is supplied. Sample-reference coverage establishes available observations, not the absence of physiological or acquisition artifacts.

The biological subject count is **one**. Development contains one source and three target dates, with30 evaluation trials/date. Primary reliability comparisons contain20 overlapping uniform calibration subsets/date/budget. These 60 allocations per budget are not 60 independent sessions. The complete study retains369 allocations, including chronological and balanced sensitivity cases, and 60 population model/session comparisons.

Exact asset IDs, published/local SHA256, clocks, trial masks and licenses appear in the manifests and [native eligibility audit](../docs/datasets/m023_native_eligibility.md). New Feb 24/Feb 25/Jun 26 files each have 375 trials and96 contacts, synchronized modalities and compatible targets. Their recorded arrays were audited, but no model performance outcomes were scored. June's long gap is explicitly retained rather than replaced with a favorable date.

## Prespecification and methods

The complete [protocol](../docs/research/m023_protocol.md) and native eligibility evidence were committed at `a2861a2` before M023 model execution. The [risk-metric clarification](../docs/research/m023_reliability_clarification.md), committed at `ca5a0ad` before Workstream A execution, specifies the ratio of aggregate equal-date risk errors. Five-percent gates were prespecified and subsequently confirmed unchanged by the owner. No candidate, threshold, dimension or date was changed in response to outcomes.

### Adaptation outcome and information access

The source decoder reproduces Mission 022 exactly: source-only ridge-alpha selection on 225/75 source-training trials, chosen alpha 1000, then refit on 300 source trials with a source-fitted neural StandardScaler. Direct recalibration uses only B selected labeled trials, B ∈{5,15,30}, with the same source scaling and penalty. Source weights, intercept and all369 direct-decoder outcome vectors are restored exactly against Mission 022.

For subset s of date j, the risk target is

\[
\Delta_{js}=\frac{1}{T_j}\sum_t\left[\mathrm{MSE}(\hat y^{direct}_{jst},y_{jt})-\mathrm{MSE}(\hat y^{frozen}_{jt},y_{jt})\right].
\]

Each trial MSE averages its available time bins and two targets. Positive Δ means adaptation harm. Risk prediction MSE has units flexion⁴; decoder MSE and Δ have units flexion².

Coverage is the fraction of source commands represented in selected calibration trials, requiring B additional command labels. Bootstrap instability resamples whole trials **within the same B labels**20 times and measures prediction variance on 45 permitted unlabeled pool trials. Neural shift is the squared source-standardized calibration mean. Disagreement is frozen/direct prediction difference on the same unlabeled probe pool. Label-only controls use calibration position means/variances relative to source moments. No feature receives evaluation neural samples, target moments or prediction errors. In particular, Mission 022's post-hoc evaluation-label distance and evaluation-ensemble dispersion are forbidden predictors.

Separate fixed ridge risk models, alpha 1, use coverage, instability, shift, disagreement or all four. Controls are training-date constant risk, majority harm, label-only moments, and within-training-session outcome permutation. Coverage+label moments is a task control; adding source-neural forecast mismatch tests dynamics information beyond it. Every risk scaler and parameter is fitted on the other two dates only. Budgets are modeled separately; chronological/balanced allocation results are sensitivity checks without refitting or promotion.

The fixed promotion order is disagreement, coverage, instability, combined. A candidate must reduce aggregate equal-date risk MSE≥5% versus constant, label-only and shift regressors, improve every held-out date, have paired conditional intervals below zero, and reach pooled session-weighted two-class balanced accuracy≥0.60. Single-class fold balanced accuracy is undefined; ordinary accuracy is not substituted. Secondary decoder policy adapts only when predicted Δ<0. Predicting risk and improving the resulting decoder policy are distinct estimands.

### Observed population dynamics

Source-only PCA/FA dimensions 3/6/12 and local first 15/45-trial observation models supply coordinates z. The primary fixed model is source PCA 6 with ridge AR1:

\[
x_t\approx Cz_t+\mu,\qquad \hat z_{t+1}=Az_t+b.
\]

Horizons 1 and5 propagate the inferred current state without later teacher forcing. Transitions and forecast targets remain within each original trial. Neural predictions are reconstructed into a common **source-standardized count space**; latent MSE is secondary because coordinate scaling is arbitrary. Baselines include raw neural persistence, latent persistence, training mean, within-training-trial temporal permutation, independent-channel AR and training-command neural means. The command control receives evaluation task metadata and falls back to training mean for unseen commands. Reconstruction from contemporaneous observations is explicitly separate from forecasting.

Offline behavior probes, ridge1000, fit training latents and labels only. Covariance cosine uses source-standardized observations. Principal angles use a shared raw-count loading frame, whose contact weighting differs from the forecast error frame. Orthogonal relabeling checks latent, reconstructed-forecast and subspace invariance. Condition-matched trajectories require at least two repetitions in both source and pool and average ten within-trial phase segments. Phase normalization is acausal and descriptive, not movement-onset synchronization or a forecast input.

The temporal promotion gate is fixed source PCA 6 horizon1, requiring≥5% equal-date improvement, every-date improvement and conditional intervals below zero against persistence, training mean and time-permuted fitting. FA, dimensions, local scaling and longer horizons cannot substitute for a failed primary model. The scientific model is a Gaussian/linear approximation to recorded counts; FA observation likelihood is not a spike-count likelihood.

### Uncertainty and reproducibility

Conditional intervals use 1000 moving-five-trial-block draws within each date. For reliability, the same trial-block indices are shared across overlapping calibration subsets before recomputing Δ labels, holding trained risk parameters fixed. These intervals exclude risk-training uncertainty and unseen-session/animal variability. Training-date-only fits quantify risk-prediction instability separately. We report date-specific errors rather than treating subset draws or bins as biological replication. No multiplicity-adjusted significance or precise population interval is claimed from three dates.

All configurations, seeds, allocation IDs, input units, source hashes, model parameters and array digests are retained. Numerical checkpoints and raw data stay Git-ignored; public results contain derived statistics and provenance. Synthetic tests verify arithmetic and access restrictions, while neural findings use authentic recordings only.

## Results

### Reliability prediction failed the frozen gate

| 15-label risk model | Equal-date risk MSE flexion⁴ | Pooled balanced harm accuracy |
|---|---:|---:|
| Constant | 1.20796515×10⁻⁵ | 0.5000 |
| Command coverage | 1.21242606×10⁻⁵ | 0.4500 |
| Bootstrap instability | 1.21409292×10⁻⁵ | 0.3875 |
| Neural shift | 7.27629965×10⁻⁵ | 0.6625 |
| Decoder disagreement | 3.89097309×10⁻⁵ | 0.3375 |
| Combined | 1.09374672×10⁻⁵ | 0.6750 |
| Label-only | 7.20229323×10⁻⁶ | 0.7625 |
| Permuted combined | 1.24974785×10⁻⁵ | 0.6750 |

Combined risk MSE improved 9.46% versus constant but was 51.86% worse than label-only. Combined-minus-constant conditional risk-MSE interval was [−1.765×10⁻⁵,2.259×10⁻⁵] flexion⁴; combined-minus-label-only was [−9.756×10⁻⁶,2.153×10⁻⁵]. Both cross zero. Combined risk MSE worsened on the held-out Feb 5 date relative to constant and label-only. Its balanced accuracy equaled the permutation control, illustrating why harm classification alone cannot establish useful neural reliability information.

Adding source-neural dynamics mismatch to coverage+label moments increased risk MSE from 7.23305494×10⁻⁶ to 7.31301738×10⁻⁶ flexion⁴, a 1.11% worsening. Effects varied by date and budget; this secondary comparison does not establish additional explanatory value. All candidates failed promotion. Complete B5/B30, allocation-shift, action-policy, training-date stability and per-date results remain in the [reliability report](m023_reliability.md) and [machine artifact](m023_reliability.json).

### Temporal structure exists but misses the practical criterion

| Control | Mean date-wise relative improvement | Equal-date AR−control neural MSE | Conditional95% interval |
|---|---:|---:|---|
| Neural persistence | 42.364% | −1.079553 | [−1.133521,−1.031258] |
| Training mean | 3.594% | −0.058542 | [−0.069887,−0.045812] |
| Time-permuted AR fitting | 2.398% | −0.038528 | [−0.045734,−0.030474] |

Source PCA6 one-step neural MSE was 1.176594,1.510297 and1.785513 on Jan 30/Feb 4/Feb 5; five-step values were 1.180799,1.573923 and1.902846. Actual elapsed clocks were approximately 19–21ms and 99–101ms, with exact date-specific limits reported. All three primary relative effects were favorable on every date, but mean/permutation improvements remained below 5%. The primary temporal gate therefore failed despite intervals below zero. Beating noisy raw persistence alone would have overstated the practical latent-dynamics contribution.

Source/pool covariance cosines were 0.710868,0.535491,0.420153. Condition-matched phase-trajectory comparisons had only 6, 7, 7 supported commands, with mean cosines 0.295525,0.246371,0.293271. These describe observed distribution changes with limited task replication. They do not separate physiology from behavioral mixture or establish stable biological representations. All 60 population ablations, behavioral probes, controls, geometry and likelihoods appear in the [dynamics report](m023_dynamics.md) and [machine artifact](m023_dynamics.json).

### Independent validation decision

Feb 24/Feb 25/Jun 26 pass native within-subject eligibility. Nevertheless **neither question passes its development promotion gate**, so no final addendum/model promotion or new-session outcome evaluation occurs. This is a prespecified null-rule stop, not absence of accessible compatible data. The sessions remain available for a future separately frozen hypothesis; no outcome-driven search was performed.

## Discussion and alternative explanations

H1–H4 as fixed single-feature risk predictors did not establish reliable out-of-date benefit over simple controls. The combined diagnostic offered some development discrimination but failed the stronger label-only, uncertainty and date-consistency requirements. Calibration target moments may reflect task sampling, and prediction error can change through constant offsets without neural representational change. Small effective sample size, feature penalty choice and the contrast between uniform development subsets and future chronological calibration remain limitations. We do not infer that every possible reliability method must fail.

Observed low-dimensional temporal structure is supported under the fixed development comparisons. Its practical effect against stronger controls is modest. Local observation fits and changes in dimensionality can improve neural reconstruction while offering different or weaker behavioral prediction; neither neural reconstruction nor a visually stable trajectory demonstrates a stable task-relevant neural computation. The dynamics mismatch feature did not add consistent risk information beyond task/label moments in the primary comparison.

FA fitting produced no fitting warnings, but held-out scoring produced 2700 recorded NumPy `slogdet` runtime warnings while final Gaussian scores remained finite. This limits scientific use of likelihood differences; the primary forecast endpoint is PCA neural MSE and is unaffected by those FA likelihood calculations. It is not appropriate to advertise these scores as numerically unqualified evidence.

A separate raw-parameter covariance/Cholesky calculation reproduced all900 reported FA trial-mean likelihoods across30 model/session comparisons, with maximum absolute difference8.53×10⁻¹⁴. This supports the numerical values despite the recorded library warnings; it does not validate the Gaussian observation approximation or turn likelihood differences into physiological evidence.

The principal limitations are one biological subject, three already inspected development dates, overlapping subsets, correlated within-trial bins, conditional uncertainty with fixed trained risk parameters, contact rather than neuron correspondence, unmodeled acquisition quality and normalized source targets. Session leave-one-out folds are nonchronological: training may include dates later than the held-out development date. They measure out-of-session development performance, not forward deployment. The unexecuted gated later cohort would have supplied forward evaluation. No causal connectivity, physiological drift, live BCI, subject invariance or general neural foundation-model validity follows.

## Evidence classification and contribution

| Question | Classification | Supported claim |
|---|---|---|
| Calibration-only reliability | **Bounded negative finding** | These fixed models fail the gate; combined does not beat label-only risk prediction reliably. |
| Observed temporal structure | **Mechanism supported, statistical only** | Linear latent forecasts improve recorded neural predictions over fixed controls on development dates. |
| Practical reliability or adaptation benefit | **Not independently validated** | No candidate was promoted; decision utility is secondary development evidence. |
| Separation of physiology and task changes | **Scientifically inconclusive** | Observation/task controls narrow interpretations but do not identify physiological cause. |
| Independent evaluation | **Not executed by null rule** | Compatible data exist; no new-session model outcomes were consumed. |

**Contribution in three sentences:** Calibration-only reliability diagnostics were tested with whole-session splits and explicit information budgets on authentic longitudinal neural recordings. Strong label-only and temporal controls narrowed apparent gains: no reliability candidate or fixed temporal model met the prespecified practical promotion criteria. The result is a reproducible, bounded negative case study that preserves an eligible later cohort instead of spending it on unpromoted methods.

## Figures, data/code availability and reviewer materials

- [Figure 1: calibration-only reliability](figures/m023_reliability.pdf), with date-level risk, budget sensitivity, overlapping-subset predictions and conditional contrast intervals.
- [Figure 2: observed dynamics](figures/m023_dynamics_comparison.pdf), with per-date primary forecasts, horizon effects, geometry and explicit controls.
- [Frozen configuration](../configs/m023_protocol.json), [reviewer reproduction guide](../docs/research/m023_reproduction.md), [verification record](../docs/research/m023_validation.json).
- [Ten-slide presentation](m023_research_presentation.pptx) and [technical interview evidence pack](../docs/research/m023_interview_pack.md).

Source code and derived reports are available in the M023 research PR; raw LINK data remain with the public DANDI source and are not redistributed here. CEREBRO software is MIT-licensed, while the separate dataset attribution/license remains CC-BY-4.0. PR2 and historical negative results are preserved. This manuscript is an external-review candidate, not peer-review acceptance or a clinical/implant validation.
