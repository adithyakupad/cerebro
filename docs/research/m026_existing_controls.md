# M026 independent existing-control and benchmark audit

Audited M025 head `552e50bcd44004895fa75eea7d9345b15e89fc2c` without
fitting models, changing stored outcomes or selecting new controls from evaluation
performance. This review reads source and already published/saved M025 outputs.

## Scope and direct verification

Standard MC_Maze is DANDI `000128/0.220113.0400`, asset
`26e85f09-39b7-480f-b337-278a8f034007`, SHA256
`a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4`.
The frozen eligibility record is
[`m025_evaluation_eligibility.md`](m025_evaluation_eligibility.md).
There are 2,295 retained trials, 70 bins/trial, 137 held-in units and two physical
velocity coordinates; no coverage exclusions. Original source partitions are
1,721 training / 574 validation; the training-only internal split is 1,377 / 344.
The same animal was recorded separately from Small development; no unit
correspondence, subject independence or decoder transfer is established.

Read-only recomputation confirmed all **40 saved array digests**, **eight saved
checkpoint/archive file hashes**, and **11 per-model primary trial-loss arrays**
exactly against `reports/m025_final.json`. Every primary metric uses the same
saved `target`, original `trial_ids`, and zero-based bins `4:70`: 574 trials ×
66 bins × two coordinates. MSE averages coordinates and bins within a trial,
then trials. CNN summaries average seed-specific trial losses, not predictions;
there is no best-seed selection or ensemble advantage hidden in the headline.

The historical final values remain CNN200 **0.0127916679**, CNN20
**0.0266053581**, Kalman **0.0302108898**, history ridge **0.0220675991**
(m/s)². The supporting existing files are `reports/m025_final.json`,
`data/processed/m025_final/{predictions.npz,controls.npz,cnn_*_seed_*.pt}`.
The ignored arrays/checkpoints are local verification inputs, not redistributed
research data. Initial working-tree status was clean at the verified head.

## Existing control validity matrix

| Control | Removes | Preserves / task clock | Identity, shift and retraining | Supported interpretation | Unsupported interpretation |
| --- | --- | --- | --- | --- | --- |
| Training-mean feature replacement | Temporal variability of only 13 of 137 selected neural columns | Remaining 124 observed units, their joint activity, bin order, all trial/task associations; selected columns become training-mean counts | Inference intervention only; fractional mean counts and disrupted cross-unit dependence may be out of distribution; no trial-ID feature added | Sensitivity to this prespecified partial feature intervention | No-neural performance, neural necessity, full electrode-loss robustness or information-matched baseline |
| Within-condition trial permutation | Recipient-specific neural/behavior pairing when donor differs | Entire simultaneous donor population and its temporal order, condition membership and go-relative phase; donor-specific timing remains | Inference intervention, no retraining; donor/recipient joint pairing is shifted. Condition metadata used, not evaluation velocity. Fixed points retain original pairing | Dependence on trial-specific pairing beyond the defined condition/clock, conditional on intervention validity | Complete neural-information removal, causal neural effect, independently confirmed generalization |
| Global training mean | All evaluation neural features and trial-specific behavior | Training target mean only; no time-varying task clock in prediction | Fitted training labels; same constant for every trial/bin; no recipient identity feature | Intercept-only supervised baseline | Strongest possible task-only prediction |
| Go-time template | All evaluation neural features and trial-specific behavior | Training velocity mean separately at each of 70 go-relative bins; explicit clock | Fitted training labels; no condition feature or evaluation labels; broadcasts same trajectory across trials | Empirical task-clock-only conditional mean | All task information, condition-specific task prediction or matched CNN optimization |
| Five-bin history ridge | Nonlinear feature interactions and older-than-five-bin neural history | Current and four previous bins of all units, within each trial | Trained model; first four bins excluded, histories never concatenate trials; no explicit task clock | Linear history-matched reference for five-bin CNN receptive field | Capacity/optimization-matched neural model or unrestricted dynamical baseline |
| CNN prefix/future perturbation check | Access to future neural bins in a mathematical validation copy | Current/past inputs; trial-local start padding | Validation only, not a neural-information ablation; double precision copy, unchanged float32 production weights | Structural causal receptive field within the extracted sequence | Bitwise float32 future invariance, future-velocity prediction, causal physiology or live initialization |

For standard validation the stored permutation changes **445/574** assignments;
**129 fixed points** remain, despite zero singleton trials. It is a permutation,
not a derangement. Small's 25 conditions are singleton and its permutation
changes zero trials: **uninformative** as a neural null. The selected feature
columns in standard are `[0,20,26,28,29,35,48,63,71,80,108,132,133]`.

Sources: `optimization_study.condition_permutation` and `run`;
`optimization_controls.train_controls`, `predict_controls`, `history_features`;
`event_audit.condition_keys` uses maze ID, trial type, trial version and active
target and rejects incompatible target/barrier geometry. Conditions are native
metadata, not inferred from validation target trajectories. Their availability
for an actual online deployment must not be assumed from this offline control.

## Architecture, clock and alignment

`src/cerebro/sequence_models.py:CausalTemporalCNN.forward` applies two width-three
convolutions, each padded **only on the left**, with shared weights and ReLUs.
Its receptive field is exactly five neural bins (100 ms), including the current
20-ms bin. Each trial is a separate batch sequence; no convolution crosses a
trial boundary. There is no trial ID, recurrent state or positional channel.

**Important matched-control constraint:** constant features passed to the
unchanged CNN yield the same mathematical output at every primary scored bin.
The padding transient occupies only bins 0–3, which are excluded. Consequently,
a constant-input CNN is a useful matched no-neural/intercept control, but is
**not** a task-phase model. A trained task-phase model must receive an explicit
clock representation or use the existing fitted time template. It must be
labeled as receiving that additional information. Neural inputs can themselves
encode task phase; absence of an explicit clock does not remove that confound.

`benchmark.prepare` selects only held-in units and complete native-coverage
windows, go cue −0.4 to +1.0 s. `sense.bin_spikes` uses half-open 20-ms bins;
`sense.align_behavior` averages native samples in each identical bin, with
maximum sample gap 2 ms and no interpolation, extrapolation or lag optimization.
Predictions are assigned bin-right timestamps and reconstruct contemporaneous
mean hand velocity in m/s, not future velocity. Offline pre-cue windows are
indexed using the subsequently recorded go cue. Native upstream velocity
estimation is supplied by the dataset; its physiological causality has not been
independently reconstructed.

## Benchmark fairness and remaining differences

| Item | Common or different | Consequence |
| --- | --- | --- |
| Evaluation observations | Identical 574 targets, trial IDs and 66-bin mask across all 11 saved predictors | Primary MSE contrasts are aligned |
| Training observations | CNN and Kalman use all 70 training bins; instantaneous/history ridge fit targets only in bins 4 onward | Across-family training-mask difference; unchanged in CNN20 vs CNN200 |
| Neural preprocessing | Unitwise StandardScaler fitted only on inner training for selection, then all original training for final refits | Validation statistics do not fit normalizers |
| Target preprocessing | CNN trains standardized coordinate loss using training target mean/std, then unscales; ridge/Kalman fit physical targets | Different training objectives; all selection and reported losses use physical MSE |
| History and causality | CNN and history ridge use exactly five bins; instantaneous ridge one; Kalman recursively summarizes all preceding within-trial bins and current observation | History matched only for history ridge; no claim of identical family inductive bias |
| Model selection | CNN cap-specific minimum inner physical MSE; separate alpha grid `[1,10,100,1000]` for each classical model | No final-loss selection; CNN200 expands updates and epoch candidates together |
| Capacity and budget | CNN hidden32/nonlinear; ridge linear, Kalman two-state linear Gaussian; no equal wall-time budget | A practical recipe comparison, not isolated architecture or compute-efficiency proof |
| Reset and labels at inference | CNN trial-local padding; Kalman training prior reset per trial; no evaluation behavior supplied as predictor | No teacher-forced validation behavior or carryover state |

CNN200 selected standard epochs 174,187,174 versus CNN20's 20,20,20. It is not
valid to infer undertraining solely because an epoch lies at the shorter cap.
The causal-check numerical recovery is explicitly documented in
`docs/research/m025_recovery.{md,json}` and `reports/m025_numerical_failure.json`.
An original float32 check failed before final scoring; old seed0 checkpoint
bytes and start markers were preserved. Double-precision validation replaced
only the verification procedure, not production dtype, weights or predictions.

## M026 evaluation access policy

All 574 standard validation outcomes have now been scored and reported by M025.
They are **previously inspected evaluation data** for every new M026 control,
regardless of whether its architecture is new. Freeze control definitions,
seeds, selection rules, comparisons and uncertainty before any new validation
comparison. Fit/select only within the original 1,721 training trials and fixed
1,377/344 inner split. Final refits may use all original training trials after
selection. Metadata conditioning is an explicit information budget; never
permute donors across train/inner/validation boundaries or incompatible task
conditions. Any new standard-validation result is a **retrospective diagnostic**,
not another independent confirmation or untouched test. No additional eligible,
never-scored cohort was established by this read-only audit.

Descriptive trial and ordered-block intervals condition on one recording and
fixed fits. Seeds are optimization replicates, not biological units. Even a
successful matched-control contrast cannot establish across-subject/recording
BCI performance, physiological mechanisms or general subject invariance.

Not performed here: new fitting, new control scores, native re-acquisition,
GPU/live-BCI testing or proof of absent private/unlogged historical exposure.
