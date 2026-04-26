#!/usr/bin/env bash
# 启动三体 Wiki 本地服务（前台，Ctrl+C 停止）
#
# 用法:
#   ./wiki/wiki.sh          # 默认端口 8001
#   ./wiki/wiki.sh 9001     # 指定端口

set -euo pipefail

PORT="${1:-8001}"
WIKI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLIC_DIR="$WIKI_ROOT/public"
REGISTRY_SCRIPT="$WIKI_ROOT/scripts/build_registry.py"
SERVE_SCRIPT="$WIKI_ROOT/server/serve.js"

for f in "$PUBLIC_DIR" "$REGISTRY_SCRIPT" "$SERVE_SCRIPT"; do
  if [[ ! -e "$f" ]]; then
    echo "✗ 未找到: $f" >&2; exit 1
  fi
done
if ! command -v node >/dev/null 2>&1; then
  echo "✗ 未找到 node，请先安装 Node.js" >&2; exit 1
fi

echo "[1/2] 重建 pages.json..."
python3 "$REGISTRY_SCRIPT" "$PUBLIC_DIR/pages" --out "$PUBLIC_DIR/pages.json"

echo "[2/2] 启动服务 (Ctrl+C 停止)"
exec node "$SERVE_SCRIPT" "$PUBLIC_DIR" "$PORT"
