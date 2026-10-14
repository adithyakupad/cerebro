"""Audit standard MC_Maze repetitions using original compatible conditions."""

import argparse
import hashlib
import json
from pathlib import Path

from cerebro.dataset import verify_asset
from cerebro.event_audit import audit
from cerebro.sense import load_recording


def run(manifest_path, output):
    manifest = json.loads(Path(manifest_path).read_text())
    verify_asset(manifest['local_path'], manifest)
    recording = load_recording(manifest['local_path'])
    report = audit(recording)
    qualifying = report['conditions_passing_residual_screen']
    report['residual_feasibility'] = (
        f'{qualifying} conditions pass the declared 20-trial screening threshold; '
        'screening is not evidence of reliable high-dimensional covariance. '
        'No residual correlation inference performed in this feasibility audit.'
    )
    report['provenance'] = manifest
    report['source_sha256'] = {}
    for filename in ('maze_feasibility.py', 'event_audit.py', 'sense.py'):
        source = Path(__file__).parent / filename
        report['source_sha256'][filename] = hashlib.sha256(source.read_bytes()).hexdigest()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--output', default='reports/mc_maze_event_feasibility.json')
    arguments = parser.parse_args()
    report = run(arguments.manifest, arguments.output)
    print(json.dumps({key: report[key] for key in ('training_trials', 'unused_validation_trials', 'repetition_histogram', 'residual_feasibility')}, indent=2))


if __name__ == '__main__':
    main()
