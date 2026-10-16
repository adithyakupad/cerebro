"""Recover checksum-pinned Brochier members from the publisher's ZIP by byte range."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
from urllib.request import Request, urlopen
import zlib


MANIFEST = Path("docs/datasets/mission_019_brochier_assets.json")
RAW_DIR = Path("data/raw/brochier")
CHUNK_BYTES = 16_777_216


def read_archive_range(url, archive_size, etag, start, stop):
    request_headers = {"Range": f"bytes={start}-{stop}", "If-Range": etag}
    request = Request(url, headers=request_headers)
    with urlopen(request, timeout=60) as response:
        expected_range = f"bytes {start}-{stop}/{archive_size}"
        actual_range = response.headers.get("Content-Range")
        if response.status != 206 or actual_range != expected_range:
            raise ValueError("Publisher archive range or revision changed")
        content = response.read()
    expected_length = stop - start + 1
    if len(content) != expected_length:
        raise ValueError("Publisher archive range was truncated")
    return content


def extract_member(entry, read_range, output_path):
    """Extract one original ZIP member; validate name, size, CRC and SHA-256."""
    header_offset = entry["local_header_offset"]
    header = read_range(header_offset, header_offset + 29)
    fields = struct.unpack("<IHHHHHIIIHH", header)
    signature = fields[0]
    flags = fields[2]
    compression_method = fields[3]
    filename_length = fields[9]
    extra_length = fields[10]
    if signature != 0x04034B50 or compression_method != 8 or flags & 1:
        raise ValueError("Unsupported or encrypted publisher ZIP member")

    name_start = header_offset + 30
    name_stop = name_start + filename_length - 1
    native_name = read_range(name_start, name_stop).decode("utf-8")
    if native_name != entry["archive_path"]:
        raise ValueError("Publisher ZIP member name changed")

    data_start = name_stop + 1 + extra_length
    data_stop = data_start + entry["compressed_bytes"]
    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    digest = hashlib.sha256()
    crc = 0
    byte_count = 0
    temporary_path = output_path.with_suffix(output_path.suffix + ".part")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # shortcut: a failed range restarts this member, add resumable state if source reliability demands it.
    try:
        with temporary_path.open("wb") as target:
            for chunk_start in range(data_start, data_stop, CHUNK_BYTES):
                chunk_stop = min(chunk_start + CHUNK_BYTES, data_stop) - 1
                compressed = read_range(chunk_start, chunk_stop)
                original = decompressor.decompress(compressed)
                target.write(original)
                digest.update(original)
                crc = zlib.crc32(original, crc)
                byte_count += len(original)
            final_bytes = decompressor.flush()
            target.write(final_bytes)
            digest.update(final_bytes)
            crc = zlib.crc32(final_bytes, crc)
            byte_count += len(final_bytes)
        valid_stream = decompressor.eof and not decompressor.unused_data
        valid_size = byte_count == entry["size_bytes"]
        valid_crc = f"{crc:08x}" == entry["zip_crc32"]
        valid_sha = digest.hexdigest() == entry["sha256"]
        if not all((valid_stream, valid_size, valid_crc, valid_sha)):
            raise ValueError("Publisher ZIP member failed integrity verification")
        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", nargs="+", help="Names from the pinned manifest")
    arguments = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    archive = manifest["archive"]
    for asset_name in arguments.assets:
        entry = manifest["assets"][asset_name]
        output_path = RAW_DIR / asset_name
        if output_path.exists():
            with output_path.open("rb") as stream:
                existing = hashlib.file_digest(stream, "sha256").hexdigest()
            if output_path.stat().st_size != entry["size_bytes"] or existing != entry["sha256"]:
                raise ValueError(f"Existing raw asset has wrong SHA-256: {asset_name}")
            print(asset_name, "verified existing", existing)
            continue
        def reader(start, stop):
            return read_archive_range(
                archive["url"], archive["size_bytes"], archive["etag"], start, stop
            )
        checksum = extract_member(entry, reader, output_path)
        print(asset_name, "downloaded and verified", checksum)


if __name__ == "__main__":
    main()
