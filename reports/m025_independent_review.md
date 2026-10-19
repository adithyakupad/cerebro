# M025 independent review

## Before real-data training

Separate reviewers audited decoder implementation, methodology and native-data
provenance. The frozen protocol is commit7f756c2; implementation477ed95.
Review identified a reversed verification API call and incomplete final-access
evidence checks; both were corrected before fitting. Regression tests cover
committed config/protocol/source evidence, stale cache rejection, finite gate
losses, promotion/eligibility failures, paired trial/block resampling and shared
short/long-cap trajectories. 31 focused tests passed before genuine-data training.

The existing target-shape defect was corrected separately in ce588f5. Correct
shapes preserve exact loss, parameter updates and RNG consumption. The unrelated
nondefault permuted-risk ridge-alpha defect is not used by this experiment and
remains a separately documented correction proposal.

## Development review before prospective evaluation

An independent reviewer recomputed from saved predictions, without fitting or
standard-validation access:

- Every file, array, source and protocol hash matches; published/cache reports agree.
- Each model's paired trial loss and all three contrasts' 10,000-draw trial and
  ordered-block-five bootstrap intervals reproduce exactly.
- CNN20 inner curves are exact prefixes of CNN200 curves; selected epochs minimize
  the corresponding physical inner-validation error.
- Original 75/25 and inner60/15 identities remain unchanged and disjoint.
- Development promotion is 18.60118134%, above the frozen5% gate. It remains
  selection-conditioned development evidence, not an independent effect estimate.
- Every development evaluation condition is a singleton: the permutation changes
  zero of25trials. This control is **NOT INFORMATIVE**, not a passed neural null.
- All three CNN20 prediction arrays match historical sequence06 predictions exactly.

The prospective eligibility reviewer supports the bounded claim of a previously
performance-unscored Sep25recording, not never-opened raw data or new subjects.
The historical eager-loading exposure and lack of private/unlogged-use proof
are disclosed in docs/research/m025_evaluation_eligibility.md. Finite target and
spike-conservation execution guards remain mandatory.

## Disclosed pre-scoring numerical failure and recovery review

The final attempt stopped in the validation check, before any final metric/report,
after saving seed0 CNN20/CNN200 and classical parameters. Float32 cross-length
roundoff exceeded the new runner's1e-6 assertion. Synthetic diagnosis reproduced
the discrepancy; double-precision structural prefix/future checks passed. No
final behavioral labels were used for this diagnosis. See m025_numerical_failure.json
and m025_failed_attempt.txt; the failure is preserved, not hidden.

An independent reviewer approved a validation-only correction: production float32
parameters/predictions remain unchanged; a copied double model must pass prefix
and same-shape future perturbation at1e-12, including rejection of an acausal fixture.
This does not assert bitwise production-float32 future invariance.

Recovery regression tests verify checkpoint-byte/prediction preservation without
refitting saved models, matching selected epochs/normalization, rejection of
unauthorized method-source changes and authentication of every preserved artifact
and reviewed source hash. 22 study tests passed; the complete software subset
then passed289tests. Original development/source/protocol lineage remains immutable.
Only the exact reviewed runner hash may bridge the validation correction; all
other method hashes still must match. The original marker and partial artifacts
are preserved and a second exclusive recovery journal is mandatory. This is a
reviewed continuation before the first loss calculation, not another final outcome
selection or an alternate dataset. No thresholds, architecture, splits or seeds change.
