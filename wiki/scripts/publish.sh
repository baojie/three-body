#!/usr/bin/env bash
# publish.sh — 重建注册表 + 记录修订
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WIKI_DIR="$SCRIPT_DIR/../public"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[publish] 重建 pages.json..."
python3 "$SCRIPT_DIR/build_registry.py" "$WIKI_DIR/pages" --out "$WIKI_DIR/pages.json"

echo "[publish] 记录修订到 history/ + recent.json..."
# 检测 git 中新增或修改的页面（未提交的变更）
changed=$(git -C "$ROOT" -c core.quotePath=false \
    diff --name-only HEAD -- "wiki/public/pages/*.md" 2>/dev/null || true)
untracked=$(git -C "$ROOT" -c core.quotePath=false \
    ls-files --others --exclude-standard "wiki/public/pages/*.md" 2>/dev/null || true)

for fpath in $changed $untracked; do
    slug=$(basename "$fpath" .md)
    echo "  record_revision: $slug"
    python3 "$SCRIPT_DIR/record_revision.py" "$slug" --author butler || true
done

echo "[publish] 完成。请 git add 并提交。"
