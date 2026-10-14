"""Acquire a pinned public asset and verify it before scientific use."""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def verify_asset(path, manifest):
    """Check identity by published byte size and SHA-256 (not an S3 ETag)."""
    path = Path(path)
    if path.stat().st_size != manifest["size_bytes"]:
        raise ValueError("Asset size does not match provenance")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != manifest["sha256"]:
        raise ValueError("Asset checksum does not match provenance")
    return digest


def download_asset(manifest):
    """Download to a partial file; preserve any existing verified recording."""
    with urllib.request.urlopen(manifest["metadata_url"], timeout=30) as response:
        metadata = json.load(response)
    if (metadata["identifier"] != manifest["asset_id"]
            or metadata["path"] != manifest["asset_path"]
            or metadata["contentSize"] != manifest["size_bytes"]
            or metadata["digest"]["dandi:sha2-256"] != manifest["sha256"]):
        raise ValueError("Published metadata does not match pinned manifest")
    path = Path(manifest["local_path"])
    if path.exists():
        verify_asset(path, manifest)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".part")
    # Keep interrupted partial files for diagnosis; exclusive creation prevents
    # silently overwriting one on a later attempt.
    with urllib.request.urlopen(manifest["download_url"], timeout=60) as response:
        with partial.open("xb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    verify_asset(partial, manifest)
    partial.rename(path)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    print(download_asset(manifest))


if __name__ == "__main__":
    main()
