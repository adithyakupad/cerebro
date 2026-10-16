"""Known synthetic counts test arithmetic; genuine data tests reproducibility."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cerebro.characterize import (
    analyze, count_statistics, matched_intervals, metadata_audit, write_report,
)
from cerebro.sense import bin_spikes


def test_known_sparse_statistics_and_rates():
    result = count_statistics([0, 0, 1, 3], np.full(4, 0.02))
    assert result["zero_fraction"] == 0.5
    assert result["mean_count"] == 1
    assert result["count_variance"] == 2
    assert result["fano_across_time"] == 2
    assert result["mean_rate_hz"] == 50
    assert result["count_histogram"] == [[0, 2], [1, 1], [3, 1]]


def test_fano_zero_mean_single_bin_and_missing():
    result = count_statistics([0, 0], [0.02, 0.02])
    assert result["fano_across_time"] is None
    assert result["count_variance"] == 0 and result["mean_rate_hz"] == 0
    result = count_statistics([2], [0.02])
    assert result["fano_across_time"] is None and result["count_variance"] is None
    result = count_statistics([-1, 0, 1], [0.02] * 3)
    assert result["observed_bins"] == 2 and result["mean_rate_hz"] == 25
    assert result["zero_fraction"] == 0.5
    result = count_statistics([], [])
    assert result["mean_rate_hz"] is None and result["zero_fraction"] is None
    assert count_statistics([-1], [0.02])["fano_across_time"] is None
    assert count_statistics([2, 2], [0.02, 0.02])["fano_across_time"] == 0


@pytest.mark.parametrize("counts,durations", [([1.5], [.02]), ([-2], [.02]),
    ([np.nan], [.02]), ([1], [0]), ([1], []), ([[1]], [.02]), ([1, 2], [.01, .02])])
def test_invalid_statistical_inputs(counts, durations):
    with pytest.raises(ValueError):
        count_statistics(counts, durations)


def synthetic_recording():
    intervals = np.array([[0, .121], [.2, .371]])
    spikes = np.array([0, .004999, .005, .019999, .02, .049999, .05,
                       .099999, .1, .12, .121, .2, .205, .249999, .299999, .3, .35, .371])
    electrodes = pd.DataFrame({"location": ["PMd", "M1"]}, index=[0, 96])
    units = pd.DataFrame({"spike_times": [spikes, np.array([])],
                          "obs_intervals": [intervals, intervals],
                          "heldout": [False, True],
                          "electrodes": [electrodes.loc[[0]], electrodes.loc[[0]]]}, index=[1011, 2011])
    trials = pd.DataFrame({"start_time": intervals[:, 0], "stop_time": intervals[:, 1],
                           "split": ["train", "val"]}, index=[7, 9])
    return SimpleNamespace(units=units, trials=trials, electrodes=electrodes)


def test_matched_grid_and_short_trial_policy():
    intervals, quantum = matched_intervals([[0, .121], [.2, .371]])
    assert quantum == .1
    np.testing.assert_allclose(intervals, [[0, .1], [.2, .3]])
    with pytest.raises(ValueError, match="shorter"):
        matched_intervals([[0, .05]])
    with pytest.raises(ValueError, match="microseconds"):
        matched_intervals([[0, 1]], widths=[0.0000001])


def test_conservation_boundaries_trial_sensitivity_and_silent_unit():
    recording = synthetic_recording()
    result = analyze(recording)
    assert result["trial_ids"] == [7, 9] and result["matched_source_spikes_identical"]
    totals = [entry["matched"]["per_unit"][0]["spikes"] for entry in result["widths"].values()]
    assert totals == [12, 12, 12]
    for entry in result["widths"].values():
        matched = entry["matched"]
        assert matched["per_unit"][0]["mean_rate_hz"] == pytest.approx(60)
        assert matched["per_unit"][1]["spikes"] == 0
        assert matched["per_unit"][1]["fano_across_time"] is None
        assert matched["excluded_spikes"] == result["raw_spikes_in_trials"] - 12
        assert [t["trial_id"] for t in matched["trials"]] == [7, 9]
        assert [t["split"] for t in matched["trials"]] == ["train", "val"]
        assert entry["native"]["conservation_passed"]
    assert result["widths"]["5ms"]["native"]["shape"] == [58, 2]
    # Spike at each bin stop goes into the next bin, and final trial stops are excluded.
    source = recording.trials[["start_time", "stop_time"]].to_numpy()
    counts = bin_spikes(recording.units.spike_times, source, recording.units.index,
                        recording.trials.index, recording.units.obs_intervals, .02)
    assert np.all(counts.right[counts.trial_ids == 7] <= .121)
    assert np.all(counts.left[counts.trial_ids == 9] >= .2)


def test_metadata_candidates_do_not_modify_raw_links():
    recording = synthetic_recording()
    before = recording.units.electrodes.iloc[1].copy(deep=True)
    audit = metadata_audit(recording)
    assert audit["conflicting_units"] == 1 and audit["m1_candidates_all_link_to_m1"]
    assert audit["units"][1]["publisher_plus96_candidate_ids"] == [96]
    assert not audit["raw_metadata_modified"]
    pd.testing.assert_frame_equal(before, recording.units.electrodes.iloc[1])


@pytest.mark.skipif(not Path("data/raw/mc_maze_small/sub-Jenkins_ses-small_desc-train_behavior+ecephys.nwb").exists(),
                    reason="Local real recording absent; no automatic dataset download")
@pytest.mark.data
def test_real_report_is_reproducible_and_matched_rates_equal(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    result = write_report("configs/mc_maze_small.json", first)
    write_report("configs/mc_maze_small.json", second)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text())["provenance"]["sha256"] == "dcaf3a524e2b2f65f163ee3b07789b8474bdfc6ca66098bc542ab93dff489884"
    rates = [[u["mean_rate_hz"] for u in entry["matched"]["per_unit"]]
             for entry in result["widths"].values()]
    np.testing.assert_allclose(rates[0], rates[1], rtol=0, atol=1e-12)
    np.testing.assert_allclose(rates[0], rates[2], rtol=0, atol=1e-12)
    assert result["metadata_audit"]["conflicting_units"] == 70
