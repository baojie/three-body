#!/usr/bin/env python3
"""从 queue.md 原子领取一个任务（[ ] → [~]）。

用法：
    python3 wiki/scripts/butler/claim_task.py [--focus create|enrich|all] [--instance ID] [--stale-minutes N]

输出（JSON to stdout）：
    {"page": "希恩斯", "type": "create", "priority": "P1", "note": "corpus 147处"}
    或：{"page": null}  （无可用任务）

三态说明：
    - [ ]  available   — 未认领
    - [~]  in-progress — 已被某实例认领，格式：- [~] P1 create | 页面 | [instance@HH:MM:SS] 备注
    - [x]  done        — 已完成

超过 --stale-minutes（默认30）未完成的 [~] 任务视为超时，可被其他实例抢占。
"""
from __future__ import annotations
import argparse, fcntl, json, os, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

QUEUE = Path(__file__).resolve().parents[3] / "wiki/logs/butler/queue.md"

# 匹配 - [ ] P1 create | 页面名 | 备注
RE_AVAIL = re.compile(r"^(\s*- \[ \] )(P[123] )(\S+) \| ([^|]+) \| (.*)$")
# 匹配 - [~] ... [instance@HH:MM:SS] 或 [instance@ISO]
RE_INPROG = re.compile(r"^(\s*- \[~\] )(P[123] )(\S+) \| ([^|]+) \| \[([^\]@]+)@([^\]]+)\] (.*)$")


def _now_tag(instance: str) -> str:
    t = datetime.now(timezone.utc).strftime("%H:%M:%S")
    return f"[{instance}@{t}]"


def _is_stale(tag_time: str, stale_minutes: int) -> bool:
    """tag_time 格式 HH:MM:SS（UTC）。同天内比较，跨天保守认为未超时。"""
    try:
        now = datetime.now(timezone.utc)
        hms = datetime.strptime(tag_time, "%H:%M:%S")
        claimed = now.replace(hour=hms.hour, minute=hms.minute, second=hms.second, microsecond=0)
        if claimed > now:  # 跨天
            return False
        return (now - claimed).total_seconds() > stale_minutes * 60
    except ValueError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--focus", default="all",
                    help="任务类型过滤：create / enrich / fix-links / stub / all（默认all）")
    ap.add_argument("--instance", default=f"inst{os.getpid()}", help="实例标识符")
    ap.add_argument("--stale-minutes", type=int, default=30, help="超时重抢时间（分钟）")
    args = ap.parse_args()

    focus = args.focus.lower()

    with open(QUEUE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        claimed = None

        for i, line in enumerate(lines):
            # 先尝试匹配 available
            m = RE_AVAIL.match(line)
            if m:
                _, priority, task_type, page, note = m.group(1), m.group(2).strip(), m.group(3), m.group(4).strip(), m.group(5).strip()
                if focus != "all" and task_type != focus:
                    continue
                tag = _now_tag(args.instance)
                lines[i] = f"- [~] {priority} {task_type} | {page} | {tag} {note}\n"
                claimed = {"page": page, "type": task_type, "priority": priority, "note": note}
                break

            # 再尝试匹配超时的 in-progress（可抢占）
            m2 = RE_INPROG.match(line)
            if m2:
                _, priority, task_type, page, inst, tag_time, note = (
                    m2.group(1), m2.group(2).strip(), m2.group(3),
                    m2.group(4).strip(), m2.group(5), m2.group(6), m2.group(7).strip()
                )
                if focus != "all" and task_type != focus:
                    continue
                if _is_stale(tag_time, args.stale_minutes):
                    tag = _now_tag(args.instance)
                    lines[i] = f"- [~] {priority} {task_type} | {page} | {tag} {note}\n"
                    claimed = {"page": page, "type": task_type, "priority": priority,
                               "note": note, "reclaimed_from": inst}
                    break

        if claimed:
            f.seek(0)
            f.writelines(lines)
            f.truncate()

    print(json.dumps(claimed or {"page": None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
