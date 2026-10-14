"""Synthetic losses validate resampling; they make no neural findings."""

import numpy as np
import pytest

import json

from cerebro.benchmark import array_digest
from cerebro.evaluation import grouped_losses, loss_summary, read_bound_report


def test_constant_trial_summary_and_seed_aggregation():
    summary = loss_summary([[1.] * 10, [3.] * 10], np.arange(10), [3.] * 10)
    assert summary["mean_trial_loss"] == 2
    assert summary["percentile_interval"] == [2, 2]
    assert summary["paired_mean_change"] == -1
    assert summary["paired_percentile_interval"] == [-1, -1]
    assert summary["seed_mean_loss_range"] == [1, 3]
    assert summary["evaluation_trials"] == 10
    assert summary["initialization_repeats"] == 2


@pytest.mark.parametrize("block", [1, 5])
def test_resampling_deterministic_and_paired_negative(block):
    losses = np.arange(20.)
    first = loss_summary(losses, np.arange(20), losses + 2, block_length=block, seed=8)
    assert first == loss_summary(losses, np.arange(20), losses + 2, block_length=block, seed=8)
    assert first["paired_percentile_interval"] == [-2, -2]


@pytest.mark.parametrize("losses,ids,reference", [
    ([1, 2], [0], None), ([1, np.nan], [0, 1], None),
    ([1, 2], [0, 0], None), ([], [], None),
    ([1, 2], [0, 1], [1]), ([1, 2], [0, 1], [1, np.nan]),
])
def test_invalid_trial_inputs(losses, ids, reference):
    with pytest.raises(ValueError):
        loss_summary(losses, ids, reference)


def test_duplicate_seed_rejected():
    rows = [{"model": "fixture", "seed": 0, "loss": [1, 2]}] * 2
    with pytest.raises(ValueError, match="Duplicate"):
        grouped_losses(rows, ("model",), "loss")


def test_report_array_binding_rejects_tampering(tmp_path):
    losses = np.array([1., 2.])
    report = {"arrays": {"losses": {"sha256": array_digest(losses)}}}
    (tmp_path / "results.json").write_text(json.dumps(report))
    np.savez(tmp_path / "arrays.npz", losses=losses)
    read_bound_report(tmp_path, "arrays.npz")
    np.savez(tmp_path / "arrays.npz", losses=losses + 1)
    with pytest.raises(ValueError, match="provenance"):
        read_bound_report(tmp_path, "arrays.npz")


@pytest.mark.parametrize("block,draws", [(0, 1000), (21, 1000), (5, 1)])
def test_invalid_resampling_settings(block, draws):
    with pytest.raises(ValueError):
        loss_summary(np.ones(20), np.arange(20), block_length=block, draws=draws)
