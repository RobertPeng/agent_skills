#!/usr/bin/env python3
"""
Strip UnityCFS headers from Unity asset bundles.

UnityCFS format: 32-byte header (magic + version + SHA1 hash) prepended to standard UnityFS data.
This script detects and removes the header, converting CFS bundles to standard UnityFS format.

Usage:
    python3 strip_cfs.py <input_dir> <output_dir>
    python3 strip_cfs.py <input_file> <output_file>
"""

import os
import sys
import struct
import hashlib
from pathlib import Path

CFS_MAGIC = b"UnityCFS"
CFS_HEADER_SIZE = 32
UNITYFS_MAGIC = b"UnityFS"


def is_cfs_bundle(filepath: str) -> bool:
    """Check if a file has a UnityCFS header."""
    try:
        with open(filepath, "rb") as f:
            magic = f.read(8)
            return magic == CFS_MAGIC
    except (IOError, OSError):
        return False


def strip_cfs_header(input_path: str, output_path: str) -> bool:
    """
    Strip UnityCFS header from a bundle file.
    Returns True if header was stripped, False if file was copied as-is.
    """
    with open(input_path, "rb") as f:
        magic = f.read(8)

        if magic == CFS_MAGIC:
            # Read CFS header info
            version = struct.unpack("<I", f.read(4))[0]
            sha1_hash = f.read(20)

            # Read the UnityFS data
            data = f.read()

            # Verify it starts with UnityFS
            if not data.startswith(UNITYFS_MAGIC):
                print(f"  WARNING: Data after CFS header doesn't start with UnityFS: {input_path}")

            # Optionally verify SHA1
            actual_hash = hashlib.sha1(data).digest()
            if actual_hash != sha1_hash:
                print(f"  WARNING: SHA1 mismatch in {input_path} (data may still be valid)")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as out:
                out.write(data)
            return True
        else:
            # Not a CFS file, copy as-is
            f.seek(0)
            data = f.read()
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as out:
                out.write(data)
            return False


def process_directory(input_dir: str, output_dir: str) -> dict:
    """Process all bundle files in a directory."""
    stats = {"cfs_stripped": 0, "already_standard": 0, "errors": 0, "total": 0}

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Find all files (common extensions for Unity bundles)
    bundle_extensions = {".bundle", ".unity3d", ".assets", ".resource", ""}
    files = []
    for f in input_path.rglob("*"):
        if f.is_file() and (f.suffix.lower() in bundle_extensions or not f.suffix):
            files.append(f)

    if not files:
        # If no matching extensions, try all files
        files = [f for f in input_path.rglob("*") if f.is_file()]

    for filepath in sorted(files):
        stats["total"] += 1
        rel_path = filepath.relative_to(input_path)
        out_file = output_path / rel_path

        try:
            was_cfs = strip_cfs_header(str(filepath), str(out_file))
            if was_cfs:
                stats["cfs_stripped"] += 1
                print(f"  [CFS→UnityFS] {rel_path}")
            else:
                stats["already_standard"] += 1
        except Exception as e:
            stats["errors"] += 1
            print(f"  [ERROR] {rel_path}: {e}")

    return stats


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_dir_or_file> <output_dir_or_file>")
        print()
        print("Strip UnityCFS headers from Unity asset bundles.")
        print("Supports both single files and directories (recursive).")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if os.path.isfile(input_path):
        # Single file mode
        was_cfs = strip_cfs_header(input_path, output_path)
        if was_cfs:
            print(f"Stripped CFS header: {input_path} → {output_path}")
        else:
            print(f"Not a CFS file, copied as-is: {input_path} → {output_path}")
    elif os.path.isdir(input_path):
        # Directory mode
        print(f"Processing directory: {input_path}")
        print(f"Output directory: {output_path}")
        print()

        stats = process_directory(input_path, output_path)

        print()
        print(f"Done! Processed {stats['total']} files:")
        print(f"  CFS headers stripped: {stats['cfs_stripped']}")
        print(f"  Already standard:     {stats['already_standard']}")
        if stats["errors"]:
            print(f"  Errors:               {stats['errors']}")
    else:
        print(f"Error: {input_path} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    main()
