#!/usr/bin/env python3
"""
扫描 wiki/public/pages/ 中所有 [[wikilink]]，找出尚无对应页面的"wanted pages"。

用法:
    python3 wiki/scripts/butler/discover_wanted.py [--top N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

WIKILINK_RE = re.compile(r'\[\[([^\[\]|]+?)(?:\|[^\[\]]+?)?\]\]')
FRONTMATTER_RE = re.compile(r'\A---\s*\n.*?\n---\s*\n', re.DOTALL)

import yaml

def load_page_ids(pages_root: Path) -> set[str]:
    ids = set()
    label_to_id: dict[str, str] = {}
    for f in pages_root.rglob('*.md'):
        pid = str(f.relative_to(pages_root).with_suffix(''))
        ids.add(pid)
        text = f.read_text(encoding='utf-8')
        m = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
        if m:
            try:
                front = yaml.safe_load(m.group(1)) or {}
                label = front.get('label', '')
                if label:
                    label_to_id[label] = pid
                    ids.add(label)
                for alias in (front.get('aliases') or []):
                    if isinstance(alias, str):
                        ids.add(alias)
            except Exception:
                pass
    return ids


def scan_wanted(pages_root: Path, top: int) -> list[tuple[str, int]]:
    existing = load_page_ids(pages_root)
    wanted: Counter = Counter()
    for f in pages_root.rglob('*.md'):
        text = f.read_text(encoding='utf-8')
        body = FRONTMATTER_RE.sub('', text)
        for m in WIKILINK_RE.finditer(body):
            target = m.group(1).strip()
            if target not in existing:
                wanted[target] += 1

    return wanted.most_common(top)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', default='wiki/public/pages', help='pages directory')
    ap.add_argument('--top', type=int, default=30, help='show top N wanted pages')
    ap.add_argument('--json', action='store_true', help='output JSON')
    args = ap.parse_args()

    root = Path(args.pages)
    if not root.is_dir():
        print(f'[error] {root} is not a directory', file=sys.stderr)
        sys.exit(1)

    results = scan_wanted(root, args.top)

    if args.json:
        print(json.dumps([{'page': p, 'count': c} for p, c in results], ensure_ascii=False, indent=2))
    else:
        if not results:
            print('无 wanted pages（所有链接均已解析）')
            return
        print(f'Top {len(results)} wanted pages（按引用次数排）：\n')
        for page, count in results:
            print(f'  {count:3d}x  {page}')


if __name__ == '__main__':
    main()
