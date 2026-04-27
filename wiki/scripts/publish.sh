#!/usr/bin/env bash
# publish.sh — 重建注册表 + 记录修订
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WIKI_DIR="$SCRIPT_DIR/../public"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[publish] 重建 pages.json..."
python3 "$SCRIPT_DIR/build_registry.py" "$WIKI_DIR/pages" --out "$WIKI_DIR/pages.json"

echo "[publish] 记录修订到 history/ + recent.json..."
# 检测 git 中新增或修改的页面（已暂存 + 未暂存 + 未跟踪，三种情况都覆盖）
{
  # 已暂存的变更（index vs HEAD）
  git -C "$ROOT" -c core.quotePath=false diff --cached --name-only HEAD 2>/dev/null
  # 未暂存的变更（working tree vs index）
  git -C "$ROOT" -c core.quotePath=false diff --name-only 2>/dev/null
  # 未跟踪的新文件
  git -C "$ROOT" -c core.quotePath=false ls-files --others --exclude-standard 2>/dev/null
} | grep '^wiki/public/pages/.*\.md$' | sort -u | while read -r fpath; do
    slug=$(basename "$fpath" .md)
    echo "  record_revision: $slug"
    python3 "$SCRIPT_DIR/record_revision.py" "$slug" --author butler || true
done

echo "[publish] 更新知识量快照..."
python3 "$SCRIPT_DIR/compute_knowledge.py"

echo "[publish] 完成。请 git add 并提交。"
