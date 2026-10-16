"""Supervised linear Gaussian velocity filter with trial-local transitions."""

import numpy as np


def _sequence(values, feature_count=None):
    sequence = np.asarray(values, dtype=float)
    if sequence.ndim != 3 or min(sequence.shape) < 1:
        raise ValueError("Sequence must be nonempty trials × bins × features.")
    if feature_count is not None and sequence.shape[2] != feature_count:
        raise ValueError("Unexpected sequence feature count.")
    if not np.all(np.isfinite(sequence)):
        raise ValueError("Sequence must contain finite observations.")
    return sequence


def _regularized_covariance(residuals, covariance_floor):
    sample_count, feature_count = residuals.shape
    centered = residuals - residuals.mean(axis=0)
    denominator = max(sample_count - 1, 1)
    covariance = centered.T @ centered / denominator
    symmetric_covariance = (covariance + covariance.T) / 2
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric_covariance)
    floored_eigenvalues = np.maximum(eigenvalues, covariance_floor)
    scaled_eigenvectors = eigenvectors * floored_eigenvalues[None, :]
    regularized = scaled_eigenvectors @ eigenvectors.T
    return (regularized + regularized.T) / 2


def _fit_affine(inputs, outputs, ridge_alpha):
    input_mean = inputs.mean(axis=0)
    output_mean = outputs.mean(axis=0)
    centered_inputs = inputs - input_mean
    centered_outputs = outputs - output_mean
    feature_count = inputs.shape[1]
    regularization = ridge_alpha * np.eye(feature_count)
    gram_matrix = centered_inputs.T @ centered_inputs
    cross_product = centered_inputs.T @ centered_outputs
    if ridge_alpha == 0:
        coefficients, _, _, _ = np.linalg.lstsq(centered_inputs, centered_outputs, rcond=None)
    else:
        coefficients = np.linalg.solve(gram_matrix + regularization, cross_product)
    matrix = coefficients.T
    offset = output_mean - matrix @ input_mean
    predicted_outputs = inputs @ matrix.T + offset
    residuals = outputs - predicted_outputs
    return matrix, offset, residuals


def fit_kalman(training_features, training_targets, ridge_alpha=1, covariance_floor=1e-5):
    """Fit velocity states (two coordinates) using training trials only.

    Neural observations use x = H y + observation_offset. Transitions use
    y[t] = A y[t-1] + transition_offset exclusively within source trials.
    Covariance floors have their corresponding squared physical units.
    """
    features = _sequence(training_features)
    targets = _sequence(training_targets, feature_count=2)
    if features.shape[:2] != targets.shape[:2]:
        raise ValueError("Features and targets must share trial and bin axes.")
    if targets.shape[1] < 2:
        raise ValueError("At least two bins per trial are needed for transitions.")
    for value in (ridge_alpha, covariance_floor):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
            raise ValueError("Regularization parameters must be finite numeric scalars.")
        if not np.isfinite(value):
            raise ValueError("Regularization parameters must be finite numeric scalars.")
    if ridge_alpha < 0 or covariance_floor <= 0:
        raise ValueError("Ridge alpha must be nonnegative and covariance floor positive.")
    unit_count = features.shape[2]
    flat_features = features.reshape(-1, unit_count)
    flat_targets = targets.reshape(-1, 2)
    observation_matrix, observation_offset, observation_residuals = _fit_affine(
        flat_targets, flat_features, ridge_alpha
    )
    previous_states = targets[:, :-1, :].reshape(-1, 2)
    following_states = targets[:, 1:, :].reshape(-1, 2)
    transition_matrix, transition_offset, transition_residuals = _fit_affine(
        previous_states, following_states, ridge_alpha
    )
    initial_states = targets[:, 0, :]
    initial_mean = initial_states.mean(axis=0)
    initial_covariance = _regularized_covariance(initial_states, covariance_floor)
    process_covariance = _regularized_covariance(transition_residuals, covariance_floor)
    observation_covariance = _regularized_covariance(observation_residuals, covariance_floor)
    model = {
        "A": transition_matrix,
        "H": observation_matrix,
        "Q": process_covariance,
        "R": observation_covariance,
        "transition_offset": transition_offset,
        "observation_offset": observation_offset,
        "initial_mean": initial_mean,
        "initial_covariance": initial_covariance,
    }
    return model


def _validate_model(model, unit_count):
    expected_shapes = {
        "A": (2, 2), "H": (unit_count, 2), "Q": (2, 2),
        "R": (unit_count, unit_count), "transition_offset": (2,),
        "observation_offset": (unit_count,), "initial_mean": (2,),
        "initial_covariance": (2, 2),
    }
    parameters = {}
    for name, expected_shape in expected_shapes.items():
        if name not in model:
            raise ValueError(f"Missing Kalman parameter: {name}.")
        value = np.asarray(model[name], dtype=float)
        if value.shape != expected_shape or not np.all(np.isfinite(value)):
            raise ValueError(f"Invalid Kalman parameter: {name}.")
        parameters[name] = value
    for name in ("Q", "R", "initial_covariance"):
        covariance = parameters[name]
        if not np.allclose(covariance, covariance.T):
            raise ValueError(f"Covariance {name} must be symmetric.")
        if np.linalg.eigvalsh(covariance).min() <= 0:
            raise ValueError(f"Covariance {name} must be positive definite.")
    return parameters


def predict_kalman(model, observations):
    """Filter contemporaneous neural bins, available offline at each bin end.

    No future bins or preceding trial states are accessed. The first bin uses
    the training initial-state prior before its contemporaneous update.
    """
    features = _sequence(observations)
    trial_count, bin_count, unit_count = features.shape
    parameters = _validate_model(model, unit_count)
    transition = parameters["A"]
    observation = parameters["H"]
    process_covariance = parameters["Q"]
    observation_covariance = parameters["R"]
    state_identity = np.eye(2)
    noise_weighted_observation = np.linalg.solve(observation_covariance, observation)
    observation_information = observation.T @ noise_weighted_observation
    predicted_targets = np.empty((trial_count, bin_count, 2), dtype=float)
    for trial_index in range(trial_count):
        state_mean = parameters["initial_mean"].copy()
        state_covariance = parameters["initial_covariance"].copy()
        for bin_index in range(bin_count):
            if bin_index > 0:
                state_mean = transition @ state_mean + parameters["transition_offset"]
                projected_covariance = transition @ state_covariance @ transition.T
                state_covariance = projected_covariance + process_covariance
            expected_observation = observation @ state_mean + parameters["observation_offset"]
            innovation = features[trial_index, bin_index, :] - expected_observation
            # Solve in the two-dimensional state space rather than every neural unit.
            gain_system = state_identity + state_covariance @ observation_information
            gain_right_hand_side = state_covariance @ noise_weighted_observation.T
            gain = np.linalg.solve(gain_system, gain_right_hand_side)
            state_mean = state_mean + gain @ innovation
            update_operator = state_identity - gain @ observation
            retained_covariance = update_operator @ state_covariance @ update_operator.T
            update_noise = gain @ observation_covariance @ gain.T
            state_covariance = retained_covariance + update_noise
            state_covariance = (state_covariance + state_covariance.T) / 2
            if not np.all(np.isfinite(state_mean)) or not np.all(np.isfinite(state_covariance)):
                raise ValueError("Kalman filtering produced nonfinite state estimates.")
            predicted_targets[trial_index, bin_index, :] = state_mean
    return predicted_targets
