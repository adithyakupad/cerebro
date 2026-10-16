"""Within-session causal GRU pretraining and label-budget controls.

This experiment does not establish foundation-model, subject-transfer, or
cross-session capabilities. Validation trials are report-only.
"""

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import Ridge
from torch import nn

from cerebro.benchmark import array_digest, trial_metrics


class RepresentationGRU(nn.Module):
    def __init__(self, input_units, hidden=32):
        super().__init__()
        self.encoder = nn.GRU(input_units, hidden, batch_first=True)
        self.reconstruction_head = nn.Linear(hidden, input_units)
        self.prediction_head = nn.Linear(hidden, input_units)

    def encode(self, features):
        latent, _ = self.encoder(features)
        return latent

    def forward(self, features):
        latent = self.encode(features)
        reconstructed = self.reconstruction_head(latent)
        predicted_next = self.prediction_head(latent)
        return reconstructed, predicted_next


class VelocityGRU(nn.Module):
    def __init__(self, encoder, hidden, output_coordinates=2):
        super().__init__()
        self.encoder = copy.deepcopy(encoder)
        self.readout = nn.Linear(hidden, output_coordinates)

    def forward(self, features):
        latent, _ = self.encoder(features)
        velocity = self.readout(latent)
        return velocity


def standardize_counts(counts, training_mask):
    counts = np.asarray(counts, dtype=float)
    mask = np.asarray(training_mask, dtype=bool)
    if counts.ndim != 3 or min(counts.shape) < 1:
        raise ValueError('Counts must be nonempty trials × bins × units')
    if mask.shape != (counts.shape[0],) or not np.any(mask):
        raise ValueError('Normalization requires explicit training trials')
    if not np.all(np.isfinite(counts)) or np.any(counts < 0) or np.any(counts != np.floor(counts)):
        raise ValueError('Counts must be finite nonnegative integers')
    training_counts = counts[mask].reshape(-1, counts.shape[2])
    feature_mean = training_counts.mean(axis=0)
    feature_scale = training_counts.std(axis=0)
    feature_scale = np.where(feature_scale > 0, feature_scale, 1.0)
    centered_counts = counts - feature_mean
    standardized = centered_counts / feature_scale
    return standardized, {'feature_mean': feature_mean, 'feature_scale': feature_scale}


def feature_mask(shape, probability, generator):
    if len(shape) != 3 or min(shape) < 1 or not 0 < probability < 1:
        raise ValueError('Mask requires a nonempty sequence and probability in (0,1)')
    random_values = torch.rand(shape, generator=generator)
    mask = random_values < probability
    if not torch.any(mask):
        raise ValueError('No masked entries; objective would be undefined')
    return mask


def self_supervised_loss(reconstructed, predicted_next, targets, mask):
    if reconstructed.shape != targets.shape or predicted_next.shape != targets.shape:
        raise ValueError('Heads and targets must share trial × bin × unit axes')
    if targets.ndim != 3 or targets.shape[1] < 2:
        raise ValueError('Predictive learning requires at least two bins per trial')
    if mask.shape != targets.shape or mask.dtype != torch.bool or not torch.any(mask):
        raise ValueError('Reconstruction loss requires a nonempty Boolean mask')
    reconstruction_errors = reconstructed - targets
    selected_errors = reconstruction_errors[mask]
    masked_loss = torch.mean(selected_errors.square())
    predictive_errors = predicted_next[:, :-1, :] - targets[:, 1:, :]
    predictive_loss = torch.mean(predictive_errors.square())
    combined_loss = masked_loss + predictive_loss
    return combined_loss, masked_loss, predictive_loss


def nested_budget_ids(training_ids, budgets, seed):
    ids = np.asarray(training_ids)
    if ids.ndim != 1 or len(np.unique(ids)) != len(ids):
        raise ValueError('Training trial identities must be unique')
    if any(not isinstance(size, int) or isinstance(size, bool) or size < 1 or size > len(ids) for size in budgets):
        raise ValueError('Label budgets must be positive and fit source training trials')
    generator = np.random.default_rng(seed)
    shuffled_ids = generator.permutation(ids)
    return {size: shuffled_ids[:size].tolist() for size in budgets}


def _train_pretraining(model, training_features, config, seed):
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    mask_generator = torch.Generator().manual_seed(seed + 1000)
    history = []
    model.train()
    for epoch in range(config['epochs']):
        mask = feature_mask(training_features.shape, config['mask_probability'], mask_generator)
        masked_input = training_features.masked_fill(mask, 0)
        reconstructed, predicted_next = model(masked_input)
        combined, masked, predictive = self_supervised_loss(
            reconstructed, predicted_next, training_features, mask,
        )
        if not torch.isfinite(combined):
            raise ValueError('Nonfinite self-supervised loss')
        optimizer.zero_grad()
        combined.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config['gradient_clip'])
        optimizer.step()
        history.append({
            'epoch': epoch + 1, 'masked_loss': float(masked.detach()),
            'predictive_loss': float(predictive.detach()),
            'combined_loss': float(combined.detach()),
            'masked_entries': int(mask.sum()),
        })
    return history


def _train_supervised(model, features, physical_targets, config):
    flat_targets = physical_targets.reshape(-1, physical_targets.shape[-1])
    target_mean = flat_targets.mean(axis=0)
    target_scale = flat_targets.std(axis=0)
    target_scale = np.where(target_scale > 0, target_scale, 1.0)
    normalized_targets = (physical_targets - target_mean) / target_scale
    target_tensor = torch.tensor(normalized_targets, dtype=torch.float32)
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    model.train()
    history = []
    for epoch in range(config['epochs']):
        prediction = model(features)
        differences = prediction - target_tensor
        loss = torch.mean(differences.square())
        if not torch.isfinite(loss):
            raise ValueError('Nonfinite supervised loss')
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config['gradient_clip'])
        optimizer.step()
        history.append({'epoch': epoch + 1, 'normalized_velocity_loss': float(loss.detach())})
    return history, {'target_mean': target_mean, 'target_scale': target_scale}


def _evaluate_row(name, seed, budget, prediction, targets, history, checkpoint_path, restored):
    trial_mse, coordinate_r2 = trial_metrics(targets, prediction)
    return {
        'control': name, 'seed': seed, 'label_budget_trials': budget,
        'mse_m2_s2': float(trial_mse.mean()), 'trial_mse_m2_s2': trial_mse.tolist(),
        'pooled_r2_by_coordinate': [float(value) if np.isfinite(value) else None for value in coordinate_r2],
        'history': history, 'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
        'checkpoint_restored_predictions_identical': restored,
    }


def _save_restore_pretraining(model, path, config, seed, parameters, splits):
    checkpoint = {
        'state_dict': copy.deepcopy(model.state_dict()), 'config': config, 'seed': seed,
        'normalization': {name: torch.tensor(value) for name, value in parameters.items()},
        'split_manifest': splits, 'input_units': model.encoder.input_size,
        'hidden': model.encoder.hidden_size,
    }
    torch.save(checkpoint, path)
    restored = torch.load(path, weights_only=True)
    replica = RepresentationGRU(restored['input_units'], restored['hidden'])
    replica.load_state_dict(restored['state_dict'])
    return replica


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    for name in ('epochs', 'hidden'):
        value = config[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError('Epochs and hidden dimensions must be positive integers')
    finite_parameters = [config[name] for name in ('learning_rate', 'mask_probability', 'ridge_alpha', 'gradient_clip')]
    if not np.all(np.isfinite(finite_parameters)):
        raise ValueError('Optimization parameters must be finite')
    if config['bin_width_seconds'] != 0.020:
        raise ValueError('This experiment uses recorded 20 ms preprocessing')
    if config['epochs'] < 1 or config['hidden'] < 1 or config['learning_rate'] <= 0:
        raise ValueError('Training dimensions, epochs and learning rate must be positive')
    if not 0 < config['mask_probability'] < 1 or config['ridge_alpha'] < 0 or config['gradient_clip'] <= 0:
        raise ValueError('Invalid masking, ridge or gradient configuration')
    root = Path(config['classical_run'])
    classical = json.loads((root / 'results.json').read_text())
    splits = json.loads((root / 'split_manifest.json').read_text())
    if splits != classical['splits']:
        raise ValueError('Input split manifest differs from source report')
    if classical['config']['bin_width_seconds'] != config['bin_width_seconds']:
        raise ValueError('Source bin timestamps differ from experiment timing')
    with np.load(root / 'arrays.npz', allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    for name, metadata in classical['arrays'].items():
        if array_digest(arrays[name]) != metadata['sha256']:
            raise ValueError('Input array provenance mismatch')
    counts = arrays['counts']
    velocity = arrays['velocity_m_s']
    trial_ids = arrays['trial_ids']
    bin_right_seconds = arrays['bin_right_seconds']
    if bin_right_seconds.shape != counts.shape[:2] or not np.all(np.isfinite(bin_right_seconds)):
        raise ValueError('Original bin-right timestamps must match source observations')
    bin_intervals = np.diff(bin_right_seconds, axis=1)
    if not np.allclose(bin_intervals, 0.020, rtol=0, atol=1e-10):
        raise ValueError('Source timestamps do not represent consecutive 20 ms bins')
    training_mask = np.isin(trial_ids, splits['source_training'])
    validation_mask = np.isin(trial_ids, splits['source_validation'])
    if np.any(training_mask & validation_mask) or not np.all(training_mask | validation_mask):
        raise ValueError('Source training/validation must be disjoint and exhaustive')
    if len(np.unique(trial_ids)) != len(trial_ids):
        raise ValueError('Source trial identities must be unique')
    if set(trial_ids[training_mask].tolist()) != set(splits['source_training']):
        raise ValueError('Source training identities are missing from input arrays')
    if set(trial_ids[validation_mask].tolist()) != set(splits['source_validation']):
        raise ValueError('Source validation identities are missing from input arrays')
    if velocity.shape != counts.shape[:2] + (2,) or not np.all(np.isfinite(velocity)):
        raise ValueError('Physical velocity must match trial/bin axes and two coordinates')
    standardized, parameters = standardize_counts(counts, training_mask)
    features = torch.tensor(standardized, dtype=torch.float32)
    budgets = nested_budget_ids(trial_ids[training_mask], config['label_budgets'], config['budget_seed'])
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    saved_arrays = {
        'evaluation_trial_ids': trial_ids[validation_mask],
        'evaluation_bin_right_seconds': bin_right_seconds[validation_mask],
    }
    results = []
    pretraining_reports = []
    for seed in config['seeds']:
        torch.manual_seed(seed)
        pretrained = RepresentationGRU(counts.shape[-1], config['hidden'])
        initial_state = copy.deepcopy(pretrained.state_dict())
        history = _train_pretraining(pretrained, features[training_mask], config, seed)
        checkpoint_path = output / ('pretrained_seed_' + str(seed) + '.pt')
        replica = _save_restore_pretraining(pretrained, checkpoint_path, config, seed, parameters, splits)
        pretrained.eval()
        replica.eval()
        with torch.no_grad():
            latent = pretrained.encode(features).numpy()
            restored_latent = replica.encode(features).numpy()
        if not np.array_equal(latent, restored_latent):
            raise ValueError('Pretraining checkpoint restoration changed latent states')
        random_encoder = RepresentationGRU(counts.shape[-1], config['hidden'])
        random_encoder.load_state_dict(initial_state)
        random_encoder.eval()
        with torch.no_grad():
            random_latent = random_encoder.encode(features).numpy()
        pretraining_reports.append({
            'seed': seed, 'history': history,
            'training_trial_ids': trial_ids[training_mask].tolist(),
            'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
            'restored_latents_identical': True,
        })
        for budget, label_ids in budgets.items():
            label_mask = np.isin(trial_ids, label_ids)
            validation_targets = velocity[validation_mask]
            for name, representation in (('pretrained_frozen_ridge', latent), ('random_frozen_ridge', random_latent)):
                label_features = representation[label_mask].reshape(-1, config['hidden'])
                label_targets = velocity[label_mask].reshape(-1, 2)
                probe = Ridge(alpha=config['ridge_alpha']).fit(label_features, label_targets)
                flat_validation = representation[validation_mask].reshape(-1, config['hidden'])
                flat_prediction = probe.predict(flat_validation)
                prediction = flat_prediction.reshape(validation_targets.shape)
                identifier = name + '_seed_' + str(seed) + '_budget_' + str(budget)
                probe_path = output / (identifier + '.npz')
                np.savez_compressed(probe_path, coefficients=probe.coef_, intercept=probe.intercept_)
                with np.load(probe_path, allow_pickle=False) as archive:
                    restored_flat = flat_validation @ archive['coefficients'].T + archive['intercept']
                if not np.array_equal(restored_flat, flat_prediction):
                    raise ValueError('Ridge parameter restoration changed predictions')
                saved_arrays[identifier + '_prediction_m_s'] = prediction
                results.append(_evaluate_row(name, seed, budget, prediction, validation_targets, [], probe_path, True))
            for name, encoder_source in (('supervised_only', random_encoder), ('pretrained_finetuned', pretrained)):
                torch.manual_seed(seed + 2000)
                supervised = VelocityGRU(encoder_source.encoder, config['hidden'])
                training_history, target_parameters = _train_supervised(
                    supervised, features[label_mask], velocity[label_mask], config,
                )
                supervised.eval()
                with torch.no_grad():
                    normalized_prediction = supervised(features[validation_mask]).numpy()
                prediction = normalized_prediction * target_parameters['target_scale']
                prediction = prediction + target_parameters['target_mean']
                identifier = name + '_seed_' + str(seed) + '_budget_' + str(budget)
                supervised_path = output / (identifier + '.pt')
                checkpoint = {
                    'state_dict': copy.deepcopy(supervised.state_dict()),
                    'input_units': counts.shape[-1], 'hidden': config['hidden'],
                    'normalization': {key: torch.tensor(value) for key, value in {**parameters, **target_parameters}.items()},
                    'label_trial_ids': label_ids, 'split_manifest': splits,
                    'config': config, 'seed': seed, 'control': name,
                }
                torch.save(checkpoint, supervised_path)
                restored = torch.load(supervised_path, weights_only=True)
                fresh_encoder = RepresentationGRU(counts.shape[-1], config['hidden'])
                restored_model = VelocityGRU(fresh_encoder.encoder, config['hidden'])
                restored_model.load_state_dict(restored['state_dict'])
                restored_model.eval()
                with torch.no_grad():
                    restored_prediction = restored_model(features[validation_mask]).numpy()
                if not np.array_equal(restored_prediction, normalized_prediction):
                    raise ValueError('Supervised checkpoint restoration changed predictions')
                saved_arrays[identifier + '_prediction_m_s'] = prediction
                results.append(_evaluate_row(name, seed, budget, prediction, validation_targets, training_history, supervised_path, True))
    np.savez_compressed(output / 'predictions.npz', **saved_arrays)
    report = {
        'schema_version': 1, 'config': config, 'splits': splits,
        'label_budget_trial_ids': {str(key): value for key, value in budgets.items()},
        'normalization': {key: value.tolist() for key, value in parameters.items()},
        'normalization_training_trial_ids': trial_ids[training_mask].tolist(),
        'input_report_sha256': hashlib.sha256((root / 'results.json').read_bytes()).hexdigest(),
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'torch_version': str(torch.__version__), 'device': 'CPU',
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True)),
        'pretraining': pretraining_reports, 'results': results,
        'protocol': 'Fixed epochs with no validation selection. SSL and feature scaling use every source training trial only; probe/supervised velocity labels use nested trial budgets. Target scaling uses each labeled budget only. Evaluation uses original source validation trials.',
        'information_access': 'Causal GRU hidden state consumes past/current bins; same-bin velocity is available offline at bin-right time. Next-bin SSL targets remain within source trials. Pretraining reconstruction is masked standardized count MSE, not a generative count likelihood.',
        'limitations': [
            'Within-session representation experiment only; no foundation-model validation',
            'No cross-session or multi-subject pretraining or transfer was executed',
            'All75 training trials supply unlabeled neural data and feature scaling even at low label budgets; this is label-budget comparison, not equal-data-budget comparison',
            'Source validation is report-only and already used in exploratory analyses; it is not untouched test data',
            'Three initialization seeds are not independent biological replicates',
            'Five default epochs are a fixed plumbing baseline, not optimized convergence',
        ],
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in saved_arrays.items()},
    }
    (output / 'results.json').write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/representation_07.json')
    parser.add_argument('--output', default='data/processed/representation_07')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    print(json.dumps(report['results'], indent=2))


if __name__ == '__main__':
    main()
