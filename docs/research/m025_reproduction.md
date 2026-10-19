# Reproducing M025

This is a fixed offline velocity experiment, not a new architecture, cross-session
transfer of one trained decoder, or a new-subject study. The scientific specification
is [the committed protocol](m025_protocol.md); eligibility/exposure is documented in
[m025_evaluation_eligibility.md](m025_evaluation_eligibility.md).

## Existing owner artifacts: no-fitting replay

Use Conda `cerebro`, Python3.11, with the repository's declared `dev,classical,deep`
extras. The saved stage reports list the exact executed library versions.
From the repository root:

```sh
conda run -n cerebro python -m pytest -q
conda run -n cerebro python -m pip check
conda run -n cerebro python -m cerebro.optimization_study --stage development --replay
conda run -n cerebro python -m cerebro.optimization_study --stage final --replay
conda run -n cerebro python tools/m025_report.py
conda run -n cerebro python tools/m025_numerical_diagnosis.py
```

The final replay applies only if that stage completed. Replays validate file/array
hashes, restore every checkpoint, compare exact predictions and regenerate reports;
they do not retrain or select models. They require the ignored local
`data/processed/m025_*` artifacts. Those checkpoints and raw recordings are not
bundled in the public repository/wheel. An exact local replay is not a claim of
fresh-install training reproduction or biological replication.

## External reviewer: fresh training reproduction

Use a separate clone/reproduction branch at reviewed numerical-repair revision
8d459de (or its published descendant with identical scientific sources). Archive
the published reports separately before generating reviewer outputs in that clone;
never replace canonical public results. The earlier477ed95 implementation is
preserved for provenance but reproduces the disclosed float32 validation failure.
Follow README Conda creation and editable `.[dev,classical,deep]` installation.
Match the recorded numerical-library versions when exact input digests are needed.
Acquisition/preparation commands, verified against the existing CLI interfaces:

```sh
conda run -n cerebro python -m cerebro.dataset configs/mc_maze_small.json
conda run -n cerebro python -m cerebro.dataset configs/mc_maze.json
conda run -n cerebro python -m cerebro.benchmark configs/mc_maze_small.json
conda run -n cerebro python -m cerebro.optimization_study --stage development
```

The published historical `reports/classical_05.json` pins all input-array digests;
these guards are intentionally strict. A mismatch must be investigated, not disabled.
The two recordings are pinned CC-BY-4.0 DANDI assets; manifests specify source DOI,
version, size, SHA256 and relative local path. No manual source-path edits are needed.
Downloads were not repeated in M025 because authentic local bytes already matched.

Compare reproduced numerical outcomes against the published stage report. Elapsed
wall time and local Git revision are expected to differ. Independently review and
commit the new development report and eligibility evidence on that isolated reviewer
branch before invoking `--stage final`; the access guard requires cache/published
agreement and committed evidence. Only a passing frozen development gate permits
that run. On public data whose original outcomes are now known, this is **reproduction
of a published analysis**, not another prospective confirmation or an opportunity
to select revised hyperparameters. Never replace canonical historical reports.

The original owner evaluation used a disclosed pre-scoring recovery: see
[m025_recovery.md](m025_recovery.md). Owner-only `--recover-final` requires the
exact preserved partial-checkpoint/marker hashes; it is not a general retry switch.
A fresh reviewer reproduction uses the corrected validation normally, not that
owner-specific recovery manifest.

An exclusive `final_started.json` guards each evaluation directory. Do not delete it,
repeat final selection, or overwrite existing stage results. Recovery from an
interrupted evaluation must state the precise failure and be separately reviewed.
New outcomes require a newly approved independent cohort, not reuse of the574trials.

## Executed versus unexecuted

M025 executes local genuine-data training, independent stored-output recomputation,
exact checkpoint/prediction replay, source/asset lineage verification, software and
authentic-data tests, dependency checks, wheel creation and scientific figure
regeneration. Fresh Conda creation, a full second training reproduction from a
clean clone, GPU performance, streaming inference and biological closed-loop control
are not claimed. Source-checksum verification cannot establish unknown private data
exposure or longitudinal neuron identity.
