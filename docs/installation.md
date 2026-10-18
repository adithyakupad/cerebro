# Installation and reproduction

Use Python 3.11. Clone the public v1.1.0 research candidate; after approved publication select `v1.1.0` instead. Package version metadata alone does not mean the release has been published. All commands run from the clone root.

```sh
git clone --branch research/m023-reliability-dynamics https://github.com/adithyakupad/cerebro.git
cd cerebro
conda env create -f environment.yml
conda activate cerebro
python -m pip install -e '.[dev,classical,deep,brochier]'
python -m pip check
python -m pytest -m 'not data' -q
```

If `cerebro` already exists, activate it rather than recreating it. Base dependencies are NumPy, PyNWB and Matplotlib. `dev` adds pytest; `classical` adds SciPy/scikit-learn; `deep` adds PyTorch; `brochier` pins Neo for native Blackrock reading. No database, cloud account or service is required. The distribution is installable as a wheel, but repository research commands under `tools/`, configurations and historical reports require the source checkout. Editable installation is the tested researcher workflow; its installation tests intentionally verify that mode.

For Linux CPU-only PyTorch, install the official CPU wheel first, then the project extras as CI does:

```sh
python -m pip install 'torch>=2.5,<3' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[dev,classical,deep,brochier]'
```

The release qualification records actual versions. `requirements-research.txt` is a historical direct-version snapshot, not a universal dependency lock. CPU scientific execution is supported within the tested workflows. Apple MPS checks are synthetic software smoke tests only; CUDA, GPU scientific equivalence, and full-data Windows reproduction are not established.

## Representative reproduction

The [README quick start](../README.md) acquires checksum-pinned MC_Maze Small and produces authentic neural counts and event figures. The [workflow guide](research/workflows.md) contains all recorded analyses, target-specific commands and native Brochier acquisition. Acquisition commands verify public source metadata and bytes; network access is required only for acquisition. Data go into ignored `data/raw/`; derived arrays and trusted checkpoints go into ignored `data/processed/`. Paths are repository relative and need no manual editing.

For the integrated post-v1.0 studies, use the [external-review reproduction guide](research/v1_1_reproduction.md). It reconstructs M022 inputs and the fixed M023 experiments without scoring the later LINK cohort. Historical output comparisons should run in a disposable clone; the checked-in original reports remain an execution-time record.

Run `python -m pytest -q` only after acquiring required sources and generating experiment outputs for data-dependent cases. Public CI runs `-m 'not data'` and collects `-m data`; collected cases are not authentic-data validation. Use a disposable clone when regenerating historical reports, since commands intentionally replace their output reports and figures. Reproduction comparisons must consider numeric arrays and timing/split identities, rather than assuming version or archive-byte changes imply changed science.

Build a wheel with `python -m pip wheel --no-deps --wheel-dir /tmp/cerebro-wheels .`. No raw recording, generated tensor or trained model is distributed in that wheel. Source and wheel are MIT; datasets retain separate [attribution and restrictions](release/data_attribution.md). No raw Brochier redistribution is authorized while its source license texts conflict.
