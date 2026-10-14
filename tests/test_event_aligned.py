"""Synthetic timing fixtures test software; real recordings support findings."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cerebro.event_audit import condition_keys, window_reason
from cerebro.event_aligned import (
    align_training, condition_residuals, covariance_correlation,
    relative_grid, trial_bootstrap, write_experiment,
    validate_publication_protocol,
)
from cerebro.event_figures import matched_event_latencies
from cerebro.sense import Behavior


def fixture_recording():
    trials = pd.DataFrame({
        "start_time": [0., 2., 4., 6.], "stop_time": [1., 3., 5., 7.],
        "go_cue_time": [.4, 2.4, 4.4, 6.4], "move_onset_time": [.5, 2.5, 4.5, 6.5],
        "split": ["train", "train", "train", "val"],
        "maze_id": [1] * 4, "trial_type": [1] * 4,
        "trial_version": [0] * 4, "active_target": [0] * 4,
        "target_pos": [np.array([[1, 2]])] * 4,
        "barrier_pos": [np.empty((0, 4))] * 4,
        "num_targets": [1] * 4, "num_barriers": [0] * 4,
    }, index=[10, 30, 50, 90])
    intervals = trials[["start_time", "stop_time"]].to_numpy()
    units = pd.DataFrame({
        "spike_times": [np.array([.2, .399999, .4, .42, .44, .6, 2.4, 4.4, 6.4]), np.array([])],
        "obs_intervals": [intervals.copy(), intervals.copy()],
    }, index=[1011, 2011])
    times = np.concatenate([np.arange(start, stop, .001) for start, stop in intervals])
    behavior = {"hand_vel": Behavior(times, np.ones((len(times), 2)), "m/s", .001, 0., "synthetic", "x,y")}
    return SimpleNamespace(trials=trials, units=units, behavior=behavior)


def protocol():
    return {"pre_seconds": -.2, "post_seconds": .2, "bin_width_seconds": .02,
            "behavior_max_gap_seconds": .002}


@pytest.mark.parametrize("parameter,value", [
    ("primary_event", "move_onset_time"), ("bin_width_seconds", .05),
    ("pre_seconds", -.2), ("baseline_seconds", [-.2, 0.]),
    ("bootstrap_draws", 100), ("bootstrap_seed", 5),
])
def test_publication_protocol_rejects_mislabeled_parameters(parameter, value):
    settings = json.loads(Path("configs/event_04.json").read_text())
    validate_publication_protocol(settings)
    settings[parameter] = value
    with pytest.raises(ValueError, match=parameter):
        validate_publication_protocol(settings)


def test_event_latency_join_preserves_trial_identity():
    arrays = {
        "trial_ids": np.array([10, 30, 50]),
        "secondary_trial_ids": np.array([50, 10, 90]),
        "source_go_cue_seconds": np.array([.4, 2.4, 4.4]),
        "source_movement_onset_seconds": np.array([4.7, .5, 6.5]),
    }
    np.testing.assert_allclose(matched_event_latencies(arrays), [.1, .3])
    arrays["secondary_trial_ids"] = np.array([70, 80, 90])
    assert matched_event_latencies(arrays).size == 0
    arrays["secondary_trial_ids"] = np.array([50, 50, 90])
    with pytest.raises(ValueError, match="unique"):
        matched_event_latencies(arrays)


def test_event_alignment_identity_half_open_bins_and_rates():
    aligned = align_training(fixture_recording(), "go_cue_time", protocol())
    assert aligned["counts"].shape == (3, 20, 2)
    np.testing.assert_equal(aligned["trial_ids"], [10, 30, 50])
    np.testing.assert_equal(aligned["source_event_seconds"], [.4, 2.4, 4.4])
    np.testing.assert_equal(aligned["counts"][0, 10:13, 0], [1, 1, 1])
    assert aligned["counts"][0, :, 0].sum() == 5  # .6 final edge excluded
    assert aligned["counts"][0, 10, 0] / .02 == 50
    assert aligned["counts"][:, :, 1].sum() == 0
    assert not aligned["exclusions"]
    np.testing.assert_allclose(aligned["absolute_left_seconds"][0, 10], .4)
    np.testing.assert_allclose(aligned["hand_velocity"], .001)


@pytest.mark.parametrize("pre,post,width", [(0, 0, .02), (-.2, .21, .02), (-.2, .2, 0), (np.nan, 1, .02)])
def test_bad_grid(pre, post, width):
    with pytest.raises(ValueError):
        relative_grid(pre, post, width)


def test_missing_event_and_trial_boundary_exclusions():
    recording = fixture_recording()
    recording.trials.loc[10, "go_cue_time"] = np.nan
    recording.trials.loc[30, "go_cue_time"] = 2.95
    aligned = align_training(recording, "go_cue_time", protocol())
    np.testing.assert_equal(aligned["trial_ids"], [50])
    assert [e["reason"] for e in aligned["exclusions"]] == ["missing_event", "trial_boundary"]
    recording.trials.loc[50, "go_cue_time"] = 5.0
    with pytest.raises(ValueError, match="No training trials"):
        align_training(recording, "go_cue_time", protocol())


def test_neural_coverage_and_behavior_gaps():
    recording = fixture_recording()
    row = recording.trials.loc[10]
    recording.units.obs_intervals.iloc[0][0, 1] = .3
    assert window_reason(recording, row, .4, -.2, .2) == "neural_coverage"
    recording = fixture_recording()
    series = recording.behavior["hand_vel"]
    keep = ~((series.timestamps >= .39) & (series.timestamps <= .41))
    series.timestamps, series.raw_data = series.timestamps[keep], series.raw_data[keep]
    aligned = align_training(recording, "go_cue_time", protocol())
    assert aligned["exclusions"][0]["reason"] == "behavior_coverage"
    assert 10 not in aligned["trial_ids"]


def test_condition_grouping_rejects_mixed_variants_and_geometry():
    recording = fixture_recording()
    train = recording.trials.query("split == 'train'").copy()
    train.loc[30, "trial_version"] = 1
    keys = condition_keys(train)
    assert keys[0] != keys[1] and keys[0] == keys[2]
    train.loc[30, "trial_version"] = 0
    train.at[30, "target_pos"] = np.array([[99, 2]])
    with pytest.raises(ValueError, match="incompatible"):
        condition_keys(train)
    with pytest.raises(ValueError, match="missing"):
        condition_keys(train.drop(columns="active_target"))
    with pytest.raises(ValueError, match="geometry"):
        condition_keys(train.drop(columns="barrier_pos"))


def test_validation_trials_cannot_affect_aligned_summary():
    recording = fixture_recording()
    before = align_training(recording, "go_cue_time", protocol())
    recording.trials.loc[90, "go_cue_time"] = np.nan
    recording.trials.loc[90, "trial_version"] = 99
    after = align_training(recording, "go_cue_time", protocol())
    np.testing.assert_equal(before["counts"], after["counts"])
    np.testing.assert_equal(before["condition_keys"], after["condition_keys"])
    assert 90 not in after["trial_ids"]


def test_condition_time_residuals_and_low_repetition_exclusion():
    counts = np.array([[[0, 2], [1, 0]], [[3, 2], [1, 3]], [[6, 5], [4, 3]], [[99, 99], [99, 99]]])
    means, keys, indices, residuals = condition_residuals(counts, ["a", "a", "a", "b"])
    assert means.shape == (1, 2, 2)
    np.testing.assert_equal(indices, [0, 1, 2]); np.testing.assert_equal(keys, ["a"])
    np.testing.assert_allclose(means[0], [[3, 3], [2, 2]])
    np.testing.assert_allclose(residuals.sum(axis=0), 0)
    np.testing.assert_allclose(residuals + means[0], counts[:3])
    empty, _, indices, residuals = condition_residuals(counts[:2], ["a", "a"])
    assert empty.shape == (0, 2, 2) and len(indices) == 0 and residuals.shape == (0, 2, 2)


def test_correlations_constant_missing_and_one_observation():
    covariance, correlation = covariance_correlation([[1, 2, 0], [2, 4, 0], [3, 6, 0]])
    assert covariance[0, 0] == 1 and covariance[0, 1] == 2
    np.testing.assert_allclose(correlation[:2, :2], 1)
    assert np.isnan(correlation[2]).all() and np.isnan(correlation[:, 2]).all()
    assert np.isnan(covariance_correlation([[1, 2]])[0]).all()
    with pytest.raises(ValueError, match="Finite"):
        covariance_correlation([[1, np.nan], [2, 3]])
    np.testing.assert_allclose(covariance_correlation([[1, 3], [2, 2], [3, 1]])[1][0, 1], -1)


def test_whole_trial_stratified_bootstrap_reproducible():
    # Constant rows within each condition fix the pooled value under resampling.
    values = np.array([[1, 2], [1, 2], [9, 10], [9, 10]])
    bands = trial_bootstrap(values, ["a", "a", "b", "b"], draws=100, seed=4)
    np.testing.assert_allclose(bands, [[5, 6], [5, 6]])
    varied = np.arange(12).reshape(4, 3)
    np.testing.assert_equal(trial_bootstrap(varied, ["a"] * 4, 100, 4), trial_bootstrap(varied, ["a"] * 4, 100, 4))


@pytest.mark.skipif(not Path("data/raw/mc_maze_small/sub-Jenkins_ses-small_desc-train_behavior+ecephys.nwb").exists(),
                    reason="Real recording is not local; no implicit network download")
def test_real_event_report_and_tensor_reproducibility(tmp_path):
    output = tmp_path / "events.json"
    tensors = tmp_path / "events.npz"
    result = write_experiment("configs/mc_maze_small.json", output=output, tensor_path=tensors)
    first = output.read_bytes()
    with np.load(tensors, allow_pickle=False) as arrays:
        counts = arrays["counts"].copy()
        assert counts.shape == (75, 70, 142)
        assert arrays["residual_counts"].shape == (63, 70, 142)
        np.testing.assert_allclose(arrays["rates_hz"], counts / .02)
        assert len(set(arrays["trial_ids"])) == 75
    write_experiment("configs/mc_maze_small.json", output=output, tensor_path=tensors)
    assert output.read_bytes() == first
    with np.load(tensors, allow_pickle=False) as arrays:
        np.testing.assert_equal(counts, arrays["counts"])
    assert result["validation_trials_used"] == 0 and result["residual_correlations"]["qualifying_conditions"] == 0
    assert result["checks"]["condition_residual_zero_sum_max_absolute"] < 1e-12
