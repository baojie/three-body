#!/usr/bin/env python3
"""record_revision.py — 为 wiki/public/pages/<page>.md 写入一条修订记录。

产出:
  1. wiki/public/history/<page>.jsonl  (per-page 索引，JSONL 格式，flock 保护)
  2. wiki/public/recent.jsonl          (全局修订日志，O_APPEND 原子追加)

recent.json 由 rebuild_recent.py 在发布时从 recent.jsonl 重建，供前端读取。

rev_id 格式: YYYYMMDD-HHMMSS-<sha256[:6]>  (UTC)
"""
from __future__ import annotations
import argparse, difflib, fcntl, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[2]
PUBLIC  = ROOT / "wiki/public"
PAGES   = PUBLIC / "pages"
HIST    = PUBLIC / "history"
RECENT  = PUBLIC / "recent.jsonl"


def _diff(old: str, new: str, context: int = 2) -> list[list[str]]:
    """行级 unified diff，返回 [["+"/"-"/" ", line], ...] 去掉 @@/---/+++ 头。"""
    chunks = []
    for line in difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        n=context,
    ):
        if line.startswith(("--- ", "+++ ", "@@ ")):
            continue
        op = line[0] if line else " "
        text = line[1:].rstrip("\n") if line else ""
        chunks.append([op, text])
    return chunks


def _iso(dt: datetime) -> str:
    s = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return s[:-2] + ":" + s[-2:] if not s.endswith("Z") else s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page", help="slug（不含 .md）")
    ap.add_argument("--summary", default="")
    ap.add_argument("--author", default="butler")
    ap.add_argument("--action", default="edit", choices=["edit", "delete"])
    ap.add_argument("--timestamp", default=None, help="ISO 时间（默认现在）")
    args = ap.parse_args()

    page = args.page
    src  = PAGES / f"{page}.md"
    if not src.exists():
        print(f"✗ {src} 不存在", file=sys.stderr)
        return 1

    content = src.read_text(encoding="utf-8")
    sha     = hashlib.sha256(content.encode("utf-8")).hexdigest()

    if args.timestamp:
        now = datetime.fromisoformat(args.timestamp)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now = now.astimezone(timezone.utc)
    else:
        now = datetime.now(timezone.utc)

    rev_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{sha[:6]}"
    ts_iso = _iso(now)

    # ── per-page history（flock 排他锁，防并发覆写）────────────────────────────
    HIST.mkdir(exist_ok=True)
    page_jsonl = HIST / f"{page}.jsonl"

    # 以 a+ 模式打开保证文件存在，再 flock
    with page_jsonl.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        lines = [l for l in fh.read().splitlines() if l.strip()]
        entries = []
        for l in lines:
            try:
                entries.append(json.loads(l))
            except json.JSONDecodeError:
                pass

        # 去重：末行（最新）content_hash 与当前相同则跳过
        if entries and entries[-1].get("content_hash") == f"sha256:{sha}":
            print(f"= {page} 内容与 latest 相同，跳过")
            return 0

        # 从末行（最新条目）取 parent 信息
        last = entries[-1] if entries else None
        parent_content = last["content"] if last else ""
        size_before    = last["size"] if last else 0
        parent_rev     = last["rev_id"] if last else None

        size_after  = len(content.encode("utf-8"))
        diff_chunks = _diff(parent_content, content)
        entry = {
            "rev_id":       rev_id,
            "timestamp":    ts_iso,
            "author":       args.author,
            "summary":      args.summary or f"{args.author} {args.action}",
            "parent_rev":   parent_rev,
            "content_hash": f"sha256:{sha}",
            "size_before":  size_before,
            "size":         size_after,
            "content":      content,
        }
        if args.action == "delete":
            entry["action"] = "delete"

        # 追加新行到文件末尾
        fh.seek(0, 2)
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # flock 在 close 时自动释放

    # ── recent.jsonl（O_APPEND 原子追加，无需锁）─────────────────────────────
    # diff 计算针对本页在 recent.jsonl 中的上一行版本（即 parent_content，已在 flock 内取得）
    RECENT.parent.mkdir(exist_ok=True)
    recent_entry = {
        "page": page,
        **{k: v for k, v in entry.items() if k != "content"},
        "diff": diff_chunks,
    }
    line = json.dumps(recent_entry, ensure_ascii=False) + "\n"
    with RECENT.open("a", encoding="utf-8") as f:
        f.write(line)

    delta = size_after - size_before
    print(f"✓ {page} rev={rev_id} size={size_before}→{size_after}({'+' if delta>=0 else ''}{delta}) author={args.author}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
