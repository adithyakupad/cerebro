"""Recorded coverage and native target semantics for authentic calibration data."""

import json
from pathlib import Path

import numpy as np
import pytest
from pynwb import NWBHDF5IO

from cerebro.falcon import load_falcon


@pytest.mark.parametrize("label,trial_count,sample_count,unordered", [
    ("a", 412, 54633, 33), ("b", 429, 58552, 15),
])
def test_real_calibration_coverage(label, trial_count, sample_count, unordered):
    manifest = json.loads(Path(f"configs/falcon_m1_{label}.json").read_text())
    if not Path(manifest["local_path"]).exists():
        pytest.skip("Pinned calibration recording has not been acquired")
    recording = load_falcon(manifest)
    assert len(recording["trials"]) == trial_count
    assert sum(len(trial["timestamps"]) for trial in recording["trials"]) == sample_count
    assert len(recording["metadata"]["native_unordered_unit_ids"]) == unordered
    assert "quantile" in recording["metadata"]["target_interpretation"]
    assert len(recording["muscle_names"]) == 16
    assert len(set(recording["muscle_names"])) == 16
    for trial in recording["trials"]:
        assert trial["counts"].shape == (len(trial["timestamps"]), 64)
        assert trial["targets"].shape == (len(trial["timestamps"]), 16)
        assert trial["neural_valid"].all()
        assert trial["target_valid"].all()
        assert trial["source_eval_mask"].all()
        np.testing.assert_allclose(trial["bin_right_seconds"] - trial["timestamps"], .02, atol=1e-9)
        assert (trial["counts"] >= 0).all()
        for intervals in recording["observation_intervals"]:
            assert (trial["timestamps"] >= intervals[0, 0]).all()
            assert (trial["bin_right_seconds"] <= intervals[0, 1]).all()
    first_trial = recording["trials"][0]
    with NWBHDF5IO(manifest["local_path"], "r") as io:
        native = io.read()
        source_spikes = np.asarray(native.units["spike_times"][0])
        window_start = first_trial["timestamps"][0]
        window_stop = first_trial["bin_right_seconds"][-1]
        expected_count = ((source_spikes >= window_start) & (source_spikes < window_stop)).sum()
        assert first_trial["counts"][:, 0].sum() == expected_count
        source_numbers = native.trials["number"][:]
        assert [trial["source_trial_number"] for trial in recording["trials"]] == source_numbers.tolist()


def test_non_native_bin_width_fails_before_reading():
    with pytest.raises(ValueError, match="native 20 ms"):
        load_falcon({}, bin_width=.01)


def test_challenge_split_not_supported(tmp_path):
    from hashlib import sha256
    path = tmp_path / "source.nwb"
    path.write_bytes(b"fixture")
    manifest = {"local_path": str(path), "size_bytes": 7,
                "sha256": sha256(b"fixture").hexdigest(), "source_split": "held-out-calib"}
    with pytest.raises(ValueError, match="calibration"):
        load_falcon(manifest)
