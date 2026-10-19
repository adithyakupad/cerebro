# Full-scope completion matrix

**Overall: incomplete.** Mission014 software audit passed within its documented scope. Mission019 verified native Brochier sampled neural coverage and completed a frozen two-animal condition-classification case study, finding no clear source-assisted advantage. Strict continuous cross-subject target-preprocessing validation, broader biological replication, and human publication approval remain unresolved. Scientific scope is preserved; negative findings are valid outcomes.

See [explicit release acceptance statuses](../release/acceptance_matrix.md), [independent audit](../development/mission_014_audit.md), [fresh validation](../development/mission_014_validation.md), and [new-date measurements](../../reports/mission_014.md). Historical report hashes and row-level revisions remain in [the machine matrix](completion_matrix.json).

| Subsystem / capability | Implementation / validation | Real data / measured evidence | Limitations / blockers |
|---|---|---|---|
| SENSE: NWB acquisition, timestamp/unit validation, trial binning and behavior masks | implemented / implemented | Maze Small; standard Maze; LINK; FALCON native coverage; 9 pinned assets checksum-verified; Maze100×70×107; LINK375 trials/session; FALCON54633/58552 complete bins; Mission014:11 repository manifests verified, additional6 FALCON dates and LINK Feb05 audited | Perich audit only: unknown neural coverage; LINK count-unit ambiguity; FALCON upstream normalized EMG |
| SENSE: Trials, sessions, subjects, units/contact policies and immutable split manifests | implemented / implemented | Maze and three LINK sessions; Original IDs/clocks retained; contact coordinates checked; split mutation rejected | Contacts are not tracked neurons; no private or speech acquisition |
| MAP: PCA/FA and training-only dimension selection | implemented / implemented | Maze Small; PCA20; FA5 selected on inner60/15; outer25 untouched by fitting | PCA reconstruction favors largest candidate; Gaussian FA approximates counts |
| MAP: Population covariance, similarity, CCA and principal angles | implemented descriptive / implemented descriptive | LINK Jan27/Jan30 calibration only; Covariance cosine0.718375; CCA/angles reported without independent inference | CCA in-sample noisy anchors; no causal connectivity or reliable residual covariance |
| MAP: Neural latent dynamics and geometric controls | implemented exploratory / implemented exploratory | Maze Small; Trial-local AR1, persistence/mean/permuted-time fitting controls executed | Teacher-forced one-step forecast; no validated physiological dynamics |
| DECODE: Mean, event-time, linear, ridge and Kalman | implemented / implemented | Maze Small; Mean MSE0.0383248; ridge0.0354214; Kalman0.0313141 m²/s² | Offline contemporaneous evaluation; source validation is exploratory |
| DECODE: MLP, GRU/LSTM, temporal CNN, Transformer, state-space sequence | implemented / implemented | Maze Small; Six architectures ×3 seeds executed; temporalCNN mean MSE0.0310519 | Unequal parameter counts; small fixed compute; Scientific runs CPU;6-model MPS software smoke passed; CUDA unavailable |
| REMEMBER: Session indexing, feature mapping and shared/session representations | implemented within subject / implemented within subject | Perich native audit; three LINK sessions; Session-scoped IDs; exact contact-key mapping; source/session representations compared | Perich neuron mapping unestablished; no cross-subject feature correspondence |
| REMEMBER: Subject-aware generalization | implemented exploratory / implemented exploratory | FALCON MonkeyL→MonkeyX; native recorded coverage; Source300 fit/112 eval; target75 calibration/354 eval; zero-shot MSE0.180151 vs source mean0.178826 normalized EMG². Mission019 Brochier L↔N frozen four-class case: source-assisted minus target-only balanced accuracy +0.0126/+0.0021, both trial intervals include zero | Brochier native 93/156 SUAs and all 135/142 correct go windows verified; label classification is not continuous movement decoding. Two animals/one session each confound subject/date/session; FALCON original EMG preprocessing precedes splits; M1-B draft |
| ADAPT: Frozen transfer, recalibration, few-shot/residual correction and budget curves | implemented / implemented | LINK Jan27→Jan30; Source300 fit/source75 eval; target75 calibration/300 eval; budgets1/5/15/50/75 | Small-budget calibration often worsens error; no test-driven method selection |
| ADAPT: Unsupervised marginal and supervised condition-anchor alignment | implemented exploratory / implemented exploratory | LINK first75 target calibration only; Unlabeled normalization MSE0.0263827 versus frozen0.0269661 flexion² | Marginal rescaling is not general identifiable alignment; extra target metadata disclosed |
| ADAPT: Shift and failure analysis | implemented descriptive / implemented descriptive | LINK Jan27/Jan30; Geometry, chronological error segments, extrapolated prediction fractions and block sensitivity reported | Two sessions do not identify drift causation; broader robustness unvalidated |
| FOUNDATION: Masked/predictive SSL, frozen probing and fine-tuning | implemented experimental / implemented experimental | Maze Small and LINK; Within-session36 runs; cross-session168 controls/12 SSL runs; Mission014:3 source-only SSL fits and42 controls on later date | No broad SSL benefit demonstrated; no validated neural foundation model claim |
| FOUNDATION: Multi-recording pretraining and held-out-session transfer | implemented same subject / implemented same subject | LINK Jan27+Jan30→Feb04; Reference pretrained/random zero-shot MSE0.0211969/0.0211803 flexion²; New Feb05 reference pretrained/random zero-shot0.02439402/0.02442170, tiny mixed probe differences | Same contacts/subject; first40 native samples per trial only |
| FOUNDATION: Random/supervised controls and model/data/compute ablations | implemented finite controls / implemented finite controls | Three LINK sessions; Four prespecified settings ×3 seeds; nested5/15/75 label budgets | Data100 changes SSL observations and scaler pool; finite ablations are not scaling laws |
| FOUNDATION: Session/subject identity leakage controls | implemented held-out diagnostics / implemented held-out diagnostics | LINK held-out150 trials; FALCON source112/target354; 24 date diagnostics: SSL98.0%, random97.78%; FALCON balanced subject accuracy100% vs chance50% | Implicit date/subject information retained; FALCON one recording per animal confounds subject, session and date; post-hoc diagnostic |
| INTERACT: Activity, behavioral alignment, trajectories and decoder predictions | implemented locally / implemented locally | Stored Maze real-data outputs; Trial/model/PCA controls checked in browser; no JS errors | Self-contained offline explorer; no hardware control |
| INTERACT: Session shifts, calibration curves, models and experiment inspection | implemented locally / implemented locally | Stored LINK/representation outputs; Calibration and ablation selectors checked; provenance/limitations visible | Cross-subject outputs unavailable; no simulated replacement |
| Research engine: Versioned configs, registries, preprocessing/checkpoints/provenance | implemented / implemented | All executed workflows; Fresh11 experiments;350 registry artifact digests;529 reported-array digests;229 raw-count prediction replays,227 exact; unsupported formats integrity/workflow restoration only | Direct requirements snapshot not transitive/cross-platform lock |
| Research engine: Statistical evaluation, causality/leakage checks and reports | implemented exploratory / implemented exploratory | Eight executed experiments; 96 common per-trial summaries; trial/block intervals and paired contrasts | Intervals depend on independence/block assumptions; no multiplicity-corrected significance |
| Release: Tests, wheel, clean-checkout reproduction and incremental PR | verified software within documented scope / PASS | 11 pinned manifests;fresh Small download,10 verified raw reuses;macOS arm64 fresh environment; Fresh Conda Python3.11.17;46 commands pass;222 full tests;210 software tests plus12 data cases separately collected;11 experiments526 arrays numerically exact;wheel built;CPU/MPS6-model smokes | CI does not execute authentic-data workflows;MPS is synthetic smoke only;CUDA/GPU science/type checker untested |
| Release: Final full-scope release | incomplete;no final tag / SCIENTIFICALLY INCONCLUSIVE | Not applicable; v0.1.0 remains at8f9ffd91e4342713cb5a571e63d9931484caa143 | General-purpose foundation-model validity unestablished;negative results preserved;not a prerequisite that every hypothesis be positive; Strict FALCON original target-processing validation unresolved;obtain raw provenance or independently suitable data. Human approval for merge/final tag pending. |

Mission014 committed validation revision: `a3a2dfd04daf3d923a47d133ce4acf30b5983571`. Unchanged scientific rows retain their historical execution revisions in JSON; the original reports are not rewritten. Cross-subject preprocessing is a data-validity limitation rather than an implementation success claim. General foundation-model validity remains unestablished, while all implemented objectives, pretraining controls and transfer experiments remain in scope.

## Mission 016 prospective evidence update

The [dataset screen](../datasets/mission_016_eligibility.md) and [protocol](mission_016_protocol.json) were committed at `5a7376a694825005500cd357694fa8e27e2ce31e` before new model outcomes. The three checksum-pinned LINK targets (Feb 6/11/22, 2020) passed native sampled-coverage and same-task checks; all remain one Monkey N. [Full reports and figures](../../reports/mission_016.md) preserve the fixed outcomes.

| Question | New verified evidence | Completion status |
|---|---|---|
| Within-session decoding | Jan 27 source reserved 75-trial ridge MSE 0.03150958 flexion²; historically inspected source evaluation, not an untouched final test. | Implemented; qualified offline evidence |
| Frozen cross-session transfer | Target MSE 0.02635430, 0.02786564 and 0.02601508 flexion² on the three future dates. Source-mean controls are 0.02387138, 0.02765507 and 0.02420724. | Executed on new dates; broad robustness unvalidated |
| Calibration-efficient adaptation | At the prespecified 15-label budget, source-assisted minus target-only equal-trial MSE is +0.00055375, +0.00067157 and +0.00061931 flexion²; equal-date +0.00061488. Both methods trail frozen/source-mean controls on all three dates. Negative source-assistance finding; no implementation failure. | Methods complete; robust advantage not demonstrated |
| Self-supervised transfer | Three-seed Feb 6 pretrained/random/supervised controls have tiny mixed differences under a separate first-40-bin protocol. | Executed; general foundation claim unvalidated |
| Strict cross-subject transfer | Not run: FALCON original targets unavailable; Perich coverage undocumented; Zenodo Indy/Loco native coverage still pending. | Blocked by suitable data/provenance, not a missing decoder family |

Mission 016 does not alter the historical 22 subsystem rows above. The [machine matrix](completion_matrix.json) records the addendum and exact report hashes separately. Dates are repeated observations within one animal; neither trial-level block intervals nor optimization seeds are independent-subject uncertainty.

## Mission 017 evidence update

The three Mission 015/016 commits through `fda96d87c3bc9c43a038b8b727f3519724a6ee9b` are published on draft PR #1. Both GitHub test runs at that head succeeded: **212 software tests passed, 15 data cases collected but not executed in public CI**. After Mission 017 diagnostics, the local full suite passed **230 tests**; 405 artifact/755 array digests passed and 229 historical predictions replayed, 227 exactly. These checks validate software and stored outputs, not cross-subject neuroscience claims.

Mission 017 research commit `071232c8a03fd85dc54d634d9490b025f8f3c442` also passed two GitHub runs: **215 software tests passed, 15 data tests collected/deselected** in each. The authentic-data cases passed locally, not in public CI.

| Requirement | New Mission 017 evidence | Current status |
|---|---|---|
| Strict independent-subject transfer | [Eligibility ranking](../datasets/mission_017_eligibility.md) leaves Indy/Loco without documented Loco neural coverage; Brochier native assets, timing and data terms require direct audit; FALCON raw EMG remains unavailable. [No new model result](../../reports/mission_017_cross_subject.md). | **BLOCKED by data/provenance**, no verified strict cross-subject experiment |
| Low-budget adaptation mechanism | [Descriptive diagnosis](../../reports/mission_017_adaptation.md) finds only 15 independent labeled trials, early calibration index-position means 0.585–0.597 versus later evaluation means 0.496–0.509, and source alpha selection nearly flat at the grid edge. Retrospective dates were not used for new model selection. | **PARTIAL**: calibration sampling bias is plausible; contribution of regularization and neural drift remains unresolved |
| Validated subject-invariant representation or neural foundation model | No new eligible held-out-subject experiment; historical small/mixed SSL and negative transfer outcomes remain unchanged. | **UNVALIDATED** scientifically; implemented objectives and software remain present |

Historical subsystem rows and Mission 016 results remain immutable. A negative transfer finding is not a software defect. The [release addendum](../release/acceptance_matrix.md) distinguishes the passing PR checks from the blocked scientific gate.

## Exact continuation gates

1. Review Mission014 release acceptance evidence and PR1; preserve v0.1.0, do not merge/tag without explicit human approval and satisfied original completion criteria.
2. Resolve strict cross-subject original target-preprocessing validation with authoritative raw EMG/clock/calibration sources or independent suitable data; preserve published-target exploratory reports.
3. Keep Perich audit-only until documented neural coverage is established.
4. For any further model selection, prespecify a new untouched cohort and practical effect criteria. All Mission014 dates and Mission016 Feb 6/11/22 evaluation outcomes are now inspected.
5. Retain full foundation scope and negative/mixed SSL results; validate broader transfer before general-purpose foundation claims. CUDA and GPU real-data equivalence need appropriate hardware if claimed.

No continuation automation is installed. Work does not continue after a session unless a new active execution occurs.

## Mission 018 native-data gate

The [Brochier native-asset audit](../datasets/mission_018_brochier.md) confirms two named animals and sessions, published sensor/event streams, and dataset-level CC-BY-4.0 from authoritative documents. Native files were not reachable in this execution environment; individual checksums, sampled coverage and common physical target calibration remain unverified. The [eligibility matrix](../../reports/mission_018_eligibility.md) therefore keeps strict cross-subject transfer **BLOCKED by data/provenance**, with **no new model experiment**. [Condition counts](../../reports/mission_018_variability.md) support only a prospective variability feasibility judgment, not an empirical covariance result. Historical software and scientific statuses above are unchanged.

## Mission 019 native-data update

The [publisher ZIP assets](../datasets/mission_019_brochier_assets.json) were recovered and SHA-256 verified. Both native 30 kHz sampled streams, 1 kHz analog streams, source odML and sorted NEV were audited; all 135 L and 142 N correct 280-ms go windows have raw sampled neural coverage and source GO events. This resolves the Mission 018 **native-access** blocker for these two recordings. A [protocol committed before outcomes](mission_019_protocol.md) tested four grip-by-load **task-condition** labels with 93/156 source-designated single units. L→N and N→L source-assisted minus target-only balanced accuracy were +0.0126 and +0.0021; both target-trial bootstrap intervals include zero. The [report](../../reports/mission_019_brochier_transfer.md) preserves negative evidence. Software execution and this bounded empirical test are complete; improved transfer and general subject-invariant representation remain **UNVALIDATED**. One session per animal, unresolved physical sensor calibration and source-license text conflict still prevent strict continuous-target cross-subject validation or raw-data redistribution.

## Mission 020 population and integration update

The [pre-outcome Brochier protocol](mission_020_protocol.md) and [feasibility audit](mission_020_feasibility.md) precede the real-data analysis. The [population report](../../reports/mission_020_brochier_population.md) and [machine results](../../reports/mission_020_brochier_population.json) describe 135 L and 142 N correctly labeled, fully sampled SR-aligned trials in `135×30×93` and `142×30×156` count tensors. Condition/time-specific residuals, trial-level aggregate sharing, Fano summaries and descriptive trajectories were computed. Single-condition residual rank ceilings remain below the unit counts; reliable full high-dimensional residual covariance is **not** established. No connectivity or cross-animal biological-generalization claim follows.

The [integrated technical report](mission_020_technical_report.md) consolidates all historical studies without recomputing or replacing their results. The [33-requirement Mission 020 traceability matrix](mission_020_traceability.md) retains the original scope: 14 COMPLETE, 8 PARTIAL, 5 UNVALIDATED, 4 BLOCKED, 2 MISSING. Only M2 advances from UNVALIDATED to PARTIAL because real condition-matched residual descriptive statistics now exist; high-dimensional inference and independent biological replication remain outstanding. Software execution, experiments and scientific hypotheses are classified separately.

## Mission 021 software qualification

The [v1.0 qualification report](../release/qualification_021.md) verifies the implemented platform using a public clone, fresh Conda installation, authentic-data workflow reproduction, independent reviews and explicitly separated CI/data tests. The original 33 statuses above remain unchanged: software delivery does not turn inconclusive transfer hypotheses or external-data gaps into scientific successes. Under the owner's Mission 021 criteria, valid negative results and disclosed unavailable-data limits can accompany a software release. Final publication still requires explicit owner approval; neither this matrix nor the package version constitutes a merge, tag or public release.

## Mission 022 calibration mechanisms

This addendum starts from the subsequently published v1.0.0 commit `b780e5cc53f246f4b305d413c4bd1afb962ff42c`; the historical qualification text above remains an execution-time record. The release tag and prior scientific artifacts are preserved.

| Requirement | New evidence | Status and limitation |
|---|---|---|
| Low-budget adaptation mechanism | [Frozen protocol](m022_protocol.md), committed before outcomes; 369 whole-trial allocations on Jan 30/Feb 4/Feb 5 previously inspected development partitions. Finite-subset prediction dispersion declines from 5 to 30 labels; balanced 15-trial allocation lowers direct-ridge MSE by 12.17%, 8.70%, 1.36% relative to chronological allocation. | **PARTIAL**: bounded statistical contributors, extra command-metadata access disclosed; not physiological causation. |
| Practical adaptation mitigation | Seven prespecified chronological-15 candidates tested against both frozen and direct controls, with 5% practical threshold and all-date/conditional block-interval requirements. [All outcomes](../../reports/m022_calibration_mechanisms.md) preserved. | **UNVALIDATED practical benefit**: no candidate passes; a valid negative finding, no software defect. |
| Untouched independent sessions | [Metadata-only inventory](../datasets/m022_eligibility.json) identifies Feb 24/Feb 25/Jun 26 CO candidates, one Monkey N. | **NOT EXECUTED** by failed-promotion null rule; native eligibility unverified, no new decoder outcomes inspected. This is distinct from unavailable data. |
| Software and reproducibility | Existing ridge/scaling infrastructure reused; [verification evidence](m022_validation.json) covers split/allocation/shrinkage/coefficient/decomposition/gate/report tests, source hashes and numerical rerun. | Verified within stated checks; no new model family or dependency. |

The original 33-requirement statuses remain **14 COMPLETE, 8 PARTIAL, 5 UNVALIDATED, 4 BLOCKED, 2 MISSING**. Development mechanistic evidence does not establish reliable cross-session benefit, biological subject generalization or neural foundation-model validity. Trials, subset resamples and optimization seeds are not independent biological subjects.

## Mission 023 reliability and observed dynamics

The [manuscript](../../reports/m023_manuscript.md), [acceptance matrix](m023_acceptance.md) and [validation record](m023_validation.json) add two bounded development studies while preserving M022 as draft PR2. The frozen protocol was committed before outcomes; no release tag or main merge was changed.

| Requirement | New evidence | Scientific status |
|---|---|---|
| Calibration-only adaptation reliability |369 allocations, whole-session folds, fixed information budgets; primary combined risk MSE1.09375e-5 versus label-only7.20229e-6 flexion⁴. Combined BA0.675 equals permutation control and trails label-only0.7625. | **BOUNDED NEGATIVE**: no reliability candidate passes promotion; no independently validated harm avoidance. |
| Interpretable observed dynamics |60 model/session evaluations; PCA6 AR forecast gains42.36% versus persistence,3.59% versus mean,2.40% versus shuffled training. Multi-step, dimensionality, local/scaling, geometry and behavior controls executed. | **PARTIAL development evidence**: statistical temporal structure; fixed practical gate fails. Original M3 generalization requirement remains UNVALIDATED. |
| Added dynamics risk information | Coverage+label risk MSE7.23305e-6 versus dynamics-augmented7.31302e-6 flexion⁴. | **INCONCLUSIVE / no primary added benefit**. No physiological inference. |
| Native independent cohort | Exact Feb24/Feb25/Jun26 hashes,375 trials/session,96-contact joins and synchronized sampled coverage verified. | **Eligible within one subject; outcomes unscored** because both development gates fail. Not a data-access blocker. |
| Reproducibility and software |274 local tests including22 data cases;1348 new saved-array entries reproduced; raw-count checkpoints, independent FA likelihood reconstruction, wheel and presentation checks. | **PASS within executed scope**; public CI verified separately at the research PR head. |

The original33 statuses remain14 COMPLETE,8 PARTIAL,5 UNVALIDATED,4 BLOCKED,2 MISSING. No broad adaptive-neural-intelligence, foundation-model, clinical, subject-invariance or physiology conclusion is upgraded. Eligible unscored recordings are preserved for a separately approved future protocol, not outcome-driven method retries.

## Mission 024 integration qualification

The [v1.1 consolidated study](v1_1_manuscript.md) and [release acceptance](../release/qualification_024.md) integrate M022/M023 without changing original33-requirement statuses or historical results. Fresh authentic-data reconstruction, package verification and independent review qualify software/reproducibility separately from failed scientific promotion gates. Eligible later LINK dates remain unscored. Merge/tag/release await explicit owner approval.

## Mission 025 bounded decoder optimization

The [frozen protocol](m025_protocol.md), [eligibility audit](m025_evaluation_eligibility.md),
[scientific report](../../reports/m025_optimization.md) and
[reproduction guide](m025_reproduction.md) add a controlled CNN optimization-budget
study. The original 33 requirement rows and historical results remain unchanged.

| Evidence domain | Executed evidence | Status and limits |
| --- | --- | --- |
| Within-session velocity reconstruction | Unchanged CNN, 20 versus 200 maximum updates, three fixed seeds, physical-MSE epoch selection; Small inner promotion improves 18.6012%. On the separately recorded standard session, CNN200 MSE is 0.01279167 (m/s)² versus CNN20 0.02660536 and tuned Kalman 0.03021089. | **PASS, bounded practical gate**: 51.9207% / 57.6588% reductions; paired and ordered-block intervals exclude zero. This is a session-specific training-recipe replication, not frozen-decoder transfer. |
| Eligibility and provenance | DANDI 000128 version 0.220113.0400, asset 26e85f09-39b7-480f-b337-278a8f034007; Jenkins Sep 25, 2009, versus Small Sep 28; 1,721/574 original train/validation identities, no exclusions. | One animal, two recordings, separately fitted unit sets. Standard outcomes were performance-unscored in maintained records; earlier whole-file raw access is disclosed. Not a never-opened reserve or independent subject. |
| Verification and limitations | 289 software tests and 22 authentic-data tests; exact saved prediction restoration, historical artifact hashes, independent stored-output review. Pre-scoring float32 validation failure and reviewed recovery are preserved explicitly. | **PASS within executed checks**; causal structure does not imply bitwise float32 prefix invariance, prospective event detection or online BCI. Trial uncertainty is conditional on fixed fits. |
| Longitudinal adaptation, subject invariance and foundation-model validity | No new transfer, new-subject or self-supervised experiment. Earlier negative results and LINK unscored reserves remain preserved. | Original limitations and statuses unchanged. No full-scope scientific completion claim follows from this result. |
