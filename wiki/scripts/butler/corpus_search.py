#!/usr/bin/env python3
"""
从三体三部曲原文中检索包含关键词的段落。

用法:
    python3 wiki/scripts/butler/corpus_search.py 叶文洁 --max 10
    python3 wiki/scripts/butler/corpus_search.py 黑暗森林 --book 2 --max 5
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CORPUS_DIR = Path('corpus')
BOOKS = {
    '1': '三体I：地球往事.txt',
    '2': '三体II：黑暗森林.txt',
    '3': '三体III：死神永生.txt',
}


def search_corpus(keyword: str, book: str | None, max_results: int, context: int) -> None:
    if book:
        files = [CORPUS_DIR / BOOKS[book]] if book in BOOKS else []
    else:
        files = [CORPUS_DIR / name for name in BOOKS.values()]

    found = 0
    for fpath in files:
        if not fpath.exists():
            print(f'[warn] 文件不存在: {fpath}', file=sys.stderr)
            continue

        text = fpath.read_text(encoding='gb18030', errors='replace')
        lines = text.split('\n')
        book_label = fpath.stem.split('：')[0] if '：' in fpath.stem else fpath.stem

        for i, line in enumerate(lines):
            if keyword in line:
                lo = max(0, i - context)
                hi = min(len(lines) - 1, i + context)
                snippet = '\n'.join(lines[lo:hi+1]).strip()
                print(f'--- [{book_label}] 行 {i+1} ---')
                # 高亮关键词（终端 ANSI，grep 风格）
                highlighted = snippet.replace(keyword, f'\033[1;33m{keyword}\033[0m')
                print(highlighted)
                print()
                found += 1
                if found >= max_results:
                    print(f'[截断] 已显示 {max_results} 条结果，使用 --max 增加上限')
                    return

    if found == 0:
        print(f'[未找到] "{keyword}" 在语料库中无匹配')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('keyword', help='搜索关键词')
    ap.add_argument('--book', choices=['1', '2', '3'], default=None, help='限定书册 (1/2/3)')
    ap.add_argument('--max', type=int, default=8, dest='max_results', help='最多显示条数')
    ap.add_argument('--context', type=int, default=3, help='上下文行数')
    args = ap.parse_args()

    search_corpus(args.keyword, args.book, args.max_results, args.context)


if __name__ == '__main__':
    main()
