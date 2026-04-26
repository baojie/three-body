#!/usr/bin/env python3
"""从 git log 回填 wiki/public/history/ 和 wiki/public/recent.json。

用 git show <hash>:<path> 获取每次提交时的实际文件内容（而非当前版本），
保证历史记录准确反映每次提交的状态。
"""
import argparse, hashlib, json, subprocess, sys, os
from datetime import datetime, timezone
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[2]
PUBLIC      = ROOT / "wiki/public"
PAGES_DIR   = PUBLIC / "pages"
HIST_DIR    = PUBLIC / "history"
RECENT      = PUBLIC / "recent.json"
PAGES_PFX   = "wiki/public/pages/"
WINDOW_SIZE = 1000


def git(*args, text=True):
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        text=text, errors="replace", cwd=ROOT
    ).strip()


def git_show_content(commit_hash, fpath):
    """返回指定 commit 时文件的内容，失败返回 None。"""
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit_hash}:{fpath}"],
            text=True, errors="replace", cwd=ROOT
        )
    except subprocess.CalledProcessError:
        return None


def _iso(dt):
    s = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return s[:-2] + ":" + s[-2:] if not s.endswith("Z") else s


def record(slug, content, ts_iso, author, summary, hist_data, recent_entries):
    """向 hist_data 追加一条修订，向 recent_entries 追加摘要条目。"""
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # 去重：若 content hash 与最新一条相同，跳过
    if hist_data["revisions"] and hist_data["revisions"][0].get("content_hash") == f"sha256:{sha}":
        return False

    now = datetime.fromisoformat(ts_iso)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    rev_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{sha[:6]}"

    size_before = hist_data["revisions"][0]["size"] if hist_data["revisions"] else 0
    size_after  = len(content.encode("utf-8"))

    entry = {
        "rev_id":       rev_id,
        "timestamp":    _iso(now),
        "author":       author,
        "summary":      summary,
        "parent_rev":   hist_data["latest_rev_id"],
        "content_hash": f"sha256:{sha}",
        "size_before":  size_before,
        "size":         size_after,
        "content":      content,
    }
    hist_data["revisions"].insert(0, entry)
    hist_data["latest_rev_id"]  = rev_id
    hist_data["revision_count"] = len(hist_data["revisions"])

    recent_entries.append({
        "page":    slug,
        **{k: v for k, v in entry.items() if k != "content"},
    })
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="清空并重建所有 history/")
    ap.add_argument("--author", default="git")
    args = ap.parse_args()

    HIST_DIR.mkdir(exist_ok=True)

    if args.force:
        for f in HIST_DIR.glob("*.json"):
            f.unlink()

    # 加载现有 history 文件
    hist_cache = {}
    for f in HIST_DIR.glob("*.json"):
        hist_cache[f.stem] = json.loads(f.read_text(encoding="utf-8"))

    # 已存在 history 且不 force → 记录已有条目的 rev_id 集合，用于增量判断
    # 增量模式：只处理比现有 latest rev 更新的提交（按 timestamp）
    latest_ts = {}  # slug → 最新已记录的 timestamp（UTC ISO）
    if not args.force:
        for slug, data in hist_cache.items():
            if data["revisions"]:
                latest_ts[slug] = data["revisions"][0]["timestamp"]

    # git log，按时间正序
    log = git(
        "log", "--format=COMMIT|%H|%aI|%an|%s",
        "--name-only", "--diff-filter=AM",
        "--", f"{PAGES_PFX}*.md"
    )

    commits = []
    current = None
    for line in log.splitlines():
        if line.startswith("COMMIT|"):
            _, rev, ts, author, summary = line.split("|", 4)
            current = {"rev": rev, "ts": ts, "author": author, "summary": summary, "files": []}
            commits.append(current)
        elif line.startswith(PAGES_PFX) and current:
            current["files"].append(line)

    commits.reverse()  # 最旧的先处理

    # 收集将新增的 recent 条目
    new_recent = []
    total = 0

    for c in commits:
        for fpath in c["files"]:
            slug = os.path.basename(fpath)[:-3]

            # 增量：若此提交时间 ≤ 已有最新记录，跳过
            if not args.force and slug in latest_ts:
                if c["ts"] <= latest_ts[slug]:
                    continue

            content = git_show_content(c["rev"], fpath)
            if content is None:
                continue

            if slug not in hist_cache:
                hist_cache[slug] = {
                    "page": slug, "latest_rev_id": None,
                    "revision_count": 0, "revisions": []
                }

            added = record(
                slug, content, c["ts"], c["author"], c["summary"],
                hist_cache[slug], new_recent
            )
            if added:
                print(f"✓ {slug} @ {c['ts'][:10]} ({c['summary'][:30]})")
                total += 1
            else:
                print(f"= {slug} 内容相同，跳过")

    # 写回 history 文件
    for slug, data in hist_cache.items():
        if data["revision_count"] > 0:
            (HIST_DIR / f"{slug}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    # 合并 recent.json
    if RECENT.exists():
        existing = json.loads(RECENT.read_text(encoding="utf-8"))
        old_entries = existing.get("entries", existing.get("recent", []))
    else:
        old_entries = []

    all_entries = old_entries + new_recent
    all_entries.sort(key=lambda e: e.get("timestamp", ""))
    all_entries = all_entries[-WINDOW_SIZE:]

    RECENT.write_text(
        json.dumps({"entries": all_entries, "rotations": 0}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"\n完成：新增 {total} 条修订记录，recent.json 共 {len(all_entries)} 条。")


if __name__ == "__main__":
    main()
