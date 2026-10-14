"""Synthetic observations validate software, not neuroscience claims."""

from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from pynwb import NWBFile, NWBHDF5IO, TimeSeries
import pytest

from cerebro.dataset import download_asset, verify_asset
from cerebro.sense import (
    Behavior, align_behavior, bin_spikes, load_recording,
    validate_intervals, validate_timestamps,
)


def make_counts(spikes=None, intervals=None, observations=None, width=0.02):
    spikes = [np.array([0, 0.019, 0.02, 0.04, 0.059, 0.06])] if spikes is None else spikes
    intervals = np.array([[0, 0.06]]) if intervals is None else intervals
    observations = [intervals] * len(spikes) if observations is None else observations
    return bin_spikes(spikes, intervals, range(len(spikes)), range(len(intervals)), observations, width)


@pytest.mark.parametrize("times", [[1, 0], [0, 0], [np.nan], [[0, 1]], [np.inf]])
def test_invalid_timestamps(times):
    with pytest.raises(ValueError):
        validate_timestamps(times)


def test_timestamp_units_and_spike_duplicates():
    with pytest.raises(ValueError, match="seconds"):
        validate_timestamps([0, 1], unit="milliseconds")
    np.testing.assert_equal(validate_timestamps([0, 0], strict=False), [0, 0])
    assert validate_timestamps([]).size == 0


@pytest.mark.parametrize("intervals", [[[0, 0]], [[1, 0]], [[0, 2], [1, 3]], [[np.nan, 2]]])
def test_invalid_trials(intervals):
    with pytest.raises(ValueError):
        validate_intervals(intervals)


def test_half_open_binning_and_dimensions():
    counts = make_counts()
    np.testing.assert_equal(counts.values[:, 0], [2, 1, 2])
    assert counts.values.shape == (3, 1)
    assert counts.values.sum() == 5  # spike at final stop excluded
    assert counts.values.dtype.kind == "i"
    assert counts.valid.all()


def test_trial_boundaries_gaps_and_short_trial():
    trials = np.array([[0, 0.045], [0.1, 0.14], [0.2, 0.21]])
    counts = make_counts([np.array([0.01, 0.04, 0.06, 0.1, 0.12, 0.14, 0.205])], trials)
    np.testing.assert_allclose(counts.left, [0, 0.02, 0.1, 0.12])
    np.testing.assert_equal(counts.trial_ids, [0, 0, 1, 1])
    np.testing.assert_equal(counts.values[:, 0], [1, 0, 1, 1])
    np.testing.assert_allclose(counts.dropped_tail_seconds, [0.005, 0, 0.01], atol=1e-12)


def test_empty_units_and_missing_observation_are_distinct():
    counts = make_counts([np.array([]), np.array([0.01])],
                         observations=[np.array([[0, 0.06]]), np.empty((0, 2))])
    np.testing.assert_equal(counts.values[:, 0], [0, 0, 0])
    np.testing.assert_equal(counts.values[:, 1], [-1, -1, -1])
    assert not counts.valid[:, 1].any()
    empty = make_counts([], observations=[])
    assert empty.values.shape == (3, 0)


@pytest.mark.parametrize("width", [0, -1, np.nan, np.inf])
def test_invalid_bin_width(width):
    with pytest.raises(ValueError):
        make_counts(width=width)


def test_invalid_feature_dimensions():
    with pytest.raises(ValueError, match="dimensions"):
        bin_spikes([[]], [[0, 1]], [1, 2], [0], [[[0, 1]]])


def behavior(times, data):
    return Behavior(np.asarray(times), np.asarray(data).reshape(-1, 1), "meters", 0.001, 0.1, "synthetic", "x")


def test_alignment_physical_units_and_no_extrapolation():
    counts = make_counts(width=0.02)
    times = np.arange(0.001, 0.04, 0.001)
    series = behavior(times, np.full(len(times), 10))
    aligned, valid = align_behavior(series, counts)
    np.testing.assert_equal(valid, [True, True, False])
    np.testing.assert_allclose(aligned[:2], 0.11)
    assert np.isnan(aligned[2]).all()
    np.testing.assert_equal(series.raw_data, 10)


def test_alignment_internal_gap_nan_and_trial_isolation():
    counts = make_counts(intervals=np.array([[0, 0.02], [0.1, 0.12]]))
    times = np.r_[np.arange(0, 0.006, 0.001), np.arange(0.014, 0.02, 0.001), np.arange(0.1, 0.12, 0.001)]
    data = np.r_[np.zeros(12), np.full(len(times) - 12, 100)]
    aligned, valid = align_behavior(behavior(times, data), counts)
    assert not valid[0] and valid[1]
    np.testing.assert_allclose(aligned[1], 0.2)
    data[-1] = np.nan
    _, valid = align_behavior(behavior(times, data), counts)
    assert not valid.any()


def test_empty_behavior():
    aligned, valid = align_behavior(behavior([], []), make_counts())
    assert not valid.any() and np.isnan(aligned).all()


def test_provenance_rejects_corruption(tmp_path):
    path = tmp_path / "recording.nwb"
    path.write_bytes(b"synthetic file for hashing")
    manifest = {"size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    assert verify_asset(path, manifest) == manifest["sha256"]
    path.write_bytes(b"X" * manifest["size_bytes"])
    with pytest.raises(ValueError, match="checksum"):
        verify_asset(path, manifest)
    path.write_bytes(b"")
    with pytest.raises(ValueError, match="size"):
        verify_asset(path, manifest)


def test_download_checks_pinned_identity_and_preserves_existing(tmp_path, monkeypatch):
    payload = b"synthetic download, not neural data"
    path = tmp_path / "recording.nwb"
    manifest = {"size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                "asset_id": "synthetic", "asset_path": "recording.nwb",
                "local_path": str(path), "metadata_url": "metadata", "download_url": "download"}
    metadata = {"identifier": "synthetic", "path": "recording.nwb", "contentSize": len(payload),
                "digest": {"dandi:sha2-256": manifest["sha256"]}}
    def response(url, timeout):
        return io.BytesIO(json.dumps(metadata).encode() if url == "metadata" else payload)
    monkeypatch.setattr("cerebro.dataset.urllib.request.urlopen", response)
    assert download_asset(manifest) == path
    assert path.read_bytes() == payload
    assert not path.with_suffix(".part").exists()
    assert download_asset(manifest) == path
    path.write_bytes(b"X" * len(payload))
    with pytest.raises(ValueError, match="checksum"):
        download_asset(manifest)
    assert path.read_bytes() == b"X" * len(payload)
    metadata["identifier"] = "different-asset"
    with pytest.raises(ValueError, match="pinned manifest"):
        download_asset(manifest)


def test_decimal_grid_at_nonzero_trial_start():
    counts = make_counts([np.array([1.00, 1.02, 1.04, 1.06])],
                         np.array([[1.00, 1.06]]))
    np.testing.assert_equal(counts.values[:, 0], [1, 1, 1])
    np.testing.assert_equal(counts.left, [1.00, 1.02, 1.04])


def write_fixture(path, *, units=True, observation_intervals=True, trials=True):
    nwb = NWBFile("synthetic software test", "synthetic", datetime(2020, 1, 1, tzinfo=timezone.utc))
    if units:
        kwargs = {"obs_intervals": [[0.0, 0.04]]} if observation_intervals else {}
        nwb.add_unit(id=1, spike_times=[0.01, 0.03], **kwargs)
    if trials:
        nwb.add_trial(start_time=0.0, stop_time=0.04)
    module = nwb.create_processing_module("behavior", "synthetic")
    module.add(TimeSeries(name="position", data=np.arange(40)[:, None], unit="meters",
                          conversion=0.001, starting_time=0.0, rate=1000.0))
    with NWBHDF5IO(path, "w") as io:
        io.write(nwb)


def test_nwb_reader_preserves_data_and_metadata(tmp_path):
    path = tmp_path / "fixture.nwb"
    write_fixture(path)
    recording = load_recording(path)
    assert recording.metadata["identifier"] == "synthetic"
    series = recording.behavior["position"]
    np.testing.assert_allclose(series.timestamps, np.arange(40) / 1000)
    np.testing.assert_equal(series.raw_data[:, 0], np.arange(40))
    assert series.conversion == 0.001 and series.unit == "meters"
    np.testing.assert_equal(recording.units.spike_times.iloc[0], [0.01, 0.03])


@pytest.mark.parametrize("kwargs, message", [({"units": False}, "no neural units"),
    ({"trials": False}, "no trials"), ({"observation_intervals": False}, "Observation intervals")])
def test_reader_rejects_missing_data(tmp_path, kwargs, message):
    path = tmp_path / "missing.nwb"
    write_fixture(path, **kwargs)
    with pytest.raises(ValueError, match=message):
        load_recording(path)


@pytest.mark.skipif(not Path("data/raw/mc_maze_small/sub-Jenkins_ses-small_desc-train_behavior+ecephys.nwb").exists(),
                    reason="Pinned real recording not downloaded; unit tests remain offline")
def test_local_real_recording():
    manifest = json.loads(Path("configs/mc_maze_small.json").read_text())
    verify_asset(manifest["local_path"], manifest)
    recording = load_recording(manifest["local_path"])
    assert len(recording.units) == 142 and len(recording.trials) == 100
    assert set(recording.behavior) == {"hand_pos", "hand_vel", "cursor_pos", "eye_pos"}
    counts = bin_spikes(recording.units.spike_times,
                        recording.trials[["start_time", "stop_time"]].to_numpy(),
                        recording.units.index, recording.trials.index,
                        recording.units.obs_intervals)
    assert counts.valid.all() and counts.values.shape[1] == 142
    for series in recording.behavior.values():
        _, valid = align_behavior(series, counts)
        assert valid.all()
