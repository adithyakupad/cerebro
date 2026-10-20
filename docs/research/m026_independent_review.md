# M026 independent scientific and provenance review

## Scope and review state

Independent review of the frozen M026 control design, source implementation and
existing M025 evidence. Protocol commit `014e06a`; implementation `deecf12`;
additional guards `bb89524`; progress logging and native condition inventory
`b8ebe5f`. This reviewer did not select controls from new validation outcomes,
fit models, or execute a new experiment. **Pre-fit review: PASS for the bounded
retrospective diagnostic claim. Final-output review: PENDING.**

## Direct checks completed

- Read `docs/research/m026_protocol.md`,
  `configs/m026_neural_information.json`, `src/cerebro/neural_information.py`,
  `src/cerebro/neural_information_controls.py`, and `tools/m026_prepare.py`.
  Traced callers into normalization/training, causal CNN, physical metrics,
  spike/behavior preparation and condition-key validation.
- Independently checked existing standard M025 predictions against
  `reports/m025_final.json`: all **40 array digests**, **eight numerical
  checkpoint/archive file hashes**, and **11 primary per-trial MSE arrays**
  reproduced exactly. This used stored historical outputs, not new model scores.
- Confirmed common original validation identities and target arrays for all
  historical comparators: 574 trials, 137 held-in units, 70 bins, two physical
  velocity coordinates. Primary scores use zero-based bins 4–69 (66 bins).
- Reviewed regression-test source covering cache/array/source lineage rejection,
  split corruption, partition-safe donor assignment, deterministic fitting and
  checkpoint restoration. The lead agent must record executed test counts;
  this receipt does not claim this reviewer independently ran those tests.

## Findings and dispositions

| Finding | Classification | Disposition / evidence |
| --- | --- | --- |
| Historical feature replacement is partial, not no-neural | Interpretation constraint | Replaces 13/137 columns at inference; preserves 124 columns and task structure. Fractional mean counts/disrupted joint dependence can cause distribution shift. New trained zero/clock controls address different questions. |
| Constant CNN cannot express primary-window task phase | Design constraint, resolved | Two width-three causal convolutions have five-bin receptive field. Padding affects first four bins, excluded from scoring. Protocol explicitly distinguishes constant-input CNN from separate explicit-clock CNN. |
| M025 validation is already inspected | Scientific limitation, disclosed | All M026 validation comparisons are retrospective, single-session diagnostics. No untouched/independent confirmation claim is permitted. |
| Family fitting masks and objectives differ | Benchmark limitation, disclosed | CNN/Kalman train all70bins; ridge target fitting starts at bin4. CNN trains standardized coordinate MSE; physical MSE selects all methods and scores common observations. New matched CNN controls preserve original CNN masks and objective. |
| Condition permutation is one fixed surrogate | Scientific limitation, disclosed | Fixed cyclic derangement avoids nonsingleton fixed points, preserves condition/clock/whole-trial covariance, but does not establish conditional independence or remove all neural information. Singleton identity is retained and counted. |
| Evaluation metadata is additional information | Information-budget constraint | Condition template/permutation use recorded compatible-condition metadata, not validation velocity to fit/select. Explicit clock and conditions are offline task inputs; availability in live use is not established. |
| Original cache dtype differed before preparation correction | Pre-fit representation defect, corrected | Native bin counts are converted to float64 before comparison/caching, matching original M025 `optimization_study.run`'s `.astype(float)`. Shape/value equality and dtype-sensitive digests must both match. No old result or scientific preprocessing changes. |
| Replay could otherwise accept replacement cache provenance | Engineering safeguard, resolved | `bb89524` compares checked input lineage with experiment-recorded lineage and regression-tests rejection. It also verifies original M025 file hashes before fitting. |
| Long-running fitting needs visibility | Engineering safeguard, resolved | `b8ebe5f` adds flushed progress every50epochs and renames an unused loop index. It introduces no RNG calls, altered numerical transformations or selection rules; only timing overhead changes. |

No blocking scientific design or implementation defect was identified in this
pre-fit review. This is not proof that every conceivable defect is absent.

## Data, split and access trace

Pinned DANDI `000128/0.220113.0400`, asset
`26e85f09-39b7-480f-b337-278a8f034007`, SHA256
`a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4`.
Existing native observation intervals, clock and physical-velocity metadata are
recorded in `docs/research/m025_evaluation_eligibility.{md,json}`. Preparation
checks the exact asset and uses unchanged `benchmark.prepare` with frozen
`configs/classical_05.json`: go cue −400:+1000ms, half-open20ms bins, complete
within-trial neural coverage and behavioral gap limit2ms. Bin-right predictions
reconstruct same-bin mean velocity, not future movement.

`m026_prepare.py` verifies exact M025 evaluation count/target/trial/unit/time
arrays and their existing digests, plus unchanged exclusions. `checked_inputs`
verifies cache/file/array lineage, exact ordered identities and source/inner
partition separation. The inner union must equal source training.
Normalization fits only on inner-training IDs for selection, or all original
source-training IDs for final refits. Donor mapping never crosses the supplied
partition; recipient velocity targets stay in place. Inner and full permuted
arrays are separate. Fixed seeds, unchanged CNN, common optimization cap and
physical-MSE selection are committed before fitting. Existing M025 predictions
are read, not refitted or overwritten.

Native condition-only inventory (`reports/m026_condition_inventory.json`)
records 108 compatible conditions in full training and validation: training
13–20repetitions, validation4–7. Inner validation has104conditions and10singleton
trials; retain this imperfection in interpretation. No unseen validation task
condition is implied by the original split. This inventory is metadata, not a
neural decoding outcome or an independent biological replication.

Original M025 values and partial-neural interventions remain historical evidence.
Repeated trials, model seeds and bootstrap samples are not independent subjects.
The trained task templates/clock CNN are finite estimators, not upper bounds on
all task information. A real-neural advantage over them remains bounded by
model/representation adequacy and one previously inspected session.

## Pending final-output review

Before claiming M026 completion, independently inspect saved results and:

1. Recompute equal-trial metrics, seed averaging, primary paired intervals and
   ordered-block sensitivity from saved arrays.
2. Verify donor maps, singleton counts, condition-template fallback and scored
   trial identities; reproduce condition/speed/direction strata as practical.
3. Verify all checkpoint restoration and output hashes, retained M025 hashes,
   immutable start markers, report/figure lineage and actual test receipts.
4. Confirm conclusions distinguish neural dependence, task information,
   distribution-shift sensitivity and retrospective uncertainty; preserve every
   result, including any failed descriptive gate.

No new fitting, additional held-out cohort, GPU/live-BCI operation or across-session
biological generalization was checked by this pre-fit review.
