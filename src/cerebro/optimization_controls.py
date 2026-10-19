"""Training-only classical controls for the fixed M025 optimization experiment."""

import numpy as np
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import trial_metrics
from cerebro.kalman import fit_kalman, predict_kalman
from cerebro.population import fit_decoder


def _counts(values):
    counts = np.asarray(values, dtype=float)
    if counts.ndim != 3 or counts.shape[0] < 1 or counts.shape[1] < 5 or counts.shape[2] < 1:
        raise ValueError('Counts require trials × at least five bins × units')
    if not np.all(np.isfinite(counts)) or np.any(counts < 0):
        raise ValueError('Counts must be finite and nonnegative')
    return counts


def _velocity(values, counts):
    velocity = np.asarray(values, dtype=float)
    expected_shape = counts.shape[:2] + (2,)
    if velocity.shape != expected_shape or not np.all(np.isfinite(velocity)):
        raise ValueError('Velocity must match trials × bins × two finite coordinates')
    return velocity


def history_features(normalized_counts):
    """Return trials × complete bins × (five × units), oldest bin first."""
    values = np.asarray(normalized_counts, dtype=float)
    if values.ndim != 3 or values.shape[1] < 5 or not np.all(np.isfinite(values)):
        raise ValueError('History requires finite trials × at least five bins × units')
    complete_bins = values.shape[1] - 4
    lagged_counts = []
    for lag in range(5):
        current_counts = values[:, lag:lag + complete_bins, :]
        lagged_counts.append(current_counts)
    return np.concatenate(lagged_counts, axis=2)


def predict_controls(parameters, counts):
    """Restore all controls from numerical parameters without pickle."""
    counts = _counts(counts)
    feature_mean = np.asarray(parameters['scaler_mean'])
    feature_scale = np.asarray(parameters['scaler_scale'])
    if feature_mean.shape != (counts.shape[2],) or feature_scale.shape != feature_mean.shape:
        raise ValueError('Checkpoint unit dimensions differ')
    if not np.all(np.isfinite(feature_mean)) or not np.all(np.isfinite(feature_scale)) or np.any(feature_scale <= 0):
        raise ValueError('Checkpoint scaling must be finite and positive')
    normalized_counts = (counts - feature_mean) / feature_scale
    target_shape = counts.shape[:2] + (2,)
    predictions = {
        'mean': np.broadcast_to(parameters['mean_baseline'], target_shape).copy(),
        'go_time_template': np.broadcast_to(parameters['time_template_baseline'], target_shape).copy(),
    }
    predictions['ridge'] = normalized_counts @ parameters['ridge_coef'].T
    predictions['ridge'] += parameters['ridge_intercept']
    history = history_features(normalized_counts)
    history_prediction = history @ parameters['history_ridge_coef'].T
    history_prediction += parameters['history_ridge_intercept']
    predictions['history_ridge'] = np.full(target_shape, np.nan)
    predictions['history_ridge'][:, 4:, :] = history_prediction
    kalman_parameters = {}
    for name, value in parameters.items():
        if name.startswith('kalman_'):
            kalman_parameters[name.removeprefix('kalman_')] = value
    predictions['kalman'] = predict_kalman(kalman_parameters, normalized_counts)
    return predictions


def train_controls(training_counts, training_velocity, evaluation_counts,
                   evaluation_velocity, alphas, selected_alphas=None):
    """Select on supplied inner validation, or refit fixed alphas without labels.

    Ridge fits use bins 4 onward for both history lengths. Kalman transitions
    use all within-trial bins. Every selection loss is equal-trial physical MSE
    on bins 4 onward; fixed-alpha refits never inspect evaluation targets.
    """
    training_counts = _counts(training_counts)
    evaluation_counts = _counts(evaluation_counts)
    training_velocity = _velocity(training_velocity, training_counts)
    if training_counts.shape[1:] != evaluation_counts.shape[1:]:
        raise ValueError('Training and evaluation bin/unit dimensions differ')
    alphas = list(alphas)
    if not alphas:
        raise ValueError('Alphas must be finite nonnegative scalars')
    for alpha in alphas:
        numeric = isinstance(alpha, (int, float, np.integer, np.floating))
        if isinstance(alpha, (bool, np.bool_)) or not numeric:
            raise ValueError('Alphas must be finite nonnegative scalars')
        if not np.isfinite(alpha) or alpha < 0:
            raise ValueError('Alphas must be finite nonnegative scalars')
    if selected_alphas is None:
        evaluation_velocity = _velocity(evaluation_velocity, evaluation_counts)
    else:
        expected_models = {'ridge', 'history_ridge', 'kalman'}
        if set(selected_alphas) != expected_models:
            raise ValueError('Fixed alphas must specify ridge, history_ridge and kalman')
        if any(alpha not in alphas for alpha in selected_alphas.values()):
            raise ValueError('Fixed alphas must belong to the prespecified grid')

    unit_count = training_counts.shape[2]
    flat_counts = training_counts.reshape(-1, unit_count)
    scaler = StandardScaler().fit(flat_counts)
    training_normalized = scaler.transform(flat_counts).reshape(training_counts.shape)
    evaluation_normalized = (evaluation_counts - scaler.mean_) / scaler.scale_
    training_features = {
        'ridge': training_normalized[:, 4:, :],
        'history_ridge': history_features(training_normalized),
    }
    evaluation_features = {
        'ridge': evaluation_normalized[:, 4:, :],
        'history_ridge': history_features(evaluation_normalized),
    }
    training_targets = training_velocity[:, 4:, :].reshape(-1, 2)
    selection = []
    chosen_alphas = {}
    parameters = {
        'scaler_mean': scaler.mean_,
        'scaler_scale': scaler.scale_,
        'mean_baseline': training_velocity.mean(axis=(0, 1)),
        'time_template_baseline': training_velocity.mean(axis=0),
    }
    for kind in ('ridge', 'history_ridge', 'kalman'):
        if selected_alphas is None:
            candidates = alphas
        else:
            candidates = [selected_alphas[kind]]
        best_loss = np.inf
        for alpha in candidates:
            if kind == 'kalman':
                model = fit_kalman(training_normalized, training_velocity, ridge_alpha=alpha)
                prediction = predict_kalman(model, evaluation_normalized)[:, 4:, :]
            else:
                feature_count = training_features[kind].shape[2]
                flat_features = training_features[kind].reshape(-1, feature_count)
                model = fit_decoder(flat_features, training_targets, alpha=alpha)
                prediction = model.predict(evaluation_features[kind].reshape(-1, feature_count))
                prediction = prediction.reshape(evaluation_counts.shape[0], -1, 2)
            if selected_alphas is None:
                trial_loss, _ = trial_metrics(evaluation_velocity[:, 4:, :], prediction)
                loss = float(trial_loss.mean())
                selection.append({'model': kind, 'alpha': float(alpha), 'mse_m2_s2': loss})
            else:
                loss = 0.
            if loss < best_loss:
                best_loss = loss
                chosen_alphas[kind] = float(alpha)
                selected_model = model
        if kind == 'kalman':
            for name, value in selected_model.items():
                parameters['kalman_' + name] = value
        else:
            parameters[kind + '_coef'] = selected_model.coef_
            parameters[kind + '_intercept'] = selected_model.intercept_
    predictions = predict_controls(parameters, evaluation_counts)
    return {
        'predictions': predictions,
        'selection': selection,
        'selected_alphas': chosen_alphas,
        'parameters': parameters,
    }
