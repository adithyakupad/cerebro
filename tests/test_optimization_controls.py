"""Synthetic controls check temporal boundaries and training-only information."""

import numpy as np
import pytest

from cerebro.optimization_controls import history_features, predict_controls, train_controls


def fixture():
    generator = np.random.default_rng(25)
    training_counts = generator.poisson(2, size=(5, 9, 3))
    evaluation_counts = generator.poisson(3, size=(2, 9, 3))
    training_velocity = generator.normal(size=(5, 9, 2))
    evaluation_velocity = generator.normal(size=(2, 9, 2))
    return training_counts, training_velocity, evaluation_counts, evaluation_velocity


def test_history_order_and_trial_boundaries():
    counts = np.arange(2 * 7 * 2).reshape(2, 7, 2)
    features = history_features(counts)
    assert features.shape == (2, 3, 10)
    for trial in range(2):
        for bin_index in range(3):
            expected = counts[trial, bin_index:bin_index + 5].reshape(-1)
            np.testing.assert_array_equal(features[trial, bin_index], expected)
    altered = counts.copy()
    altered[0] += 100
    np.testing.assert_array_equal(history_features(altered)[1], features[1])


def test_scaling_selection_and_checkpoint_restoration(tmp_path):
    training_counts, training_velocity, evaluation_counts, evaluation_velocity = fixture()
    result = train_controls(training_counts, training_velocity, evaluation_counts, evaluation_velocity, [1, 10])
    parameters = result['parameters']
    np.testing.assert_array_equal(parameters['scaler_mean'], training_counts.reshape(-1, 3).mean(axis=0))
    np.testing.assert_array_equal(parameters['scaler_scale'], training_counts.reshape(-1, 3).std(axis=0))
    assert len(result['selection']) == 6
    for kind, alpha in result['selected_alphas'].items():
        candidates = [row for row in result['selection'] if row['model'] == kind]
        expected = min(candidates, key=lambda row: row['mse_m2_s2'])
        assert alpha == expected['alpha']
    checkpoint = tmp_path / 'controls.npz'
    np.savez(checkpoint, **parameters)
    with np.load(checkpoint, allow_pickle=False) as saved:
        restored = predict_controls(dict(saved), evaluation_counts)
    for kind, prediction in result['predictions'].items():
        assert prediction.shape == (2, 9, 2)
        np.testing.assert_array_equal(prediction, restored[kind])
        assert np.isfinite(prediction[:, 4:]).all()
    assert np.isnan(restored['history_ridge'][:, :4]).all()
    np.testing.assert_array_equal(restored['mean'][0, 0], training_velocity.mean(axis=(0, 1)))
    np.testing.assert_array_equal(restored['go_time_template'][0], training_velocity.mean(axis=0))


def test_fixed_alphas_ignore_evaluation_targets_and_counts_for_fitting():
    training_counts, training_velocity, evaluation_counts, evaluation_velocity = fixture()
    fixed = {'ridge': 1, 'history_ridge': 10, 'kalman': 1}
    original = train_controls(training_counts, training_velocity, evaluation_counts, evaluation_velocity, [1, 10], fixed)
    changed = train_controls(training_counts, training_velocity, evaluation_counts + 100, None, [1, 10], fixed)
    assert original['selection'] == changed['selection'] == []
    assert original['selected_alphas'] == changed['selected_alphas'] == fixed
    for name, value in original['parameters'].items():
        np.testing.assert_array_equal(value, changed['parameters'][name])


def test_controls_are_deterministic_and_require_matching_dimensions():
    values = fixture()
    first = train_controls(*values, [1])
    second = train_controls(*values, [1])
    assert first['selection'] == second['selection']
    for kind in first['predictions']:
        np.testing.assert_array_equal(first['predictions'][kind], second['predictions'][kind])
    with pytest.raises(ValueError, match='dimensions differ'):
        train_controls(values[0], values[1], values[2][:, :, :2], values[3], [1])
    with pytest.raises(ValueError, match='two finite coordinates'):
        train_controls(values[0], values[1][:, :, :1], values[2], values[3], [1])
    with pytest.raises(ValueError, match='nonnegative'):
        train_controls(*values, [-1])


def test_prediction_is_causal_and_trial_local():
    training_counts, training_velocity, evaluation_counts, evaluation_velocity = fixture()
    result = train_controls(training_counts, training_velocity, evaluation_counts, evaluation_velocity, [1])
    altered_counts = evaluation_counts.copy()
    altered_counts[0, 6:] += 100
    altered_predictions = predict_controls(result['parameters'], altered_counts)
    for kind, original_prediction in result['predictions'].items():
        np.testing.assert_array_equal(original_prediction[0, :6], altered_predictions[kind][0, :6])
        np.testing.assert_array_equal(original_prediction[1], altered_predictions[kind][1])


def test_ridge_training_excludes_incomplete_history_targets():
    training_counts, training_velocity, evaluation_counts, evaluation_velocity = fixture()
    fixed = {'ridge': 1, 'history_ridge': 1, 'kalman': 1}
    original = train_controls(training_counts, training_velocity, evaluation_counts, None, [1], fixed)
    changed_velocity = training_velocity.copy()
    changed_velocity[:, :4] += 100
    changed = train_controls(training_counts, changed_velocity, evaluation_counts, None, [1], fixed)
    for name in ('ridge_coef', 'ridge_intercept', 'history_ridge_coef', 'history_ridge_intercept'):
        np.testing.assert_array_equal(original['parameters'][name], changed['parameters'][name])
