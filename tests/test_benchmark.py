"""Leakage and immutable split checks use fixtures, not neural claims."""

import json
from pathlib import Path

import numpy as np
import pytest

from cerebro.benchmark import split_manifest, save_immutable, trial_metrics, prepare
from cerebro.sense import load_recording


def test_split_manifest_disjoint_and_deterministic(tmp_path):
    data = {
        'trial_ids': np.arange(10),
        'splits': np.array(['train'] * 7 + ['val'] * 3),
        'unit_ids': np.array([101, 202]),
    }
    config = {'seed': 5, 'inner_validation_trials': 2}
    asset = {'sha256': 'fixture'}
    manifest = split_manifest(data, asset, config)
    assert manifest == split_manifest(data, asset, config)
    assert set(manifest['inner_training']).isdisjoint(manifest['inner_validation'])
    assert set(manifest['source_training']).isdisjoint(manifest['source_validation'])
    assert set(manifest['inner_training'] + manifest['inner_validation']) == set(range(7))
    path = tmp_path / 'splits.json'
    save_immutable(path, manifest)
    save_immutable(path, manifest)
    with pytest.raises(ValueError, match='differs'):
        save_immutable(path, {'changed': True})
    assert json.loads(path.read_text()) == manifest


def test_trial_metrics_and_degenerate_target():
    target = np.array([[[1., 2.], [3., 2.]], [[5., 2.], [7., 2.]]])
    prediction = target.copy()
    prediction[1, :, 0] += 2
    mse, r_squared = trial_metrics(target, prediction)
    np.testing.assert_allclose(mse, [0, 2])
    assert r_squared[0] == pytest.approx(.6)
    assert np.isnan(r_squared[1])
    with pytest.raises(ValueError):
        trial_metrics(target, prediction[0])
    target[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        trial_metrics(target, prediction)


def test_real_preparation_preserves_source_split_and_heldin_units():
    manifest_path = Path('configs/mc_maze_small.json')
    asset = json.loads(manifest_path.read_text())
    if not Path(asset['local_path']).exists():
        pytest.skip('Pinned real recording not acquired')
    config = json.loads(Path('configs/classical_05.json').read_text())
    recording = load_recording(asset['local_path'])
    data = prepare(recording, config)
    assert data['counts'].shape == (100, 70, 107)
    assert data['velocity'].shape == (100, 70, 2)
    assert len(data['exclusions']) == 0
    assert np.sum(data['splits'] == 'train') == 75
    assert np.sum(data['splits'] == 'val') == 25
    for index, trial_id in enumerate(data['trial_ids']):
        trial = recording.trials.loc[trial_id]
        assert data['splits'][index] == trial['split']
        assert data['right_seconds'][index, -1] <= trial.stop_time
    assert not recording.units.loc[data['unit_ids']].heldout.any()


def test_gaussian_likelihood_identity_covariance():
    from cerebro.benchmark import gaussian_log_likelihood
    class IdentityGaussian:
        mean_ = np.zeros(2)
        def get_covariance(self):
            return np.eye(2)
    observations = np.array([[0., 0.], [1., 0.]])
    expected = -np.log(2 * np.pi) - .25
    assert gaussian_log_likelihood(IdentityGaussian(), observations) == pytest.approx(expected)


def test_restored_decoder_and_baselines():
    from cerebro.benchmark import restore_prediction
    parameters = {
        'scaler_mean': np.array([2., 3.]), 'scaler_scale': np.array([2., 1.]),
        'ridge_coef': np.eye(2), 'ridge_intercept': np.array([.1, .2]),
        'mean_baseline': np.array([.3, .4]),
        'time_template_baseline': np.array([[.5, .6], [.7, .8]]),
    }
    counts = np.array([[[4., 4.], [2., 3.]]])
    restored = restore_prediction(parameters, 'ridge', counts)
    np.testing.assert_allclose(restored, [[[1.1, 1.2], [.1, .2]]])
    np.testing.assert_allclose(restore_prediction(parameters, 'mean', counts), [[[.3, .4], [.3, .4]]])
    np.testing.assert_allclose(restore_prediction(parameters, 'go_time_template', counts), [[[.5, .6], [.7, .8]]])
    with pytest.raises(ValueError):
        restore_prediction(parameters, 'ridge', -counts)
