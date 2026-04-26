#!/usr/bin/env python3
"""edit_page.py — 编辑 wiki 页面并自动记录修订历史。

用法:
    python3 wiki/scripts/edit_page.py <slug> <content_file> \
        [--summary "更新: ..."] [--author butler]

    # 从 stdin 读取:
    cat new.md | python3 wiki/scripts/edit_page.py <slug> - --summary "..."

铁律（不可绕过，除非显式传标志）:
    - 旧版有 frontmatter（--- 开头），新版没有 → 拒绝（退出码 3）
    - 新版 size < 旧版 size × 0.6 → 拒绝（退出码 4）
    - 以上两条加 --allow-shrink 可跳过（仅限 redirect/merge 操作）
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[2]
PAGES  = ROOT / "wiki/public/pages"
REC    = ROOT / "wiki/scripts/record_revision.py"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", help="页面 slug（不含 .md）")
    ap.add_argument("content_file", help="内容文件路径，或 - 表示 stdin")
    ap.add_argument("--summary", default="")
    ap.add_argument("--author", default="butler")
    ap.add_argument("--allow-shrink", action="store_true",
                    help="允许 frontmatter 丢失或内容大幅缩减（redirect/merge 专用）")
    args = ap.parse_args()

    target = PAGES / f"{args.slug}.md"
    if not target.exists():
        print(f"✗ 页面不存在: {target}（请用 add_page.py）", file=sys.stderr)
        sys.exit(1)

    old_content = target.read_text(encoding="utf-8")

    if args.content_file == "-":
        new_content = sys.stdin.read()
    else:
        src = Path(args.content_file)
        if not src.exists():
            print(f"✗ 内容文件不存在: {src}", file=sys.stderr)
            sys.exit(1)
        new_content = src.read_text(encoding="utf-8")

    # 铁律1：frontmatter 不得被非授权操作删除
    if not args.allow_shrink and old_content.lstrip().startswith("---") and not new_content.lstrip().startswith("---"):
        print(
            f"⛔ 禁止写入：{args.slug} 旧版含 frontmatter，新版缺失。\n"
            f"   若确为 redirect/merge 操作，请加 --allow-shrink 标志。",
            file=sys.stderr,
        )
        sys.exit(3)

    # 铁律2：禁止内容大幅缩减（新版 < 旧版 60%）
    old_size = len(old_content.encode("utf-8"))
    new_size  = len(new_content.encode("utf-8"))
    if not args.allow_shrink and old_size > 400 and new_size < old_size * 0.6:
        print(
            f"⛔ 禁止写入：{args.slug} 新版 {new_size}B 不足旧版 {old_size}B 的 60%。\n"
            f"   若确为 redirect/merge 操作，请加 --allow-shrink 标志。",
            file=sys.stderr,
        )
        sys.exit(4)

    target.write_text(new_content, encoding="utf-8")
    print(f"✓ 更新 {target}")

    r = subprocess.run(
        [sys.executable, str(REC), args.slug,
         "--summary", args.summary or f"编辑: {args.slug}",
         "--author", args.author],
        capture_output=True, text=True, cwd=ROOT
    )
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
