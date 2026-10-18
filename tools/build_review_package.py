"""Build a deterministic configuration archive and v1.1 research evidence index."""

import argparse
import hashlib
import json
from pathlib import Path
import tomllib
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


CONFIGURATIONS = [
    'configs/m022_calibration.json', 'configs/m023_protocol.json',
    'configs/link_20200127.json', 'configs/link_20200130.json',
    'configs/link_20200204.json', 'configs/link_20200205.json',
    'configs/link_20200224.json', 'configs/link_20200225.json', 'configs/link_20200626.json',
]
PROTOCOLS = [
    'docs/research/m022_protocol.md', 'docs/research/m023_protocol.md',
    'docs/research/m023_reliability_clarification.md',
]
REPORTS = ['reports/m022_calibration_mechanisms.json', 'reports/m023_reliability.json', 'reports/m023_dynamics.json']
SOURCES = [
    'src/cerebro/calibration_mechanisms.py', 'src/cerebro/reliability.py',
    'src/cerebro/research_dynamics.py', 'src/cerebro/longitudinal.py',
    'src/cerebro/population.py', 'src/cerebro/link.py',
]
FIGURES = [
    'reports/figures/m022_mechanism_comparison.pdf',
    'reports/figures/m023_reliability.pdf', 'reports/figures/m023_dynamics_comparison.pdf',
    'reports/m023_research_presentation.pptx',
]


def entry(path):
    payload = Path(path).read_bytes()
    return {'path': path, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}


def build(output='reports'):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    payload_paths = CONFIGURATIONS + PROTOCOLS + [
        'docs/datasets/m023_native_eligibility.json', 'docs/release/data_attribution.md', 'LICENSE',
    ]
    archive_path = output / 'v1_1_configurations.zip'
    with ZipFile(archive_path, 'w') as archive:
        for path in sorted(payload_paths):
            info = ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, Path(path).read_bytes())
    reports = [json.loads(Path(path).read_text()) for path in REPORTS]
    metadata = tomllib.loads(Path('pyproject.toml').read_text())['project']
    manifest = {
        'schema_version': 1, 'package_version': metadata['version'],
        'publication_status': 'Candidate only; merge/tag/release require explicit owner approval',
        'v1_0_0_commit': 'b780e5cc53f246f4b305d413c4bd1afb962ff42c',
        'historical_research_heads': {'M022': '222486826cc4562669370b6f0486477b79bb740a',
                                      'M023': '99ef1831ba009e53bac05d97e49c3da22da5e455'},
        'archive': {'name': archive_path.name, 'bytes': archive_path.stat().st_size,
                    'sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest()},
        'archive_payload': [entry(path) for path in sorted(payload_paths)],
        'experiment_reports': [entry(path) for path in REPORTS],
        'scientific_source': [entry(path) for path in SOURCES],
        'figures_and_presentation': [entry(path) for path in FIGURES],
        'assets': [json.loads(Path(path).read_text()) for path in CONFIGURATIONS[2:]],
        'scientific_decisions': {'M022_selected_mitigation': reports[0]['promotion']['selected_method'],
                                 'M023_selected_reliability_model': reports[1]['evaluation']['selected_method'],
                                 'M023_temporal_promotion': reports[2]['temporal_gate']['passed'],
                                 'later_session_model_outcomes_scored': False},
        'archive_scope': 'Configurations, frozen protocols, native audit and attribution only; no raw recordings, derived arrays or checkpoints',
    }
    (output / 'v1_1_review_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='reports')
    arguments = parser.parse_args()
    build(arguments.output)
