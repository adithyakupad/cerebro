# Full-scope completion matrix

**Overall: incomplete.** Software execution and scientific success are distinct. Negative findings are retained. No final release tag is authorized by incomplete evidence.

| Subsystem / capability | Implementation and validation | Real data / measured evidence | Limitations and remaining work |
| --- | --- | --- | --- |
| SENSE: NWB acquisition, timestamp/unit validation, trial binning and behavior masks | implemented | Maze Small; standard Maze; LINK; FALCON native coverage; 9 pinned assets checksum-verified; Maze100×70×107; LINK375 trials/session; FALCON54633/58552 complete bins | Perich audit only: unknown neural coverage; LINK count-unit ambiguity; FALCON upstream normalized EMG |
| SENSE: Trials, sessions, subjects, units/contact policies and immutable split manifests | implemented | Maze and three LINK sessions; Original IDs/clocks retained; contact coordinates checked; split mutation rejected | Contacts are not tracked neurons; no private or speech acquisition |
| MAP: PCA/FA and training-only dimension selection | implemented | Maze Small; PCA20; FA5 selected on inner60/15; outer25 untouched by fitting | PCA reconstruction favors largest candidate; Gaussian FA approximates counts |
| MAP: Population covariance, similarity, CCA and principal angles | implemented descriptive | LINK Jan27/Jan30 calibration only; Covariance cosine0.718375; CCA/angles reported without independent inference | CCA in-sample noisy anchors; no causal connectivity or reliable residual covariance |
| MAP: Neural latent dynamics and geometric controls | implemented exploratory | Maze Small; Trial-local AR1, persistence/mean/permuted-time fitting controls executed | Teacher-forced one-step forecast; no validated physiological dynamics |
| DECODE: Mean, event-time, linear, ridge and Kalman | implemented | Maze Small; Mean MSE0.0383248; ridge0.0354214; Kalman0.0313141 m²/s² | Offline contemporaneous evaluation; source validation is exploratory |
| DECODE: MLP, GRU/LSTM, temporal CNN, Transformer, state-space sequence | implemented | Maze Small; Six architectures ×3 seeds executed; temporalCNN mean MSE0.0310519 | Unequal parameter counts; small fixed compute; CPU only |
| REMEMBER: Session indexing, feature mapping and shared/session representations | implemented within subject | Perich native audit; three LINK sessions; Session-scoped IDs; exact contact-key mapping; source/session representations compared | Perich neuron mapping unestablished; no cross-subject feature correspondence |
| REMEMBER: Subject-aware generalization | implemented exploratory | FALCON MonkeyL→MonkeyX; native recorded coverage; Source300 fit/112 eval; target75 calibration/354 eval; zero-shot MSE0.180151 vs source mean0.178826 normalized EMG² | Lossy anonymous features; negative zero-shot result; one session/subject; original EMG preprocessing precedes splits; M1-B draft |
| ADAPT: Frozen transfer, recalibration, few-shot/residual correction and budget curves | implemented | LINK Jan27→Jan30; Source300 fit/source75 eval; target75 calibration/300 eval; budgets1/5/15/50/75 | Small-budget calibration often worsens error; no test-driven method selection |
| ADAPT: Unsupervised marginal and supervised condition-anchor alignment | implemented exploratory | LINK first75 target calibration only; Unlabeled normalization MSE0.0263827 versus frozen0.0269661 flexion² | Marginal rescaling is not general identifiable alignment; extra target metadata disclosed |
| ADAPT: Shift and failure analysis | implemented descriptive | LINK Jan27/Jan30; Geometry, chronological error segments, extrapolated prediction fractions and block sensitivity reported | Two sessions do not identify drift causation; broader robustness unvalidated |
| FOUNDATION: Masked/predictive SSL, frozen probing and fine-tuning | implemented experimental | Maze Small and LINK; Within-session36 runs; cross-session168 controls/12 SSL runs | No broad SSL benefit demonstrated; no validated neural foundation model claim |
| FOUNDATION: Multi-recording pretraining and held-out-session transfer | implemented same subject | LINK Jan27+Jan30→Feb04; Reference pretrained/random zero-shot MSE0.0211969/0.0211803 flexion² | Same contacts/subject; first40 native samples per trial only |
| FOUNDATION: Random/supervised controls and model/data/compute ablations | implemented finite controls | Three LINK sessions; Four prespecified settings ×3 seeds; nested5/15/75 label budgets | Data100 changes SSL observations and scaler pool; finite ablations are not scaling laws |
| FOUNDATION: Session/subject identity leakage controls | implemented held-out diagnostics | LINK held-out150 trials; FALCON source112/target354; 24 date diagnostics: SSL98.0%, random97.78%; FALCON balanced subject accuracy100% vs chance50% | Implicit date/subject information retained; FALCON one recording per animal confounds subject, session and date; post-hoc diagnostic |
| INTERACT: Activity, behavioral alignment, trajectories and decoder predictions | implemented locally | Stored Maze real-data outputs; Trial/model/PCA controls checked in browser; no JS errors | Self-contained offline explorer; no hardware control |
| INTERACT: Session shifts, calibration curves, models and experiment inspection | implemented locally | Stored LINK/representation outputs; Calibration and ablation selectors checked; provenance/limitations visible | Cross-subject outputs unavailable; no simulated replacement |
| Research engine: Versioned configs, registries, preprocessing/checkpoints/provenance | implemented | All executed workflows; Schema-versioned configs; immutable splits;283 checkpoint/array entries; restored predictions checked | Direct requirements snapshot not transitive/cross-platform lock |
| Research engine: Statistical evaluation, causality/leakage checks and reports | implemented exploratory | Eight executed experiments; 96 common per-trial summaries; trial/block intervals and paired contrasts | Intervals depend on independence/block assumptions; no multiplicity-corrected significance |
| Release: Tests, wheel, clean-checkout reproduction and incremental PR | verification in progress | Host existing Conda environment; 205-test final workspace run passed; isolated fresh-asset reproduction exact; committed checkout/publication gates pending | Do not infer final release readiness |
| Release: Final full-scope release | incomplete; no final tag | Not applicable; v0.1.0 remains at8f9ffd91e4342713cb5a571e63d9931484caa143 | Cross-subject validation and release checks remain unresolved |

Base execution revision: `1250ee328abf3d8eaf3d040d7dea03a0a3a13456`. Exact report digests and row-level revision fields are in [the machine-readable matrix](completion_matrix.json). Reports include current source hashes; earlier dirty runs do not imply those files existed in the base commit.

## Exact continuation gates

1. Enforce human-selected documented-coverage policy; preserve unknown Perich coverage and validate FALCON cross-subject workflow.
2. Extend beyond the two-subject FALCON descriptive baseline using independently documented raw preprocessing and additional recordings; preserve separate Maze velocity, LINK flexion and EMG targets.
3. Use new untouched datasets/splits for further model selection; current validation reports are exploratory.
4. Broaden session/subject and temporal/compute robustness before neural foundation-model claims; retained session identity is a measured limitation.
5. Finish clean-checkout verification, reviewed incremental PR publication and evidence updates; final tag requires every completion criterion.

No continuation automation is installed. Work does not continue after a session unless a new active execution occurs.
