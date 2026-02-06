---
name: analyze-game-video
description: Analyze game videos from YouTube by downloading with yt-dlp, extracting frames with ffmpeg, and providing comprehensive analysis of UI/UX, gameplay, art style, and technical implementation. Use when the user wants to analyze a game video, study game design from YouTube footage, or extract frames from gameplay videos.
---

# 游戏视频分析

从 YouTube 下载游戏视频，用 ffmpeg 截帧，对截取的画面进行全面分析并生成报告。

## 前置依赖

- `yt-dlp`：下载 YouTube 视频
- `ffmpeg`：视频截帧

## 工作流程

### Step 1: 下载视频

使用 yt-dlp 下载视频到临时目录：

```bash
mkdir -p /tmp/game-video-analysis
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
  --merge-output-format mp4 \
  -o "/tmp/game-video-analysis/%(title)s.%(ext)s" \
  "<YouTube_URL>"
```

如果只需要分析画面（不需要音频），可以只下载视频流以加快速度：

```bash
yt-dlp -f "bestvideo[height<=1080]" \
  -o "/tmp/game-video-analysis/%(title)s.%(ext)s" \
  "<YouTube_URL>"
```

### Step 2: 截帧

默认每秒截 1 帧。用户可指定不同的截帧频率。

```bash
mkdir -p /tmp/game-video-analysis/frames
ffmpeg -i "/tmp/game-video-analysis/<video_file>" \
  -vf "fps=1" \
  -q:v 2 \
  "/tmp/game-video-analysis/frames/frame_%04d.jpg"
```

常用截帧频率参考：

| 频率 | fps 值 | 适用场景 |
|------|--------|----------|
| 每秒 1 帧 | `fps=1` | 默认，通用分析 |
| 每 2 秒 1 帧 | `fps=0.5` | 长视频概览 |
| 每 5 秒 1 帧 | `fps=0.2` | 快速浏览 |
| 每秒 2 帧 | `fps=2` | 动作细节分析 |

截帧完成后，统计总帧数以便规划分析：

```bash
ls /tmp/game-video-analysis/frames/ | wc -l
```

### Step 3: 分析截帧

逐批读取截帧图片（每批 5-10 张），从以下四个维度进行分析：

#### 3.1 UI/UX 界面设计
- HUD 布局与信息层级
- 菜单系统与导航流程
- 字体、图标、配色方案
- 交互反馈（按钮状态、动画提示）
- 信息密度与可读性

#### 3.2 游戏玩法机制
- 核心循环（Core Loop）
- 操作方式与控制方案
- 进度系统与成长体系
- 关卡/场景设计思路
- 难度曲线与节奏控制

#### 3.3 美术风格与视觉表现
- 整体美术风格定位（写实 / 卡通 / 像素 / 其他）
- 色彩运用与氛围营造
- 角色与场景设计特点
- 特效与粒子系统表现
- 光影与后处理效果

#### 3.4 技术实现
- 推测使用的引擎或框架
- 渲染技术特点
- 性能表现观察（帧率、加载等）
- 值得借鉴的技术方案

### Step 4: 生成报告

将分析结果输出为 Markdown 文件，保存到 `Docs/` 目录。

**报告模板：**

```markdown
# [游戏名称] 视频分析报告

> 视频来源：[YouTube URL]
> 分析日期：[日期]
> 截帧设置：每秒 X 帧，共 N 帧

## 概述
[一段话总结游戏的核心特点与整体印象]

## UI/UX 分析
### 亮点
- ...
### 可改进之处
- ...

## 玩法机制分析
### 核心循环
- ...
### 特色系统
- ...

## 美术风格分析
### 风格定位
- ...
### 视觉亮点
- ...

## 技术实现分析
### 引擎与技术
- ...
### 值得借鉴
- ...

## 关键截帧参考
[插入最具代表性的截帧及说明]

## 总结与启发
### 可借鉴的设计要素
1. ...
2. ...
3. ...

### 对当前项目的建议
1. ...
2. ...
3. ...
```

### Step 5: 清理

分析完成后，询问用户是否删除临时文件：

```bash
rm -rf /tmp/game-video-analysis
```

## 注意事项

- 截帧数量较多时（>50），分批分析，每批 5-10 张
- 优先分析画面变化较大的帧，跳过重复或相似的帧
- 如果视频较长（>10 分钟），建议降低截帧频率或截取特定时间段
- 截取特定时间段示例：`ffmpeg -ss 00:01:00 -to 00:03:00 -i video.mp4 -vf "fps=1" -q:v 2 frames/frame_%04d.jpg`
- 报告文件名格式：`Docs/GameAnalysis_[游戏名]_[日期].md`
