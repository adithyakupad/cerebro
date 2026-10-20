# M026 control validity matrix

Read alongside the [existing-control audit](m026_existing_controls.md) and
[frozen protocol](m026_protocol.md). All new standard-validation results are
retrospective. No control is a universal upper bound on task-only prediction.

| Control | Information removed | Preserved / added information | Retraining and shift | What can be concluded | What cannot be concluded |
| --- | --- | --- | --- | --- | --- |
| Zero-input CNN | All observed neural variation, task condition and trial-specific behavior | Same shape, trial duration and reset; constant raw zeros. Padding distinguishes only excluded bins0–3. | Trained from scratch and evaluated on the same zero-input distribution; no inference-only neural ablation | Learned intercept-like prediction under matched nominal optimization; software negative control | Strong phase-only prediction, neural necessity or capacity-equivalent functional model |
| Explicit-clock CNN | All observed neural variation and condition/trial-specific behavior | Bin-right go-relative time repeated across137input slots; same clock trajectory for every trial | Train-only clock scaling, same architecture/loss/optimizer/cap; train/eval input policy matches | Accuracy attainable by this optimized phase-only estimator | All task predictability, all condition information, live pre-cue clock availability, equivalent effective capacity |
| Condition×time template | All observed neural variation and trial-specific deviations | Exact native compatible condition plus go-relative bin, training condition-mean velocity | Closed-form training labels only; unseen conditions use global training-bin mean | Specified condition/clock predictability and real-model incremental accuracy relative to it | Exhaustive non-neural prediction ceiling or training-budget-matched CNN control |
| Condition-permuted training CNN, permuted evaluation | Recipient-specific neural/behavior pairing for nonsingletons in each partition | Complete donor population/temporal structure, compatible condition and go-relative phase | Train and evaluate under same fixed pairing intervention; donor assignment never crosses fitting/selecting/train/eval boundaries | Sensitivity to trial pairing when retraining accounts for that intervention; indirect task-conditioned information control | Perfect conditional independence, removal of all neural information or causal neural physiology |
| Same permuted-trained CNN, original evaluation | Trial-specific neural/behavior pairing during training only | Original recipient neural input at evaluation; trained task/condition structure remains | Prespecified additional inference convention, potentially different joint pairing distribution from training | Diagnostic difference between training intervention and evaluation pairing | A separately optimized primary model or permission to select whichever inference gives a favorable interpretation |
| Original real-neural CNN200 | No experimentally removed neural information | Original same-bin/past neural counts; task structure implicitly encoded; no explicit ID or condition/clock channel | Preserved M025 model/checkpoints, no retraining | Reference predictive association and comparisons with specified trained controls | New independent confirmation or broad BCI generalization |

## Access and identity

Each CNN sees trial-local sequences, not trial identifiers. IDs only choose and
check original partitions and record lineage. Donor IDs are indices, never input
channels. Condition metadata choose compatible donor groups; this is deliberately
an offline batch intervention. Condition-template predictions receive condition
labels explicitly, not evaluation velocity. Shared conditions are not independent
subjects and do not imply unique neural-unit correspondence across sessions.

Inner-selection donors come only from inner-validation neural observations;
inner-fitting donors come only from inner fitting. Full refitting then uses all
original source-training observations with a newly constructed full-training
mapping. Validation donor observations stay within the evaluation partition and
never enter fitting. Evaluation targets enter only frozen loss/stratum calculations.
A condition singleton keeps its own pairing and is explicitly counted.

## Timing and interpretation

Every prediction is assigned to the original bin-right timestamp, after the
current count bin is available. No lag search, wrapping, interpolation or new
smoothing is performed. Zero/clock policies do not fit timing from target values;
all trials have the same70bins. The clock and templates intentionally receive
task timing; offline pre-cue sequences use a subsequently recorded go cue.

Information removal and distribution-shift robustness are distinct. M025's partial
mean replacement is an inference distribution-shift probe; it does not supply a
trained no-neural baseline. Conditional donor trials retain neural condition/time
information and may preserve fine uncontrolled covariates. One fixed surrogate
per partition is not an exhaustive randomization distribution. Convergent results
can support incremental predictive association beyond these controls, while leaving
other task predictors, physiological causes and outside-session performance open.

The suite trains input controls only at cap200. It does not estimate a complete
optimization-budget × information interaction or partition the M02520→200 gain
into additive neural/task/optimization effects. Trial intervals condition on the
observed task mix and fixed surrogate; they do not resample task-condition clusters.

Absence of an explicit trial-ID feature does not exclude neural proxies for slow
recording state or repeated trajectory templates. The original interleaved split
tests held-out trials in this recording, not new conditions or chronological
deployment. Any implicit time/condition association is part of the predictive
result and must not be interpreted as an identified physiological cause.
