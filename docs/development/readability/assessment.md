# CEREBRO readability assessment and refactor

Baseline HEAD: `d506ff408b62a7d79b14c59987f20c1d7b46fef4`, initially clean, package1.1.0. Review branch: `codex/readability-refactor`, based on the existing stacked research branch rather than rewriting either PR. No publication/merge/tag approval was supplied by this task.

Scope: all81 maintained Python files in `src/`, `tools/` and `tests/`. [The inventory](inventory.json) lists every changed and unchanged file with before/after SHA256, module purpose, functions and rationale. [Baseline protection](baseline.json) records201 research/configuration/release documents and413 local checkpoint/array files. These counts do not claim every raw dataset was downloaded anew.

## Inputs, outputs and invariants by subsystem

| Subsystem | Inputs → outputs | Scientific/numerical invariants | Decision |
|---|---|---|---|
| Acquisition/native parsing | Pinned manifests/native files → verified recording metadata and trials | Asset identity, authentic coverage, native clocks, unit conversions and errors | Keep already explicit download/NWB/LINK/FALCON adapters |
| SENSE/events | Spikes/events/behavior → complete-bin counts, masks, condition tensors | Half-open windows, picosecond edge policy, no extrapolation, original trial IDs, coverage exclusions | Expose bin offsets/indices, state buffers, residuals and covariance stages |
| Characterization/plotting | Counts or saved reports → statistics and scientific figures | Identical counts/units/weights, no fitting in renderers, no figure/report content changes | Name per-unit extraction and edge-center/CDF calculations; separate plotting statements |
| Classical models | Training observations/targets → selected/fitted models and held-out predictions | Train-only transforms, same masks, PCA/FA/Kalman dimensions/penalties, float operation grouping and checkpoint keys | Clarify benchmark masks/features/targets and posterior solve; retain already readable population/Kalman code |
| Sequence/SSL | Trial tensors → same models, losses, histories and outputs | Causal masks, architecture/state dictionaries, float32/device, RNG consumption and optimizer sequence | Clarify normalization/transfer; retain sequence architectures and hash-bound SSL module |
| Cross-subject/evaluation | Independent recording trials → fixed partitions, predictions and block intervals | Feature correspondence, no assumed unit identity, same source selection, calibration access and resampling calls | Expose fit/predict stages, identity projections and block-index arrays |
| Reliability/population dynamics | Fixed development partitions → diagnostic/gate outputs | Frozen criteria, session masks, no new labels or untouched-session scoring | Assess but preserve hash-bound files; propose correctness fixes separately |
| CLI/report/test infrastructure | Verified inputs → portable artifacts/assertions | Same APIs, serialization/attribution, rejection paths and historical lineage | Keep already procedural tools; clarify checkpoint scaling and one two-assert test line |

Independent bounded reviewers covered ingestion, models and transfer/evaluation. The lead reviewed affected callers/diffs and remaining plotting/tool/test infrastructure. Full-suite and direct before/after replay complement manual review; neither proves all possible external inputs equivalent.

## Material changes, not blanket formatting

1. `benchmark.py` used `inner_x`, `inner_z`, `inner_y` and nested matrix/reshape expressions across split selection. Names now reveal training/validation scope and counts/features/targets. Fitting order is unchanged.
2. SENSE/event code combined multiple state mutations and dimension labels on one line. Lists and updates now appear independently; formulas expose search indices and covariance cross-products.
3. Sequence/transfer helpers combined selection, flattening, normalization, fitting and prediction reshaping. Meaningful intermediates make each dependency available for inspection.
4. Cross-subject block statistics and checkpoint affine projections now name their stages. No new helper classes, callback layers, model families or dependencies were introduced.
5. Already clear adapters, Kalman/sequence architectures, trust-boundary checks and compact test fixtures remain unchanged. Scientific assumptions, timing/leakage comments, licenses and attribution remain.

## Before/after examples

```python
# Before
counts = np.searchsorted(spikes, right, side="left") - np.searchsorted(spikes, left, side="left")

# After
stop_indices = np.searchsorted(spikes, right, side="left")
start_indices = np.searchsorted(spikes, left, side="left")
counts = stop_indices - start_indices
```

```python
# Before
inner_x = counts[inner_train].reshape(-1, features_number)
inner_z = scaler.fit_transform(inner_x)

# After
inner_training_counts = counts[inner_training_mask].reshape(-1, num_units)
inner_training_features = scaler.fit_transform(inner_training_counts)
```

```python
# Before
predictions = classifier.predict(scaler.transform(evaluation_rows))

# After
normalized_evaluation = scaler.transform(evaluation_rows)
predictions = classifier.predict(normalized_evaluation)
```

```python
# Before
indices = blocks.reshape(draws, -1)[:, :len(identities)]
sampled_means = trial_means[indices].mean(axis=1)

# After
block_indices = blocks.reshape(draws, -1)
indices = block_indices[:, :len(identities)]
sampled_losses = trial_means[indices]
sampled_means = sampled_losses.mean(axis=1)
```

## Source-lineage constraints discovered and retained

The v1.1 review manifest requires six source files byte-identical to the reviewed candidate. The historical checkpoint validator also hashes the entire `representation_benchmark.py` as its architecture identity. Initial readability edits to that module triggered its guard; they were reverted completely, after which checkpoint replay passed. No historical hash or guard was modified. `tools/brochier_population.py` and `tools/diagnose_mission_017.py` are also explicitly tied to historical reports and remain unchanged.

Thus this is a repository-wide assessment with selective refactoring, not a claim that every dense expression was rewritten. These provenance-bound files retain opportunities for clearer expressions. Their future refactoring depends on a separately reviewed archival/versioned provenance contract; byte identity cannot coexist with source edits. Numerical equivalence alone must not be represented as unchanged source provenance.

## Verification and remaining limits

See [verification](verification.json) for executed counts, digests, numerical comparisons, memory/runtime measurements and checks not executed. Historical outputs are immutable: new verification runs write only scratch/ignored audit destinations. Source hashes/Git revision in *new* reports necessarily differ after refactoring; scientific values are compared separately, without changing old reports. No known defect was silently fixed and no test assertion/tolerance was weakened.

Whole-file Ruff formatting is not a repository policy. Its optional check reports existing legacy formatting in both baseline and branch; a wholesale formatter rewrite would add unrelated churn and invalidate frozen source hashes. Installed Ruff correctness/compound-statement checks and whitespace/compilation checks are reported separately.

[Correctness proposals](correctness_proposals.md) describe the nondefault-alpha risk control and broadcast-compatible training labels. [The comprehension guide](guide.md) identifies ten functions to trace and reconstruct independently. No new scientific hypothesis, model selection or independent validation outcome was generated by this refactor.
