#!/usr/bin/env python3
"""delete_page.py — "删除" wiki 页面：保留文件，改为 deleted stub 或 redirect。

用法:
    # 默认：改为 deleted stub
    python3 wiki/scripts/delete_page.py <slug> [--summary "..."] [--author butler]

    # 合并后保留入口：改为 redirect
    python3 wiki/scripts/delete_page.py <slug> --redirect-to <target> [--summary "..."]

规则:
    - 永不物理删除文件
    - 先调用 record_revision.py 存档当前版本快照
    - 无 --redirect-to：写入 type:deleted stub，--action delete
    - 有 --redirect-to：写入 type:redirect 页，--action edit
    - history/<slug>.json 始终保留
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[2]
PAGES  = ROOT / "wiki/public/pages"
REC    = ROOT / "wiki/scripts/record_revision.py"
REG    = ROOT / "wiki/scripts/build_registry.py"


def _rebuild_registry() -> None:
    r = subprocess.run(
        [sys.executable, str(REG), str(PAGES), "--out", str(ROOT / "wiki/public/pages.json")],
        capture_output=True, text=True, cwd=ROOT
    )
    if r.returncode == 0:
        print("✓ pages.json 已更新")
    else:
        print(f"⚠ pages.json 更新失败: {r.stderr.strip()}", file=sys.stderr)


def _redirect_content(slug: str, target: str) -> str:
    return f"---\nid: {slug}\ntype: redirect\ntarget: {target}\nquality: standard\n---\n#REDIRECT [[{target}]]\n"


def _deleted_content(slug: str) -> str:
    return f"---\nid: {slug}\ntype: deleted\n---\n"


def _record(slug: str, summary: str, author: str, action: str = "edit") -> bool:
    r = subprocess.run(
        [sys.executable, str(REC), slug,
         "--summary", summary, "--author", author, "--action", action],
        capture_output=True, text=True, cwd=ROOT
    )
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", help="页面 slug（不含 .md）")
    ap.add_argument("--redirect-to", metavar="TARGET", default=None,
                    help="改为 redirect 而非 deleted stub")
    ap.add_argument("--summary", default="")
    ap.add_argument("--author", default="butler")
    args = ap.parse_args()

    target_file = PAGES / f"{args.slug}.md"
    if not target_file.exists():
        print(f"✗ 页面不存在: {target_file}", file=sys.stderr)
        sys.exit(1)

    # 先存档当前版本快照
    action = "edit" if args.redirect_to else "delete"
    if not _record(args.slug, args.summary or f"存档: {args.slug}", args.author, action=action):
        sys.exit(1)

    # 写入新内容
    if args.redirect_to:
        target_file.write_text(_redirect_content(args.slug, args.redirect_to), encoding="utf-8")
        print(f"✓ {args.slug} → REDIRECT [[{args.redirect_to}]]（文件保留）")
    else:
        target_file.write_text(_deleted_content(args.slug), encoding="utf-8")
        print(f"✓ {args.slug} → deleted stub（文件保留，内容已清空）")

    _rebuild_registry()


if __name__ == "__main__":
    main()
