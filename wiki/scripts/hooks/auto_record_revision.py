#!/usr/bin/env python3
"""PostToolUse hook: Write/Edit 写入 wiki/public/pages/*.md 时自动补录 revision。

Claude Code 将 hook 事件 JSON 通过 stdin 传入，格式:
  {"tool_name": "Write", "tool_input": {"file_path": "...", ...}, ...}

若 wiki/logs/butler/pending_revision.json 存在，则使用其中的 author/summary/round 信息
（butler 在写页面前写入，hook 消费后删除）。
"""
import json, subprocess, sys
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[3]
PAGES   = ROOT / "wiki/public/pages"
REC     = ROOT / "wiki/scripts/record_revision.py"
PENDING = ROOT / "wiki/logs/butler/pending_revision.json"


def _consume_pending() -> tuple[str, str]:
    """读取并删除 pending_revision.json，返回 (author, summary)。"""
    if not PENDING.exists():
        return "hook", ""
    try:
        ctx = json.loads(PENDING.read_text(encoding="utf-8"))
        PENDING.unlink(missing_ok=True)
        author  = ctx.get("author", "butler")
        round_n = ctx.get("round", "")
        atype   = ctx.get("type", "")
        desc    = ctx.get("desc", "")
        parts   = [f"R{round_n}" if round_n else "", atype, desc]
        summary = " ".join(p for p in parts if p)
        return author, summary or atype or "butler edit"
    except Exception:
        PENDING.unlink(missing_ok=True)
        return "hook", ""


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    file_path  = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    p = Path(file_path)
    try:
        p.resolve().relative_to(PAGES.resolve())
    except ValueError:
        sys.exit(0)  # 不在 pages/ 下，忽略

    if p.suffix != ".md":
        sys.exit(0)

    if not p.exists():
        sys.exit(0)  # 文件不存在（删除场景），忽略

    slug = p.stem
    author, summary = _consume_pending()
    if not summary:
        summary = f"hook: {slug}"

    r = subprocess.run(
        [sys.executable, str(REC), slug,
         "--summary", summary,
         "--author", author],
        capture_output=True, text=True, cwd=ROOT
    )
    if r.stdout.strip():
        print(r.stdout.strip(), file=sys.stderr)


if __name__ == "__main__":
    main()
