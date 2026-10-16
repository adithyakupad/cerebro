"""Run the prospectively frozen Brochier four-condition transfer case study."""

from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
from neo.rawio import BlackrockRawIO
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cerebro.cross_subject import anonymous_features
from cerebro.dataset import verify_asset
from tools.audit_brochier import RAW_DIR, covered, read_trials, sampled_intervals


MANIFEST = Path("docs/datasets/mission_019_brochier_assets.json")
OUTPUT = Path("reports/mission_019_brochier_transfer.json")
CLASSES = ("SGLF", "SGHF", "PGLF", "PGHF")
BIN_TICKS = 600
BIN_COUNT = 14
CALIBRATION_PER_CLASS = 5


def single_unit_indices(path, spike_channels):
    """Resolve source-designated SUA IDs to Neo sorted-NEV rows."""
    root = ElementTree.parse(path).getroot()
    source_ids = []
    for electrode in root.iter("section"):
        section_name = electrode.findtext("name") or ""
        if not section_name.startswith("Electrode_"):
            continue
        channel_number = int(section_name.removeprefix("Electrode_"))
        sorting = next(
            (child for child in electrode.findall("section")
             if child.findtext("name") == "OfflineSpikeSorting"),
            None,
        )
        if sorting is None:
            continue
        unit_property = next(
            (prop for prop in sorting.findall("property")
             if prop.findtext("name") == "SUAIDs"),
            None,
        )
        if unit_property is None:
            raise ValueError("Missing source single-unit designation")
        for value in unit_property.findall("value"):
            unit_id = int(value.text)
            if unit_id >= 0:
                source_ids.append(f"ch{channel_number}#{unit_id}")

    channel_names = [str(row["name"]) for row in spike_channels]
    if len(set(channel_names)) != len(channel_names):
        raise ValueError("Native sorted spike-channel names are duplicated")
    missing = set(source_ids) - set(channel_names)
    if missing:
        raise ValueError(f"Source-designated single units missing from NEV: {sorted(missing)}")
    indices = [channel_names.index(source_id) for source_id in source_ids]
    if len(indices) != len(set(indices)):
        raise ValueError("Source single-unit IDs are duplicated")
    return indices


def count_trial_spikes(unit_spikes, go_tick):
    """Return fourteen 20-ms half-open bins by selected source single unit."""
    edges = go_tick + np.arange(BIN_COUNT + 1, dtype=np.int64) * BIN_TICKS
    count_columns = []
    for spike_ticks in unit_spikes:
        spike_ticks = np.asarray(spike_ticks, dtype=np.int64)
        if np.any(np.diff(spike_ticks) < 0):
            raise ValueError("Native spike timestamps are unordered")
        edge_positions = np.searchsorted(spike_ticks, edges, side="left")
        count_columns.append(np.diff(edge_positions))
    counts = np.column_stack(count_columns)
    if counts.shape != (BIN_COUNT, len(unit_spikes)):
        raise ValueError("Trial count matrix dimensions changed")
    return counts


def trial_rows(session, assets):
    prefix = session["id"]
    required_names = (session["sorted_nev"], session["neural_nsx"], f"{prefix}.odml")
    for name in required_names:
        verify_asset(RAW_DIR / name, assets[name])
    sorted_prefix = session["sorted_nev"].removesuffix(".nev")
    reader = BlackrockRawIO(
        filename=str(RAW_DIR / prefix),
        nev_override=str(RAW_DIR / sorted_prefix),
        nsx_to_load=session["neural_stream"],
    )
    reader.parse_header()
    sampling_rate, intervals = sampled_intervals(reader)
    tick_rate = int(reader._nev_basic_header["timestamp_resolution"])
    if sampling_rate != 30000 or tick_rate != 30000:
        raise ValueError("Native neural and event clocks differ from frozen protocol")

    recorded_events = set()
    for segment_index in range(reader.segment_count(0)):
        event_ticks, _, _ = reader.get_event_timestamps(0, segment_index, 0)
        recorded_events.update(int(tick) for tick in event_ticks)

    unit_indices = single_unit_indices(RAW_DIR / f"{prefix}.odml", reader.header["spike_channels"])
    expected_units = {"l101210-001": 93, "i140703-001": 156}
    if len(unit_indices) != expected_units[prefix]:
        raise ValueError("Selected single-unit count differs from source odML summary")
    unit_spikes = [reader.get_spike_timestamps(0, 0, index) for index in unit_indices]
    trials = read_trials(RAW_DIR / f"{prefix}.odml")
    rows = []
    exclusions = Counter()
    for trial in trials:
        if trial["performance_code"] != 255 or trial["condition"] not in CLASSES:
            exclusions["not_correct_four_condition"] += 1
            continue
        go_tick = trial["events_ticks"].get("GO-ON", -1)
        if go_tick < 0 or go_tick not in recorded_events:
            exclusions["missing_native_go_event"] += 1
            continue
        stop_tick = trial["events_ticks"].get("STOP", -1)
        window_stop_tick = go_tick + BIN_COUNT * BIN_TICKS
        if stop_tick < window_stop_tick:
            exclusions["window_crosses_trial_stop"] += 1
            continue
        start_seconds = go_tick / tick_rate
        stop_seconds = window_stop_tick / tick_rate
        if not covered(intervals, start_seconds, stop_seconds):
            exclusions["neural_samples_not_covered"] += 1
            continue
        count_matrix = count_trial_spikes(unit_spikes, go_tick)
        bin_features = anonymous_features(count_matrix)
        trial_features = bin_features.mean(axis=0)
        rows.append({
            "trial_id": trial["id"],
            "go_tick": go_tick,
            "condition": trial["condition"],
            "features": trial_features,
            "spike_count": int(count_matrix.sum()),
        })
    rows.sort(key=lambda row: row["go_tick"])
    trial_ids = [row["trial_id"] for row in rows]
    if len(set(trial_ids)) != len(trial_ids):
        raise ValueError("Eligible native trial identities are duplicated")
    counts = Counter(row["condition"] for row in rows)
    if any(counts[label] < CALIBRATION_PER_CLASS + 1 for label in CLASSES):
        raise ValueError("Native class counts fail the frozen eligibility gate")
    return rows, {"unit_count": len(unit_indices), "class_counts": dict(counts),
                  "exclusions": dict(exclusions), "neural_intervals": intervals}


def split_calibration(rows):
    seen = Counter()
    calibration = []
    evaluation = []
    for row in rows:
        label = row["condition"]
        seen[label] += 1
        destination = calibration if seen[label] <= CALIBRATION_PER_CLASS else evaluation
        destination.append(row)
    return calibration, evaluation


def fit_predict(training, evaluation):
    features = np.stack([row["features"] for row in training])
    labels = np.asarray([row["condition"] for row in training])
    test_features = np.stack([row["features"] for row in evaluation])
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    model.fit(features, labels)
    prediction = model.predict(test_features)
    return prediction


def score(true_labels, prediction):
    return {
        "balanced_accuracy": float(balanced_accuracy_score(true_labels, prediction)),
        "accuracy": float(accuracy_score(true_labels, prediction)),
        "macro_f1": float(f1_score(true_labels, prediction, labels=CLASSES, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(true_labels, prediction, labels=CLASSES).tolist(),
        "per_class_recall": {
            label: float(np.mean(prediction[true_labels == label] == label)) for label in CLASSES
        },
    }


def bootstrap_contrast(true_labels, assisted, target_only, seed=19019, repetitions=1000):
    """Trial-conditional stratified interval; subjects are not resampled."""
    rng = np.random.default_rng(seed)
    class_rows = [np.flatnonzero(true_labels == label) for label in CLASSES]
    if any(len(rows) == 0 for rows in class_rows):
        raise ValueError("Every held-out class needs trials")
    differences = np.empty(repetitions, dtype=float)
    for draw_index in range(repetitions):
        sampled_rows = np.concatenate([
            rng.choice(rows, size=len(rows), replace=True) for rows in class_rows
        ])
        assisted_score = balanced_accuracy_score(true_labels[sampled_rows], assisted[sampled_rows])
        target_score = balanced_accuracy_score(true_labels[sampled_rows], target_only[sampled_rows])
        differences[draw_index] = assisted_score - target_score
    limits = np.quantile(differences, [0.025, 0.975])
    return [float(value) for value in limits]


def evaluate_direction(source_rows, target_rows):
    calibration, evaluation = split_calibration(target_rows)
    labels = np.asarray([row["condition"] for row in evaluation])
    predictions = {
        "source_only": fit_predict(source_rows, evaluation),
        "target_only": fit_predict(calibration, evaluation),
        "source_assisted": fit_predict(source_rows + calibration, evaluation),
    }
    for name, training in (
        ("source_prior", source_rows),
        ("target_prior", calibration),
        ("source_assisted_prior", source_rows + calibration),
    ):
        counts = Counter(row["condition"] for row in training)
        majority_label = max(CLASSES, key=lambda label: (counts[label], -CLASSES.index(label)))
        predictions[name] = np.repeat(majority_label, len(evaluation))
    scores = {name: score(labels, prediction) for name, prediction in predictions.items()}
    primary_difference = (
        scores["source_assisted"]["balanced_accuracy"]
        - scores["target_only"]["balanced_accuracy"]
    )
    interval = bootstrap_contrast(
        labels, predictions["source_assisted"], predictions["target_only"]
    )
    return {
        "source_training_trials": len(source_rows),
        "target_calibration_trials": len(calibration),
        "target_evaluation_trials": len(evaluation),
        "calibration_trial_ids": [row["trial_id"] for row in calibration],
        "evaluation_trial_ids": [row["trial_id"] for row in evaluation],
        "evaluation_class_counts": dict(Counter(labels)),
        "scores": scores,
        "source_assisted_minus_target_only_balanced_accuracy": float(primary_difference),
        "conditional_trial_bootstrap_95_percent": interval,
    }


def main():
    manifest = json.loads(MANIFEST.read_text())
    data = {}
    audits = {}
    for session in manifest["sessions"]:
        rows, audit = trial_rows(session, manifest["assets"])
        data[session["subject"]] = rows
        audits[session["subject"]] = audit
    outcomes = {
        "L_to_N": evaluate_direction(data["L"], data["N"]),
        "N_to_L": evaluate_direction(data["N"], data["L"]),
    }
    protocol_path = Path("docs/research/mission_019_protocol.md")
    protocol_hash = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    report = {
        "dataset_doi": manifest["dataset_doi"],
        "archive_etag": manifest["archive"]["etag"],
        "protocol_sha256": protocol_hash,
        "frozen_protocol_commit": "d5fbe7f7d717d37b762d83a4f512476895adf61b",
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "asset_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "neo_version": importlib.metadata.version("neo"),
        "sklearn_version": importlib.metadata.version("scikit-learn"),
        "class_order": CLASSES,
        "bin_width_ms": 20,
        "bins_per_trial": BIN_COUNT,
        "features_per_trial": 7,
        "animals": audits,
        "directions": outcomes,
        "uncertainty_note": "Trial-conditional bootstrap only; two animals, one session each.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
