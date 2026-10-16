"""Render stored authentic-data benchmark outputs without fitting models."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from cerebro.benchmark import array_digest


def checked_arrays(root, report, filename):
    with np.load(Path(root) / filename, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    for name, metadata in report['arrays'].items():
        if array_digest(arrays[name]) != metadata['sha256']:
            raise ValueError('Array/report lineage mismatch')
    return arrays


def render(classical_path, sequence_path, figures_dir='reports/figures'):
    classical_path = Path(classical_path)
    sequence_path = Path(sequence_path)
    classical = json.loads((classical_path / 'results.json').read_text())
    sequence = json.loads((sequence_path / 'results.json').read_text())
    input_hash = hashlib.sha256((classical_path / 'results.json').read_bytes()).hexdigest()
    if sequence['input_report_sha256'] != input_hash:
        raise ValueError('Sequence experiment used a different classical input')
    arrays = checked_arrays(classical_path, classical, 'arrays.npz')
    checked_arrays(sequence_path, sequence, 'predictions.npz')
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    header = (
        f"MC_Maze Small | DANDI {classical['asset']['dandiset']} v{classical['asset']['version']}\n"
        f"asset {classical['asset']['asset_id']} | 20 ms bins, 107 held-in units\n"
        '75 source training / 25 source validation trials; offline exploratory evaluation'
    )
    figure_paths = []

    def save(figure, name):
        figure.suptitle(header, fontsize=8)
        figure.tight_layout(rect=(0, 0, 1, .85))
        path = figures_dir / ('benchmark_' + name + '.png')
        figure.savefig(path, dpi=160)
        plt.close(figure)
        figure_paths.append(str(path))

    names = list(classical['metrics'])
    values = np.array([classical['metrics'][name]['mse_m2_s2'] for name in names])
    intervals = np.array([classical['metrics'][name]['trial_bootstrap_mse_interval'] for name in names])
    errors = np.vstack([values - intervals[:, 0], intervals[:, 1] - values])
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(names, values)
    axes[0].errorbar(names, values, yerr=errors, fmt='none', color='black', capsize=3)
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].set(ylabel='Velocity MSE (m²/s²)', title='Classical models: whole-trial percentile bands')
    seed_results = defaultdict(list)
    for result in sequence['results']:
        seed_results[result['model']].append(result['mse_m2_s2'])
    for index, (name, seeds) in enumerate(seed_results.items()):
        axes[1].scatter(np.full(len(seeds), index), seeds, label=name)
    axes[1].set_xticks(np.arange(len(seed_results)), list(seed_results), rotation=45)
    axes[1].axhline(classical['metrics']['mean']['mse_m2_s2'], color='gray', linestyle='--')
    axes[1].set(ylabel='Velocity MSE (m²/s²)', title='Deep models: three initialization seeds (not trial CIs)')
    save(figure, 'errors')

    figure, axes = plt.subplots(1, 2, figsize=(10, 5))
    for axis, kind, ylabel in [(axes[0], 'pca', 'Standardized reconstruction MSE'), (axes[1], 'fa', 'Negative Gaussian log likelihood / bin')]:
        candidates = classical['geometry'][kind]['candidates']
        dimensions = [row['dimension'] for row in candidates]
        losses = [row['inner_validation_loss'] for row in candidates]
        axis.plot(dimensions, losses, marker='o')
        axis.set(xlabel='Latent dimensions', ylabel=ylabel, title=kind.upper() + ': inner 60/15 trial selection')
    save(figure, 'dimensions')

    latents = arrays['pca_validation_latents'][0]
    seconds = (np.arange(latents.shape[0]) + .5) * .02 - .4
    figure, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].plot(latents[:, 0], latents[:, 1], color='lightgray')
    colors = axes[0].scatter(latents[:, 0], latents[:, 1], c=seconds, cmap='viridis', s=15)
    axes[0].set(xlabel='PC1 (standardized count coordinates)', ylabel='PC2', title='First source validation trial; training-fitted axes')
    figure.colorbar(colors, ax=axes[0], label='From go cue (s)')
    explained = classical['geometry']['pca']['training_explained_variance_ratio']
    axes[1].plot(np.arange(1, len(explained) + 1), np.cumsum(explained), marker='o')
    axes[1].set(xlabel='Components', ylabel='Training cumulative explained variance', title='Population geometry is descriptive')
    save(figure, 'geometry')

    validation_ids = classical['evaluation_trial_ids']
    trial_index = np.flatnonzero(arrays['trial_ids'] == validation_ids[0])[0]
    figure, axes = plt.subplots(2, 1, figsize=(10, 6))
    for coordinate, axis in enumerate(axes):
        axis.plot(seconds, arrays['velocity_m_s'][trial_index, :, coordinate], label='Observed native-bin velocity')
        for name in ('ridge', 'kalman'):
            axis.plot(seconds, arrays[name + '_prediction_m_s'][0, :, coordinate], label=name)
        axis.set(xlabel='From go cue (s; center labels)', ylabel=f"{'vx' if coordinate == 0 else 'vy'} (m/s)")
        axis.legend(fontsize=8)
    axes[0].set_title(f'Source validation trial {validation_ids[0]}: same-bin offline predictions')
    save(figure, 'predictions')
    Path('reports/classical_05.json').write_bytes((classical_path / 'results.json').read_bytes())
    Path('reports/sequence_06.json').write_bytes((sequence_path / 'results.json').read_bytes())
    lines = [
        '# Exploratory population and velocity benchmarks', '',
        header.replace('\n', '  \n'), '',
        'Hypothesis: neural observations may predict held-out-trial hand velocity better than training-only baselines. No architecture superiority was presumed.', '',
        'Source trial identities are immutable in `split_manifest.json`. Inner training/validation are 60/15 trials; fitted preprocessing and selection exclude all 25 source validation trials. Final models refit on 75 training trials. Published benchmark test remains unacquired.', '',
        'Counts tensor: 100 × 70 × 107; velocity: 100 × 70 × 2 in m/s. No missing-window exclusions. Standardization fits training only. Predictions use current and, for temporal models, past bins and become available at each bin right edge. No future smoothing or lag optimization. The go-time baseline also receives recorded event timing.', '',
        '| Classical model | Velocity MSE (m²/s²) |', '| --- | ---: |',
    ]
    for name in names:
        lines.append(f"| {name} | {classical['metrics'][name]['mse_m2_s2']:.8f} |")
    lines.extend(['', '| Sequence model | Mean across 3 seeds | Seed range |', '| --- | ---: | --- |'])
    for name, seeds in seed_results.items():
        lines.append(f'| {name} | {np.mean(seeds):.8f} | {min(seeds):.8f}–{max(seeds):.8f} |')
    lines.extend([
        '', f"PCA selected {classical['geometry']['pca']['selected_dimension']} components by inner reconstruction loss; FA selected {classical['geometry']['fa']['selected_dimension']} by inner Gaussian likelihood. Reconstruction loss often prefers the largest candidate; this is not a claim of intrinsic neural dimensionality. The two family scores are not directly comparable.", '',
        'Kalman uses supervised velocity state transitions within trials, regularized observation/process covariance, and independent initial priors per trial. Covariance floor is 1e-5 in corresponding squared units; transition stability is not enforced. The neural state-space baseline is a stable diagonal exponential recurrence with fixed 20 ms steps and learned input/output maps, not a Mamba or foundation model.', '',
        'Deep models use a common Adam optimizer, full-trial batches, 20-epoch cap, inner-only epoch selection, and three seeds. Parameter counts differ. Saved checkpoints restore identical predictions including saved normalization. No GPU run was performed.', '',
        'Whole-trial bootstrap assumes independent curated trials; seed spread describes initialization only. No significance or corrected multiple-model comparison is claimed. There is one subject/session, unequal conditions, no cross-session or cross-subject conclusion. Source validation has been viewed and is now exploratory, not a final untouched test. Latent ridge inherits the raw-ridge alpha rather than separate tuning.', '',
        'All numerical results arise from the checksum-verified real NWB. Dataset: Churchland and Kaufman (2022), [DANDI 000140 v0.220113.0408](https://doi.org/10.48324/dandi.000140/0.220113.0408), CC-BY-4.0. Established [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), [FA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FactorAnalysis.html), and [ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) implementations are used.', '',
        'Next experiment: establish a justified longitudinal feature policy and coverage assumption before interpreting adaptation; run fixed held-out protocols on standard Maze and compare temporal models under matched parameter/data/compute budgets.', '',
        '## Figures', '',
    ])
    lines.extend(['- [' + Path(path).name + '](figures/' + Path(path).name + ')' for path in figure_paths])
    Path('reports/benchmarks.md').write_text('\n'.join(lines) + '\n')
    return figure_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classical', default='data/processed/classical_05')
    parser.add_argument('--sequence', default='data/processed/sequence_06')
    arguments = parser.parse_args()
    print('\n'.join(render(arguments.classical, arguments.sequence)))


if __name__ == '__main__':
    main()
