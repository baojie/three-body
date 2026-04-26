#!/usr/bin/env bash
# publish.sh — 将 wiki/public/ 同步到 docs/（GitHub Pages 源目录）
set -euo pipefail

WIKI_DIR="$(cd "$(dirname "$0")/../public" && pwd)"
DOCS_DIR="$(cd "$(dirname "$0")/../../docs" && pwd)"

echo "[publish] 重建 pages.json..."
python3 "$(dirname "$0")/build_registry.py" "$WIKI_DIR/pages" --out "$WIKI_DIR/pages.json"

echo "[publish] 同步 wiki/public → docs/..."
rsync -av --delete \
  --exclude='.DS_Store' \
  "$WIKI_DIR/" "$DOCS_DIR/"

# GitHub Pages 需要此文件来禁用 Jekyll
touch "$DOCS_DIR/.nojekyll"

echo "[publish] 完成。docs/ 已更新，请 git add docs/ 并提交。"
