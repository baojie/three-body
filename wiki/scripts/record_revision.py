#!/usr/bin/env python3
"""record_revision.py — 为 wiki/public/pages/<page>.md 写入一条修订记录。

产出:
  1. wiki/public/history/<page>.json   (per-page 索引，追加 entry)
  2. wiki/public/recent.json           (全局修订日志，滚动窗口 1000 条)

rev_id 格式: YYYYMMDD-HHMMSS-<sha256[:6]>  (UTC)
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "wiki/public"
PAGES  = PUBLIC / "pages"
HIST   = PUBLIC / "history"
RECENT = PUBLIC / "recent.json"

WINDOW_SIZE   = 1000
ARCHIVE_BATCH = 500
LOG_DIR       = ROOT / "wiki/logs/recent"


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

    # ── per-page history ──────────────────────────────────────────────────────
    HIST.mkdir(exist_ok=True)
    page_json = HIST / f"{page}.json"
    if page_json.exists():
        data = json.loads(page_json.read_text(encoding="utf-8"))
    else:
        data = {"page": page, "latest_rev_id": None, "revision_count": 0, "revisions": []}

    if data["revisions"] and data["revisions"][0].get("content_hash") == f"sha256:{sha}":
        print(f"= {page} 内容与 latest 相同，跳过")
        return 0

    size_before = data["revisions"][0]["size"] if data["revisions"] else 0
    size_after  = len(content.encode("utf-8"))
    entry = {
        "rev_id":       rev_id,
        "timestamp":    ts_iso,
        "author":       args.author,
        "summary":      args.summary or f"{args.author} {args.action}",
        "parent_rev":   data["latest_rev_id"],
        "content_hash": f"sha256:{sha}",
        "size_before":  size_before,
        "size":         size_after,
        "content":      content,
    }
    if args.action == "delete":
        entry["action"] = "delete"

    data["revisions"].insert(0, entry)
    data["latest_rev_id"]  = rev_id
    data["revision_count"] = len(data["revisions"])
    if args.action == "delete":
        data["deleted"]    = True
        data["deleted_at"] = ts_iso

    page_json.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # ── recent.json ───────────────────────────────────────────────────────────
    if RECENT.exists():
        recent = json.loads(RECENT.read_text(encoding="utf-8"))
        # 迁移旧 {"recent": [...]} 格式
        if "recent" in recent and "entries" not in recent:
            recent = {"entries": recent["recent"]}
    else:
        recent = {"entries": []}

    rotations = recent.get("rotations", 0)
    entries   = recent.get("entries", [])

    new_entry = {"page": page, **{k: v for k, v in entry.items() if k != "content"}}
    entries.append(new_entry)

    if len(entries) > WINDOW_SIZE:
        batch    = entries[:ARCHIVE_BATCH]
        entries  = entries[ARCHIVE_BATCH:]
        rotations += 1
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        lines = "\n".join(json.dumps(e, ensure_ascii=False) for e in batch) + "\n"
        (LOG_DIR / f"recent.{rotations}.jsonl").write_text(lines, encoding="utf-8")
        print(f"  [archive] {len(batch)} entries → wiki/logs/recent/recent.{rotations}.jsonl")

    recent = {"entries": entries, "rotations": rotations}
    RECENT.write_text(
        json.dumps(recent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    delta = size_after - size_before
    print(f"✓ {page} rev={rev_id} size={size_before}→{size_after}({'+' if delta>=0 else ''}{delta}) author={args.author}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
