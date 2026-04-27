#!/usr/bin/env python3
"""
追加一条 action 记录到 wiki/logs/butler/actions.jsonl。

用法:
    python3 wiki/scripts/butler/record_action.py \
        --round 1 \
        --type create-page \
        --page 汪淼 \
        --result accept \
        --instance 幸存者 \
        --desc "从corpus三体I提取汪淼基本信息，创建人物页" \
        --reflect "语料命中率高，但缺少死亡时间相关段落"

--instance  命名实例（幸存者/破壁人/执剑人/广播员/监听员/统帅），可选
--reflect   每轮一句话观察，可选；W5 反思时扫此字段找规律
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
                    choices=['create-page', 'enrich-page', 'enrich-quality', 'stub',
                             'fix-links', 'add-quote', 'add-pn-citations', 'fix-alias',
                             'discover', 'publish', 'housekeeping', 'reflect-w5'])
    ap.add_argument('--page', default='')
    ap.add_argument('--result', required=True, choices=['accept', 'fail', 'skip'])
    ap.add_argument('--instance', default='', help='命名实例（幸存者/破壁人/统帅等）')
    ap.add_argument('--desc', default='')
    ap.add_argument('--reflect', default='', help='一句话观察（可选），供 W5 扫描找规律')
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
    if args.instance:
        record['instance'] = args.instance
    if args.reflect:
        record['reflect'] = args.reflect

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

    inst_tag = f" [{args.instance}]" if args.instance else ""
    print(f"[logged] R{args.round}{inst_tag} {args.action_type} | {args.page} | {args.result}")


if __name__ == '__main__':
    main()
