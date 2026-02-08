# Agent Skills

一组为 AI Coding Agent 打造的专业技能（Skills），让 Agent 在特定领域具备深度执行能力。

适用于 **Cursor**、**Claude Code** 等支持 Skill 机制的 AI 编程工具。

## 什么是 Skill？

Skill 是一份结构化的指令文档（`SKILL.md`），当用户的任务匹配到关键词时，Agent 会自动加载对应 Skill，按照其中定义的工作流程、工具链和经验知识来完成任务——无需用户手动指定。

## 技能列表

### 🎮 [analyze-game-video](./analyze-game-video/)

从 YouTube 下载游戏视频，用 ffmpeg 截帧，对画面进行多维度分析并生成结构化报告。

**触发场景**：分析游戏视频、研究游戏设计、从 YouTube 素材中提取画面

**工作流程**：`yt-dlp 下载` → `ffmpeg 截帧` → `逐批分析` → `生成 Markdown 报告`

**分析维度**：
- UI/UX 界面设计（HUD 布局、菜单系统、配色方案）
- 游戏玩法机制（核心循环、进度系统、难度曲线）
- 美术风格与视觉表现（风格定位、色彩运用、特效表现）
- 技术实现推测（引擎识别、渲染技术、性能表现）

**依赖**：`yt-dlp`、`ffmpeg`

---

### 🔧 [unity-asset-extract](./unity-asset-extract/)

Unity 游戏资源提取工具包，基于 IL2CPP + TypeTree-stripped 游戏的实战经验沉淀。

**触发关键词**：`AssetRipper`、`UnityPy`、`UnityCFS`、`Unreadable`、`TypeTree`、`asset bundle`、`IL2CPP`、`DummyDll` 等

**文件结构**：

```
unity-asset-extract/
├── SKILL.md                    # 主文档 (8KB)
└── scripts/
    ├── strip_cfs.py            # UnityCFS 头剥离工具
    ├── extract_assets.py       # 全类型资源提取 (Texture/Mesh/Audio/Text/Font/Sprite)
    └── extract_textures.py     # 快速贴图批量提取
```

**包含的经验知识**：

| 章节 | 内容 |
|------|------|
| 诊断流程图 | APK → 检测格式 → 选择工具的决策树 |
| §1 UnityCFS | 32字节头结构、检测方法、剥离脚本 |
| §2 TypeTree + IL2CPP | Unreadable 根因分析、Il2CppDumper 工作流、DummyDll 用法 |
| §3 UnityPy | 配置要点、版本检测方法、批量提取 |
| §4 常见目录结构 | YooAsset / Addressables / 标准 Unity 的目录布局 |
| §5 AssetRipper 技巧 | HTTP API 用法、与 UnityPy 配合策略 |
| §6 导出格式表 | 各资源类型的导出方法和格式 |
| §7 故障排查表 | 8个常见问题的原因和解决方案 |

## 如何使用

将本仓库克隆到对应工具的 Skills 目录，Agent 即可自动识别并加载：

| 工具 | Skills 目录 |
|------|------------|
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |

当用户的提问匹配到 Skill 的触发条件时，Agent 会自动加载并按照 Skill 中定义的流程执行任务。

## 创建新 Skill

每个 Skill 是一个独立目录，至少包含一个 `SKILL.md` 文件：

```
my-skill/
├── SKILL.md          # 必须：技能定义文档
└── scripts/          # 可选：配套脚本
```

`SKILL.md` 的 frontmatter 需包含 `name` 和 `description` 字段，`description` 用于触发匹配。
