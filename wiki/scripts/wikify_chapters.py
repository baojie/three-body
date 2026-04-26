#!/usr/bin/env python3
"""
为已导入的章节页面添加实体 wikilink。

规则：
- 每个实体在每章首次出现时链接，后续出现不重复链接
- 使用 [[page_id]] 或 [[page_id|显示文字]]（别名不等于 id 时）
- 不在 [[...]] / [PN] / （PN） / 标题行内二次处理
- 只处理 type=chapter 的页面，不修改其他页面

用法：
    python3 wiki/scripts/wikify_chapters.py
    python3 wiki/scripts/wikify_chapters.py --dry-run   # 只打印，不写文件
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / 'public' / 'pages'
PAGES_JSON = ROOT / 'public' / 'pages.json'


# ── 构建别名映射 ──────────────────────────────────────────────────────────────

def build_alias_map(pages: dict) -> list[tuple[str, str, str]]:
    """
    返回 [(alias, page_id, display), ...] 按 alias 长度降序排列。
    display = alias（即链接的显示文字）。
    """
    entries = []
    for pid, meta in pages.items():
        if meta.get('type') == 'chapter':
            continue
        label = meta.get('label', pid)
        aliases = meta.get('aliases', [label])
        seen = set()
        for alias in aliases:
            if not isinstance(alias, str):
                continue
            # 跳过英文别名（避免误链接英文片段）
            if alias.isascii():
                continue
            if alias in seen:
                continue
            seen.add(alias)
            entries.append((alias, pid, alias))
    # 长别名优先，避免短别名误匹配长实体的一部分
    entries.sort(key=lambda e: len(e[0]), reverse=True)
    return entries


# ── 单段落链接化 ──────────────────────────────────────────────────────────────

# 匹配已有 wikilink [[...]] 或 PN 标签 [B-CC-PPP] 或 PN 引文 （B-CC-PPP）
RE_SKIP = re.compile(r'\[\[[^\]]*\]\]|\[\d-\d{2}-\d{3}\]|（\d-\d{2}-\d{3}）')


def wikify_paragraph(text: str, alias_map: list[tuple[str, str, str]],
                     linked: set[str]) -> str:
    """
    对一个段落文本，将未链接的实体首次出现替换为 [[link]]。
    linked: 本章已链接的 page_id 集合（in-place 更新）。
    """
    # 找出所有"保护区间"（不应被替换的范围）
    protected = []
    for m in RE_SKIP.finditer(text):
        protected.append((m.start(), m.end()))

    def in_protected(start: int, end: int) -> bool:
        return any(ps <= start < pe or ps < end <= pe for ps, pe in protected)

    result = []
    pos = 0
    while pos < len(text):
        matched = False
        for alias, pid, display in alias_map:
            if pid in linked:
                continue  # 本章已链接过此实体
            if text[pos:pos + len(alias)] == alias:
                if not in_protected(pos, pos + len(alias)):
                    # 生成 wikilink
                    if display == pid:
                        link = f'[[{pid}]]'
                    else:
                        link = f'[[{pid}|{display}]]'
                    result.append(link)
                    linked.add(pid)
                    pos += len(alias)
                    matched = True
                    # 更新保护区以覆盖新插入的 link
                    link_start = sum(len(s) for s in result) - len(link)
                    protected.append((pos - len(alias), pos))
                    break
        if not matched:
            result.append(text[pos])
            pos += 1

    return ''.join(result)


# ── 处理单个章节文件 ──────────────────────────────────────────────────────────

RE_FRONTMATTER = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
RE_PARA_LINE = re.compile(r'^(\[\d-\d{2}-\d{3}\]\s*)(.*)', re.DOTALL)


def process_chapter(path: Path, alias_map: list, dry_run: bool) -> int:
    """返回本章新增的 wikilink 数量。"""
    text = path.read_text(encoding='utf-8')

    fm_match = RE_FRONTMATTER.match(text)
    if not fm_match:
        return 0
    fm_end = fm_match.end()
    frontmatter = text[:fm_end]
    body = text[fm_end:]

    linked: set[str] = set()  # 本章已链接的实体
    new_links = 0
    lines_out = []

    for line in body.splitlines(keepends=True):
        stripped = line.rstrip('\n')
        # 标题行：不做链接化（但仍统计已见实体可选）
        if stripped.startswith('#'):
            lines_out.append(line)
            continue
        # 段落行（以 PN 标签开头）
        m = RE_PARA_LINE.match(stripped)
        if m:
            pn_tag = m.group(1)
            para_text = m.group(2)
            before_count = len(linked)
            new_text = wikify_paragraph(para_text, alias_map, linked)
            new_links += len(linked) - before_count
            lines_out.append(pn_tag + new_text + '\n')
        else:
            lines_out.append(line)

    if new_links == 0:
        return 0

    new_body = ''.join(lines_out)
    new_content = frontmatter + new_body

    if not dry_run:
        path.write_text(new_content, encoding='utf-8')

    return new_links


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只打印，不写文件')
    ap.add_argument('--book', choices=['1', '2', '3'], default=None, help='只处理指定书册')
    args = ap.parse_args()

    with open(PAGES_JSON, encoding='utf-8') as f:
        pages = json.load(f)['pages']

    alias_map = build_alias_map(pages)
    print(f'实体别名表：{len(alias_map)} 条（{len(set(pid for _, pid, _ in alias_map))} 个实体）')
    for alias, pid, _ in alias_map:
        print(f'  "{alias}" → {pid}')
    print()

    book_prefix = {'1': '三体I-', '2': '三体II-', '3': '三体III-'}.get(args.book, '')

    chapter_files = sorted(
        [p for p in PAGES_DIR.glob('*.md')
         if p.stem.startswith(('三体I-', '三体II-', '三体III-'))
         and (not book_prefix or p.stem.startswith(book_prefix))],
        key=lambda p: p.stem
    )

    total_links = 0
    changed = 0
    for path in chapter_files:
        n = process_chapter(path, alias_map, args.dry_run)
        if n > 0:
            changed += 1
            total_links += n
            print(f'  {"[dry]" if args.dry_run else "[ok]"} {path.stem}: +{n} 链接')

    action = '（dry-run，未写入）' if args.dry_run else '已写入'
    print(f'\n共 {changed}/{len(chapter_files)} 章有变更，新增 {total_links} 个 wikilink {action}')


if __name__ == '__main__':
    main()
