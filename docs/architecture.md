# Scientific architecture

CEREBRO studies adaptive neural intelligence: representations supporting neural
population analysis, behavioral decoding, longitudinal comparison and calibration.
These capabilities require separate empirical validation; model implementation
alone does not establish scientific success. The authoritative delivery status is
[the completion matrix](research/completion_matrix.md).

| Boundary | Current implementation | Inputs and outputs |
| --- | --- | --- |
| SENSE | `sense`, `dataset`, `nwb_audit`, `link` | Verified NWB assets → original clocks, trials, session/subject/contact or unit IDs, observations, masks and explicit metadata ambiguities |
| MAP | `population`, `event_aligned`, `dynamics` | Training observations → PCA/FA, covariance, principal angles, latent coordinates and trial-local one-step dynamics |
| DECODE | `benchmark`, `kalman`, `sequence_models`, `sequence_benchmark` | Training neural features → mean/event-time/linear/ridge/Kalman/MLP/GRU/LSTM/CNN/Transformer/diagonal state-space predictions |
| REMEMBER | `nwb_audit`, LINK contact mapping, `longitudinal` | Session-scoped identities → explicit contact correspondence, covariance/subspace/condition-anchor comparisons; no persistent-neuron inference |
| ADAPT | `longitudinal` | Frozen source predictions and disclosed target calibration → direct recalibration, residual correction, marginal normalization and condition-anchor latent alignment |
| FOUNDATION | `representation_benchmark`, `representation_transfer` | Masked/predictive pretraining → random/supervised controls, frozen probes and fine-tuning; foundation-model validity is not assumed |
| INTERACT | `explorer` | Hash-verified stored results → local trial/model/trajectory exploration; unavailable outputs are identified |
| Research engine | configurations, immutable split manifests, `registry` | Source and configuration identities → checkpoint/array lineage, versions, seeds, metrics and reproducible commands |

Raw recordings remain immutable and Git-ignored. Source releases, asset IDs,
published checksums, license and reference clocks precede preprocessing. Splitting
precedes any fitted normalization, representation, decoder, alignment or model
selection. Training and calibration identity lists are written to immutable local
manifests; changing a split requires a new experiment output directory.

Within-session Maze uses source `train` and `val` labels, preserving the separate
published test asset. Inner training/validation selects dimensions, ridge penalty
and sequence epoch counts; refitting uses source training only. Source validation
has now been examined for exploratory reporting and is no longer an untouched
final test. No eventual final model should be selected from those results.

LINK stores sampled threshold-crossing features, not sorted units. Its explicit
trial references govern retention, including excluded endpoint samples. Native
contact coordinates can be matched within the same monkey and acquisition setup;
this does not assert stable neurons. Native threshold-crossing `volts` metadata
conflicts with the count description and integer values; interpretation and source
labels are retained separately. Finger flexion targets are not pooled with Maze
hand velocities. Perich–Miller lacks neural observation intervals in the inspected
pair, so unobserved coverage is kept unknown rather than synthesized.
The human requires documented neural coverage. FALCON calibration recordings
provide explicit observation intervals for two monkeys; their separate EMG
experiment uses anonymous population summaries without cross-subject neuron
mapping. Published EMG is author-normalized despite native mV labels and remains
separate from Maze velocity and LINK finger flexion.

Chronological source fitting/selection and target calibration/evaluation partitions
remain distinct. Unsupervised target marginal normalization receives only disclosed
calibration neural features. Direct recalibration receives labeled calibration
trials. Condition-anchor alignment additionally uses commanded-target metadata;
it does not imply paired cross-day trials. These access policies must accompany
comparisons. Covariance, CCA and principal angles never imply causal connectivity.

Sequence models preserve trial boundaries and reset hidden states per trial.
Causal neural access means past/current bins available at their right edge;
contemporaneous behavior prediction is offline replay. The explorer controls no
hardware. Neither simulated perturbation nor offline decoding is biological
closed-loop operation.

Human researchers own model selection, evaluation design, interpretation and
conclusions. Automated agents implement and critique explicit comparisons and
retain negative findings. Cross-subject transfer, validated foundation-model
claims and final release status require their own acceptance evidence.
