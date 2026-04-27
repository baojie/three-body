#!/usr/bin/env python3
"""从 git log 回填 wiki/public/history/ 和 wiki/public/recent.jsonl。

用 git show <hash>:<path> 获取每次提交时的实际文件内容（而非当前版本），
保证历史记录准确反映每次提交的状态。

history/*.jsonl 每行一条 JSON 修订记录，按时间正序排列（最旧在首行，最新在末行）。
recent.jsonl 是 append-only，每行一条 JSON 修订记录。
recent.json（前端快照）由 rebuild_recent.py 在发布时从 recent.jsonl 重建。
"""
import argparse, hashlib, json, subprocess, sys, os
from datetime import datetime, timezone
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[2]
PUBLIC      = ROOT / "wiki/public"
PAGES_DIR   = PUBLIC / "pages"
HIST_DIR    = PUBLIC / "history"
RECENT_JSONL = PUBLIC / "recent.jsonl"
PAGES_PFX   = "wiki/public/pages/"


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


def record(slug, content, ts_iso, author, summary, hist_entries, recent_entries):
    """向 hist_entries（正序列表）追加一条修订，向 recent_entries 追加摘要条目。"""
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # 去重：若末行（最新）content hash 与当前相同，跳过
    if hist_entries and hist_entries[-1].get("content_hash") == f"sha256:{sha}":
        return False

    now = datetime.fromisoformat(ts_iso)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    rev_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{sha[:6]}"

    # 从末行（最新条目）取 parent 信息
    last = hist_entries[-1] if hist_entries else None
    size_before = last["size"] if last else 0
    parent_rev  = last["rev_id"] if last else None

    size_after  = len(content.encode("utf-8"))

    entry = {
        "rev_id":       rev_id,
        "timestamp":    _iso(now),
        "author":       author,
        "summary":      summary,
        "parent_rev":   parent_rev,
        "content_hash": f"sha256:{sha}",
        "size_before":  size_before,
        "size":         size_after,
        "content":      content,
    }
    # 正序：直接 append（最旧在前，最新在后）
    hist_entries.append(entry)

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
        for f in HIST_DIR.glob("*.jsonl"):
            f.unlink()

    # 加载现有 history 文件（JSONL 格式，正序，列表）
    hist_cache = {}  # slug → list of entry dicts（正序）
    for f in HIST_DIR.glob("*.jsonl"):
        lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        hist_cache[f.stem] = [json.loads(l) for l in lines]

    # 已存在 history 且不 force → 增量模式：只处理比现有 latest rev 更新的提交（按 timestamp）
    latest_ts = {}  # slug → 最新已记录的 timestamp（UTC ISO）
    if not args.force:
        for slug, entries in hist_cache.items():
            if entries:
                latest_ts[slug] = entries[-1]["timestamp"]  # 末行 = 最新

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
                hist_cache[slug] = []

            added = record(
                slug, content, c["ts"], c["author"], c["summary"],
                hist_cache[slug], new_recent
            )
            if added:
                print(f"✓ {slug} @ {c['ts'][:10]} ({c['summary'][:30]})")
                total += 1
            else:
                print(f"= {slug} 内容相同，跳过")

    # 写回 history 文件（JSONL 格式，正序，每行一条）
    for slug, entries in hist_cache.items():
        if entries:
            page_jsonl = HIST_DIR / f"{slug}.jsonl"
            page_jsonl.write_text(
                "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n",
                encoding="utf-8"
            )

    # 追加到 recent.jsonl（O_APPEND，按时间正序写入）
    new_recent.sort(key=lambda e: e.get("timestamp", ""))
    if new_recent:
        with RECENT_JSONL.open("a", encoding="utf-8") as f:
            for e in new_recent:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"\n完成：新增 {total} 条修订记录，追加至 recent.jsonl（+{len(new_recent)} 条）。")


if __name__ == "__main__":
    main()
