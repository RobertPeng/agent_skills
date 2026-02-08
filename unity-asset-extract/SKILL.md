---
name: unity-asset-extract
description: Unity game asset extraction toolkit. Use when user wants to extract, decrypt, or export assets from Unity APK/IPA/bundles, handle UnityCFS encrypted bundles, fix AssetRipper "Unreadable" resources, use UnityPy for batch extraction, or recover TypeTree-stripped assets. Triggers on keywords like "AssetRipper", "UnityPy", "UnityCFS", "Unreadable", "TypeTree", "asset bundle", "extract textures", "extract mesh", "IL2CPP", "DummyDll", or Unity game reverse engineering tasks.
---

# Unity 游戏资源提取技能

基于 IL2CPP + TypeTree-stripped 游戏实战经验的综合提取指南。

## 快速诊断流程图

```
APK/IPA/游戏文件
  │
  ├─ 解压 APK (unzip) → 找到 asset bundle
  │    └─ 常见位置: assets/bin/Data/, assets/yoo/*, assets/aa/*
  │
  ├─ 检查 bundle 格式
  │    ├─ 以 "UnityFS" 开头 → 标准 bundle，直接处理
  │    ├─ 以 "UnityCFS" 开头 → 需先剥离 32 字节头 (见 §1)
  │    ├─ 以 "UnityRaw" 开头 → 旧格式，多数工具支持
  │    └─ 未知魔数 → 可能是自定义加密（需游戏专用解密）
  │
  ├─ 优先尝试 AssetRipper
  │    ├─ 所有资源可读 → 完成!
  │    └─ 大量 "Unreadable" 资源 → 检查脚本后端 (见 §2)
  │
  └─ 若 Unreadable → 使用 UnityPy 内置 TypeTree (见 §3)
```

## §1 UnityCFS 格式（并非真正加密）

UnityCFS 是一层轻量级包装，并非加密。结构如下：

```
偏移    大小   内容
0x00    8     魔数: "UnityCFS"
0x08    4     版本号 (uint32 小端序)
0x0C    20    UnityFS 数据的 SHA1 哈希
0x20    ...   标准 UnityFS 数据从此处开始
```

**检测方法**：前 8 字节 == `UnityCFS`

**解决方案**：剥离前 32 字节。使用 `scripts/strip_cfs.py`：

```bash
python3 scripts/strip_cfs.py <输入目录> <输出目录>
```

## §2 TypeTree 剥离 + IL2CPP（"Unreadable" 的根因）

### 资源为何不可读

Unity 游戏可以剥离 TypeTree 信息以减小 bundle 体积。当 TypeTree 被剥离时：
- **内置类型**（Texture2D、Mesh、AudioClip 等）→ 需要 TypeTree 数据库来反序列化
- **自定义类型**（MonoBehaviour 脚本）→ 需要 DLL 类型信息来反序列化

### 如何判断

1. **检查脚本后端**：查找 `libil2cpp.so`（Android）或 `GameAssembly.dll`（Windows/iOS）
   - 若存在 → IL2CPP 后端，很可能已剥离 TypeTree
2. **在 AssetRipper 中检查**：若大量 Texture2D/Mesh 显示为 "Unreadable" → TypeTree 已剥离

### 恢复策略

| 资源类型 | 解决方案 | 工具 |
|---------|---------|------|
| **内置类型**（Texture2D、Mesh、AudioClip、Shader、AnimationClip、Font、TextAsset、Sprite） | 使用 UnityPy（内置所有 Unity 版本的 TypeTree 数据库） | `scripts/extract_assets.py` |
| **MonoBehaviour**（自定义脚本） | 用 Il2CppDumper 生成 DummyDll，然后在 AssetRipper 中加载 | Il2CppDumper |

### Il2CppDumper 工作流（针对 MonoBehaviour）

```bash
# 1. 获取 Il2CppDumper（匹配你的 .NET 版本）
# 下载地址: https://github.com/Perfare/Il2CppDumper/releases

# 2. 从游戏中获取所需文件:
#    - libil2cpp.so (APK 中的 lib/arm64-v8a/)
#    - global-metadata.dat (assets/bin/Data/Managed/)

# 3. 运行 Il2CppDumper
dotnet Il2CppDumper.dll libil2cpp.so global-metadata.dat /output/path

# 4. 输出: DummyDll/ 目录，包含重建的 .dll 文件
#    将 DummyDll/*.dll 复制到游戏的 Managed/ 目录

# 5. 在 AssetRipper 中重新加载 → MonoBehaviour 类型现在可读了
```

## §3 UnityPy 提取（内置类型的首选方案）

UnityPy 内置了覆盖所有 Unity 版本的 TypeTree 数据库，能读取 AssetRipper 标记为 "Unreadable" 的资源。

### 安装

```bash
pip install UnityPy Pillow
```

### 关键配置

```python
import UnityPy
# 必须为 TypeTree 被剥离的 bundle 设置回退版本号
UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.57f2"  # 匹配游戏的 Unity 版本
```

### 查找 Unity 版本号

```bash
# 方法 1: 从 bundle 头部读取
python3 -c "
with open('somefile.bundle', 'rb') as f:
    data = f.read(64)
    # UnityFS 头部包含版本字符串
    print(data)
"

# 方法 2: 从 globalgamemanagers 或 data.unity3d
strings assets/bin/Data/globalgamemanagers | grep "20[12][0-9]\."

# 方法 3: 从 APK 的 lib 目录
strings lib/arm64-v8a/libunity.so | grep "20[12][0-9]\.[0-9]"
```

### 完整提取

```bash
# 提取所有支持的资源类型
python3 scripts/extract_assets.py <bundle目录> <输出目录> --unity-version 2021.3.57f2

# 仅提取贴图（支持热更新资源）
python3 scripts/extract_textures.py <bundle目录> <输出目录> --unity-version 2021.3.57f2
```

## §4 常见游戏资源目录结构

### YooAsset（国内开发团队常用）

```
assets/
├── yoo/
│   └── Main/           # 主资源包
│       ├── *.bundle     # 资源包（可能带 CFS 头）
│       ├── PackageManifest_*.bytes  # 清单文件
│       └── ...
```

热更新文件通常单独存储在设备上：
```
/sdcard/Android/data/<包名>/files/yoo/Main/  # 或类似路径
```

### Addressables（Unity 默认方案）

```
assets/
├── aa/
│   └── Android/
│       ├── *.bundle
│       └── catalog.json
```

### 标准 Unity 结构

```
assets/
├── bin/
│   └── Data/
│       ├── data.unity3d          # 主数据
│       ├── globalgamemanagers    # 设置
│       ├── Managed/              # DLL (Mono) 或元数据 (IL2CPP)
│       │   └── global-metadata.dat
│       └── Resources/
```

## §5 AssetRipper 使用技巧

### API 模式（无头模式）

```bash
# 启动 AssetRipper GUI，然后通过 HTTP API 操作
# 加载文件夹
curl -X POST http://localhost:8888/LoadFolder \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "path=/path/to/bundles"

# 导出全部
curl -X POST http://localhost:8888/ExportAll \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "path=/path/to/output"
```

### 提升导出效果

1. **添加 DummyDll**：加载前将 Il2CppDumper 输出的 DLL 复制到游戏的 `Managed/` 目录
2. **设置 Unity 版本**：确保正确检测到版本号
3. **与 UnityPy 配合使用**：AssetRipper 处理场景结构 + MonoBehaviour；UnityPy 处理贴图/网格/音频

## §6 支持的导出格式

| 类型 | UnityPy 导出方法 | 格式 | 备注 |
|------|----------------|------|------|
| Texture2D | `obj.read().image.save()` | PNG | 支持所有贴图格式（ETC、ASTC、DXT 等） |
| Mesh | `obj.read().export()` | OBJ | 包含顶点、法线、UV、面 |
| AudioClip | `obj.read().samples` | WAV/raw | 返回 {名称: 字节} 字典 |
| TextAsset | `obj.read().m_Script` | TXT/bytes | 可能是二进制数据 |
| Font | `obj.read().m_FontData` | TTF/OTF | 原始字体数据 |
| Sprite | `obj.read().image.save()` | PNG | 从图集中裁剪 |
| AnimationClip | 有限支持 | — | 格式复杂，可导出 YAML |
| Shader | 有限支持 | — | 已编译着色器，难以反编译 |
| MonoBehaviour | `obj.read_typetree()` | JSON/dict | 需要 TypeTree 或 DummyDll |

## §7 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| "No valid Unity version found" | TypeTree 已剥离，未设置版本号 | 设置 `FALLBACK_UNITY_VERSION` |
| 贴图导出为纯色 | 贴图格式检测错误 | 更新 UnityPy 到最新版本 |
| 网格缺少 UV | UV 数据在其他通道中 | 检查 `m_UV1`、`m_UV2` 等 |
| AudioClip 采样为空 | FMOD 音频（已加密） | 需要 FMOD bank 提取工具 |
| MonoBehaviour 不可读 | 缺少类型定义 | 使用 Il2CppDumper → DummyDll |
| AssetRipper Content-Type 错误 | HTTP 请求格式错误 | 使用 `application/x-www-form-urlencoded` |
| .NET 版本不匹配 | Il2CppDumper 需要特定 .NET 版本 | 下载匹配的版本（net6/net7/net8） |
| CFS bundle 无法加载 | UnityCFS 头未剥离 | 剥离前 32 字节 |
