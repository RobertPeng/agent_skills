---
name: unity-asset-extract
description: Unity game asset extraction toolkit. Use when user wants to extract, decrypt, or export assets from Unity APK/IPA/bundles, handle UnityCFS encrypted bundles, fix AssetRipper "Unreadable" resources, use UnityPy for batch extraction, or recover TypeTree-stripped assets. Triggers on keywords like "AssetRipper", "UnityPy", "UnityCFS", "Unreadable", "TypeTree", "asset bundle", "extract textures", "extract mesh", "IL2CPP", "DummyDll", or Unity game reverse engineering tasks.
---

# Unity Game Asset Extraction Skill

A comprehensive guide for extracting assets from Unity games, based on real-world experience with IL2CPP + TypeTree-stripped games.

## Quick Diagnosis Flowchart

```
APK/IPA/Game Files
  │
  ├─ Extract APK (unzip) → Find asset bundles
  │    └─ Common locations: assets/bin/Data/, assets/yoo/*, assets/aa/*
  │
  ├─ Check bundle format
  │    ├─ Starts with "UnityFS" → Standard bundle, proceed normally
  │    ├─ Starts with "UnityCFS" → Strip 32-byte header first (see §1)
  │    ├─ Starts with "UnityRaw" → Old format, most tools support it
  │    └─ Unknown magic → May be custom encryption (need game-specific decryption)
  │
  ├─ Try AssetRipper first
  │    ├─ All resources readable → Done!
  │    └─ Many "Unreadable" resources → Check scripting backend (see §2)
  │
  └─ If Unreadable → Use UnityPy with built-in TypeTree (see §3)
```

## §1 UnityCFS Format (Not Real Encryption)

UnityCFS is a lightweight wrapper, NOT encryption. Structure:

```
Offset  Size  Content
0x00    8     Magic: "UnityCFS"
0x08    4     Version (uint32 LE)
0x0C    20    SHA1 hash of the UnityFS data
0x20    ...   Standard UnityFS data starts here
```

**Detection**: First 8 bytes == `UnityCFS`

**Solution**: Strip the first 32 bytes. Use `scripts/strip_cfs.py`:

```bash
python3 scripts/strip_cfs.py <input_dir> <output_dir>
```

## §2 TypeTree Stripping + IL2CPP (Root Cause of "Unreadable")

### Why Resources Are Unreadable

Unity games can strip TypeTree info to reduce bundle size. When TypeTree is stripped:
- **Built-in types** (Texture2D, Mesh, AudioClip, etc.) → need TypeTree database to deserialize
- **Custom types** (MonoBehaviour scripts) → need DLL type info to deserialize

### How to Identify

1. **Check scripting backend**: Look for `libil2cpp.so` (Android) or `GameAssembly.dll` (Windows/iOS)
   - If present → IL2CPP backend, likely TypeTree-stripped
2. **Check in AssetRipper**: If many Texture2D/Mesh show as "Unreadable" → TypeTree stripped

### Recovery Strategy

| Resource Type | Solution | Tool |
|--------------|----------|------|
| **Built-in types** (Texture2D, Mesh, AudioClip, Shader, AnimationClip, Font, TextAsset, Sprite) | Use UnityPy (has built-in TypeTree DB for all Unity versions) | `scripts/extract_assets.py` |
| **MonoBehaviour** (custom scripts) | Use Il2CppDumper to generate DummyDll, then load in AssetRipper | Il2CppDumper |

### Il2CppDumper Workflow (for MonoBehaviour)

```bash
# 1. Get Il2CppDumper (match your .NET version)
# Download from: https://github.com/Perfare/Il2CppDumper/releases

# 2. Required files from game:
#    - libil2cpp.so (from lib/arm64-v8a/ in APK)
#    - global-metadata.dat (from assets/bin/Data/Managed/)

# 3. Run Il2CppDumper
dotnet Il2CppDumper.dll libil2cpp.so global-metadata.dat /output/path

# 4. Output: DummyDll/ directory with reconstructed .dll files
#    Copy DummyDll/*.dll → game's Managed/ directory

# 5. Reload in AssetRipper → MonoBehaviour types now readable
```

## §3 UnityPy Extraction (Primary Solution for Built-in Types)

UnityPy has a built-in TypeTree database covering all Unity versions. It can read resources that AssetRipper marks as "Unreadable".

### Setup

```bash
pip install UnityPy Pillow
```

### Critical Configuration

```python
import UnityPy
# MUST set fallback version for TypeTree-stripped bundles
UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.57f2"  # Match game's Unity version
```

### Finding Unity Version

```bash
# Method 1: From bundle header
python3 -c "
with open('somefile.bundle', 'rb') as f:
    data = f.read(64)
    # UnityFS header contains version string
    print(data)
"

# Method 2: From globalgamemanagers or data.unity3d
strings assets/bin/Data/globalgamemanagers | grep "20[12][0-9]\."

# Method 3: From APK lib
strings lib/arm64-v8a/libunity.so | grep "20[12][0-9]\.[0-9]"
```

### Full Extraction

```bash
# Extract all supported asset types
python3 scripts/extract_assets.py <bundle_dir> <output_dir> --unity-version 2021.3.57f2

# Extract textures only (with hotupdate support)
python3 scripts/extract_textures.py <bundle_dir> <output_dir> --unity-version 2021.3.57f2
```

## §4 Common Game Resource Structures

### YooAsset (Common in Chinese Mobile Games)

```
assets/
├── yoo/
│   └── Main/           # Main asset bundles
│       ├── *.bundle     # Asset bundles (may have CFS header)
│       ├── PackageManifest_*.bytes  # Manifest
│       └── ...
```

Hotupdate files typically stored separately on device:
```
/sdcard/Android/data/<package>/files/yoo/Main/  # or similar
```

### Addressables (Unity Default)

```
assets/
├── aa/
│   └── Android/
│       ├── *.bundle
│       └── catalog.json
```

### Standard Unity

```
assets/
├── bin/
│   └── Data/
│       ├── data.unity3d          # Main data
│       ├── globalgamemanagers    # Settings
│       ├── Managed/              # DLLs (Mono) or metadata (IL2CPP)
│       │   └── global-metadata.dat
│       └── Resources/
```

## §5 AssetRipper Usage Tips

### API Mode (Headless)

```bash
# Start AssetRipper GUI, then use HTTP API
# Load folder
curl -X POST http://localhost:8888/LoadFolder \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "path=/path/to/bundles"

# Export all
curl -X POST http://localhost:8888/ExportAll \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "path=/path/to/output"
```

### Improving Results

1. **Add DummyDll**: Copy Il2CppDumper output DLLs to game's `Managed/` directory before loading
2. **Set Unity version**: Ensure correct version is detected
3. **Use with UnityPy**: AssetRipper for scene structure + MonoBehaviour; UnityPy for textures/meshes/audio

## §6 Supported Export Formats

| Type | UnityPy Export | Format | Notes |
|------|---------------|--------|-------|
| Texture2D | `obj.read().image.save()` | PNG | Includes all texture formats (ETC, ASTC, DXT, etc.) |
| Mesh | `obj.read().export()` | OBJ | Vertices, normals, UVs, faces |
| AudioClip | `obj.read().samples` | WAV/raw | Dict of {name: bytes} |
| TextAsset | `obj.read().m_Script` | TXT/bytes | May be binary data |
| Font | `obj.read().m_FontData` | TTF/OTF | Raw font data |
| Sprite | `obj.read().image.save()` | PNG | Cropped from atlas |
| AnimationClip | Limited support | — | Complex format, YAML possible |
| Shader | Limited support | — | Compiled shader, hard to decompile |
| MonoBehaviour | `obj.read_typetree()` | JSON/dict | Needs TypeTree or DummyDll |

## §7 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "No valid Unity version found" | TypeTree stripped, no version set | Set `FALLBACK_UNITY_VERSION` |
| Texture exports as solid color | Wrong texture format detection | Update UnityPy to latest |
| Mesh has no UVs | UV data in separate channel | Check `m_UV1`, `m_UV2`, etc. |
| AudioClip empty samples | FMOD audio (encrypted) | Need FMOD bank extraction |
| MonoBehaviour unreadable | Missing type definitions | Use Il2CppDumper → DummyDll |
| AssetRipper Content-Type error | Wrong HTTP request format | Use `application/x-www-form-urlencoded` |
| .NET version mismatch | Il2CppDumper needs specific .NET | Download matching version (net6/net7/net8) |
| CFS bundles won't load | UnityCFS header not stripped | Strip first 32 bytes |
