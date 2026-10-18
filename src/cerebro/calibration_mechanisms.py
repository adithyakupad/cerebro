"""Frozen M022 development diagnostics; no previously evaluated target rows."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest, save_immutable
from cerebro.link import align_channel_keys, load_link
from cerebro.longitudinal import condition_anchors, flatten, trial_losses, validate_chronology
from cerebro.population import fit_decoder


def allocate(trials, budget, policy, seed):
    """Select whole pool trials without evaluation access or replacement."""
    if not 1 <= budget <= len(trials):
        raise ValueError('Budget must fit the calibration pool')
    generator = np.random.default_rng(seed)
    if policy == 'chronological':
        return np.arange(budget)
    if policy == 'uniform':
        return np.sort(generator.choice(len(trials), budget, replace=False))
    if policy != 'balanced':
        raise ValueError('Unknown allocation policy')
    groups = {}
    for index, trial in enumerate(trials):
        key = tuple(trial['target'])
        groups.setdefault(key, []).append(index)
    queues = [list(generator.permutation(rows)) for rows in groups.values()]
    condition_order = generator.permutation(len(queues))
    selected = []
    while len(selected) < budget:
        for condition in condition_order:
            if queues[condition]:
                selected.append(int(queues[condition].pop()))
            if len(selected) == budget:
                break
    return np.sort(selected)


def development_split(recording, permitted, pool_size):
    """Slice permitted rows before any new development feature construction."""
    if not 1 < pool_size < permitted <= len(recording['trials']):
        raise ValueError('Insufficient permitted development trials')
    accessible = dict(recording)
    accessible['trials'] = recording['trials'][:permitted]
    validate_chronology(accessible)
    pool = accessible['trials'][:pool_size]
    evaluation = accessible['trials'][pool_size:]
    return pool, evaluation


def source_split(trials, training_number, inner_number):
    if not 1 < inner_number < training_number <= len(trials):
        raise ValueError('Source must contain the exact fitting and selection partitions')
    return trials[:training_number]


def shrink(frozen, recalibrated, weight):
    if frozen.shape != recalibrated.shape or not 0 <= weight <= 1:
        raise ValueError('Shrinkage requires matching arrays and weight in [0, 1]')
    correction = recalibrated - frozen
    return frozen + weight * correction


def coefficient_dispersion(coefficients):
    """Mean squared raw-count coefficient deviation; denominator is draws."""
    coefficients = np.asarray(coefficients)
    if coefficients.ndim != 3 or not np.isfinite(coefficients).all():
        raise ValueError('Expected finite draw by output by feature coefficients')
    mean_coefficients = coefficients.mean(axis=0)
    deviations = coefficients - mean_coefficients
    return float(np.mean(deviations ** 2))


def error_components(trials, prediction):
    offsets = np.cumsum([0] + [len(trial['position']) for trial in trials])
    offset_losses = []
    centered_losses = []
    for index, trial in enumerate(trials):
        residual = prediction[offsets[index]:offsets[index + 1]] - trial['position']
        mean_residual = residual.mean(axis=0)
        centered_residual = residual - mean_residual
        offset_losses.append(float(np.mean(mean_residual ** 2)))
        centered_losses.append(float(np.mean(centered_residual ** 2)))
    return float(np.mean(offset_losses)), float(np.mean(centered_losses))


def ensemble_diagnostics(trials, predictions, coefficients):
    """Exact finite-ensemble identity, with equal weighting of whole trials."""
    predictions = np.asarray(predictions)
    mean_prediction = predictions.mean(axis=0)
    deviations = predictions - mean_prediction
    prediction_variance = np.mean(deviations ** 2, axis=0)
    zero_trials = []
    for trial in trials:
        zero_trial = dict(trial)
        zero_trial['position'] = np.zeros_like(trial['position'])
        zero_trials.append(zero_trial)
    variance_losses = trial_losses(zero_trials, np.sqrt(prediction_variance))
    dispersion = float(variance_losses.mean())
    mean_prediction_loss = float(trial_losses(trials, mean_prediction).mean())
    losses = [float(trial_losses(trials, prediction).mean()) for prediction in predictions]
    identity_error = float(np.mean(losses) - mean_prediction_loss - dispersion)
    offset_loss, centered_loss = error_components(trials, mean_prediction)
    return {
        'mean_subset_mse': float(np.mean(losses)),
        'ensemble_mean_mse': mean_prediction_loss,
        'prediction_dispersion': dispersion,
        'bias_variance_identity_error': identity_error,
        'ensemble_offset_mse': offset_loss,
        'ensemble_centered_mse': centered_loss,
        'coefficient_dispersion_raw_count_frame': coefficient_dispersion(coefficients),
    }


def paired_session_interval(differences, draws, block_length, seed):
    """Conditional equal-session paired moving-block interval, not animal CI."""
    generator = np.random.default_rng(seed)
    session_means = []
    for values in differences:
        values = np.asarray(values)
        if len(values) < block_length:
            raise ValueError('Too few ordered trials for block sampling')
        block_count = int(np.ceil(len(values) / block_length))
        starts = generator.integers(len(values) - block_length + 1, size=(draws, block_count))
        indices = starts[:, :, None] + np.arange(block_length)
        indices = indices.reshape(draws, -1)[:, :len(values)]
        session_means.append(values[indices].mean(axis=1))
    equal_session_means = np.mean(session_means, axis=0)
    return np.quantile(equal_session_means, [.025, .975]).tolist()


def _model_predictions(counts, positions, evaluation_counts, source_scaler,
                       source_decoder, alpha, multipliers, weights):
    training_features = source_scaler.transform(counts)
    evaluation_features = source_scaler.transform(evaluation_counts)
    frozen_training = source_decoder.predict(training_features)
    frozen_evaluation = source_decoder.predict(evaluation_features)
    predictions = {}
    coefficients = {}
    degrees = {}
    centered_features = training_features - training_features.mean(axis=0)
    singular_values = np.linalg.svd(centered_features, compute_uv=False)
    eigenvalues = singular_values ** 2
    for multiplier in multipliers:
        penalty = alpha * multiplier
        degrees[str(multiplier)] = float(np.sum(eigenvalues / (eigenvalues + penalty)))
        for method in ('direct', 'residual'):
            targets = positions if method == 'direct' else positions - frozen_training
            decoder = fit_decoder(training_features, targets, alpha=penalty)
            prediction = decoder.predict(evaluation_features)
            total_coefficients = decoder.coef_.copy()
            if method == 'residual':
                prediction = prediction + frozen_evaluation
                total_coefficients = total_coefficients + source_decoder.coef_
            name = f'{method}_{multiplier:g}'
            predictions[name] = prediction
            coefficients[name] = total_coefficients / source_scaler.scale_[None, :]
            if multiplier == 1:
                for weight in weights:
                    shrink_name = f'{method}_shrink_{weight:g}'
                    predictions[shrink_name] = shrink(frozen_evaluation, prediction, weight)
                    total_raw = coefficients[name]
                    source_raw = source_decoder.coef_ / source_scaler.scale_[None, :]
                    coefficients[shrink_name] = shrink(source_raw, total_raw, weight)
    target_scaler = StandardScaler().fit(counts)
    scaled_decoder = fit_decoder(target_scaler.transform(counts), positions, alpha=alpha)
    predictions['direct_target_scale'] = scaled_decoder.predict(target_scaler.transform(evaluation_counts))
    coefficients['direct_target_scale'] = scaled_decoder.coef_ / target_scaler.scale_[None, :]
    calibration_mean = positions.mean(axis=0)
    mean_residual = (positions - frozen_training).mean(axis=0)
    predictions['calibration_mean'] = np.broadcast_to(calibration_mean, frozen_evaluation.shape).copy()
    predictions['intercept_correction'] = frozen_evaluation + mean_residual
    for name in ('calibration_mean', 'intercept_correction'):
        raw_coefficients = np.zeros_like(source_decoder.coef_)
        if name == 'intercept_correction':
            raw_coefficients = source_decoder.coef_ / source_scaler.scale_[None, :]
        coefficients[name] = raw_coefficients
    return predictions, coefficients, degrees


def run(config_path, output):
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source_manifest = json.loads(Path(config['source_manifest']).read_text())
    source = load_link(source_manifest)
    _, source_stop = validate_chronology(source)
    inner_number = config['source_inner_training_trials']
    source_trials = source_split(source['trials'], config['source_training_trials'], inner_number)
    development_manifests = [json.loads(Path(path).read_text()) for path in config['development_manifests']]
    asset_ids = [manifest['asset_id'] for manifest in development_manifests]
    if len(set(asset_ids)) != len(asset_ids) or source_manifest['asset_id'] in asset_ids:
        raise ValueError('Source and development assets must be distinct')
    inner_trials = source_trials[:inner_number]
    selection_trials = source_trials[inner_number:]
    inner_counts = flatten(inner_trials, 'counts')
    inner_position = flatten(inner_trials, 'position')
    inner_scaler = StandardScaler().fit(inner_counts)
    source_selection = []
    for alpha in config['source_alpha_grid']:
        decoder = fit_decoder(inner_scaler.transform(inner_counts), inner_position, alpha=alpha)
        prediction = decoder.predict(inner_scaler.transform(flatten(selection_trials, 'counts')))
        selection_loss = float(trial_losses(selection_trials, prediction).mean())
        source_selection.append({'alpha': alpha, 'mse': selection_loss})
    alpha = min(source_selection, key=lambda row: row['mse'])['alpha']
    source_counts = flatten(source_trials, 'counts')
    source_position = flatten(source_trials, 'position')
    source_scaler = StandardScaler().fit(source_counts)
    source_decoder = fit_decoder(source_scaler.transform(source_counts), source_position, alpha=alpha)
    arrays = {'source_coef': source_decoder.coef_, 'source_intercept': source_decoder.intercept_,
              'source_scaler_mean': source_scaler.mean_, 'source_scaler_scale': source_scaler.scale_}
    sessions = []
    allocations = []
    session_identities = set()
    source_anchors = condition_anchors(source_trials, source_counts, 2)
    for session_index, manifest_path in enumerate(config['development_manifests']):
        manifest = json.loads(Path(manifest_path).read_text())
        target = load_link(manifest)
        if target['session_id'] in session_identities:
            raise ValueError('Development sessions must be distinct')
        session_identities.add(target['session_id'])
        pool, evaluation = development_split(target, config['permitted_trial_rows'], config['allocation_pool_trials'])
        accessible = dict(target)
        accessible['trials'] = pool + evaluation
        target_start, _ = validate_chronology(accessible)
        if source_stop >= target_start or source['subject_id'] != target['subject_id']:
            raise ValueError('Development must follow source within the same subject')
        if source['metadata']['position_units'] != target['metadata']['position_units']:
            raise ValueError('Behavior units differ')
        order = align_channel_keys(source['channel_keys'], target['channel_keys'])
        evaluation_counts = flatten(evaluation, 'counts', order)
        evaluation_features = source_scaler.transform(evaluation_counts)
        frozen = source_decoder.predict(evaluation_features)
        source_mean = np.broadcast_to(source_position.mean(axis=0), frozen.shape)
        pool_counts = flatten(pool, 'counts', order)
        pool_scaler = StandardScaler().fit(pool_counts)
        pool_normalized = pool_scaler.transform(evaluation_counts)
        marginal = source_decoder.predict(pool_normalized)
        generator = np.random.default_rng(config['random_seed'])
        permutation = generator.permutation(evaluation_counts.shape[1])
        permuted_features = source_scaler.transform(evaluation_counts[:, permutation])
        permuted = source_decoder.predict(permuted_features)
        target_anchors = condition_anchors(pool, pool_counts, 2)
        shared = sorted(set(source_anchors) & set(target_anchors))
        tuning_cosines = []
        for key in shared:
            source_pattern = source_anchors[key] - source_counts.mean(axis=0)
            target_pattern = target_anchors[key] - pool_counts.mean(axis=0)
            denominator = np.linalg.norm(source_pattern) * np.linalg.norm(target_pattern)
            tuning_cosines.append(None if denominator == 0 else float(source_pattern @ target_pattern / denominator))
        session_id = manifest['asset_path'].split('ses-')[1][:8]
        base = {
            'session': session_id, 'manifest': manifest,
            'pool_trial_ids': [trial['trial_id'] for trial in pool],
            'evaluation_trial_ids': [trial['trial_id'] for trial in evaluation],
            'pool_bins': len(pool_counts), 'evaluation_bins': len(evaluation_counts),
            'native_metadata': target['metadata'],
            'frozen_trial_mse': trial_losses(evaluation, frozen).tolist(),
            'source_mean_trial_mse': trial_losses(evaluation, source_mean).tolist(),
            'marginal_normalization_trial_mse': trial_losses(evaluation, marginal).tolist(),
            'permuted_contact_trial_mse': trial_losses(evaluation, permuted).tolist(),
            'target_column_order': order.tolist(), 'permuted_source_columns': permutation.tolist(),
            'matched_command_patterns': [{
                'command': list(key), 'cosine': cosine,
                'source_repetitions': sum(tuple(trial['target']) == key for trial in source_trials),
                'target_pool_repetitions': sum(tuple(trial['target']) == key for trial in pool),
            } for key, cosine in zip(shared, tuning_cosines)],
            'groups': [],
        }
        arrays[session_id + '_evaluation_timestamps'] = flatten(evaluation, 'timestamps')
        arrays[session_id + '_evaluation_position'] = flatten(evaluation, 'position')
        arrays[session_id + '_frozen_prediction'] = frozen
        for budget in config['budgets']:
            for policy in ('chronological', 'uniform', 'balanced'):
                draw_count = 1 if policy == 'chronological' else config['subset_draws']
                predictions_by_model = {}
                coefficients_by_model = {}
                diagnostics = []
                for draw in range(draw_count):
                    seed = config['random_seed'] + session_index * 10000 + budget * 100 + draw
                    indices = allocate(pool, budget, policy, seed)
                    selected_trials = [pool[index] for index in indices]
                    counts = flatten(selected_trials, 'counts', order)
                    positions = flatten(selected_trials, 'position')
                    predictions, coefficients, degrees = _model_predictions(
                        counts, positions, evaluation_counts, source_scaler,
                        source_decoder, alpha, config['alpha_multipliers'], config['shrinkage_weights'])
                    allocation = {
                        'session': session_id, 'budget': budget, 'policy': policy, 'draw': draw, 'seed': seed,
                        'trial_ids': [trial['trial_id'] for trial in selected_trials],
                        'pool_indices': indices.tolist(), 'labeled_bins': len(counts),
                        'command_metadata_trials': len(pool) if policy == 'balanced' else 0,
                    }
                    allocations.append(allocation)
                    command_count = len({tuple(trial['target']) for trial in selected_trials})
                    mean_distance = positions.mean(axis=0) - flatten(evaluation, 'position').mean(axis=0)
                    standardized_counts = source_scaler.transform(counts)
                    diagnostics.append({
                        'labeled_bins': len(counts), 'commands_covered_posthoc': command_count,
                        'label_mean_distance_squared_posthoc': float(np.mean(mean_distance ** 2)),
                        'source_standardized_mean_squared': float(np.mean(standardized_counts.mean(axis=0) ** 2)),
                        'source_standardized_scale_squared_deviation': float(np.mean((standardized_counts.std(axis=0) - 1) ** 2)),
                        'effective_degrees_of_freedom_excluding_intercept': degrees,
                    })
                    for name, prediction in predictions.items():
                        predictions_by_model.setdefault(name, []).append(prediction)
                        coefficients_by_model.setdefault(name, []).append(coefficients[name])
                models = {}
                group_prefix = f'{session_id}_{budget}_{policy}_'
                for name, predictions in predictions_by_model.items():
                    coefficients = np.asarray(coefficients_by_model[name])
                    summary = ensemble_diagnostics(evaluation, predictions, coefficients)
                    losses = np.asarray([trial_losses(evaluation, prediction) for prediction in predictions])
                    summary['subset_trial_mse'] = losses.tolist()
                    summary['coefficient_mean_squared_norm'] = float(np.mean(np.sum(coefficients ** 2, axis=(1, 2))))
                    components = [error_components(evaluation, prediction) for prediction in predictions]
                    summary['mean_subset_offset_mse'] = float(np.mean([row[0] for row in components]))
                    summary['mean_subset_centered_mse'] = float(np.mean([row[1] for row in components]))
                    models[name] = summary
                    arrays[group_prefix + name + '_predictions'] = np.asarray(predictions)
                    arrays[group_prefix + name + '_coefficients'] = coefficients
                base['groups'].append({'budget': budget, 'policy': policy, 'draw_diagnostics': diagnostics, 'models': models})
        sessions.append(base)
        print('Completed development session ' + session_id, flush=True)
    promotion = promotion_results(sessions, config)
    protocol_path = Path('docs/research/m022_protocol.md')
    lineage = {
        'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
        'source_manifest': source_manifest, 'source_trial_ids': [trial['trial_id'] for trial in source_trials],
        'source_channel_keys': [list(key) for key in source['channel_keys']],
        'allocations': allocations,
    }
    save_immutable(output / 'split_manifest.json', lineage)
    report = {
        'schema_version': 1, 'config': config, 'source_selection': source_selection,
        'selected_source_alpha': alpha, 'source_training_bins': len(source_counts),
        'source_metadata': source['metadata'], 'sessions': sessions,
        'promotion': promotion, 'lineage': lineage,
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                          for name in ('calibration_mechanisms.py', 'link.py', 'longitudinal.py', 'population.py')},
        'versions': {name: importlib.metadata.version(name) for name in ('numpy', 'scikit-learn', 'pynwb', 'matplotlib')},
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in arrays.items()},
    }
    np.savez_compressed(output / 'arrays.npz', **arrays)
    (output / 'results.json').write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return report


def promotion_results(sessions, config):
    candidates = []
    for weight in config['shrinkage_weights']:
        candidates.extend([f'direct_shrink_{weight:g}', f'residual_shrink_{weight:g}'])
    candidates.append('direct_100')
    decisions = []
    selected = None
    for candidate in candidates:
        comparisons = {}
        for baseline in ('frozen', 'direct_1'):
            differences = []
            relative_changes = []
            for session in sessions:
                primary = next(group for group in session['groups']
                               if group['budget'] == config['primary_budget'] and group['policy'] == 'chronological')
                candidate_losses = np.asarray(primary['models'][candidate]['subset_trial_mse'][0])
                baseline_losses = np.asarray(session['frozen_trial_mse'])
                if baseline != 'frozen':
                    baseline_losses = np.asarray(primary['models'][baseline]['subset_trial_mse'][0])
                differences.append(candidate_losses - baseline_losses)
                relative_changes.append(float(1 - candidate_losses.mean() / baseline_losses.mean()))
            interval = paired_session_interval(differences, config['bootstrap_draws'],
                                               config['bootstrap_block_trials'], config['random_seed'])
            improvement = float(np.mean(relative_changes))
            each_date_better = all(values.mean() < 0 for values in differences)
            passed = improvement >= config['practical_relative_improvement'] and each_date_better and interval[1] < 0
            comparisons[baseline] = {'mean_relative_improvement': improvement, 'session_relative_improvements': relative_changes,
                                     'paired_mse_difference': float(np.mean([values.mean() for values in differences])),
                                     'conditional_block_interval': interval, 'every_date_better': each_date_better, 'passed': passed}
        passed = all(row['passed'] for row in comparisons.values())
        decisions.append({'candidate': candidate, 'comparisons': comparisons, 'passed': passed})
        if passed and selected is None:
            selected = candidate
    return {'selected_method': selected, 'candidate_decisions': decisions,
            'independent_validation_status': 'Requires separately committed native eligibility and validation addendum' if selected
            else 'NOT EXECUTED: prespecified development promotion gate failed; new sessions remain unscored'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/m022_calibration.json')
    parser.add_argument('--output', default='data/processed/m022_calibration')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    print(json.dumps(report['promotion'], indent=2))


if __name__ == '__main__':
    main()
