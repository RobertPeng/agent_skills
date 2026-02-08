#!/usr/bin/env python3
"""
Fast texture extraction from Unity bundles using UnityPy.

Optimized for batch Texture2D extraction with progress reporting.
Handles TypeTree-stripped bundles via UnityPy's built-in TypeTree database.

Usage:
    python3 extract_textures.py <bundle_dir> <output_dir> [--unity-version 2021.3.57f2]

Requirements:
    pip install UnityPy Pillow
"""

import os
import sys
import argparse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy not installed. Run: pip install UnityPy Pillow")
    sys.exit(1)


def safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)


def find_bundles(bundle_dir: str) -> list:
    bundle_path = Path(bundle_dir)
    bundles = []
    extensions = {".bundle", ".unity3d", ".assets", ".resource"}

    for f in bundle_path.rglob("*"):
        if f.is_file() and (f.suffix.lower() in extensions or (not f.suffix and f.stat().st_size > 100)):
            bundles.append(f)

    if not bundles:
        bundles = [f for f in bundle_path.rglob("*") if f.is_file() and f.stat().st_size > 100]

    return sorted(bundles)


def main():
    parser = argparse.ArgumentParser(description="Extract Texture2D from Unity bundles")
    parser.add_argument("bundle_dir", help="Directory containing Unity bundles")
    parser.add_argument("output_dir", help="Output directory for PNG textures")
    parser.add_argument("--unity-version", "-v", default="2021.3.57f2",
                        help="Unity version (default: 2021.3.57f2)")
    parser.add_argument("--min-size", type=int, default=0,
                        help="Minimum texture dimension to export (default: 0)")

    args = parser.parse_args()

    UnityPy.config.FALLBACK_UNITY_VERSION = args.unity_version
    os.makedirs(args.output_dir, exist_ok=True)

    bundles = find_bundles(args.bundle_dir)
    print(f"Unity version: {args.unity_version}")
    print(f"Found {len(bundles)} bundles")
    print(f"Output: {args.output_dir}")
    print()

    extracted = 0
    failed = 0
    skipped = 0

    for i, bundle_file in enumerate(bundles):
        if (i + 1) % 100 == 0 or i == 0:
            print(f"  [{i + 1}/{len(bundles)}] Processing... ({extracted} textures extracted)")

        try:
            env = UnityPy.load(str(bundle_file))
            for obj in env.objects:
                if obj.type.name == "Texture2D":
                    try:
                        data = obj.read()

                        # Skip small textures if min-size set
                        if args.min_size > 0:
                            if data.m_Width < args.min_size and data.m_Height < args.min_size:
                                skipped += 1
                                continue

                        img = data.image
                        if img and img.size[0] > 0 and img.size[1] > 0:
                            name = safe_filename(data.m_Name or f"texture_{obj.path_id}")
                            outpath = os.path.join(
                                args.output_dir,
                                f"{name}_{data.m_Width}x{data.m_Height}.png"
                            )
                            if os.path.exists(outpath):
                                outpath = os.path.join(
                                    args.output_dir,
                                    f"{name}_{data.m_Width}x{data.m_Height}_{obj.path_id}.png"
                                )
                            img.save(outpath)
                            extracted += 1
                        else:
                            failed += 1
                    except Exception:
                        failed += 1
        except Exception:
            pass

    print()
    print("=" * 40)
    print(f"  Extracted: {extracted}")
    print(f"  Failed:    {failed}")
    if skipped:
        print(f"  Skipped:   {skipped} (below min-size)")
    print(f"  Output:    {args.output_dir}")
    print("=" * 40)


if __name__ == "__main__":
    main()
