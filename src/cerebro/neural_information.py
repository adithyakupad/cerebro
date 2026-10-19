"""M026 retrospective neural-information controls; no historical model refitting."""

import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

import numpy as np
import torch

from cerebro.benchmark import array_digest
from cerebro.neural_information_controls import condition_donors, condition_template, input_features, stratified_summary
from cerebro.optimization_study import check_committed_protocol, digest, losses, paired_summary, read_json, restore_cnn
from cerebro.sequence_benchmark import normalized_tensors, train_epoch
from cerebro.sequence_models import make_sequence_model


def checked_inputs(config):
    output = Path(config['output'])
    lineage = read_json(output / 'inputs.json')
    if lineage['cache_sha256'] != digest(output / 'inputs.npz'):
        raise ValueError('Input cache checksum differs')
    for key, path in [('protocol_sha256', config['protocol']), ('m025_report_sha256', config['m025_report']), ('preprocessing_sha256', config['preprocessing'])]:
        if lineage[key] != digest(path):
            raise ValueError('Input lineage differs: ' + key)
    with np.load(output / 'inputs.npz', allow_pickle=False) as archive:
        arrays = dict(archive)
    for name, values in arrays.items():
        if array_digest(values) != lineage['arrays'][name]['sha256']:
            raise ValueError('Input array differs: ' + name)
    original = read_json(config['m025_report'])
    ids = arrays['trial_ids']
    groups = {}
    for role, identities in original['splits'].items():
        groups[role] = np.flatnonzero(np.isin(ids, identities))
        if ids[groups[role]].tolist() != sorted(identities):
            raise ValueError('Trial identity/order differs: ' + role)
    if set(groups['source_training']) & set(groups['source_validation']):
        raise ValueError('Source split overlap')
    if set(groups['inner_training']) & set(groups['inner_validation']):
        raise ValueError('Inner split overlap')
    inner_union = np.union1d(groups['inner_training'], groups['inner_validation'])
    np.testing.assert_array_equal(inner_union, groups['source_training'])
    return arrays, groups, original, lineage


def control_counts(counts, keys, groups, mode, seed):
    if mode != 'permuted':
        values = input_features(counts, mode)
        return values, values, {}
    inner = counts.copy()
    full = counts.copy()
    mappings = {}
    for role in ('inner_training', 'inner_validation', 'source_training', 'source_validation'):
        recipients = groups[role]
        donors = condition_donors(keys, recipients, seed)
        destination = inner if role.startswith('inner_') else full
        destination[recipients] = counts[donors]
        mappings[role] = {'recipients': recipients.tolist(), 'donors': donors.tolist(),
                          'unchanged': int(np.sum(recipients == donors))}
    return inner, full, mappings


def fit_seed(counts, velocity, keys, groups, mode, seed, config, output):
    inner_counts, full_counts, mappings = control_counts(counts, keys, groups, mode, config['donor_seed'])
    fitting = groups['inner_training']
    selecting = groups['inner_validation']
    training = groups['source_training']
    evaluating = groups['source_validation']
    inner_features, inner_targets, inner_parameters = normalized_tensors(inner_counts, velocity, fitting)
    full_features, full_targets, full_parameters = normalized_tensors(full_counts, velocity, training)
    torch.manual_seed(seed)
    model = make_sequence_model('temporal_cnn', counts.shape[2], config['hidden'], 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    history = []
    for epoch in range(config['maximum_epochs']):
        started = time.perf_counter()
        training_loss = train_epoch(model, optimizer, inner_features[fitting], inner_targets[fitting], config['gradient_clip'])
        model.eval()
        with torch.no_grad():
            normalized_prediction = model(inner_features[selecting]).numpy()
        physical_prediction = normalized_prediction * inner_parameters['target_scale']
        physical_prediction = physical_prediction + inner_parameters['target_mean']
        selection_loss = float(losses(velocity[selecting], physical_prediction).mean())
        history.append({'epoch': epoch + 1, 'training_standardized_mse': training_loss,
                        'inner_physical_mse': selection_loss, 'seconds': time.perf_counter() - started})
    selected = min(history, key=lambda row: row['inner_physical_mse'])
    torch.manual_seed(seed)
    fitted = make_sequence_model('temporal_cnn', counts.shape[2], config['hidden'], 2)
    optimizer = torch.optim.Adam(fitted.parameters(), lr=config['learning_rate'])
    fit_started = time.perf_counter()
    for _ in range(selected['epoch']):
        train_epoch(fitted, optimizer, full_features[training], full_targets[training], config['gradient_clip'])
    fit_seconds = time.perf_counter() - fit_started
    fitted.eval()
    inference_started = time.perf_counter()
    with torch.no_grad():
        normalized_prediction = fitted(full_features[evaluating]).numpy()
    inference_seconds = time.perf_counter() - inference_started
    prediction = normalized_prediction * full_parameters['target_scale']
    prediction = prediction + full_parameters['target_mean']
    name = mode + '_seed_' + str(seed)
    checkpoint = {'kind': 'temporal_cnn', 'input_units': counts.shape[2], 'hidden': config['hidden'],
                  'output_coordinates': 2, 'state_dict': copy.deepcopy(fitted.state_dict()),
                  'normalization': {key: torch.tensor(value) for key, value in full_parameters.items()},
                  'seed': seed, 'selected_epoch': selected['epoch'], 'control_mode': mode}
    checkpoint_path = output / (name + '.pt')
    torch.save(checkpoint, checkpoint_path)
    restored = restore_cnn(checkpoint_path, full_counts[evaluating])
    np.testing.assert_array_equal(restored, prediction)
    predictions = {name: prediction}
    if mode == 'permuted':
        predictions['permuted_real_seed_' + str(seed)] = restore_cnn(checkpoint_path, counts[evaluating])
    row = {'name': name, 'mode': mode, 'seed': seed, 'selected_epoch': selected['epoch'],
           'history': history, 'fit_seconds': fit_seconds, 'evaluation_forward_seconds': inference_seconds,
           'parameters': sum(parameter.numel() for parameter in fitted.parameters()),
           'checkpoint_sha256': digest(checkpoint_path), 'restoration_exact': True,
           'mapping': mappings}
    return row, predictions


def families(predictions):
    result = {}
    for name, prediction in predictions.items():
        family = name.split('_seed_')[0]
        result.setdefault(family, []).append(prediction)
    return result


def summarize(target, predictions, keys, config):
    metrics = {}
    family_losses = {}
    strata = {}
    for family, values in families(predictions).items():
        seed_losses = np.asarray([losses(target, prediction) for prediction in values])
        trial_loss = seed_losses.mean(axis=0)
        family_losses[family] = trial_loss
        metrics[family] = {'mse_m2_s2': float(trial_loss.mean()), 'seed_mse_m2_s2': seed_losses.mean(axis=1).tolist(),
                           'trial_mse_m2_s2': trial_loss.tolist()}
        scored_target = target[:, config['score_start_bin']:, :]
        seed_strata = []
        for prediction in values:
            scored_prediction = prediction[:, config['score_start_bin']:, :]
            seed_strata.append(stratified_summary(scored_target, scored_prediction, keys, start=0))
        combined = copy.deepcopy(seed_strata[0])
        for dimension, groups in combined.items():
            for label, row in groups.items():
                values_by_seed = [entry[dimension][label]['trial_mse'] for entry in seed_strata]
                if row['num_trials']:
                    trial_values = np.asarray(values_by_seed).mean(axis=0)
                    row['trial_mse'] = trial_values.tolist()
                    row['equal_trial_mse'] = float(trial_values.mean())
        strata[family] = combined
    contrasts = {}
    for name, reference in family_losses.items():
        if name == 'neural_200':
            continue
        contrast = paired_summary(family_losses['neural_200'], reference, config['bootstrap_draws'], config['bootstrap_seed'])
        contrast['ordered_block5'] = paired_summary(family_losses['neural_200'], reference, config['bootstrap_draws'], config['bootstrap_seed'], 5)
        contrasts[name] = contrast
    supported = all(contrasts[name]['relative_reduction'] is not None and contrasts[name]['relative_reduction'] >= config['descriptive_reduction'] and contrasts[name]['paired_interval_95'][1] < 0 for name in ('clock', 'permuted'))
    return {'metrics': metrics, 'contrasts': contrasts, 'stratification': strata,
            'primary_descriptive_support': bool(supported)}


def preserve_original(config):
    paths = list(Path(config['m025_directory']).glob('*'))
    paths += [Path(config['m025_report']), Path('reports/m025_development.json')]
    return {str(path): digest(path) for path in paths if path.is_file()}


def run(config_path='configs/m026_neural_information.json'):
    config = read_json(config_path)
    check_committed_protocol(config_path, config)
    sources = ['src/cerebro/neural_information.py', 'src/cerebro/neural_information_controls.py',
               'src/cerebro/sequence_models.py', 'src/cerebro/sequence_benchmark.py',
               'src/cerebro/optimization_study.py', 'src/cerebro/benchmark.py',
               'src/cerebro/sense.py', 'src/cerebro/event_audit.py']
    for name in sources:
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + name])
        if committed != Path(name).read_bytes():
            raise ValueError('Scientific implementation must be committed: ' + name)
    output = Path(config['output'])
    with (output / 'started.json').open('x') as stream:
        json.dump({'protocol_sha256': digest(config['protocol'])}, stream)
    started = time.perf_counter()
    protected = preserve_original(config)
    arrays, groups, original, lineage = checked_inputs(config)
    for name, expected in original['files'].items():
        if digest(Path(config['m025_directory']) / name) != expected:
            raise ValueError('Original M025 artifact checksum differs: ' + name)
    counts = arrays['counts'].astype(float)
    target = arrays['velocity']
    keys = arrays['conditions']
    evaluating = groups['source_validation']
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    predictions = {}
    rows = []
    for mode in config['models']:
        for seed in config['seeds']:
            row, fitted_predictions = fit_seed(counts, target, keys, groups, mode, seed, config, output)
            rows.append(row)
            predictions.update(fitted_predictions)
            (output / 'training_progress.json').write_text(json.dumps(rows, indent=2) + '\n')
    with np.load(Path(config['m025_directory']) / 'predictions.npz', allow_pickle=False) as old:
        for seed in config['seeds']:
            for cap in (20, 200):
                predictions['neural_' + str(cap) + '_seed_' + str(seed)] = old['cnn_' + str(cap) + '_seed_' + str(seed)]
        for name in ('kalman', 'history_ridge', 'mean', 'go_time_template'):
            predictions[name] = old[name]
    training = groups['source_training']
    template, fallback = condition_template(target[training], keys[training], keys[evaluating])
    predictions['condition_template'] = template
    summary = summarize(target[evaluating], predictions, keys[evaluating], config)
    summary['condition_support'] = {}
    for label, mask in [('seen_in_training', ~fallback), ('unseen_in_training', fallback)]:
        summary['condition_support'][label] = {'trials': int(mask.sum()), 'mse_m2_s2': {}}
        if mask.any():
            for name, metric in summary['metrics'].items():
                trial_values = np.asarray(metric['trial_mse_m2_s2'])
                summary['condition_support'][label]['mse_m2_s2'][name] = float(trial_values[mask].mean())
    for path, expected in protected.items():
        if digest(path) != expected:
            raise ValueError('Historical artifact changed: ' + path)
    saved_arrays = dict(predictions)
    saved_arrays.update({'target': target[evaluating], 'trial_ids': arrays['trial_ids'][evaluating],
                         'conditions': keys[evaluating], 'condition_fallback': fallback})
    np.savez_compressed(output / 'predictions.npz', **saved_arrays)
    report = {'evidence_status': 'RETROSPECTIVE_SINGLE_SESSION_DIAGNOSTIC', 'config': config,
              'versions': {name: importlib.metadata.version(name) for name in ('numpy', 'torch', 'scikit-learn', 'pynwb')},
              'device': 'CPU', 'protocol_sha256': digest(config['protocol']), 'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'source_sha256': {name: digest(name) for name in sources}, 'lineage': lineage,
              'splits': original['splits'], 'models': rows, 'summary': summary,
              'condition_template_fallback_trials': int(fallback.sum()), 'seconds_total': time.perf_counter() - started,
              'protected_m025_sha256': protected,
              'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in saved_arrays.items()},
              'files': {path.name: digest(path) for path in output.glob('*.pt')}}
    (output / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    Path('reports/m026_neural_information.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'completed': True, 'seconds': report['seconds_total'], 'mse': {name: row['mse_m2_s2'] for name, row in summary['metrics'].items()}}))


def replay(config_path='configs/m026_neural_information.json'):
    config = read_json(config_path)
    output = Path(config['output'])
    report = read_json(output / 'results.json')
    for name, expected in report['protected_m025_sha256'].items():
        if digest(name) != expected:
            raise ValueError('Historical checksum changed: ' + name)
    arrays, groups, _, lineage = checked_inputs(config)
    if lineage != report['lineage']:
        raise ValueError('Replay input lineage differs from recorded experiment')
    with np.load(output / 'predictions.npz', allow_pickle=False) as archive:
        saved = dict(archive)
    for name, values in saved.items():
        if array_digest(values) != report['arrays'][name]['sha256']:
            raise ValueError('Prediction checksum changed: ' + name)
    for row in report['models']:
        path = output / (row['name'] + '.pt')
        if digest(path) != row['checkpoint_sha256']:
            raise ValueError('Checkpoint checksum changed')
        _, full, _ = control_counts(arrays['counts'].astype(float), arrays['conditions'], groups, row['mode'], config['donor_seed'])
        restored = restore_cnn(path, full[groups['source_validation']])
        np.testing.assert_array_equal(restored, saved[row['name']])
        if row['mode'] == 'permuted':
            restored_real = restore_cnn(path, arrays['counts'][groups['source_validation']])
            np.testing.assert_array_equal(restored_real, saved['permuted_real_seed_' + str(row['seed'])])
    print(json.dumps({'models_restored_exact': len(report['models']), 'array_digests': len(saved), 'historical_files_unchanged': len(report['protected_m025_sha256'])}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    if args.replay:
        replay()
    else:
        run()


if __name__ == '__main__':
    main()
