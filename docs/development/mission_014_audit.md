# Mission 014 independent audit

## Scope and evidence

The independent data/protocol and model/evaluation reviewers inspected PR1 at
`491921c436aa22f9b8b1dcd969af6f9f974542ab`, against main
`8f9ffd91e4342713cb5a571e63d9931484caa143`. They were separate from the implementation
reviewer. Initial review was read-only. This document consolidates their findings
and a narrow review of fixes `9b66f3ef15674bed14f977ce373c777d01fd0c19` and
`a3a2dfd04daf3d923a47d133ce4acf30b5983571`.

Data scope: `falcon.py`, `link.py`, `longitudinal.py`, `cross_subject.py`,
`subject_identity.py`, `dataset.py`, `nwb_audit.py`, related tests, configurations,
and dataset documentation. Model scope: `population.py`, `benchmark.py`,
`kalman.py`, `sequence_models.py`, `sequence_benchmark.py`,
`representation_benchmark.py`, `representation_transfer.py`, `dynamics.py`,
`evaluation.py`, and related tests. This was not a new scientific experiment or
an exhaustive review of every repository file.

## Findings and resolution

| Severity | Finding at original head | Resolution and remaining limits |
|---|---|---|
| P2; blocked acceptance of imported frozen lineage | `src/cerebro/subject_identity.py:69-83` accepted coordinated report/split changes without checking original-row chronology or preparation code | Resolved in `9b66f3e`: current lines 71-128 verify frozen config digest, bound `cross_subject.py`/`falcon.py` source digests, exact chronological identities including inner subsets, original-row metadata, and label-budget prefixes. Regression tests reject coordinated swaps, stale preparation bindings, changed config, rows, and budgets. |
| P2; nonblocking for pinned recordings | `src/cerebro/link.py:24-31` cast out-of-range integer-valued counts to int64 | Resolved in `9b66f3e`: values must be below `2**63` before casting. Tests cover uint64 `2**63`, uint64 maximum, float `2**63`, large float input, and preservation of exact int64 maximum and native 0–8 counts. |
| P2; nonblocking for checked-in default experiment | `src/cerebro/sequence_benchmark.py:37-48` allowed invalid gradient clipping bounds | Resolved in `9b66f3e`: `train_epoch` rejects nonfinite or nonpositive bounds before model/optimizer mutation. Tests reject negative, zero, NaN, and infinite bounds and verify unchanged parameters. |
| Operational correction, no scientific-result defect | Checkpoint audit assumed its destination directory already existed | Resolved in `a3a2dfd`: `tools/validate_checkpoints.py` creates the output parent before writing. Narrow source review confirmed the directory creation is independent of earlier setup. |

The lineage reproduction used synthetic repository fixtures: exchange source
training trial 100 with evaluation trial 119 and target calibration trial 100
with evaluation trial 117, updating both report and split JSON while retaining
original config digest, original-row metadata, budget lists, and decoder outputs.
The original runner accepted these disjoint but incorrect fitting/evaluation
sets. The regression rejects them. This did not demonstrate corruption of the
checked-in authentic report.

The count reproduction returned negative int64 for `[[2**63]]`, despite a
nonnegative-integer input contract. Pinned LINK recordings contain tested counts
0–8 and were unaffected. The gradient reproduction used a one-weight linear
model: negative clipping changed weight 1 to approximately 1.1, increasing loss
from 1 to 1.21. These are software boundary tests, not neuroscience results.

No confirmed release-blocking model leakage or statistical-claim defect was
found in the reviewed default protocols. All three reproduced code defects are
resolved; that conclusion is limited to the reviewed scope and test evidence.

## Remaining limitations and compatibility

- The whole-file preparation digest guard is deliberately conservative. The
  publication writer change to `cross_subject.py` in `9b66f3e` also changes its
  digest. Executing the current diagnostic with the old frozen cross12 run now
  rejects it with `Frozen decoder preparation code differs from current source`,
  even though that writer change did not alter feature preparation. Reproduce
  historical diagnostics with their recorded source, or create a separate new
  decoder run with current source before diagnosing it. Do not rewrite historical
  report hashes to bypass this check. The guard does not compare the diagnostic's
  own newly edited source against historical hashes. This compatibility limit
  does not invalidate the historical measured report.
- Hashes identify consistency with declared inputs, not authenticity against an
  independent signing authority. An adversary able to replace all configurations,
  manifests and hashes is outside this local lineage consistency check.
- Author FALCON EMG filtering and quantile scaling precede CEREBRO splits. Native
  target samples at left bin edges are paired with neural counts through right
  edges. Both limits are disclosed: original preprocessing is not certified
  leakage-free, and prediction is offline rather than causal real-time control.
- Exact muscle names define output coordinates, not common physiological scaling
  or matched task distributions. Channel/contact correspondence is not stable
  neuron identity. One recording per FALCON subject confounds subject/session/date.
- Longitudinal target normalization/PCA receive the whole unlabeled calibration
  pool, while supervised label budgets use prefixes; unequal unlabeled access is
  disclosed and target evaluation fitting/selection is excluded. Commanded-target
  anchors are noisy trial means, not event-matched repeated responses; in-sample
  CCA does not establish transfer or neuron correspondence. Reviewed pinned LINK
  pairs use CO/run3; no concrete mixed-condition error was demonstrated.
- Sequence states reset within trials; source normalization, model selection and
  representation learning exclude evaluation trials. Within-session learned
  representations are not validated neural foundation models. Seed repetitions
  are not biological replication. Moving-block intervals are descriptive
  sensitivity analyses, not certified population confidence intervals.
- PCA reconstruction selection tends toward the largest candidate dimension;
  selected dimension is not evidence of intrinsic neural dimensionality.
- Original representation checkpoint flags mostly compare outputs from prepared
  features, rather than independently replaying raw-count normalization through
  physical outputs. The later checkpoint audit expands replay coverage, but
  representation07 random probes still depend on seeded encoder reconstruction
  and representation09 pretraining/session-identity components have integrity
  checks only. Unsupported historical formats are not validated by byte integrity.
- Generic `nwb_audit` does not enumerate LINK trial-reference series; that limit
  is already documented in the native LINK feasibility record.

## Executed checks

All Python checks used `/opt/anaconda3/envs/cerebro/bin/python`; no installation
or editable-environment switch was performed by these reviewers.

| Check | Evidence |
|---|---|
| Original data/protocol suite | **29 passed**, 8 upstream HDMF deprecation warnings, 14.34 s. `test_falcon`, `test_link`, `test_longitudinal`, `test_cross_subject`, `test_subject_identity`, `test_nwb_audit`; authentic adapter tests ran without skips. |
| Original model/evaluation suite | **100 passed**, 2 HDMF warnings, 5.18 s. `test_population`, `test_kalman`, `test_benchmark`, `test_sequence_models`, `test_representation_benchmark`, `test_representation_transfer`, `test_dynamics`, `test_evaluation`. This is software validation, not a new authentic-data benchmark. |
| Data-fix focused tests before integration | **21 passed**, 6.36 s (`test_subject_identity`, `test_link`); **16 passed**, 4 HDMF warnings, 12.07 s (`test_cross_subject`, `test_falcon`, `test_longitudinal`). |
| Preintegration authentic diagnostic replay | Original cross12 preparation digests still matched at that point. Temporary output fit counts `[300,75]`, evaluation counts `[112,354]`, descriptive balanced accuracy 1.0, and identical restored predictions. Historical artifacts were untouched. This predates the publication writer digest change described above. |
| Integrated narrow fix review at `a3a2dfd` | **38 passed**, 18.97 s: `python -m pytest -q tests/test_subject_identity.py tests/test_link.py tests/test_sequence_benchmark.py tests/test_longitudinal.py tests/test_cross_subject.py`. |
| Existing saved checkpoint audit inspected | `data/processed/mission_014/checkpoints.json` records 283 verified files, 368 report-array digests and 229 prediction replays, 227 exact; remaining replays satisfy declared `rtol=1e-7`, `atol=1e-9`. This reviewer inspected saved evidence and source; did not independently execute that replay command. |

The reports and synthetic reproductions underpinning this consolidation were
initially written under temporary paths. Their essential evidence and limitations
are reproduced here so this record does not depend on temporary-file retention.

## Tracked-file security, size and portability scan

Snapshot: tracked working-tree files at `a3a2dfd`, before this new audit document
or the ongoing Mission 014 report artifacts were tracked. Enumeration used
`git ls-files -z`; the scan read current file bytes, not all historical Git blobs.

| Check | Result |
|---|---|
| Tracked files | 168 files: 141 UTF-8 text, 27 binary; 12,846,271 bytes total. No tracked symlinks. Binary files were PNG figures. |
| Largest tracked artifact | `reports/signal_characterization.json`, 3,642,568 bytes; next `reports/representation_09.json`, 1,940,280 bytes. No file exceeded the explicit 10 MiB screening threshold. |
| Raw data/tabular/model archive screening | No tracked non-placeholder file under `data/` and no tracked `.nwb`, `.h5`, `.hdf5`, `.npz`, `.npy`, `.pt`, `.pth`, `.pkl`, `.pickle`, `.csv`, `.tsv`, `.parquet`, `.arrow`, `.feather`, `.mat`, `.edf`, `.bin`, or `.dat`. `.gitkeep` placeholders are allowed. Derived JSON reports and PNG figures are intentionally tracked. |
| Credential heuristics | No candidates in UTF-8 text for private-key headers, AWS AKIA/ASIA identifiers, GitHub token prefixes, OpenAI key prefixes, credential-bearing HTTP URLs, or quoted long API-key/secret-key/access-token/password assignments. No `.env`, `credentials`, `id_rsa`, `id_ed25519`, `.pem`, `.key`, `.p12`, or `.pfx` filename candidates. |
| Configuration portability | Recursively inspected all 22 tracked `configs/*.json` files; no string value beginning with `/` or a Windows drive-root prefix. Reviewed `environment.yml` and `pyproject.toml`: no machine-specific absolute installation prefix. |

Security screening is heuristic, not a certification that no secret exists. It
cannot detect every provider token, arbitrary high-entropy string, encoded value,
or unquoted credential assignment. Binary image metadata/content was not inspected
for secrets. Git history, ignored raw/checkpoint files, untracked experiment
outputs, remotes, external services and dependency vulnerabilities were not
scanned. The size threshold is a repository hygiene check, not a hosting limit.
No network source/license revalidation, fresh-environment validation, full new
scientific reruns, or cross-platform check was performed by this reviewer.
Those checks, where executed by the lead agent, belong in its release evidence.

Lead final prospective snapshot, including new Mission014 docs/reports before
staging: **187 files, 14,533,794 bytes**; largest file unchanged at 3,642,568 bytes.
Repeated selected private-key/AWS/GitHub/credential-URL pattern screening found
no candidates; no tracked/proposed raw-data or checkpoint archive extensions,
non-placeholder data files or absolute config values were found. This narrower
repeat has the same heuristic/history/binary exclusions; the detailed original
scan above is retained as a historical snapshot.
