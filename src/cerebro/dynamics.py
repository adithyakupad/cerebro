"""Training-only latent AR(1), evaluated as an offline one-step forecast."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from cerebro.benchmark import array_digest
from cerebro.population import fit_decoder


def transition_rows(latents):
    latents = np.asarray(latents, dtype=float)
    if latents.ndim != 3 or latents.shape[1] < 2 or not np.all(np.isfinite(latents)):
        raise ValueError('Finite trials × at least two bins × latent coordinates required')
    dimension = latents.shape[-1]
    previous = latents[:, :-1, :].reshape(-1, dimension)
    following = latents[:, 1:, :].reshape(-1, dimension)
    return previous, following


def validate_bin_clock(right_seconds, bin_width):
    times = np.asarray(right_seconds, dtype=float)
    if times.ndim != 2 or times.shape[1] < 2 or not np.isfinite(times).all():
        raise ValueError('Finite trial-local bin timestamps required')
    if bin_width != .02:
        raise ValueError('This dynamics protocol requires 20 ms bins')
    steps = np.diff(times, axis=1)
    if not np.allclose(steps, bin_width, atol=1e-9, rtol=0):
        raise ValueError('Trial-local timestamps disagree with bin width')


def run(root='data/processed/classical_05', output='data/processed/dynamics_10'):
    root = Path(root)
    report = json.loads((root / 'results.json').read_text())
    with np.load(root / 'arrays.npz', allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    for name, metadata in report['arrays'].items():
        if array_digest(arrays[name]) != metadata['sha256']:
            raise ValueError('Classical array lineage mismatch')
    bin_width = report['config']['bin_width_seconds']
    validate_bin_clock(arrays['bin_right_seconds'], bin_width)
    counts = arrays['counts']
    normalized = (counts - arrays['scaler_mean']) / arrays['scaler_scale']
    centered = normalized - arrays['pca_mean']
    latents = centered @ arrays['pca_components'].T
    train_mask = np.isin(arrays['trial_ids'], report['splits']['source_training'])
    validation_mask = np.isin(arrays['trial_ids'], report['splits']['source_validation'])
    previous, following = transition_rows(latents[train_mask])
    validation_previous, validation_following = transition_rows(latents[validation_mask])
    model = fit_decoder(previous, following, alpha=1.)
    predictions = {'ar1': model.predict(validation_previous), 'persistence': validation_previous}
    training_mean = following.mean(axis=0)
    predictions['training_mean'] = np.broadcast_to(training_mean, validation_following.shape)
    generator = np.random.default_rng(10)
    shuffled = latents[train_mask].copy()
    for index in range(len(shuffled)):
        shuffled[index] = shuffled[index, generator.permutation(shuffled.shape[1])]
    null_previous, null_following = transition_rows(shuffled)
    null_model = fit_decoder(null_previous, null_following, alpha=1.)
    predictions['within_trial_permutation_training_control'] = null_model.predict(validation_previous)
    metrics = {}
    shape = latents[validation_mask, 1:].shape
    for name, prediction in predictions.items():
        errors = prediction - validation_following
        squared_errors = (errors ** 2).reshape(shape)
        losses = squared_errors.mean(axis=(1, 2))
        metrics[name] = {'mean_trial_mse_latent2': float(losses.mean()), 'per_trial_mse_latent2': losses.tolist()}
    eigenvalues = np.linalg.eigvals(model.coef_)
    result = {
        'schema_version': 1,
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
        'hypothesis': 'Past training-fitted latent coordinates may improve one-bin neural forecasts over persistence, mean and time-permuted fitting controls.',
        'source_classical_report_sha256': hashlib.sha256((root / 'results.json').read_bytes()).hexdigest(),
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'splits': report['splits'], 'bin_width_seconds': bin_width,
        'latent_shape': list(latents.shape), 'metrics': metrics,
        'training_transition_rows': len(previous), 'validation_transition_rows': len(validation_previous),
        'training_transition_spectral_radius': float(np.max(np.abs(eigenvalues))),
        'information_policy': 'One-step teacher-forced forecast from actual preceding neural bin, trial boundaries excluded. PCA and AR fit the recorded source-training partition; source-validation predictions are report only. Fixed ridge1; no test selection.',
        'limitations': ['One session; latent coordinates have arbitrary standardized-count units', 'No multi-step stability or physiological dynamical-mechanism claim', 'Time-permuted training control is altered real observations, explicitly not an observed chronological recording', 'Source validation is exploratory, separate published test untouched'],
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'parameters.npz', transition_matrix=model.coef_, offset=model.intercept_)
    (output / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    Path('reports/dynamics_10.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classical', default='data/processed/classical_05')
    parser.add_argument('--output', default='data/processed/dynamics_10')
    arguments = parser.parse_args()
    result = run(arguments.classical, arguments.output)
    print(json.dumps(result['metrics'], indent=2))


if __name__ == '__main__':
    main()
