"""Verify the installed package without adding src to the import path."""

import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import cerebro


def test_import_uses_source_package():
    root = Path(__file__).resolve().parents[1]
    assert Path(cerebro.__file__).resolve() == root / "src/cerebro/__init__.py"


def test_installed_metadata():
    metadata = importlib.metadata.metadata("cerebro")
    assert metadata["Version"] == "0.1.0"
    assert set(metadata["Requires-Python"].split(",")) == {">=3.11", "<3.12"}


def test_import_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-c",
         "import cerebro; print(cerebro.__file__)"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert Path(result.stdout.strip()).resolve() == Path(cerebro.__file__).resolve()


def test_editable_install():
    distribution = importlib.metadata.distribution("cerebro")
    direct_url = json.loads(distribution.read_text("direct_url.json"))
    assert direct_url["dir_info"]["editable"] is True
