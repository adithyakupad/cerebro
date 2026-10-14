from datetime import datetime, timezone
import hashlib
import json

import numpy as np
import pytest
from pynwb import NWBFile, NWBHDF5IO

from cerebro import cross_subject
from cerebro.falcon import load_falcon


def recordings_fixture():
    generator = np.random.default_rng(22)
    recordings = []
    for subject_index, trial_count in enumerate((20, 18)):
        trials = []
        unit_count = 3 + subject_index
        for row in range(trial_count):
            counts = generator.poisson(1, (5, unit_count))
            mean_count = counts.mean(axis=1)
            targets = np.column_stack([mean_count, mean_count * .5])
            left = row + np.arange(5) * .020
            trials.append({
                'trial_id': row + 100, 'counts': counts,
                'targets': targets, 'neural_valid': np.ones(counts.shape, dtype=bool),
                'target_valid': np.ones(5, dtype=bool), 'source_eval_mask': np.ones(5, dtype=bool),
                'timestamps': left, 'bin_right_seconds': left + .020,
            })
        recordings.append({
            'subject_id': 'fixture_subject_' + str(subject_index),
            'muscle_names': ['fixture_muscle_a', 'fixture_muscle_b'],
            'source_target_units': ['mV', 'mV'],
            'unit_keys': [(str(subject_index), unit) for unit in range(unit_count)],
            'metadata': {'target_interpretation': 'synthetic software fixture'}, 'trials': trials,
        })
    return recordings


def config_fixture(tmp_path):
    paths = []
    for index in range(2):
        path = tmp_path / ('manifest_' + str(index) + '.json')
        path.write_text(json.dumps({'fixture_index': index, 'sha256': 'test-only-' + str(index)}))
        paths.append(str(path))
    config = {
        'source_manifest': paths[0], 'target_manifest': paths[1],
        'source_training_trials': 12, 'source_inner_training_trials': 8,
        'target_calibration_trials': 6, 'label_budgets': [2, 6],
        'ridge_alphas': [1., 10.], 'uncertainty_block_lengths': [1, 2],
        'bootstrap_draws': 30, 'seed': 12,
    }
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config))
    return path


def test_anonymous_features_are_unit_permutation_invariant():
    counts = np.array([[0, 1, 3, 2], [2, 2, 0, 1]])
    first = cross_subject.anonymous_features(counts)
    permuted = cross_subject.anonymous_features(counts[:, [2, 0, 3, 1]])
    np.testing.assert_array_equal(first, permuted)
    assert first.shape == (2, 7)
    assert first[0, 0] == 1.5
    assert first[0, 2] == .25
    with pytest.raises(ValueError):
        cross_subject.anonymous_features([[0, -1]])


def test_missing_coverage_and_masks_preserve_original_indices():
    recording = recordings_fixture()[0]
    trial = recording['trials'][0]
    trial['neural_valid'][1, 0] = False
    trial['counts'][1, 0] = -1
    trial['source_eval_mask'][2] = False
    trial['target_valid'][3] = False
    recording['trials'][1]['neural_valid'][:] = False
    trials, excluded = cross_subject.prepare_trials(recording)
    np.testing.assert_array_equal(trials[0]['native_sample_indices'], [0, 4])
    assert trials[1]['original_trial_row'] == 2
    assert excluded[0]['trial_id'] == 101
    assert excluded[0]['whole_trial_excluded']
    assert trials[0]['audit']['excluded_samples_union'] == 3


def test_overlapping_trial_bins_rejected_and_losses_trial_weighted():
    recording = recordings_fixture()[0]
    recording['trials'][1]['timestamps'] = recording['trials'][0]['timestamps'].copy()
    recording['trials'][1]['bin_right_seconds'] = recording['trials'][0]['bin_right_seconds'].copy()
    with pytest.raises(ValueError):
        cross_subject.prepare_trials(recording)
    trials = [{'targets': np.zeros((1, 2))}, {'targets': np.zeros((3, 2))}]
    prediction = np.array([[1., 1.], [2., 2.], [2., 2.], [2., 2.]])
    losses = cross_subject.trial_losses(trials, prediction)
    np.testing.assert_array_equal(losses, [1, 4])
    assert losses.mean() == 2.5


def test_missing_observation_intervals_rejected_in_actual_nwb_adapter(tmp_path):
    path = tmp_path / 'missing_coverage.nwb'
    recording = NWBFile('synthetic software fixture', 'test', datetime(2020, 1, 1, tzinfo=timezone.utc))
    recording.add_unit(id=1, spike_times=[.1, .2])
    with NWBHDF5IO(path, 'w') as writer:
        writer.write(recording)
    manifest = {'local_path': str(path), 'size_bytes': path.stat().st_size,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_split': 'held-in-calib'}
    with pytest.raises(ValueError, match='observation intervals'):
        load_falcon(manifest)


def test_run_restore_reproducibility_and_heldout_mutation(monkeypatch, tmp_path):
    recordings = recordings_fixture()
    config = config_fixture(tmp_path)
    monkeypatch.setattr(cross_subject, 'load_falcon', lambda manifest: recordings[manifest['fixture_index']])
    first = cross_subject.run(config, tmp_path / 'first')
    second = cross_subject.run(config, tmp_path / 'second')
    assert first == second
    assert all(row['checkpoint_restored_predictions_identical'] for row in first['results'])
    assert len(first['results']) == 10
    mean_controls = [row for row in first['results'] if row['control'] == 'target_calibration_mean']
    assert len(mean_controls) == 2
    for row in mean_controls:
        with np.load(tmp_path / 'first' / row['checkpoint_file']) as archive:
            np.testing.assert_array_equal(archive['coefficients'], 0)
    for recording, boundary in zip(recordings, (12, 6)):
        for trial in recording['trials'][boundary:]:
            trial['counts'] += 100
            trial['targets'] += 100
    changed = cross_subject.run(config, tmp_path / 'changed')
    assert first['source_selection'] == changed['source_selection']
    assert first['normalization'] == changed['normalization']
    for original, mutated in zip(first['results'], changed['results']):
        assert original['checkpoint_sha256'] == mutated['checkpoint_sha256']


def test_missing_trial_does_not_shift_chronological_split_boundaries(monkeypatch, tmp_path):
    recordings = recordings_fixture()
    recordings[0]['trials'][0]['source_eval_mask'][:] = False
    recordings[1]['trials'][0]['source_eval_mask'][:] = False
    config = config_fixture(tmp_path)
    monkeypatch.setattr(cross_subject, 'load_falcon', lambda manifest: recordings[manifest['fixture_index']])
    report = cross_subject.run(config, tmp_path / 'run')
    assert report['splits']['source_training'] == list(range(101, 112))
    assert report['splits']['source_evaluation'][0] == 112
    assert report['splits']['target_calibration'] == list(range(101, 106))
    assert report['splits']['target_evaluation'][0] == 106
    assert report['splits']['target_label_budgets']['2'] == [101]


def test_cross_subject_same_identity_or_muscle_mismatch_rejected(monkeypatch, tmp_path):
    recordings = recordings_fixture()
    config = config_fixture(tmp_path)
    monkeypatch.setattr(cross_subject, 'load_falcon', lambda manifest: recordings[manifest['fixture_index']])
    recordings[1]['subject_id'] = recordings[0]['subject_id']
    with pytest.raises(ValueError, match='distinct observed subjects'):
        cross_subject.run(config, tmp_path / 'run')
    recordings = recordings_fixture()
    recordings[1]['muscle_names'] = ['wrong', 'wrong_other']
    with pytest.raises(ValueError, match='muscle names'):
        cross_subject.run(config, tmp_path / 'run')


def test_public_artifacts_render_actual_report_values(monkeypatch, tmp_path):
    recordings = recordings_fixture()
    config = config_fixture(tmp_path)
    for path in (tmp_path / 'manifest_0.json', tmp_path / 'manifest_1.json'):
        manifest = json.loads(path.read_text())
        manifest.update({'dandiset_id': 'synthetic-fixture', 'version': 'fixture', 'asset_id': path.stem})
        path.write_text(json.dumps(manifest))
    monkeypatch.setattr(cross_subject, 'load_falcon', lambda manifest: recordings[manifest['fixture_index']])
    report = cross_subject.run(config, tmp_path / 'run')
    report_path = tmp_path / 'public.json'
    markdown_path = tmp_path / 'public.md'
    figure_path = tmp_path / 'figures' / 'calibration.png'
    cross_subject.write_artifacts(report, report_path, markdown_path, figure_path)
    assert json.loads(report_path.read_text()) == report
    assert 'target_calibration_mean' in markdown_path.read_text()
    assert 'not an official FALCON score' in markdown_path.read_text()
    assert figure_path.read_bytes().startswith(b'\x89PNG')
