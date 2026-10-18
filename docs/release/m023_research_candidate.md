# Proposed CEREBRO research release: M023

**Unreleased research candidate. No tag or merge is proposed automatically.**

This candidate adds a narrow, reproducible longitudinal neural-data case study to v1.0.0 and the separately reviewable M022 contribution. It tests calibration-only predictors of adaptation harm with whole-session-held-out evaluation, and source/local PCA/FA plus linear latent forecasts with explicit observation, behavioral, temporal and dimensionality controls.

The reliability candidate fails the prespecified gate against constant, label-only and shift controls. The fixed temporal model improves neural forecasts but misses the practical effect requirement against training-mean and temporal-permutation controls. All ablations, negative findings, numerical warnings and information budgets remain visible. New compatible recordings are acquired and audited without consuming model outcomes after failed development gates.

Included evidence: [manuscript](../../reports/m023_manuscript.md), A/B machine reports, figures, editable ten-slide research presentation, [reproduction guide](../research/m023_reproduction.md), [interview evidence pack](../research/m023_interview_pack.md), native provenance and scientific/engineering review records. Raw recordings and numerical checkpoints are not bundled. Data attribution remains separate from the MIT software license.

Recommended decision: publish the research PR as a transparent negative case study for external review after applicable tests and independent review pass. Do not market it as independently validated harm avoidance, physiological neural drift, subject-invariant representation, clinical BCI or neural foundation-model generalization. Preserve v1.0.0 and PR2; any merge/tag requires explicit owner approval.
