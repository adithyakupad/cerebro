"""Synthetic checks for M026 information access and trial-aware summaries."""

import numpy as np
import pytest
import torch

from cerebro.neural_information_controls import (
    condition_donors,
    condition_template,
    input_features,
    stratified_summary,
)
from cerebro.sequence_models import make_sequence_model


def test_inputs_remove_neural_values_and_clock_preserves_right_edge():
    counts = np.arange(2 * 70 * 3).reshape(2, 70, 3)
    original = counts.copy()
    zero = input_features(counts, 'zero')
    clock = input_features(counts, 'clock')
    neural = input_features(counts, 'neural')
    np.testing.assert_array_equal(zero, np.zeros_like(counts))
    np.testing.assert_allclose(clock[0, :, 0], -.4 + .02 * np.arange(1, 71))
    np.testing.assert_array_equal(clock[0], clock[1])
    np.testing.assert_array_equal(clock[:, :, 0], clock[:, :, 2])
    np.testing.assert_array_equal(neural, counts)
    neural[0, 0, 0] = -1
    np.testing.assert_array_equal(counts, original)
    np.testing.assert_array_equal(input_features(counts + 100, 'clock'), clock)


def test_constant_cnn_has_no_interior_phase_information():
    torch.manual_seed(26)
    model = make_sequence_model('temporal_cnn', 3, 32, 2)
    features = torch.ones(2, 70, 3, dtype=torch.float64)
    model = model.double().eval()
    with torch.no_grad():
        prediction = model(features).numpy()
    expected = np.broadcast_to(prediction[:, 4:5], prediction[:, 4:].shape)
    np.testing.assert_array_equal(prediction[:, 4:], expected)


@pytest.mark.parametrize('counts,mode', [
    (np.zeros((2, 0, 3)), 'zero'),
    (np.zeros((2, 3)), 'zero'),
    (np.full((1, 5, 2), np.nan), 'clock'),
    (-np.ones((1, 5, 2)), 'neural'),
    (np.ones((1, 5, 2)), 'unknown'),
])
def test_input_validation(counts, mode):
    with pytest.raises(ValueError):
        input_features(counts, mode)


def test_donors_are_global_deranged_split_local_and_reproducible():
    keys = np.array(['a', 'b', 'a', 'x', 'a', 'b', 'a', 'b'])
    recipients = np.array([7, 4, 3, 1, 0, 2])
    donors = condition_donors(keys, recipients, 26)
    np.testing.assert_array_equal(donors, condition_donors(keys, recipients, 26))
    np.testing.assert_array_equal(keys[donors], keys[recipients])
    np.testing.assert_array_equal(np.sort(donors), np.sort(recipients))
    singleton = recipients == 3
    np.testing.assert_array_equal(donors[singleton], recipients[singleton])
    assert np.all(donors[~singleton] != recipients[~singleton])
    assert not np.any(np.isin(donors, [5, 6]))
    untouched_keys = keys.copy()
    untouched_keys[[5, 6]] = ['unseen_a', 'unseen_b']
    np.testing.assert_array_equal(donors, condition_donors(untouched_keys, recipients, 26))


@pytest.mark.parametrize('indices', [[0, 0], [-1], [8], [True, False], [1.5]])
def test_invalid_donor_indices_rejected(indices):
    with pytest.raises(ValueError):
        condition_donors(np.array(['a'] * 8), np.asarray(indices), 26)


def test_singleton_and_empty_donors():
    keys = np.array(['a', 'b'])
    np.testing.assert_array_equal(condition_donors(keys, np.array([1]), 26), [1])
    assert condition_donors(keys, np.array([], dtype=int), 26).shape == (0,)


def test_condition_template_train_only_means_and_unseen_fallback():
    targets = np.array([np.ones((5, 2)), np.full((5, 2), 3.), np.full((5, 2), 10.)])
    predictions, fallback = condition_template(targets, ['a', 'a', 'b'], ['b', 'new', 'a'])
    np.testing.assert_array_equal(predictions[0], 10.)
    np.testing.assert_allclose(predictions[1], 14 / 3)
    np.testing.assert_array_equal(predictions[2], 2.)
    np.testing.assert_array_equal(fallback, [False, True, False])
    assert predictions.shape == (3, 5, 2)
    empty, empty_fallback = condition_template(targets, ['a', 'a', 'b'], [])
    assert empty.shape == (0, 5, 2)
    assert empty_fallback.shape == (0,)


@pytest.mark.parametrize('targets,keys', [
    (np.empty((0, 5, 2)), []),
    (np.zeros((1, 5, 1)), ['a']),
    (np.full((1, 5, 2), np.inf), ['a']),
    (np.zeros((2, 5, 2)), ['a']),
])
def test_template_validation(targets, keys):
    with pytest.raises(ValueError):
        condition_template(targets, keys, ['a'])


def test_strata_equal_trial_weight_not_pooled_bin_weight():
    target = np.array([[[0., 0.], [.2, 0.]], [[0., 0.], [0., 0.]]])
    prediction = target + np.array([[[1., 1.], [1., 1.]], [[3., 3.], [3., 3.]]])
    result = stratified_summary(target, prediction, ['a', 'b'], start=0)
    low_speed = result['speed_m_s']['[0,0.1)']
    assert low_speed['num_bins'] == 3
    assert low_speed['num_trials'] == 2
    assert low_speed['equal_trial_mse'] == 5.
    assert low_speed['trial_mse'] == [1., 9.]
    assert result['conditions']['a']['equal_trial_mse'] == 1.
    assert result['conditions']['b']['equal_trial_mse'] == 9.
    assert result['speed_m_s']['[0.5,inf)']['equal_trial_mse'] is None


def test_direction_boundaries_zero_speed_and_start_exclusion():
    target = np.array([[[1., 1.], [0., 0.], [.1, 0.], [0., .25], [-.5, 0.], [0., -.2]]])
    prediction = target.copy()
    prediction[:, 0] = 100.
    result = stratified_summary(target, prediction, ['a'], start=1)
    assert result['conditions']['a']['equal_trial_mse'] == 0.
    groups = result['direction']
    assert groups['zero_speed']['num_bins'] == 1
    for quadrant in range(4):
        label = f'[{quadrant * 90},{(quadrant + 1) * 90})_degrees'
        assert groups[label]['num_bins'] == 1
    assert result['speed_m_s']['[0,0.1)']['num_bins'] == 1
    assert result['speed_m_s']['[0.1,0.25)']['num_bins'] == 2
    assert result['speed_m_s']['[0.25,0.5)']['num_bins'] == 1
    assert result['speed_m_s']['[0.5,inf)']['num_bins'] == 1


@pytest.mark.parametrize('prediction,start', [
    (np.zeros((2, 5, 1)), 0),
    (np.full((2, 5, 2), np.nan), 0),
    (np.zeros((2, 5, 2)), -1),
    (np.zeros((2, 5, 2)), 5),
    (np.zeros((2, 5, 2)), True),
])
def test_strata_validation(prediction, start):
    with pytest.raises(ValueError):
        stratified_summary(np.zeros((2, 5, 2)), prediction, ['a', 'b'], start=start)
