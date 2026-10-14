import json

import numpy as np
import pytest
import torch

from cerebro.benchmark import array_digest
from cerebro.representation_benchmark import (
    RepresentationGRU,
    feature_mask,
    nested_budget_ids,
    run,
    self_supervised_loss,
    standardize_counts,
)


def test_masked_loss_ignores_unmasked_entries_and_next_trial_boundaries():
    targets = torch.tensor([[[1.], [2.]], [[100.], [101.]]])
    reconstruction = targets.clone()
    mask = torch.tensor([[[True], [False]], [[False], [False]]])
    reconstruction[~mask] = 10000
    predictions = torch.tensor([[[2.], [-9999.]], [[101.], [-9999.]]])
    total, masked, predictive = self_supervised_loss(reconstruction, predictions, targets, mask)
    assert total == 0
    assert masked == 0
    assert predictive == 0
    reconstruction[mask] += 3
    total, masked, predictive = self_supervised_loss(reconstruction, predictions, targets, mask)
    assert masked == 9
    assert predictive == 0


def test_masks_and_nested_budgets_are_seeded():
    first_generator = torch.Generator().manual_seed(2)
    second_generator = torch.Generator().manual_seed(2)
    first = feature_mask((3, 4, 5), .5, first_generator)
    second = feature_mask((3, 4, 5), .5, second_generator)
    torch.testing.assert_close(first, second)
    assert torch.any(first) and torch.any(~first)
    budgets = nested_budget_ids([10, 20, 30, 40], [1, 2, 4], 7)
    assert budgets[1] == budgets[2][:1]
    assert budgets[2] == budgets[4][:2]
    assert budgets == nested_budget_ids([10, 20, 30, 40], [1, 2, 4], 7)


def test_scaler_uses_only_source_training():
    counts = np.array([[[0, 2], [2, 2]], [[100, 100], [200, 200]]], dtype=float)
    standardized, parameters = standardize_counts(counts, [True, False])
    np.testing.assert_array_equal(parameters['feature_mean'], [1, 2])
    np.testing.assert_array_equal(parameters['feature_scale'], [1, 1])
    changed = counts.copy()
    changed[1] *= 100
    _, changed_parameters = standardize_counts(changed, [True, False])
    for name in parameters:
        np.testing.assert_array_equal(parameters[name], changed_parameters[name])
    np.testing.assert_array_equal(standardized[0, :, 0], [-1, 1])


def test_gru_causal_prefix_and_independent_trials():
    torch.manual_seed(3)
    model = RepresentationGRU(4, hidden=7)
    model.eval()
    features = torch.randn(2, 6, 4)
    with torch.no_grad():
        full = model.encode(features)
        prefix = model.encode(features[:, :3])
        single = model.encode(features[1:2])
    torch.testing.assert_close(full[:, :3], prefix)
    torch.testing.assert_close(full[1:2], single)


def test_invalid_mask_and_training_data():
    values = torch.ones(1, 2, 3)
    with pytest.raises(ValueError):
        self_supervised_loss(values, values, values, torch.zeros_like(values, dtype=torch.bool))
    with pytest.raises(ValueError):
        feature_mask((1, 2, 3), 0, torch.Generator())
    with pytest.raises(ValueError):
        standardize_counts(np.ones((2, 3, 4)), [False, False])
    with pytest.raises(ValueError):
        nested_budget_ids([1, 2], [3], 0)


def write_fixture(tmp_path):
    root = tmp_path / 'classical'
    root.mkdir()
    generator = np.random.default_rng(4)
    arrays = {
        'counts': generator.poisson(1, (5, 4, 3)),
        'velocity_m_s': generator.normal(size=(5, 4, 2)) * .1,
        'trial_ids': np.array([10, 20, 30, 40, 50]),
        'bin_right_seconds': np.arange(5)[:, None] + np.arange(1, 5)[None, :] * .02,
    }
    splits = {'source_training': [10, 20, 30], 'source_validation': [40, 50]}
    classical = {
        'splits': splits, 'config': {'bin_width_seconds': .02},
        'arrays': {name: {'sha256': array_digest(value)} for name, value in arrays.items()},
    }
    np.savez_compressed(root / 'arrays.npz', **arrays)
    (root / 'split_manifest.json').write_text(json.dumps(splits))
    (root / 'results.json').write_text(json.dumps(classical))
    config = {
        'classical_run': str(root), 'epochs': 1, 'hidden': 4, 'learning_rate': .001,
        'mask_probability': .5, 'ridge_alpha': 1., 'gradient_clip': 1.,
        'label_budgets': [1, 3], 'budget_seed': 7, 'seeds': [0], 'bin_width_seconds': .02,
    }
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config))
    return path, arrays, root


def test_run_reproducibility_restore_and_training_provenance(tmp_path):
    path, _, _ = write_fixture(tmp_path)
    first = run(path, tmp_path / 'first')
    second = run(path, tmp_path / 'second')
    assert first == second
    assert len(first['results']) == 8
    assert first['normalization_training_trial_ids'] == [10, 20, 30]
    assert first['pretraining'][0]['training_trial_ids'] == [10, 20, 30]
    for row in first['results']:
        assert len(row['trial_mse_m2_s2']) == 2
        assert row['checkpoint_restored_predictions_identical']
    with np.load(tmp_path / 'first' / 'predictions.npz') as archive:
        np.testing.assert_array_equal(archive['evaluation_trial_ids'], [40, 50])


def test_validation_targets_cannot_change_training(tmp_path):
    path, arrays, root = write_fixture(tmp_path)
    first = run(path, tmp_path / 'first')
    arrays['velocity_m_s'][3:] += 100
    np.savez_compressed(root / 'arrays.npz', **arrays)
    classical = json.loads((root / 'results.json').read_text())
    classical['arrays']['velocity_m_s']['sha256'] = array_digest(arrays['velocity_m_s'])
    (root / 'results.json').write_text(json.dumps(classical))
    second = run(path, tmp_path / 'second')
    for first_row, second_row in zip(first['results'], second['results']):
        assert first_row['history'] == second_row['history']
        assert first_row['checkpoint_sha256'] == second_row['checkpoint_sha256']
    assert first['pretraining'] == second['pretraining']
