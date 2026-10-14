"""Trial-disjoint exploratory PCA/FA and offline velocity decoder benchmark."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.linalg import cholesky, solve_triangular
from sklearn.preprocessing import StandardScaler

from cerebro.dataset import verify_asset
from cerebro.sense import load_recording, bin_spikes, align_behavior
from cerebro.population import fit_population, reconstruction, fit_decoder
from cerebro.kalman import fit_kalman, predict_kalman


def array_digest(values):
    values = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(values.dtype).encode())
    digest.update(str(values.shape).encode())
    digest.update(values.tobytes())
    return digest.hexdigest()


def gaussian_log_likelihood(model, observations):
    """Gaussian FA score using Cholesky, avoiding local NumPy slogdet warnings."""
    covariance = model.get_covariance()
    factor = cholesky(covariance, lower=True)
    centered = observations - model.mean_
    whitened = solve_triangular(factor, centered.T, lower=True)
    squared_distance = np.sum(whitened ** 2, axis=0)
    log_determinant = 2 * np.sum(np.log(np.diag(factor)))
    normalizer = observations.shape[1] * np.log(2 * np.pi)
    log_density = -.5 * (normalizer + log_determinant + squared_distance)
    return float(np.mean(log_density))


def prepare(recording, config):
    """Complete event windows; retain source training/validation and held-in IDs."""
    width = float(config['bin_width_seconds'])
    duration = config['post_seconds'] - config['pre_seconds']
    if not np.all(np.isfinite([width, duration])) or width <= 0 or duration <= 0:
        raise ValueError('Window and bin width require positive finite seconds')
    bin_number = int(round(duration / width))
    if width <= 0 or bin_number <= 0 or not np.isclose(bin_number * width, duration):
        raise ValueError('Window must contain complete positive-width bins')
    units = recording.units.loc[recording.units.heldout == False]
    if len(units) == 0 or config['neural_unit_policy'] != 'heldin_only':
        raise ValueError('This benchmark requires held-in source units')
    behavior = recording.behavior[config['behavior']]
    if behavior.unit != 'm/s':
        raise ValueError('Velocity benchmark requires physical m/s metadata')
    tensors = []
    velocities = []
    identities = []
    splits = []
    timestamps = []
    exclusions = []
    for trial_id, trial in recording.trials.iterrows():
        split = str(trial['split'])
        if split not in ('train', 'val'):
            continue
        event = float(trial[config['event']])
        start = event + config['pre_seconds']
        stop = event + config['post_seconds']
        if not np.isfinite(event) or start < trial.start_time or stop > trial.stop_time:
            exclusions.append({'trial_id': int(trial_id), 'reason': 'event/window'})
            continue
        counts = bin_spikes(
            units.spike_times, [[start, stop]], units.index, [trial_id],
            units.obs_intervals, bin_width=width,
        )
        velocity, valid_behavior = align_behavior(
            behavior, counts, max_gap=config['behavior_max_gap_seconds'],
        )
        complete = len(counts.left) == bin_number
        covered = np.all(counts.valid) and np.all(valid_behavior)
        if not complete or not covered:
            exclusions.append({'trial_id': int(trial_id), 'reason': 'coverage'})
            continue
        original_spike_totals = np.zeros(len(units), dtype=np.int64)
        for column, spikes in enumerate(units.spike_times):
            within_window = (spikes >= counts.left[0]) & (spikes < counts.right[-1])
            original_spike_totals[column] = np.sum(within_window)
        if not np.array_equal(counts.values.sum(axis=0), original_spike_totals):
            raise ValueError('Per-trial spike conservation failed')
        tensors.append(counts.values)
        velocities.append(velocity)
        timestamps.append(counts.right)
        identities.append(int(trial_id))
        splits.append(split)
    if not tensors:
        raise ValueError('No complete observations')
    return {
        'counts': np.stack(tensors), 'velocity': np.stack(velocities),
        'right_seconds': np.stack(timestamps), 'trial_ids': np.asarray(identities),
        'splits': np.asarray(splits), 'unit_ids': units.index.to_numpy(),
        'exclusions': exclusions,
    }


def split_manifest(data, asset, config):
    """Source validation never enters inner selection; immutable identity record."""
    train_ids = data['trial_ids'][data['splits'] == 'train']
    validation_ids = data['trial_ids'][data['splits'] == 'val']
    number = config['inner_validation_trials']
    if number < 1 or number >= len(train_ids) or len(validation_ids) < 2:
        raise ValueError('Insufficient independent trials for benchmark splits')
    generator = np.random.default_rng(config['seed'])
    shuffled_ids = generator.permutation(train_ids)
    inner_validation = np.sort(shuffled_ids[:number])
    inner_training = np.sort(shuffled_ids[number:])
    return {
        'schema_version': 1, 'asset_sha256': asset['sha256'],
        'config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        'inner_training': inner_training.tolist(),
        'inner_validation': inner_validation.tolist(),
        'source_training': train_ids.tolist(),
        'source_validation': validation_ids.tolist(),
        'heldout_test': 'not acquired or accessed',
        'unit_ids': data['unit_ids'].tolist(),
    }


def save_immutable(path, content):
    encoded = json.dumps(content, indent=2, sort_keys=True) + '\n'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Existing split manifest differs; use a new experiment identity')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(encoded)


def trial_metrics(target, prediction):
    if target.shape != prediction.shape or target.ndim != 3:
        raise ValueError('Metrics require matching trials × bins × coordinates')
    if not np.all(np.isfinite(target)) or not np.all(np.isfinite(prediction)):
        raise ValueError('Missing values must be excluded before evaluation')
    errors = target - prediction
    trial_mse = np.mean(errors ** 2, axis=(1, 2))
    flattened_target = target.reshape(-1, target.shape[-1])
    flattened_error = errors.reshape(-1, errors.shape[-1])
    target_mean = flattened_target.mean(axis=0)
    centered_target = flattened_target - target_mean
    sums_error = np.sum(flattened_error ** 2, axis=0)
    sums_total = np.sum(centered_target ** 2, axis=0)
    r_squared = np.full(sums_total.shape, np.nan)
    variable = sums_total > 0
    r_squared[variable] = 1 - sums_error[variable] / sums_total[variable]
    return trial_mse, r_squared


def restore_prediction(parameters, kind, counts):
    """Restore numerical checkpoints without pickle; caller preserves unit order."""
    counts = np.asarray(counts, dtype=float)
    if counts.ndim != 3 or not np.all(np.isfinite(counts)) or np.any(counts < 0):
        raise ValueError('Finite nonnegative trial × bin × unit counts required')
    if counts.shape[-1] != len(parameters['scaler_mean']):
        raise ValueError('Checkpoint unit dimensions differ')
    normalized = (counts - parameters['scaler_mean']) / parameters['scaler_scale']
    target_shape = counts.shape[:2] + (2,)
    if kind == 'mean':
        return np.broadcast_to(parameters['mean_baseline'], target_shape).copy()
    if kind == 'go_time_template':
        return np.broadcast_to(parameters['time_template_baseline'], target_shape).copy()
    if kind == 'kalman':
        model = {}
        for name, value in parameters.items():
            if name.startswith('kalman_'):
                model[name.removeprefix('kalman_')] = value
        return predict_kalman(model, normalized)
    features = normalized
    if kind in ('pca_ridge', 'fa_ridge'):
        family = kind.split('_')[0]
        components = parameters[family + '_components']
        centered = normalized - parameters[family + '_mean']
        if family == 'pca':
            features = centered @ components.T
        else:
            noise_variance = parameters['fa_noise_variance']
            weighted_components = components / noise_variance
            posterior_precision = np.eye(len(components)) + weighted_components @ components.T
            projected = centered @ weighted_components.T
            features = np.linalg.solve(posterior_precision, projected.reshape(-1, len(components)).T).T
            features = features.reshape(counts.shape[:2] + (len(components),))
    prediction = features @ parameters[kind + '_coef'].T
    prediction = prediction + parameters[kind + '_intercept']
    return prediction


def run(manifest_path, config_path, output):
    asset = json.loads(Path(manifest_path).read_text())
    config = json.loads(Path(config_path).read_text())
    verify_asset(asset['local_path'], asset)
    recording = load_recording(asset['local_path'])
    data = prepare(recording, config)
    splits = split_manifest(data, asset, config)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_immutable(output / 'split_manifest.json', splits)
    counts = data['counts'].astype(float)
    target = data['velocity']
    ids = data['trial_ids']
    inner_train = np.isin(ids, splits['inner_training'])
    inner_val = np.isin(ids, splits['inner_validation'])
    source_train = data['splits'] == 'train'
    source_val = data['splits'] == 'val'
    features_number = counts.shape[-1]
    scaler = StandardScaler()
    inner_x = counts[inner_train].reshape(-1, features_number)
    inner_z = scaler.fit_transform(inner_x)
    inner_validation_x = counts[inner_val].reshape(-1, features_number)
    inner_validation_z = scaler.transform(inner_validation_x)
    geometry = {}
    selected_dimensions = {}
    for kind in ('pca', 'fa'):
        scores = []
        for dimension in config['dimensions']:
            model = fit_population(inner_z, dimension, kind=kind, seed=config['seed'])
            if kind == 'pca':
                recovered = reconstruction(model, inner_validation_z)
                score = float(np.mean((inner_validation_z - recovered) ** 2))
            else:
                score = -gaussian_log_likelihood(model, inner_validation_z)
            scores.append({'dimension': dimension, 'inner_validation_loss': score})
        selected = min(scores, key=lambda entry: entry['inner_validation_loss'])['dimension']
        selected_dimensions[kind] = selected
        geometry[kind] = {'candidates': scores, 'selected_dimension': selected}
    inner_y = target[inner_train].reshape(-1, target.shape[-1])
    inner_validation_y = target[inner_val].reshape(-1, target.shape[-1])
    alpha_scores = []
    for alpha in config['ridge_alphas']:
        decoder = fit_decoder(inner_z, inner_y, alpha=alpha)
        prediction = decoder.predict(inner_validation_z)
        loss = float(np.mean((inner_validation_y - prediction) ** 2))
        alpha_scores.append({'alpha': alpha, 'inner_validation_mse_m2_s2': loss})
    selected_alpha = min(alpha_scores, key=lambda entry: entry['inner_validation_mse_m2_s2'])['alpha']
    kalman_candidates = []
    for alpha in config['ridge_alphas']:
        model = fit_kalman(
            inner_z.reshape(len(counts[inner_train]), counts.shape[1], features_number),
            target[inner_train], ridge_alpha=alpha,
        )
        kalman_prediction = predict_kalman(
            model, inner_validation_z.reshape(len(counts[inner_val]), counts.shape[1], features_number),
        )
        kalman_loss = float(np.mean((target[inner_val] - kalman_prediction) ** 2))
        kalman_candidates.append({'alpha': alpha, 'inner_validation_mse_m2_s2': kalman_loss})
    kalman_alpha = min(kalman_candidates, key=lambda entry: entry['inner_validation_mse_m2_s2'])['alpha']
    scaler = StandardScaler()
    training_x = counts[source_train].reshape(-1, features_number)
    training_z = scaler.fit_transform(training_x)
    validation_x = counts[source_val].reshape(-1, features_number)
    validation_z = scaler.transform(validation_x)
    training_y = target[source_train].reshape(-1, target.shape[-1])
    validation_y = target[source_val]
    predictions = {}
    training_mean = training_y.mean(axis=0)
    predictions['mean'] = np.broadcast_to(training_mean, validation_y.shape).copy()
    temporal_mean = target[source_train].mean(axis=0)
    predictions['go_time_template'] = np.broadcast_to(temporal_mean, validation_y.shape).copy()
    decoder_parameters = {}
    for name, alpha in [('linear', None), ('ridge', selected_alpha)]:
        decoder = fit_decoder(training_z, training_y, alpha=alpha)
        predicted_flat = decoder.predict(validation_z)
        predictions[name] = predicted_flat.reshape(validation_y.shape)
        decoder_parameters[name + '_coef'] = decoder.coef_
        decoder_parameters[name + '_intercept'] = decoder.intercept_
    fitted_arrays = {
        'scaler_mean': scaler.mean_, 'scaler_scale': scaler.scale_,
        'trial_ids': ids, 'unit_ids': data['unit_ids'], 'counts': data['counts'],
        'velocity_m_s': target, 'bin_right_seconds': data['right_seconds'],
        'mean_baseline': training_mean, 'time_template_baseline': temporal_mean,
        **decoder_parameters,
    }
    kalman_model = fit_kalman(
        training_z.reshape(np.sum(source_train), counts.shape[1], features_number),
        target[source_train], ridge_alpha=kalman_alpha,
    )
    predictions['kalman'] = predict_kalman(
        kalman_model, validation_z.reshape(len(validation_y), counts.shape[1], features_number),
    )
    for name, value in kalman_model.items():
        fitted_arrays['kalman_' + name] = value
    for kind in ('pca', 'fa'):
        dimension = selected_dimensions[kind]
        model = fit_population(training_z, dimension, kind=kind, seed=config['seed'])
        training_latents = model.transform(training_z)
        validation_latents = model.transform(validation_z)
        decoder = fit_decoder(training_latents, training_y, alpha=selected_alpha)
        predicted_flat = decoder.predict(validation_latents)
        predictions[kind + '_ridge'] = predicted_flat.reshape(validation_y.shape)
        fitted_arrays[kind + '_ridge_coef'] = decoder.coef_
        fitted_arrays[kind + '_ridge_intercept'] = decoder.intercept_
        fitted_arrays[kind + '_components'] = model.components_
        fitted_arrays[kind + '_mean'] = model.mean_
        fitted_arrays[kind + '_validation_latents'] = validation_latents.reshape(
            len(validation_y), counts.shape[1], dimension,
        )
        if kind == 'pca':
            geometry[kind]['training_explained_variance_ratio'] = model.explained_variance_ratio_.tolist()
        else:
            geometry[kind]['source_validation_log_likelihood'] = gaussian_log_likelihood(model, validation_z)
            fitted_arrays['fa_noise_variance'] = model.noise_variance_
    metrics = {}
    generator = np.random.default_rng(config['seed'])
    trial_number = len(validation_y)
    resample_indices = generator.integers(trial_number, size=(config['bootstrap_draws'], trial_number))
    for name, prediction in predictions.items():
        restored_prediction = restore_prediction(fitted_arrays, name, counts[source_val])
        if not np.allclose(restored_prediction, prediction, rtol=1e-10, atol=1e-10):
            raise ValueError('Numerical checkpoint restoration changed predictions')
        trial_mse, r_squared = trial_metrics(validation_y, prediction)
        bootstrap_means = trial_mse[resample_indices].mean(axis=1)
        interval = np.quantile(bootstrap_means, [.025, .975])
        metrics[name] = {
            'mse_m2_s2': float(trial_mse.mean()), 'trial_mse_m2_s2': trial_mse.tolist(),
            'trial_bootstrap_mse_interval': interval.tolist(),
            'pooled_r2_by_coordinate': [float(value) if np.isfinite(value) else None for value in r_squared],
            'checkpoint_restoration_passed': True,
        }
        fitted_arrays[name + '_prediction_m_s'] = prediction
    revisions = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    source_hashes = {}
    for filename in ('benchmark.py', 'population.py', 'sense.py', 'kalman.py'):
        path = Path(__file__).parent / filename
        source_hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        'schema_version': 1, 'hypothesis': 'Neural observations predict held-out-trial hand velocity better than fixed training-only baselines; an exploratory software benchmark, not a mechanistic claim.',
        'config': config, 'asset': asset, 'recording': recording.metadata,
        'splits': splits, 'exclusions': data['exclusions'],
        'counts_shape': list(counts.shape), 'target_shape': list(target.shape),
        'prediction_target': 'same-bin native mean hand velocity in m/s',
        'information_policy': 'Offline contemporaneous bins; outputs available only at bin right edge. Go-time template has recorded go-cue timing. No smoothing or lag search.',
        'selection_policy': f"{len(splits['inner_training'])}/{len(splits['inner_validation'])} inner training/validation source trials; refit on all source train after selection; source val used only for final exploratory reporting. Published test file untouched.",
        'geometry': geometry, 'ridge_selection': alpha_scores, 'selected_ridge_alpha': selected_alpha,
        'metrics': metrics, 'evaluation_trial_ids': ids[source_val].tolist(),
        'kalman_selection': kalman_candidates, 'selected_kalman_alpha': kalman_alpha,
        'kalman_covariance_floor': 1e-5,
        'uncertainty': 'Whole-trial percentile bootstrap; assumes independent trials from this curated session. No claim of calibrated population uncertainty or model significance.',
        'limitations': ['One subject and session', 'No cross-session unit mapping', 'Condition imbalance and only 25 evaluation trials', 'PCA loss is reconstruction, FA loss is negative Gaussian likelihood; scores are not comparable across families', 'Ridge alpha for latent models is inherited from raw ridge, not optimized separately', 'Source validation is exploratory evaluation, not untouched benchmark test'],
        'git_revision': revisions, 'source_sha256': source_hashes,
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
        'environment': {name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'scikit-learn', 'pynwb')},
        'arrays': {name: {'shape': list(values.shape), 'sha256': array_digest(values)} for name, values in fitted_arrays.items()},
    }
    np.savez_compressed(output / 'arrays.npz', **fitted_arrays)
    (output / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--config', default='configs/classical_05.json')
    parser.add_argument('--output', default='data/processed/classical_05')
    args = parser.parse_args()
    report = run(args.manifest, args.config, args.output)
    print(json.dumps({'counts_shape': report['counts_shape'], 'metrics': report['metrics']}, indent=2))


if __name__ == '__main__':
    main()
