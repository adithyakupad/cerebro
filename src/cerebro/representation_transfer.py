"""Observed-session LINK representation transfer with fixed one-factor settings."""

import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression, Ridge

from cerebro.benchmark import array_digest, trial_metrics
from cerebro.link import align_channel_keys, load_link
from cerebro.longitudinal import validate_chronology
from cerebro.representation_benchmark import (
    RepresentationGRU, VelocityGRU, _save_restore_pretraining,
    _train_pretraining, _train_supervised, standardize_counts,
)


def prepare_sessions(recordings, config):
    """Preserve chronological trial identities and native sample timestamps."""
    if len(recordings) != 3:
        raise ValueError('Exactly two source sessions and one later target are required')
    absolute_ranges = [validate_chronology(recording) for recording in recordings]
    for index in range(2):
        if absolute_ranges[index][1] >= absolute_ranges[index + 1][0]:
            raise ValueError('Source sessions must precede the unseen target in absolute time')
    reference = recordings[0]
    native_bins = config['native_bins_per_trial']
    if not isinstance(native_bins, int) or native_bins < 2:
        raise ValueError('At least two native bins per trial are required')
    sessions = []
    mappings = []
    for recording in recordings:
        if recording['subject_id'] != reference['subject_id']:
            raise ValueError('This transfer experiment requires the same observed subject')
        if recording['metadata']['position_units'] != reference['metadata']['position_units']:
            raise ValueError('Native position units differ across sessions')
        column_order = align_channel_keys(reference['channel_keys'], recording['channel_keys'])
        mappings.append(column_order.tolist())
        counts = []
        positions = []
        timestamps = []
        identities = []
        for trial in recording['trials']:
            if len(trial['counts']) < native_bins:
                raise ValueError('A source trial lacks the fixed native sample window')
            observed_counts = trial['counts'][:native_bins, column_order]
            observed_position = trial['position'][:native_bins]
            original_times = trial['timestamps'][:native_bins]
            if not np.all(trial['position_valid'][:native_bins]) or not np.all(np.isfinite(observed_position)):
                raise ValueError('A trial has missing positions in the fixed window')
            clock_step_error = np.abs(np.diff(original_times) - .020)
            if np.any(clock_step_error > config['native_clock_step_tolerance_seconds']):
                raise ValueError('Native clock steps exceed the disclosed nominal 20 ms tolerance')
            counts.append(observed_counts)
            positions.append(observed_position)
            timestamps.append(original_times)
            identities.append(int(trial['trial_id']))
        sessions.append({
            'counts': np.stack(counts), 'position': np.stack(positions),
            'timestamps': np.stack(timestamps), 'trial_ids': np.asarray(identities),
        })
    calibration_number = config['target_calibration_trials']
    evaluation_number = config['target_evaluation_trials']
    if calibration_number < 1 or evaluation_number < 1:
        raise ValueError('Calibration and evaluation trial counts must be positive')
    if calibration_number + evaluation_number > len(sessions[2]['trial_ids']):
        raise ValueError('Target chronological calibration and evaluation overlap')
    if any(size < 1 or size > calibration_number for size in config['label_budgets']):
        raise ValueError('Label budgets exceed the independent calibration pool')
    return sessions, mappings, absolute_ranges


def source_standardization(source_counts, target_counts):
    """Fit feature moments exclusively on source recordings, never on target."""
    source_mask = np.ones(source_counts.shape[0], dtype=bool)
    normalized_source, parameters = standardize_counts(source_counts, source_mask)
    if not np.all(np.isfinite(target_counts)) or np.any(target_counts < 0):
        raise ValueError('Target counts must be finite and nonnegative')
    normalized_target = (target_counts - parameters['feature_mean']) / parameters['feature_scale']
    return normalized_source, normalized_target, parameters


def _encoded(model, features):
    model.eval()
    with torch.no_grad():
        latent = model.encode(features).numpy()
    return latent


def _metrics(prediction, targets):
    trial_mse, coordinate_r2 = trial_metrics(targets, prediction)
    return {
        'mse_native_position_squared': float(trial_mse.mean()),
        'trial_mse_native_position_squared': trial_mse.tolist(),
        'pooled_r2_by_coordinate': [float(value) if np.isfinite(value) else None for value in coordinate_r2],
    }


def session_identity_probe(training_latent, training_sessions, evaluation_latent, evaluation_sessions):
    """Classify source session using independent trial-mean latent rows."""
    if training_latent.ndim != 3 or evaluation_latent.ndim != 3:
        raise ValueError('Identity probing requires trials × bins × latent coordinates')
    training_rows = training_latent.mean(axis=1)
    evaluation_rows = evaluation_latent.mean(axis=1)
    classifier = LogisticRegression(C=1.0, max_iter=1000, random_state=0)
    classifier.fit(training_rows, training_sessions)
    predictions = classifier.predict(evaluation_rows)
    accuracy = float(np.mean(predictions == evaluation_sessions))
    return classifier, predictions, accuracy


def _frozen_probe(encoder, source_latent, source_labels, evaluation_features, config, path, parameters, provenance):
    hidden = encoder.encoder.hidden_size
    label_features = source_latent.reshape(-1, hidden)
    label_targets = source_labels.reshape(-1, 2)
    probe = Ridge(alpha=config['ridge_alpha']).fit(label_features, label_targets)
    evaluation_latent = _encoded(encoder, evaluation_features)
    flat_evaluation = evaluation_latent.reshape(-1, hidden)
    prediction = probe.predict(flat_evaluation).reshape(evaluation_features.shape[:2] + (2,))
    checkpoint = {
        'state_dict': copy.deepcopy(encoder.state_dict()), 'input_units': encoder.encoder.input_size,
        'hidden': hidden, 'ridge_coefficients': torch.tensor(probe.coef_),
        'ridge_intercept': torch.tensor(probe.intercept_), 'provenance': provenance,
        'normalization': {name: torch.tensor(value) for name, value in parameters.items()},
    }
    torch.save(checkpoint, path)
    restored = torch.load(path, weights_only=True)
    replica = RepresentationGRU(restored['input_units'], restored['hidden'])
    replica.load_state_dict(restored['state_dict'])
    restored_latent = _encoded(replica, evaluation_features).reshape(-1, hidden)
    restored_prediction = restored_latent @ restored['ridge_coefficients'].numpy().T
    restored_prediction = restored_prediction + restored['ridge_intercept'].numpy()
    restored_prediction = restored_prediction.reshape(prediction.shape)
    if not np.array_equal(prediction, restored_prediction):
        raise ValueError('Frozen probe checkpoint changed predictions')
    return prediction


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    if len(config['source_manifests']) != 2 or not config['settings'] or not config['seeds']:
        raise ValueError('Two source manifests, settings, and initialization seeds are required')
    positive_integer_names = (
        'native_bins_per_trial', 'source_reserved_trials', 'target_calibration_trials',
        'target_evaluation_trials', 'supervised_epochs', 'source_probe_trials_each',
    )
    for name in positive_integer_names:
        value = config[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError('Trial counts, sample windows, and epochs must be positive integers')
    for setting in config['settings']:
        for name in ('hidden', 'source_trials_each', 'epochs'):
            value = setting[name]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError('Setting dimensions, trial counts, and epochs must be positive integers')
    numeric_parameters = [config[name] for name in ('learning_rate', 'gradient_clip', 'mask_probability', 'ridge_alpha')]
    if not np.all(np.isfinite(numeric_parameters)):
        raise ValueError('Optimization parameters must be finite')
    if config['learning_rate'] <= 0 or config['gradient_clip'] <= 0 or config['ridge_alpha'] < 0:
        raise ValueError('Learning rate/gradient bound must be positive and ridge penalty nonnegative')
    if not 0 < config['mask_probability'] < 1:
        raise ValueError('Mask probability must lie strictly between zero and one')
    clock_tolerance = config['native_clock_step_tolerance_seconds']
    if not np.isfinite(clock_tolerance) or not 0 <= clock_tolerance < .020:
        raise ValueError('Clock tolerance must be finite and smaller than a nominal bin')
    manifest_paths = config['source_manifests'] + [config['target_manifest']]
    manifests = [json.loads(Path(path).read_text()) for path in manifest_paths]
    recordings = [load_link(manifest) for manifest in manifests]
    sessions, mappings, absolute_ranges = prepare_sessions(recordings, config)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = sessions[2]
    calibration_number = config['target_calibration_trials']
    evaluation_start = len(target['trial_ids']) - config['target_evaluation_trials']
    evaluation_position = target['position'][evaluation_start:]
    saved_arrays = {
        'evaluation_trial_ids': target['trial_ids'][evaluation_start:],
        'evaluation_native_timestamps_seconds': target['timestamps'][evaluation_start:],
        'evaluation_position_native_units': evaluation_position,
        'calibration_trial_ids': target['trial_ids'][:calibration_number],
        'calibration_native_timestamps_seconds': target['timestamps'][:calibration_number],
    }
    results = []
    pretraining_results = []
    identity_results = []
    setting_splits = {}
    for setting in config['settings']:
        training_number = setting['source_trials_each']
        for session in sessions[:2]:
            available = len(session['trial_ids']) - config['source_reserved_trials']
            if training_number < 1 or training_number > available or config['source_probe_trials_each'] > available:
                raise ValueError('Source fitting would consume reserved source trials')
        source_counts = np.concatenate([session['counts'][:training_number] for session in sessions[:2]], axis=0)
        probe_number = config['source_probe_trials_each']
        probe_counts = np.concatenate([session['counts'][:probe_number] for session in sessions[:2]], axis=0)
        source_position = np.concatenate([session['position'][:probe_number] for session in sessions[:2]], axis=0)
        normalized_source, normalized_target, parameters = source_standardization(source_counts, target['counts'])
        source_features = torch.tensor(normalized_source, dtype=torch.float32)
        normalized_probe = (probe_counts - parameters['feature_mean']) / parameters['feature_scale']
        source_probe_features = torch.tensor(normalized_probe, dtype=torch.float32)
        reserved_number = config['source_reserved_trials']
        reserved_counts = np.concatenate([session['counts'][-reserved_number:] for session in sessions[:2]], axis=0)
        normalized_reserved = (reserved_counts - parameters['feature_mean']) / parameters['feature_scale']
        reserved_features = torch.tensor(normalized_reserved, dtype=torch.float32)
        training_session_labels = np.repeat([0, 1], probe_number)
        evaluation_session_labels = np.repeat([0, 1], reserved_number)
        target_features = torch.tensor(normalized_target, dtype=torch.float32)
        evaluation_features = target_features[evaluation_start:]
        split = {
            'source_training': [session['trial_ids'][:training_number].tolist() for session in sessions[:2]],
            'source_labeled_probe_training': [session['trial_ids'][:probe_number].tolist() for session in sessions[:2]],
            'source_reserved': [session['trial_ids'][-config['source_reserved_trials']:].tolist() for session in sessions[:2]],
            'target_calibration': target['trial_ids'][:calibration_number].tolist(),
            'target_evaluation': target['trial_ids'][evaluation_start:].tolist(),
        }
        setting_splits[setting['name']] = split
        ssl_config = dict(config)
        ssl_config['epochs'] = setting['epochs']
        supervised_config = dict(config)
        supervised_config['epochs'] = config['supervised_epochs']
        for seed in config['seeds']:
            torch.manual_seed(seed)
            pretrained = RepresentationGRU(source_counts.shape[-1], setting['hidden'])
            initial_state = copy.deepcopy(pretrained.state_dict())
            history = _train_pretraining(pretrained, source_features, ssl_config, seed)
            prefix = setting['name'] + '_seed_' + str(seed)
            ssl_path = output / (prefix + '_pretrained.pt')
            replica = _save_restore_pretraining(pretrained, ssl_path, ssl_config, seed, parameters, split)
            source_latent = _encoded(pretrained, source_features)
            if not np.array_equal(source_latent, _encoded(replica, source_features)):
                raise ValueError('SSL checkpoint changed source latent states')
            random_encoder = RepresentationGRU(source_counts.shape[-1], setting['hidden'])
            random_encoder.load_state_dict(initial_state)
            encoders = [('pretrained', pretrained), ('random', random_encoder)]
            pretraining_results.append({
                'setting': setting['name'], 'seed': seed, 'history': history,
                'source_shape': list(source_counts.shape), 'hidden': setting['hidden'],
                'parameters': sum(parameter.numel() for parameter in pretrained.parameters()),
                'normalization': {name: value.tolist() for name, value in parameters.items()},
                'checkpoint_sha256': hashlib.sha256(ssl_path.read_bytes()).hexdigest(),
                'checkpoint_restored_latents_identical': True,
            })
            for encoder_name, encoder in encoders:
                training_latent = _encoded(encoder, source_probe_features)
                reserved_latent = _encoded(encoder, reserved_features)
                identity_classifier, identity_predictions, identity_accuracy = session_identity_probe(
                    training_latent, training_session_labels, reserved_latent, evaluation_session_labels,
                )
                identity_path = output / (prefix + '_' + encoder_name + '_session_identity.pt')
                identity_checkpoint = {
                    'state_dict': copy.deepcopy(encoder.state_dict()), 'input_units': source_counts.shape[-1],
                    'hidden': setting['hidden'], 'coefficients': torch.tensor(identity_classifier.coef_),
                    'intercept': torch.tensor(identity_classifier.intercept_),
                    'classes': torch.tensor(identity_classifier.classes_),
                    'normalization': {name: torch.tensor(value) for name, value in parameters.items()},
                    'provenance': {'config': config, 'setting': setting, 'seed': seed, 'splits': split},
                }
                torch.save(identity_checkpoint, identity_path)
                restored_identity = torch.load(identity_path, weights_only=True)
                restored_encoder = RepresentationGRU(restored_identity['input_units'], restored_identity['hidden'])
                restored_encoder.load_state_dict(restored_identity['state_dict'])
                restored_rows = _encoded(restored_encoder, reserved_features).mean(axis=1)
                restored_scores = restored_rows @ restored_identity['coefficients'].numpy().T
                restored_scores = restored_scores + restored_identity['intercept'].numpy()
                restored_classes = restored_identity['classes'].numpy()
                restored_predictions = restored_classes[(restored_scores[:, 0] > 0).astype(int)]
                if not np.array_equal(restored_predictions, identity_predictions):
                    raise ValueError('Identity classifier checkpoint changed predictions')
                identity_results.append({
                    'setting': setting['name'], 'seed': seed, 'encoder': encoder_name,
                    'accuracy': identity_accuracy, 'balanced_chance_accuracy': .5,
                    'training_trial_rows': len(training_session_labels),
                    'evaluation_trial_rows': len(evaluation_session_labels),
                    'evaluation_session_labels': evaluation_session_labels.tolist(),
                    'evaluation_predictions': identity_predictions.tolist(),
                    'C': 1.0, 'max_iter': 1000,
                    'checkpoint_sha256': hashlib.sha256(identity_path.read_bytes()).hexdigest(),
                    'checkpoint_restored_predictions_identical': True,
                })
                identifier = prefix + '_' + encoder_name + '_zero_shot'
                checkpoint_path = output / (identifier + '.pt')
                provenance = {'config': config, 'setting': setting, 'seed': seed, 'splits': split, 'fit_labels': 'source only'}
                prediction = _frozen_probe(
                    encoder, training_latent, source_position, evaluation_features,
                    config, checkpoint_path, parameters, provenance,
                )
                saved_arrays[identifier] = prediction
                results.append({
                    'setting': setting['name'], 'seed': seed, 'control': encoder_name + '_zero_shot',
                    'target_label_budget': 0, 'history': [], **_metrics(prediction, evaluation_position),
                    'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
                    'checkpoint_restored_predictions_identical': True,
                    'parameters': sum(parameter.numel() for parameter in encoder.encoder.parameters()) + 2 * (setting['hidden'] + 1),
                })
            for budget in config['label_budgets']:
                labeled_features = target_features[:budget]
                labeled_position = target['position'][:budget]
                for encoder_name, encoder in encoders:
                    labeled_latent = _encoded(encoder, labeled_features)
                    identifier = prefix + '_' + encoder_name + '_frozen_budget_' + str(budget)
                    checkpoint_path = output / (identifier + '.pt')
                    provenance = {'config': config, 'setting': setting, 'seed': seed, 'splits': split, 'label_trial_ids': target['trial_ids'][:budget].tolist()}
                    prediction = _frozen_probe(
                        encoder, labeled_latent, labeled_position, evaluation_features,
                        config, checkpoint_path, parameters, provenance,
                    )
                    saved_arrays[identifier] = prediction
                    results.append({
                        'setting': setting['name'], 'seed': seed, 'control': encoder_name + '_frozen_ridge',
                        'target_label_budget': budget, 'history': [], **_metrics(prediction, evaluation_position),
                        'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
                        'checkpoint_restored_predictions_identical': True,
                        'parameters': sum(parameter.numel() for parameter in encoder.encoder.parameters()) + 2 * (setting['hidden'] + 1),
                    })
                    torch.manual_seed(seed + 2000)
                    supervised = VelocityGRU(encoder.encoder, setting['hidden'])
                    supervised_history, target_parameters = _train_supervised(
                        supervised, labeled_features, labeled_position, supervised_config,
                    )
                    for entry in supervised_history:
                        entry['normalized_position_loss'] = entry.pop('normalized_velocity_loss')
                    supervised.eval()
                    with torch.no_grad():
                        normalized_prediction = supervised(evaluation_features).numpy()
                    prediction = normalized_prediction * target_parameters['target_scale'] + target_parameters['target_mean']
                    identifier = prefix + '_' + encoder_name + '_supervised_budget_' + str(budget)
                    checkpoint_path = output / (identifier + '.pt')
                    checkpoint = {
                        'state_dict': copy.deepcopy(supervised.state_dict()), 'input_units': source_counts.shape[-1],
                        'hidden': setting['hidden'], 'provenance': provenance,
                        'normalization': {name: torch.tensor(value) for name, value in {**parameters, **target_parameters}.items()},
                    }
                    torch.save(checkpoint, checkpoint_path)
                    restored = torch.load(checkpoint_path, weights_only=True)
                    fresh_encoder = RepresentationGRU(restored['input_units'], restored['hidden'])
                    restored_model = VelocityGRU(fresh_encoder.encoder, restored['hidden'])
                    restored_model.load_state_dict(restored['state_dict'])
                    restored_model.eval()
                    with torch.no_grad():
                        restored_prediction = restored_model(evaluation_features).numpy()
                    if not np.array_equal(restored_prediction, normalized_prediction):
                        raise ValueError('Supervised checkpoint changed predictions')
                    saved_arrays[identifier] = prediction
                    results.append({
                        'setting': setting['name'], 'seed': seed,
                        'control': 'pretrained_finetuned' if encoder_name == 'pretrained' else 'random_supervised_only',
                        'target_label_budget': budget, 'history': supervised_history,
                        **_metrics(prediction, evaluation_position),
                        'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
                        'checkpoint_restored_predictions_identical': True,
                        'parameters': sum(parameter.numel() for parameter in supervised.parameters()),
                    })
    np.savez_compressed(output / 'predictions.npz', **saved_arrays)
    report = {
        'schema_version': 1, 'config': config, 'manifests': manifests,
        'subject_id': recordings[0]['subject_id'], 'native_position_units': recordings[0]['metadata']['position_units'],
        'behavior': 'index and MRS finger position/flexion; not hand velocity or m/s',
        'native_bin_width_seconds': .020, 'absolute_session_ranges_seconds': absolute_ranges,
        'native_clock_steps_seconds': [
            {'minimum': float(np.diff(session['timestamps'], axis=1).min()),
             'maximum': float(np.diff(session['timestamps'], axis=1).max())}
            for session in sessions
        ],
        'recording_metadata': [recording['metadata'] for recording in recordings],
        'native_count_metadata': [recording['native_metadata'] for recording in recordings],
        'channel_keys': [list(key) for key in recordings[0]['channel_keys']],
        'channel_column_mappings': mappings, 'session_shapes': [list(session['counts'].shape) for session in sessions],
        'trial_target_styles': [sorted(set(trial['target_style'] for trial in recording['trials'])) for recording in recordings],
        'splits': setting_splits, 'pretraining': pretraining_results, 'results': results,
        'session_identity_diagnostics': identity_results,
        'torch_version': str(torch.__version__), 'device': 'CPU',
        'source_sha256': {
            name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ('representation_transfer.py', 'representation_benchmark.py', 'link.py', 'longitudinal.py')
        },
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()),
        'package_versions': {name: importlib.metadata.version(name) for name in ('numpy', 'scikit-learn', 'torch', 'pynwb')},
        'access_rules': 'SSL and feature normalization use two earlier source-session subsets only. First300/source session supply fixed position-label zero-shot source probes and fixed session-identity classifier fitting, including the data100 SSL setting. Reserved final75/source session supply auxiliary identity evaluation only and no parameter fitting or selection. Target first75 supply nested first5/15/75 position labels only to calibration controls; final300 target trials supply no fitted parameter or selection decision. Fixed architecture, epochs and regularization; no outer evaluation selection.',
        'limitations': [
            'Observed same-subject, three-session experiment; not validated foundation-model capability',
            'Contact coordinates establish feature order, not longitudinal neuron identity',
            'Fixed first40 native samples restrict observations to 0.8 seconds per trial and may truncate task events',
            'Current native neural bin predicts same-time native position offline; no closed-loop validation',
            'Source nominal 20 ms count bins have native timestamp-step jitter; original clocks are preserved and deviations beyond the configured tolerance are rejected',
            'GRU recurrence advances by native sample order, not continuously by physical clock intervals; temporal dynamics are not exact continuous-time models',
            'One-factor settings are finite ablations, not scaling laws or optimized convergence',
            'Initialization seeds do not provide independent subject/session replication',
            'The data100 setting changes both SSL observations and the scaler-fitting pool while labeled source probes remain300/session; it is not an isolated SSL-objective data effect',
            'No subject/session/time identifiers are supplied as model inputs; above-chance identity probing nevertheless indicates retained source-date information, not identity-free representations',
            'Session-classifier accuracy is an auxiliary diagnostic, not a significance test or independent-subject inference',
        ],
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in saved_arrays.items()},
    }
    (output / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/representation_09.json')
    parser.add_argument('--output', default='data/processed/representation_09')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    print(json.dumps({'results': len(report['results']), 'pretraining': len(report['pretraining'])}))


if __name__ == '__main__':
    main()
