"""Check native trial parsing and sampled-block coverage decisions."""

from tools.audit_brochier import covered, read_sorting_counts, read_trials


def test_trial_metadata_preserves_ids_codes_and_native_ticks(tmp_path):
    xml = """<odML><section><name>Trial_001</name>
    <property><value>1</value><name>TrialID</name></property>
    <property><value>255</value><name>PerformanceCode</name></property>
    <property><value>SGLF</value><name>TrialType</name></property>
    <section><name>DigitalEvents</name>
    <property><value>30000</value><name>GO-ON</name></property>
    <property><value>-1</value><name>STOP</name></property>
    </section></section></odML>"""
    path = tmp_path / "trial.odml"
    path.write_text(xml)
    assert read_trials(path) == [{
        "id": 1, "performance_code": 255, "condition": "SGLF",
        "events_ticks": {"GO-ON": 30000, "STOP": -1},
    }]


def test_coverage_rejects_windows_crossing_recording_gaps():
    intervals = [
        {"start_seconds": 0.0, "stop_seconds": 1.0},
        {"start_seconds": 1.2, "stop_seconds": 2.0},
    ]
    assert covered(intervals, 0.5, 1.0)
    assert not covered(intervals, 0.9, 1.3)
    assert covered(intervals, 1.2, 1.5)


def test_sorting_counts_are_version_specific(tmp_path):
    xml = """<odML><section><name>Sorting-02</name>
    <property><value>93</value><name>TotalNum_SUAs</name></property>
    <property><value>49</value><name>TotalNum_MUAs</name></property>
    </section></odML>"""
    path = tmp_path / "sorting.odml"
    path.write_text(xml)
    assert read_sorting_counts(path, "-02") == {"single_units": 93, "multi_units": 49}
