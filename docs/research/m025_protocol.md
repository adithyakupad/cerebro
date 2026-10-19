# M025 frozen decoder optimization protocol

Authorized 2026-10-19 by the researcher following `m025_decision_report.md`.
This file and `configs/m025_optimization.json` must be committed before genuine-data
training. No historical artifact is overwritten. Scientific question: does a larger
optimization budget improve the existing causal CNN, rather than merely hit a
longer stopping ceiling? Final-epoch selection is evidence for testing this question,
not proof of undertraining or physiological limitation.

## Immutable design

- Seeds 0/1/2; existing `make_sequence_model('temporal_cnn', units,32,2)` unchanged.
  Adam 0.001, gradient clip1, full-trial batches, standardized target training
  loss exactly as historical. Compare maximum20 and200 updates. Select minimum
  physical velocity MSE on the fixed inner validation trials; ties choose first
  epoch. Selection and primary scoring use zero-based bins4:70 for every model.
  CNN training loss still includes all70bins. Both caps may share a deterministic
  200-update inner trajectory (first20 is exactly the short-cap trajectory);
  refit each selected epoch count from its seed on all source-training trials.
- Small development: existing classical05 tensor hashes and exact original
  trial IDs, source75train/25previouslyinspectedval and inner60/15, unchanged.
  Fit counts and target scaling on inner60 during selection, refit on75 only
  after selection. The outer25 are descriptive development, never untouched.
- Independently tune instantaneous and five-bin history ridge, and Kalman,
  alpha[1,10,100,1000], smallest grid-order winner. Count standardization is
  training-only and precedes lag construction; five-bin feature order is oldest
  to current, entirely within trial. Ridge fitting uses bins4:70 for both history
  lengths. Kalman fitting uses all trial-local training transitions, scoring
  starts at bin4, state initialization uses a training prior, never true behavior.
- Mean and go-time template use training velocity only. Refit selected classical
  models and controls on all source-training trials. No tuning on outer25.
  No new architecture, loss, learning-rate schedule or hyperparameter grid.
- Primary endpoint: equal-trial mean of squared errors across66bins and2physical
  velocity coordinates, (m/s)^2. All70-bin CNN/Kalman/instantaneous sensitivities
  are secondary; five-bin ridge has no complete history at the first4bins.
- Development promotion requires mean selected inner loss(CNN200) <=0.95 times
  mean selected inner loss(CNN20), averaging the three seed losses. This is
  selection-conditioned evidence, not independent performance estimation.
  Failure stops prospective evaluation; do not inspect another dataset for a
  favorable result. Preserve every seed, epoch curve and negative outcome.

## Prospective evaluation eligibility and procedure

The only approved prospective recording is DANDI000128v0.220113.0400, asset
26e85f09-39b7-480f-b337-278a8f034007, SHA256
`a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4`.
Jenkins Sep25,2009 differs from Small Sep28,2009. These are separate recordings
of one animal, not independent subjects or matched neuron populations. The137
held-in units define a separate input layer and session-specific fit; there is
no cross-session decoder transfer claim.

Before any standard validation target values or predictions are loaded:
independently document exact native/session identity, coverage, unit definitions,
clocks/behavior units, source train/val identities, prior use and duplicate/overlap
checks in `m025_evaluation_eligibility` evidence. Metadata or behavioral descriptions
previously audited must be disclosed. "Untouched" means performance-unscored
under this bounded recipe, never data that nobody has inspected. If genuine
independence under this claim cannot be established, stop this component.

Only after both development and independent eligibility pass, reuse go-cue
−0.4:+1.0s,20msbins, hand_vel m/s, heldin-only and2msgap from classical05.
Require each trial's full window inside trial bounds, every neural unit's authentic
observation coverage, valid behavioral coverage and spike conservation. Exclude
incomplete trials with recorded IDs/reasons, no extrapolation. Preserve original
NWB train/val splits. Freeze exact eligible identities before any fitting.

Use original train only (nominal1721): seed5 NumPy default_rng permutation,
first floor(0.2*N) IDs internal validation, remaining fitting, sorted identities.
Nominal1377/344; excluded windows may reduce counts. Original574val are final
only; no scaling, regularization, epochs or thresholds fitted from them.
Apply the same frozen recipe, refit on all eligible source train, evaluate once.
Create an exclusive final-start marker before loading validation target arrays;
no repeat or automatic substitution. A crash is reported and requires explicit
recovery, not a hidden second attempt. Source/target unit IDs are not paired.

Primary final contrast CNN200 minus CNN20. Practical improvement requires at
least5% lower equal-trial MSE than BOTH CNN20 and independently tuned Kalman,
and both paired95% trial-bootstrap difference intervals below0. Report history
ridge regardless; no superiority over strong classical methods if it wins.
Average seed losses within trial, not ensemble predictions. Fixed10000draws,
seed25; resample trials jointly across methods. Ordered nonoverlapping5-trial
blocks (last short block retained), resampled as blocks with equal-trial weighting,
are a sensitivity, not biological population inference. Report every seed,
coordinate R², absolute and relative changes. Do not bootstrap seeds as subjects.

## Controls, resources and failure rules

No primary lag changes: current/past counts predict same-bin velocity, available
at bin right. No future smoothing or behavior inputs. Test prefix causality.
History-matched ridge controls temporal information; mean/template control task
clock; report full learning curves to expose plateau/overfit and epoch choices.

Secondary fixed inference perturbation: seed25 selects floor(0.1*units) columns;
replace counts in those columns by fitted training means before each fixed model's
normalizer (equivalent to standardized zeros), same columns/masks for all models.
This tests missing-feature sensitivity, not real electrode dropout/neural drift.
Phase-preserving negative control: within each exact recorded condition key
(trial_type, maze_id where available), seed25 randomly permutes whole neural
trials, keeping behavior/trial clocks fixed; singleton groups remain unchanged
and are counted. This is an explicitly offline null, not a deployable decoder.
If condition metadata cannot be recovered unambiguously, mark this null NOT TESTED;
do not silently pool conditions. No10-bin or new-lag search in the primary study.

Record wall time, CPU threads/library versions, per-epoch times, fit/inference
cost, input/output digests, protocol/config/source hashes, revision, native
asset checksums and exact split IDs. CPU deterministic algorithms and one thread;
no GPU/online control claims. One CPU-day budget per stage; stop if exceeded,
preserve partial outcomes, no outcome-dependent cap/seed adjustment. Maximum
three repair attempts for the same failure. A data-integrity/test failure blocks
new outcomes. Software-only corrections require separate commits and regression
checks; historical source-bound records remain unchanged.

Outputs: reports/m025_optimization.{json,md}, figures under reports/figures/m025_*,
ignored data/processed/m025_development and (only if eligible/promoted) m025_final.
Checkpoint restoration and prediction digests must pass. Reproduction is a
no-fitting replay from immutable saved arrays/checkpoints; training reruns belong
in a new directory and must reproduce predictions numerically. All results,
including failed gates and unsupported independent validation, are retained.
