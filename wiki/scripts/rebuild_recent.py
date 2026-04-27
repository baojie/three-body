#!/usr/bin/env python3
"""独立工具：从 wiki/public/recent.jsonl 重建 recent.json（可选快照）。

前端现在直接读取 recent.jsonl，不再依赖 recent.json。
此脚本仅供手动诊断/导出使用，不再由 publish.sh 调用。
支持 --from-history 回退模式：当 recent.jsonl 缺失时从 history/*.jsonl 重建。
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[2]
PUBLIC  = ROOT / "wiki/public"
HIST    = PUBLIC / "history"
JSONL   = PUBLIC / "recent.jsonl"
RECENT  = PUBLIC / "recent.json"
LIMIT   = 600  # 前端窗口大小


def from_jsonl() -> list:
    if not JSONL.exists():
        return []
    entries = []
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def from_history() -> list:
    entries = []
    for hist_file in sorted(HIST.glob("*.jsonl")):
        try:
            lines = [l for l in hist_file.read_text(encoding="utf-8").splitlines() if l.strip()]
            if not lines:
                continue
            latest = json.loads(lines[-1])  # 末行 = 最新
            entry = {"page": hist_file.stem, **{k: v for k, v in latest.items() if k != "content"}}
            entries.append(entry)
        except Exception:
            continue
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-history", action="store_true",
                    help="忽略 recent.jsonl，从 history/*.jsonl 重建")
    ap.add_argument("--limit", type=int, default=LIMIT)
    args = ap.parse_args()

    if args.from_history or not JSONL.exists():
        entries = from_history()
        source = "history/"
    else:
        entries = from_jsonl()
        source = "recent.jsonl"

    entries.sort(key=lambda e: e.get("timestamp", ""))
    entries = entries[-args.limit:]

    out = {"entries": entries, "rotations": 0}
    RECENT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ recent.json 重建完成：{len(entries)} 条（来源：{source}）")


if __name__ == "__main__":
    main()
