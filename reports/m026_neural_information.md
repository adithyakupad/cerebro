# M026: neural information and decoder validity

**Retrospective diagnostic analysis.** The standard validation outcomes were already inspected in M025. These comparisons are not a second independent confirmation.

## Question and design

We tested whether the M025 CNN gain can be explained by task-phase predictability or persists against trained controls that disrupt trial-specific neural–behavior pairing. No CNN architecture, historical output, trial partition, loss or optimizer was changed.

The frozen [protocol](../docs/research/m026_protocol.md) ranks alternatives before training. The [control validity matrix](../docs/research/m026_control_validity.md) documents removed/preserved information, task clocks, distribution shifts and limitations. All control seeds 0/1/2 receive at most 200 updates; epoch selection uses only 1377/344 inner fitting/validation trials, then refits 1721 original training trials. Both coordinates and all 70 bins enter training loss; common primary scoring uses 574 trials × 66 bins × 2 coordinates, equal-trial physical MSE. These are separately fitted models of one animal and one recording.

## Scientific finding

Both task structure and neural pairing contribute to prediction under these controls. The condition×time template reduces mean MSE by 61.43% versus the training-mean baseline; real CNN200 reduces it a further 14.92% relative to that template. Task phase alone is a much weaker predictor.
The neural advantage is heterogeneous: 233/574 trial wins and 53/108 condition-mean wins versus the task template. Median paired difference is 0.00215161 (m/s)², so a typical trial favors the template even though aggregate mean MSE favors the neural model. The neural model reduces larger errors in a subset; no uniform per-trial benefit is demonstrated.
The permuted-trained CNN scores better on original neural inputs than on matched permuted inputs. This illustrates sensitivity to pairing and the intervention’s joint input/target distribution; it does not isolate a physiological cause. The stronger condition template and original-input inference are retained, not hidden behind the weaker matched-null headline.

## Measurements

| Model / information | MSE [(m/s)²] | Seed-specific MSE |
| --- | ---: | --- |
| Real CNN200 | 0.0127916679 | [0.012820015942213199, 0.012828942228901158, 0.012726045672807853] |
| Real CNN20 | 0.0266053581 | [0.026289050628017514, 0.025826950903091932, 0.027700072896067313] |
| Clock CNN | 0.0387546361 | [0.03880944988114545, 0.038765035406681594, 0.038689423114595264] |
| Zero CNN | 0.0389871247 | [0.0389958749018197, 0.03898077568861053, 0.038984723491840435] |
| Permuted train+eval | 0.0270401233 | [0.02715342665715655, 0.027030001282650384, 0.02693694206267002] |
| Permuted train/real eval | 0.0186028709 | [0.01882340107014714, 0.01856703423498424, 0.018418177256613908] |
| Condition×time | 0.0150349067 | [0.015034906676431767] |
| Global time | 0.0382411475 | [0.03824114746265374] |
| History ridge | 0.0220675991 | [0.02206759910843223] |
| Kalman | 0.0302108898 | [0.030210889823428972] |
| Mean | 0.0389789450 | [0.03897894495133024] |

| Real CNN200 minus control | Absolute MSE difference [(m/s)²] | Relative reduction | Paired95% interval | Ordered-block 5 interval |
| --- | ---: | ---: | --- | --- |
| zero | -0.0261954567 | 67.190% | [-0.02720445304100656, -0.025202699824272284] | [-0.02717049432127946, -0.025250703131945815] |
| clock | -0.0259629682 | 66.993% | [-0.02695136340510267, -0.02499411357958091] | [-0.02691232156758391, -0.025043279130596553] |
| permuted | -0.0142484554 | 52.694% | [-0.015522517303581779, -0.013021895764229631] | [-0.015431172855520824, -0.013124288979678867] |
| permuted_real | -0.0058112029 | 31.238% | [-0.006328815029015033, -0.005308493754327841] | [-0.006285951276877646, -0.005352029629996429] |
| neural_20 | -0.0138136902 | 51.921% | [-0.014492678531511238, -0.013148738958225463] | [-0.014457669693085715, -0.013175527763175538] |
| kalman | -0.0174192219 | 57.659% | [-0.018164016157946, -0.016671469546967372] | [-0.01809284664004304, -0.016757223779653566] |
| history_ridge | -0.0092759312 | 42.034% | [-0.00974457396907184, -0.008816837815790476] | [-0.00971926392522807, -0.008841116182909853] |
| mean | -0.0261872770 | 67.183% | [-0.02719680876785903, -0.025197919920073662] | [-0.027159183080803354, -0.025244698977763335] |
| go_time_template | -0.0254494795 | 66.550% | [-0.02643123864574191, -0.024492241972980573] | [-0.026379080495427077, -0.0245439141051304] |
| condition_template | -0.0022432387 | 14.920% | [-0.003591317891763016, -0.0009658326029374654] | [-0.0035191143634950364, -0.0010057261814368276] |

Both frozen primary descriptive thresholds (5% and negative paired interval): **True**. These thresholds do not restore untouched-test status.

Condition-template fallback: 0/574 trials. Unseen conditions use the global training-bin template. Condition, speed and direction tables in JSON include participating trial/bin counts and per-trial errors, averaged over seed losses rather than ensemble predictions. Speed strata are [0,.1,.25,.5,infinity] m/s; direction uses four Cartesian quadrants and stationary samples separately. Strata are descriptive, with no outcome-driven thresholds or per-bin biological inference.

## Training and information budgets

| Control, seed | Selected epoch | Inner selected MSE [(m/s)²] | Refit seconds | Batch forward seconds |
| --- | ---: | ---: | ---: | ---: |
| zero_seed_0 | 1 | 0.0383905075 | 1.5348 | 0.3956 |
| zero_seed_1 | 29 | 0.0384085535 | 36.4147 | 0.3591 |
| zero_seed_2 | 44 | 0.0384010005 | 63.7504 | 0.4167 |
| clock_seed_0 | 20 | 0.0383127866 | 29.0410 | 0.4226 |
| clock_seed_1 | 20 | 0.0382970800 | 29.0072 | 0.4152 |
| clock_seed_2 | 32 | 0.0383100632 | 46.7756 | 0.4291 |
| permuted_seed_0 | 75 | 0.0269234861 | 108.6022 | 0.4012 |
| permuted_seed_1 | 84 | 0.0267861093 | 122.0023 | 0.4072 |
| permuted_seed_2 | 90 | 0.0267120393 | 130.5841 | 0.4089 |

Fixed donor-map unchanged counts by partition: {'inner_training': 0, 'inner_validation': 10, 'source_training': 0, 'source_validation': 0}. Every nonsingleton is deranged; singleton pairs retain original information. One fixed surrogate per partition is shared across optimization seeds; seeds do not sample independent permutations.

All newly trained CNN controls have the same nominal parameter count (16354); effective input rank and usable functional capacity differ. Repeated explicit-clock channels intentionally provide task timing, not neural observations. Zero CNN becomes constant after its four-bin padding transient and is not a strong task-phase predictor. The unrestricted training-bin template and condition×time template supplement the optimized clock model. The latter receives task-condition metadata that the original CNN does not receive explicitly.

The permuted-training model is evaluated on both partition-local permuted inputs and original inputs. The matched permuted-input comparison disrupts residual pairing during training AND inference while preserving complete donor trajectories and condition/time structure. Original-input inference is separately reported; no favorable variant was selected. Fixed-map finite-sample surrogate error and singleton retention prevent interpreting this as perfect conditional independence.

Total fit/stage seconds: 3011.8479636248667; unchanged native preparation seconds: 1531.4169519159477. Batch-forward timings describe offline CPU execution, not prospective streaming latency. All per-epoch histories are in JSON.

## Four interpretation questions

1. **Historical accuracy:** M025 real CNN200 remains 0.0127916679 versus CNN20 reference 0.0266053581, Kalman 0.0302108898 and history ridge 0.0220675991 (m/s)². M026 does not modify or independently reconfirm those comparisons.
2. **Neural beyond phase:** compare real CNN200 with explicit clock and global time template. An advantage is relative to these specified task estimators, not proof that all possible task predictors have been exhausted.
3. **Training advantage and task conditions:** compare real CNN with matched condition-permuted training/evaluation, the same permuted-trained model on real inputs, and condition×time template. These are controls for predictive information, not physiological necessity or causal neural effects. Convergent advantages support trial-specific neural–behavior association beyond these task summaries. Information budgets and finite optimization differ in effective capacity despite equal nominal architecture.
4. **Generalization:** none of these retrospective same-session controls demonstrates outside-task/recording prediction, cross-subject invariance, decoder transfer or online BCI. No future-behavior forecast is evaluated.

## Integrity, uncertainty and limitations

All comparisons retain exact M025 evaluation targets/IDs and complete-coverage bins. Data are genuine intracortical spikes and supplied hand velocity in physical m/s; no synthetic observation replaces an empirical claim. Source is DANDI 000128 v0.220113.0400, asset 26e85f09-39b7-480f-b337-278a8f034007, SHA256 a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4. [Churchland and Kaufman (2022), CC-BY-4.0](https://doi.org/10.48324/dandi.000128/0.220113.0400). Raw recordings and checkpoints are not redistributed.
No explicit trial ID enters the CNN, but activity may encode slow recording state or repeated trajectory templates. Interleaved same-session validation does not rule out these implicit temporal/task associations. Held-out conditions and chronological out-of-distribution deployment were not tested.
Paired 10,000-draw intervals resample whole trials with seed 26; block 5 is a temporal-dependence sensitivity. Uncertainty conditions on fixed fits in one session. It excludes independent-session/subject variation and repeated surrogate-generation variability. Optimization seeds are not biological replicates; no multiplicity-adjusted confirmatory p-value is claimed.
The CNN has a five-bin causal receptive field but reconstructs contemporaneous velocity at bin right. Offline pre-cue windows depend on a later recorded go cue. Task selection and native upstream velocity estimation remain potential structure; causal neural input does not imply prospective task initialization or a physiologically causal target. Ridge training masks differ from CNN/Kalman, although evaluation masks agree; see original audit.
Only cap200 input controls were trained. A full cap×input factorial was not run; these contrasts cannot quantitatively apportion the 20→200 improvement into additive neural, task and optimization components. Task-condition clusters and alternative donor maps are not resampled by the conditional trial intervals.
Partial feature replacement from M025 is a distribution-shift sensitivity, not a no-neural baseline. A permuted neural population still contains abundant condition/time information and donor dynamics. Task templates are particular estimators, not all-task-information ceilings. No positive control result establishes a physiological mechanism, general subject invariance, adaptive decoder superiority or foundation-model validity.

## Research figures

- [Neural-information comparison](figures/m026_neural_information.pdf)
- [Speed and direction strata](figures/m026_error_strata.pdf)
- [Training and selection curves](figures/m026_training_curves.pdf)
- [Trial-error heterogeneity](figures/m026_trial_error_distribution.pdf)

## Reproduction and review

Use the existing Conda cerebro Python 3.11 environment and declared dev,classical,deep extras. Parent M025 artifacts are local inputs, with exact original hashes authenticated; regenerate M025 using its [public reproduction guide](../docs/research/m025_reproduction.md) in a separate clone if absent. The corrected M025 numerical verification/recovery remains unchanged.

```sh
conda run -n cerebro python tools/m026_prepare.py
conda run -n cerebro python -m cerebro.neural_information
conda run -n cerebro python -m cerebro.neural_information --replay
conda run -n cerebro python tools/m026_report.py
conda run -n cerebro python -m pytest -q
```

Preparation refuses to overwrite its cache; fitting uses an exclusive start marker and refuses an implicit rerun. Execute fresh reproduction in a separate clone and archive canonical reports. Reproduction of published outcomes is not a new independent test. Replay restores every new checkpoint, verifies array digests and original M025 file hashes without fitting. Independent review and executed validation are recorded in the [validation record](../docs/research/m026_validation.json) and [independent review](../docs/research/m026_independent_review.md).

## Application evidence

A. Demonstrated earlier: frozen CNN optimization-and-selection recipe reduced MSE 51.92% versus 20 updates and 57.66% versus tuned Kalman in a separately fitted recording of the same animal.
B. Incremental neural evidence: report the fixed real-versus-control contrasts above explicitly as retrospective; promotion thresholds do not establish new independent confirmation.
C. Unresolved: broader task representations, finite surrogate/optimization uncertainty, one-session diagnostics, repeated condition structure and native target estimation.
D. Unsupported: physiological causation, future forecasting, clinical/online BCI, subject-invariant representations, general-purpose foundation models or independent human authorship of agent-assisted code.
Conservative resume bullet: “Built and audited reproducible neural-velocity decoding experiments on public intracortical recordings; demonstrated a prespecified CNN optimization gain and evaluated trained task-clock and condition-matched neural-pairing controls, preserving trial-aware uncertainty and negative findings.” Narrow neural-information numbers may be added only with their retrospective qualification after researcher review.
