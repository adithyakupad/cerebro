# v1.1 research reproduction and external review

This guide integrates preserved M022/M023 studies. Run from repository root in a disposable reviewer clone: experiment renderers regenerate public reports there. Do not overwrite historical artifacts in a research working tree. The release candidate has not yet been merged, tagged or published.

## Install and identify the candidate

```sh
git clone https://github.com/adithyakupad/cerebro.git
cd cerebro
git checkout research/m023-reliability-dynamics
conda create -n cerebro python=3.11
conda run -n cerebro python -m pip install -e '.[dev,classical,deep,brochier]'
conda run -n cerebro python -m pip check
conda run -n cerebro python -c "import cerebro; from importlib.metadata import version; print(version('cerebro'))"
```

Skip environment creation if `cerebro` already exists. Record `git rev-parse HEAD`; after authorized publication, replace the branch checkout with `git checkout v1.1.0`. Full historical capabilities and optional dependency purposes are described in [installation](../installation.md). No GPU is required for these studies.

## Inputs, partitions and attribution

Acquire only the four source/development assets:

```sh
for date in 20200127 20200130 20200204 20200205; do
  conda run -n cerebro python -m cerebro.dataset "configs/link_${date}.json"
done
```

The pinned manifests verify public asset metadata, size and SHA256. Attribute Temmar and colleagues, [LINK, DANDI 001201/0.251023.2336](https://doi.org/10.48324/dandi.001201/0.251023.2336), CC-BY-4.0. [Full attribution](../release/data_attribution.md) and [native coverage audit](../datasets/m023_native_eligibility.md) describe count-unit conflicts, sample-reference coverage, contact correspondence, normalized flexion and clocks. Raw recordings are not redistributed.

Source Jan27 first300 trials retain original225/75 penalty selection. Jan30/Feb4/Feb5 contribute only first75 previously permitted calibration trials:45 pool and30 development evaluation. There is one animal, not four independent subjects. Preserve frozen [M022](m022_protocol.md), [M023](m023_protocol.md) and [pre-execution clarification](m023_reliability_clarification.md). Later Feb24/Feb25/Jun26 are eligible but remain **unscored** because promotion failed; they are unnecessary for reproduction and must not be consumed as an alternative positive test.

## Reconstruct and repeat fixed results

Set single-thread numerical execution to match verified runs:

```sh
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export MPLCONFIGDIR=/tmp/cerebro-mpl
conda run -n cerebro python -m cerebro.calibration_mechanisms --output data/processed/m022_calibration_verified
conda run -n cerebro python -m cerebro.reliability --output data/processed/m023_reliability
conda run -n cerebro python -m cerebro.reliability --output data/processed/m023_reliability_verified
conda run -n cerebro python -m cerebro.research_dynamics --output data/processed/m023_dynamics
conda run -n cerebro python tools/report_m023.py
conda run -n cerebro python tools/m023_dynamics_report.py
```

These are fixed configurations, not model selection. M022 numerical inputs are checked against scientific array hashes and allocation lineage before M023 consumes them. Git/environment metadata may legitimately differ; scientific values, IDs and decisions must not. Inspect generated ignored result manifests and compare to committed reports; disclose numerical differences rather than silently widening tolerance. M022/M023 selected methods must remain null and the temporal gate false. Neither null alone substitutes for numerical comparison.

The fresh-install record linked below documents exact equality for2,171 shared array entries/23,625,391 values, independent reliability repetition, scientific report comparison and both M023 PDF reproductions. FA scoring warnings are retained; independent Cholesky checks reproduce900 trial-mean likelihoods. See [statistical appendix](v1_1_statistics_appendix.md) for units, equal-trial weighting, conditional block intervals and gate definitions.

## Compact review artifacts without raw data or fitting

```sh
conda run -n cerebro python tools/m024_tables.py
conda run -n cerebro python tools/build_review_package.py
conda run -n cerebro python -m pytest -q
conda run -n cerebro python -m compileall -q src tests
conda run -n cerebro python -m pip wheel --no-deps --no-build-isolation . -w /tmp/cerebro-wheel
```

[CSV tables](../../reports/v1_1_tables/), [configuration ZIP](../../reports/v1_1_configurations.zip) and [hash manifest](../../reports/v1_1_review_manifest.json) are deterministic. The ZIP has15 configuration/protocol/audit/attribution files; it contains no raw neural data, numerical checkpoints or derived arrays. Scientific report/source/figure hashes are indexed separately. [Primary PDFs and presentation](v1_1_manuscript.md#14-independent-validation-requirements-and-availability) reuse preserved outputs. The [M023 guide](m023_reproduction.md) documents the optional editable presentation builder and historical checkpoint validator.

Public CI executes software tests and separately collects data-marked tests; collection is not execution. A fresh clone without raw inputs skips data tests. Full local integration additionally requires historical acquisitions/checkpoints, independently checked in the release qualification. Fresh reproduction deliberately copies no processed inputs. CPU validation does not establish GPU performance or online BCI operation.

## Reviewer entry points

Read the [manuscript](v1_1_manuscript.md), [abstract](v1_1_abstract.md), [negative findings](v1_1_negative_results.md), [review checklist](v1_1_reviewer_checklist.md), [fresh installation evidence](../development/m024_fresh_install.md), and [release acceptance](../release/qualification_024.md). The original33-requirement scope remains unchanged. This package supports a narrow negative development study, not validated neural adaptation superiority, physiological drift or subject invariance.
