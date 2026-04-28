#!/usr/bin/env python3
"""
Generate category listing pages for each page type.
Output: wiki/public/pages/分类·<type>.md
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
PAGES_JSON = BASE / "public" / "pages.json"
PAGES_DIR = BASE / "public" / "pages"

# Human-readable names and descriptions for each type
TYPE_META = {
    "person": {
        "label": "人物",
        "slug": "人物",
        "description": "《三体》三部曲中出现的所有人物角色",
        "tags": ["分类", "人物"],
    },
    "concept": {
        "label": "概念",
        "slug": "概念",
        "description": "《三体》三部曲中的核心概念、理论与思想",
        "tags": ["分类", "概念"],
    },
    "technology": {
        "label": "科技",
        "slug": "科技",
        "description": "《三体》三部曲中出现的科技设备、工程与技术手段",
        "tags": ["分类", "科技"],
    },
    "event": {
        "label": "事件",
        "slug": "事件",
        "description": "《三体》三部曲中的重大历史事件",
        "tags": ["分类", "事件"],
    },
    "place": {
        "label": "地点",
        "slug": "地点",
        "description": "《三体》三部曲中出现的重要地点与空间",
        "tags": ["分类", "地点"],
    },
    "organization": {
        "label": "组织",
        "slug": "组织",
        "description": "《三体》三部曲中出现的组织、机构与团体",
        "tags": ["分类", "组织"],
    },
    "civilization": {
        "label": "文明",
        "slug": "文明",
        "description": "《三体》三部曲中出现的各类宇宙文明",
        "tags": ["分类", "文明"],
    },
    "era": {
        "label": "历史纪元",
        "slug": "历史纪元",
        "description": "《三体》三部曲中的历史纪元与时代划分",
        "tags": ["分类", "纪元"],
    },
    "weapon": {
        "label": "武器",
        "slug": "武器",
        "description": "《三体》三部曲中出现的武器与打击手段",
        "tags": ["分类", "武器"],
    },
    "theory": {
        "label": "理论",
        "slug": "理论",
        "description": "《三体》三部曲中的科学理论与宇宙法则",
        "tags": ["分类", "理论"],
    },
}

BOOK_ORDER = {"三体I": 1, "三体II": 2, "三体III": 3}
QUALITY_ORDER = {"featured": 0, "standard": 1, "basic": 2, "stub": 3, "unknown": 4}


def sort_key(item):
    slug, info = item
    books = info.get("books") or []
    min_book = min((BOOK_ORDER.get(b, 99) for b in books), default=99)
    quality = QUALITY_ORDER.get(info.get("quality", "unknown"), 4)
    return (min_book, quality, slug)


def load_books_from_md(slug):
    """Read books field from the Markdown frontmatter of a page."""
    import re
    import yaml as _yaml
    md_path = PAGES_DIR / f"{slug}.md"
    if not md_path.exists():
        return []
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return []
    try:
        front = _yaml.safe_load(m.group(1)) or {}
        return front.get("books") or []
    except Exception:
        return []


def build_page_for_type(type_key, meta, pages):
    items = [(k, v) for k, v in pages.items() if v.get("type") == type_key]
    items.sort(key=sort_key)

    label = meta["label"]
    slug = meta["slug"]
    desc = meta["description"]
    tags = meta["tags"]

    # Group by first/primary book (read from Markdown frontmatter)
    groups = {"三体I": [], "三体II": [], "三体III": [], "通用": []}
    for k, v in items:
        books = load_books_from_md(k)
        if not books:
            groups["通用"].append((k, v))
        else:
            # Primary book = lowest index in BOOK_ORDER
            primary = min(books, key=lambda b: BOOK_ORDER.get(b, 99))
            if primary in groups:
                groups[primary].append((k, v))
            else:
                groups["通用"].append((k, v))

    lines = [
        "---",
        f"id: 分类·{slug}",
        f"type: list",
        f"label: {label}",
        f"aliases: [{label}, 分类·{slug}]",
        f"tags: {tags}",
        f'description: {desc}',
        f"books: [三体I, 三体II, 三体III]",
        "quality: standard",
        "---",
        f"# {label}",
        "",
        f"{desc}。共 **{len(items)}** 个词条。",
        "",
    ]

    book_labels = {
        "三体I": "《地球往事》",
        "三体II": "《黑暗森林》",
        "三体III": "《死神永生》",
        "通用": "跨册 / 通用",
    }

    for book_key in ["三体I", "三体II", "三体III", "通用"]:
        group = groups[book_key]
        if not group:
            continue
        lines.append(f"## {book_labels[book_key]}（{len(group)} 条）")
        lines.append("")
        for k, v in group:
            entry_label = v.get("label", k)
            entry_desc = v.get("description", "")
            quality = v.get("quality", "")
            quality_mark = " ★" if quality == "featured" else ""
            if entry_desc:
                lines.append(f"- [[{k}|{entry_label}]]{quality_mark} — {entry_desc}")
            else:
                lines.append(f"- [[{k}|{entry_label}]]{quality_mark}")
        lines.append("")

    lines.append("## 相关词条")
    lines.append("")
    for other_key, other_meta in TYPE_META.items():
        if other_key != type_key:
            lines.append(f"- [[分类·{other_meta['slug']}]]")
    lines.append("")

    return "\n".join(lines)


def main():
    data = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    pages = data["pages"]

    created = []
    for type_key, meta in TYPE_META.items():
        content = build_page_for_type(type_key, meta, pages)
        slug = meta["slug"]
        out_path = PAGES_DIR / f"分类·{slug}.md"
        out_path.write_text(content, encoding="utf-8")
        count = len([k for k, v in pages.items() if v.get("type") == type_key])
        print(f"  {out_path.name} ({count} entries)")
        created.append(str(out_path))

    print(f"\nGenerated {len(created)} category pages.")
    return created


if __name__ == "__main__":
    main()
