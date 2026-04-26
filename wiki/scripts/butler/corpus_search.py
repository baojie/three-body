#!/usr/bin/env python3
"""
从三体三部曲原文中检索包含关键词的段落，并输出 PN 引文编号。

用法:
    python3 wiki/scripts/butler/corpus_search.py 叶文洁 --max 10
    python3 wiki/scripts/butler/corpus_search.py 黑暗森林 --book 2 --max 5

搜索 wiki/public/pages/ 中已标注 PN 的章节页面，每条结果直接给出
可用于文章引用的 PN 格式，如 （1-02-015）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent          # wiki/
PAGES_DIR = ROOT / 'public' / 'pages'

BOOK_FILTER = {'1': '三体I', '2': '三体II', '3': '三体III'}

# 匹配段落 PN 标签：[1-02-001]
RE_PN = re.compile(r'^\[(\d-\d{2}-\d{3})\]\s*(.*)', re.DOTALL)


def search_pages(keyword: str, book: str | None, max_results: int, context_chars: int) -> None:
    book_prefix = BOOK_FILTER.get(book) if book else None

    # 只搜索 chapter 类型页面
    chapter_pages = sorted(
        [p for p in PAGES_DIR.glob('*.md') if p.stem.startswith(('三体I-', '三体II-', '三体III-'))],
        key=lambda p: p.stem
    )
    if book_prefix:
        chapter_pages = [p for p in chapter_pages if p.stem.startswith(book_prefix)]

    found = 0
    for page_path in chapter_pages:
        text = page_path.read_text(encoding='utf-8')
        # 跳过 frontmatter
        body = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)

        for line in body.splitlines():
            m = RE_PN.match(line.strip())
            if not m:
                continue
            pn, para_text = m.group(1), m.group(2)
            if keyword not in para_text:
                continue

            # 截取上下文（字符级别）
            idx = para_text.index(keyword)
            lo = max(0, idx - context_chars)
            hi = min(len(para_text), idx + len(keyword) + context_chars)
            snippet = ('…' if lo > 0 else '') + para_text[lo:hi] + ('…' if hi < len(para_text) else '')

            # 高亮关键词（ANSI）
            highlighted = snippet.replace(keyword, f'\033[1;33m{keyword}\033[0m')
            print(f'[{pn}] {highlighted}')
            print(f'       → 引用格式：（{pn}）')
            print()
            found += 1
            if found >= max_results:
                print(f'[截断] 已显示 {max_results} 条，使用 --max 增加上限')
                return

    if found == 0:
        print(f'[未找到] "{keyword}" 在章节原文中无匹配')


def main():
    ap = argparse.ArgumentParser(description='搜索三体原文并输出 PN 引文')
    ap.add_argument('keyword', help='搜索关键词')
    ap.add_argument('--book', choices=['1', '2', '3'], default=None, help='限定书册 (1/2/3)')
    ap.add_argument('--max', type=int, default=8, dest='max_results', help='最多显示条数')
    ap.add_argument('--context', type=int, default=80, help='关键词前后字符数（默认80）')
    args = ap.parse_args()

    search_pages(args.keyword, args.book, args.max_results, args.context)


if __name__ == '__main__':
    main()
