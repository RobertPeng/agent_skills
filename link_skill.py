#!/usr/bin/env python3
"""
Agent Skills 链接管理工具

将本仓库中的技能（含 SKILL.md 的目录）符号链接到对应 AI 工具的 Skills 目录：
  - ~/.claude/skills/   (Claude Code)
  - ~/.cursor/skills/   (Cursor)

用法:
  python link_skill.py                     # 交互式选择
  python link_skill.py -t claude           # 链接到 Claude Code
  python link_skill.py -t cursor           # 链接到 Cursor
  python link_skill.py -t claude -s unity-asset-extract  # 指定技能
  python link_skill.py -t claude --all     # 链接全部技能
  python link_skill.py --unlink -t claude -s unity-asset-extract  # 取消链接
  python link_skill.py --status            # 查看当前链接状态
"""

import argparse
import os
import sys
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────────────────────────

TARGETS = {
    "claude": Path.home() / ".claude" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
}

REPO_ROOT = Path(__file__).resolve().parent

# ── ANSI 颜色 ─────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def color(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{RESET}"


# ── 工具函数 ──────────────────────────────────────────────────────────────────


def discover_skills() -> list[Path]:
    """扫描仓库根目录，返回所有含 SKILL.md 的一级子目录。"""
    skills = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            if (entry / "SKILL.md").exists():
                skills.append(entry)
    return skills


def get_link_status(skill_path: Path, target_dir: Path) -> str:
    """
    返回链接状态:
      'linked'    - 已正确符号链接到本仓库
      'conflict'  - 目标路径已存在（非本仓库链接）
      'none'      - 未链接
    """
    dest = target_dir / skill_path.name
    if dest.is_symlink():
        real = dest.resolve()
        if real == skill_path.resolve():
            return "linked"
        return "conflict"
    elif dest.exists():
        return "conflict"
    return "none"


def format_status_badge(status: str) -> str:
    if status == "linked":
        return color("● 已链接", GREEN)
    elif status == "conflict":
        return color("▲ 冲突", YELLOW)
    return color("○ 未链接", DIM)


def print_skill_table(skills: list[Path]):
    """打印技能列表和当前链接状态。"""
    print(f"\n{color('可用技能', BOLD)}  (仓库: {REPO_ROOT})\n")
    header = f"  {'序号':<6} {'技能名称':<30} {'Claude Code':<16} {'Cursor':<16}"
    print(color(header, DIM))
    print(color("  " + "─" * 70, DIM))
    for i, skill in enumerate(skills, 1):
        claude_st = format_status_badge(get_link_status(skill, TARGETS["claude"]))
        cursor_st = format_status_badge(get_link_status(skill, TARGETS["cursor"]))
        print(f"  {i:<6} {skill.name:<30} {claude_st:<28} {cursor_st:<28}")
    print()


def link_skill(skill_path: Path, target_dir: Path, force: bool = False) -> bool:
    """创建符号链接，返回是否成功。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / skill_path.name

    if dest.is_symlink():
        real = dest.resolve()
        if real == skill_path.resolve():
            print(f"  {color('跳过', DIM)} {skill_path.name} → 已链接")
            return True
        if force:
            dest.unlink()
            print(f"  {color('替换', YELLOW)} 移除旧链接 → {real}")
        else:
            print(f"  {color('冲突', RED)} {dest} 已链接到 {real}")
            print(f"         使用 --force 覆盖")
            return False
    elif dest.exists():
        if force:
            import shutil
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
            print(f"  {color('替换', YELLOW)} 移除已有目录/文件 {dest}")
        else:
            print(f"  {color('冲突', RED)} {dest} 已存在（非符号链接）")
            print(f"         使用 --force 覆盖")
            return False

    dest.symlink_to(skill_path.resolve())
    print(f"  {color('链接', GREEN)} {skill_path.name} → {dest}")
    return True


def unlink_skill(skill_path: Path, target_dir: Path) -> bool:
    """移除符号链接，返回是否成功。"""
    dest = target_dir / skill_path.name

    if dest.is_symlink():
        real = dest.resolve()
        if real == skill_path.resolve():
            dest.unlink()
            print(f"  {color('已取消链接', GREEN)} {skill_path.name} (从 {target_dir})")
            return True
        else:
            print(f"  {color('跳过', YELLOW)} {dest} 链接到其他位置 ({real})，不操作")
            return False
    elif dest.exists():
        print(f"  {color('跳过', YELLOW)} {dest} 不是符号链接，不操作")
        return False
    else:
        print(f"  {color('跳过', DIM)} {skill_path.name} 在 {target_dir} 中不存在")
        return True


# ── 交互式选择 ────────────────────────────────────────────────────────────────


def prompt_choice(prompt: str, options: list[str], allow_multiple: bool = False) -> list[int]:
    """交互式选择，返回选中的索引列表。"""
    while True:
        if allow_multiple:
            raw = input(f"{prompt} (逗号分隔多选, a=全部): ").strip()
            if raw.lower() == "a":
                return list(range(len(options)))
        else:
            raw = input(f"{prompt}: ").strip()

        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            if all(0 <= i < len(options) for i in indices):
                return indices
        except ValueError:
            pass
        print(color("  输入无效，请重试", RED))


def interactive_mode(force: bool = False):
    """交互式引导用户完成链接操作。"""
    skills = discover_skills()
    if not skills:
        print(color("未在仓库中发现任何技能（含 SKILL.md 的目录）", RED))
        return

    print_skill_table(skills)

    # 选择操作
    print("  操作:")
    print(f"    1) {color('链接', GREEN)} 技能")
    print(f"    2) {color('取消链接', YELLOW)} 技能")
    print()
    action_idx = prompt_choice("  选择操作 [1/2]", ["link", "unlink"])
    action = "link" if action_idx[0] == 0 else "unlink"

    # 选择目标
    print()
    print("  目标:")
    target_names = list(TARGETS.keys())
    for i, name in enumerate(target_names, 1):
        print(f"    {i}) {name:<12} ({TARGETS[name]})")
    print()
    target_indices = prompt_choice("  选择目标", target_names, allow_multiple=True)

    # 选择技能
    print()
    print("  技能:")
    for i, skill in enumerate(skills, 1):
        print(f"    {i}) {skill.name}")
    print()
    skill_indices = prompt_choice("  选择技能", [s.name for s in skills], allow_multiple=True)

    # 执行
    print()
    for ti in target_indices:
        target_name = target_names[ti]
        target_dir = TARGETS[target_name]
        print(f"  {color(f'[{target_name}]', CYAN)} {target_dir}")
        for si in skill_indices:
            skill = skills[si]
            if action == "link":
                link_skill(skill, target_dir, force=force)
            else:
                unlink_skill(skill, target_dir)
        print()

    print(color("完成!", GREEN))


# ── CLI ───────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent Skills 链接管理工具 — 将技能符号链接到 AI 工具的 Skills 目录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-t", "--target",
        choices=list(TARGETS.keys()),
        help="目标工具 (claude / cursor)",
    )
    parser.add_argument(
        "-s", "--skill",
        action="append",
        help="要操作的技能名称（可多次指定）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="操作全部技能",
    )
    parser.add_argument(
        "--unlink",
        action="store_true",
        help="取消链接（默认为创建链接）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的目标",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="仅显示当前链接状态",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    skills = discover_skills()
    if not skills:
        print(color("未在仓库中发现任何技能（含 SKILL.md 的目录）", RED))
        sys.exit(1)

    # --status: 仅显示状态
    if args.status:
        print_skill_table(skills)
        return

    # 无参数 → 交互模式
    if not args.target and not args.skill and not args.all:
        interactive_mode(force=args.force)
        return

    # 命令行模式需要 --target
    if not args.target:
        parser.error("请指定 --target (claude / cursor)")

    target_dir = TARGETS[args.target]

    # 确定要操作的技能
    skill_map = {s.name: s for s in skills}
    if args.all:
        selected = skills
    elif args.skill:
        selected = []
        for name in args.skill:
            if name not in skill_map:
                print(color(f"未找到技能: {name}", RED))
                print(f"  可用技能: {', '.join(skill_map.keys())}")
                sys.exit(1)
            selected.append(skill_map[name])
    else:
        selected = skills  # 未指定则全部

    # 执行
    print(f"\n  {color(f'[{args.target}]', CYAN)} {target_dir}\n")
    ok = True
    for skill in selected:
        if args.unlink:
            ok &= unlink_skill(skill, target_dir)
        else:
            ok &= link_skill(skill, target_dir, force=args.force)

    print()
    if ok:
        print(color("完成!", GREEN))
    else:
        print(color("部分操作失败，请检查上面的输出", YELLOW))
        sys.exit(1)


if __name__ == "__main__":
    main()
