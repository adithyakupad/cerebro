"""Trial-local, training-only PCA/FA observation models and latent AR diagnostics."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import warnings

import numpy as np
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest
from cerebro.calibration_mechanisms import development_split
from cerebro.link import align_channel_keys, load_link
from cerebro.longitudinal import block_interval, flatten, validate_chronology
from cerebro.population import covariance_similarity, fit_decoder, fit_population, principal_angles


def trial_transitions(sequences, horizon=1):
    """Return aligned rows without bridging variable-length trial boundaries."""
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError('Horizon must be a positive integer')
    previous = []
    following = []
    for sequence in sequences:
        values = np.asarray(sequence, dtype=float)
        if values.ndim != 2 or len(values) <= horizon or not np.isfinite(values).all():
            raise ValueError('Finite trial arrays longer than the forecast horizon required')
        previous.append(values[:-horizon])
        following.append(values[horizon:])
    if not previous:
        raise ValueError('At least one trial required')
    return np.concatenate(previous), np.concatenate(following)


def fitted_source(trials, dimension=6, kind='pca', scaler=None, order=None, seed=23023):
    """Fit on supplied trials only; callers own immutable split restrictions."""
    counts = flatten(trials, 'counts', order)
    if scaler is None:
        scaler = StandardScaler().fit(counts)
    normalized = scaler.transform(counts)
    with warnings.catch_warnings(record=True) as fitting_warnings:
        warnings.simplefilter('always')
        population = fit_population(normalized, dimension, kind=kind, seed=seed)
    lengths = [len(trial['counts']) for trial in trials]
    boundaries = np.cumsum(lengths)[:-1]
    coordinates = population.transform(normalized)
    sequences = np.split(coordinates, boundaries)
    previous, following = trial_transitions(sequences)
    transition = fit_decoder(previous, following, alpha=1.)
    generator = np.random.default_rng(seed)
    permuted = []
    for sequence in sequences:
        indices = generator.permutation(len(sequence))
        permuted.append(sequence[indices])
    null_previous, null_following = trial_transitions(permuted)
    null_transition = fit_decoder(null_previous, null_following, alpha=1.)
    neural_sequences = np.split(normalized, boundaries)
    neural_previous, neural_following = trial_transitions(neural_sequences)
    channel_models = []
    for channel in range(counts.shape[1]):
        features = neural_previous[:, channel:channel + 1]
        targets = neural_following[:, channel:channel + 1]
        channel_models.append(fit_decoder(features, targets, alpha=1.))
    behavior = flatten(trials, 'position')
    behavior_decoder = fit_decoder(coordinates, behavior, alpha=1000.)
    condition_rows = {}
    for trial, normalized_trial in zip(trials, neural_sequences):
        condition = tuple(trial['target'].tolist())
        condition_rows.setdefault(condition, []).append(normalized_trial)
    condition_means = {}
    for condition, rows in condition_rows.items():
        condition_means[condition] = np.concatenate(rows).mean(axis=0)
    model = {'scaler': scaler, 'population': population, 'transition': transition,
             'null_transition': null_transition, 'channel_models': channel_models,
             'behavior_decoder': behavior_decoder, 'training_mean': normalized.mean(axis=0),
             'latent_mean': following.mean(axis=0), 'kind': kind, 'dimension': dimension,
             'condition_means': condition_means,
             'fitting_warnings': sorted({str(row.message) for row in fitting_warnings}),
             'fitting_warning_count': len(fitting_warnings)}
    return model


def reconstructed(model, coordinates):
    population = model['population']
    centered = coordinates @ population.components_
    return centered + population.mean_


def iterate_transition(initial, transition, horizon):
    state = initial.copy()
    for _ in range(horizon):
        state = transition.predict(state)
    return state


def projection_errors(model, trials, order=None, reference_scaler=None, horizon=1):
    """Calibration-only mismatch: trial-equal neural AR forecast MSE, no labels."""
    if reference_scaler is None:
        reference_scaler = model['scaler']
    losses = []
    for trial in trials:
        counts = trial['counts']
        if order is not None:
            counts = counts[:, order]
        normalized = model['scaler'].transform(counts)
        coordinates = model['population'].transform(normalized)
        trial_transitions([coordinates], horizon)
        predicted_coordinates = iterate_transition(coordinates[:-horizon], model['transition'], horizon)
        predicted_normalized = reconstructed(model, predicted_coordinates)
        predicted_counts = model['scaler'].inverse_transform(predicted_normalized)
        predicted_reference = reference_scaler.transform(predicted_counts)
        target_reference = reference_scaler.transform(counts[horizon:])
        errors = predicted_reference - target_reference
        losses.append(float(np.mean(errors ** 2)))
    return np.asarray(losses)


def _metric(values, config):
    values = np.asarray(values)
    interval = block_interval(values, config['bootstrap_draws'], config['bootstrap_block_trials'], config['random_seed'])
    return {'mean_trial': float(values.mean()), 'per_trial': values.tolist(), 'conditional_95_block_interval': interval}


def evaluate(model, trials, reference_scaler, order, config):
    """Offline contemporaneous reconstruction, and causal trial-local forecasts."""
    collected = {}
    likelihood_warnings = []
    unknown_condition_trials = []
    for trial in trials:
        counts = trial['counts'][:, order]
        normalized = model['scaler'].transform(counts)
        reference = reference_scaler.transform(counts)
        coordinates = model['population'].transform(normalized)
        condition = tuple(trial['target'].tolist())
        condition_mean = model['condition_means'].get(condition, model['training_mean'])
        if condition not in model['condition_means']:
            unknown_condition_trials.append(trial['trial_id'])
        reconstructed_normalized = reconstructed(model, coordinates)
        reconstructed_counts = model['scaler'].inverse_transform(reconstructed_normalized)
        reconstructed_reference = reference_scaler.transform(reconstructed_counts)
        collected.setdefault('reconstruction_neural_mse', []).append(float(np.mean((reconstructed_reference - reference) ** 2)))
        behavior_prediction = model['behavior_decoder'].predict(coordinates)
        collected.setdefault('offline_behavior_mse_flexion2', []).append(float(np.mean((behavior_prediction - trial['position']) ** 2)))
        if model['kind'] == 'fa':
            with warnings.catch_warnings(record=True) as score_warnings:
                warnings.simplefilter('always')
                log_likelihood = model['population'].score_samples(normalized)
            likelihood_warnings.extend(str(row.message) for row in score_warnings)
            if not np.isfinite(log_likelihood).all():
                raise ValueError('FA Gaussian likelihood must be finite before reporting')
            scale_jacobian = np.log(model['scaler'].scale_ / reference_scaler.scale_).sum()
            reference_log_likelihood = log_likelihood - scale_jacobian
            collected.setdefault('fa_loglikelihood_reference_per_bin', []).append(float(reference_log_likelihood.mean()))
        for horizon in config['forecast_horizons_bins']:
            trial_transitions([coordinates], horizon)
            initial = coordinates[:-horizon]
            target_coordinates = coordinates[horizon:]
            forecast_coordinates = iterate_transition(initial, model['transition'], horizon)
            permuted_coordinates = iterate_transition(initial, model['null_transition'], horizon)
            neural_forecasts = {
                'latent_ar': reconstructed(model, forecast_coordinates),
                'permuted_training_ar': reconstructed(model, permuted_coordinates),
                'neural_persistence': normalized[:-horizon],
                'latent_persistence': reconstructed(model, initial),
                'command_condition_mean': np.broadcast_to(condition_mean, normalized[horizon:].shape),
                'training_mean': np.broadcast_to(model['training_mean'], normalized[horizon:].shape)}
            channel_forecast = normalized[:-horizon].copy()
            for _ in range(horizon):
                for channel, channel_model in enumerate(model['channel_models']):
                    channel_prediction = channel_model.predict(channel_forecast[:, channel:channel + 1])
                    channel_forecast[:, channel] = channel_prediction.reshape(-1)
            neural_forecasts['independent_channel_ar'] = channel_forecast
            for name, prediction in neural_forecasts.items():
                predicted_counts = model['scaler'].inverse_transform(prediction)
                predicted_reference = reference_scaler.transform(predicted_counts)
                residual = predicted_reference - reference[horizon:]
                key = f'h{horizon}_{name}_neural_mse'
                collected.setdefault(key, []).append(float(np.mean(residual ** 2)))
            latent_residual = forecast_coordinates - target_coordinates
            collected.setdefault(f'h{horizon}_latent_ar_mse', []).append(float(np.mean(latent_residual ** 2)))
    metrics = {name: _metric(values, config) for name, values in collected.items()}
    for horizon in config['forecast_horizons_bins']:
        ar = np.asarray(collected[f'h{horizon}_latent_ar_neural_mse'])
        for control in ('neural_persistence', 'training_mean', 'permuted_training_ar'):
            control_losses = np.asarray(collected[f'h{horizon}_{control}_neural_mse'])
            difference = ar - control_losses
            metrics[f'h{horizon}_paired_ar_minus_{control}'] = _metric(difference, config)
    metrics['command_control_unknown_trial_ids'] = unknown_condition_trials
    metrics['fa_scoring_warnings'] = sorted(set(likelihood_warnings))
    metrics['fa_scoring_warning_count'] = len(likelihood_warnings)
    return metrics


def rotation_error(model, counts, order=None):
    """Orthogonal latent relabeling must preserve reconstructed AR forecasts."""
    if order is not None:
        counts = counts[:, order]
    coordinates = model['population'].transform(model['scaler'].transform(counts))
    generator = np.random.default_rng(23023)
    rotation, _ = np.linalg.qr(generator.normal(size=(model['dimension'], model['dimension'])))
    rotated = coordinates[:-1] @ rotation
    matrix = model['transition'].coef_.T
    rotated_matrix = rotation.T @ matrix @ rotation
    rotated_offset = model['transition'].intercept_ @ rotation
    rotated_prediction = rotated @ rotated_matrix + rotated_offset
    restored_prediction = rotated_prediction @ rotation.T
    original_prediction = model['transition'].predict(coordinates[:-1])
    coordinate_error = np.max(np.abs(restored_prediction - original_prediction))
    components = model['population'].components_
    rotated_components = rotation.T @ components
    rotated_reconstruction = rotated_prediction @ rotated_components
    original_reconstruction = original_prediction @ components
    reconstruction_error = np.max(np.abs(rotated_reconstruction - original_reconstruction))
    angles = principal_angles(components.T, rotated_components.T)
    geometry_error = np.max(np.abs(angles))
    error = max(coordinate_error, reconstruction_error, geometry_error)
    return float(error)


def phase_trajectories(trials, scaler, order=None):
    """Acausal descriptive ten-quantile condition means, never forecast input."""
    grouped = {}
    for trial in trials:
        counts = trial['counts']
        if order is not None:
            counts = counts[:, order]
        normalized = scaler.transform(counts)
        phase_parts = np.array_split(normalized, 10)
        if any(len(part) == 0 for part in phase_parts):
            raise ValueError('Ten phase bins require at least ten samples per trial')
        phase_mean = np.stack([part.mean(axis=0) for part in phase_parts])
        condition = tuple(trial['target'].tolist())
        grouped.setdefault(condition, []).append(phase_mean)
    return grouped


def matched_conditions(source_trials, pool_trials, evaluation_trials, scaler, order):
    source_grouped = phase_trajectories(source_trials, scaler)
    pool_grouped = phase_trajectories(pool_trials, scaler, order)
    common = sorted(set(source_grouped) & set(pool_grouped))
    common = [key for key in common if min(len(source_grouped[key]), len(pool_grouped[key])) >= 2]
    similarities = []
    repetition_counts = []
    for key in common:
        source_mean = np.mean(source_grouped[key], axis=0)
        pool_mean = np.mean(pool_grouped[key], axis=0)
        source_centered = source_mean - source_mean.mean(axis=0)
        pool_centered = pool_mean - pool_mean.mean(axis=0)
        denominator = np.linalg.norm(source_centered) * np.linalg.norm(pool_centered)
        similarity = float(np.sum(source_centered * pool_centered) / denominator) if denominator else None
        similarities.append(similarity)
        repetition_counts.append({'condition': list(key), 'source_trials': len(source_grouped[key]), 'pool_trials': len(pool_grouped[key])})
    condition_means = {}
    for key, trajectories in pool_grouped.items():
        trial_means = [trajectory.mean(axis=0) for trajectory in trajectories]
        condition_means[key] = np.mean(trial_means, axis=0)
    losses = []
    ids = []
    for trial in evaluation_trials:
        key = tuple(trial['target'].tolist())
        training_mean = flatten(pool_trials, 'counts', order).mean(axis=0)
        fallback = scaler.transform(training_mean[None])[0]
        normalized = scaler.transform(trial['counts'][:, order])
        errors = normalized - condition_means.get(key, fallback)
        losses.append(float(np.mean(errors ** 2)))
        ids.append(trial['trial_id'])
    return {'conditions_with_two_repetitions_each': repetition_counts,
            'phase_trajectory_centered_cosine': similarities,
            'command_condition_mean_control_trial_ids': ids,
            'command_condition_mean_control_unknown_trial_ids': [trial['trial_id'] for trial in evaluation_trials if tuple(trial['target'].tolist()) not in condition_means],
            'command_condition_mean_control_neural_mse': losses,
            'information': 'Pool neural samples and commanded labels; control additionally reads evaluation command labels, no evaluation neural fit or behavior positions.'}


def parameter_arrays(model):
    arrays = {'scaler_mean': model['scaler'].mean_, 'scaler_scale': model['scaler'].scale_,
              'components': model['population'].components_, 'population_mean': model['population'].mean_,
              'transition_coef': model['transition'].coef_, 'transition_intercept': model['transition'].intercept_,
              'null_coef': model['null_transition'].coef_, 'null_intercept': model['null_transition'].intercept_,
              'behavior_coef': model['behavior_decoder'].coef_, 'behavior_intercept': model['behavior_decoder'].intercept_}
    arrays['channel_ar_coef'] = np.asarray([row.coef_.reshape(-1)[0] for row in model['channel_models']])
    arrays['channel_ar_intercept'] = np.asarray([row.intercept_.reshape(-1)[0] for row in model['channel_models']])
    arrays['training_mean'] = model['training_mean']
    arrays['condition_keys'] = np.asarray(list(model['condition_means']))
    arrays['condition_means'] = np.asarray(list(model['condition_means'].values()))
    if model['kind'] == 'fa':
        arrays['noise_variance'] = model['population'].noise_variance_
    return arrays


def restore_forecast(parameters, counts, kind, horizon=1):
    """Replay raw-count predictions from saved numerical parameters only."""
    normalized = (counts - parameters['scaler_mean']) / parameters['scaler_scale']
    centered = normalized - parameters['population_mean']
    components = parameters['components']
    if kind == 'pca':
        coordinates = centered @ components.T
    elif kind == 'fa':
        weighted_components = components / parameters['noise_variance']
        posterior_precision = np.eye(len(components)) + weighted_components @ components.T
        posterior_covariance = np.linalg.inv(posterior_precision)
        coordinates = centered @ weighted_components.T @ posterior_covariance
    else:
        raise ValueError('Only PCA/FA checkpoints supported')
    trial_transitions([coordinates], horizon)
    predicted = coordinates[:-horizon]
    for _ in range(horizon):
        predicted = predicted @ parameters['transition_coef'].T + parameters['transition_intercept']
    normalized_prediction = predicted @ components + parameters['population_mean']
    return normalized_prediction * parameters['scaler_scale'] + parameters['scaler_mean']


def temporal_gate(sessions, config):
    """Evaluate the fixed primary temporal hypothesis, never select a model."""
    decisions = []
    generator = np.random.default_rng(config['random_seed'])
    for control in ('neural_persistence', 'training_mean', 'permuted_training_ar'):
        differences = []
        reductions = []
        for session in sessions:
            primary = next(row for row in session['comparisons'] if row['fit'] == 'source' and row['model'] == 'pca' and row['dimension'] == config['primary_dimension'])
            metrics = primary['metrics']
            ar = np.asarray(metrics['h1_latent_ar_neural_mse']['per_trial'])
            baseline = np.asarray(metrics[f'h1_{control}_neural_mse']['per_trial'])
            differences.append(ar - baseline)
            reductions.append(float(1 - ar.mean() / baseline.mean()))
        sampled_means = []
        block_length = config['bootstrap_block_trials']
        for values in differences:
            block_count = int(np.ceil(len(values) / block_length))
            starts = generator.integers(len(values) - block_length + 1, size=(config['bootstrap_draws'], block_count))
            indices = starts[:, :, None] + np.arange(block_length)
            indices = indices.reshape(config['bootstrap_draws'], -1)[:, :len(values)]
            sampled_means.append(values[indices].mean(axis=1))
        equal_date_draws = np.mean(sampled_means, axis=0)
        interval = np.quantile(equal_date_draws, [.025, .975]).tolist()
        practical = np.mean(reductions) >= config['practical_relative_improvement']
        every_date = all(value > 0 for value in reductions)
        passed = bool(practical and every_date and interval[1] < 0)
        decisions.append({'control': control, 'per_date_relative_improvement': reductions,
                          'equal_date_mean_relative_improvement': float(np.mean(reductions)),
                          'equal_date_paired_mse_difference': float(np.mean([values.mean() for values in differences])),
                          'conditional_95_block_interval': interval, 'passed': passed})
    return {'primary': 'source PCA6 latent AR1, horizon1', 'comparisons': decisions,
            'passed': all(row['passed'] for row in decisions)}


def run(config_path='configs/m023_protocol.json', output='data/processed/m023_dynamics'):
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    source_manifest = json.loads(Path(config['source_manifest']).read_text())
    source = load_link(source_manifest)
    source_training = source['trials'][:config['source_training_trials']]
    _, source_stop = validate_chronology({**source, 'trials': source_training})
    source_counts = flatten(source_training, 'counts')
    source_scaler = StandardScaler().fit(source_counts)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    arrays = {}
    source_models = {}
    for kind in config['population_kinds']:
        for dimension in config['population_dimensions']:
            key = f'{kind}_{dimension}'
            model = fitted_source(source_training, dimension, kind, source_scaler, seed=config['random_seed'])
            source_models[key] = model
            for name, values in parameter_arrays(model).items():
                arrays[f'source_{key}_{name}'] = values
    sessions = []
    for manifest_path in config['development_manifests']:
        manifest = json.loads(Path(manifest_path).read_text())
        recording = load_link(manifest)
        pool, evaluation = development_split(recording, config['permitted_trial_rows'], config['allocation_pool_trials'])
        target_start, _ = validate_chronology({**recording, 'trials': pool + evaluation})
        if target_start <= source_stop:
            raise ValueError('Development recording must follow source chronologically')
        if recording['subject_id'] != source['subject_id']:
            raise ValueError('Development requires the same identified subject')
        order = align_channel_keys(source['channel_keys'], recording['channel_keys'])
        pool_counts = flatten(pool, 'counts', order)
        local_scaler = StandardScaler().fit(pool_counts)
        local_covariance = np.cov(source_scaler.transform(pool_counts), rowvar=False)
        source_covariance = np.cov(source_scaler.transform(source_counts), rowvar=False)
        comparisons = []
        for key, source_model in source_models.items():
            kind = source_model['kind']
            dimension = source_model['dimension']
            fitting_options = [('source', source_training, source_scaler, None)]
            fitting_options.extend([(f'local_{budget}', pool[:budget], source_scaler, order) for budget in config['local_training_trials']])
            if dimension == config['primary_dimension']:
                fitting_options.append(('local_45_pool_scaler', pool, local_scaler, order))
            for fit_name, training, scaler, training_order in fitting_options:
                model = source_model if fit_name == 'source' else fitted_source(training, dimension, kind, scaler, training_order, config['random_seed'])
                metrics = evaluate(model, evaluation, source_scaler, order, config)
                identifier = f"{recording['session_id']}_{key}_{fit_name}"
                for name, values in parameter_arrays(model).items():
                    arrays[f'{identifier}_{name}'] = values
                replay_counts = evaluation[0]['counts'][:, order]
                replay = restore_forecast(parameter_arrays(model), replay_counts, kind)
                expected_latents = model['population'].transform(scaler.transform(replay_counts))
                expected_next = model['transition'].predict(expected_latents[:-1])
                expected_counts = scaler.inverse_transform(reconstructed(model, expected_next))
                checkpoint_error = float(np.max(np.abs(replay - expected_counts)))
                if checkpoint_error > 1e-9:
                    raise ValueError('Saved-parameter replay differs from estimator predictions')
                angles = None
                if kind == 'pca':
                    source_basis = source_model['population'].components_.T
                    local_basis = model['population'].components_.T
                    source_basis = source_basis * source_scaler.scale_[:, None]
                    local_basis = local_basis * scaler.scale_[:, None]
                    angles = principal_angles(source_basis, local_basis).tolist()
                comparisons.append({'model': kind, 'dimension': dimension, 'fit': fit_name,
                                    'fitting_trials': len(training), 'metrics': metrics,
                                    'fitting_warnings': model['fitting_warnings'],
                                    'fitting_warning_count': model['fitting_warning_count'],
                                    'raw_count_principal_angles_radians': angles,
                                    'transition_spectral_radius': float(np.max(np.abs(np.linalg.eigvals(model['transition'].coef_)))),
                                    'checkpoint_replay_max_abs_count_error': checkpoint_error,
                                    'rotation_invariance_max_abs_error': rotation_error(model, evaluation[0]['counts'], order)})
        elapsed = {}
        for horizon in config['forecast_horizons_bins']:
            durations = []
            for trial in evaluation:
                durations.append(trial['timestamps'][horizon:] - trial['timestamps'][:-horizon])
            durations = np.concatenate(durations)
            elapsed[str(horizon)] = {'minimum_seconds': float(durations.min()), 'maximum_seconds': float(durations.max()),
                                     'mean_seconds': float(durations.mean()), 'comparison_bins': len(durations)}
        sessions.append({'session_id': recording['session_id'], 'manifest': manifest_path,
                         'verified_sha256': recording['verified_sha256'], 'pool_trial_ids': [trial['trial_id'] for trial in pool],
                         'evaluation_trial_ids': [trial['trial_id'] for trial in evaluation],
                         'pool_bins': len(pool_counts), 'evaluation_bins': len(flatten(evaluation, 'counts', order)),
                         'covariance_frobenius_cosine': covariance_similarity(source_covariance, local_covariance),
                         'forecast_actual_elapsed_clock': elapsed,
                         'condition_matching': matched_conditions(source_training, pool, evaluation, source_scaler, order),
                         'comparisons': comparisons})
    result = {'schema_version': 1, 'config': config,
              'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
              'source_asset_sha256': source['verified_sha256'], 'source_training_trial_ids': [trial['trial_id'] for trial in source_training],
              'independent_subjects': 1, 'development_target_sessions': len(sessions),
              'temporal_gate': temporal_gate(sessions, config),
              'sessions': sessions, 'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in arrays.items()},
              'conventions': ['Native jittered nominal20ms bins; horizon1/5 are sample steps, approximately20/100ms',
                              'Neural MSE in source-standardized count squared units; trials equally weighted',
                              'PCA/FA are static training-only observation models; ridge AR1 is a statistical latent-state forecast, not fitted Kalman process noise',
                              'Behavior probes and observation reconstructions are offline contemporaneous, forecasts use only past neural bins',
                              'Conditional moving-five-trial block intervals do not establish between-subject uncertainty',
                              'Phase quantile trajectories are acausal descriptive summaries; no causal connectivity or stable neuron identity inferred']}
    np.savez_compressed(output / 'parameters.npz', **arrays)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    (output / 'results.json').write_text(text)
    Path('reports/m023_dynamics.json').write_text(text)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/m023_protocol.json')
    parser.add_argument('--output', default='data/processed/m023_dynamics')
    arguments = parser.parse_args()
    result = run(arguments.config, arguments.output)
    print(json.dumps({'development_target_sessions': result['development_target_sessions']}, indent=2))


if __name__ == '__main__':
    main()
