#!/usr/bin/env python3
"""
追加一条 action 记录到 wiki/logs/butler/actions.jsonl。

用法:
    python3 wiki/scripts/butler/record_action.py \
        --round 1 \
        --type create-page \
        --page 汪淼 \
        --result accept \
        --desc "从corpus三体I提取汪淼基本信息，创建人物页"
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--type', required=True, dest='action_type',
                    choices=['create-page', 'enrich-page', 'stub', 'fix-links',
                             'discover', 'publish', 'housekeeping'])
    ap.add_argument('--page', default='')
    ap.add_argument('--result', required=True, choices=['accept', 'fail', 'skip'])
    ap.add_argument('--desc', default='')
    ap.add_argument('--log', default='wiki/logs/butler/actions.jsonl')
    args = ap.parse_args()

    record = {
        'round':  args.round,
        'type':   args.action_type,
        'page':   args.page,
        'result': args.result,
        'desc':   args.desc,
        'ts':     datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"[logged] R{args.round} {args.action_type} | {args.page} | {args.result}")


if __name__ == '__main__':
    main()
