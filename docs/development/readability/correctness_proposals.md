# Correctness issues excluded from the readability refactor

Baseline: `d506ff408b62a7d79b14c59987f20c1d7b46fef4`.
Neither proposal is implemented. A style-only branch must retain historical numerical behavior, including known defects. No historical claim is revised on the basis of these demonstrations.

## Permuted-risk ridge parameter

`cerebro.reliability.evaluate_risk` passes `config['reliability_ridge_alpha']` to actual risk fits, but calls `fit_risk(features[training], permuted_outcomes, MODELS['combined'])` for its permutation control. That call takes default alpha=1 even when the requested penalty differs. A nondefault-alpha comparison therefore has an unmatched regularization control.

Independent fix: pass the same configured alpha to the null fit. Regression: use a nondefault alpha (for example, 17), spy on every `fit_risk` call including all three permutation folds, and independently reconstruct the seeded permutations/folds to verify the resulting predictions. Keep tests for default alpha=1 exact.

Scientific requalification: frozen M023 uses alpha=1, so the missing argument does not change that study's penalty. Reproduce its arrays to establish that expectation; separately qualify any future nondefault-alpha study and invalidate unmatched controls rather than silently correcting historical artifacts. No evidence here establishes that a historical nondefault-alpha scientific experiment was executed.

## Broadcast-compatible target shapes

`cerebro.sequence_benchmark.train_epoch` computes squared prediction-target differences without requiring identical shapes. A model producing (4,2) and labels shaped (4,1) produces finite loss and changes weights through NumPy/PyTorch-style broadcasting. This is an actual software contract defect when coordinates are intended to match.

Independent fix: validate prediction and target shapes immediately after forward prediction and before subtraction, backward propagation or the optimizer step. Do not blanket-reject every broadcast elsewhere in the codebase: explicitly intentional broadcasting is part of valid vectorized algorithms.

Regression: matching shapes still train identically; singleton coordinate, bin and trial dimensions fail with an informative `ValueError`. Compare model and optimizer states before/after rejection; do not accept a partially updated model. Since a forward pass can mutate running-state buffers in general models, scope that guarantee carefully or validate available static dimensions before forward execution. Existing CEREBRO sequence architectures have no BatchNorm running statistics.

Audit all `train_epoch` callers and the separate `_train_supervised` path before a dedicated fix. Current experiment preparation constructs paired feature/target tensors with matched trial/bin/coordinate dimensions, and the refactor replays those paths exactly. That is not proof that arbitrary external callers were safe. Requalify any experiment found to have actually broadcast targets; never reinterpret or replace its old results silently.

## Other observed limits

The SENSE inspector serializes native NWB object representations in the electrode CSV. Their memory addresses differ between processes. Four PNGs, 31 saved arrays, scientific report fields and the other two CSVs reproduced exactly; the electrode CSV matches only after stripping object-address text. Serialization behavior was not changed. A future portable-metadata change needs its own contract and regression test.

Historical source guards hash entire modules, not only model topology. This branch leaves eight hash-bound package files plus the pinned Brochier population and M017 diagnostic generators unchanged. Refactoring these later requires a separately designed versioned provenance contract, archival source replay and explicit review; replacing hashes in historical reports or disabling guards is not an acceptable shortcut.


## Additional pre-existing historical identity provenance blocker

The default `configs/subject_identity_13.json` points to `data/processed/cross_subject_12/results.json`. Its producer `cross_subject.py` hash is `d762673870a18120b193b6be3af9f4b16aec52bfc1a32b8cc5eec3692e9a7692`; the baseline file at d506ff4 hashes to `6a56c8329422308e0430d1357fc8eea39d72bae93c5affc9990bc5ff48593e81`. The FALCON adapter hash matches. Therefore the historical consumer rejects this exact local input with `Frozen decoder preparation code differs from current source` even before refactoring. Existing synthetic tests generate mutually matching source/report fixtures and do not establish compatibility of this historical default path.

The refactor leaves `cross_subject.py` byte-identical to baseline, preserves this guard and does not overwrite the historical report. This limitation is outside the two initially identified defects and must not be described as a passing historical workflow.

Independent resolution: recover and verify the exact original producer source snapshot, or generate a separately named, lineage-verified producer/identity chain in scratch using a reviewed compatible revision. Compare every original trial assignment, normalization, prediction and decision before accepting a successor artifact. Never replace the old report hash just to satisfy the guard. Add a historical-artifact compatibility test that checks the default input's producer binding before any fitting. This is a provenance/reproduction task, not evidence of a changed scientific result or permission to rerun untouched evaluations.
