"""Calibration-only M023 risk features and entire-session-held-out prediction."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest
from cerebro.calibration_mechanisms import development_split
from cerebro.link import align_channel_keys, load_link
from cerebro.longitudinal import flatten, trial_losses
from cerebro.population import fit_decoder
from cerebro.research_dynamics import fitted_source, projection_errors


FEATURES = ['command_coverage', 'bootstrap_instability', 'neural_shift', 'decoder_disagreement',
            'label_mean_index', 'label_mean_mrs', 'label_variance_index', 'label_variance_mrs', 'dynamics_mismatch']
MODELS = {'coverage': [0], 'instability': [1], 'shift': [2], 'disagreement': [3],
          'combined': [0, 1, 2, 3], 'label_only': [4, 5, 6, 7],
          'task_control': [0, 4, 5, 6, 7], 'task_plus_dynamics': [0, 4, 5, 6, 7, 8]}


def calibration_features(selected, probe_counts, source_scaler, source_decoder,
                         source_position, source_commands, neural_model, source_neural_loss,
                         bootstrap_draws, seed, order=None):
    """No evaluation argument exists: resample only selected labeled trials."""
    counts = flatten(selected, 'counts', order)
    position = flatten(selected, 'position')
    features = source_scaler.transform(counts)
    probe_features = source_scaler.transform(probe_counts)
    direct = fit_decoder(features, position, alpha=1000.)
    direct_probe = direct.predict(probe_features)
    frozen_probe = source_decoder.predict(probe_features)
    generator = np.random.default_rng(seed)
    bootstrap_predictions = []
    bootstrap_ids = []
    for _ in range(bootstrap_draws):
        rows = generator.integers(len(selected), size=len(selected))
        sampled_trials = [selected[index] for index in rows]
        sampled_counts = flatten(sampled_trials, 'counts', order)
        sampled_position = flatten(sampled_trials, 'position')
        decoder = fit_decoder(source_scaler.transform(sampled_counts), sampled_position, alpha=1000.)
        bootstrap_predictions.append(decoder.predict(probe_features))
        bootstrap_ids.append(rows.tolist())
    prediction_variance = np.var(bootstrap_predictions, axis=0, ddof=0)
    commands = {tuple(trial['target']) for trial in selected}
    coverage = len(commands) / source_commands
    instability = float(prediction_variance.mean())
    neural_mean = features.mean(axis=0)
    shift = float(np.mean(neural_mean ** 2))
    disagreement = float(np.mean((direct_probe - frozen_probe) ** 2))
    label_mean_difference = position.mean(axis=0) - source_position.mean(axis=0)
    label_variance_difference = position.var(axis=0) - source_position.var(axis=0)
    neural_loss = projection_errors(neural_model, selected, order=order).mean()
    mismatch = float(neural_loss / source_neural_loss)
    values = [coverage, instability, shift, disagreement]
    values.extend(label_mean_difference.tolist())
    values.extend(label_variance_difference.tolist())
    values.append(mismatch)
    if not np.isfinite(values).all():
        raise ValueError('Calibration features must be finite')
    return np.asarray(values), direct, bootstrap_ids


def balanced_accuracy(labels, predictions, weights=None):
    labels = np.asarray(labels, dtype=bool)
    predictions = np.asarray(predictions, dtype=bool)
    if labels.shape != predictions.shape or labels.ndim != 1:
        raise ValueError('Matching one-dimensional class arrays required')
    if weights is None:
        weights = np.ones(len(labels))
    recalls = []
    for value in (False, True):
        mask = labels == value
        if not mask.any():
            return None
        recall = np.average(predictions[mask] == labels[mask], weights=np.asarray(weights)[mask])
        recalls.append(recall)
    return float(np.mean(recalls))


def session_folds(sessions):
    sessions = np.asarray(sessions)
    identities = sorted(set(sessions))
    if len(identities) < 3:
        raise ValueError('At least three entire development sessions required')
    for identity in identities:
        testing = np.flatnonzero(sessions == identity)
        training = np.flatnonzero(sessions != identity)
        yield identity, training, testing


def fit_risk(training_features, outcomes, columns, alpha=1.):
    selected = training_features[:, columns]
    scaler = StandardScaler().fit(selected)
    normalized = scaler.transform(selected)
    decoder = fit_decoder(normalized, np.asarray(outcomes)[:, None], alpha=alpha)
    return scaler, decoder


def predict_risk(model, values, columns):
    scaler, decoder = model
    selected = values[:, columns]
    prediction = decoder.predict(scaler.transform(selected))
    return prediction.reshape(-1)


def conditional_risk_interval(predictions, controls, trial_differences, session_ids, config):
    """Shared trial blocks across subsets; fitted risk parameters remain fixed."""
    generator = np.random.default_rng(config['random_seed'])
    session_changes = []
    for session in sorted(set(session_ids)):
        rows = np.flatnonzero(session_ids == session)
        values = trial_differences[rows]
        trial_count = values.shape[1]
        block_size = config['bootstrap_block_trials']
        block_count = int(np.ceil(trial_count / block_size))
        if trial_count < block_size:
            raise ValueError('Insufficient whole trials for moving-block resampling')
        starts = generator.integers(trial_count - block_size + 1,
                                   size=(config['bootstrap_draws'], block_count))
        indices = starts[:, :, None] + np.arange(block_size)
        indices = indices.reshape(config['bootstrap_draws'], -1)[:, :trial_count]
        outcome_draws = values[:, indices].mean(axis=2)
        prediction_error = predictions[rows, None] - outcome_draws
        control_error = controls[rows, None] - outcome_draws
        session_changes.append(np.mean(prediction_error ** 2 - control_error ** 2, axis=0))
    equal_session_changes = np.mean(session_changes, axis=0)
    return np.quantile(equal_session_changes, [.025, .975]).tolist()


def evaluate_risk(rows, config):
    """Train scalers and risk targets on other dates; subsets never define folds."""
    all_results = {}
    arrays = {}
    for budget in config['budgets']:
        uniform = [row for row in rows if row['budget'] == budget and row['policy'] == 'uniform']
        features = np.asarray([row['features'] for row in uniform])
        trial_differences = np.asarray([row['trial_difference'] for row in uniform])
        outcomes = trial_differences.mean(axis=1)
        sessions = np.asarray([row['session'] for row in uniform])
        predictions = {name: np.empty(len(uniform)) for name in MODELS}
        predictions.update({name: np.empty(len(uniform)) for name in ('constant', 'permuted_combined')})
        majority = np.empty(len(uniform), dtype=bool)
        stability = {name: [] for name in MODELS}
        secondary_predictions = {name: {} for name in MODELS}
        folds = []
        for fold_index, (identity, training, testing) in enumerate(session_folds(sessions)):
            train_sessions = sorted(set(sessions[training]))
            counts = [np.sum(sessions[training] == value) for value in train_sessions]
            if len(set(counts)) != 1:
                raise ValueError('Equal-session training requires equal allocation counts')
            predictions['constant'][testing] = outcomes[training].mean()
            majority[testing] = np.mean(outcomes[training] > 0) > .5
            folds.append({'held_out_session': str(identity), 'training_sessions': list(train_sessions),
                          'training_rows': training.tolist(), 'testing_rows': testing.tolist()})
            for name, columns in MODELS.items():
                model = fit_risk(features[training], outcomes[training], columns, config['reliability_ridge_alpha'])
                predictions[name][testing] = predict_risk(model, features[testing], columns)
                prefix = f'b{budget}_{identity}_{name}'
                scaler, decoder = model
                arrays[prefix + '_mean'] = scaler.mean_
                arrays[prefix + '_scale'] = scaler.scale_
                arrays[prefix + '_coef'] = decoder.coef_
                arrays[prefix + '_intercept'] = decoder.intercept_
                single_session_predictions = []
                for training_session in train_sessions:
                    single_rows = np.flatnonzero(sessions == training_session)
                    single = fit_risk(features[single_rows], outcomes[single_rows], columns, config['reliability_ridge_alpha'])
                    single_session_predictions.append(predict_risk(single, features[testing], columns))
                instability = np.var(single_session_predictions, axis=0).mean()
                stability[name].append(float(instability))
                secondary = [row for row in rows if row['session'] == identity and row['budget'] == budget and row['policy'] != 'uniform']
                values = np.asarray([row['features'] for row in secondary])
                secondary_predictions[name][str(identity)] = {
                    'policies': [row['policy'] for row in secondary],
                    'predicted_difference': predict_risk(model, values, columns).tolist(),
                    'observed_difference': [float(np.mean(row['trial_difference'])) for row in secondary],
                }
            generator = np.random.default_rng(config['random_seed'] + budget + fold_index)
            permuted_outcomes = outcomes[training].copy()
            for identity_train in train_sessions:
                positions = np.flatnonzero(sessions[training] == identity_train)
                permuted_outcomes[positions] = generator.permutation(permuted_outcomes[positions])
            null_model = fit_risk(features[training], permuted_outcomes, MODELS['combined'])
            predictions['permuted_combined'][testing] = predict_risk(null_model, features[testing], MODELS['combined'])
        metrics = {}
        for name, prediction in predictions.items():
            per_session = []
            for identity in sorted(set(sessions)):
                mask = sessions == identity
                predicted = prediction[mask]
                actual = outcomes[mask]
                selected = predicted < 0
                subset_rows = [uniform[index] for index in np.flatnonzero(mask)]
                frozen_losses = np.asarray([row['frozen_mse'] for row in subset_rows])
                policy_losses = frozen_losses + np.where(selected, actual, 0.)
                per_session.append({'session': str(identity), 'risk_mse_flexion4': float(np.mean((predicted - actual) ** 2)),
                                    'harm_fraction': float(np.mean(actual > 0)),
                                    'balanced_accuracy': balanced_accuracy(actual > 0, predicted > 0),
                                    'policy_mse_flexion2': float(policy_losses.mean()),
                                    'always_frozen_mse_flexion2': float(frozen_losses.mean()),
                                    'always_direct_mse_flexion2': float(np.mean(frozen_losses + actual)),
                                    'adapt_fraction': float(selected.mean())})
            metrics[name] = {'risk_mse_flexion4': float(np.mean([row['risk_mse_flexion4'] for row in per_session])),
                             'pooled_session_weighted_balanced_accuracy': balanced_accuracy(outcomes > 0, prediction > 0),
                             'per_session': per_session, 'predicted_differences': prediction.tolist(),
                             'training_date_only_prediction_dispersion': stability.get(name),
                             'secondary_allocations': secondary_predictions.get(name)}
            arrays[f'b{budget}_{name}_predictions'] = prediction
        comparisons = {}
        for name in MODELS:
            comparisons[name] = {}
            for control in ('constant', 'label_only', 'shift'):
                baseline = metrics[control]['risk_mse_flexion4']
                error = metrics[name]['risk_mse_flexion4']
                interval = conditional_risk_interval(predictions[name], predictions[control], trial_differences, sessions, config)
                lower_each = all(left['risk_mse_flexion4'] < right['risk_mse_flexion4']
                                 for left, right in zip(metrics[name]['per_session'], metrics[control]['per_session']))
                relative = None if baseline == 0 else 1 - error / baseline
                passed = relative is not None and relative >= config['practical_relative_improvement'] and lower_each and interval[1] < 0
                comparisons[name][control] = {'relative_risk_mse_improvement': relative,
                                              'lower_on_every_date': lower_each,
                                              'conditional_paired_risk_mse_interval': interval, 'passed': passed}
        all_results[str(budget)] = {'models': metrics, 'comparisons': comparisons, 'folds': folds,
                                    'majority_balanced_accuracy': balanced_accuracy(outcomes > 0, majority),
                                    'majority_predictions': majority.tolist(), 'outcomes': outcomes.tolist(),
                                    'sessions': sessions.tolist()}
        arrays[f'b{budget}_features'] = features
        arrays[f'b{budget}_trial_differences'] = trial_differences
    primary = all_results[str(config['primary_budget'])]
    gate = []
    selected_method = None
    for name in ('disagreement', 'coverage', 'instability', 'combined'):
        accuracy = primary['models'][name]['pooled_session_weighted_balanced_accuracy']
        passed = all(row['passed'] for row in primary['comparisons'][name].values())
        passed = passed and accuracy is not None and accuracy >= config['minimum_balanced_accuracy']
        gate.append({'candidate': name, 'balanced_accuracy': accuracy, 'passed': passed})
        if passed and selected_method is None:
            selected_method = name
    return {'budgets': all_results, 'promotion': gate, 'selected_method': selected_method}, arrays


def run(config_path='configs/m023_protocol.json', output='data/processed/m023_reliability'):
    config = json.loads(Path(config_path).read_text())
    historical = json.loads(Path('data/processed/m022_calibration_verified/results.json').read_text())
    published = json.loads(Path('reports/m022_calibration_mechanisms.json').read_text())
    if historical['lineage'] != published['lineage'] or historical['config'] != published['config']:
        raise ValueError('M022 allocation or configuration lineage changed')
    for name, entry in published['arrays'].items():
        if historical['arrays'][name] != entry:
            raise ValueError('M022 numerical provenance changed')
    source_manifest = json.loads(Path(config['source_manifest']).read_text())
    source = load_link(source_manifest)
    source_trials = source['trials'][:config['source_training_trials']]
    source_counts = flatten(source_trials, 'counts')
    source_position = flatten(source_trials, 'position')
    source_scaler = StandardScaler().fit(source_counts)
    source_decoder = fit_decoder(source_scaler.transform(source_counts), source_position, alpha=1000.)
    if historical['selected_source_alpha'] != 1000:
        raise ValueError('Frozen source ridge selection differs')
    for name, values in [('source_coef', source_decoder.coef_), ('source_intercept', source_decoder.intercept_)]:
        if array_digest(values) != historical['arrays'][name]['sha256']:
            raise ValueError('Frozen source decoder restoration differs')
    neural_model = fitted_source(source_trials, dimension=config['primary_dimension'], seed=config['random_seed'])
    source_neural_loss = projection_errors(neural_model, source_trials).mean()
    source_commands = len({tuple(trial['target']) for trial in source_trials})
    rows = []
    for manifest_path in config['development_manifests']:
        manifest = json.loads(Path(manifest_path).read_text())
        target = load_link(manifest)
        session = manifest['asset_path'].split('ses-')[1][:8]
        pool, evaluation = development_split(target, config['permitted_trial_rows'], config['allocation_pool_trials'])
        order = align_channel_keys(source['channel_keys'], target['channel_keys'])
        probe_counts = flatten(pool, 'counts', order)
        evaluation_counts = flatten(evaluation, 'counts', order)
        evaluation_features = source_scaler.transform(evaluation_counts)
        frozen_prediction = source_decoder.predict(evaluation_features)
        frozen_losses = trial_losses(evaluation, frozen_prediction)
        original_session = next(item for item in historical['sessions'] if item['session'] == session)
        session_allocations = [row for row in historical['lineage']['allocations'] if row['session'] == session]
        for allocation_index, allocation in enumerate(session_allocations):
            selected = [pool[index] for index in allocation['pool_indices']]
            values, direct, resampling = calibration_features(
                selected, probe_counts, source_scaler, source_decoder, source_position,
                source_commands, neural_model, source_neural_loss,
                config['within_budget_bootstrap_draws'], config['random_seed'] + len(rows), order)
            direct_prediction = direct.predict(evaluation_features)
            direct_losses = trial_losses(evaluation, direct_prediction)
            group = next(item for item in original_session['groups'] if item['budget'] == allocation['budget'] and item['policy'] == allocation['policy'])
            original_losses = group['models']['direct_1']['subset_trial_mse'][allocation['draw']]
            if not np.array_equal(direct_losses, original_losses):
                raise ValueError('M022 stored outcomes do not reproduce exactly')
            rows.append({**allocation, 'features': values.tolist(),
                         'within_selected_trial_indices': resampling,
                         'frozen_mse': float(frozen_losses.mean()),
                         'trial_difference': (direct_losses - frozen_losses).tolist(),
                         'information': {'labeled_position_trials': len(selected), 'command_trials': len(selected),
                                         'unlabeled_probe_neural_trials': len(pool)},
                         'source_asset_sha256': source_manifest['sha256'], 'target_asset_sha256': manifest['sha256']})
        print('Completed calibration-only features ' + session, flush=True)
    evaluation, arrays = evaluate_risk(rows, config)
    arrays['all_features'] = np.asarray([row['features'] for row in rows])
    result = {'schema_version': 1, 'config': config, 'feature_names': FEATURES, 'model_columns': MODELS,
              'rows': rows, 'evaluation': evaluation, 'source_neural_training_error': float(source_neural_loss),
              'source_manifest': source_manifest, 'source_training_trials': [trial['trial_id'] for trial in source_trials],
              'source_array_restoration': 'Exact M022 source coefficients/intercept and every direct outcome',
              'protocol_sha256': hashlib.sha256(Path('docs/research/m023_protocol.md').read_bytes()).hexdigest(),
              'config_sha256': hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
              'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
              'source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                for name in ('reliability.py', 'research_dynamics.py', 'calibration_mechanisms.py', 'population.py', 'link.py')},
              'versions': {name: importlib.metadata.version(name) for name in ('numpy', 'scikit-learn', 'pynwb')},
              'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in arrays.items()}}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'arrays.npz', **arrays)
    (output / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/m023_protocol.json')
    parser.add_argument('--output', default='data/processed/m023_reliability')
    arguments = parser.parse_args()
    results = run(arguments.config, arguments.output)
    print(json.dumps(results['evaluation']['promotion'], indent=2))
