#!/usr/bin/env bash
# publish.sh — 重建 wiki/public/pages.json（docs/ 已软链接到 wiki/public/，无需同步）
set -euo pipefail

WIKI_DIR="$(cd "$(dirname "$0")/../public" && pwd)"

echo "[publish] 重建 pages.json..."
python3 "$(dirname "$0")/build_registry.py" "$WIKI_DIR/pages" --out "$WIKI_DIR/pages.json"

echo "[publish] 完成。请 git add 并提交。"
