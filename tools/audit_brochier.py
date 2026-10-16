"""Audit native Brochier clocks, sampled coverage and trial events without fitting."""

import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
from xml.etree import ElementTree

from neo.rawio import BlackrockRawIO

from cerebro.dataset import verify_asset


MANIFEST = Path("docs/datasets/mission_019_brochier_assets.json")
RAW_DIR = Path("data/raw/brochier")


def read_trials(path):
    """Read source odML labels/events; values remain in native 30-kHz ticks."""
    root = ElementTree.parse(path).getroot()
    trials = []
    for section in root.iter("section"):
        section_name = section.findtext("name") or ""
        if not section_name.startswith("Trial_"):
            continue
        properties = {}
        for prop in section.findall("property"):
            properties[prop.findtext("name")] = prop.findtext("value")
        event_section = next(
            child for child in section.findall("section")
            if child.findtext("name") == "DigitalEvents"
        )
        events = {}
        for prop in event_section.findall("property"):
            events[prop.findtext("name")] = int(prop.findtext("value"))
        trials.append({
            "id": int(properties["TrialID"]),
            "performance_code": int(properties["PerformanceCode"]),
            "condition": properties["TrialType"],
            "events_ticks": events,
        })
    trial_ids = [trial["id"] for trial in trials]
    if len(set(trial_ids)) != len(trial_ids):
        raise ValueError("Source odML trial IDs are not unique")
    return trials


def read_sorting_counts(path, version):
    root = ElementTree.parse(path).getroot()
    sorting_name = f"Sorting{version}"
    section = next(
        section for section in root.iter("section")
        if section.findtext("name") == sorting_name
    )
    properties = {}
    for prop in section.findall("property"):
        properties[prop.findtext("name")] = prop.findtext("value")
    return {
        "single_units": int(properties["TotalNum_SUAs"]),
        "multi_units": int(properties["TotalNum_MUAs"]),
    }


def sampled_intervals(reader):
    """Return every recorded NSx block as half-open seconds and sample count."""
    if len(reader.header["signal_streams"]) != 1:
        raise ValueError("Exactly one selected native NSx stream is required")
    sampling_rate = reader.get_signal_sampling_rate(0)
    intervals = []
    for segment_index in range(reader.segment_count(0)):
        start = reader.get_signal_t_start(0, segment_index, 0)
        sample_count = reader.get_signal_size(0, segment_index, 0)
        stop = start + sample_count / sampling_rate
        intervals.append({
            "start_seconds": float(start),
            "stop_seconds": float(stop),
            "sample_count": int(sample_count),
        })
    if any(left["stop_seconds"] > right["start_seconds"]
           for left, right in zip(intervals, intervals[1:])):
        raise ValueError("Native NSx segments overlap or are out of order")
    return float(sampling_rate), intervals


def covered(intervals, start_seconds, stop_seconds):
    return any(
        interval["start_seconds"] <= start_seconds
        and stop_seconds <= interval["stop_seconds"]
        for interval in intervals
    )


def audit_session(session, assets):
    prefix = session["id"]
    sorted_prefix = session["sorted_nev"].removesuffix(".nev")
    required_names = [
        f"{prefix}.odml", f"{prefix}.ns2", session["neural_nsx"],
        session["sorted_nev"],
    ]
    checksums = {}
    for name in required_names:
        checksums[name] = verify_asset(RAW_DIR / name, assets[name])

    neural = BlackrockRawIO(
        filename=str(RAW_DIR / prefix),
        nev_override=str(RAW_DIR / sorted_prefix),
        nsx_to_load=session["neural_stream"],
    )
    neural.parse_header()
    neural_rate, neural_intervals = sampled_intervals(neural)
    analog = BlackrockRawIO(
        filename=str(RAW_DIR / prefix),
        nev_override=str(RAW_DIR / sorted_prefix),
        nsx_to_load=2,
    )
    analog.parse_header()
    analog_rate, analog_intervals = sampled_intervals(analog)
    recorded_event_ticks = set()
    for segment_index in range(neural.segment_count(0)):
        event_ticks, _, _ = neural.get_event_timestamps(0, segment_index, 0)
        recorded_event_ticks.update(map(int, event_ticks))
    tick_rate = int(neural._nev_basic_header["timestamp_resolution"])
    if tick_rate != 30000 or neural_rate != 30000 or analog_rate != 1000:
        raise ValueError("Native Brochier clocks differ from declared rates")

    trials = read_trials(RAW_DIR / f"{prefix}.odml")
    sorting_version = sorted_prefix.removeprefix(prefix)
    sorting_counts = read_sorting_counts(RAW_DIR / f"{prefix}.odml", sorting_version)
    matched_events = {}
    for event_name in ("TS-ON", "CUE-ON", "GO-ON", "SR", "STOP"):
        present = [
            trial["events_ticks"][event_name]
            for trial in trials
            if trial["events_ticks"].get(event_name, -1) >= 0
        ]
        matched_events[event_name] = {
            "odml_count": len(present),
            "matched_sorted_nev": sum(tick in recorded_event_ticks for tick in present),
        }

    correct = [trial for trial in trials if trial["performance_code"] == 255]
    eligible = []
    for trial in correct:
        go_ticks = trial["events_ticks"].get("GO-ON", -1)
        stop_ticks = trial["events_ticks"].get("STOP", -1)
        if go_ticks < 0 or stop_ticks < 0:
            continue
        go_seconds = go_ticks / tick_rate
        window_stop = go_seconds + 0.28
        within_trial = stop_ticks >= go_ticks + 8400
        if within_trial and go_ticks in recorded_event_ticks and covered(neural_intervals, go_seconds, window_stop):
            eligible.append(trial)

    return {
        "session": prefix,
        "verified_sha256": checksums,
        "sorted_nev": session["sorted_nev"],
        "neural_sampling_hz": neural_rate,
        "neural_recorded_intervals": neural_intervals,
        "analog_sampling_hz": analog_rate,
        "analog_recorded_intervals": analog_intervals,
        "nev_timestamp_ticks_per_second": tick_rate,
        "spike_channel_rows_including_noise": len(neural.header["spike_channels"]),
        "source_odml_sorted_unit_counts": sorting_counts,
        "analog_channel_rows": len(analog.header["signal_channels"]),
        "trial_count": len(trials),
        "performance_codes": dict(sorted(Counter(t["performance_code"] for t in trials).items())),
        "correct_condition_counts": dict(sorted(Counter(t["condition"] for t in correct).items())),
        "source_event_matches": matched_events,
        "correct_go_windows_neural_covered_280ms": len(eligible),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/mission_019_brochier_native.json"))
    arguments = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    results = [audit_session(session, manifest["assets"]) for session in manifest["sessions"]]
    report = {
        "dataset_doi": manifest["dataset_doi"],
        "archive_etag": manifest["archive"]["etag"],
        "neo_version": importlib.metadata.version("neo"),
        "sessions": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(arguments.output)


if __name__ == "__main__":
    main()
