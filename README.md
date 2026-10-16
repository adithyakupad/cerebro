# CEREBRO

**Adaptive Neural Intelligence Research Platform — v1.0.0 release candidate.**

CEREBRO studies representations of real neural population activity for behavioral
prediction, population analysis, cross-session comparison and calibration-efficient
adaptation. It provides reproducible computational neuroengineering workflows,
including negative and inconclusive findings. Broad subject invariance and a
validated neural foundation model remain research objectives.

## Capabilities

| Capability | Implemented workflows |
|---|---|
| SENSE | Public recording acquisition, checksums, NWB/native Blackrock inspection, coverage-aware spike counts and behavior alignment |
| MAP | Event responses, condition/time-matched trial residuals, PCA/FA, population geometry and descriptive trajectories |
| DECODE | Mean, event-time, linear/ridge, Kalman and six sequence-model baselines |
| REMEMBER | Explicit subjects/sessions, contact correspondence and representation comparisons |
| ADAPT | Frozen source transfer, target-only/source-assisted calibration and disclosed latent-alignment controls |
| FOUNDATION | Masked/predictive self-supervised objectives and matched random/supervised transfer controls |
| INTERACT | Local, self-contained results explorer; no hardware control |

See the [architecture](docs/architecture.md), [integrated technical report](docs/research/mission_020_technical_report.md),
[33-requirement traceability](docs/research/mission_020_traceability.md) and
[release qualification](docs/release/qualification_021.md).
Software functionality, executed experiments and scientific conclusions are separate.

## Install

Python **3.11** and Conda are required. Use an existing `cerebro` environment if
available; create it only when absent:

```sh
git clone --branch codex/research-platform https://github.com/adithyakupad/cerebro.git
cd cerebro
# Only if the environment does not already exist:
conda env create -f environment.yml
conda activate cerebro
python -m pip install -e '.[dev,classical,deep,brochier]'
python -m pip check
python -c "import cerebro; print(cerebro.__file__)"
python -m pytest -m 'not data' -q
```

This candidate is on `codex/research-platform`. Once the owner approves and
publishes the release, `git checkout v1.0.0` selects the approved revision.
[Installation details](docs/installation.md) explain optional extras, CPU/GPU scope,
wheel installation and tests. `requirements-research.txt` records historical direct
versions; it is not a transitive lockfile.

## Quick start: authentic neural data

Run from the repository root:

```sh
python -m cerebro.dataset configs/mc_maze_small.json
python -m cerebro.sense_inspect configs/mc_maze_small.json --bin-width 0.02 --max-gap 0.002
python -m cerebro.event_audit configs/mc_maze_small.json
python -m cerebro.event_aligned configs/mc_maze_small.json
python -m cerebro.event_figures
```

The manifest pins DANDI **000140**, version **0.220113.0408**, asset
**7821971e-c6a4-4568-8773-1bfa205c13f8**, 29,207,528 bytes and published SHA-256.
Acquisition verifies official metadata and bytes. It needs public DANDI network
access and writes ignored data under `data/raw/`; no path editing is required.
Counts, masks and metadata are written to `data/processed/`. The SENSE machine
report is `reports/sense_01.json`; figures are `reports/figures/sense_01_*.png`.
Rerunning workflows intentionally regenerates their outputs; use a separate clone
to compare against immutable historical reports.

## Models and explorer

After acquiring MC_Maze Small:

```sh
python -m cerebro.benchmark configs/mc_maze_small.json
python -m cerebro.sequence_benchmark
python -m cerebro.representation_benchmark
python -m cerebro.dynamics
python -m cerebro.benchmark_figures
python -m cerebro.explorer --sequence data/processed/sequence_06
```

Open `data/processed/explorer.html` in a browser. Trial, model and PCA controls
inspect stored, hash-verified results. The HTML is local and self-contained.
LINK calibration, held-out-session SSL, exploratory FALCON, Brochier four-condition
classification/population analysis, downloads and checkpoint replay commands are
in the [workflow guide](docs/research/workflows.md). Deep experiments run on CPU by
default and can take longer than the quick start.

## Supported recordings and restrictions

| Recording | Validated use | Important restriction |
|---|---|---|
| [MC_Maze Small](docs/datasets/mc_maze_small.md) | Counts, event analysis, offline decoding and representation baselines | Single session; source validation outcomes have been inspected; unit/electrode region metadata conflict is retained |
| Standard MC_Maze | Native metadata and event feasibility | Not the source of the Small decoder benchmarks |
| [LINK](docs/datasets/link_feasibility.md) | Contact-level session transfer and finger-flexion targets | One animal; contact matching is not persistent neuron identity |
| [FALCON](docs/datasets/falcon_multisubject.md) | Exploratory author-preprocessed EMG and subject diagnostics | Original target preprocessing precedes our splits and cannot be inverted; no independently split-safe raw-target claim |
| [Brochier](docs/datasets/mission_019_brochier.md) | Native coverage, two-animal grip-by-load condition classification and descriptive residual variability | Classification is not continuous movement regression; one session per animal; physical sensor calibration and raw-data licensing conflict unresolved |
| [Perich–Miller](docs/datasets/longitudinal_feasibility.md) | Native metadata audit | No modeling until authentic neural observation coverage is established |

Exact versions, asset identities, checksums and attribution are in the manifests
and linked audits. Only required recordings are acquired. Raw recordings, large
arrays and trained checkpoints are excluded from Git and release attachments.
DANDI data here retain CC-BY-4.0 attribution. Brochier's ZIP root says CC-BY-4.0
while a bundled dataset license says CC-BY-SA-4.0; no raw redistribution is authorized
by this release. [Third-party attribution](docs/release/data_attribution.md) records
the distinction. CEREBRO source code is [MIT licensed](LICENSE).

## Evidence and limitations

The [technical report](docs/research/mission_020_technical_report.md) links numerical
findings to reproducible artifacts. Prespecified LINK low-budget source assistance
failed its primary benefit criterion. Brochier source-assisted condition accuracy
showed no clear advantage in either direction. Self-supervised gains are small,
mixed or absent against controls. Brochier residual covariance is rank limited;
its correlations and PCA trajectories are descriptive and do not establish causal
connectivity. FALCON upstream target preprocessing remains exploratory.

No general-purpose neural foundation model, stable subject-invariant representation,
clinical BCI, prospective live control or CUDA performance is claimed. Offline
current-bin decoding is not biological closed-loop operation. Human researchers
own model selection, interpretations and release claims. The original scientific
scope remains documented and incomplete where evidence is unavailable; a valid
negative experiment is a supported research output.

## Validation, citation and development

```sh
python -m pytest -m 'not data' -q
python -m pytest --collect-only -m data -q
# After acquiring recordings and generating the documented experiment outputs:
python -m pytest -q
python -m cerebro.registry
python tools/validate_checkpoints.py
```

Public CI executes software tests and only collects data-dependent cases. Local
full-data execution and exact reproduction evidence are distinguished in the
[qualification report](docs/release/qualification_021.md). Missing data never become
synthetic neuroscience evidence. Historical Mission 014–020 records remain preserved.

Cite this software using [CITATION.cff](CITATION.cff), and cite each underlying
dataset separately. Follow [AGENTS.md](AGENTS.md), the explicit scientific coding
style, and bounded INSPECT → PLAN → VERIFY → REPAIR → REVIEW loops.
