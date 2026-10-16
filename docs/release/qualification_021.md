# CEREBRO v1.0 release qualification — Mission 021

**Release qualification: PASS within the documented scope. Publication: awaiting explicit owner approval and final published-head recheck.** No merge, `v1.0.0` tag or public release has occurred. This is qualification of an implemented research platform, not certification that every original scientific hypothesis succeeded.

Starting research head: `de18d68c2a6304fa02b40b3d477806f5891b2cda`. The exact validated code revision, fresh environment, wheel and UI checks are in [installation evidence](../development/mission_021_validation.json); every pipeline command, exit code and output is in [64-command evidence](../development/mission_021_commands.json). The final approval request binds the published PR head/base and GitHub test-merge snapshot. Historical scientific reports in the development repository were not regenerated or replaced.

## Independent audit and repairs

Two independently scoped reviewers inspected the PR history/diff and actual adapters, fitting, evaluation, checkpoints and claims. They found no demonstrated critical model defect, leakage, security failure or unauthorized raw redistribution in the reviewed paths. This is an evidence-backed review, not an exhaustive correctness or security certification.

Installed Ponytail and ECC verification-loop instructions guided the bounded checks; native Codex agents performed the independent reviews. Graphify's actual CLI help was inspected; no graph, watcher or hook was needed. Git, Conda, pytest, Ruff F checks, the scientific libraries and the in-app browser were used directly. The ECC Chrome tool was unavailable because Chrome stable is absent, so actual explorer interaction used the in-app browser instead. No global tooling or new runtime dependency was installed.

| Finding | Severity / classification before correction | Source / correction | Current state |
|---|---|---|---|
| Package and version test still declared `0.2.0.dev0` | P1 release metadata defect | `pyproject.toml`, `tests/test_installation.py`: consistent `1.0.0`; fresh editable and wheel imports verified | RESOLVED |
| README collectively described recordings as CC-BY-4.0 | P1 misleading license summary | `README.md`, `docs/release/data_attribution.md`: explicit Brochier CC-BY/CC-BY-SA conflict and no raw redistribution | RESOLVED |
| Standard MC_Maze incorrectly credited with Small decoder benchmarks | P2 scientific documentation defect | `docs/research/mission_020_technical_report.md`: standard dataset row now describes native/event feasibility only; benchmark values unchanged | RESOLVED |
| Main install omitted Neo extra; old data-test counts/status | P2 reproduction/documentation defect | README/install/workflow guide includes declared `brochier` extra and distinguishes current evidence from historical counts | RESOLVED |
| Mission 016 current-revision command contradicted historical renderer's strict revision checks | P2 documented reproduction defect | `docs/research/workflows.md`: isolated frozen-commit procedure, later renderer, original source installation; actually executed without relaxing checks | RESOLVED |
| Historical matrices conflated incomplete scientific success with the new software-release decision | P2 release interpretation defect | This current acceptance decision and matrix addenda preserve all original scientific statuses while applying Mission 021's explicit blocker definitions | RESOLVED |

No scientific values, partitions, hyperparameters, models or frozen protocols were changed. No new model family was introduced. The only executable candidate change is package metadata and its version assertion.

## Engineering verification

A public HTTPS clone at the expected research head was actually created. A new temporary Conda environment used Python **3.11.17**; declared extras `dev,classical,deep,brochier` installed successfully. The committed candidate preparation was then selected in that clone and reinstalled; dependency checks and isolated imports passed. The existing development `cerebro` environment remains Python 3.11 and its editable metadata/install tests also passed.

| Required check | Outcome and evidence |
|---|---|
| Public cloning, Python environment, editable installation and declared dependencies | PASS; actual public clone, new Conda prefix, full dependency resolution and `pip check`; no global tool installation |
| Package import | PASS; isolated import from fresh clone; separate wheel-target import resolves outside source |
| Automated tests | PASS; fresh full suite **245 passed**, 20 upstream HDMF deprecation warnings, no failures/skips; software selection **229 passed / 16 deselected**; **16 data cases collected** separately |
| Authentic acquisition | PASS; MC_Maze Small downloaded anew from public DANDI, 29,207,528 bytes with pinned metadata/SHA; other explicitly identified public raw recordings reused after source metadata and checksum checks |
| Dataset metadata/checksums | PASS; DANDI acquisition checks, native Perich audit-only, checksum-pinned Brochier NEV/NSx/odML and sampled neural coverage verified |
| Population workflows | PASS; SENSE, bin-width characterization, Maze event analysis, standard Maze feasibility, PCA/FA, Brochier residual variability and descriptive trajectories |
| Classical and deep decoding | PASS; classical and six sequence families executed on authentic Maze Small, with recorded restoration checks and unchanged partitions |
| Cross-session adaptation | PASS; LINK baseline, Mission 014 date, and all three Mission 016 held-out dates reproduced; negative primary finding retained |
| Cross-animal condition classification | PASS; native Brochier fixed L↔N four-class protocol reproduced; no continuous-regression substitution |
| Self-supervised representation workflows | PASS; within-session, held-out-session, Mission 014 and frozen Mission 016 reference controls executed; no broad benefit claim |
| Interactive explorer | PASS; fresh HTML, actual trial/model/PCA/calibration/ablation changes updated plots/tables; no warning/error logs; temporary loopback server closed |
| Checkpoint integrity/restoration | PASS in stated formats; **350 file digests**, **529 reported-array digests**, **229 independent CPU prediction replays** (227 exact, 2 within `rtol=1e-7, atol=1e-9`); new FALCON/representation workflows performed their own restoration checks |
| Reports, figures and manifests | PASS; regenerated in isolated clones and numerical lineage checked; no historical output overwritten in primary repository |
| Documentation commands/references | PASS for executed workflows and checked local links; fixed historical Mission 016 procedure executed; related-work references retain primary sources |
| Wheel packaging | PASS; `cerebro-1.0.0-py3-none-any.whl`, 118,995 bytes; 35 entries, MIT license; no recordings, tensors, checkpoints, tools/tests/reports bundled; separately installed wheel import passed |
| CPU / available GPU software backend | CPU and Apple MPS six-model synthetic forward/backward/update/restore smoke PASS; CUDA unavailable; all scientific experiments CPU |
| Security/portable configuration | Known credential signatures absent in 259 tracked files and 339 introduced history blobs; no tracked raw/checkpoint files or executable machine paths. [Scope](../development/mission_021_security.json) is heuristic, not vulnerability certification |

The clone received **no preexisting processed arrays or checkpoints**. Reused raw data were explicit ignored symlinks to public checksum-pinned source files, not hidden runtime dependencies. Mission 016 was generated from a separately installed clean frozen revision (`5a7376a694825005500cd357694fa8e27e2ce31e`) before its strict renderer ran. The release clone regenerated all other listed workflows under candidate code. This distinction is necessary for honest historical provenance.

## Numerical and historical integrity

[Reproduction comparisons](../development/mission_021_reproduction.json) cover 914 shared numerical arrays, **48,133,360 elements**, all bitwise equal; none needed the stated floating tolerance. All **144,137** compared numerical JSON values across signal characterization, Maze events, Mission 016, Brochier transfer and Brochier population reports were exactly equal. Original row identities, source ticks, masks and trials were retained. Ten additional `target_calibration_mean_*` arrays in regenerated longitudinal 08 were already disclosed in Mission 014; no historical shared array was removed or changed. Whole-file report hashes can differ because genuine revision/environment metadata changes; those differences are not silently rewritten as scientific differences.

Fresh checkpoint replay independently checks supported classical/sequence/representation 07/09 raw-count predictions. Other experiment formats use their workflow restoration/array-integrity checks where implemented. The old tool alone does not establish universal standalone export portability. Random frozen representation-07 probes still need the documented architecture/seed/runtime to reconstruct their encoder; they are not marketed as portable pretrained-model releases.

## Scientific acceptance classification

| Classification | Finding / decision |
|---|---|
| RELEASE BLOCKER | **None remains identified locally** after the documented repairs. Final candidate CI and exact-head approval remain required publication gates. |
| NONBLOCKING SCIENTIFIC LIMITATION | LINK low-budget source assistance failed its prespecified benefit criterion; valid negative experiment. Brochier four-condition source assistance was inconclusive; subject/session confounding remains. |
| NONBLOCKING SCIENTIFIC LIMITATION | FALCON targets were author-preprocessed before CEREBRO splits; raw EMG inversion/train-only reconstruction remains unavailable. Exploratory results are labeled accordingly. |
| NONBLOCKING SCIENTIFIC LIMITATION | Brochier condition residual covariance is rank-limited; nonlinear-statistic bootstrap ranges are biased/descriptive. Correlations do not establish causal connectivity. |
| NONBLOCKING SCIENTIFIC LIMITATION | Perich neural coverage is undocumented and modeling remains disabled. Brochier physical target calibration and source license-text conflict remain unresolved; native files are excluded from distribution. |
| NONBLOCKING SCIENTIFIC LIMITATION | Small/mixed/absent SSL gains do not validate broad transferable features or a general-purpose neural foundation model. Offline decoding does not demonstrate biological closed-loop control. |
| FUTURE RESEARCH | Independent biological subjects/sessions with synchronized, comparable raw continuous targets; prospective untouched evaluation; robust residual-covariance precision, dynamics and representation transfer. |
| FUTURE RESEARCH | Conditional speech, streaming, latency/failure handling and biological online control remain in the original long-term scope; no claimed implementation or clinical validation. |
| NOT TESTED | CUDA, scientific CPU/GPU equivalence, full-data Windows reproduction, clinical/online operation, exhaustive security/dependency vulnerability audit and standalone static typing/coverage. These are not advertised release capabilities. |

The [original 33-requirement audit](../research/full_scope_audit.json) and [current traceability](../research/mission_020_traceability.md) remain unchanged: **14 COMPLETE, 8 PARTIAL, 5 UNVALIDATED, 4 BLOCKED, 2 MISSING**. These do not become 33 successful scientific hypotheses because software is released. Mission 021 explicitly permits valid negative/inconclusive findings and unavailable-data limits when honestly represented. The historical full-scope scientific gate stays incomplete; the implemented software platform can qualify under this mission's release definition.

## Proposed publication and approval binding

Proposed title: **CEREBRO v1.0: Adaptive Neural Intelligence Research Platform**. Proposed annotated tag: **`v1.0.0`**, only at the verified resulting main commit after owner approval. [Prepared release notes](v1.0.0.md), [installation](../installation.md), [data attribution](data_attribution.md) and [software citation](../../CITATION.cff) are reviewable now. No raw data, checkpoint or binary asset is proposed as a release attachment.

Proposed merge: normal history-preserving merge commit for PR #1 into main, preserving all research commits. Expected main base is `8f9ffd91e4342713cb5a571e63d9931484caa143`. The final approval request records the exact reviewed PR head and GitHub synthetic test-merge SHA/tree. **The actual final merge commit SHA is assigned by GitHub when the approved merge executes; it cannot honestly be reported as an existing release commit beforehand.** After approval, recheck head/base/CI and mergeability, verify the resulting main commit/tree, then create the annotated tag and publish only the approved notes. Unexpected material changes require renewed approval.

Release notes remain a versioned local draft at this checkpoint. No release-creation command that could automatically create a Git tag is executed before approval. Main and `v0.1.0` remain preserved. Both public CI runs at candidate code revision `f14a4396af2eff4bb40e73809e227be9c806326c` succeeded (229 software tests each, 16 data cases collected only); final documentation-head checks and the exact test-merge snapshot are verified in the PR/approval request before authorization.
