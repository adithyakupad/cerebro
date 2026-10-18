"""Release review evidence must be portable, deterministic and data-free."""

import hashlib
import json
from pathlib import Path
import runpy
from zipfile import ZipFile


def test_review_configuration_archive_is_deterministic_and_data_free(tmp_path):
    build = runpy.run_path('tools/build_review_package.py')['build']
    first = build(tmp_path / 'first')
    second = build(tmp_path / 'second')
    assert first == second
    archive_path = tmp_path / 'first/v1_1_configurations.zip'
    assert archive_path.read_bytes() == (tmp_path / 'second/v1_1_configurations.zip').read_bytes()
    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert len(names) == 15
        assert 'configs/m022_calibration.json' in names
        assert 'docs/research/m023_protocol.md' in names
        assert not any(name.endswith(('.nwb', '.npz', '.pt')) for name in names)
        for record in first['archive_payload']:
            assert hashlib.sha256(archive.read(record['path'])).hexdigest() == record['sha256']


def test_review_manifest_preserves_frozen_science_and_matches_files(tmp_path):
    build = runpy.run_path('tools/build_review_package.py')['build']
    generated = build(tmp_path)
    published = json.loads(Path('reports/v1_1_review_manifest.json').read_text())
    assert generated == published
    assert generated['package_version'] == '1.1.0'
    decisions = generated['scientific_decisions']
    assert decisions['M022_selected_mitigation'] is None
    assert decisions['M023_selected_reliability_model'] is None
    assert decisions['M023_temporal_promotion'] is False
    assert decisions['later_session_model_outcomes_scored'] is False
    for group in ('experiment_reports', 'scientific_source', 'figures_and_presentation'):
        for record in generated[group]:
            assert hashlib.sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256']
