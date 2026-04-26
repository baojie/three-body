#!/usr/bin/env python3
"""从 git log 回填 wiki/public/history/ 和 wiki/public/recent.json。

每个提交中改动的页面文件 → 调用 record_revision.py（带 --timestamp）。
已有 history/<page>.json 的页面默认跳过，除非传 --force。
"""
import argparse, subprocess, sys, os
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[2]
PAGES_DIR   = ROOT / "wiki/public/pages"
RECORD_REV  = Path(__file__).parent / "record_revision.py"
PAGES_PFX   = "wiki/public/pages/"


def git(*args):
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        text=True, errors="replace", cwd=ROOT
    ).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="重建所有，即使 history/ 已存在")
    ap.add_argument("--author", default="git", help="写入修订的 author 字段")
    args = ap.parse_args()

    hist_dir = ROOT / "wiki/public/history"
    existing = {p.stem for p in hist_dir.glob("*.json")} if not args.force else set()

    # git log: 每次 commit 一个 COMMIT 块，后跟改动的文件
    log = git(
        "log", "--format=COMMIT|%H|%aI|%an|%s",
        "--name-only", "--diff-filter=AM",
        "--", f"{PAGES_PFX}*.md"
    )

    commits = []
    current = None
    for line in log.splitlines():
        if line.startswith("COMMIT|"):
            _, rev, ts, author, summary = line.split("|", 4)
            current = {"rev": rev, "ts": ts, "author": author, "summary": summary, "files": []}
            commits.append(current)
        elif line.startswith(PAGES_PFX) and current:
            current["files"].append(line)

    # 按时间正序处理（最旧的提交先写入）
    commits.reverse()

    total = 0
    for c in commits:
        for fpath in c["files"]:
            slug = os.path.basename(fpath)[:-3]
            if slug in existing:
                continue
            page_md = PAGES_DIR / f"{slug}.md"
            if not page_md.exists():
                continue
            r = subprocess.run(
                [sys.executable, str(RECORD_REV),
                 slug,
                 "--author", c["author"],
                 "--summary", c["summary"],
                 "--timestamp", c["ts"]],
                capture_output=True, text=True, cwd=ROOT
            )
            if r.returncode != 0:
                print(f"  ✗ {slug}: {r.stderr.strip()}")
            else:
                print(r.stdout.strip())
                total += 1

    print(f"\n完成：共写入 {total} 条修订记录。")


if __name__ == "__main__":
    main()
