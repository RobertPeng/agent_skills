#!/usr/bin/env python3
"""
Extract assets from Unity bundles using UnityPy.

UnityPy has a built-in TypeTree database for all Unity versions,
making it capable of reading assets that AssetRipper marks as "Unreadable"
(typically caused by TypeTree stripping in IL2CPP builds).

Supported types: Texture2D, Mesh, AudioClip, TextAsset, Font, Sprite, AnimationClip

Usage:
    python3 extract_assets.py <bundle_dir> <output_dir> [--unity-version 2021.3.57f2] [--types Texture2D,Mesh]

Requirements:
    pip install UnityPy Pillow
"""

import os
import sys
import argparse
import warnings
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy not installed. Run: pip install UnityPy Pillow")
    sys.exit(1)


SUPPORTED_TYPES = {
    "Texture2D", "Mesh", "AudioClip", "TextAsset",
    "Font", "Sprite", "AnimationClip", "MonoBehaviour"
}


def safe_filename(name: str) -> str:
    """Sanitize a filename."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)


def extract_texture2d(obj, output_dir: str) -> bool:
    """Extract Texture2D as PNG."""
    data = obj.read()
    try:
        img = data.image
        if img and img.size[0] > 0 and img.size[1] > 0:
            name = safe_filename(data.m_Name or f"texture_{obj.path_id}")
            outpath = os.path.join(output_dir, f"{name}_{data.m_Width}x{data.m_Height}.png")
            # Handle duplicate names
            if os.path.exists(outpath):
                outpath = os.path.join(output_dir, f"{name}_{data.m_Width}x{data.m_Height}_{obj.path_id}.png")
            img.save(outpath)
            return True
    except Exception:
        pass
    return False


def extract_mesh(obj, output_dir: str) -> bool:
    """Extract Mesh as OBJ."""
    data = obj.read()
    try:
        name = safe_filename(data.m_Name or f"mesh_{obj.path_id}")
        outpath = os.path.join(output_dir, f"{name}.obj")
        if os.path.exists(outpath):
            outpath = os.path.join(output_dir, f"{name}_{obj.path_id}.obj")
        mesh_data = data.export()
        if mesh_data:
            with open(outpath, "w") as f:
                f.write(mesh_data)
            return True
    except Exception:
        pass
    return False


def extract_audioclip(obj, output_dir: str) -> bool:
    """Extract AudioClip as WAV or raw audio."""
    data = obj.read()
    try:
        samples = data.samples
        if samples:
            for name_str, audio_data in samples.items():
                name = safe_filename(name_str or f"audio_{obj.path_id}")
                # Determine extension from data
                ext = ".wav"
                if audio_data[:4] == b"OggS":
                    ext = ".ogg"
                elif audio_data[:4] == b"RIFF":
                    ext = ".wav"
                elif audio_data[:2] == b"\xff\xfb" or audio_data[:3] == b"ID3":
                    ext = ".mp3"
                outpath = os.path.join(output_dir, f"{name}{ext}")
                if os.path.exists(outpath):
                    outpath = os.path.join(output_dir, f"{name}_{obj.path_id}{ext}")
                with open(outpath, "wb") as f:
                    f.write(audio_data)
            return True
    except Exception:
        pass
    return False


def extract_textasset(obj, output_dir: str) -> bool:
    """Extract TextAsset as text or binary."""
    data = obj.read()
    try:
        name = safe_filename(data.m_Name or f"text_{obj.path_id}")
        script = data.m_Script

        if isinstance(script, str):
            outpath = os.path.join(output_dir, f"{name}.txt")
            if os.path.exists(outpath):
                outpath = os.path.join(output_dir, f"{name}_{obj.path_id}.txt")
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(script)
        else:
            # Binary data
            outpath = os.path.join(output_dir, f"{name}.bytes")
            if os.path.exists(outpath):
                outpath = os.path.join(output_dir, f"{name}_{obj.path_id}.bytes")
            with open(outpath, "wb") as f:
                f.write(bytes(script) if not isinstance(script, bytes) else script)
        return True
    except Exception:
        pass
    return False


def extract_font(obj, output_dir: str) -> bool:
    """Extract Font as TTF/OTF."""
    data = obj.read()
    try:
        font_data = data.m_FontData
        if font_data:
            name = safe_filename(data.m_Name or f"font_{obj.path_id}")
            ext = ".otf" if font_data[:4] == b"OTTO" else ".ttf"
            outpath = os.path.join(output_dir, f"{name}{ext}")
            if os.path.exists(outpath):
                outpath = os.path.join(output_dir, f"{name}_{obj.path_id}{ext}")
            with open(outpath, "wb") as f:
                f.write(bytes(font_data))
            return True
    except Exception:
        pass
    return False


def extract_sprite(obj, output_dir: str) -> bool:
    """Extract Sprite as PNG."""
    data = obj.read()
    try:
        img = data.image
        if img and img.size[0] > 0 and img.size[1] > 0:
            name = safe_filename(data.m_Name or f"sprite_{obj.path_id}")
            outpath = os.path.join(output_dir, f"{name}.png")
            if os.path.exists(outpath):
                outpath = os.path.join(output_dir, f"{name}_{obj.path_id}.png")
            img.save(outpath)
            return True
    except Exception:
        pass
    return False


EXTRACTORS = {
    "Texture2D": extract_texture2d,
    "Mesh": extract_mesh,
    "AudioClip": extract_audioclip,
    "TextAsset": extract_textasset,
    "Font": extract_font,
    "Sprite": extract_sprite,
}


def find_bundles(bundle_dir: str) -> list:
    """Find all bundle files in a directory."""
    bundle_path = Path(bundle_dir)
    bundles = []

    # Common bundle extensions
    extensions = {".bundle", ".unity3d", ".assets", ".resource"}

    for f in bundle_path.rglob("*"):
        if f.is_file():
            if f.suffix.lower() in extensions or (not f.suffix and f.stat().st_size > 100):
                bundles.append(f)

    # If nothing found with extensions, try all files
    if not bundles:
        bundles = [f for f in bundle_path.rglob("*") if f.is_file() and f.stat().st_size > 100]

    return sorted(bundles)


def main():
    parser = argparse.ArgumentParser(
        description="Extract assets from Unity bundles using UnityPy"
    )
    parser.add_argument("bundle_dir", help="Directory containing Unity bundles")
    parser.add_argument("output_dir", help="Output directory for extracted assets")
    parser.add_argument(
        "--unity-version", "-v",
        default="2021.3.57f2",
        help="Unity version for TypeTree fallback (default: 2021.3.57f2)"
    )
    parser.add_argument(
        "--types", "-t",
        default=None,
        help=f"Comma-separated list of types to extract (default: all). Available: {','.join(sorted(SUPPORTED_TYPES))}"
    )

    args = parser.parse_args()

    # Set Unity version
    UnityPy.config.FALLBACK_UNITY_VERSION = args.unity_version
    print(f"Unity version: {args.unity_version}")

    # Parse types
    if args.types:
        extract_types = set(args.types.split(","))
        invalid = extract_types - SUPPORTED_TYPES
        if invalid:
            print(f"Warning: Unknown types: {invalid}")
        extract_types &= SUPPORTED_TYPES
    else:
        extract_types = set(EXTRACTORS.keys())

    # Create output directories
    for type_name in extract_types:
        os.makedirs(os.path.join(args.output_dir, type_name), exist_ok=True)

    # Find bundles
    bundles = find_bundles(args.bundle_dir)
    print(f"Found {len(bundles)} bundle files")
    print(f"Extracting types: {', '.join(sorted(extract_types))}")
    print()

    # Extract
    stats = defaultdict(lambda: {"success": 0, "failed": 0})
    total_bundles = len(bundles)

    for i, bundle_file in enumerate(bundles):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"Processing bundle {i + 1}/{total_bundles}...")

        try:
            env = UnityPy.load(str(bundle_file))
            for obj in env.objects:
                type_name = obj.type.name
                if type_name in extract_types and type_name in EXTRACTORS:
                    output_subdir = os.path.join(args.output_dir, type_name)
                    try:
                        success = EXTRACTORS[type_name](obj, output_subdir)
                        if success:
                            stats[type_name]["success"] += 1
                        else:
                            stats[type_name]["failed"] += 1
                    except Exception:
                        stats[type_name]["failed"] += 1
        except Exception as e:
            if "bundle" in str(e).lower() or "unity" in str(e).lower():
                pass  # Skip non-bundle files silently
            else:
                print(f"  Error loading {bundle_file.name}: {e}")

    # Print summary
    print()
    print("=" * 50)
    print("Extraction Summary")
    print("=" * 50)
    total_success = 0
    total_failed = 0
    for type_name in sorted(stats.keys()):
        s = stats[type_name]
        total_success += s["success"]
        total_failed += s["failed"]
        print(f"  {type_name:20s}  {s['success']:6d} extracted, {s['failed']:4d} failed")

    print(f"  {'TOTAL':20s}  {total_success:6d} extracted, {total_failed:4d} failed")
    print()
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
