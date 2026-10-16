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


def test_calibration_mean_uses_only_the_named_label_prefix(monkeypatch, tmp_path):
    import json
    from cerebro import longitudinal

    generator = np.random.default_rng(14)
    recordings = {}
    for domain, date in [('source', '2020-01-01'), ('target', '2020-01-02')]:
        trials = []
        for row in range(10):
            position = np.full((3, 2), row / 10.)
            trials.append({'trial_id': row, 'counts': generator.poisson(3, (3, 3)),
                           'position': position, 'timestamps': row + np.arange(3) * .02,
                           'target': np.array([.5, .5])})
        recordings[domain] = {'trials': trials, 'subject_id': 'fixture',
                              'timestamps_reference_time': date + 'T00:00:00+00:00',
                              'metadata': {'position_units': ['flexion units'] * 2},
                              'channel_keys': [('a', 'b', index, index, index, index) for index in range(3)]}
    manifest_paths = {}
    for domain in recordings:
        path = tmp_path / (domain + '.json')
        path.write_text(json.dumps({'fixture': domain, 'sha256': domain}))
        manifest_paths[domain] = str(path)
    config = {'source_manifest': manifest_paths['source'], 'target_manifest': manifest_paths['target'],
              'source_training_trials': 6, 'source_inner_training_trials': 4,
              'target_calibration_pool_trials': 4, 'calibration_budgets': [1, 2, 4],
              'ridge_alphas': [1.], 'latent_dimensions': 1, 'anchor_min_repetitions': 10,
              'bootstrap_draws': 10, 'bootstrap_trial_block': 2, 'seed': 14}
    config_path = tmp_path / 'experiment.json'
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(longitudinal, 'load_link', lambda manifest: recordings[manifest['fixture']])
    longitudinal.run(config_path, tmp_path / 'first')
    for trial in recordings['target']['trials'][4:]:
        trial['position'] += 100
    longitudinal.run(config_path, tmp_path / 'changed')
    with np.load(tmp_path / 'first' / 'arrays.npz') as first:
        with np.load(tmp_path / 'changed' / 'arrays.npz') as changed:
            for budget, expected in [(1, 0.), (2, .05), (4, .15)]:
                key = 'target_calibration_mean_' + str(budget)
                np.testing.assert_allclose(first[key], [expected, expected])
                np.testing.assert_array_equal(first[key], changed[key])
                np.testing.assert_array_equal(first[key + '_prediction_flexion'],
                                              changed[key + '_prediction_flexion'])
