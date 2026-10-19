"""Synthetic M025 checks do not consume prospective neural outcomes."""

import hashlib
import json

import numpy as np
import pytest
import torch

from cerebro import optimization_study as study


def test_paired_summary_uses_trial_pairs_and_seeded_block_resampling():
    reference = np.asarray([2., 4., 6., 8., 10., 12., 14.])
    candidate = reference + np.asarray([-1., 2., -3., 4., -5., 6., -7.])
    result = study.paired_summary(candidate, reference, draws=100, seed=7, block=3)
    differences = candidate - reference
    blocks = [differences[:3], differences[3:6], differences[6:]]
    generator = np.random.default_rng(7)
    means = []
    for _ in range(100):
        selected = generator.integers(3, size=3)
        sampled = np.concatenate([blocks[index] for index in selected])
        means.append(sampled.mean())
    expected_interval = np.quantile(means, [.025, .975])
    np.testing.assert_array_equal(result['paired_interval_95'], expected_interval)
    assert result['difference_m2_s2'] == differences.mean()
    assert result['relative_reduction'] == 1 - candidate.mean() / reference.mean()
    assert result['trial_wins'] == 4
    assert result == study.paired_summary(candidate, reference, draws=100, seed=7, block=3)


@pytest.mark.parametrize('candidate,reference', [([], []), ([1], [1, 2]), ([[1]], [[1]]), ([np.nan], [1])])
def test_paired_summary_rejects_incompatible_or_nonfinite_losses(candidate, reference):
    with pytest.raises(ValueError):
        study.paired_summary(candidate, reference, draws=10)


def test_zero_reference_has_no_defined_relative_reduction():
    result = study.paired_summary(np.zeros(3), np.zeros(3), draws=10)
    assert result['relative_reduction'] is None
    assert result['paired_interval_95'] == [0., 0.]


def test_protocol_guard_checks_both_committed_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = 'config.json'
    protocol_path = 'protocol.md'
    config = {'protocol': protocol_path}
    (tmp_path / config_path).write_text(json.dumps(config))
    (tmp_path / protocol_path).write_text('Frozen protocol\n')
    committed = {}
    for name in (config_path, protocol_path):
        committed['HEAD:' + name] = (tmp_path / name).read_bytes()
    monkeypatch.setattr(study.subprocess, 'check_output', lambda command: committed[command[-1]])
    study.check_committed_protocol(config_path, config)
    for name in (config_path, protocol_path):
        original = (tmp_path / name).read_bytes()
        (tmp_path / name).write_bytes(original + b'changed')
        with pytest.raises(ValueError, match='committed'):
            study.check_committed_protocol(config_path, config)
        (tmp_path / name).write_bytes(original)


def final_fixture(monkeypatch):
    content = b'committed bytes'
    expected = hashlib.sha256(content).hexdigest()
    config = {'protocol': 'protocol.md', 'promotion_reduction': .05, 'final_manifest': 'asset.json'}
    development = {'config': dict(config), 'protocol_sha256': expected,
                   'source_sha256': {'optimization_study.py': expected},
                   'inner_loss_by_cap': {'20': 1., '200': .9}, 'development_gate_passed': True}
    eligibility = {'eligible_for_prospective_recipe_replication': True, 'asset': {'sha256': 'native'}}
    monkeypatch.setattr(study, 'digest', lambda path: expected)
    monkeypatch.setattr(study.subprocess, 'check_output', lambda command: content)

    def read_json(path):
        if str(path) == 'asset.json':
            return eligibility['asset']
        if str(path) == 'reports/m025_development.json':
            return development
        raise AssertionError('Unexpected evidence read: ' + str(path))

    monkeypatch.setattr(study, 'read_json', read_json)
    return config, development, eligibility


@pytest.mark.parametrize('development_passed,eligibility_passed', [(False, True), (True, False), (False, False)])
def test_final_access_requires_both_gates(tmp_path, monkeypatch, development_passed, eligibility_passed):
    config, development, eligibility = final_fixture(monkeypatch)
    development['development_gate_passed'] = development_passed
    eligibility['eligible_for_prospective_recipe_replication'] = eligibility_passed
    original_read = study.read_json

    def read_json(path):
        if str(path).endswith('results.json'):
            return development
        if str(path).endswith('eligibility.json'):
            return eligibility
        return original_read(path)

    monkeypatch.setattr(study, 'read_json', read_json)
    monkeypatch.setattr(study, 'verify_asset', lambda *args: pytest.fail('Final data accessed'))
    with pytest.raises(ValueError, match='gate|eligibility'):
        study.load_stage('final', config, tmp_path)
    assert not (tmp_path / 'final_started.json').exists()


def test_authorization_checks_frozen_config_protocol_source_and_committed_evidence(monkeypatch):
    config, development, eligibility = final_fixture(monkeypatch)
    study.authorize_final(development, eligibility, config)
    development['config'] = dict(config, promotion_reduction=.01)
    with pytest.raises(ValueError, match='protocol/config'):
        study.authorize_final(development, eligibility, config)
    development['config'] = config
    development['protocol_sha256'] = 'changed'
    with pytest.raises(ValueError, match='protocol/config'):
        study.authorize_final(development, eligibility, config)
    development['protocol_sha256'] = study.digest('protocol.md')
    development['source_sha256']['optimization_study.py'] = 'changed'
    with pytest.raises(ValueError, match='Implementation changed'):
        study.authorize_final(development, eligibility, config)
    development['source_sha256']['optimization_study.py'] = study.digest('source.py')
    monkeypatch.setattr(study.subprocess, 'check_output', lambda command: b'other revision')
    with pytest.raises(ValueError, match='committed'):
        study.authorize_final(development, eligibility, config)


def test_authorization_recomputes_reduction_instead_of_trusting_boolean(monkeypatch):
    config, development, eligibility = final_fixture(monkeypatch)
    development['inner_loss_by_cap']['200'] = .99
    with pytest.raises(ValueError, match='gate'):
        study.authorize_final(development, eligibility, config)


@pytest.mark.parametrize('short_loss,long_loss', [(0., 0.), (np.nan, .1), (1., np.nan), (1., -.1), (np.inf, .1)])
def test_authorization_rejects_invalid_gate_losses(monkeypatch, short_loss, long_loss):
    config, development, eligibility = final_fixture(monkeypatch)
    development['inner_loss_by_cap'] = {'20': short_loss, '200': long_loss}
    with pytest.raises(ValueError, match='losses'):
        study.authorize_final(development, eligibility, config)


def test_authorization_rejects_stale_ignored_development_cache(monkeypatch):
    config, development, eligibility = final_fixture(monkeypatch)
    original_read = study.read_json

    def read_json(path):
        if str(path) == 'reports/m025_development.json':
            return dict(development, development_gate_passed=False)
        return original_read(path)

    monkeypatch.setattr(study, 'read_json', read_json)
    with pytest.raises(ValueError, match='Cached development'):
        study.authorize_final(development, eligibility, config)


def test_shared_inner_trajectory_preserves_short_cap_predictions(tmp_path):
    torch.set_num_threads(1)
    generator = np.random.default_rng(25)
    counts = generator.poisson(2, size=(5, 8, 2)).astype(float)
    velocity = generator.normal(size=(5, 8, 2))
    fitting = np.asarray([True, True, False, False, False])
    selecting = np.asarray([False, False, True, False, False])
    training = fitting | selecting
    evaluating = ~training
    config = {'score_start_bin': 4, 'seeds': [2], 'hidden': 3,
              'learning_rate': .001, 'gradient_clip': 1., 'epoch_caps': [2],
              'maximum_stage_seconds': 100}
    short_path = tmp_path / 'short'
    shared_path = tmp_path / 'shared'
    short_path.mkdir()
    shared_path.mkdir()
    short_rows, short_predictions = study.cnn_experiment(
        counts, velocity, fitting, selecting, training, evaluating, config, short_path)
    config['epoch_caps'] = [2, 4]
    shared_rows, shared_predictions = study.cnn_experiment(
        counts, velocity, fitting, selecting, training, evaluating, config, shared_path)
    name = 'cnn_2_seed_2'
    np.testing.assert_array_equal(short_predictions[name], shared_predictions[name])
    assert short_rows[0]['selected_epoch'] == shared_rows[0]['selected_epoch']
    for short_epoch, shared_epoch in zip(short_rows[0]['history'], shared_rows[0]['history']):
        assert short_epoch['training_standardized_mse'] == shared_epoch['training_standardized_mse']
        assert short_epoch['inner_physical_mse'] == shared_epoch['inner_physical_mse']
    restored = study.restore_cnn(shared_path / (name + '.pt'), counts[evaluating])
    np.testing.assert_array_equal(restored, shared_predictions[name])
