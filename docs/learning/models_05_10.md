# Population models, decoding and transfer

**Prediction.** Neural population features may improve held-out behavior prediction,
while temporal context or calibration may help. More complexity and pretraining
are not presumed beneficial.

**Learn.** PCA maximizes training variance; FA separates a low-rank Gaussian shared
component from diagonal noise. Both here use standardized20 ms counts fitted on
training only. Sparse counts are not Gaussian observations, so FA is approximate.
Reconstruction loss can favor the largest PCA candidate without identifying an
intrinsic neural dimension.

Linear/ridge models predict behavior from current features. Kalman models describe
behavior dynamics and their neural observation relationship. Recurrent, convolution,
attention and diagonal state-space baselines use prior/current neural bins. Resetting
state at trial boundaries prevents invented continuity. A one-step latent AR forecast
using observed previous states is not a free-running physiological dynamical model.

**Implement.** Immutable trial lists precede fitting. Inner selection never sees
source validation; target calibration never sees target evaluation. Same-bin offline
predictions become available at bin-right time. Counts, rates, velocity(m/s), native
finger flexion and arbitrary latent coordinates retain distinct units.

**Interrogate.** Mean and event-time templates, random frozen representations,
supervised-only models, limited-label prefixes and altered-time fitting controls
can reveal weak effects or shortcut learning. Pretraining masks count features and
predicts the next bin within the same trial; it does not receive the target session's
held-out observations. Session identity may remain implicit in neural distributions
even when dates and subject IDs are excluded from the model input.

**Validate.** A seed is not a biological replicate. Trial/bootstrap uncertainty
requires independence assumptions; moving-block sensitivity does not validate those
assumptions. Same contacts across days do not imply the same neurons. CCA fitted
on a few condition anchors can overfit; principal angles are descriptive geometry,
not connectivity. Recalibration can worsen predictions. Small mixed SSL/random
control differences do not establish a validated neural foundation model.

**Human decision.** Resolve coverage assumptions and choose a valid cross-subject
target/correspondence policy before biological generalization claims. Final model
selection needs an untouched evaluation protocol and a new scientific hypothesis.

## Cross-subject coverage and anonymous features

Recorded observation intervals distinguish an observed zero-spike bin from
unknown acquisition. The human requires that evidence; behavior alone does not
certify neural coverage. FALCON supplies native intervals for both monkeys.
Unit IDs remain subject-specific. Mean, spread, sparsity and quantiles of counts
are permutation-invariant population summaries, deliberately discarding unit
selectivity; transfer failures do not disprove richer shared representations.
Matching muscle names establishes output coordinates, not equal gain or anatomy.
Author-normalized EMG cannot be interpreted as calibrated physical mV. Compare
calibration against its own mean to distinguish neural prediction from baseline
adjustment, and keep target evaluation out of every fit and selection step.
