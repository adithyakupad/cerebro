"""Fixed M026 information controls; synthetic fixtures establish software behavior only."""

import numpy as np


def _keys(values, trial_count):
    keys = np.asarray(values)
    if keys.ndim != 1 or len(keys) != trial_count:
        raise ValueError('Condition keys must identify every trial')
    return keys


def input_features(counts, mode):
    """Return trials × bins × units; the explicit clock is bin-right seconds."""
    counts = np.asarray(counts, dtype=float)
    if counts.ndim != 3 or min(counts.shape) < 1:
        raise ValueError('Counts require nonempty trials × bins × units')
    if not np.all(np.isfinite(counts)) or np.any(counts < 0):
        raise ValueError('Counts must be finite and nonnegative')
    if mode == 'neural':
        features = counts.copy()
    elif mode == 'zero':
        features = np.zeros_like(counts)
    elif mode == 'clock':
        bin_numbers = np.arange(1, counts.shape[1] + 1)
        right_seconds = -.4 + .02 * bin_numbers
        features = np.broadcast_to(right_seconds[None, :, None], counts.shape).copy()
    else:
        raise ValueError('Mode must be neural, zero or clock')
    return features


def condition_donors(keys, indices, seed):
    """Return global donor IDs in recipient order, never outside supplied indices.

    Every nonsingleton condition is deranged by a nonzero cyclic shift after
    random ordering. Singleton recipients retain their original neural trial.
    """
    keys = np.asarray(keys)
    if keys.ndim != 1:
        raise ValueError('Condition keys must be one dimensional')
    indices = np.asarray(indices)
    if indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer):
        raise ValueError('Recipient indices must be one-dimensional integers')
    if len(np.unique(indices)) != len(indices):
        raise ValueError('Recipient indices must be unique')
    if np.any(indices < 0) or np.any(indices >= len(keys)):
        raise ValueError('Recipient indices must index the condition array')
    donors = indices.copy()
    selected_keys = keys[indices]
    generator = np.random.default_rng(seed)
    for key in np.unique(selected_keys):
        positions = np.flatnonzero(selected_keys == key)
        if len(positions) < 2:
            continue
        shuffled_positions = generator.permutation(positions)
        shift = generator.integers(1, len(positions))
        donor_positions = np.roll(shuffled_positions, shift)
        donors[shuffled_positions] = indices[donor_positions]
    return donors


def condition_template(training_targets, training_keys, evaluation_keys):
    """Fit condition × bin physical-velocity means; unseen keys use global phase."""
    training_targets = np.asarray(training_targets, dtype=float)
    if training_targets.ndim != 3 or min(training_targets.shape) < 1:
        raise ValueError('Targets require nonempty trials × bins × coordinates')
    if training_targets.shape[2] != 2 or not np.all(np.isfinite(training_targets)):
        raise ValueError('Targets require two finite velocity coordinates')
    training_keys = _keys(training_keys, len(training_targets))
    evaluation_keys = np.asarray(evaluation_keys)
    if evaluation_keys.ndim != 1:
        raise ValueError('Evaluation keys must be one dimensional')
    global_template = training_targets.mean(axis=0)
    prediction_shape = (len(evaluation_keys),) + global_template.shape
    predictions = np.broadcast_to(global_template, prediction_shape).copy()
    fallback = np.ones(len(evaluation_keys), dtype=bool)
    for key in np.unique(training_keys):
        training_mask = training_keys == key
        evaluation_mask = evaluation_keys == key
        predictions[evaluation_mask] = training_targets[training_mask].mean(axis=0)
        fallback[evaluation_mask] = False
    return predictions, fallback


def _masked_summary(bin_errors, mask):
    bin_counts = mask.sum(axis=1)
    included = bin_counts > 0
    error_sums = np.where(mask, bin_errors, 0.).sum(axis=1)
    trial_losses = error_sums[included] / bin_counts[included]
    mean_loss = float(trial_losses.mean()) if len(trial_losses) else None
    return {
        'equal_trial_mse': mean_loss,
        'num_trials': int(included.sum()),
        'num_bins': int(bin_counts.sum()),
        'trial_indices': np.flatnonzero(included).tolist(),
        'trial_mse': trial_losses.tolist(),
    }


def stratified_summary(target, prediction, keys, start=4):
    """Describe per-condition/speed/direction errors, giving each included trial equal weight.

    Strata use observed target values only for retrospective description. They
    never select models; time bins are not independent biological replicates.
    """
    target = np.asarray(target, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    if target.ndim != 3 or min(target.shape) < 1 or target.shape[2] != 2:
        raise ValueError('Targets require nonempty trials × bins × two coordinates')
    if prediction.shape != target.shape:
        raise ValueError('Predictions must match target shape exactly')
    if not np.all(np.isfinite(target)) or not np.all(np.isfinite(prediction)):
        raise ValueError('Targets and predictions must be finite')
    if isinstance(start, bool) or not isinstance(start, (int, np.integer)):
        raise ValueError('Start must be an integer bin index')
    if start < 0 or start >= target.shape[1]:
        raise ValueError('Start must retain at least one observation bin')
    keys = _keys(keys, len(target))
    target = target[:, start:, :]
    prediction = prediction[:, start:, :]
    differences = prediction - target
    bin_errors = np.mean(differences ** 2, axis=2)
    conditions = {}
    for key in np.unique(keys):
        trial_mask = keys == key
        mask = np.broadcast_to(trial_mask[:, None], bin_errors.shape)
        conditions[str(key)] = _masked_summary(bin_errors, mask)
    speed_squared = np.sum(target ** 2, axis=2)
    speed = np.sqrt(speed_squared)
    speed_edges = [0., .1, .25, .5, np.inf]
    speed_groups = {}
    for lower, upper in zip(speed_edges[:-1], speed_edges[1:]):
        mask = (speed >= lower) & (speed < upper)
        label = f'[{lower:g},{upper:g})'
        speed_groups[label] = _masked_summary(bin_errors, mask)
    moving = speed > 1e-12
    directions = {'zero_speed': _masked_summary(bin_errors, ~moving)}
    angles = np.mod(np.arctan2(target[:, :, 1], target[:, :, 0]), 2 * np.pi)
    for quadrant in range(4):
        lower = quadrant * np.pi / 2
        upper = (quadrant + 1) * np.pi / 2
        mask = moving & (angles >= lower) & (angles < upper)
        label = f'[{quadrant * 90},{(quadrant + 1) * 90})_degrees'
        directions[label] = _masked_summary(bin_errors, mask)
    return {'conditions': conditions, 'speed_m_s': speed_groups, 'direction': directions}
