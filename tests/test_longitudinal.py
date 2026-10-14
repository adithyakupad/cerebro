"""Boundary-preserving longitudinal metrics and calibration checks."""

import numpy as np
import pytest

from cerebro.longitudinal import flatten, trial_losses, block_interval, condition_anchors


def test_variable_length_trials_metrics_preserve_identity():
    trials = [
        {'position': np.zeros((2, 2)), 'counts': np.ones((2, 2))},
        {'position': np.ones((3, 2)), 'counts': np.ones((3, 2)) * 2},
    ]
    prediction = np.zeros((5, 2))
    np.testing.assert_allclose(trial_losses(trials, prediction), [0, 1])
    np.testing.assert_array_equal(flatten(trials, 'counts', [1, 0]), [[1, 1], [1, 1], [2, 2], [2, 2], [2, 2]])
    with pytest.raises(ValueError):
        trial_losses(trials, prediction[:-1])


def test_block_bootstrap_is_reproducible_and_constant():
    values = np.arange(20.)
    assert block_interval(values, 100, 5, 8) == block_interval(values, 100, 5, 8)
    assert block_interval(np.ones(20), 100, 5, 8) == [1, 1]
    with pytest.raises(ValueError):
        block_interval(values[:3], 10, 5, 0)


def test_condition_anchors_use_trials_not_bins_as_repetitions():
    trials = [
        {'counts': np.zeros((2, 3)), 'target': np.array([.5, .5])},
        {'counts': np.zeros((3, 3)), 'target': np.array([.5, .5])},
        {'counts': np.zeros((2, 3)), 'target': np.array([.1, .5])},
    ]
    latent = np.array([[1., 2.]] * 2 + [[3., 4.]] * 3 + [[7., 8.]] * 2)
    anchors = condition_anchors(trials, latent, minimum=2)
    assert set(anchors) == {(.5, .5)}
    np.testing.assert_allclose(anchors[(.5, .5)], [2, 3])


def test_chronology_rejects_duplicate_overlap_and_reordered_trials():
    from cerebro.longitudinal import validate_chronology
    recording = {
        'timestamps_reference_time': '2020-01-01T00:00:00+00:00',
        'trials': [
            {'trial_id': 10, 'timestamps': np.array([1., 1.02])},
            {'trial_id': 20, 'timestamps': np.array([2., 2.02])},
        ],
    }
    start, stop = validate_chronology(recording)
    assert stop - start == pytest.approx(1.02)
    recording['trials'].reverse()
    with pytest.raises(ValueError, match='chronological'):
        validate_chronology(recording)
    recording['trials'].reverse()
    recording['trials'][1]['trial_id'] = 10
    with pytest.raises(ValueError, match='unique'):
        validate_chronology(recording)
    recording['trials'][1]['trial_id'] = 20
    recording['trials'][1]['timestamps'] = np.array([1.02, 1.04])
    with pytest.raises(ValueError, match='nonoverlapping'):
        validate_chronology(recording)
