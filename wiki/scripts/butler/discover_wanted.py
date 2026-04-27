#!/usr/bin/env python3
"""
发现待创建页面：优先找 broken wikilinks，若无则从语料频率中发现。

两阶段策略：
  Phase 1: 扫描所有 [[wikilink]] 找无对应页的 broken links（引用驱动）
  Phase 2: 若 Phase 1 为空，调用 discover_corpus.py 按语料频率发现（语料驱动）

用法:
    python3 wiki/scripts/butler/discover_wanted.py [--top N]
    python3 wiki/scripts/butler/discover_wanted.py --json
    python3 wiki/scripts/butler/discover_wanted.py --corpus-only   # 只做语料扫描
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
PAGES_DIR = ROOT / "public" / "pages"

WIKILINK_RE = re.compile(r'\[\[([^\[\]|]+?)(?:\|[^\[\]]+?)?\]\]')
FRONTMATTER_RE = re.compile(r'\A---\s*\n.*?\n---\s*\n', re.DOTALL)


def load_page_ids(pages_root: Path) -> set[str]:
    ids: set[str] = set()
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
                    ids.add(label)
                for alias in (front.get('aliases') or []):
                    if isinstance(alias, str):
                        ids.add(alias)
            except Exception:
                pass
    return ids


def scan_broken_links(pages_root: Path, top: int) -> list[tuple[str, int]]:
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


def scan_corpus_candidates(pages_root: Path, top: int, min_freq: int = 3) -> list[dict]:
    try:
        from discover_corpus import discover_candidates
        pages_json = pages_root.parent / "pages.json"
        return discover_candidates(pages_root, pages_json, top, min_freq)
    except ImportError:
        return []


def main():
    ap = argparse.ArgumentParser(description='发现待创建页面（broken links + 语料频率）')
    ap.add_argument('--pages', default=str(PAGES_DIR), help='pages directory')
    ap.add_argument('--top', type=int, default=30, help='show top N results')
    ap.add_argument('--min-freq', type=int, default=3, help='corpus scan 最小频率（默认3）')
    ap.add_argument('--json', action='store_true', help='output JSON')
    ap.add_argument('--corpus-only', action='store_true', help='只做语料扫描，跳过 broken-link 检查')
    args = ap.parse_args()

    root = Path(args.pages)
    if not root.is_dir():
        print(f'[error] {root} is not a directory', file=sys.stderr)
        sys.exit(1)

    broken: list[tuple[str, int]] = []
    if not args.corpus_only:
        broken = scan_broken_links(root, args.top)

    if broken:
        # Phase 1：有 broken links，优先返回
        if args.json:
            print(json.dumps(
                [{'page': p, 'count': c, 'source': 'broken-link'} for p, c in broken],
                ensure_ascii=False, indent=2
            ))
        else:
            print(f'Top {len(broken)} broken wikilinks（按引用次数排）：\n')
            for page, count in broken:
                print(f'  {count:3d}x  {page}')
        return

    # Phase 2：无 broken links，扫描语料
    corpus = scan_corpus_candidates(root, args.top, args.min_freq)

    if args.json:
        print(json.dumps(corpus, ensure_ascii=False, indent=2))
        return

    if not corpus:
        print('无候选页面（broken links 已全部解析，语料频率扫描也无新结果）')
        return

    print(f'语料频率扫描发现 {len(corpus)} 个候选（无 broken links，改用语料模式）：\n')
    src_label = {'ships': '舰船', 'suffixed': '后缀型', 'persons': '人名', 'quoted': '引号型'}
    for c in corpus:
        sl = src_label.get(c.get('source', ''), c.get('source', '?'))
        print(f"  {c['freq']:3d}x  [{sl}]  {c['name']}")


if __name__ == '__main__':
    main()
