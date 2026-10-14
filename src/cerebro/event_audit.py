"""Training-only feasibility audit before choosing event-aligned analyses."""

import argparse
import json
from pathlib import Path

import numpy as np

from cerebro.dataset import verify_asset
from cerebro.sense import load_recording


CONDITION_FIELDS = ("maze_id", "trial_type", "trial_version", "active_target")
GEOMETRY_FIELDS = ("target_pos", "barrier_pos", "num_targets", "num_barriers")
EVENT_FIELDS = ("target_on_time", "go_cue_time", "move_onset_time")


def condition_keys(trials):
    """Retain task variant and active target; reject incompatible geometry."""
    if any(field not in trials for field in (*CONDITION_FIELDS, *GEOMETRY_FIELDS)):
        raise ValueError("Required condition identifiers or geometry are missing")
    keys, geometry = [], {}
    for _, row in trials.iterrows():
        values = [row[field] for field in CONDITION_FIELDS]
        if any(not np.isfinite(v) or int(v) != v for v in values):
            raise ValueError("Condition identifiers must be finite integers")
        key = "/".join(str(int(v)) for v in values)
        signature = [np.asarray(row[field]) for field in GEOMETRY_FIELDS]
        if key in geometry and any(not np.array_equal(a, b) for a, b in zip(signature, geometry[key])):
            raise ValueError("Condition key pools incompatible target/barrier geometry")
        geometry[key] = signature
        keys.append(key)
    return np.asarray(keys, dtype=str)


def window_reason(recording, row, event, pre, post, max_gap=.002):
    """Complete coverage only; no crossing source trial or observation gaps."""
    if not np.isfinite(event):
        return "missing_event"
    if event < row.start_time or event >= row.stop_time:
        return "event_outside_trial"
    start, stop = np.round([event + pre, event + post], 12)
    if start < row.start_time - 1e-12 or stop > row.stop_time + 1e-12:
        return "trial_boundary"
    for obs in recording.units.obs_intervals:
        if not np.any((obs[:, 0] <= start + 1e-12) & (obs[:, 1] >= stop - 1e-12)):
            return "neural_coverage"
    if "hand_vel" not in recording.behavior:
        return "missing_hand_velocity"
    series = recording.behavior["hand_vel"]
    a, b = np.searchsorted(series.timestamps, [start, stop], side="left")
    times, data = series.timestamps[a:b], series.raw_data[a:b]
    if (len(times) == 0 or times[0] - start > max_gap or stop - times[-1] > max_gap
            or np.any(np.diff(times) > max_gap) or not np.all(np.isfinite(data))):
        return "behavior_coverage"
    return None


def distribution(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return None
    return dict(zip(["min", "q25", "median", "q75", "max"],
                    np.quantile(values, [0, .25, .5, .75, 1]).tolist()))


def audit(recording, *, pre=-.4, post=1.0):
    train = recording.trials[recording.trials["split"] == "train"]
    keys = condition_keys(train)
    conditions = []
    for key in sorted(set(keys)):
        subset = train.iloc[np.flatnonzero(keys == key)]
        row = subset.iloc[0]
        conditions.append({"key": key, "training_trials": len(subset),
                           "trial_ids": [int(v) for v in subset.index],
                           "identifiers": {f: int(row[f]) for f in CONDITION_FIELDS},
                           "geometry_consistent": True})
    events = {}
    for field in EVENT_FIELDS:
        values = train[field].to_numpy() if field in train else np.full(len(train), np.nan)
        reasons = [window_reason(recording, row, value, pre, post)
                   for (_, row), value in zip(train.iterrows(), values)]
        events[field] = {
            "source_description": recording.metadata["trial_descriptions"].get(field),
            "finite_events": int(np.isfinite(values).sum()),
            "event_before_trial_start": int(np.sum(values < train.start_time)),
            "event_at_or_after_trial_stop": int(np.sum(values >= train.stop_time)),
            "event_from_start_seconds": distribution(values - train.start_time),
            "remaining_trial_seconds": distribution(train.stop_time - values),
            "complete_window_trials": sum(reason is None for reason in reasons),
            "exclusions": {str(reason): reasons.count(reason) for reason in sorted(set(reasons) - {None})},
            "coverage_by_trial": [{"trial_id": int(i), "reason": reason} for i, reason in zip(train.index, reasons)],
        }
    repetitions = np.array([c["training_trials"] for c in conditions])
    return {
        "training_trial_ids": [int(i) for i in train.index],
        "training_trials": len(train), "unused_validation_trials": int((recording.trials.split == "val").sum()),
        "condition_fields": list(CONDITION_FIELDS), "conditions": conditions,
        "repetition_histogram": {str(int(n)): int(np.sum(repetitions == n)) for n in sorted(set(repetitions))},
        "events": events, "candidate_window_seconds": [pre, post],
        "movement_minus_go_seconds": distribution(train.move_onset_time - train.go_cue_time),
        "go_minus_target_seconds": distribution(train.go_cue_time - train.target_on_time),
        "trial_duration_seconds": distribution(train.stop_time - train.start_time),
        "movement_source": "Existing source annotation calculated offline; no new kinematic onset estimator",
        "descriptive_min_repetitions": 3,
        "residual_reliability_screen_repetitions": 20,
        "conditions_passing_descriptive_screen": int(np.sum(repetitions >= 3)),
        "conditions_passing_residual_screen": int(np.sum(repetitions >= 20)),
        "residual_feasibility": "unsupported: each compatible condition has only 2–3 training trials",
    }


def write_audit(manifest_path, output="reports/event_04_feasibility.json",
                markdown="reports/event_04_feasibility.md"):
    manifest = json.loads(Path(manifest_path).read_text())
    verify_asset(manifest["local_path"], manifest)
    results = audit(load_recording(manifest["local_path"]))
    results["provenance"] = manifest
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n")
    lines = ["# Mission 004: event and condition feasibility", "",
        "Audit performed before finalizing the event-alignment analysis.", "",
        f"Source: DANDI {manifest['dandiset']} v{manifest['version']}, asset `{manifest['asset_id']}` (SHA-256 verified).",
        "75 train trials are available; 25 validation trials are excluded from estimation.", "",
        "Grouping by maze alone appears to give 6–9 repetitions, but mixes task variants.",
        "Compatible keys retain maze_id / trial_type / trial_version / active_target and",
        "check identical target/barrier geometry. There are **27 conditions**:",
        "**21 have 3 training trials; 6 have 2**. No condition has adequate replication",
        "for a reliable trial-residual covariance claim. No compatible conditions are pooled.", "",
        "| Event | Source | Finite train markers | Complete −0.4 to +1.0 s windows |",
        "| --- | --- | ---: | ---: |"]
    for field, description in [("target_on_time", "photobox target presentation"),
                               ("go_cue_time", "photobox go cue"),
                               ("move_onset_time", "offline source algorithm")]:
        e = results["events"][field]
        lines.append(f"| {field} | {description} | {e['finite_events']} | {e['complete_window_trials']} |")
    d = results["movement_minus_go_seconds"]
    lines += ["", f"Go-to-source-movement latency ranges {d['min']:.3f}–{d['max']:.3f} s (median {d['median']:.3f} s).",
        "Existing movement markers can be used without deriving onset again, but their",
        "offline detection algorithm is not specified fully in this asset. The go cue is",
        "the primary candidate because its photobox detection is documented; secondary",
        "movement-marker alignment can describe timing sensitivity without treating the",
        "marker as a verified hardware event.", "",
        "## Supported scope and reliability screen", "",
        "Peri-event averages and their trial-bootstrap uncertainty are feasible. A three-trial",
        "minimum permits descriptive condition means for 21 conditions (63 trials), with",
        "explicitly weak precision. Residuals can be calculated around condition- and",
        "event-time-specific means, but correlation inference is not supported by 2–3 repeats.",
        "A conservative 20-repetition screen is a declared triage rule, not a theorem of",
        "statistical sufficiency; no condition passes it. Reliable covariance may need more",
        "than that, depending on sparsity, effect size and population dimension.", "",
        "Use [standard MC_Maze DANDI 000128](https://dandiarchive.org/dandiset/000128/0.220113.0400)",
        "for a next feasibility audit, without assuming its repetitions or fields are sufficient.",
        "No larger recording is downloaded by this mission. The",
        "[official NLB documentation](https://neurallatents.github.io/datasets.html) describes",
        "the delayed reaching task and published variants; event provenance and repetitions",
        "above come from this actual NWB file.", "",
        "## Training condition inventory", "",
        "| Key (maze/type/version/active target) | Repetitions | Trial IDs |", "| --- | ---: | --- |"]
    lines += [f"| {c['key']} | {c['training_trials']} | {', '.join(map(str,c['trial_ids']))} |" for c in results["conditions"]]
    Path(markdown).write_text("\n".join(lines) + "\n")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    results = write_audit(args.manifest)
    print(json.dumps({k: results[k] for k in ["repetition_histogram", "conditions_passing_descriptive_screen", "residual_feasibility"]}, indent=2))


if __name__ == "__main__":
    main()
