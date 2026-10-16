import json

import numpy as np
import pytest
import torch

from cerebro import representation_transfer
from cerebro.representation_benchmark import RepresentationGRU


def fixture_recordings():
    generator = np.random.default_rng(17)
    recordings = []
    keys = [('array', 'bank', index, 0, index, index) for index in range(3)]
    for session_index in range(3):
        trials = []
        for trial_index in range(5):
            trials.append({
                'trial_id': trial_index + 1, 'counts': generator.poisson(1, (4, 3)),
                'position': generator.normal(size=(4, 2)),
                'position_valid': np.ones(4, dtype=bool),
                'timestamps': trial_index + np.arange(4) * .020,
                'target_style': 'test-only fixture',
            })
        recordings.append({
            'trials': trials, 'channel_keys': keys, 'subject_id': 'synthetic-fixture',
            'timestamps_reference_time': '2020-01-0' + str(session_index + 1) + 'T00:00:00+00:00',
            'metadata': {'position_units': ['flexion', 'flexion']},
            'native_metadata': {'unit_conflict': 'synthetic test fixture'},
        })
    return recordings


def fixture_config(tmp_path):
    paths = []
    for index in range(3):
        manifest = tmp_path / ('manifest_' + str(index) + '.json')
        manifest.write_text(json.dumps({'fixture_index': index}))
        paths.append(str(manifest))
    config = {
        'source_manifests': paths[:2], 'target_manifest': paths[2],
        'native_bins_per_trial': 4, 'source_reserved_trials': 2,
        'source_probe_trials_each': 3,
        'native_clock_step_tolerance_seconds': .0011,
        'target_calibration_trials': 2, 'target_evaluation_trials': 3,
        'seeds': [0], 'label_budgets': [1, 2], 'supervised_epochs': 1,
        'learning_rate': .001, 'gradient_clip': 1., 'mask_probability': .5,
        'ridge_alpha': 1.,
        'settings': [{'name': 'fixture', 'hidden': 4, 'source_trials_each': 3, 'epochs': 1}],
    }
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config))
    return config, path


def test_prepare_preserves_clock_channel_mapping_and_chronology(tmp_path):
    recordings = fixture_recordings()
    config, _ = fixture_config(tmp_path)
    target = recordings[2]
    target['channel_keys'] = target['channel_keys'][::-1]
    for trial in target['trials']:
        trial['counts'] = trial['counts'][:, ::-1]
    sessions, mappings, ranges = representation_transfer.prepare_sessions(recordings, config)
    assert sessions[2]['counts'].shape == (5, 4, 3)
    assert mappings[2] == [2, 1, 0]
    np.testing.assert_array_equal(sessions[2]['timestamps'][0], target['trials'][0]['timestamps'])
    assert ranges[0][1] < ranges[1][0] < ranges[2][0]
    recordings[2]['subject_id'] = 'different'
    with pytest.raises(ValueError):
        representation_transfer.prepare_sessions(recordings, config)


def test_prepare_rejects_overlapping_trials_and_missing_samples(tmp_path):
    recordings = fixture_recordings()
    config, _ = fixture_config(tmp_path)
    recordings[0]['trials'][1]['timestamps'] = recordings[0]['trials'][0]['timestamps'].copy()
    with pytest.raises(ValueError):
        representation_transfer.prepare_sessions(recordings, config)
    recordings = fixture_recordings()
    recordings[2]['trials'][0]['position_valid'][0] = False
    with pytest.raises(ValueError):
        representation_transfer.prepare_sessions(recordings, config)


def test_source_scaler_invariant_to_target_counts():
    source = np.arange(24).reshape(2, 4, 3)
    target = np.ones((2, 4, 3))
    first_source, _, first = representation_transfer.source_standardization(source, target)
    second_source, _, second = representation_transfer.source_standardization(source, target * 1000)
    np.testing.assert_array_equal(first_source, second_source)
    for name in first:
        np.testing.assert_array_equal(first[name], second[name])


def test_native_clock_jitter_is_disclosed_without_resampling(tmp_path):
    recordings = fixture_recordings()
    config, _ = fixture_config(tmp_path)
    original_times = recordings[0]['trials'][0]['timestamps']
    jittered_times = original_times + [0, .001, 0, .001]
    recordings[0]['trials'][0]['timestamps'] = jittered_times
    sessions, _, _ = representation_transfer.prepare_sessions(recordings, config)
    np.testing.assert_array_equal(sessions[0]['timestamps'][0], jittered_times)
    recordings[0]['trials'][0]['timestamps'][1] += .005
    with pytest.raises(ValueError):
        representation_transfer.prepare_sessions(recordings, config)


def test_causal_hidden_state_prefix():
    torch.manual_seed(7)
    model = RepresentationGRU(3, 4)
    features = torch.randn(2, 6, 3)
    full = representation_transfer._encoded(model, features)
    prefix = representation_transfer._encoded(model, features[:, :3])
    np.testing.assert_allclose(full[:, :3], prefix, atol=1e-7)


def test_runner_restore_reproducibility_and_target_mutation(monkeypatch, tmp_path):
    recordings = fixture_recordings()
    config, path = fixture_config(tmp_path)
    monkeypatch.setattr(representation_transfer, 'load_link', lambda manifest: recordings[manifest['fixture_index']])
    first = representation_transfer.run(path, tmp_path / 'first')
    second = representation_transfer.run(path, tmp_path / 'second')
    assert first == second
    assert len(first['results']) == 10
    assert first['splits']['fixture']['target_evaluation'] == [3, 4, 5]
    assert first['pretraining'][0]['source_shape'] == [6, 4, 3]
    assert all(row['checkpoint_restored_predictions_identical'] for row in first['results'])
    for trial in recordings[2]['trials']:
        trial['counts'] += 100
        trial['position'] += 100
    changed = representation_transfer.run(path, tmp_path / 'changed')
    assert first['pretraining'] == changed['pretraining']
    for original, mutated in zip(first['results'], changed['results']):
        if original['target_label_budget'] == 0:
            assert original['checkpoint_sha256'] == mutated['checkpoint_sha256']


def test_source_reserved_trial_mutation_cannot_change_fits(monkeypatch, tmp_path):
    recordings = fixture_recordings()
    _, path = fixture_config(tmp_path)
    monkeypatch.setattr(representation_transfer, 'load_link', lambda manifest: recordings[manifest['fixture_index']])
    first = representation_transfer.run(path, tmp_path / 'first')
    for recording in recordings[:2]:
        for trial in recording['trials'][-2:]:
            trial['counts'] += 1000
            trial['position'] += 1000
    changed = representation_transfer.run(path, tmp_path / 'changed')
    assert first['pretraining'] == changed['pretraining']
    for original, mutated in zip(first['results'], changed['results']):
        assert original['checkpoint_sha256'] == mutated['checkpoint_sha256']
        assert original['mse_native_position_squared'] == mutated['mse_native_position_squared']
    for original, mutated in zip(first['session_identity_diagnostics'], changed['session_identity_diagnostics']):
        assert original['checkpoint_sha256'] == mutated['checkpoint_sha256']
        assert original['training_trial_rows'] == 6
        assert original['evaluation_trial_rows'] == 4


def test_identity_probe_uses_trial_means_and_fixed_source_labels():
    latent = np.array([[[-2., 0], [-2., 1]], [[-1., 0], [-1., 1]],
                       [[1., 0], [1., 1]], [[2., 0], [2., 1]]])
    labels = np.array([0, 0, 1, 1])
    classifier, prediction, accuracy = representation_transfer.session_identity_probe(
        latent, labels, latent, labels,
    )
    assert accuracy == 1
    np.testing.assert_array_equal(prediction, labels)
    assert classifier.n_features_in_ == 2
    assert classifier.C == 1 and classifier.max_iter == 1000


def test_outer_evaluation_cannot_change_any_fitted_checkpoint(monkeypatch, tmp_path):
    recordings = fixture_recordings()
    _, path = fixture_config(tmp_path)
    monkeypatch.setattr(representation_transfer, 'load_link', lambda manifest: recordings[manifest['fixture_index']])
    first = representation_transfer.run(path, tmp_path / 'first')
    for trial in recordings[2]['trials'][2:]:
        trial['counts'] += 1000
        trial['position'] += 1000
    changed = representation_transfer.run(path, tmp_path / 'changed')
    assert first['pretraining'] == changed['pretraining']
    for original, mutated in zip(first['results'], changed['results']):
        assert original['checkpoint_sha256'] == mutated['checkpoint_sha256']
        assert original['history'] == mutated['history']
