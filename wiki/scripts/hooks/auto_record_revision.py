#!/usr/bin/env python3
"""PostToolUse hook: Write/Edit 写入 wiki/public/pages/*.md 时自动补录 revision。

Claude Code 将 hook 事件 JSON 通过 stdin 传入，格式:
  {"tool_name": "Write", "tool_input": {"file_path": "...", ...}, ...}
"""
import json, subprocess, sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parents[3]
PAGES = ROOT / "wiki/public/pages"
REC   = ROOT / "wiki/scripts/record_revision.py"

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
    r = subprocess.run(
        [sys.executable, str(REC), slug,
         "--summary", "auto: direct Write/Edit (bypassed script)",
         "--author", "hook"],
        capture_output=True, text=True, cwd=ROOT
    )
    if r.stdout.strip():
        print(r.stdout.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
