# Mission 017 validation and independent review

Phase A published exactly three pre-existing local commits (`07094ac`, `5a7376a`, `fda96d8`) by fast-forward to the existing `codex/research-platform` PR branch. [PR #1](https://github.com/adithyakupad/cerebro/pull/1) was verified open and draft at `fda96d87c3bc9c43a038b8b727f3519724a6ee9b`. [GitHub run 38823922640](https://github.com/adithyakupad/cerebro/actions/runs/38823922640) and [run 38823917782](https://github.com/adithyakupad/cerebro/actions/runs/38823917782) both concluded success at that SHA. Their job logs each show `pip check`, **212 passed software tests, 15 data tests deselected**, and separate collection of all 15 data tests. Public CI did not download neural data or execute those cases. Remote `main` remained `8f9ffd91e4342713cb5a571e63d9931484caa143`; `v0.1.0` remained at its original annotated tag object `de736b0ba035617ded816085d93784190b65f1d1`.

Local existing Conda `cerebro`, Python 3.11.16:

| Check | Executed result |
|---|---|
| Phase A full suite at published Mission 016 head | 227 passed, 20 upstream HDMF deprecation warnings |
| Mission 017 full suite after diagnostic changes | 230 passed, 20 upstream HDMF deprecation warnings |
| Mission 017 public-CI-equivalent subset and data collection | 215 software tests passed; 15 data cases deselected and separately collected |
| Local dependencies | `python -m pip check`: no broken requirements |
| Mission 016 stored-artifact validation | 405 files and 755 reported arrays matched digests; 229 CPU predictions replayed, 227 exactly and two within recorded tolerance |
| Mission 016 report regeneration | Completed without tracked changes; frozen protocol/report hashes matched the completion matrix |
| New source/target diagnostic | Original four LINK asset SHA256s, native referenced observations, exact source/target split identities, and stored prediction-array digests checked; no fit or selection |
| Mission 017 unit/provenance tests | Three cases cover grouped statistics, empty input and versioned report/input hashes; included in the 230 full-suite pass |
| Compilation | `python -m compileall -q src tests tools` passed |
| Optional local Ruff lint | Not executed: `python -m ruff` is not installed in the existing Conda environment; no tooling was installed. |

The new [diagnostic generator](../../tools/diagnose_mission_017.py) records the immutable input code revision, its own SHA256, source asset identity and stored-report digest. Its [machine report](../../reports/mission_017_adaptation.json) and [figure](../../reports/figures/mission_017_source_coverage.png) are versioned; raw recordings and numerical checkpoints remain ignored. A second generator pass reproduced identical SHA256s: report `81454ddb107b6f84df6c1a7610fea7f021d2637cc3c36d63f6195826f3d52873`, figure `c82c6da31d52c7236ab4540b505a37236531ee07086e65004fb18af8e91f5f60`.

Independent read-only review inspected the code, reports and source-backed eligibility claims. It found **no P0/P1 defect or apparent train/evaluation leakage**. One P2 hardening request—assert every source validation/evaluation and target calibration identity before naming diagnostic groups—was implemented. The reviewer verified the Brochier session identifiers in the primary paper; direct native asset terms, checksums and timing remain an eligibility blocker, not an inferred pass.

No new cross-subject model, new architecture, GPU experiment, fresh Conda install, or biological closed-loop test was performed. The Mission 017 evidence screen is source-document based for outside candidate corpora; native Indy/Loco/Brochier assets were not downloaded or accepted for modeling.
