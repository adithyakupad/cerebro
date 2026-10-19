# M025 decoding diagnostic and scientific decision

2026-10-19. **PROPOSAL — awaiting researcher approval.** This is the first
decision gate, not a frozen experiment or evidence of improved decoding. The
complete Mission 025 message is the research contract; no additional supplied
specification file was located. No decoder source, historical configuration,
result or evaluation partition was changed. No new model was fitted or previously
unscored performance evaluated.

## Repository and evidence reconciliation

- Fetched main: `554103b13e8946c6a0d72127c541cdc466822dc0`.
  New branch: `codex/m025-decoder-diagnostics`, created from that exact revision.
  Initial working tree was clean on `codex/readability-refactor` at
  `8fadaf9df3cbf221bcacdbc65e7df49706a21dac`; that branch is preserved.
- PRs 2 and 3 are merged into main; M022 head `222486826cc4562669370b6f0486477b79bb740a`
  and M023/M024 integrated head `d506ff408b62a7d79b14c59987f20c1d7b46fef4`
  remain in its ancestry. [PR 4](https://github.com/adithyakupad/cerebro/pull/4)
  is still draft/open, based on main, at `8fadaf9`; it was not merged.
- Annotated historical v1.0.0 resolves to
  `b780e5cc53f246f4b305d413c4bd1afb962ff42c`;
  [public release](https://github.com/adithyakupad/cerebro/releases/tag/v1.0.0)
  exists. Main's package metadata says 1.1.0 and release notes exist, but the
  public release list currently contains only v1.0.0. Integration is not proof
  of v1.1 publication.
- Main [CI run 39171826466](https://github.com/adithyakupad/cerebro/actions/runs/39171826466)
  completed successfully at the verified main SHA. No M025 branch CI or PR is
  claimed. This gate leaves only two new audit documents locally.

Evidence reviewed: `AGENTS.md`, `docs/architecture.md`,
`docs/research/completion_matrix.md`, `docs/research/mission_020_traceability.md`,
`docs/research/m022_protocol.md`, `docs/research/m023_protocol.md`,
`docs/release/acceptance_matrix.md`, `docs/release/qualification_024.md`,
`reports/benchmarks.md`, `reports/evaluation_11.md`, M022/M023 reports,
the manifests/configurations below, decoder source and tests. Historical
negative adaptation and reliability findings remain intact. LINK held-out
dates protected by failed M022/M023 promotion gates are not released for reuse.

## Verified benchmark and data flow

| Property | Verified implementation/evidence |
| --- | --- |
| Recording | Jenkins, 2009-09-28; DANDI 000140 v0.220113.0408; CC-BY-4.0 |
| Asset | `7821971e-c6a4-4568-8773-1bfa205c13f8`; 29,207,528 bytes; SHA256 `dcaf3a524e2b2f65f163ee3b07789b8474bdfc6ca66098bc542ab93dff489884` |
| Neural observations | Authentic sorted-unit spikes; 107 held-in units, excluding 35 held-out units; complete observed trial windows |
| Counts | `100 × 70 × 107` trials × bins × units; 20 ms, left-closed/right-open bins |
| Target | `100 × 70 × 2` bin-mean hand velocity, m/s; native conversion preserved; no target interpolation or extrapolation |
| Clock | Recorded go cue −400 to +1000 ms; behavior valid within each bin, maximum gap 2 ms; predictions available at bin right |
| Partitions | 75 source train / 25 source validation; seeded inner 60/15; no window exclusions in this historical run |
| Preprocessing | Count mean/scale fit on inner 60 for selection, refit on 75 for final training; no evaluation fitting |
| Exposure | All 100 trials, including the 25 source-validation outcomes, have been inspected; none is now an untouched test |

Flow: NWB units/observation intervals + trial events + velocity → complete
trial-local windows → count/velocity tensors → immutable trial masks →
training-only scaling → model → inverse target scaling → per-trial physical
MSE → equal trial average. Sequences reset at trials; no true past behavior is
provided during evaluation. Arrays flattened for classical fitting contain
5,250 training bins, but these are not 5,250 independent trials.

| Decoder | Historical MSE, (m/s)² | Inputs / fitting |
| --- | ---: | --- |
| Training mean | 0.0383248163 | Constant training velocity |
| Go-time template | 0.0374873628 | Training mean at each event-relative bin; receives event clock |
| Linear / ridge | 0.0354568055 / 0.0354214378 | Current-bin standardized counts; ridge alpha 100 |
| PCA / FA ridge | 0.0362256903 / 0.0373429434 | PCA 20 / FA 5 dimensions; inherited raw ridge alpha |
| Kalman | 0.0313141455 | Supervised velocity-state linear Gaussian filter; alpha 10; trial-local transitions and prior; covariance floor 1e-5 |
| MLP | 0.03737999 | Current-bin nonlinear mapping |
| GRU / LSTM | 0.03667213 / 0.03663704 | Causal recurrent history |
| Temporal CNN | 0.0310519317 | Two width-3 causal convolutions, hidden 32, ReLU, linear readout; 5-bin support: current + 80 ms past |
| Transformer | 0.03594738 | One causal encoder layer; one head; hidden 32, feedforward 64, no dropout |
| Diagonal state space | 0.03458228 | Fixed exponential decay with learned input/output projections; not Mamba |

Deep values are means of seed-specific losses for seeds 0/1/2, not the loss of
an ensemble prediction. All use full-trial Adam batches, learning rate 0.001,
gradient clip 1, hidden 32 and a 20-epoch cap; best inner epoch is refitted on
75 trials. Parameter counts: MLP 3,522; GRU 13,602; LSTM 18,114; CNN 13,474;
Transformer 12,066; diagonal state space 3,490.

The CNN's observed advantage over Kalman is **0.8374%**, an absolute paired
trial mean difference of **−0.0002622138 (m/s)²**. A new descriptive replay of
existing losses (10,000 whole-trial bootstrap draws, seed 25) gives a 95%
interval **[−0.0020200141, +0.0016323320]**; CNN wins 13/25 trials. This is
exploratory, uncorrected for historical model comparisons and does not establish
superiority. Seeds measure optimization variation, not biological replication.

### Fairness and the three leading bottlenecks

Same units, observations, physical targets and trial masks make the historical
paired comparison meaningful. It is **not a controlled architecture comparison**:

1. **Optimization ceiling:** all 18 deep fits selected epoch 20, exactly the cap.
   CNN inner losses still fell from epochs 16 to 20: 0.81101→0.75299,
   0.79119→0.72978 and 0.82105→0.76410. More training may help, or may overfit.
2. **Temporal information:** ridge uses one bin, CNN five, Kalman recursive
   dynamics. Architecture and history are confounded. No history-matched linear
   baseline was tested.
3. **Timing/estimand:** no neural–behavior lag study was performed. Official NLB
   preprocessing uses a 120 ms behavioral lag and a different movement-onset
   window. That is an external timing prior, not proof of an optimal CEREBRO
   lag. Same-bin reconstruction and future-velocity forecasting are different
   estimands. [Pinned official source](https://github.com/neurallatents/nlb_tools/blob/42f8410b88e12db136910fa2f888b025ea0aa2ae/nlb_tools/make_tensors.py).

Classical tuning uses physical MSE; deep training and epoch selection use
coordinate-standardized MSE. Training target variances are approximately
0.04639770 and 0.03917656, giving y about 18.43% more relative weight than x
under the deep objective. This is a selection-objective mismatch, not evidence
of leakage. Ridge and Kalman separately search alpha [1,10,100,1000]; latent
ridge does not. Neither unequal tuning nor parameter count establishes a bug.

## Ranked mechanistic candidates

Costs are prospective estimates: low = hours of implementation / minutes of
CPU work; moderate = 1–3 days / hours of CPU work. They are not measured training
times. Each experiment would need its own approved, frozen information budget.

| Rank / mechanism | Supporting and contrary evidence | Falsifiable prediction and discriminating control | Cost; leakage risk |
| --- | --- | --- | --- |
| 1 E: optimization/capacity/regularization | Every deep run hits cap; late inner loss falls. No longer-run evidence; 75 trials may overfit. | Fixed CNN, 20 versus 200 maximum updates, inner-only selection; longer cap improves independent physical MSE. Keep architecture/optimizer/seed fixed. | Low implementation, moderate CPU; no selecting caps on final outcomes. |
| 2 B: history | CNN/Kalman beat instantaneous ridge; no matched-history linear arm. Nonlinearity/optimization remain alternatives. | Ridge histories 1/5/10 bins with matched alpha search and common evaluation bins; improvement without nonlinear capacity supports history contribution. | Low/moderate; prohibit cross-trial lags, future inputs and unequal warm-up masks. |
| 3 A: alignment | Zero-lag only; external NLB 120 ms convention. No local lag evidence; tasks/windows differ. | Development-only fixed timing curve with explicit forecast/reconstruction estimands; time-shift negative controls. | Low/moderate; final-target lag search and future inputs are forbidden. Not primary this sprint. |
| 4 C: trial-limited estimation | Only 75 train, sparse condition repetition, 25 evaluation trials. Existing performance is finite but unstable across trials. | Fixed whole-trial learning curves and coefficient dispersion, identical holdout and budgets; more trials reduce instability. | Moderate; repeated subsets are not independent sessions; condition-aware allocation uses extra metadata. |
| 5 I/J: tuning and methodology | Unequal tuning, coordinate objectives, no CNN–Kalman superiority interval. Shared masks and strict splits already work. | Identical physical-MSE selection, separately tuned baselines, paired trial contrasts; ranking changes without new architecture. | Low/moderate; no post-test grid expansion or winner selection. |
| 6 G: behavioral autocorrelation | Neighbor-bin correlations on inspected trials x≈0.9704, y≈0.9596; Kalman strong. Go-time template is weaker. | Training-only event template, Kalman dynamics-only control, condition-matched neural-trial permutation; neural gains must exceed clock/dynamics controls. | Low/moderate; past true velocity is privileged and cannot be an ordinary decoder input. |
| 7 D: normalization | Train-only standardization is present; target coordinate weighting differs. No evidence scaler leakage or normalization failure. | Fixed train-only scaling sensitivity with held-out fit prohibition; effect persists after matching objective. | Low; no transductive evaluation statistics. |
| 8 F: population representation | PCA/FA ridge did not win; dimensions selected for reconstruction/likelihood, not decoding. | Matched-history, independently regularized projection controls; gains require reproducible supervised evidence. | Moderate; fitting projections on evaluation would leak. No new representation family justified. |
| 9 H: nonstationarity | Trial chronology and independently recorded sessions can differ. Current data cannot isolate physiological drift. | Chronology-aware development diagnostics, then independent-session replication with session-specific fits; shift predicts failure after task controls. | Moderate; distribution summaries do not establish neural drift or neuron identity. |

J also limits every candidate: bins/seeds are not independent biological units;
previously viewed validation is development data; a best-model search requires
one frozen final comparison. No candidate is established as a physiological cause.

## Recommended experiment — approval requested

**Primary hypothesis:** the unchanged causal CNN is limited by the historical
optimization budget. Increasing the maximum from 20 to 200 full-batch updates,
with training-only preprocessing and inner-only epoch selection, improves
same-bin velocity decoding. **Strongest competing explanation:** additional
training overfits a small, autocorrelated set; apparent gains reflect task-phase
structure or baseline history rather than improved neural information use.

Proposed design, to be frozen and committed only after approval:

1. Use already inspected Small trials for development. Preserve the original
   75/25 and inner 60/15 identities. The 25 are descriptive development, never
   final tests. Compare fixed seeds 0/1/2 and the same existing CNN at 20 and
   200 maximum epochs. Both new arms choose epochs by **physical equal-trial
   MSE** on inner validation, with standardized training loss unchanged. Retain
   historical standardized-selection results separately; a matched 20-cap arm
   distinguishes epoch-selection changes from increased budget.
2. Controls: mean, event template, instantaneous ridge, history-ridge with
   exactly five trial-local bins, independently tuned Kalman, and fixed legacy
   CNN checkpoints on development only. Ridge/Kalman alpha grid stays
   [1,10,100,1000]. No new neural architecture. Score bins 5–70 for every primary
   comparator, including every inner-validation epoch/alpha selection,
   excluding the first four consistently; retain their original
   neural prefixes for recurrent initialization. Report all-70-bin sensitivity
   separately. A predeclared 10-bin ridge arm and dynamics-only Kalman may be
   secondary diagnostics, not extra candidates for the primary winner. The
   10-bin secondary comparison uses bins 10–70 for every paired model, without
   selecting models on final outcomes.
3. Promote this recipe to prospective session replication only if the extended
   CNN beats the matched 20-cap arm by at least 5% on mean inner-validation
   physical loss across the three seeds. Failure means a valid development
   negative result and **no consumption of the reserved session outcomes**.
   This gate is a proposed rule, not an already approved or passed criterion.
   Because those same inner trials select epochs, this gate is selection-
   conditioned development evidence, not an independent improvement estimate.
4. Prefer the already-local standard MC_Maze recording dated **2009-09-25** for
   independent recording replication. Reserve its original 574 validation
   trials now; do not read model outcomes. Use only its 1,721 original training
   trials for a fixed seeded 80/20 internal split (seed 5, 344 internal validation,
   1,377 fitting trials), preprocessing, regularization and epoch selection.
   Refit on all eligible source-training trials, then score eligible original
   validation once. Counts after exclusions must be recorded, not assumed;
   freeze exact eligible IDs/splits before fitting. If coverage exclusions
   change counts, use floor(20% of eligible train) for internal validation.
   Fit separate session-specific models with its 137 held-in units; this is
   method replication, **not unit-matched decoder transfer**.
5. Primary metric: mean of within-trial mean squared error over the two velocity
   coordinates, (m/s)². Primary scientific contrast: 200-cap minus matched
   20-cap CNN; average seed losses within each trial before uncertainty.
   Practical-improvement claim requires ≥5% relative reduction versus **both**
   matched 20-cap CNN and separately tuned Kalman, with paired 95% trial-bootstrap
   difference intervals below zero for both. Also report history-ridge; no
   claim of outperforming strong classical methods if it wins. Use fixed
   10,000 draws, seed 25; ordered five-trial-block sensitivity, per-coordinate
   R², absolute/relative effect and every seed. No best-seed selection or
   treating bootstrap replicates as animals. One replication session cannot
   establish general improvement across animals/sessions.
6. Secondary controls: train-only task-phase template; phase-preserving
   within-condition cross-trial neural permutation where repetitions permit
   (explicit offline null, not deployable input); causal prefix equality;
   fixed inference-only 10% contact dropout masks (seed 25), all methods on
   identical masks, no retuning. Replace masked standardized neural features
   with zero (training-mean replacement), not raw counts with zero; this is a
   missing-feature sensitivity, not measured electrode silence. Record this
   perturbation as robustness to missing observations, not neural drift. Resampling
   uncertainty remains conditional on fitted models.
7. Native timestamp/coverage and split guards precede modeling. Current+past
   spikes only, no smoothing with future samples, no behavior inputs at
   inference, no neuron-identity claim, no fitting on reserved outcomes.
   No primary lag search; any later 120 ms forecasting study needs its own
   approved estimand. If the independent recording fails coverage/target
   compatibility, report that blocker rather than silently change endpoint.

**Independent evaluation unit:** a held-out trial conditional on one recording;
independent recording replication is one additional session of the same animal.
The 25 Small trials and all historical LINK evaluation dates are not untouched.
No biological population-level confidence interval is available from this design.

### Available unscored data and exclusions

| Candidate | Exact provenance and exposure | Role / remaining gate |
| --- | --- | --- |
| Standard MC_Maze | DANDI 000128 v0.220113.0400; asset `26e85f09-39b7-480f-b337-278a8f034007`; SHA256 `a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4`; 690,612,247 bytes; CC-BY-4.0 | Hash verified locally. Native coverage/event audits exist, no decoder outcomes found. Jenkins Sep25 differs from Small Sep28. 137 held-in/45 held-out units; 1,721/574 source train/val. Coverage of the proposed decoder windows and exact identity partition must still pass. |
| Small challenge test | DANDI 000140 same version; asset `544a660e-a173-46f3-985a-60fd67e6ae1f`; SHA256 `ca8a0bef5f189eafb9db1961d617e065cb461360718fde1c16a538922a6fa5fe`; 689,312 bytes | Unacquired, metadata only inspected. Same session; optional future endpoint, **not an automatic fallback** for failed standard replication. Native/target schema, units, trial mapping and compatible windows unresolved. |
| LINK reserves | Feb24/Feb25/Jun26 normalized finger positions | Incompatible endpoint and protected by prior stopping rules; do not consume. |
| FALCON / Brochier / Perich | Author-preprocessed EMG / task-condition classification / unresolved native neural coverage | Not interchangeable with hand-velocity evaluation; existing limitations preserved. |

The [official NLB challenge guidance](https://neurallatents.github.io/challenge)
now says submissions have ended and test data are public; old private-server
assumptions are obsolete. The codepack's `data/eval_data_test.h5` is pinned at
commit `42f8410b88e12db136910fa2f888b025ea0aa2ae`, LFS SHA256
`f2f434d30193251b58e6a693381fdd185c8fbc0e47d38f8810e65295bc42c865`,
105,927,616 bytes. Only pointer metadata was inspected; neither schema nor
target values were downloaded. [Pinned repository](https://github.com/neurallatents/nlb_tools/tree/42f8410b88e12db136910fa2f888b025ea0aa2ae/data).

## Validation, known issues and cost

Executed in existing Conda `cerebro`, Python 3.11.16:

- `python -m pip check`: no broken requirements.
- Public-CI-equivalent `python -m pytest -q -m 'not data'`: **255 passed,
  22 deselected**, 14.01 seconds. This does not execute those 22 genuine-data tests.
- Independent decoder reviewer: **49 relevant tests passed**, including actual
  pinned Small preparation; two existing HDMF deprecation warnings.
- Existing `tools/validate_checkpoints.py`: **405 files**, **755 array digests**,
  **229 prediction replays**, **227 exact** and two within the existing tolerance
  rtol 1e-7 / atol 1e-9. No training. Output refreshed only in ignored processed
  validation storage; historical checkpoints/results untouched.
- New timing diagnostic used restored historical seed-0 checkpoints and one
  already inspected 70-bin trial, CPU, one thread, 3 warm-ups / 30 repetitions:
  median trial inference mean 0.0131 ms, ridge 0.0171 ms, Kalman 1.7780 ms,
  CNN 0.0487 ms, Transformer 0.1359 ms. This is **offline whole-trial timing**,
  not per-bin streaming latency, hardware delay or GPU performance. Deep input
  normalization was precomputed; classical restoration includes normalization
  and validation. Unequal overhead prevents architectural speed claims.
  Training time was not logged historically and was not measured by new fits.

Known issues remain separate from this proposal:

- `src/cerebro/reliability.py:190` omits configured nondefault ridge alpha in the
  permuted-risk fit. Frozen M023 alpha=1 matches the default; no evidence its
  published outputs change. Later fix needs a nondefault-alpha regression and
  requalification of affected future controls, preserving historical artifacts.
- `src/cerebro/sequence_benchmark.py:42` permits broadcast-compatible target
  mismatches. Reviewer reproduced `(2,4,2)` predictions against `(2,4,1)` targets.
  Historical tensors are correctly `(100,70,2)`. Before new training, a separate
  exact-shape guard/test should reject mismatches before any optimizer mutation;
  replay correct-shape behavior. Neither issue was repaired during this gate.
- Historical source-hash/checkpoint guards must stay intact. A previously noted
  cross-subject cache/source mismatch is not evidence against these velocity
  predictions and must not be bypassed to reuse that unrelated cache.

Three bounded independent reviewers audited decoder behavior/performance,
methodology/leakage and data provenance. They agree on the limitations; they
ranked history and optimization differently. We prioritize optimization because
the cap evidence is directly observable and it reuses an unchanged architecture;
the history-ridge control tests the strongest architectural confound. A further
methodology review of this proposal found no blocking leakage defect; its
requested common selection masks, history-10 burn-in, explicit mean-replacement
control and selection-conditioned gate caveat are incorporated above. ECC's
research-ops evidence workflow and Ponytail minimal-change review were applied.
Graphify's actual CLI was checked; no existing graph justified an index rebuild.
No tooling or environment was installed.

**Burden estimate:** 1–2 days for isolated correctness guards, frozen protocol,
history control and split tests; 1–2 days for development/replication CPU runs;
2–3 days for uncertainty, figures, independent review and application evidence.
Extending 20→200 is up to ten times the optimization updates, not a measured
tenfold wall-clock claim. Standard training has roughly 23 times as many trials
as Small; measure approved development throughput first. Budget one CPU day for
the fixed model set; if exceeded, stop and report rather than change epochs or
seeds after outcomes. The 11-day window to the researcher's October 30 deadline
is credible for this bounded study with prompt approval and eligible windows,
not a guarantee of a positive result or independent subject generalization.

The [official ML internship description](https://job-boards.greenhouse.io/neuralink/jobs/6594261003)
supports relevance to decoder evaluation, complex data, ML fundamentals and
clear communication. October 30 is the researcher's stated deadline; this audit
did not verify it as a posting deadline. Application evidence can already claim
reproducible offline benchmarks and honest negative research. Any new improvement
claim must await the frozen final gate; no individual contribution or hiring
qualification is inferred from platform breadth.

**Decision requested:** approve the optimization-budget experiment and controls,
the proposed 5% gates, and the one-shot standard-Maze validation partition above,
or amend them before any implementation or new outcome access. After approval,
commit the full protocol before experiments. Until then, no decoder edits,
experiment execution, publication or final-evaluation scoring.
