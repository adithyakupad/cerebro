# M023 reviewer reproduction guide

## Claim and scope

This branch tests calibration-only reliability and two-stage observed population dynamics. Neither prespecified primary candidate passes its practical promotion gate. Three additional recordings pass native eligibility but remain unscored. A positive reliability/transfer claim is not required to reproduce this negative result. The [manuscript](../../reports/m023_manuscript.md), [protocol](m023_protocol.md) and [pre-execution clarification](m023_reliability_clarification.md) define the analysis.

Use Python3.11 and the existing Conda `cerebro` environment. A new researcher can follow the repository installation guide and install declared extras with `python -m pip install -e '.[dev,classical,deep,brochier]'`; no new M023 dependency exists. Only NumPy/PyNWB/scikit-learn/Matplotlib are needed for these new experiments; the complete historical suite needs the original optional extras and separately acquired data.

## Public inputs and immutable partitions

From repository root, acquire the four development/source assets through their pinned public manifests:

```sh
for date in 20200127 20200130 20200204 20200205; do
  conda run -n cerebro python -m cerebro.dataset "configs/link_${date}.json"
done
```

The downloader verifies official asset metadata, byte size and SHA256. Attribute Temmar and colleagues' LINK corpus, [DANDI001201/0.251023.2336](https://doi.org/10.48324/dandi.001201/0.251023.2336), CC-BY-4.0. Raw paths are relative and Git-ignored. Native counts, source unit conflicts, normalized flexion units, clocks and coverage must retain their original definitions.

Source first300 trials are fitted; source225/75 selection is original. Each development date uses only first75 previously permitted calibration trials, split45 pool/30 evaluation. No later inspected target outcomes enter new selection. Keep exact row/condition/seed metadata; never substitute favorable dates or treat overlapping allocations as independent sessions.

Reconstruct M022 numerical inputs if absent. This command uses the unchanged M022 implementation and frozen configuration. Its revision metadata may differ from the historical report; M023 verifies the scientific array digests, exact allocation lineage and direct outcomes rather than requiring an old checkout's environment metadata:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n cerebro python -m cerebro.calibration_mechanisms --output data/processed/m022_calibration_verified
```

## Execute the frozen studies and numerical repetition

Run each A experiment into its own ignored directory:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n cerebro python -m cerebro.reliability --output data/processed/m023_reliability
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n cerebro python -m cerebro.reliability --output data/processed/m023_reliability_verified
```

For B, the standard command also regenerates its new public machine report. In a reviewer checkout, preserve/copy the checked-in report for comparison first; do not overwrite historical M001–M022 artifacts:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n cerebro python -m cerebro.research_dynamics --output data/processed/m023_dynamics
MPLCONFIGDIR=/tmp/cerebro-mpl conda run -n cerebro python tools/report_m023.py
MPLCONFIGDIR=/tmp/cerebro-mpl conda run -n cerebro python tools/m023_dynamics_report.py
```

The A renderer compacts resampling indices into digests/seeds while retaining all feature/outcome results. Full within-B bootstrap indices remain in the ignored experiment results and are deterministic from the recorded seed and selected trial indices. B checkpoints include scaling, observation model, transition, null, channel, behavior and condition parameters. Checkpoint replay accepts raw counts and verifies numerical restoration.

Expected fixed decisions: A selected method null; B temporal promotion false. Numerical results must agree, not merely the decisions. Current platform/runtime differences can alter final floating-point bits; compare with explicit tolerances if exact equality fails and disclose the difference. Never replace observed results or widen tolerances silently. FA likelihood scoring warnings are preserved in B metadata and limit interpretation; PCA primary endpoints do not use those likelihoods.

## Native audit without outcome consumption

The audit already acquired Feb24,Feb25,Jun26, but reproducing development does not require those files. To recheck eligibility only:

```sh
for date in 20200224 20200225 20200626; do
  conda run -n cerebro python -m cerebro.dataset "configs/link_${date}.json"
done
conda run -n cerebro python -m pytest tests/test_m023_data.py -k native -q
```

These tests inspect sample references, identity, contacts and finite observations; they do **not** execute or score a decoder. The [native audit](../datasets/m023_native_eligibility.json) explicitly distinguishes375 trials/session from one animal and records unreferenced native rows. No independent outcome command is provided because neither frozen promotion gate passed. A revised study needs a new protocol and explicit interpretation of prior access.

## Tests, checks and figures

```sh
MPLCONFIGDIR=/tmp/cerebro-mpl OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 conda run -n cerebro python -m pytest -q
conda run -n cerebro python -m pip check
conda run -n cerebro python -m compileall -q src tests
```

Public CI runs `pytest -m 'not data'` and separately collects data-marked cases without acquiring recordings. A fresh public clone therefore cannot claim authentic-data integration solely from green CI. Local cases require their declared data and skip when absent. See [validation record](m023_validation.json) for actual executed counts, checkpoint and numerical evidence. The full historical checkpoint validator independently restores original CPU outputs without fitting; it writes its generated verification record into ignored `data/processed/mission_014/checkpoints.json` and does not change model/result artifacts.

Primary figures are [reliability](../../reports/figures/m023_reliability.pdf) and [dynamics](../../reports/figures/m023_dynamics_comparison.pdf). Their renderers fit no models. The data test checks reliability JSON/PDF regeneration; numerical manifests verify B saved parameters and report values. Report hashes can legitimately differ after new Git/runtime metadata while shared scientific values remain identical.

## Ten-slide presentation

[PPTX](../../reports/m023_research_presentation.pptx) contains editable text and two native data charts. Its builder is `tools/m023_presentation.mjs`, requiring the locally bundled `@oai/artifact-tool`, not a new Python/research dependency. Set `RUNTIME_NODE_MODULES`, `RUNTIME_PYTHON` and `PRESENTATIONS_SKILL_DIR` from the installed Codex workspace runtime, then execute with its Node executable. It reads the executed A/B reports. Set `M023_PRESENTATION_OUTPUT=data/processed/m023_presentation_output/reproduced.pptx` for a new reproduction destination outside the private build directory; the finalizer intentionally refuses to overwrite an existing final file. Render/finalizer intermediates belong in ignored `data/processed/m023_presentation_build`.

All ten slide previews were inspected individually; package/layout/font/native-chart checks were executed. Native PowerPoint/Google Slides editing was not tested. The deck and [interview evidence pack](m023_interview_pack.md) document work and scientific judgment, not clinical competence, in-vivo/fMRI experience or a hiring guarantee.

## Independent review and publication boundary

Independent reviewers checked M022, frozen M023 design, actual code and scientific interpretations. Resolved findings and remaining numerical caveats are in the validation/acceptance records. Preserve draft PR2 independently; M023 is a separate draft research PR. No merge, new release tag, clinical claim, general subject-invariance or foundation-model conclusion is authorized by a passing software suite.
