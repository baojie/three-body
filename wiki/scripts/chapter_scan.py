#!/usr/bin/env python3
"""
chapter_scan.py — 逐章扫描工具

用法：
  python3 wiki/scripts/chapter_scan.py status
  python3 wiki/scripts/chapter_scan.py next
  python3 wiki/scripts/chapter_scan.py scan [--chapter 三体I-05]
  python3 wiki/scripts/chapter_scan.py advance
  python3 wiki/scripts/chapter_scan.py reset
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PAGES_DIR = Path("wiki/public/pages")
PAGES_JSON = Path("wiki/public/pages.json")
PROGRESS_FILE = Path("wiki/logs/chapter-scan/progress.json")
CORPUS_SEARCH = Path("wiki/scripts/butler/corpus_search.py")

# ── Chapter ordering ─────────────────────────────────────────────────────────

def get_all_chapters():
    """Return sorted list of (book_num, chap_num, filename_stem) for all chapter pages."""
    chapters = []
    for f in PAGES_DIR.iterdir():
        m = re.match(r'^(三体(I+))-(\d+)-(.+)\.md$', f.name)
        if m:
            book = m.group(1)
            book_num = len(m.group(2))  # I→1, II→2, III→3
            chap_num = int(m.group(3))
            stem = f.stem  # e.g. "三体I-05-三十八年后"
            chapters.append((book_num, chap_num, book, stem))
    chapters.sort()
    return chapters

def get_chapter_key(stem):
    """Extract sortable key from stem like '三体I-05-...'"""
    m = re.match(r'^(三体(I+))-(\d+)', stem)
    if m:
        return (len(m.group(2)), int(m.group(3)))
    return (99, 99)

# ── Progress state ────────────────────────────────────────────────────────────

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {
        "next_index": 0,
        "total_chapters": 0,
        "chapters_scanned": [],
        "stats": {"total_missing_found": 0, "total_added_to_queue": 0},
    }

def save_progress(data):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Wikilink extraction ───────────────────────────────────────────────────────

def extract_wikilinks(md_text):
    """Return set of link targets (the part before |, or the whole thing)."""
    targets = set()
    for m in re.finditer(r'\[\[([^\]]+)\]\]', md_text):
        inner = m.group(1)
        # [[target|display]] → target;  [[target]] → target
        target = inner.split('|')[0].strip()
        # Drop anchor fragments like [[page#section]]
        target = target.split('#')[0].strip()
        if target:
            targets.add(target)
    return targets

# ── Pages lookup ─────────────────────────────────────────────────────────────

def load_alias_index():
    with open(PAGES_JSON) as f:
        data = json.load(f)
    return data.get("alias_index", {})

# ── Main commands ─────────────────────────────────────────────────────────────

def cmd_status(args):
    chapters = get_all_chapters()
    prog = load_progress()
    idx = prog.get("next_index", 0)
    scanned = len(prog.get("chapters_scanned", []))
    total = len(chapters)
    pct = 100 * scanned // total if total else 0

    print(f"進度: {scanned}/{total} 章 ({pct}%)")
    if idx < total:
        _, _, book, stem = chapters[idx]
        print(f"下一章: [{idx+1}/{total}] {stem}")
    else:
        print("✓ 全部章节已扫描完毕")
    print(f"累计发现遗漏: {prog['stats'].get('total_missing_found', 0)} 个")
    print(f"累计加入队列: {prog['stats'].get('total_added_to_queue', 0)} 个")

def cmd_next(args):
    chapters = get_all_chapters()
    prog = load_progress()
    idx = prog.get("next_index", 0)
    if idx >= len(chapters):
        print("ALL_DONE")
        return
    _, _, book, stem = chapters[idx]
    print(f"{stem}")

def cmd_scan(args):
    chapters = get_all_chapters()
    prog = load_progress()
    alias_index = load_alias_index()

    # Determine which chapter to scan
    if args.chapter:
        match = None
        for bnum, cnum, book, stem in chapters:
            if stem.startswith(args.chapter) or stem == args.chapter:
                match = (bnum, cnum, book, stem)
                break
        if not match:
            print(f"ERROR: chapter '{args.chapter}' not found", file=sys.stderr)
            sys.exit(1)
        _, _, book, stem = match
    else:
        idx = prog.get("next_index", 0)
        if idx >= len(chapters):
            print("ALL_DONE")
            return
        _, _, book, stem = chapters[idx]

    # Read chapter file
    chapter_file = PAGES_DIR / f"{stem}.md"
    if not chapter_file.exists():
        print(f"ERROR: {chapter_file} not found", file=sys.stderr)
        sys.exit(1)

    text = chapter_file.read_text(encoding="utf-8")
    links = extract_wikilinks(text)

    # Check broken wikilinks (existing links without pages)
    broken = sorted(l for l in links if l not in alias_index)

    # Output chapter metadata + full text for Claude analysis
    print(f"CHAPTER: {stem}")
    print(f"BOOK: {book}")
    print(f"TOTAL_LINKS: {len(links)}")
    print(f"BROKEN_WIKILINKS({len(broken)}): {', '.join(broken) if broken else '(none)'}")
    print("---KNOWN_ENTITIES---")
    for l in sorted(links):
        if l in alias_index:
            print(f"  {l}")
    print("---CHAPTER_TEXT---")
    # Print only PN lines (content) for Claude to analyze, stripping frontmatter
    in_frontmatter = False
    fm_count = 0
    for line in text.split("\n"):
        if line.strip() == "---":
            fm_count += 1
            if fm_count <= 2:
                continue
        if fm_count < 2:
            continue
        # Strip [[X|Y]] → Y for readability but keep raw links visible
        print(line)

def cmd_advance(args):
    chapters = get_all_chapters()
    prog = load_progress()
    idx = prog.get("next_index", 0)
    if idx >= len(chapters):
        print("ALREADY_DONE")
        return
    _, _, book, stem = chapters[idx]
    prog.setdefault("chapters_scanned", []).append(stem)
    prog["next_index"] = idx + 1
    save_progress(prog)
    print(f"ADVANCED: {stem} → index {idx+1}/{len(chapters)}")

def cmd_record_found(args):
    """Record stats after a scan."""
    prog = load_progress()
    prog["stats"]["total_missing_found"] = prog["stats"].get("total_missing_found", 0) + args.found
    prog["stats"]["total_added_to_queue"] = prog["stats"].get("total_added_to_queue", 0) + args.queued
    save_progress(prog)
    print(f"STATS_UPDATED: found+{args.found} queued+{args.queued}")

def cmd_reset(args):
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    print("RESET: progress cleared")

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Chapter scan tool")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status")
    sub.add_parser("next")

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--chapter", default=None, help="Chapter stem prefix")

    sub.add_parser("advance")

    p_rec = sub.add_parser("record-found")
    p_rec.add_argument("--found", type=int, default=0)
    p_rec.add_argument("--queued", type=int, default=0)

    sub.add_parser("reset")

    args = parser.parse_args()
    if args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "next":
        cmd_next(args)
    elif args.cmd == "scan":
        cmd_scan(args)
    elif args.cmd == "advance":
        cmd_advance(args)
    elif args.cmd == "record-found":
        cmd_record_found(args)
    elif args.cmd == "reset":
        cmd_reset(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
