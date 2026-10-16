"""Local real-data regression, skipped when publisher assets are not present."""

import json
from pathlib import Path

import pytest

from tools.audit_brochier import audit_session
from tools.run_brochier_transfer import trial_rows


MANIFEST = Path("docs/datasets/mission_019_brochier_assets.json")
RAW_DIR = Path("data/raw/brochier")
REPORT = Path("reports/mission_019_brochier_transfer.json")


@pytest.mark.data
@pytest.mark.skipif(
    not all((RAW_DIR / name).exists() for name in (
        "l101210-001.odml", "l101210-001.ns2", "l101210-001.ns5", "l101210-001-02.nev",
        "i140703-001.odml", "i140703-001.ns2", "i140703-001.ns6", "i140703-001-03.nev",
    )),
    reason="Brochier native assets absent",
)
def test_brochier_source_counts_clocks_and_report_reproduce():
    manifest = json.loads(MANIFEST.read_text())
    report = json.loads(REPORT.read_text())
    expected_units = {"L": 93, "N": 156}
    expected_trials = {"L": 135, "N": 142}
    for session in manifest["sessions"]:
        subject = session["subject"]
        native = audit_session(session, manifest["assets"])
        rows, audit = trial_rows(session, manifest["assets"])
        assert native["correct_go_windows_neural_covered_280ms"] == expected_trials[subject]
        assert audit["unit_count"] == expected_units[subject]
        assert len(rows) == expected_trials[subject]
        assert report["animals"][subject]["class_counts"] == audit["class_counts"]
        assert all(item["matched_sorted_nev"] == item["odml_count"]
                   for item in native["source_event_matches"].values())
