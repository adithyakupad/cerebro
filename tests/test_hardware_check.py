import json

from cerebro import hardware_check


def test_cpu_roundtrips_and_failure_report_survives(monkeypatch, tmp_path):
    monkeypatch.setattr(hardware_check, "backend_availability", lambda: {"cpu": True, "mps": False, "cuda": False})
    output = tmp_path / "hardware.json"
    report = hardware_check.run(output)
    assert report["status"] == "PASS"
    assert len(report["backends"]["cpu"]["models"]) == 6
    assert all(row["weights_only_restore_checked"] for row in report["backends"]["cpu"]["models"].values())
    assert report["backends"]["mps"]["status"] == "NOT_TESTED"
    assert report["backends"]["cuda"]["status"] == "NOT_TESTED"

    def failed_model(kind, backend, path):
        raise RuntimeError("Deliberate test failure")

    monkeypatch.setattr(hardware_check, "check_model", failed_model)
    assert hardware_check.main(["--output", str(output)]) == 1
    stored = json.loads(output.read_text())
    assert stored["status"] == "FAIL"
    assert all(row["error"] == "Deliberate test failure" for row in stored["backends"]["cpu"]["models"].values())
