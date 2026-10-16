"""Check selective publisher-ZIP recovery without network or neural fixtures."""

from hashlib import sha256
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from tools.fetch_brochier import extract_member


def test_extract_member_checks_original_bytes_and_checksum(tmp_path):
    archive_path = tmp_path / "publisher.zip"
    original = b"authentic bytes are required for scientific claims" * 10
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("datasets/sample.odml", original)
    with ZipFile(archive_path) as archive:
        info = archive.getinfo("datasets/sample.odml")
    archive_bytes = archive_path.read_bytes()
    entry = {
        "archive_path": info.filename,
        "local_header_offset": info.header_offset,
        "compressed_bytes": info.compress_size,
        "size_bytes": info.file_size,
        "zip_crc32": f"{info.CRC:08x}",
        "sha256": sha256(original).hexdigest(),
    }
    def read_range(start, stop):
        return archive_bytes[start:stop + 1]

    output_path = tmp_path / "sample.odml"
    assert extract_member(entry, read_range, output_path) == entry["sha256"]
    assert output_path.read_bytes() == original

    wrong_entry = dict(entry, sha256="0" * 64)
    bad_output_path = tmp_path / "wrong.odml"
    with pytest.raises(ValueError, match="integrity"):
        extract_member(wrong_entry, read_range, bad_output_path)
    assert not bad_output_path.exists()
