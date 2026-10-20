# M026 frozen neural-information diagnostic protocol

## Scope and evidence status

Start from M025 `552e50bcd44004895fa75eea7d9345b15e89fc2c`. Preserve
all M025 methods/results/checkpoints. Branch `codex/m026-neural-information`
is stacked on draft PR5; neither PR4 nor PR5 is merged. This protocol must be
committed before fitting controls. New standard-validation comparisons are
**retrospective diagnostics**, never another independent confirmation. No new
recording cohort or untouched evaluation claim is attempted.

Question: how much of M025's optimized offline same-bin velocity reconstruction
is explained by task phase, recorded conditions and trial-specific neural pairing?
Hypotheses: phase/conditions explain some predictability; real neural pairing
adds prediction accuracy. Null: appropriately trained non-neural or disrupted-pair
controls match the real model. A result cannot establish a physiological cause.

## Ranked controls, before execution

1. Explicit-clock CNN: task predictability, no neural observations. Repeat the
   fixed bin-right clock [-0.38, -0.36, ..., 1.00] seconds across all 137 existing
   input slots; same CNN architecture, 32 hidden units, optimizer and selection.
   Clock access is intentional additional task information, not neural leakage.
2. Condition-by-time template: training-only mean velocity for each full compatible
   recorded condition and bin; unseen keys fall back to global training-bin mean.
   Exact keys use existing `condition_keys` (maze, trial type/version, active target,
   validated geometry). Report counts and results for seen/unseen conditions.
   This has explicit condition metadata, no trial IDs or neural input.
3. Condition-permuted-training CNN: preserve complete neural trajectories and task
   condition while disrupting trial-specific pairing within each partition. Fixed
   seed25 donor assignment: shuffle group order and cyclically shift by a nonzero
   offset, so every nonsingleton changes. Singleton donors remain themselves and
   are counted. Independently map inner-training, inner-validation, full training
   and evaluation; never use donors across these boundaries. Refit uses full
   training donors, not inner-validation targets in selection fitting.
   Score BOTH original evaluation neural inputs and independently permuted
   evaluation inputs; the latter is the matched training-intervention contrast.
   Neither result may select a different control or interpretation.
4. Zero-input CNN: trained no-neural negative baseline with same nominal capacity
   and optimization. Zero inputs remove all task-condition/trial information.
   Padding can only distinguish first four bins, which are not primary scoring;
   subsequent predictions are constant. This is NOT a phase-preserving model.
5. Boundary-safe lag tests: useful alignment/OOD sensitivity but deferred; avoid
   circular wrapping, changed score masks and an unbounded lag search.
6. Synthetic/surrogate neural counts: deferred because distribution assumptions
   confound information removal with surrogate mismatch.
7. Information-matched real/non-neural comparisons and incremental-task prediction
   are addressed by controls1–3 plus the original mean/bin-template baselines;
   they do not exhaust every possible task-conditioned predictor.

## Fixed data and fitting

Only standard MC_Maze DANDI000128 v0.220113.0400, asset
26e85f09-39b7-480f-b337-278a8f034007, SHA256
`a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4`.
Jenkins Sep25,2009, one subject/session. Use existing native reader and
`benchmark.prepare(configs/classical_05.json)` unmodified; cached tensors must
match every saved M025 evaluation count/velocity/ID/unit/time exactly. Neural
coverage, original source partitions, go alignment, physical m/s conversion,
20ms half-open bins, −400:+1000ms and exclusions remain identical.
Counts2295×70×137; velocity2295×70×2. Source train1721, inner1377/344,
evaluation574. Retain exact IDs from M025. No fitted transform sees evaluation
outcomes; raw whole-file materialization is disclosed, not training access.

All CNN controls use seeds0/1/2, maximum200 full-batch Adam updates at0.001,
gradient clip1, existing standardized two-coordinate training MSE on all70bins.
Select minimum physical equal-trial MSE on inner344, bins4:70; first epoch wins
ties. Reinitialize from same seed and refit selected count on all1721training
trials. Training-only feature/target statistics, same shapes and unchanged model.
No tuning of capacity, clock representation, thresholds or loss after scoring.
Zero inputs retain valid scale1; clocks use train-fitted scale. Full-trial forward
passes reset trial context. Existing M025 real CNN200/20, Kalman, ridge, mean
and event template use stored predictions, never refitted or rewritten.
The zero/clock controls have equal nominal parameters but different effective
capacity/information. Train loss uses all70bins; all primary evaluation uses66.
Condition-template coefficients are training targets only, without iterative fit.

## Outcomes and uncertainty

Primary descriptive contrasts: original real CNN200 minus explicit-clock CNN,
and original real CNN200 minus permuted-training CNN evaluated on permuted neural
inputs. Average seed-specific loss within trial (not ensemble predictions).
Also report original-input inference for the permuted-trained model, zero CNN,
condition template, global event template and all historical comparators.
Prespecified descriptive support threshold: at least5% lower equal-trial MSE
and paired95% trial-difference interval strictly below0 for EACH primary contrast.
This is an interpretation rule, not a fresh confirmatory hypothesis test.
Retain all results even if no threshold passes. No gate permits additional models.

Use fixed10000 bootstrap draws, seed26; same joint trial resamples across paired
methods. Report ordered nonoverlapping blocks of5trials as sensitivity, including
last short block; no seeds/bins/bootstrap replicates treated as animals. Intervals
condition on fitted models and this session, not population-level inference.
Condition-stratified errors include condition/trial counts and template fallback.
Speed bins fixed [0,.1,.25,.5,infinity] m/s; direction four atan2 quadrants, with
speed<=1e-12 separately classed as stationary. Average within-trial stratum errors
first, report both participating trial and bin counts; descriptive strata only.
Report absolute/relative differences, seed spread, selected epochs, training curves,
batch inference time and total compute, not streaming/hardware latency.

## Integrity, verification and stopping

Commit source/config before execution after independent code/design review.
Use a new ignored `data/processed/m026` directory, immutable start/result markers;
no automatic repeat on failure. Save models, input digests, donor identities,
normalization, predictions, configuration, versions and source hashes. Restore
checkpoints and compare predictions exactly. Add synthetic tests for constant/clock
information, partition-safe derangement, singleton handling, template train scope,
stratification, target-shape checks and deterministic fitting/replay.
Independent reviewers check controls, saved scores and trial-aware contrasts.
Run software/data tests, historical integrity and M025 prediction preservation.
After one complete prespecified suite, stop. A failure must be documented and
reviewed before recovery; do not weaken evidence to obtain neural-information gains.

## Interpretation and publication

Task templates/clock controls are specific finite estimators, not an upper bound
on all task information. Permutation preserves within-trial covariance, temporal
shape and condition means but loses target-specific residual pairing. Singleton
conditions are incomplete nulls. Training permutation is a fixed surrogate,
not proof of conditional statistical independence or a causal neural mechanism.
Offline clock windows use a later go cue for pre-cue bins; no live event detection.
No subject/session invariance, adaptation benefit, new architecture, future velocity
prediction, Neuralink hardware or clinical BCI claim. Preserve prior negative results.
Publish a separate draft PR against M025 branch, explicitly stacked; do not merge,
tag, release or modify main. Application claims must identify this as retrospective.
