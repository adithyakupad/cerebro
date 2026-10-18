# External reviewer checklist

Use [the integrated manuscript](v1_1_manuscript.md), [statistical appendix](v1_1_statistics_appendix.md), [reproduction guide](v1_1_reproduction.md), immutable source JSON and original frozen protocols. Checkboxes are review prompts, not assertions that a reviewer executed them.

- [ ] Verify v1.0.0 and historical M022/M023 artifacts are unchanged; inspect source/config hashes and protocol-before-outcome history.
- [ ] Trace LINK source version, four development asset identities, SHA256, CC-BY-4.0 attribution and acquisition sample references.
- [ ] Confirm neural coverage is not inferred from spike extrema; note native volts/count conflict, clock jitter and absent quality masks.
- [ ] Confirm one animal, one source and three development dates are reported separately from trials, bins and 369 overlapping allocations.
- [ ] Verify source rows0:300 and inner225/75; development pool0:45/evaluation45:75; old evaluation rows75:375 excluded.
- [ ] Check same-bin offline decoding is not described as causal streaming or online BCI.
- [ ] Audit B-label versus B-command versus45-command versus45-unlabeled-neural information budgets.
- [ ] Recompute ddof0 prediction-dispersion identity, coefficient common-frame conversion and residual offset decomposition.
- [ ] Confirm M023 features never use evaluation target moments, evaluation probes or M022 post-hoc error diagnostics.
- [ ] Confirm risk preprocessing/model fitting excludes the held-out session and disclose nonchronological folds.
- [ ] Distinguish flexion² decoder loss, flexion⁴ risk loss and source-standardized count² neural loss.
- [ ] Check percentage aggregation differs between mean date-wise decoder/temporal ratios and aggregate risk ratios.
- [ ] Reproduce shared five-trial-block resampling across subsets; note fixed risk fits and missing biological/training uncertainty.
- [ ] Check undefined single-class fold balanced accuracy is not silently replaced by ordinary accuracy.
- [ ] Verify within-trial forecasting without teacher forcing, matched target bins, source-only preprocessing and fixed primary PCA6/h1.
- [ ] Inspect mean, persistence, permuted AR, channel AR, command metadata and matched-dimensionality controls.
- [ ] Test orthogonal-coordinate invariance and distinguish raw-count subspace geometry from standardized forecast error.
- [ ] Treat phase normalization as acausal descriptive matching; check supported-condition counts.
- [ ] Preserve all FA warning records; inspect the independent900-score Cholesky reproduction and Gaussian/count caveat.
- [ ] Verify all frozen gates fail and no alternative budget/family/threshold is promoted retrospectively.
- [ ] Confirm Feb24/Feb25/Jun26 native eligibility without scoring model outcomes; null-rule stop remains honored.
- [ ] Recreate tables/PDFs, restore checkpoints, run software/data tests separately and inspect package/dependency qualification evidence.
- [ ] Reject physiological-causation, subject-invariance, foundation-model or independent adaptation-benefit claims unsupported by these results.

Record actionable findings with severity, exact source/key, consequence and a reproduction step. Distinguish defects from valid negative hypotheses and from future research. Publication remains subject to owner approval; review does not authorize scoring the reserved cohort.
