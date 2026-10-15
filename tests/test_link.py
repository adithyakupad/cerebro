"""Validate native LINK sample references and explicit contact correspondence."""

import json
from pathlib import Path

import numpy as np
import pytest

from cerebro.link import align_channel_keys, load_link, validate_crossing_counts


def test_channel_mapping_uses_keys():
    first = [("A", 1), ("B", 2)]
    second = [("B", 2), ("A", 1)]
    np.testing.assert_array_equal(align_channel_keys(first, second), [1, 0])
    with pytest.raises(ValueError, match="unique"):
        align_channel_keys(first, [first[0], first[0]])
    with pytest.raises(ValueError, match="differ"):
        align_channel_keys(first, [("A", 1), ("B", 3)])


@pytest.mark.parametrize("invalid", [np.nan, -1, 0.5, np.inf])
def test_crossings_reject_invalid_values(invalid):
    with pytest.raises(ValueError, match="nonnegative integers"):
        validate_crossing_counts([[invalid]])


@pytest.mark.parametrize('values', [
    np.array([[2**63]], dtype=np.uint64),
    np.array([[2**64 - 1]], dtype=np.uint64),
    np.array([[float(2**63)]]),
    np.array([[1e20]]),
])
def test_crossings_reject_int64_overflow(values):
    with pytest.raises(ValueError, match='representable as int64'):
        validate_crossing_counts(values)


def test_crossings_preserve_exact_int64_boundary_and_native_counts():
    values = np.array([[0, 8, 2**63 - 1]], dtype=np.int64)
    np.testing.assert_array_equal(validate_crossing_counts(values), values)
    np.testing.assert_array_equal(validate_crossing_counts(values.astype(np.uint64)), values)


@pytest.mark.data
def test_native_real_link_pair():
    recordings = []
    for date, samples in [("20200127", 27274), ("20200130", 26569)]:
        manifest = json.loads(Path(f"configs/link_{date}.json").read_text())
        if not Path(manifest["local_path"]).exists():
            pytest.skip("Pinned LINK recording has not been downloaded")
        recording = load_link(manifest)
        assert recording["verified_sha256"] == manifest["sha256"]
        assert len(recording["trials"]) == 375
        assert sum(trial["sample_count"] for trial in recording["trials"]) == samples
        assert len(recording["channel_keys"]) == 96
        assert recording["native_metadata"]["count_source_unit"] == "volts"
        assert recording["source_session_id"] is None
        for trial in recording["trials"]:
            assert trial["counts"].shape == (trial["sample_count"], 96)
            assert trial["velocity"].shape == (trial["sample_count"], 2)
            assert trial["position"].shape == (trial["sample_count"], 2)
            assert trial["position_units"] == ["flexion units"] * 2
            assert trial["position_valid"].all()
            assert trial["velocity_valid"].all()
            assert trial["velocity_units"] == ["flexion units per time bin"] * 2
            assert (np.diff(trial["timestamps"]) > 0).all()
            assert trial["counts"].dtype == np.int64
            assert trial["target_style"] == "CO"
        recordings.append(recording)
    mapping = align_channel_keys(recordings[0]["channel_keys"], recordings[1]["channel_keys"])
    np.testing.assert_array_equal(mapping, np.arange(96))
    first_trial = recordings[0]["trials"][0]
    assert first_trial["sample_start"] == 0
    assert first_trial["sample_count"] == 63
    assert first_trial["timestamps"][-1] == pytest.approx(9.65)
