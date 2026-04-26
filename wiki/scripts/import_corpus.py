#!/usr/bin/env python3
"""
Import Three-Body trilogy corpus into wiki pages with PN paragraph numbering.

PN format: B-CC-PPP
  B   = book number (1/2/3)
  CC  = chapter/section sequence number within book (zero-padded 2 digits)
  PPP = paragraph number within chapter (zero-padded 3 digits)

Example: 1-02-001 = Book I, section 2 (疯狂年代), paragraph 1
"""

import re
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT.parent / "corpus"
PAGES_DIR = ROOT / "public" / "pages"
PAGES_JSON = ROOT / "public" / "pages.json"
UTF8_DIR = CORPUS / "utf8"

PAGES_DIR.mkdir(parents=True, exist_ok=True)
UTF8_DIR.mkdir(parents=True, exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def read_gbk(path):
    with open(path, "rb") as f:
        raw = f.read()
    # Try gb18030 first (superset of gbk/gb2312)
    for enc in ("gb18030", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode {path}")


def normalize(text):
    """Normalize line endings and strip trailing whitespace."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [l.rstrip() for l in text.splitlines()]
    return "\n".join(lines)


def extract_paragraphs(text):
    """Split text into non-empty paragraphs, stripping leading ideographic spaces."""
    paras = []
    for line in text.splitlines():
        line = line.strip()
        # Strip leading ideographic spaces (　= U+3000)
        line = line.lstrip("　").strip()
        if line:
            paras.append(line)
    return paras


def number_paragraphs(paragraphs, book, chapter_seq):
    """Add [B-CC-PPP] PN tags to each paragraph."""
    result = []
    for i, para in enumerate(paragraphs, 1):
        pn = f"{book}-{chapter_seq:02d}-{i:03d}"
        result.append(f"[{pn}] {para}")
    return result


def make_frontmatter(fields):
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(repr(x) for x in v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


# ── Book I splitter ───────────────────────────────────────────────────────────

def split_book1(text):
    """
    Book I uses numbered sections: '1.疯狂年代', '2.寂静的春天', ...
    Returns list of (seq, title, body_text) tuples.
    """
    lines = text.splitlines()
    heading_re = re.compile(r"^(\d+)[\.．]\s*(.+)$")

    # Find special sections first
    sections = []

    # Locate 前言
    preface_start = None
    for i, l in enumerate(lines):
        if l.strip() == "前言":
            preface_start = i
            break

    # Collect numbered sections (cap at 100 to avoid matching years like 1989)
    numbered = []
    for i, l in enumerate(lines):
        m = heading_re.match(l.strip())
        if m and 1 <= int(m.group(1)) <= 100 and len(l.strip()) < 30:
            numbered.append((i, int(m.group(1)), m.group(2).strip()))

    # 后记
    postscript_start = None
    for i, l in enumerate(lines):
        if l.strip() == "后记":
            postscript_start = i

    # Build boundary list: (line_start, seq, title)
    # Use sequential numbering: 前言=1, sections 2..N+1, 后记=N+2
    boundaries = []
    seq_offset = 1
    if preface_start is not None:
        boundaries.append((preface_start, seq_offset, "前言"))
        seq_offset += 1
    for line_i, num, title in numbered:
        boundaries.append((line_i, seq_offset, title))
        seq_offset += 1
    if postscript_start is not None:
        boundaries.append((postscript_start, seq_offset, "后记"))

    # Extract body for each section
    for idx, (start, seq, title) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        body_lines = lines[start + 1:end]
        body = "\n".join(body_lines)
        sections.append((seq, title, body))

    return sections


# ── Book II splitter ──────────────────────────────────────────────────────────

def split_book2(text):
    """
    Book II: 3 parts (上/中/下部), each with 第N节.
    Returns list of (seq, title, body_text).
    Global seq across whole book.
    """
    lines = text.splitlines()
    part_re = re.compile(r"^(上部|中部|下部)\s+(.+)$")
    section_re = re.compile(r"^第(\d+)节$")

    # Map part names to numbers
    part_map = {"上部": 1, "中部": 2, "下部": 3}
    part_labels = {"上部": "上", "中部": "中", "下部": "下"}

    sections = []
    current_part = None
    current_part_label = ""
    global_seq = 0

    # First find 前言 and 序章
    special_starts = []
    for i, l in enumerate(lines):
        s = l.strip()
        if s in ("前言", "序章"):
            special_starts.append((i, s))

    # Find all structural boundaries
    boundaries = []
    for i, l in enumerate(lines):
        s = l.strip()
        pm = part_re.match(s)
        sm = section_re.match(s)
        if pm:
            boundaries.append((i, "part", pm.group(1), pm.group(1) + " " + pm.group(2)))
        elif sm:
            boundaries.append((i, "section", int(sm.group(1)), ""))
        elif s in ("前言", "序章"):
            boundaries.append((i, "special", s, s))
        elif s == "书评":
            boundaries.append((i, "end", "书评", "书评"))
            break

    # Build sections from boundaries
    global_seq = 0
    result = []
    for idx, entry in enumerate(boundaries):
        if entry[1] in ("part", "end"):
            continue
        line_start = entry[0]
        line_end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        body = "\n".join(lines[line_start + 1:line_end])

        if entry[1] == "special":
            global_seq += 1
            result.append((global_seq, entry[2], body))
        elif entry[1] == "section":
            # Find current part context
            part_name = ""
            for j in range(idx, -1, -1):
                if boundaries[j][1] == "part":
                    part_name = part_labels[boundaries[j][2]]
                    break
            global_seq += 1
            section_num = entry[2]
            title = f"{part_name}部第{section_num}节"
            result.append((global_seq, title, body))

    return result


# ── Book III splitter ─────────────────────────────────────────────────────────

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
          "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
          "十六": 16, "十七": 17}


def split_book3(text):
    """
    Book III: 6 parts (第一部~第六部), each with 第X章.
    """
    lines = text.splitlines()
    part_re = re.compile(r"^第([一二三四五六七八九十]+)部$")
    chapter_re = re.compile(r"^第([一二三四五六七八九十]+)章$")

    boundaries = []
    for i, l in enumerate(lines):
        s = l.strip()
        pm = part_re.match(s)
        cm = chapter_re.match(s)
        if s in ("前言", '写在"基石"之前', "序", "纪年对照表", "尾声"):
            boundaries.append((i, "special", s))
        elif pm:
            boundaries.append((i, "part", CN_NUM.get(pm.group(1), 0)))
        elif cm:
            boundaries.append((i, "chapter", CN_NUM.get(cm.group(1), 0)))

    result = []
    global_seq = 0
    current_part = 0

    for idx, entry in enumerate(boundaries):
        if entry[1] == "part":
            current_part = entry[2]
            continue

        line_start = entry[0]
        line_end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        # Skip part headers themselves
        while idx + 1 < len(boundaries) and boundaries[idx + 1][1] == "part":
            line_end = boundaries[idx + 1][0]
            break
        body = "\n".join(lines[line_start + 1:line_end])

        global_seq += 1
        if entry[1] == "special":
            result.append((global_seq, entry[2], body, 0, 0))
        elif entry[1] == "chapter":
            # CN_NUM keys: 一~十七; reverse lookup
            cn_rev = {v: k for k, v in CN_NUM.items()}
            part_cn = cn_rev.get(current_part, str(current_part))
            chap_cn = cn_rev.get(entry[2], str(entry[2]))
            title = f"第{part_cn}部·第{chap_cn}章"
            result.append((global_seq, title, body, current_part, entry[2]))

    return result


# ── Page writer ───────────────────────────────────────────────────────────────

def write_page(pages_dir, filename, frontmatter_dict, paragraphs_with_pn):
    fm = make_frontmatter(frontmatter_dict)
    title = frontmatter_dict.get("label", frontmatter_dict.get("id", ""))
    body = "\n\n".join(paragraphs_with_pn)
    content = f"{fm}\n\n# {title}\n\n{body}\n"
    path = pages_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def process_book1(text, pages_dir):
    sections = split_book1(text)
    entries = {}

    for seq, title, body in sections:
        paragraphs = extract_paragraphs(body)
        if not paragraphs:
            continue

        pn_paragraphs = number_paragraphs(paragraphs, 1, seq)
        page_id = f"三体I-{seq:02d}-{title}"
        filename = f"{page_id}.md"

        fm = {
            "id": page_id,
            "type": "chapter",
            "label": title,
            "book": "三体I",
            "book_seq": seq,
            "tags": ["原文", "三体I"],
            "pn_prefix": f"1-{seq:02d}",
        }
        write_page(pages_dir, filename, fm, pn_paragraphs)

        entries[page_id] = {
            "type": "chapter",
            "label": title,
            "book": "三体I",
            "book_seq": seq,
            "tags": ["原文", "三体I"],
            "pn_prefix": f"1-{seq:02d}",
            "path": f"pages/{filename}",
            "description": f"三体I 第{seq}节：{title}",
        }
        print(f"  Book I [{seq:02d}] {title} — {len(paragraphs)} paragraphs")

    return entries


def process_book2(text, pages_dir):
    sections = split_book2(text)
    entries = {}

    for seq, title, body in sections:
        paragraphs = extract_paragraphs(body)
        if not paragraphs:
            continue

        pn_paragraphs = number_paragraphs(paragraphs, 2, seq)
        page_id = f"三体II-{seq:02d}-{title}"
        filename = f"{page_id}.md"

        fm = {
            "id": page_id,
            "type": "chapter",
            "label": title,
            "book": "三体II",
            "book_seq": seq,
            "tags": ["原文", "三体II"],
            "pn_prefix": f"2-{seq:02d}",
        }
        write_page(pages_dir, filename, fm, pn_paragraphs)

        entries[page_id] = {
            "type": "chapter",
            "label": title,
            "book": "三体II",
            "book_seq": seq,
            "tags": ["原文", "三体II"],
            "pn_prefix": f"2-{seq:02d}",
            "path": f"pages/{filename}",
            "description": f"三体II {title}",
        }
        print(f"  Book II [{seq:02d}] {title} — {len(paragraphs)} paragraphs")

    return entries


def process_book3(text, pages_dir):
    sections = split_book3(text)
    entries = {}

    for item in sections:
        seq, title, body = item[0], item[1], item[2]
        part_num = item[3] if len(item) > 3 else 0

        paragraphs = extract_paragraphs(body)
        if not paragraphs:
            continue

        pn_paragraphs = number_paragraphs(paragraphs, 3, seq)
        page_id = f"三体III-{seq:02d}-{title}"
        filename = f"{page_id}.md"

        tags = ["原文", "三体III"]
        if part_num:
            tags.append(f"第{['', '一', '二', '三', '四', '五', '六'][part_num]}部")

        fm = {
            "id": page_id,
            "type": "chapter",
            "label": title,
            "book": "三体III",
            "book_seq": seq,
            "tags": tags,
            "pn_prefix": f"3-{seq:02d}",
        }
        write_page(pages_dir, filename, fm, pn_paragraphs)

        entries[page_id] = {
            "type": "chapter",
            "label": title,
            "book": "三体III",
            "book_seq": seq,
            "tags": tags,
            "pn_prefix": f"3-{seq:02d}",
            "path": f"pages/{filename}",
            "description": f"三体III {title}",
        }
        print(f"  Book III [{seq:02d}] {title} — {len(paragraphs)} paragraphs")

    return entries


def main():
    print("Converting GBK → UTF-8...")
    book_files = {
        1: "三体I：地球往事.txt",
        2: "三体II：黑暗森林.txt",
        3: "三体III：死神永生.txt",
    }
    texts = {}
    for book_num, fname in book_files.items():
        path = CORPUS / fname
        text = normalize(read_gbk(path))
        utf8_path = UTF8_DIR / fname
        utf8_path.write_text(text, encoding="utf-8")
        texts[book_num] = text
        print(f"  {fname} → utf8/ ({len(text):,} chars)")

    print("\nSplitting and importing chapters...")
    all_entries = {}
    all_entries.update(process_book1(texts[1], PAGES_DIR))
    all_entries.update(process_book2(texts[2], PAGES_DIR))
    all_entries.update(process_book3(texts[3], PAGES_DIR))

    print(f"\nUpdating pages.json ({len(all_entries)} chapter entries)...")
    pages_json_path = PAGES_JSON
    with open(pages_json_path, encoding="utf-8") as f:
        pages_data = json.load(f)

    # Remove old chapter entries and add new ones
    existing = {k: v for k, v in pages_data["pages"].items()
                if v.get("type") != "chapter"}
    existing.update(all_entries)
    pages_data["pages"] = existing

    with open(pages_json_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, ensure_ascii=False, indent=2)

    print(f"\nGenerating data/chapter_map.json...")
    chapter_map = {
        meta["pn_prefix"]: pid
        for pid, meta in existing.items()
        if meta.get("type") == "chapter" and "pn_prefix" in meta
    }
    data_dir = ROOT / "public" / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "chapter_map.json", "w", encoding="utf-8") as f:
        json.dump(chapter_map, f, ensure_ascii=False, indent=2)
    print(f"  {len(chapter_map)} entries → data/chapter_map.json")

    print(f"\nDone. Total pages: {len(existing)}")


if __name__ == "__main__":
    main()
