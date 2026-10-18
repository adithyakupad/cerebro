# Statistical methods and result traceability

This appendix integrates preserved protocols; it changes no analysis or gate. Read the [manuscript](v1_1_manuscript.md) and the original [M022 protocol](m022_protocol.md), [M023 protocol](m023_protocol.md), and [risk clarification](m023_reliability_clarification.md).

## Independent units, weights and dimensions

Each neural trial has counts Xᵢ of shape Tᵢ×96 and normalized flexion Yᵢ of shape Tᵢ×2. Trials keep native IDs qualified by session. There is one biological subject, one source date and three development dates. Evaluation contains30 trials/date; calibration subsets overlap. Neither bins nor bootstrap/subset draws constitute additional subjects or sessions.

For prediction Ŷᵢ, trial loss is Lᵢ=Σₜₖ(Ŷᵢₜₖ−Yᵢₜₖ)²/(2Tᵢ). Session loss is the mean over its30 trials, not a pooled-bin mean. Dates contribute equally. Decoder loss and direct-minus-frozen adaptation difference Δ have units flexion². MSE of predictions of Δ has units flexion⁴. Neural forecasts average common valid within-trial targets and96 source-standardized contacts; their units are standardized count².

For M022 mitigation and M023 temporal gates, relative improvement is the **mean of date-wise ratios**, meanⱼ[1−Lmodel,j/Lcontrol,j]. For M023 reliability, the prespecified clarification uses **one minus the ratio of equal-date risk MSEs**, 1−meanⱼ(Rmodel,j)/meanⱼ(Rcontrol,j). These are not interchangeable. CSV exports retain the original names and values.

## Calibration allocation, bias and dispersion

Chronological selects first B trials. Uniform samples B without replacement from45 pool trials, using20 fixed draws. Balanced randomizes within commanded conditions and cycles remaining condition groups until B, then sorts selected rows chronologically. It reads all45 command labels and may use later trials, unlike chronological selection. B∈{5,15,30}; no selection receives evaluation outcomes.

For K calibration-subset predictions pₖ and their pointwise mean p̄, the empirical identity is

    meanₖ[(pₖ−y)²] = (p̄−y)² + meanₖ[(pₖ−p̄)²].

Apply identical time/target, trial and date weights to both sides. The second term uses ddof0. Ensemble error is not identified physiological bias; irreducible variation and mismatch remain. Across-subset coefficients are transformed into raw-count axes before computing dispersion (standardized coefficient divided by the fitted scale). For residual correction, source and correction weights are combined before comparison. Effective ridge degrees of freedom exclude the intercept; correlated bins do not supply independent trial replication.

For trial residual eₜₖ, its time mean mₖ separates squared error exactly into meanₖ(mₖ²) plus meanₜₖ[(eₜₖ−mₖ)²]. This distinguishes offsets from centered errors, without identifying why either changed.

## Reliability features and fitting

Coverage uses selected command labels; instability resamples whole trials20 times **within the same B position labels** and probes predictions on45 unlabeled pool trials; shift measures calibration neural-mean differences in source-standardized axes; disagreement probes frozen versus direct predictions on the same pool. Label-only target moments and task/label controls account for behavioral sampling. Dynamics mismatch uses recorded neural forecast errors on only the selected B calibration trials; it does not probe the additional pool observations. Evaluation target statistics and M022 post-hoc evaluation-error diagnostics are prohibited inputs.

Each fixed risk model uses ridge alpha1. Training-only scaling and fitting exclude the entire held-out development session. Folds may include a training date later than the held-out date, so are not prospective chronological deployment. Primary labels use20 uniform allocations/date at B15. Single-class fold balanced accuracy is undefined. Promotion uses pooled two-class balanced accuracy with equal session weights; if only one class exists globally the gate fails. The adaptive action Δ̂<0 is a separate policy endpoint, not guaranteed beneficial by risk accuracy.

## Conditional uncertainty

All primary intervals use1,000 moving-five-trial-block draws within fixed sessions. Contiguous blocks preserve some local trial dependence but do not establish that longer dependence is absent. For reliability, identical ordered evaluation-trial indices are shared across overlapping allocations before recomputing their Δ labels, while fitted risk parameters stay fixed. Sessions are equally weighted. This targets conditional evaluation-trial variation, not full risk-training uncertainty, biological variability or unseen-session uncertainty. Training-date-only risk fits separately expose parameter sensitivity. Exploratory diagnostic multiplicity is not corrected; no population p-value claim is made.

## Population model and invariances

PCA/FA fits use source300 or target pool15/45 only. Fixed affine ridge AR1 predicts latent states at horizons1/5 from the actual starting observation without future teacher forcing; transitions never cross trial boundaries. Reconstructed forecasts are scored in a common source-standardized neural frame; contemporaneous reconstruction and coordinate-dependent latent error remain separate. Orthogonal coordinate transformations must preserve reconstructed predictions and subspace angles. Principal-angle comparisons map loadings into common raw-count contact axes, a different weighting from standardized error. The model is static observation coordinates plus AR, not a jointly fitted latent dynamical system/Kalman smoother.

Temporal permutation acts within training trials; held-out trials are untouched. Training mean, independent-channel AR, latent/raw persistence and command controls prevent attributing all denoising or task mixture to dynamics. Command controls explicitly receive held-out commands; phase-matched trajectories are acausal descriptive summaries requiring≥2 repetitions per matched condition. They do not prove movement-event correspondence or physiological invariance.

FA uses Gaussian observation likelihood, not count likelihood. Preserve2,700 recorded library slogdet warnings. Independent raw-covariance Cholesky scoring reproduced900 trial means over30 FA comparisons to maximum absolute8.53×10⁻¹⁴. Finite scores and reproduction do not validate distributional assumptions; primary PCA forecast MSE is separate.

## Exact result-key map and reproducible tables

| Manuscript quantity | Immutable JSON and key path |
|---|---|
| Source alpha/count/units | `reports/m022_calibration_mechanisms.json`: `selected_source_alpha`, `source_training_bins`, `source_metadata` |
| Calibration loss/dispersion/offsets | Same: `sessions[*].groups[*].models` and `draw_diagnostics` |
| Allocation contrasts | Same: `diagnostic_contrasts` |
| Seven mitigation decisions/intervals | Same: `promotion.candidate_decisions[*].comparisons` |
| B15 reliability MSE and accuracy | `reports/m023_reliability.json`: `evaluation.budgets.15.models[*].risk_mse_flexion4` and `pooled_session_weighted_balanced_accuracy` |
| Reliability intervals/ratios | Same: `evaluation.budgets.15.comparisons` |
| Per-date risk/action outcomes | Same: `evaluation.budgets.15.models[*].per_session` |
| Temporal primary effects/intervals | `reports/m023_dynamics.json`: `temporal_gate.comparisons` |
| Forecasts/geometry/warnings | Same: `sessions[*].comparisons`, `sessions[*].covariance_frobenius_cosine`, `sessions[*].condition_matching` |
| Hashes and fit revisions | Each report's `arrays`, `source_sha256`, `git_revision`; M022 `lineage`, M023 `config_sha256` |

`models[*].risk_mse_flexion4` is the preserved aggregate field; tables also export every per-session field to expose the weighting. Regenerate CSVs using only committed statistics, without data downloads, fitting or scoring:

```sh
conda run -n cerebro python tools/m024_tables.py
```

Outputs: [M022 gates](../../reports/v1_1_tables/m022_promotion.csv), [all reliability budgets/models/dates](../../reports/v1_1_tables/m023_risk.csv), [temporal primary](../../reports/v1_1_tables/m023_temporal.csv). Full machine reports remain the authoritative unrounded record and include complete secondary ablations. The release verification checks table determinism against these inputs. Figure regeneration and authentic-data reproduction are separate operations in the [reproduction guide](v1_1_reproduction.md).
