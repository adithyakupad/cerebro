"""Bounded synthetic runner checks and explicit authentic-cache integration."""

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from cerebro.benchmark import array_digest
from cerebro.neural_information import checked_inputs, control_counts, fit_seed, summarize
from cerebro.optimization_study import digest, restore_cnn


def synthetic_arrays():
    generator = np.random.default_rng(26)
    counts = generator.poisson(2., (6, 7, 3)).astype(float)
    velocity = generator.normal(0., .2, (6, 7, 2))
    keys = np.array(['a'] * 6)
    groups = {
        'inner_training': np.array([0, 1]),
        'inner_validation': np.array([2, 3]),
        'source_training': np.arange(4),
        'source_validation': np.array([4, 5]),
    }
    return counts, velocity, keys, groups


def fit_config():
    return {'donor_seed': 25, 'hidden': 3, 'learning_rate': .001,
            'gradient_clip': 1., 'maximum_epochs': 2}


@pytest.fixture
def cache(tmp_path):
    counts, velocity, keys, groups = synthetic_arrays()
    protocol = tmp_path / 'protocol.md'
    protocol.write_text('Synthetic protocol, not neuroscience evidence.\n')
    preprocessing = tmp_path / 'preprocessing.json'
    preprocessing.write_text('{}\n')
    original_path = tmp_path / 'original.json'
    original = {'splits': {key: (indices + 10).tolist() for key, indices in groups.items()}}
    original_path.write_text(json.dumps(original))
    config = {'output': str(tmp_path), 'protocol': str(protocol),
              'm025_report': str(original_path), 'preprocessing': str(preprocessing)}
    arrays = {'counts': counts, 'velocity': velocity, 'conditions': keys,
              'trial_ids': np.arange(10, 16), 'unit_ids': np.arange(3),
              'right_seconds': np.tile(np.arange(7) * .02, (6, 1))}
    np.savez_compressed(tmp_path / 'inputs.npz', **arrays)
    lineage = {'cache_sha256': digest(tmp_path / 'inputs.npz'),
               'protocol_sha256': digest(protocol), 'm025_report_sha256': digest(original_path),
               'preprocessing_sha256': digest(preprocessing),
               'arrays': {key: {'sha256': array_digest(value)} for key, value in arrays.items()}}
    (tmp_path / 'inputs.json').write_text(json.dumps(lineage))
    return config, arrays, original, lineage


def save_lineage(config, lineage):
    path = Path(config['output']) / 'inputs.json'
    path.write_text(json.dumps(lineage))


def test_checked_inputs_exact_cache_and_original_split(cache):
    config, expected, original, lineage = cache
    arrays, groups, actual_original, actual_lineage = checked_inputs(config)
    for name, values in expected.items():
        np.testing.assert_array_equal(arrays[name], values)
    assert actual_original == original
    assert actual_lineage == lineage
    assert groups['source_training'].tolist() == [0, 1, 2, 3]
    assert groups['source_validation'].tolist() == [4, 5]


@pytest.mark.parametrize('field', ['protocol', 'm025_report', 'preprocessing'])
def test_checked_inputs_rejects_source_lineage_change(cache, field):
    config, _, _, _ = cache
    path = Path(config[field])
    path.write_text(path.read_text() + '\n')
    with pytest.raises(ValueError, match='Input lineage differs'):
        checked_inputs(config)


def test_checked_inputs_rejects_file_and_array_hash_changes(cache):
    config, arrays, _, lineage = cache
    arrays['counts'][0, 0, 0] += 1
    path = Path(config['output']) / 'inputs.npz'
    np.savez_compressed(path, **arrays)
    with pytest.raises(ValueError, match='Input cache checksum differs'):
        checked_inputs(config)
    lineage['cache_sha256'] = digest(path)
    save_lineage(config, lineage)
    with pytest.raises(ValueError, match='Input array differs: counts'):
        checked_inputs(config)


@pytest.mark.parametrize('failure', ['source_overlap', 'inner_overlap', 'inner_union', 'missing_id'])
def test_checked_inputs_rejects_split_corruption(cache, failure):
    config, _, original, lineage = cache
    if failure == 'source_overlap':
        original['splits']['source_validation'] = [13, 14, 15]
    elif failure == 'inner_overlap':
        original['splits']['inner_validation'] = [11, 12, 13]
    elif failure == 'inner_union':
        original['splits']['inner_validation'] = [2 + 10]
    else:
        original['splits']['source_validation'] = [14, 99]
    path = Path(config['m025_report'])
    path.write_text(json.dumps(original))
    lineage['m025_report_sha256'] = digest(path)
    save_lineage(config, lineage)
    with pytest.raises((ValueError, AssertionError)):
        checked_inputs(config)


def test_control_counts_partition_local_mappings_and_no_input_mutation():
    counts, _, keys, groups = synthetic_arrays()
    original = counts.copy()
    inner, full, mappings = control_counts(counts, keys, groups, 'permuted', 25)
    for role, mapping in mappings.items():
        recipients = np.array(mapping['recipients'])
        donors = np.array(mapping['donors'])
        assert set(donors) == set(groups[role])
        assert np.all(recipients != donors)
        destination = inner if role.startswith('inner_') else full
        np.testing.assert_array_equal(destination[recipients], counts[donors])
    np.testing.assert_array_equal(counts, original)
    changed = counts.copy()
    changed[groups['source_validation']] += 1000
    changed_inner, changed_full, _ = control_counts(changed, keys, groups, 'permuted', 25)
    np.testing.assert_array_equal(inner[groups['source_training']], changed_inner[groups['source_training']])
    np.testing.assert_array_equal(full[groups['source_training']], changed_full[groups['source_training']])
    for mode in ('zero', 'clock'):
        inner, full, mappings = control_counts(counts, keys, groups, mode, 25)
        np.testing.assert_array_equal(inner, full)
        assert mappings == {}


@pytest.mark.parametrize('mode', ['zero', 'clock', 'permuted'])
def test_synthetic_fit_restoration_determinism_and_rng(tmp_path, mode):
    counts, velocity, keys, groups = synthetic_arrays()
    rng_before = torch.get_rng_state()
    threads_before = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        first = tmp_path / 'first'
        second = tmp_path / 'second'
        first.mkdir()
        second.mkdir()
        row, predictions = fit_seed(counts, velocity, keys, groups, mode, 0, fit_config(), first)
        first_rng = torch.get_rng_state().clone()
        repeated, repeated_predictions = fit_seed(counts, velocity, keys, groups, mode, 0, fit_config(), second)
        np.testing.assert_array_equal(torch.get_rng_state().numpy(), first_rng.numpy())
        assert row['selected_epoch'] in (1, 2)
        assert row['selected_epoch'] == min(row['history'], key=lambda entry: entry['inner_physical_mse'])['epoch']
        assert row['selected_epoch'] == repeated['selected_epoch']
        for entry, other in zip(row['history'], repeated['history']):
            assert entry['inner_physical_mse'] == other['inner_physical_mse']
            assert entry['training_standardized_mse'] == other['training_standardized_mse']
        for name, prediction in predictions.items():
            np.testing.assert_array_equal(prediction, repeated_predictions[name])
        assert row['checkpoint_sha256'] == repeated['checkpoint_sha256']
        checkpoint = first / (row['name'] + '.pt')
        _, full, _ = control_counts(counts, keys, groups, mode, 25)
        restored = restore_cnn(checkpoint, full[groups['source_validation']])
        np.testing.assert_array_equal(restored, predictions[row['name']])
        assert row['restoration_exact']
        if mode == 'permuted':
            restored_real = restore_cnn(checkpoint, counts[groups['source_validation']])
            np.testing.assert_array_equal(restored_real, predictions['permuted_real_seed_0'])
    finally:
        torch.set_rng_state(rng_before)
        torch.set_num_threads(threads_before)


def test_final_target_values_do_not_change_fitting_or_epoch_selection(tmp_path):
    counts, velocity, keys, groups = synthetic_arrays()
    altered = velocity.copy()
    altered[groups['source_validation']] += 1000
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    rng_before = torch.get_rng_state()
    threads_before = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        row, prediction = fit_seed(counts, velocity, keys, groups, 'clock', 0, fit_config(), first)
        changed, changed_prediction = fit_seed(counts, altered, keys, groups, 'clock', 0, fit_config(), second)
        assert row['selected_epoch'] == changed['selected_epoch']
        assert row['checkpoint_sha256'] == changed['checkpoint_sha256']
        np.testing.assert_array_equal(prediction['clock_seed_0'], changed_prediction['clock_seed_0'])
    finally:
        torch.set_rng_state(rng_before)
        torch.set_num_threads(threads_before)


def summary_config():
    return {'score_start_bin': 4, 'bootstrap_draws': 20, 'bootstrap_seed': 26,
            'descriptive_reduction': .05}


def test_summary_averages_seed_losses_not_ensemble_predictions():
    target = np.zeros((3, 7, 2))
    predictions = {}
    for family, magnitude in [('neural_200', 1.), ('clock', 2.), ('permuted', 3.)]:
        predictions[family + '_seed_0'] = target + magnitude
        predictions[family + '_seed_1'] = target - magnitude
    summary = summarize(target, predictions, ['a', 'b', 'a'], summary_config())
    assert summary['metrics']['neural_200']['mse_m2_s2'] == 1.
    assert summary['metrics']['clock']['mse_m2_s2'] == 4.
    assert summary['metrics']['permuted']['mse_m2_s2'] == 9.
    assert summary['stratification']['neural_200']['conditions']['a']['equal_trial_mse'] == 1.
    assert summary['contrasts']['clock']['difference_m2_s2'] == -3.
    assert summary['primary_descriptive_support']
    assert summary == summarize(target, predictions, ['a', 'b', 'a'], summary_config())


def test_perfect_control_does_not_support_relative_improvement():
    target = np.zeros((2, 7, 2))
    predictions = {'neural_200_seed_0': target + 1., 'clock_seed_0': target.copy(),
                   'permuted_seed_0': target + 2.}
    summary = summarize(target, predictions, ['a', 'a'], summary_config())
    assert summary['contrasts']['clock']['relative_reduction'] is None
    assert not summary['primary_descriptive_support']


@pytest.mark.data
def test_authentic_m026_cache_identity_and_groups_without_acquisition():
    config_path = Path('configs/m026_neural_information.json')
    config = json.loads(config_path.read_text())
    output = Path(config['output'])
    if not (output / 'inputs.npz').is_file() or not (output / 'inputs.json').is_file():
        pytest.skip('M026 authentic cache must be explicitly prepared locally; no acquisition in tests')
    arrays, groups, original, lineage = checked_inputs(config)
    assert arrays['counts'].shape == (2295, 70, 137)
    assert arrays['velocity'].shape == (2295, 70, 2)
    assert len(groups['source_training']) == 1721
    assert len(groups['source_validation']) == 574
    assert len(groups['inner_training']) == 1377
    assert len(groups['inner_validation']) == 344
    assert set(groups['source_training']).isdisjoint(groups['source_validation'])
    assert set(groups['inner_training']).isdisjoint(groups['inner_validation'])
    assert lineage['m025_evaluation_arrays_exact']
    assert lineage['asset'] == original['asset']
