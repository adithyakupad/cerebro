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
