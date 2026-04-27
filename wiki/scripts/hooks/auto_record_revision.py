#!/usr/bin/env python3
"""PostToolUse hook: Write/Edit 写入 wiki/public/pages/*.md 时自动补录 revision。

Claude Code 将 hook 事件 JSON 通过 stdin 传入，格式:
  {"tool_name": "Write", "tool_input": {"file_path": "...", ...}, ...}

Butler 在写页面前必须写入 per-slug pending 文件：
  wiki/logs/butler/pending_revision_{slug}.json
hook 读取对应 slug 的文件并消费，避免多实例并发时相互覆盖。
兜底（无 pending 文件）时 author 为 "claude"。
"""
import json, subprocess, sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parents[3]
PAGES = ROOT / "wiki/public/pages"
REC   = ROOT / "wiki/scripts/record_revision.py"
PENDING_DIR = ROOT / "wiki/logs/butler"


def _consume_pending(slug: str) -> tuple[str, str]:
    """读取并删除 pending_revision_{slug}.json，返回 (author, summary)。"""
    pending = PENDING_DIR / f"pending_revision_{slug}.json"
    if not pending.exists():
        return "claude", ""
    try:
        ctx = json.loads(pending.read_text(encoding="utf-8"))
        pending.unlink(missing_ok=True)
        author  = ctx.get("author", "butler")
        round_n = ctx.get("round", "")
        atype   = ctx.get("type", "")
        desc    = ctx.get("desc", "")
        parts   = [f"R{round_n}" if round_n else "", atype, desc]
        summary = " ".join(p for p in parts if p)
        return author, summary or atype or "butler edit"
    except Exception:
        pending.unlink(missing_ok=True)
        return "claude", ""


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
    author, summary = _consume_pending(slug)
    if not summary:
        summary = f"claude: {slug}"

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
