# Reproducible research workflows

Use the existing Python 3.11 Conda environment:

```sh
conda activate cerebro
python -m pip install -e '.[dev,classical,deep]'
```

For matching executed direct versions, install `requirements-research.txt` first.
It records this host's versions, not a transitive or cross-platform lock. A new
researcher without the environment can use `conda env create -f environment.yml`.
No new environment is created for development in the existing checkout.

## Within-session analysis and decoding

```sh
python -m cerebro.dataset configs/mc_maze_small.json
python -m cerebro.sense_inspect configs/mc_maze_small.json
python -m cerebro.event_audit configs/mc_maze_small.json
python -m cerebro.event_aligned configs/mc_maze_small.json
python -m cerebro.event_figures
python -m cerebro.benchmark configs/mc_maze_small.json
python -m cerebro.sequence_benchmark
python -m cerebro.representation_benchmark
python -m cerebro.dynamics
python -m cerebro.benchmark_figures
```

The classical workflow selects hyperparameters within source training, then
reports on the source validation trials. Neural features are held-in units only;
no published test asset is acquired. Mean/event-time/linear/ridge/Kalman and
latent-ridge models use identical complete observations. The six sequence models
use the same observations, epoch-selection split and three seeds. There is no
future-bin access. The time-template baseline receives the recorded go cue.

The representation experiment separates masked/predictive training from labeled
budgets and compares pretrained/random frozen probes and fine-tuned/supervised
models. Small within-session differences do not demonstrate a foundation model.
The dynamics workflow is a teacher-forced one-bin latent forecast, with persistence,
mean and time-permuted training controls; it is not physiological system identification.

## Larger Maze feasibility

```sh
python -m cerebro.dataset configs/mc_maze.json
python -m cerebro.nwb_audit configs/mc_maze.json --output reports/mc_maze_native_audit.json
python -m cerebro.maze_feasibility configs/mc_maze.json
```

The standard file is approximately 691 MB. The condition audit checks compatible
geometry; passing a repetition screen alone does not establish reliable covariance.
No standard-Maze test partition is downloaded.

## Longitudinal acquisition and calibration

```sh
python -m cerebro.dataset configs/perich_j_20160406.json
python -m cerebro.dataset configs/perich_j_20160407.json
python -m cerebro.nwb_audit configs/perich_j_20160406.json --output data/processed/perich_06_audit.json
python -m cerebro.nwb_audit configs/perich_j_20160407.json --output data/processed/perich_07_audit.json
python -m cerebro.dataset configs/link_20200127.json
python -m cerebro.dataset configs/link_20200130.json
python -m cerebro.dataset configs/link_20200204.json
python -m cerebro.longitudinal
python -m cerebro.representation_transfer
python -m cerebro.extended_figures
python -m cerebro.explorer --sequence data/processed/sequence_06 --longitudinal data/processed/longitudinal_08 --transfer data/processed/representation_09
python -m cerebro.registry
python -m pytest
```

The Perich pair supports native auditing. The human-selected policy requires
documented neural coverage, excluding these assets from modeling until that
evidence is available. LINK uses referenced samples and explicit
contact coordinates. The channel transfer benchmark fits source first300 trials,
selects on source-only 225/75, evaluates on source final75 and reserves target
first75 for calibration versus final300 for evaluation. Calibration prefixes are
nested; the target evaluation never chooses hyperparameters. Marginal normalization
and target PCA use all75 unlabeled calibration trials, even at smaller label budgets.
Condition-anchor alignment also uses commanded-target metadata. Comparisons are
exploratory, with their information-access differences disclosed.

The transfer-pretraining experiment uses two earlier recordings and a third
held-out session. Read its configuration and report for fixed prefix duration,
label budget, model/data/compute controls and all access policies. It does not
establish cross-subject generalization or a validated neural foundation model.

## Documented-coverage cross-subject baseline

```sh
python -m cerebro.dataset configs/falcon_m1_a.json
python -m cerebro.dataset configs/falcon_m1_b.json
python -m cerebro.cross_subject
python -m cerebro.subject_identity
```

FALCON provides native neural observation intervals for two monkeys and 16
matching muscle names. Seven anonymous count summaries avoid assuming neuron
correspondence. Source first300 original trial rows train, with source225/75
internal selection; target first75 rows provide nested calibration budgets and
the remaining354 trials provide evaluation. Coverage exclusions never replace
earlier rows with later trials. This custom calibration-asset experiment is not
an official FALCON score. Published targets are author-normalized EMG despite
native mV labels; original full-recording preprocessing precedes our splits.
See [the native audit and limitations](../datasets/falcon_multisubject.md).
M1-B is a checksum-pinned mutable draft. Reports and the calibration figure are
generated by the command; numerical checkpoints remain Git ignored.
The separate subject diagnostic uses whole-trial mean anonymous features, fixed
logistic regression and only source training plus target calibration for fitting.
It receives all75 target calibration feature trials, independently of decoder
label budgets. Held-out subject discrimination measures retained identity
information; it does not select decoders or certify an invariant representation.

## Outputs and integrity

Source assets and processed arrays/checkpoints/explorer HTML stay under Git-ignored
`data/`. Numerical reports and selected scientific figures are versioned under
`reports/`. `registry` verifies raw checksums and indexes configurations, experiments
and checkpoint digests using portable relative paths. Numerical array hashes bind
reports to data. Load trusted PyTorch checkpoints with `weights_only=True`; do not
load arbitrary pickle files. Different archive bytes do not imply different array
values, so scientific reproduction compares numerical contents and metrics.

The explorer is a self-contained local HTML file; open `data/processed/explorer.html`
in a browser. It requires no service or network access. The optional temporary
loopback server used for verification is not part of the installed platform.

See dataset documents for source licenses/attribution and metadata ambiguities.
CEREBRO source code is MIT; recording licenses remain the authors' CC-BY-4.0 terms.
No raw recording or large derived tensor is distributed with the source repository.

## Mission 014 release validation and new dates

The existing `cerebro` environment remains the development environment. For a
separate release check only, use a disposable destination prefix:

```sh
conda env create --prefix /tmp/cerebro-release-validation --file environment.yml
conda activate /tmp/cerebro-release-validation
python -m pip install -e '.[dev,classical,deep]'
python -m pip check
```

Run the acquisition and experiment commands above from the repository root.
A new checkout must generate processed outputs; copying old checkpoints does
not reproduce training. Data-dependent tests require the listed recordings and
stored real-data workflows. CI deliberately separates them:

```sh
python -m pytest -m 'not data' -q
python -m pytest --collect-only -m data -q
# After acquisition and real-data workflows:
python -m pytest -q
python -m cerebro.registry
python tools/validate_checkpoints.py
python -m cerebro.hardware_check
```

The hardware command checks each available backend with synthetic software
fixtures, reports unavailable hardware, and does not benchmark neural results.
The checkpoint tool independently replays raw-count predictions for the
classical, sequence and representation 07/09 formats, with integrity checks for
the remaining registry entries. Regenerate cross-subject results with the
current code before running the frozen-source identity diagnostic; earlier
historical inputs remain reproducible with their recorded source revision.

Mission 014 selected later dates before evaluation under the
[frozen protocol](mission_014_protocol.json), retaining existing methods:

```sh
python -m cerebro.dataset configs/link_20200205.json
python -m cerebro.dataset configs/falcon_x_20121210.json
python -m cerebro.longitudinal --config configs/longitudinal_14.json --output data/processed/longitudinal_14
python -m cerebro.representation_transfer --config configs/representation_14.json --output data/processed/representation_14
python -m cerebro.cross_subject --config configs/cross_subject_14.json --output data/processed/cross_subject_14 --report reports/cross_subject_14.json --markdown reports/cross_subject_14.md --figure reports/figures/cross_subject_14_calibration.png
```

Machine results for the first two commands are written to their output directory
as `results.json`; archived copies and the concise comparison are in
[Mission 014 results](../../reports/mission_014.md). These additional dates are
now inspected evaluation sets and must not be reused for method selection.
FALCON remains author-preprocessed exploratory EMG; new dates do not repair
upstream target leakage or add independent animals. Perich remains audit-only.

## Mission 016 prospectively selected LINK dates

The [dataset eligibility screen](../datasets/mission_016_eligibility.md) and
[frozen protocol](mission_016_protocol.json) were committed before model runs.
Acquire the three checksum-pinned targets, then reproduce the fixed same-subject
experiments and verified reports using the existing Python 3.11 environment:

```sh
python -m cerebro.dataset configs/link_20200127.json
python -m cerebro.dataset configs/link_20200130.json
python -m cerebro.dataset configs/link_20200206.json
python -m cerebro.dataset configs/link_20200211.json
python -m cerebro.dataset configs/link_20200222.json
python -m cerebro.longitudinal --config configs/longitudinal_16_20200206.json --output data/processed/longitudinal_16_20200206
python -m cerebro.longitudinal --config configs/longitudinal_16_20200211.json --output data/processed/longitudinal_16_20200211
python -m cerebro.longitudinal --config configs/longitudinal_16_20200222.json --output data/processed/longitudinal_16_20200222
python -m cerebro.representation_transfer --config configs/representation_16_20200206.json --output data/processed/representation_16_20200206
python tools/report_mission_016.py
python -m pytest
```

The report command verifies stored numeric-array digests and the committed
protocol hash before generating [Mission 016 results](../../reports/mission_016.md)
and three figures. Raw assets, arrays, and checkpoints remain Git-ignored. The
trial-level full reports are versioned under `reports/longitudinal_16_*.json`
and `reports/representation_16_20200206.json`. This is one Monkey N task and
contact-coordinate transfer, not independent-subject or online validation.
