"""Chronological LINK channel transfer and disclosed calibration comparisons."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.cross_decomposition import CCA
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest, save_immutable
from cerebro.link import load_link, align_channel_keys
from cerebro.population import fit_population, fit_decoder, covariance_similarity, principal_angles


def validate_chronology(recording):
    """Validate original table order before chronological split or block sampling."""
    identities = [trial['trial_id'] for trial in recording['trials']]
    if len(set(identities)) != len(identities):
        raise ValueError('Trial identities must be unique within a session')
    previous_stop = -np.inf
    for trial in recording['trials']:
        times = np.asarray(trial['timestamps'])
        if len(times) < 2 or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0):
            raise ValueError('Trial clocks must be finite and ordered')
        if times[0] <= previous_stop:
            raise ValueError('Source trial table is not chronological and nonoverlapping')
        previous_stop = times[-1]
    reference = datetime.fromisoformat(recording['timestamps_reference_time'])
    return reference.timestamp() + recording['trials'][0]['timestamps'][0], reference.timestamp() + previous_stop


def flatten(trials, name, column_order=None):
    observations = []
    for trial in trials:
        values = trial[name]
        if column_order is not None:
            values = values[:, column_order]
        if len(values) < 2 or not np.all(np.isfinite(values)):
            raise ValueError('Complete finite trial observations required')
        observations.append(values)
    if not observations:
        raise ValueError('No trials available')
    return np.concatenate(observations, axis=0)


def trial_losses(trials, prediction):
    lengths = np.array([len(trial['position']) for trial in trials])
    if sum(lengths) != len(prediction):
        raise ValueError('Prediction lengths do not preserve trial boundaries')
    offsets = np.concatenate([[0], np.cumsum(lengths)])
    losses = []
    for index, trial in enumerate(trials):
        predicted = prediction[offsets[index]:offsets[index + 1]]
        error = trial['position'] - predicted
        losses.append(float(np.mean(error ** 2)))
    return np.array(losses)


def block_interval(values, draws, block_length, seed):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < block_length or block_length < 1:
        raise ValueError('Block resampling requires sufficient ordered trial values')
    generator = np.random.default_rng(seed)
    blocks_number = int(np.ceil(len(values) / block_length))
    starts = generator.integers(len(values) - block_length + 1, size=(draws, blocks_number))
    indices = starts[:, :, None] + np.arange(block_length)
    indices = indices.reshape(draws, -1)[:, :len(values)]
    means = values[indices].mean(axis=1)
    return np.quantile(means, [.025, .975]).tolist()


def condition_anchors(trials, latents, minimum):
    grouped = {}
    offset = 0
    for trial in trials:
        key = tuple(trial['target'].tolist())
        length = len(trial['counts'])
        trial_mean = latents[offset:offset + length].mean(axis=0)
        grouped.setdefault(key, []).append(trial_mean)
        offset += length
    anchors = {}
    for key, rows in grouped.items():
        if len(rows) >= minimum:
            anchors[key] = np.mean(rows, axis=0)
    return anchors


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    source_manifest = json.loads(Path(config['source_manifest']).read_text())
    target_manifest = json.loads(Path(config['target_manifest']).read_text())
    source = load_link(source_manifest)
    target = load_link(target_manifest)
    _, source_stop = validate_chronology(source)
    target_start, _ = validate_chronology(target)
    if source_stop >= target_start:
        raise ValueError('Source session must precede target session in absolute time')
    if source['subject_id'] != target['subject_id']:
        raise ValueError('This channel transfer protocol requires one subject')
    if source['metadata']['position_units'] != target['metadata']['position_units']:
        raise ValueError('Source and target behavior units differ')
    column_order = align_channel_keys(source['channel_keys'], target['channel_keys'])
    training_number = config['source_training_trials']
    inner_number = config['source_inner_training_trials']
    calibration_number = config['target_calibration_pool_trials']
    if not 1 < inner_number < training_number < len(source['trials']):
        raise ValueError('Source chronology requires disjoint fitting, selection and evaluation')
    if not 1 < calibration_number < len(target['trials']):
        raise ValueError('Target calibration and evaluation must be disjoint')
    if any(budget < 1 or budget > calibration_number for budget in config['calibration_budgets']):
        raise ValueError('Calibration budgets exceed the target pool')
    source_training = source['trials'][:training_number]
    source_evaluation = source['trials'][training_number:]
    calibration_pool = target['trials'][:calibration_number]
    target_evaluation = target['trials'][calibration_number:]
    splits = {
        'schema_version': 1, 'source_asset_sha256': source_manifest['sha256'],
        'target_asset_sha256': target_manifest['sha256'],
        'source_training': [trial['trial_id'] for trial in source_training],
        'source_inner_training': [trial['trial_id'] for trial in source_training[:inner_number]],
        'source_inner_validation': [trial['trial_id'] for trial in source_training[inner_number:]],
        'source_evaluation': [trial['trial_id'] for trial in source_evaluation],
        'target_unlabeled_calibration_pool': [trial['trial_id'] for trial in calibration_pool],
        'target_evaluation': [trial['trial_id'] for trial in target_evaluation],
        'target_label_budgets': {},
        'channel_keys': [list(key) for key in source['channel_keys']],
        'config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }
    for budget in config['calibration_budgets']:
        splits['target_label_budgets'][str(budget)] = [trial['trial_id'] for trial in calibration_pool[:budget]]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_immutable(output / 'split_manifest.json', splits)
    inner_counts = flatten(source_training[:inner_number], 'counts')
    inner_position = flatten(source_training[:inner_number], 'position')
    inner_scaler = StandardScaler().fit(inner_counts)
    inner_normalized = inner_scaler.transform(inner_counts)
    selection_counts = flatten(source_training[inner_number:], 'counts')
    selection_position = flatten(source_training[inner_number:], 'position')
    selection_normalized = inner_scaler.transform(selection_counts)
    candidates = []
    for alpha in config['ridge_alphas']:
        decoder = fit_decoder(inner_normalized, inner_position, alpha=alpha)
        prediction = decoder.predict(selection_normalized)
        losses = trial_losses(source_training[inner_number:], prediction)
        candidates.append({'alpha': alpha, 'selection_trial_mse_flexion2': float(losses.mean())})
    alpha = min(candidates, key=lambda row: row['selection_trial_mse_flexion2'])['alpha']
    source_counts = flatten(source_training, 'counts')
    source_position = flatten(source_training, 'position')
    source_scaler = StandardScaler().fit(source_counts)
    source_normalized = source_scaler.transform(source_counts)
    source_decoder = fit_decoder(source_normalized, source_position, alpha=alpha)
    evaluation_counts = flatten(target_evaluation, 'counts', column_order)
    evaluation_normalized = source_scaler.transform(evaluation_counts)
    source_eval_counts = flatten(source_evaluation, 'counts')
    source_eval_normalized = source_scaler.transform(source_eval_counts)
    source_prediction = source_decoder.predict(source_eval_normalized)
    source_losses = trial_losses(source_evaluation, source_prediction)
    source_mean = source_position.mean(axis=0)
    predictions = {
        'frozen_source': source_decoder.predict(evaluation_normalized),
        'source_mean': np.broadcast_to(source_mean, (len(evaluation_counts), 2)).copy(),
    }
    calibrated_counts = flatten(calibration_pool, 'counts', column_order)
    target_scaler = StandardScaler().fit(calibrated_counts)
    target_normalized = target_scaler.transform(evaluation_counts)
    predictions['unlabeled_marginal_normalization'] = source_decoder.predict(target_normalized)
    dimension = config['latent_dimensions']
    source_population = fit_population(source_normalized, dimension)
    source_latents = source_population.transform(source_normalized)
    source_latent_decoder = fit_decoder(source_latents, source_position, alpha=alpha)
    target_calibrated_in_source_frame = source_scaler.transform(calibrated_counts)
    target_population = fit_population(target_calibrated_in_source_frame, dimension)
    target_latents = target_population.transform(evaluation_normalized)
    source_anchors = condition_anchors(source_training, source_latents, config['anchor_min_repetitions'])
    alignment_status = {}
    parameter_arrays = {
        'source_scaler_mean': source_scaler.mean_, 'source_scaler_scale': source_scaler.scale_,
        'target_marginal_mean': target_scaler.mean_, 'target_marginal_scale': target_scaler.scale_,
        'source_decoder_coef': source_decoder.coef_, 'source_decoder_intercept': source_decoder.intercept_,
        'source_pca_components': source_population.components_, 'source_pca_mean': source_population.mean_,
        'target_pca_components': target_population.components_, 'target_pca_mean': target_population.mean_,
        'source_latent_decoder_coef': source_latent_decoder.coef_,
        'source_latent_decoder_intercept': source_latent_decoder.intercept_,
    }
    for budget in config['calibration_budgets']:
        labeled_trials = calibration_pool[:budget]
        counts = flatten(labeled_trials, 'counts', column_order)
        positions = flatten(labeled_trials, 'position')
        normalized = source_scaler.transform(counts)
        direct = fit_decoder(normalized, positions, alpha=alpha)
        predictions['direct_recalibration_' + str(budget)] = direct.predict(evaluation_normalized)
        frozen_calibration = source_decoder.predict(normalized)
        target_residuals = positions - frozen_calibration
        correction = fit_decoder(normalized, target_residuals, alpha=alpha)
        corrections = correction.predict(evaluation_normalized)
        predictions['source_plus_residual_' + str(budget)] = predictions['frozen_source'] + corrections
        for prefix, decoder in [('direct', direct), ('correction', correction)]:
            parameter_arrays[prefix + '_' + str(budget) + '_coef'] = decoder.coef_
            parameter_arrays[prefix + '_' + str(budget) + '_intercept'] = decoder.intercept_
        target_calibration_latents = target_population.transform(normalized)
        target_anchors = condition_anchors(labeled_trials, target_calibration_latents, config['anchor_min_repetitions'])
        common_keys = sorted(set(source_anchors) & set(target_anchors))
        if len(common_keys) <= dimension:
            alignment_status[str(budget)] = {'status': 'insufficient repeated shared target anchors', 'anchors': len(common_keys)}
            continue
        source_rows = np.stack([source_anchors[key] for key in common_keys])
        target_rows = np.stack([target_anchors[key] for key in common_keys])
        centered_rows = target_rows - target_rows.mean(axis=0)
        if np.linalg.matrix_rank(centered_rows) < dimension:
            alignment_status[str(budget)] = {'status': 'rank-deficient target anchors', 'anchors': len(common_keys)}
            continue
        alignment = fit_decoder(target_rows, source_rows, alpha=alpha)
        aligned_target_latents = alignment.predict(target_latents)
        predictions['condition_anchor_alignment_' + str(budget)] = source_latent_decoder.predict(aligned_target_latents)
        parameter_arrays['alignment_' + str(budget) + '_coef'] = alignment.coef_
        parameter_arrays['alignment_' + str(budget) + '_intercept'] = alignment.intercept_
        alignment_status[str(budget)] = {
            'status': 'exploratory fitted alignment', 'anchors': len(common_keys),
            'minimum_repetitions': config['anchor_min_repetitions'],
            'label_access': f'Calibration commanded-target metadata, not paired neurons or cross-day trial matching. Target PCA uses all{calibration_number} unlabeled calibration trials.',
        }
    source_covariance = np.cov(source_normalized, rowvar=False)
    target_covariance = np.cov(target_calibrated_in_source_frame, rowvar=False)
    angles = principal_angles(source_population.components_.T, target_population.components_.T)
    geometry = {
        'covariance_frobenius_cosine': covariance_similarity(source_covariance, target_covariance),
        'principal_angles_radians': angles.tolist(),
        'target_data_access': f'Only first{calibration_number} target calibration trials; no target evaluation samples',
    }
    all_target_latents = target_population.transform(target_calibrated_in_source_frame)
    all_target_anchors = condition_anchors(calibration_pool, all_target_latents, config['anchor_min_repetitions'])
    common_keys = sorted(set(source_anchors) & set(all_target_anchors))
    if len(common_keys) > dimension:
        left = np.stack([source_anchors[key] for key in common_keys])
        right = np.stack([all_target_anchors[key] for key in common_keys])
        canonical = CCA(n_components=dimension, max_iter=1000)
        canonical_left, canonical_right = canonical.fit_transform(left, right)
        correlations = []
        for coordinate in range(dimension):
            coefficient = np.corrcoef(canonical_left[:, coordinate], canonical_right[:, coordinate])[0, 1]
            correlations.append(float(coefficient) if np.isfinite(coefficient) else None)
        geometry['cca_in_sample_anchor_correlations'] = correlations
        geometry['cca_limitations'] = 'In-sample small-anchor CCA overfits; not independent transfer validation or neuron correspondence.'
    metrics = {}
    baseline_losses = trial_losses(target_evaluation, predictions['frozen_source'])
    for name, prediction in predictions.items():
        losses = trial_losses(target_evaluation, prediction)
        paired_changes = losses - baseline_losses
        metrics[name] = {
            'mean_trial_mse_flexion2': float(losses.mean()), 'trial_mse_flexion2': losses.tolist(),
            'paired_mse_change_from_frozen': float(paired_changes.mean()),
            'paired_moving_block_interval': block_interval(paired_changes, config['bootstrap_draws'], config['bootstrap_trial_block'], config['seed']),
            'prediction_outside_native_flexion_range_fraction': float(np.mean((prediction < 0) | (prediction > 1))),
            'chronological_trial_segments_mse': [float(segment.mean()) for segment in np.array_split(losses, 3)],
        }
        parameter_arrays[name + '_prediction_flexion'] = prediction
    parameter_arrays['target_evaluation_timestamps_seconds'] = flatten(target_evaluation, 'timestamps')
    parameter_arrays['target_evaluation_position_flexion'] = flatten(target_evaluation, 'position')
    source_paths = ('longitudinal.py', 'link.py', 'population.py')
    report = {
        'schema_version': 1, 'config': config, 'source': source_manifest, 'target': target_manifest,
        'source_metadata': source['metadata'], 'target_metadata': target['metadata'],
        'splits': splits, 'selection': candidates, 'selected_alpha': alpha,
        'source_evaluation_mse_flexion2': float(source_losses.mean()),
        'source_training_samples': len(source_counts), 'target_calibration_samples': len(calibrated_counts),
        'target_evaluation_samples': len(evaluation_counts), 'channel_count': len(column_order),
        'metrics': metrics, 'geometry': geometry, 'alignment_status': alignment_status,
        'hypothesis': 'Chronological source-to-target channel transfer may deteriorate; disclosed calibration may reduce independent target-trial prediction loss. Negative findings are valid.',
        'target_variable': 'Native index and middle-ring-pinky finger position in flexion units (0..1), same-bin offline decoding',
        'information_policy': f'Source-only tuning; chronological target{calibration_number} calibration pool versus{len(target_evaluation)} untouched evaluation trials. All methods use same target evaluation. Marginal normalization and target PCA receive{calibration_number} unlabeled calibration trials; supervised methods receive only named prefix trial labels. Anchor methods also receive calibration commanded-target metadata. No target evaluation normalization or selection.',
        'limitations': ['Two sessions of one monkey are not independent subject replicates', 'Channel matching does not establish stable neurons', 'Threshold-crossing count interpretation follows native description and integer values despite NWB volts label', 'No explicit quality mask; finite samples are not proof of signal quality', 'Native20ms clocks jitter by up to1ms; no interpolation or recomputed firing rates', 'Unlabeled target access differs across methods and is explicitly disclosed', 'Anchor alignment uses noisy commanded-target trial means, not event-time matched repeated neural responses', f"Moving {config['bootstrap_trial_block']}-trial block interval is sensitivity analysis, not validated population uncertainty", 'Hyperparameters for adaptation inherited from source-only selection', 'No actual biological closed-loop or multisubject inference'],
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
        'source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in source_paths},
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in parameter_arrays.items()},
    }
    np.savez_compressed(output / 'arrays.npz', **parameter_arrays)
    (output / 'results.json').write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/longitudinal_08.json')
    parser.add_argument('--output', default='data/processed/longitudinal_08')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    print(json.dumps({name: row['mean_trial_mse_flexion2'] for name, row in report['metrics'].items()}, indent=2))


if __name__ == '__main__':
    main()
