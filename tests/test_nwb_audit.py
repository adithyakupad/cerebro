"""Real-asset audits validate provenance without manufacturing coverage."""

import json
from pathlib import Path

import pytest

from cerebro.nwb_audit import audit_recording


@pytest.mark.parametrize("date,units,spikes,trials", [
    ("20160406", 18, 152389, 296),
    ("20160407", 19, 130191, 331),
])
@pytest.mark.data
def test_pinned_real_recording_audit(date, units, spikes, trials):
    manifest_path = Path("configs") / f"perich_j_{date}.json"
    manifest = json.loads(manifest_path.read_text())
    if not Path(manifest["local_path"]).exists():
        pytest.skip("Pinned public recording has not been downloaded")
    result = audit_recording(manifest)
    assert result["verified_sha256"] == manifest["sha256"]
    assert result["unit_count"] == units
    assert result["total_spikes"] == spikes
    assert result["trials"]["count"] == trials
    assert result["spike_times_finite_and_ordered"]
    assert not result["observation_intervals_present"]
    assert result["neural_coverage_status"] == "unknown"
    assert len({tuple(key) for key in result["unit_keys"]}) == units
    assert all(key[0] == result["session_id"] for key in result["unit_keys"])
    assert result["neuron_correspondence"] == "not established across sessions"
    series_names = {series["name"] for series in result["behavioral_series"]}
    assert series_names == {"cursor_pos", "cursor_vel", "cursor_acc"}
    for series in result["behavioral_series"]:
        assert series["timestamps"]["finite_and_strictly_ordered"]
        assert series["timestamps"]["median_interval_seconds"] == pytest.approx(0.01)
    repeated_result = audit_recording(manifest)
    assert result == repeated_result


def test_audit_rejects_unverified_asset(tmp_path):
    recording_path = tmp_path / "unverified.nwb"
    recording_path.write_bytes(b"not an NWB recording")
    manifest = {"local_path": str(recording_path), "size_bytes": 1, "sha256": "0" * 64}
    with pytest.raises(ValueError, match="Asset size"):
        audit_recording(manifest)
