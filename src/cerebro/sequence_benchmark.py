"""Common trial-disjoint CPU sequence benchmark; source test data untouched."""

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest, trial_metrics
from cerebro.sequence_models import make_sequence_model


def normalized_tensors(counts, velocity, fitting_trials):
    feature_count = counts.shape[-1]
    selected_counts = counts[fitting_trials]
    fitting_features = selected_counts.reshape(-1, feature_count)
    scaler = StandardScaler()
    scaler.fit(fitting_features)
    centered_counts = counts - scaler.mean_
    normalized_counts = centered_counts / scaler.scale_
    selected_velocity = velocity[fitting_trials]
    fitting_targets = selected_velocity.reshape(-1, velocity.shape[-1])
    target_mean = fitting_targets.mean(axis=0)
    target_scale = fitting_targets.std(axis=0)
    target_scale = np.where(target_scale > 0, target_scale, 1.)
    centered_velocity = velocity - target_mean
    normalized_velocity = centered_velocity / target_scale
    features = torch.tensor(normalized_counts, dtype=torch.float32)
    targets = torch.tensor(normalized_velocity, dtype=torch.float32)
    parameters = {
        'feature_mean': scaler.mean_, 'feature_scale': scaler.scale_,
        'target_mean': target_mean, 'target_scale': target_scale,
    }
    return features, targets, parameters


def train_epoch(model, optimizer, features, targets, gradient_clip):
    if not np.isfinite(gradient_clip) or gradient_clip <= 0:
        raise ValueError('Gradient clipping must be finite and positive')
    model.train()
    optimizer.zero_grad()
    prediction = model(features)
    differences = prediction - targets
    loss = torch.mean(differences ** 2)
    if not torch.isfinite(loss):
        raise ValueError('Nonfinite optimization loss')
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
    optimizer.step()
    return float(loss.detach())


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    if config['bin_width_seconds'] != .02:
        raise ValueError('Fixed state-space model requires 20 ms bins')
    if config['maximum_epochs'] < 1 or config['learning_rate'] <= 0:
        raise ValueError('Positive epochs and learning rate required')
    root = Path(config['classical_run'])
    classical = json.loads((root / 'results.json').read_text())
    splits = json.loads((root / 'split_manifest.json').read_text())
    if classical['config']['bin_width_seconds'] != config['bin_width_seconds']:
        raise ValueError('Sequence timing differs from source preprocessing')
    with np.load(root / 'arrays.npz', allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    for name, metadata in classical['arrays'].items():
        if array_digest(arrays[name]) != metadata['sha256']:
            raise ValueError('Input arrays differ from recorded provenance')
    if splits != classical['splits']:
        raise ValueError('Split manifest differs from classical experiment')
    counts = arrays['counts'].astype(float)
    velocity = arrays['velocity_m_s']
    trial_ids = arrays['trial_ids']
    inner_training = np.isin(trial_ids, splits['inner_training'])
    inner_validation = np.isin(trial_ids, splits['inner_validation'])
    source_training = np.isin(trial_ids, splits['source_training'])
    source_validation = np.isin(trial_ids, splits['source_validation'])
    inner_features, inner_targets, _ = normalized_tensors(counts, velocity, inner_training)
    full_features, full_targets, full_parameters = normalized_tensors(counts, velocity, source_training)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    saved_arrays = {'evaluation_trial_ids': trial_ids[source_validation]}
    for kind in config['models']:
        for seed in config['seeds']:
            torch.manual_seed(seed)
            model = make_sequence_model(kind, counts.shape[-1], config['hidden'], velocity.shape[-1])
            optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
            history = []
            for epoch in range(config['maximum_epochs']):
                training_loss = train_epoch(
                    model, optimizer, inner_features[inner_training], inner_targets[inner_training], config['gradient_clip'],
                )
                model.eval()
                with torch.no_grad():
                    inner_prediction = model(inner_features[inner_validation])
                    inner_error = inner_prediction - inner_targets[inner_validation]
                    selection_loss = float(torch.mean(inner_error ** 2))
                history.append({'epoch': epoch + 1, 'training_loss': training_loss, 'inner_validation_loss': selection_loss})
            selected_epoch = min(history, key=lambda entry: entry['inner_validation_loss'])['epoch']
            torch.manual_seed(seed)
            model = make_sequence_model(kind, counts.shape[-1], config['hidden'], velocity.shape[-1])
            optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
            for epoch in range(selected_epoch):
                train_epoch(model, optimizer, full_features[source_training], full_targets[source_training], config['gradient_clip'])
            model.eval()
            with torch.no_grad():
                normalized_prediction = model(full_features[source_validation]).numpy()
            physical_prediction = normalized_prediction * full_parameters['target_scale']
            physical_prediction = physical_prediction + full_parameters['target_mean']
            trial_mse, r_squared = trial_metrics(velocity[source_validation], physical_prediction)
            name = kind + '_seed_' + str(seed)
            saved_arrays[name + '_prediction_m_s'] = physical_prediction
            checkpoint = {
                'schema_version': 1, 'kind': kind, 'seed': seed,
                'input_units': counts.shape[-1], 'hidden': config['hidden'],
                'output_coordinates': velocity.shape[-1], 'state_dict': copy.deepcopy(model.state_dict()),
                'normalization': {key: torch.tensor(value) for key, value in full_parameters.items()},
                'split_manifest': splits, 'config': config, 'selected_epoch': selected_epoch,
            }
            checkpoint_path = output / (name + '.pt')
            torch.save(checkpoint, checkpoint_path)
            restored = torch.load(checkpoint_path, weights_only=True)
            replica = make_sequence_model(kind, counts.shape[-1], config['hidden'], velocity.shape[-1])
            replica.load_state_dict(restored['state_dict'])
            replica.eval()
            saved_normalization = restored['normalization']
            restored_counts = counts[source_validation] - saved_normalization['feature_mean'].numpy()
            restored_counts = restored_counts / saved_normalization['feature_scale'].numpy()
            restored_features = torch.tensor(restored_counts, dtype=torch.float32)
            with torch.no_grad():
                restored_prediction = replica(restored_features).numpy()
            if not np.array_equal(restored_prediction, normalized_prediction):
                raise ValueError('Checkpoint restoration changed predictions')
            results.append({
                'model': kind, 'seed': seed, 'selected_epoch': selected_epoch,
                'parameters': sum(parameter.numel() for parameter in model.parameters()),
                'history': history, 'mse_m2_s2': float(trial_mse.mean()),
                'trial_mse_m2_s2': trial_mse.tolist(),
                'pooled_r2_by_coordinate': [float(value) if np.isfinite(value) else None for value in r_squared],
                'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
                'checkpoint_restored_predictions_identical': True,
            })
    report = {
        'schema_version': 1, 'config': config, 'splits': splits,
        'hypothesis': 'Past and current neural bins may improve held-out trial velocity prediction; no model superiority assumed.',
        'input_report_sha256': hashlib.sha256((root / 'results.json').read_bytes()).hexdigest(),
        'source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in ('sequence_models.py', 'sequence_benchmark.py')},
        'torch_version': str(torch.__version__), 'device': 'CPU', 'results': results,
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
        'protocol': 'Same complete windows, units, inner split and source validation trials as classical benchmark. Fit all normalization on training; select epoch on inner validation only; retrain all75 training. One full-trial batch per epoch, same optimizer/epoch cap, different parameter counts.',
        'information_access': 'Causal neural sequence at bin-right time, no future bins. Same-bin behavior target. Recorded go cue supplies trial clock; offline replay only, no biological closed-loop validation.',
        'limitations': ['Three seeds measure initialization variability, not independent biological replicates', 'Small curated single-session training set', 'Architectures have unequal parameter counts and compute', 'No hyperparameter grid or final-test benchmark claim', 'Source validation has been used for exploratory reports and cannot now serve as untouched test'],
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in saved_arrays.items()},
    }
    np.savez_compressed(output / 'predictions.npz', **saved_arrays)
    (output / 'results.json').write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/sequence_06.json')
    parser.add_argument('--output', default='data/processed/sequence_06')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    print(json.dumps([{'model': row['model'], 'seed': row['seed'], 'mse': row['mse_m2_s2']} for row in report['results']], indent=2))


if __name__ == '__main__':
    main()
