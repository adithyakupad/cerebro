"""Synthetic fixtures test arithmetic and split boundaries, not neural findings."""

import numpy as np
import pytest

from cerebro.research_dynamics import (
    evaluate, fitted_source, iterate_transition, matched_conditions,
    parameter_arrays, projection_errors, reconstructed, restore_forecast, rotation_error, temporal_gate, trial_transitions,
)


def trials_fixture():
    generator = np.random.default_rng(13)
    trials = []
    for index, length in enumerate((12, 14, 17, 19, 22, 25)):
        counts = generator.poisson(2, size=(length, 5))
        position = counts[:, :2] / 10
        trials.append({'counts': counts, 'position': position,
                       'target': np.asarray([index % 2, 0]), 'trial_id': index})
    return trials


def test_transitions_never_bridge_trials():
    first = np.arange(6)[:, None]
    second = np.arange(100, 108)[:, None]
    previous, following = trial_transitions([first, second], 2)
    assert previous.shape == (10, 1)
    np.testing.assert_array_equal(following - previous, 2)
    assert not np.any((previous < 100) & (following >= 100))
    for horizon in (0, True, 3.5, 8):
        with pytest.raises(ValueError):
            trial_transitions([first, second], horizon)


def test_train_only_parameters_and_calibration_feature():
    trials = trials_fixture()
    training = trials[:4]
    evaluation = trials[4:]
    model = fitted_source(training, dimension=2)
    expected_mean = np.concatenate([trial['counts'] for trial in training]).mean(axis=0)
    np.testing.assert_allclose(model['scaler'].mean_, expected_mean)
    baseline = projection_errors(model, evaluation)
    altered_labels = [{**trial, 'position': trial['position'] + 1000, 'target': np.array([100, 100])} for trial in evaluation]
    np.testing.assert_array_equal(projection_errors(model, altered_labels), baseline)
    np.testing.assert_array_equal(model['scaler'].mean_, expected_mean)


@pytest.mark.parametrize('kind', ['pca', 'fa'])
def test_forecasts_rotation_and_reproduction(kind):
    trials = trials_fixture()
    first = fitted_source(trials[:4], dimension=2, kind=kind)
    second = fitted_source(trials[:4], dimension=2, kind=kind)
    np.testing.assert_allclose(first['population'].components_, second['population'].components_, atol=0, rtol=0)
    assert rotation_error(first, trials[4]['counts']) < 1e-12
    replay = restore_forecast(parameter_arrays(first), trials[4]['counts'], kind, 5)
    coordinates = first['population'].transform(first['scaler'].transform(trials[4]['counts']))
    future = iterate_transition(coordinates[:-5], first['transition'], 5)
    expected_counts = first['scaler'].inverse_transform(reconstructed(first, future))
    np.testing.assert_allclose(replay, expected_counts, atol=1e-12)
    config = {'forecast_horizons_bins': [1, 5], 'bootstrap_draws': 20,
              'bootstrap_block_trials': 1, 'random_seed': 10}
    metrics = evaluate(first, trials[4:], first['scaler'], np.arange(5), config)
    expected = projection_errors(first, trials[4:])
    np.testing.assert_allclose(metrics['h1_latent_ar_neural_mse']['per_trial'], expected)
    assert metrics['h5_latent_ar_neural_mse']['mean_trial'] >= 0
    if kind == 'fa':
        assert np.isfinite(metrics['fa_loglikelihood_reference_per_bin']['mean_trial'])
    initial = first['population'].transform(first['scaler'].transform(trials[4]['counts']))
    direct = first['transition'].predict(first['transition'].predict(initial))
    np.testing.assert_allclose(iterate_transition(initial, first['transition'], 2), direct)


def test_condition_control_excludes_unsupported_commands():
    trials = trials_fixture()
    model = fitted_source(trials[:4], dimension=2)
    unseen = {**trials[-1], 'target': np.asarray([99, 99])}
    result = matched_conditions(trials[:4], trials[:4], [trials[-2], unseen], model['scaler'], np.arange(5))
    assert result['command_condition_mean_control_trial_ids'] == [4, 5]
    assert result['command_condition_mean_control_unknown_trial_ids'] == [5]
    assert len(result['conditions_with_two_repetitions_each']) == 2


def test_temporal_gate_requires_all_fixed_controls():
    metrics = {'h1_latent_ar_neural_mse': {'per_trial': [0.9] * 10}}
    for control in ('neural_persistence', 'training_mean', 'permuted_training_ar'):
        metrics[f'h1_{control}_neural_mse'] = {'per_trial': [1.] * 10}
    comparison = {'fit': 'source', 'model': 'pca', 'dimension': 6, 'metrics': metrics}
    sessions = [{'comparisons': [comparison]} for _ in range(3)]
    config = {'random_seed': 13, 'primary_dimension': 6, 'bootstrap_draws': 20,
              'bootstrap_block_trials': 5, 'practical_relative_improvement': .05}
    assert temporal_gate(sessions, config)['passed']
    metrics['h1_training_mean_neural_mse']['per_trial'] = [.93] * 10
    assert not temporal_gate(sessions, config)['passed']
