import json

import numpy as np
import pytest

from cerebro import cross_subject, subject_identity
from test_cross_subject import recordings_fixture, config_fixture


def setup_diagnostic(monkeypatch, tmp_path):
    recordings = recordings_fixture()
    cross_config = config_fixture(tmp_path)
    monkeypatch.setattr(cross_subject, 'load_falcon', lambda manifest: recordings[manifest['fixture_index']])
    cross_root = tmp_path / 'cross'
    cross_subject.run(cross_config, cross_root)
    config = {'cross_subject_run': str(cross_root),
              'source_manifest': str(tmp_path / 'manifest_0.json'),
              'target_manifest': str(tmp_path / 'manifest_1.json'),
              'C': 1., 'maximum_iterations': 1000, 'seed': 13, 'class_weight': 'balanced'}
    path = tmp_path / 'identity_config.json'
    path.write_text(json.dumps(config))
    monkeypatch.setattr(subject_identity, 'load_falcon', lambda manifest: recordings[manifest['fixture_index']])
    return recordings, path


def test_reproducibility_numeric_restore_and_balanced_counts(monkeypatch, tmp_path):
    _, path = setup_diagnostic(monkeypatch, tmp_path)
    first = subject_identity.run(path, tmp_path / 'first')
    second = subject_identity.run(path, tmp_path / 'second')
    assert first == second
    assert first['training_trial_counts'] == [12, 6]
    assert first['evaluation_trial_counts'] == [8, 12]
    assert first['balanced_chance_accuracy'] == .5
    assert first['balanced_accuracy'] == np.mean(first['per_subject_accuracy'])
    assert first['checkpoint_restored_predictions_identical']
    assert np.asarray(first['confusion_true_rows_predicted_columns']).sum() == 20
    assert first['cross_subject_bound_source_sha256']


def test_evaluation_feature_mutation_cannot_change_fitted_parameters(monkeypatch, tmp_path):
    recordings, path = setup_diagnostic(monkeypatch, tmp_path)
    first = subject_identity.run(path, tmp_path / 'first')
    for recording, boundary in zip(recordings, (12, 6)):
        for trial in recording['trials'][boundary:]:
            trial['counts'] += 100
            trial['targets'] += 100
    changed = subject_identity.run(path, tmp_path / 'changed')
    assert first['parameters_sha256'] == changed['parameters_sha256']
    assert first['normalization'] == changed['normalization']
    assert first['cross_subject_split_sha256'] == changed['cross_subject_split_sha256']


def test_anonymous_unit_permutation_preserves_diagnostic_predictions(monkeypatch, tmp_path):
    recordings, path = setup_diagnostic(monkeypatch, tmp_path)
    first = subject_identity.run(path, tmp_path / 'first')
    for recording in recordings:
        for trial in recording['trials']:
            trial['counts'] = trial['counts'][:, ::-1]
            trial['neural_valid'] = trial['neural_valid'][:, ::-1]
    changed = subject_identity.run(path, tmp_path / 'changed')
    assert first['confusion_true_rows_predicted_columns'] == changed['confusion_true_rows_predicted_columns']
    with np.load(tmp_path / 'first' / 'parameters.npz') as first_archive:
        with np.load(tmp_path / 'changed' / 'parameters.npz') as changed_archive:
            for name in first_archive.files:
                np.testing.assert_allclose(first_archive[name], changed_archive[name], atol=1e-12)


def test_missing_manifest_trial_and_overlap_are_rejected(monkeypatch, tmp_path):
    _, path = setup_diagnostic(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        subject_identity.select_trial_rows([], [100])
    config = json.loads(path.read_text())
    root = tmp_path / 'cross'
    splits = json.loads((root / 'split_manifest.json').read_text())
    splits['target_calibration'].append(splits['target_evaluation'][0])
    report = json.loads((root / 'results.json').read_text())
    report['splits'] = splits
    (root / 'split_manifest.json').write_text(json.dumps(splits))
    (root / 'results.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='overlap'):
        subject_identity.run(path, tmp_path / 'run')
