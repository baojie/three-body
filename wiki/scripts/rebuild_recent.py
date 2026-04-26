#!/usr/bin/env python3
"""从 wiki/public/history/*.json 重建 recent.json。

每个页面取最新一条 revision，按 timestamp 排序后写入。
用于修复重复条目或从零重建。
"""
import json
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[2]
PUBLIC  = ROOT / "wiki/public"
HIST    = PUBLIC / "history"
RECENT  = PUBLIC / "recent.json"
LIMIT   = 1000


def main():
    entries = []
    for hist_file in sorted(HIST.glob("*.json")):
        try:
            data = json.loads(hist_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  跳过 {hist_file.name}: {e}")
            continue
        revs = data.get("revisions", [])
        if not revs:
            continue
        latest = revs[0]  # revisions[0] 是最新
        entry  = {"page": hist_file.stem, **{k: v for k, v in latest.items() if k != "content"}}
        entries.append(entry)

    entries.sort(key=lambda e: e.get("timestamp", ""))
    entries = entries[-LIMIT:]

    out = {"entries": entries, "rotations": 0}
    RECENT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ recent.json 重建完成：{len(entries)} 条（来自 history/ 中 {len(entries)} 个页面）")


if __name__ == "__main__":
    main()
