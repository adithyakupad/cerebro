"""Prospective-access and session isolation tests using synthetic fixtures."""

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler

from cerebro.population import fit_decoder
from cerebro.reliability import (balanced_accuracy, calibration_features, conditional_risk_interval,
                                 evaluate_risk, fit_risk, predict_risk, session_folds)
from cerebro.research_dynamics import fitted_source, projection_errors


def fixture_trials():
    generator = np.random.default_rng(8)
    trials = []
    for index in range(9):
        counts = generator.poisson(3, (12 + index, 5))
        trials.append({'counts': counts, 'position': counts[:, :2] / 10,
                       'target': np.array([index % 3, 0]), 'trial_id': index})
    return trials


def test_calibration_features_only_budget_resampling_and_reproduction():
    trials = fixture_trials()
    training = trials[:6]
    selected = trials[6:8]
    counts = np.concatenate([row['counts'] for row in training])
    position = np.concatenate([row['position'] for row in training])
    scaler = StandardScaler().fit(counts)
    decoder = fit_decoder(scaler.transform(counts), position, alpha=1000.)
    neural = fitted_source(training, dimension=2)
    training_error = projection_errors(neural, training).mean()
    first, _, indices = calibration_features(selected, counts, scaler, decoder, position, 3, neural,
                                               training_error, 4, 9)
    second, _, repeat = calibration_features(selected, counts, scaler, decoder, position, 3, neural,
                                               training_error, 4, 9)
    np.testing.assert_array_equal(first, second)
    assert repeat == indices
    assert first.shape == (9,)
    assert all(len(draw) == 2 and set(draw) <= {0, 1} for draw in indices)
    assert first[0] == pytest.approx(2 / 3)


def test_session_folds_and_training_only_feature_scaler():
    sessions = np.repeat(['a', 'b', 'c'], 4)
    features = np.arange(24.).reshape(12, 2)
    outcomes = np.arange(12.)
    for identity, training, testing in session_folds(sessions):
        assert not set(sessions[training]) & set(sessions[testing])
        model = fit_risk(features[training], outcomes[training], [0])
        np.testing.assert_array_equal(model[0].mean_, features[training, :1].mean(axis=0))
        assert predict_risk(model, features[testing], [0]).shape == (4,)
    with pytest.raises(ValueError):
        list(session_folds(np.repeat(['a', 'b'], 4)))


def test_single_class_balanced_accuracy_is_undefined():
    assert balanced_accuracy([True, True], [True, False]) is None
    assert balanced_accuracy([True, False], [True, False]) == 1
    assert balanced_accuracy([True, False], [False, True]) == 0


def test_shared_trial_uncertainty_reproduces_and_identical_control_zero():
    generator = np.random.default_rng(3)
    values = generator.normal(size=(12, 10))
    sessions = np.repeat(['a', 'b', 'c'], 4)
    predictions = np.linspace(-1, 1, 12)
    config = {'random_seed': 23, 'bootstrap_block_trials': 2, 'bootstrap_draws': 20}
    interval = conditional_risk_interval(predictions, predictions, values, sessions, config)
    np.testing.assert_array_equal(interval, [0., 0.])
    other = conditional_risk_interval(predictions, predictions + 1, values, sessions, config)
    assert other == conditional_risk_interval(predictions, predictions + 1, values, sessions, config)


def test_whole_session_risk_evaluation_reproducible_and_null_safe():
    generator = np.random.default_rng(12)
    rows = []
    for session in ('a', 'b', 'c'):
        for policy in ('uniform', 'chronological'):
            draws = 4 if policy == 'uniform' else 1
            for draw in range(draws):
                rows.append({'budget': 15, 'session': session, 'policy': policy,
                             'features': generator.normal(size=9).tolist(),
                             'trial_difference': np.full(10, .01).tolist(), 'frozen_mse': .1})
    config = {'budgets': [15], 'primary_budget': 15, 'random_seed': 23,
              'bootstrap_block_trials': 2, 'bootstrap_draws': 20,
              'reliability_ridge_alpha': 1., 'practical_relative_improvement': .05,
              'minimum_balanced_accuracy': .6}
    first, arrays = evaluate_risk(rows, config)
    second, repeated = evaluate_risk(rows, config)
    assert first == second
    assert first['selected_method'] is None
    assert all(row['balanced_accuracy'] is None for row in first['promotion'])
    for name in arrays:
        np.testing.assert_array_equal(arrays[name], repeated[name])
