# Mission 024: v1.1.0 release acceptance

**Release candidate only. No merge, tag or GitHub Release is authorized before the explicit owner checkpoint.** This qualification integrates preserved M022/M023 evidence; it does not restart research or score later sessions.

## Scope and independent review

PR2 remains the separately reviewable M022 contribution; PR3 stacks M023 and this integration on PR2. Independent scientific review inspected calibration access, whole-trial/session splits, train-only transforms, estimator identities, conditional uncertainty, state-space controls and numerical claims. The reviewer independently recomputed primary effects and ran24 focused tests successfully. No release-blocking scientific or mathematical defect was identified.

Two review clarifications were resolved without changing historical outputs: dynamics-mismatch features use selected B neural trials, whereas instability/disagreement additionally probe45 unlabeled pool trials; exported comparison gates now explicitly distinguish individual comparisons from overall failed promotion. A verified installation-documentation defect was fixed: clone instructions previously selected the obsolete research-platform branch. Package/citation metadata and installation tests now agree on1.1.0.

## Executed qualification evidence

The machine record `qualification_024.json` and [fresh-environment record](../development/m024_fresh_install.md) retain exact outcomes. The full local suite passed277 tests, including22 authentic-data cases, with20 pre-existing HDMF deprecation warnings in82.34 seconds.

- Existing Conda `cerebro`, Python3.11.16: editable1.1.0 installation, imports, dependency consistency, compilation and wheel build executed. No runtime dependency was added.
- Fresh public clone of original M023 head, new isolated Conda Python3.11.17, declared extras only:252 original software tests passed;4 available authentic-data tests passed,18 correctly skipped without historical/native inputs. Final integration source/package checks are recorded separately in the fresh record.
- Four pinned source/development NWBs were hash-verified; raw-only links supported source-to-result reconstruction. A separate official public Jan27 download actually succeeded and verified45,005,026 bytes and pinned SHA256.
- Fixed M022/M023 reconstruction matched2,171 numerical entries/23,625,391 values exactly against canonical outputs. Reliability repeated independently; scientific report fields matched; both M023 PDF files reproduced byte-for-byte. No processed arrays/checkpoints were copied into the fresh reconstruction.
- Historical restoration reexecuted:405 files,755 reported-array digests,229 CPU prediction replays;227 exact and2 within unchanged rtol1e-7/atol1e-9. New risk/population checkpoint replay and rotation checks are part of authentic-data integration.
- All212 historical protected source/config/report/dataset-documentation files compared with99ef183 remain byte-identical. No existing scientific source, frozen protocol or numerical report was rewritten.
- Current tracked snapshot contains no NWB/native raw files, NPZ/PT checkpoints, files above10MB, or matches to the inspected private-key/GitHub-token/AWS-key signatures. This bounded signature scan is not a general security proof.
- Deterministic configuration archive/table tests validate15 authorized configuration/protocol/attribution files and public statistical tables. Wheel inspection excludes recordings/checkpoints. Relative review-document links are checked.

## Acceptance matrix

| Category | Status | Release implication |
|---|---|---|
| Historical results, partitions and tags preserved | PASS | Required integrity gate |
| Calibration/session leakage and mathematical audit | PASS | No blocker identified in reviewed scope |
| Authentic-data source-to-result reproduction | PASS | Fixed development studies only |
| Checkpoint restoration and numerical lineage | PASS | CPU; unsupported historical formats retain stated limitations |
| Installation, declared dependencies, packaging | PASS | Fresh candidate check in linked record |
| Public CI on final PR head | Verify live before approval | Software execution and data collection are distinct |
| Mitigation/reliability/temporal promotion | SCIENTIFICALLY INCONCLUSIVE / failed frozen gates | Valid negative findings, not software blockers |
| Untouched later-session outcomes | NOT TESTED, intentionally | Failed promotion stops evaluation |
| GPU performance/native presentation-app interaction | NOT TESTED | No support/performance claim |
| Physiological cause, subject invariance, foundation-model validity | FUTURE RESEARCH | Not established by these studies |

There is no identified unresolved RELEASE BLOCKER after executed checks; this statement is conditional on final-head public CI and owner approval. One animal, three inspected development dates, overlapping allocations, nonchronological folds, conditional intervals, normalized behavioral units, FA warnings and acausal descriptive phase matching remain **NONBLOCKING SCIENTIFIC LIMITATIONS**. FALCON preprocessing, Perich coverage and Brochier redistribution restrictions remain unchanged. No raw data/checkpoints are included in the proposed release.

## Scientific decisions and original scope

M022 selects no mitigation; M023 selects no reliability model; the neural temporal practical gate fails. Modest controlled neural forecasts do not establish prospective adaptation benefit or physiological drift. Feb24/Feb25/Jun26 passed native eligibility but remain unscored, rather than unavailable. The original33 requirements remain14COMPLETE,8PARTIAL,5UNVALIDATED,4BLOCKED,2MISSING. Neither scope nor scientific stopping rules were relaxed.

## Proposed Git integration and approval binding

1. Verify exact approved heads and successful CI. PR2 head: `222486826cc4562669370b6f0486477b79bb740a`, base `main`. PR3 base: `research/m022-calibration-mechanisms`; its final exact head/tree and CI are supplied in the live approval report.
2. After explicit approval only, mark ready and merge PR2 using a normal **merge commit**, preserving ancestry and its branch while PR3 depends on it. Do not squash/rebase the stack.
3. Retarget PR3 to updated main; confirm expected remaining diff/tree, mergeability and CI. Obtain renewed approval if its contents change materially.
4. Merge PR3, verify resulting main commit and approved final tree. Only then create annotated `v1.1.0` and publish [verified release notes](v1.1.0.md), with no raw data/checkpoint attachments.

The future main merge SHA cannot be truthfully fixed before GitHub creates it. Approval binds the exact PR heads and final reviewed content/tree; the resulting main SHA must be checked afterward before tagging. Main currently remains `b780e5cc53f246f4b305d413c4bd1afb962ff42c`; historical `v1.0.0` remains untouched. Public mergeability/CI are time-sensitive and are rechecked at the approval boundary rather than claimed immutable in this document.

## External-review package

Start with the [consolidated manuscript](../research/v1_1_manuscript.md), [abstract](../research/v1_1_abstract.md), [methods appendix](../research/v1_1_statistics_appendix.md), [negative results](../research/v1_1_negative_results.md), [review checklist](../research/v1_1_reviewer_checklist.md) and [reproduction guide](../research/v1_1_reproduction.md). The deterministic [manifest](../../reports/v1_1_review_manifest.json) indexes sources, reports, original assets, figures and the editable presentation. No new model architecture, favorable outcome selection or unsupported physiological assertion is part of this release.
