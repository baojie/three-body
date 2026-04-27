#!/usr/bin/env python3
"""原子递增 round_counter.txt，输出新轮号。

用法：
    ROUND=$(python3 wiki/scripts/butler/increment_round.py)
    echo "本轮：$ROUND"

使用 O_CREAT|O_EXCL 锁文件方案，对同进程多线程和跨进程均有效
（fcntl.flock 在同进程不同线程间不提供隔离）。
"""
import os, sys, time
from pathlib import Path

COUNTER  = Path(__file__).resolve().parents[3] / "wiki/logs/butler/round_counter.txt"
LOCKFILE = COUNTER.parent / "round_counter.lock"
MAX_WAIT = 10.0   # 最多等待秒数
RETRY_MS = 0.05   # 每次重试间隔


def _acquire_lock() -> None:
    deadline = time.monotonic() + MAX_WAIT
    while True:
        try:
            fd = os.open(str(LOCKFILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            if time.monotonic() > deadline:
                # 锁文件超时（持有者崩溃），强制清除
                LOCKFILE.unlink(missing_ok=True)
            time.sleep(RETRY_MS)


def _release_lock() -> None:
    LOCKFILE.unlink(missing_ok=True)


def main() -> int:
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    _acquire_lock()
    try:
        raw = COUNTER.read_text(encoding="utf-8").strip() if COUNTER.exists() else ""
        last = raw.splitlines()[-1] if raw else ""
        val = int(last) + 1 if last.isdigit() else 1
        tmp = COUNTER.with_suffix(".tmp")
        tmp.write_text(str(val) + "\n", encoding="utf-8")
        os.replace(tmp, COUNTER)   # 原子替换
    finally:
        _release_lock()
    print(val)
    return 0


if __name__ == "__main__":
    sys.exit(main())
