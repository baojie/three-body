#!/usr/bin/env python3
"""
构建 pages.json 注册表（给浏览器端 wikilink 解析用）。

用法:
    python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from compute_quality import compute_quality_score  # noqa: E402

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def build_registry(pages_root: Path) -> dict:
    pages: dict = {}
    alias_index: dict = {}

    for md_file in sorted(pages_root.rglob("*.md")):
        rel = md_file.relative_to(pages_root)
        pid = str(rel.with_suffix(""))
        text = md_file.read_text(encoding="utf-8")
        front = parse_frontmatter(text)

        # body = everything after frontmatter
        m_fm = FRONTMATTER_RE.match(text)
        body = text[m_fm.end():] if m_fm else text

        entry: dict = {
            "type":    front.get("type", "unknown"),
            "label":   front.get("label", pid),
            "aliases": front.get("aliases", []),
            "tags":    front.get("tags", []),
            "path":    f"pages/{rel}",
        }
        if front.get("description"):
            entry["description"] = front["description"]
        if front.get("featured"):
            entry["featured"] = True
        if front.get("image"):
            entry["image"] = front["image"]
        if front.get("quality"):
            entry["quality"] = front["quality"]
            entry["quality_score"] = compute_quality_score(front, body)
        # chapter-specific fields
        for field in ("book", "book_seq", "pn_prefix"):
            if front.get(field) is not None:
                entry[field] = front[field]

        pages[pid] = entry

        # alias index — chapter pages: only register by id, not label
        label_keys = [] if entry["type"] == "chapter" else [entry["label"]]
        for key in [pid] + label_keys + (entry["aliases"] or []):
            if not isinstance(key, str):
                continue
            if key in alias_index and alias_index[key] != pid:
                print(f"[warn] alias conflict: '{key}' → {alias_index[key]} vs {pid}", file=sys.stderr)
            else:
                alias_index[key] = pid

    return {
        "pages":       pages,
        "alias_index": alias_index,
        "page_count":  len(pages),
        "generated":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages_root", help="wiki/public/pages directory")
    ap.add_argument("--out", default="wiki/public/pages.json")
    args = ap.parse_args()

    root = Path(args.pages_root)
    if not root.is_dir():
        print(f"[error] not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    registry = build_registry(root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {len(registry['pages'])} pages → {out}")


if __name__ == "__main__":
    main()
