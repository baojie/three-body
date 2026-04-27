#!/usr/bin/env python3
"""
从三体语料章节页面中发现高频实体，输出尚未建页的候选词条。

不同于 discover_wanted.py（只找 broken wikilinks），本脚本主动扫描语料，
发现从未被 [[链接]] 过的高频实体——这是 discover_wanted.py 的盲区。

用法:
    python3 wiki/scripts/butler/discover_corpus.py [--top N] [--min-freq N]
    python3 wiki/scripts/butler/discover_corpus.py --json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
PAGES_DIR = ROOT / "public" / "pages"
PAGES_JSON = ROOT / "public" / "pages.json"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# ── 实体提取模式 ────────────────────────────────────────────────
# 船名/舰名：用"弯引号+中文+弯引号+号"提取，避免把标点吞进去
#   语料格式：“万有引力”号
RE_SHIP = re.compile(r"“([一-鿿]{2,8})”号")
# 纪元/计划/行动/战役/理论/技术等后缀型名词
RE_SUFFIXED = re.compile(
    r"([一-鿿]{2,8}(?:纪元|计划|行动|战役|理论|法则|悖论|假说|定律"
    r"|技术|系统|装置|探测器|飞船|飞行器|武器|防线|基地))"
)
# 人名启发式：以常见中文姓氏开头，后跟1-3字给名，紧接"说"/"问"/"答"等无歧义动词
# 用词边界约束防止误匹配（如"程心知道"→"程心知"）
_SURNAMES = (
    "赵钱孙李周吴郑王冯陈卫蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜"
    "戚谢邹柏窦章云苏潘葛范彭郎鲁韦昌马方俞任袁柳鲍史唐费薛雷贺倪"
    "汤滕殷罗毕郝邬安常于傅皮卞齐康伍余顾孟平黄穆萧尹姚邵汪祁毛禹"
    "贝明臧计伏成戴谈宋庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路江童"
    "颜郭梅盛林钟徐邱骆高夏蔡田樊胡凌霍虞万柯管卢莫干解丁宣邓单杭"
    "洪包诸左石崔吉钮龚程邢裴陆荣翁惠曲家封靳卓蒙池乔能双闻翟谭贡"
    "劳申扶冉郦刘叶宁仇祖武符景詹束龙司"
)
RE_PERSON = re.compile(
    r"(?<![一-鿿])([" + _SURNAMES + r"][一-鿿]{1,3})(?:说道|说道|问道|答道|叫道|笑道)(?![一-鿿])"
)
# 直接引号标注的专有名词（非号船）
RE_QUOTED = re.compile(r"“([一-鿿]{3,8})”(?!号)")

# ── 噪音过滤 ────────────────────────────────────────────────────
STOP_WORDS = {
    # 虚词/连接词
    "但是", "所以", "因为", "如果", "虽然", "已经", "可以", "应该",
    "需要", "知道", "看到", "听到", "感到", "觉得", "认为", "告诉",
    # 泛指名词
    "人类", "文明", "地球", "太阳", "宇宙", "时间", "空间", "世界",
    "社会", "科学", "技术", "物理", "数学", "政府", "军队", "组织",
    "机构", "委员", "会议", "情报", "信息", "数据", "问题", "解决",
    "方案", "目标", "任务", "工作", "研究", "发现", "未来", "过去",
    "现在", "历史", "文化", "语言", "思想", "意识", "精神", "太空",
    "星际", "战争", "国家", "人们", "大家", "自己", "他们", "我们",
    # 书名
    "三体", "地球往事", "黑暗森林", "死神永生",
    # 已在pages中的核心词（避免与alias重复）
    "太阳系", "三体文明", "叶文洁", "罗辑", "程心", "章北海",
    "汪淼", "史强", "云天明", "关一帆", "维德", "艾AA",
    # 指示词/无意义短语
    "这个人", "那个人", "一个人", "每个人", "这艘飞船", "那艘飞船",
    "两艘飞船", "这个系统", "那个系统", "这个计划", "那个计划",
    "这是计划", "这是乱纪元", "在危机纪元", "在威慑纪元", "在恒纪元",
    "基础理论", "操作系统", "监听系统", "航天系统", "对黑暗森林理论",
    "预警系统", "技术公有化",
}

# 频率低于此的结果在报告中降权
MIN_SIGNAL_FREQ = 2


def load_existing(pages_json_path: Path) -> set[str]:
    known: set[str] = set()
    if not pages_json_path.exists():
        return known
    with open(pages_json_path, encoding="utf-8") as f:
        data = json.load(f)
    for entry in data.get("pages", {}).values():
        known.add(entry.get("label", ""))
        for alias in (entry.get("aliases") or []):
            if isinstance(alias, str):
                known.add(alias)
    known.discard("")
    return known


def scan_chapters(pages_dir: Path) -> dict[str, Counter]:
    """返回按来源分类的候选频率 Counter。"""
    ships: Counter = Counter()
    suffixed: Counter = Counter()
    persons: Counter = Counter()
    quoted: Counter = Counter()

    chapter_files = sorted(
        f for f in pages_dir.glob("*.md")
        if f.stem.startswith(("三体I-", "三体II-", "三体III-"))
    )

    for page_path in chapter_files:
        text = page_path.read_text(encoding="utf-8", errors="replace")
        m = FRONTMATTER_RE.match(text)
        body = text[m.end():] if m else text

        for line in body.splitlines():
            # 跳过 PN 标签行头，只取正文部分
            stripped = re.sub(r"^\[\d-\d{2}-\d{3}\]\s*", "", line.strip())
            if not stripped:
                continue

            for m in RE_SHIP.finditer(stripped):
                ships[m.group(1) + "号"] += 1

            for m in RE_SUFFIXED.finditer(stripped):
                cand = m.group(1)
                if cand not in STOP_WORDS:
                    suffixed[cand] += 1

            for m in RE_PERSON.finditer(stripped):
                cand = m.group(1)
                if cand not in STOP_WORDS and len(cand) >= 2:
                    persons[cand] += 1

            for m in RE_QUOTED.finditer(stripped):
                cand = m.group(1)
                if cand not in STOP_WORDS:
                    quoted[cand] += 1

    return {"ships": ships, "suffixed": suffixed, "persons": persons, "quoted": quoted}


def discover_candidates(
    pages_dir: Path,
    pages_json: Path,
    top: int,
    min_freq: int,
) -> list[dict]:
    known = load_existing(pages_json)
    by_source = scan_chapters(pages_dir)

    # 合并所有候选，记录最高来源
    merged: Counter = Counter()
    source_map: dict[str, str] = {}
    for src, counter in by_source.items():
        for name, freq in counter.items():
            if name not in known:
                if freq > merged[name]:
                    source_map[name] = src
                merged[name] += freq

    results = [
        {"name": name, "freq": freq, "source": source_map.get(name, "?")}
        for name, freq in merged.most_common()
        if freq >= min_freq
    ]
    return results[:top]


def main():
    ap = argparse.ArgumentParser(description="从语料发现未建页的高频实体")
    ap.add_argument("--top", type=int, default=40, help="最多显示 N 条（默认40）")
    ap.add_argument("--min-freq", type=int, default=3, help="最小出现频率（默认3）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--pages", default=str(PAGES_DIR), help="pages 目录")
    args = ap.parse_args()

    pages_dir = Path(args.pages)
    candidates = discover_candidates(pages_dir, PAGES_JSON, args.top, args.min_freq)

    if not candidates:
        print("无候选（所有高频实体已建页，或频率低于阈值）")
        return

    if args.json:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
        return

    src_label = {"ships": "舰船", "suffixed": "后缀型", "persons": "人名", "quoted": "引号型"}
    print(f"{'频次':>4}  {'类型':4}  候选词条")
    print("-" * 45)
    for c in candidates:
        sl = src_label.get(c["source"], c["source"])
        print(f"{c['freq']:4d}x  {sl:4s}  {c['name']}")


if __name__ == "__main__":
    main()
