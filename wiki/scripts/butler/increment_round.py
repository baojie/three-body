#!/usr/bin/env python3
"""原子递增 round_counter.txt，输出新轮号。

用法：
    ROUND=$(python3 wiki/scripts/butler/increment_round.py)
    echo "本轮：$ROUND"

使用 fcntl.flock 排他锁，多个并发实例不会读到同一轮号。
"""
import fcntl, sys
from pathlib import Path

COUNTER = Path(__file__).resolve().parents[3] / "wiki/logs/butler/round_counter.txt"


def main() -> int:
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    # r+ 模式要求文件存在；a+ 模式 seek(0) 后读取正确但写入位置仍在末尾
    # 用 open(O_RDWR|O_CREAT) 绕过两者限制
    import os as _os
    fd = _os.open(str(COUNTER), _os.O_RDWR | _os.O_CREAT, 0o644)
    with _os.fdopen(fd, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        raw = f.read().strip()
        # 取最后一行（防止并发写残留多行）
        last = raw.splitlines()[-1] if raw else ""
        val = int(last) + 1 if last.isdigit() else 1
        f.seek(0)
        f.write(str(val) + "\n")
        f.truncate()
        # flock 随 close 释放
    print(val)
    return 0


if __name__ == "__main__":
    sys.exit(main())
