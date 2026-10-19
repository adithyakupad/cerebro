"""Frozen M025 optimization comparison; historical experiments remain immutable."""

import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch

from cerebro.benchmark import array_digest, prepare, save_immutable, trial_metrics
from cerebro.dataset import verify_asset
from cerebro.event_audit import condition_keys
from cerebro.optimization_controls import predict_controls, train_controls
from cerebro.optimization_validation import validate_causality
from cerebro.sense import load_recording
from cerebro.sequence_benchmark import normalized_tensors, train_epoch
from cerebro.sequence_models import make_sequence_model


def read_json(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def losses(target, prediction, start=4):
    trial_loss, _ = trial_metrics(target[:, start:], prediction[:, start:])
    return trial_loss


def paired_summary(candidate, reference, draws=10000, seed=25, block=1):
    candidate = np.asarray(candidate)
    reference = np.asarray(reference)
    if candidate.ndim != 1 or candidate.shape != reference.shape or not len(candidate):
        raise ValueError('Paired losses require identical nonempty trial axes')
    difference = candidate - reference
    if not np.isfinite(difference).all():
        raise ValueError('Paired losses must be finite')
    generator = np.random.default_rng(seed)
    groups = []
    for first in range(0, len(difference), block):
        groups.append(difference[first:first + block])
    bootstrap_means = np.empty(draws)
    for draw in range(draws):
        selected = generator.integers(len(groups), size=len(groups))
        sampled_groups = [groups[index] for index in selected]
        sampled = np.concatenate(sampled_groups)
        bootstrap_means[draw] = sampled.mean()
    interval = np.quantile(bootstrap_means, [.025, .975])
    reference_mean = float(reference.mean())
    reduction = None
    if reference_mean > 0:
        reduction = float(1 - candidate.mean() / reference_mean)
    return {'difference_m2_s2': float(difference.mean()),
            'relative_reduction': reduction, 'paired_interval_95': interval.tolist(),
            'trial_wins': int(np.sum(difference < 0)), 'block_trials': block}


def check_committed_protocol(config_path, config):
    for name in (str(config_path), config['protocol']):
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + name])
        if hashlib.sha256(committed).hexdigest() != digest(name):
            raise ValueError('Protocol/config must be committed before training')


def recovery_evidence(development, config, output):
    path = 'docs/research/m025_recovery.json'
    evidence = read_json(path)
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + path])
    if hashlib.sha256(committed).hexdigest() != digest(path):
        raise ValueError('Recovery evidence must be committed')
    if evidence['development_report_sha256'] != digest('reports/m025_development.json'):
        raise ValueError('Recovery development lineage differs')
    if evidence['protocol_sha256'] != digest(config['protocol']):
        raise ValueError('Recovery scientific protocol differs')
    for name, expected in evidence['preserved_artifact_sha256'].items():
        if digest(output / name) != expected:
            raise ValueError('Preserved failed-attempt artifact changed: ' + name)
    old_hash = development['source_sha256']['optimization_study.py']
    if evidence['original_runner_sha256'] != old_hash:
        raise ValueError('Recovery original source differs')
    for name, expected in evidence['reviewed_source_sha256'].items():
        if digest(Path('src/cerebro') / name) != expected:
            raise ValueError('Reviewed recovery source differs: ' + name)
    return evidence


def authorize_final(development, eligibility, config, recovery=None):
    if development != read_json('reports/m025_development.json'):
        raise ValueError('Cached development differs from published gate evidence')
    if development['config'] != config or development['protocol_sha256'] != digest(config['protocol']):
        raise ValueError('Development protocol/config differs from frozen final recipe')
    for name, expected in development['source_sha256'].items():
        actual = digest(Path('src/cerebro') / name)
        if actual != expected:
            approved_validation_repair = recovery is not None and name == 'optimization_study.py'
            if not approved_validation_repair or recovery['reviewed_source_sha256'][name] != actual:
                raise ValueError('Implementation changed since development: ' + name)
    inner = development['inner_loss_by_cap']
    values = np.asarray([inner['20'], inner['200']], dtype=float)
    if not np.isfinite(values).all() or values[0] <= 0 or values[1] < 0:
        raise ValueError('Development gate losses must be finite and valid')
    reduction = 1 - inner['200'] / inner['20']
    if reduction < config['promotion_reduction'] or not development['development_gate_passed']:
        raise ValueError('Development promotion gate failed')
    if not eligibility['eligible_for_prospective_recipe_replication']:
        raise ValueError('Independent evaluation eligibility failed')
    if eligibility['asset'] != read_json(config['final_manifest']):
        raise ValueError('Final asset differs from independent eligibility audit')
    for name in ('reports/m025_development.json', 'docs/research/m025_evaluation_eligibility.json'):
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + name])
        if hashlib.sha256(committed).hexdigest() != digest(name):
            raise ValueError('Gate evidence must be committed before final access')


def cnn_experiment(counts, velocity, fitting, selecting, training, evaluating, config, output, recover=False):
    inner_features, inner_targets, inner_parameters = normalized_tensors(counts, velocity, fitting)
    full_features, full_targets, full_parameters = normalized_tensors(counts, velocity, training)
    rows = []
    predictions = {}
    start_bin = config['score_start_bin']
    deadline = time.perf_counter() + config['maximum_stage_seconds']
    for seed in config['seeds']:
        torch.manual_seed(seed)
        model = make_sequence_model('temporal_cnn', counts.shape[-1], config['hidden'], 2)
        optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
        history = []
        for epoch in range(max(config['epoch_caps'])):
            if time.perf_counter() > deadline:
                raise RuntimeError('CPU-day budget exceeded during selection')
            started = time.perf_counter()
            training_loss = train_epoch(model, optimizer, inner_features[fitting], inner_targets[fitting], config['gradient_clip'])
            model.eval()
            with torch.no_grad():
                selected_prediction = model(inner_features[selecting]).numpy()
            physical_prediction = selected_prediction * inner_parameters['target_scale']
            physical_prediction = physical_prediction + inner_parameters['target_mean']
            selection_loss = float(losses(velocity[selecting], physical_prediction, start_bin).mean())
            history.append({'epoch': epoch + 1, 'training_standardized_mse': training_loss,
                            'inner_physical_mse': selection_loss,
                            'seconds': time.perf_counter() - started})
        for cap in config['epoch_caps']:
            candidates = history[:cap]
            selected = min(candidates, key=lambda row: row['inner_physical_mse'])
            torch.manual_seed(seed)
            fitted = make_sequence_model('temporal_cnn', counts.shape[-1], config['hidden'], 2)
            name = 'cnn_' + str(cap) + '_seed_' + str(seed)
            checkpoint_path = output / (name + '.pt')
            reused_checkpoint = checkpoint_path.exists()
            if reused_checkpoint:
                if not recover:
                    raise ValueError('Existing checkpoint requires explicit recovery')
                saved = torch.load(checkpoint_path, weights_only=True, map_location='cpu')
                if saved['selected_epoch'] != selected['epoch'] or saved['seed'] != seed or saved['cap'] != cap:
                    raise ValueError('Recovered epoch selection differs; no replacement permitted')
                for key, value in full_parameters.items():
                    np.testing.assert_array_equal(saved['normalization'][key].numpy(), value)
                fitted.load_state_dict(saved['state_dict'])
                fit_seconds = 0.
            else:
                optimizer = torch.optim.Adam(fitted.parameters(), lr=config['learning_rate'])
                fit_started = time.perf_counter()
                for _ in range(selected['epoch']):
                    if time.perf_counter() > deadline:
                        raise RuntimeError('CPU-day budget exceeded during refitting')
                    train_epoch(fitted, optimizer, full_features[training], full_targets[training], config['gradient_clip'])
                fit_seconds = time.perf_counter() - fit_started
            fitted.eval()
            inference_started = time.perf_counter()
            with torch.no_grad():
                normalized_prediction = fitted(full_features[evaluating]).numpy()
            inference_seconds = time.perf_counter() - inference_started
            prediction = normalized_prediction * full_parameters['target_scale']
            prediction = prediction + full_parameters['target_mean']
            predictions[name] = prediction
            checkpoint = {'kind': 'temporal_cnn', 'input_units': counts.shape[-1], 'hidden': config['hidden'],
                          'output_coordinates': 2, 'seed': seed, 'cap': cap, 'selected_epoch': selected['epoch'],
                          'state_dict': copy.deepcopy(fitted.state_dict()),
                          'normalization': {key: torch.tensor(value) for key, value in full_parameters.items()}}
            if not reused_checkpoint:
                torch.save(checkpoint, checkpoint_path)
            restored = restore_cnn(checkpoint_path, counts[evaluating])
            np.testing.assert_array_equal(restored, prediction)
            causality = validate_causality(fitted, full_features[evaluating])
            rows.append({'name': name, 'seed': seed, 'cap': cap, 'selected_epoch': selected['epoch'],
                         'inner_selected_mse': selected['inner_physical_mse'], 'history': candidates,
                         'fit_seconds': fit_seconds, 'evaluation_forward_seconds': inference_seconds,
                         'checkpoint_sha256': digest(checkpoint_path), 'restoration_exact': True,
                         'prefix_causality_passed': causality['passed'], 'causality_validation': causality,
                         'checkpoint_reused': reused_checkpoint})
    return rows, predictions


def restore_cnn(path, counts):
    saved = torch.load(path, weights_only=True, map_location='cpu')
    model = make_sequence_model(saved['kind'], saved['input_units'], saved['hidden'], saved['output_coordinates'])
    model.load_state_dict(saved['state_dict'])
    model.eval()
    parameters = saved['normalization']
    normalized_counts = counts - parameters['feature_mean'].numpy()
    normalized_counts = normalized_counts / parameters['feature_scale'].numpy()
    features = torch.tensor(normalized_counts, dtype=torch.float32)
    with torch.no_grad():
        normalized_prediction = model(features).numpy()
    prediction = normalized_prediction * parameters['target_scale'].numpy()
    return prediction + parameters['target_mean'].numpy()


def condition_permutation(manifest, evaluation_ids, seed):
    # Read only trial metadata; use complete compatible-condition keys, not target values.
    from pynwb import NWBHDF5IO
    with NWBHDF5IO(manifest['local_path'], 'r') as reader:
        trials = reader.read().trials.to_dataframe()
    keys = condition_keys(trials.loc[evaluation_ids])
    generator = np.random.default_rng(seed)
    indices = np.arange(len(evaluation_ids))
    singleton_trials = 0
    for key in np.unique(keys):
        positions = np.flatnonzero(keys == key)
        if len(positions) == 1:
            singleton_trials += 1
        indices[positions] = generator.permutation(positions)
    return indices, singleton_trials


def load_stage(stage, config, output, recover=False):
    if stage == 'development':
        historical = read_json(config['development_report'])
        manifest = read_json(config['development_manifest'])
        verify_asset(Path(manifest['local_path']), manifest)
        with np.load(config['development_arrays'], allow_pickle=False) as archive:
            arrays = {name: archive[name] for name in archive.files}
        for name, metadata in historical['arrays'].items():
            if array_digest(arrays[name]) != metadata['sha256']:
                raise ValueError('Historical array digest mismatch: ' + name)
        data = {'counts': arrays['counts'], 'velocity': arrays['velocity_m_s'], 'trial_ids': arrays['trial_ids'],
                'unit_ids': arrays['unit_ids'], 'right_seconds': arrays['bin_right_seconds'], 'exclusions': []}
        splits = historical['splits']
    else:
        development = read_json('data/processed/m025_development/results.json')
        eligibility = read_json('docs/research/m025_evaluation_eligibility.json')
        recovery = recovery_evidence(development, config, output) if recover else None
        authorize_final(development, eligibility, config, recovery)
        manifest = read_json(config['final_manifest'])
        verify_asset(Path(manifest['local_path']), manifest)
        marker = output / ('recovery_started.json' if recover else 'final_started.json')
        with marker.open('x') as stream:
            json.dump({'asset_sha256': manifest['sha256'], 'protocol_sha256': digest(config['protocol'])}, stream)
        recording = load_recording(manifest['local_path'])
        preprocessing = read_json('configs/classical_05.json')
        data = prepare(recording, preprocessing)
        train_ids = data['trial_ids'][data['splits'] == 'train']
        validation_ids = data['trial_ids'][data['splits'] == 'val']
        screened = eligibility['timing_coverage_screen']['split_summary']
        for label, actual_ids in [('train', train_ids), ('val', validation_ids)]:
            allowed = set(screened[label]['timing_eligible_trial_ids'])
            if not set(actual_ids) <= allowed:
                raise ValueError('Execution trial IDs exceed independently screened partition')
        generator = np.random.default_rng(5)
        shuffled = generator.permutation(train_ids)
        validation_count = int(np.floor(.2 * len(train_ids)))
        splits = {'source_training': train_ids.tolist(), 'source_validation': validation_ids.tolist(),
                  'inner_validation': sorted(shuffled[:validation_count].tolist()),
                  'inner_training': sorted(shuffled[validation_count:].tolist())}
    save_immutable(output / 'split_manifest.json', splits)
    return data, splits, manifest


def run(stage, config_path='configs/m025_optimization.json', recover=False):
    config = read_json(config_path)
    check_committed_protocol(config_path, config)
    diagnostic = read_json('docs/research/m025_diagnostic_audit.json')
    expected_preprocessing = diagnostic['source_sha256']['configs/classical_05.json']
    if digest('configs/classical_05.json') != expected_preprocessing:
        raise ValueError('Historical preprocessing configuration changed')
    output = Path('data/processed/m025_' + stage)
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'results.json').exists():
        raise ValueError('Existing results are immutable; use --replay')
    started = time.perf_counter()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    if recover and stage != 'final':
        raise ValueError('Recovery applies only to the interrupted final stage')
    data, splits, manifest = load_stage(stage, config, output, recover)
    counts = data['counts'].astype(float)
    velocity = data['velocity']
    ids = data['trial_ids']
    masks = {}
    for role in ('inner_training', 'inner_validation', 'source_training', 'source_validation'):
        masks[role] = np.isin(ids, splits[role])
    if set(splits['source_training']) & set(splits['source_validation']):
        raise ValueError('Source split leakage')
    if set(splits['inner_training']) & set(splits['inner_validation']):
        raise ValueError('Inner split leakage')
    selected_controls = train_controls(counts[masks['inner_training']], velocity[masks['inner_training']],
                                      counts[masks['inner_validation']], velocity[masks['inner_validation']], config['ridge_alphas'])
    control_started = time.perf_counter()
    controls = train_controls(counts[masks['source_training']], velocity[masks['source_training']],
                              counts[masks['source_validation']], None, config['ridge_alphas'],
                              selected_alphas=selected_controls['selected_alphas'])
    control_seconds = time.perf_counter() - control_started
    controls_path = output / 'controls.npz'
    if recover:
        with np.load(controls_path, allow_pickle=False) as saved:
            for name, value in controls['parameters'].items():
                np.testing.assert_array_equal(saved[name], value)
    else:
        np.savez_compressed(controls_path, **controls['parameters'])
    cnn_rows, predictions = cnn_experiment(counts, velocity, masks['inner_training'], masks['inner_validation'],
                                          masks['source_training'], masks['source_validation'], config, output, recover)
    predictions.update(controls['predictions'])
    evaluation_counts = counts[masks['source_validation']]
    target = velocity[masks['source_validation']]
    arrays = {'target': target, 'counts': evaluation_counts, 'trial_ids': ids[masks['source_validation']],
              'unit_ids': data['unit_ids'], 'right_seconds': data['right_seconds'][masks['source_validation']]}
    metrics = {}
    for name, prediction in predictions.items():
        arrays[name] = prediction
        trial_loss = losses(target, prediction)
        _, r_squared = trial_metrics(target[:, 4:], prediction[:, 4:])
        metrics[name] = {'mse_m2_s2': float(trial_loss.mean()), 'trial_mse_m2_s2': trial_loss.tolist(),
                         'r2_by_coordinate': [float(value) if np.isfinite(value) else None for value in r_squared]}
        if name != 'history_ridge':
            metrics[name]['all70_mse_m2_s2'] = float(losses(target, prediction, start=0).mean())
    cap_losses = {}
    inner_losses = {}
    for cap in config['epoch_caps']:
        names = ['cnn_' + str(cap) + '_seed_' + str(seed) for seed in config['seeds']]
        seed_trial_losses = np.asarray([metrics[name]['trial_mse_m2_s2'] for name in names])
        cap_losses[cap] = seed_trial_losses.mean(axis=0)
        inner_losses[cap] = float(np.mean([row['inner_selected_mse'] for row in cnn_rows if row['cap'] == cap]))
    development_reduction = float(1 - inner_losses[200] / inner_losses[20])
    contrasts = {}
    reference_losses = {'cnn20': cap_losses[20], 'kalman': np.asarray(metrics['kalman']['trial_mse_m2_s2']),
                        'history_ridge': np.asarray(metrics['history_ridge']['trial_mse_m2_s2'])}
    for name, reference in reference_losses.items():
        contrasts[name] = paired_summary(cap_losses[200], reference, config['bootstrap_draws'], config['bootstrap_seed'])
        contrasts[name]['ordered_block5'] = paired_summary(cap_losses[200], reference, config['bootstrap_draws'], config['bootstrap_seed'], 5)
    practical = True
    for name in ('cnn20', 'kalman'):
        comparison = contrasts[name]
        practical = practical and comparison['relative_reduction'] >= config['practical_reduction'] and comparison['paired_interval_95'][1] < 0
    generator = np.random.default_rng(25)
    dropout_columns = np.sort(generator.choice(counts.shape[-1], size=int(.1 * counts.shape[-1]), replace=False))
    perturbed = evaluation_counts.copy()
    perturbed[:, :, dropout_columns] = controls['parameters']['scaler_mean'][dropout_columns]
    null_indices, singletons = condition_permutation(manifest, arrays['trial_ids'], 25)
    sensitivity = {}
    for label, altered in [('training_mean_feature_replacement', perturbed), ('within_condition_trial_permutation', evaluation_counts[null_indices])]:
        altered_predictions = predict_controls(controls['parameters'], altered)
        for row in cnn_rows:
            altered_predictions[row['name']] = restore_cnn(output / (row['name'] + '.pt'), altered)
        sensitivity[label] = {}
        for name, prediction in altered_predictions.items():
            sensitivity[label][name] = float(losses(target, prediction).mean())
            arrays[label + '_' + name] = prediction
    arrays['dropout_columns'] = dropout_columns
    arrays['null_permutation_indices'] = null_indices
    np.savez_compressed(output / 'predictions.npz', **arrays)
    elapsed = time.perf_counter() - started
    if elapsed > config['maximum_stage_seconds']:
        raise RuntimeError('Prespecified CPU-day budget exceeded; preserve partial files, no automatic retry')
    source_hashes = {}
    for name in ('optimization_study.py', 'optimization_controls.py', 'optimization_validation.py', 'sequence_models.py', 'sequence_benchmark.py', 'kalman.py', 'benchmark.py', 'sense.py'):
        source_hashes[name] = digest(Path('src/cerebro') / name)
    report = {'stage': stage, 'config': config, 'protocol_sha256': digest(config['protocol']),
              'explicit_pre_scoring_recovery': recover,
              'recovery_evidence_sha256': digest('docs/research/m025_recovery.json') if recover else None,
              'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'source_sha256': source_hashes, 'asset': manifest, 'splits': splits, 'exclusions': data['exclusions'],
              'counts_shape': list(counts.shape), 'target_shape': list(velocity.shape), 'cnn': cnn_rows,
              'controls_selection': selected_controls['selection'], 'selected_alphas': selected_controls['selected_alphas'],
              'metrics': metrics, 'inner_loss_by_cap': inner_losses, 'development_relative_reduction': development_reduction,
              'development_gate_passed': development_reduction >= config['promotion_reduction'],
              'contrasts': contrasts, 'practical_gate_passed_on_this_stage': bool(practical),
              'sensitivity': sensitivity, 'null_singleton_trials': singletons,
              'null_changed_trials': int(np.sum(null_indices != np.arange(len(null_indices)))),
              'seconds_total': elapsed, 'control_refit_seconds': control_seconds,
              'versions': {name: importlib.metadata.version(name) for name in ('numpy', 'torch', 'scikit-learn', 'pynwb')},
              'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in arrays.items()},
              'files': {path.name: digest(path) for path in output.iterdir() if path.suffix in ('.npz', '.pt')},
              'limitations': ['Development gate is selection-conditioned', 'Small outer25 previously inspected',
                              'Same-bin offline reconstruction; no future neural or behavioral inputs',
                              'Trial uncertainty conditional on fixed models and one animal/session',
                              'Session-specific models are not cross-session transfer', 'No new architecture or physiological mechanism claim']}
    (output / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    render(report)
    return report


def replay(stage):
    output = Path('data/processed/m025_' + stage)
    report = read_json(output / 'results.json')
    for name, expected in report['files'].items():
        if digest(output / name) != expected:
            raise ValueError('Artifact digest mismatch: ' + name)
    with np.load(output / 'predictions.npz', allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    for name, metadata in report['arrays'].items():
        if array_digest(arrays[name]) != metadata['sha256']:
            raise ValueError('Array digest mismatch: ' + name)
    with np.load(output / 'controls.npz', allow_pickle=False) as archive:
        parameters = {name: archive[name] for name in archive.files}
    predictions = predict_controls(parameters, arrays['counts'])
    for row in report['cnn']:
        predictions[row['name']] = restore_cnn(output / (row['name'] + '.pt'), arrays['counts'])
    for name, prediction in predictions.items():
        np.testing.assert_array_equal(prediction, arrays[name])
    render(report)
    return {'stage': stage, 'restored_models': len(predictions), 'array_digests': len(arrays), 'exact': True}


def render(report):
    stage = report['stage']
    figures = Path('reports/figures')
    figures.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for row in report['cnn']:
        if row['cap'] == 200:
            epochs = [entry['epoch'] for entry in row['history']]
            curve = [entry['inner_physical_mse'] for entry in row['history']]
            axes[0].plot(epochs, curve, label='Seed ' + str(row['seed']))
    axes[0].axvline(20, color='black', linestyle='--')
    axes[0].set(xlabel='Full-batch optimizer updates', ylabel='Inner velocity MSE [(m/s)²]', title='Selection-conditioned development curves')
    axes[0].legend()
    names = ['mean', 'go_time_template', 'ridge', 'history_ridge', 'kalman']
    values = [report['metrics'][name]['mse_m2_s2'] for name in names]
    for cap in (20, 200):
        seed_values = [row['mse_m2_s2'] for name, row in report['metrics'].items() if name.startswith('cnn_' + str(cap) + '_seed_')]
        names.append('CNN ' + str(cap))
        values.append(float(np.mean(seed_values)))
    axes[1].bar(np.arange(len(names)), values)
    axes[1].set(xticks=np.arange(len(names)), xticklabels=names, ylabel='Equal-trial MSE [(m/s)²]', title=stage + ': same bins 5–70')
    axes[1].tick_params(axis='x', rotation=60)
    fig.suptitle('M025 | Jenkins | ' + report['asset']['dandiset'] + ' | go −400:+1000 ms, 20 ms bins')
    fig.savefig(figures / ('m025_' + stage + '.pdf'))
    plt.close(fig)
    lines = ['# M025 ' + stage + ' optimization experiment', '',
             'Protocol SHA256: `' + report['protocol_sha256'] + '`.',
             'Development promotion: **' + str(report['development_gate_passed']) + '**; reduction ' + str(report['development_relative_reduction']) + '.',
             'This gate uses epoch-selection trials and is not independent evidence.', '',
             '| Model | Equal-trial MSE (m/s)² |', '| --- | ---: |']
    for name, value in zip(names, values):
        lines.append('| ' + name + ' | ' + format(value, '.10f') + ' |')
    lines.extend(['', '## Paired CNN200 contrasts', '', '| Reference | Absolute difference | Relative reduction | Trial-bootstrap 95% interval |', '| --- | ---: | ---: | --- |'])
    for name, row in report['contrasts'].items():
        lines.append('| ' + name + ' | ' + str(row['difference_m2_s2']) + ' | ' + str(row['relative_reduction']) + ' | ' + str(row['paired_interval_95']) + ' |')
    lines.extend(['', 'CPU elapsed seconds: ' + str(report['seconds_total']) + '.', '', '## Interpretation', '',
                  'A final-epoch choice does not establish undertraining. A development gain does not establish independent improvement.',
                  'Previously inspected Small outer trials are exploratory; final eligibility is audited separately.',
                  'No cross-subject, physiological cause, live BCI or foundation-model conclusion follows.', '',
                  '## Reproduction', '', '`conda run -n cerebro python -m cerebro.optimization_study --stage ' + stage + ' --replay`', '',
                  'Authentic source data and ignored checkpoints/arrays are required. Replay verifies hashes and restores predictions without fitting.'])
    Path('reports/m025_' + stage + '.md').write_text('\n'.join(lines) + '\n')
    Path('reports/m025_' + stage + '.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['development', 'final'], default='development')
    parser.add_argument('--replay', action='store_true')
    parser.add_argument('--recover-final', action='store_true', help='Reviewed pre-scoring recovery; preserves original marker and checkpoints')
    arguments = parser.parse_args()
    if arguments.replay:
        torch.set_num_threads(1)
        result = replay(arguments.stage)
    else:
        result = run(arguments.stage, recover=arguments.recover_final)
    print(json.dumps({'stage': arguments.stage, 'replay': arguments.replay, 'result': result.get('development_gate_passed', result)}, default=str))


if __name__ == '__main__':
    main()
