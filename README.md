# Cerebro

> Adaptive neural intelligence from real neural population recordings.

## Thesis

Study whether neural population representations can support behavioral decoding,
cross-session generalization, and calibration-efficient adaptation. These are
research objectives, not demonstrated capabilities. Humans own model selection,
interpretation, and scientific conclusions.

## Milestones

- [x] Establish conceptual scientific architecture and Python package
- [x] Inspect a verified public neural recording
- [x] Execute exploratory classical and sequence decoder baselines
- [x] Execute disclosed channel-level cross-session calibration comparisons
- [x] Implement masked/predictive representation controls
- [ ] Satisfy every full-scope scientific validation and release criterion

## Status

**Development version 0.2.0.dev0.** Real-data workflows now cover SENSE, PCA/FA,
classical and causal sequence decoding, latent forecasts, LINK channel transfer,
calibration and controlled representation experiments. A local explorer reads
stored results. These are exploratory research workflows; the full project is
not declared complete. See the [completion matrix](docs/research/completion_matrix.md),
[execution commands](docs/research/workflows.md) and [scientific reports](reports/benchmarks.md).

This repository is part of an ongoing research-engineering project backlog. Claims, results, and benchmarks will be added only when supported by reproducible experiments.

## Development

Clone and enter the repository. If Conda `cerebro` does not already exist, create
it with Python 3.11; otherwise use the existing environment:

```sh
git clone --branch codex/research-platform https://github.com/adithyakupad/cerebro.git
cd cerebro
# Only when the environment is absent:
conda create -n cerebro python=3.11 pip
conda activate cerebro
python --version
python -m pip install -e '.[dev,classical,deep]'
python -c "import cerebro; print(cerebro.__file__)"
python -m pytest
```

Runtime dependencies are NumPy, PyNWB, and Matplotlib. The development extra adds
pytest; `classical` adds SciPy/scikit-learn and `deep` adds PyTorch. Setuptools is
the build backend. `requirements-research.txt` records executed direct versions;
it is not a transitive lock. These development workflows are on the named branch;
published `main`/`v0.1.0` preserve the earlier foundation. Tests verify editable installation and import outside the
repository without adding `src` to the test import path. Keep raw recordings,
processed data, and generated figures out of Git.

## Reproduce the initial SENSE experiment

Run from the repository root after installation:

```sh
python -m cerebro.dataset configs/mc_maze_small.json
python -m cerebro.sense_inspect configs/mc_maze_small.json --bin-width 0.02 --max-gap 0.002
python -m pytest
```

The manifest pins DANDI **000140**, version **0.220113.0408**, asset
**7821971e-c6a4-4568-8773-1bfa205c13f8** (29,207,528 bytes), and its published
SHA-256. Acquisition checks official metadata and verifies the downloaded bytes.
No path editing is required. The raw file goes into `data/raw/mc_maze_small/`.
An interrupted `.part` download remains available for diagnosis; inspect and
remove that partial file before retrying. Network access to DANDI is required.

Outputs are `data/processed/sense_01.npz`, metadata CSVs, and
`reports/sense_01.json`. Four figures in `reports/figures/sense_01_*.png` show
spike raster, population counts, hand/cursor trajectory, and timestamp alignment.
The compact reference figures are published; raw recordings and large derived
arrays stay Git-ignored. Rerunning intentionally regenerates the SENSE outputs.
Software tests run offline with `python -m pytest -m 'not data'`. Twelve
data-marked cases require acquired recordings or generated real-data experiments;
public CI collects those cases without running them. A full reproduction includes
acquisition and the research workflows followed by `python -m pytest -q`.

The initial 20 ms matrix has 14,342 bins × 142 sorted units. Behavior is averaged
within each bin, without interpolation or extrapolation. Full bins restart per
trial; incomplete tails exclude 407 spikes that remain in the original data.
Validity masks distinguish missing coverage from observed zero counts.

## Attribution and scientific limitations

Churchland, Mark; Kaufman, Matthew (2022). *MC_Maze_Small: macaque primary motor
and dorsal premotor cortex spiking activity during delayed reaching*, version
0.220113.0408. DANDI Archive. [Dataset DOI](https://doi.org/10.48324/dandi.000140/0.220113.0408).
The recording is licensed [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
Generated figures and summaries derive from that recording; full source identity,
checksum, and citation are preserved in the manifest and reports.

This is one curated session of successful trials, not evidence of cross-session
generalization. Stored electrode links conflict with 70 M1-prefix unit IDs;
no anatomical correction is silently applied. File-time alignment does not verify
hardware latency. Binning and the 2 ms behavior-coverage tolerance remain explicit
scientific choices. These describe the original SENSE milestone; subsequent
population, decoding and adaptation experiments are documented below.

See [repository instructions](AGENTS.md), [architecture](docs/architecture.md),
[tooling inventory](docs/development/tooling.md), and
[CEREBRO-1 specification](docs/next_milestone.md),
[observed dataset inventory and commands](docs/datasets/mc_maze_small.md), and
[SENSE learning notes](docs/learning/sense_01.md). Dataset arrays and generated
figures remain local; later model experiments require separate approval.

## Local signal characterization experiment

On the `research/signal-characterization` branch, after acquiring the same asset:

```sh
python -m cerebro.characterize configs/mc_maze_small.json
python -m cerebro.characterize_figures
python -m pytest
```

This compares 5/20/50 ms count statistics using both native coverage and matched
trial endpoints. See [scientific report](reports/signal_characterization.md),
[machine-readable results](reports/signal_characterization.json), and
[assumptions and learning workflow](docs/learning/signal_03.md). These are
descriptive observations; temporal Fano factors mix task epochs and conditions.
Mission 003 itself contains no dimensionality reduction or decoder; later
workflows are documented in [research commands](docs/research/workflows.md).

## Local event-aligned experiment

The preserved Mission 004 experiment uses the same pinned asset:

```sh
python -m cerebro.event_audit configs/mc_maze_small.json
python -m cerebro.event_aligned configs/mc_maze_small.json
python -m cerebro.event_figures
python -m pytest
```

The [feasibility audit](reports/event_04_feasibility.md) establishes only two or
three training repetitions per compatible condition. [Results](reports/event_04.md)
use the human-selected go cue, −400 to +1000 ms, and 20 ms bins. All summaries
exclude validation trials. Condition means and residuals are descriptive;
reliable residual correlations are withheld. See [learning notes](docs/learning/event_04.md)
and the reviewable [alignment protocol](configs/event_04.json).

## Current model and longitudinal workflows

```sh
python -m cerebro.benchmark configs/mc_maze_small.json
python -m cerebro.sequence_benchmark
python -m cerebro.representation_benchmark
python -m cerebro.dynamics
python -m cerebro.benchmark_figures
python -m cerebro.explorer --sequence data/processed/sequence_06
```

Open `data/processed/explorer.html` locally. It contains trial/model selection,
velocity comparisons, neural activity and training-fitted PCA trajectories, with
provenance and limitations. It needs no server, CDN or cloud account.

LINK, Perich–Miller and FALCON acquisition/audit commands, chronological calibration,
cross-session representation controls, cross-subject baselines and registries are in
[the workflow reference](docs/research/workflows.md). Maze hand velocity and LINK
finger flexion targets are separate experiments. Contact matching does not imply
stable neurons. Small-budget recalibration can worsen prediction; negative
findings and missing metadata are retained. The human requires documented neural
coverage; Perich remains audit-only. FALCON supports a separate two-subject EMG
baseline with recorded coverage and anonymous neural features. Frozen transfer
failed to beat its mean baseline; target calibration improved prediction. Native
EMG is author-normalized, despite mV labels, and original preprocessing precedes
our splits. A held-out diagnostic classified the two recording subjects at 100%
balanced accuracy from anonymous features; subject, session and date are
confounded, so those features are not identity-free. No broad cross-subject
success, biological closed-loop system or
validated neural foundation model is claimed.

Code is [MIT licensed](LICENSE); recording licenses and attribution remain
dataset-specific CC-BY-4.0. Raw recordings and large derived arrays/checkpoints
are never included in Git.

## Principles

- Start with explicit scientific or engineering questions.
- Establish simple baselines before adding complex models.
- Use quantitative evaluation and documented failure modes.
- Preserve reproducibility through versioned data, configuration, and experiment outputs.
- Separate demonstrated results from planned capabilities.

## Scientific release hardening (Mission 014)

The reviewed research branch has a fresh Python 3.11 Conda reproduction of all
documented workflows: 222 tests passed with real-data artifacts available;
software-only selection passed 210 tests and deselected 12 data cases. CPU
research runs and six-model Apple MPS software smoke checks passed. CUDA and
GPU scientific equivalence remain untested. This evidence does not authorize
merge or a final release tag.

See the [release acceptance matrix](docs/release/acceptance_matrix.md),
[independent audit](docs/development/mission_014_audit.md),
[installation and checkpoint evidence](docs/development/mission_014_validation.md),
[new-date comparisons](reports/mission_014.md), and
[FALCON preprocessing determination](docs/datasets/falcon_preprocessing.md).
The published EMG cannot be inverted to raw targets; those results remain
explicitly author-preprocessed and exploratory. Perich remains audit-only.
Additional LINK/FALCON dates extend evaluation without adding independent
animals. Small and mixed representation differences do not validate a general
neural foundation model. Historical negative results are preserved.

## Integrated research evidence (Mission 020)

The [technical report](docs/research/mission_020_technical_report.md) consolidates the scientific thesis, recorded datasets, model comparisons, population findings, negative results and limitations. The [33-requirement traceability matrix](docs/research/mission_020_traceability.md) preserves the original scope. The new [Brochier population report](reports/mission_020_brochier_population.md) analyzes authentic, fully sampled native neural windows around a recorded task event; its rank limits prevent a reliable full residual-covariance claim. Follow the [reproduction commands](docs/research/workflows.md) to acquire the pinned assets and regenerate the report and figures. Full scientific completion and the final release remain pending.
