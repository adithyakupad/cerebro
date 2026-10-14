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
- [ ] Establish classical population / decoder baselines
- [ ] Study cross-session representations
- [ ] Extend to self-supervised neural models

## Status

**Mission 002: SENSE recording inspection.** A verified MC_Maze Small training
recording can be loaded, binned within trials, and visualized. No model is trained.

This repository is part of an ongoing research-engineering project backlog. Claims, results, and benchmarks will be added only when supported by reproducible experiments.

## Development

Clone and enter the repository. If Conda `cerebro` does not already exist, create
it with Python 3.11; otherwise use the existing environment:

```sh
git clone https://github.com/adithyakupad/cerebro.git
cd cerebro
# Only when the environment is absent:
conda create -n cerebro python=3.11 pip
conda activate cerebro
python --version
python -m pip install -e '.[dev]'
python -c "import cerebro; print(cerebro.__file__)"
python -m pytest
```

Runtime dependencies are NumPy, PyNWB, and Matplotlib. The development extra adds
pytest; setuptools is the build backend. Tests verify editable installation and import outside the
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
Tests run offline; the local real-recording test skips only when the dataset has
not been acquired. A full reproduction includes acquisition followed by all tests.

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
scientific choices. No PCA, FA, decoding, or adaptation has been implemented.

See [repository instructions](AGENTS.md), [architecture](docs/architecture.md),
[tooling inventory](docs/development/tooling.md), and
[CEREBRO-1 specification](docs/next_milestone.md),
[observed dataset inventory and commands](docs/datasets/mc_maze_small.md), and
[SENSE learning notes](docs/learning/sense_01.md). Dataset arrays and generated
figures remain local; later model experiments require separate approval.

## Principles

- Start with explicit scientific or engineering questions.
- Establish simple baselines before adding complex models.
- Use quantitative evaluation and documented failure modes.
- Preserve reproducibility through versioned data, configuration, and experiment outputs.
- Separate demonstrated results from planned capabilities.
