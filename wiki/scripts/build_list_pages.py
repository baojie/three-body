#!/usr/bin/env python3
"""
Generate thematic list pages using ::: query blocks.
Output: wiki/public/pages/列表·<name>.md

::: query fence syntax:
  ::: query
  <yaml params>
  :::
"""
from pathlib import Path

BASE = Path(__file__).parent.parent
PAGES_DIR = BASE / "public" / "pages"


def qblock(params: str) -> str:
    """Wrap YAML params in a ::: query fence."""
    return "::: query\n" + params.strip() + "\n:::"


# ─── List page definitions ──────────────────────────────────────────────────
# Each entry: dict with keys: slug, label, description, tags, sections
# sections: list of (section_heading, query_yaml_string) or just query_yaml_string

LIST_PAGES = [

    # ── 按书册 ──────────────────────────────────────────────────────────────
    {
        "slug": "列表·地球往事词条",
        "label": "《地球往事》词条",
        "description": "《三体I》中出现的所有词条，按类型汇总",
        "tags": ["分类", "三体I", "列表"],
        "intro": "以下词条均带有「三体I」标签，涵盖《地球往事》（2006）的人物、概念、科技、事件等。",
        "sections": [
            ("人物", """title: 人物
type_any: [person]
tags: 三体I
tags_not: [原文]
sort: label
display: list
limit: 300"""),
            ("概念与理论", """title: 概念与理论
type_any: [concept, theory]
tags: 三体I
tags_not: [原文]
sort: label
display: list
limit: 300"""),
            ("科技、事件与组织", """title: 科技、事件与组织
type_any: [technology, event, organization, place, weapon, era]
tags: 三体I
tags_not: [原文]
sort: label
display: list
limit: 300"""),
        ],
        "seealso": ["列表·黑暗森林词条", "列表·死神永生词条", "分类·人物"],
    },
    {
        "slug": "列表·黑暗森林词条",
        "label": "《黑暗森林》词条",
        "description": "《三体II》中出现的所有词条，按类型汇总",
        "tags": ["分类", "三体II", "列表"],
        "intro": "以下词条均带有「三体II」标签，涵盖《黑暗森林》（2008）的人物、概念、科技、事件等。",
        "sections": [
            ("人物", """title: 人物
type_any: [person]
tags: 三体II
tags_not: [原文]
sort: label
display: list
limit: 300"""),
            ("概念与理论", """title: 概念与理论
type_any: [concept, theory]
tags: 三体II
tags_not: [原文]
sort: label
display: list
limit: 300"""),
            ("科技、事件与组织", """title: 科技、事件与组织
type_any: [technology, event, organization, place, weapon, era]
tags: 三体II
tags_not: [原文]
sort: label
display: list
limit: 300"""),
        ],
        "seealso": ["列表·地球往事词条", "列表·死神永生词条", "分类·事件"],
    },
    {
        "slug": "列表·死神永生词条",
        "label": "《死神永生》词条",
        "description": "《三体III》中出现的所有词条，按类型汇总",
        "tags": ["分类", "三体III", "列表"],
        "intro": "以下词条均带有「三体III」标签，涵盖《死神永生》（2010）的人物、概念、科技、事件等。",
        "sections": [
            ("人物", """title: 人物
type_any: [person]
tags: 三体III
tags_not: [原文]
sort: label
display: list
limit: 300"""),
            ("概念与理论", """title: 概念与理论
type_any: [concept, theory]
tags: 三体III
tags_not: [原文]
sort: label
display: list
limit: 300"""),
            ("科技、事件与组织", """title: 科技、事件与组织
type_any: [technology, event, organization, place, weapon, era]
tags: 三体III
tags_not: [原文]
sort: label
display: list
limit: 300"""),
        ],
        "seealso": ["列表·地球往事词条", "列表·黑暗森林词条", "分类·科技"],
    },

    # ── 精品与质量 ──────────────────────────────────────────────────────────
    {
        "slug": "列表·精选词条",
        "label": "精选词条",
        "description": "质量达到 featured 级别、内容充实的词条，按质量分从高到低排列",
        "tags": ["分类", "精选", "列表"],
        "intro": "以下词条质量评级为 **featured**（精品），内容充实、有 PN 引文支撑。质量分越高表示内容越完整。",
        "sections": [
            ("精选人物", """title: 精选人物
type_any: [person]
quality: featured
tags_not: [原文]
sort: quality_score
order: desc
display: table
fields: [label, tags, quality_score]
field_labels:
  quality_score: 质量分
limit: 200"""),
            ("精选概念与理论", """title: 精选概念与理论
type_any: [concept, theory]
quality: featured
tags_not: [原文]
sort: quality_score
order: desc
display: table
fields: [label, tags, quality_score]
field_labels:
  quality_score: 质量分
limit: 200"""),
            ("精选科技、事件、组织与地点", """title: 精选科技、事件、组织与地点
type_any: [technology, event, organization, place, weapon, era, civilization]
quality: featured
tags_not: [原文]
sort: quality_score
order: desc
display: table
fields: [label, type, quality_score]
field_labels:
  quality_score: 质量分
limit: 200"""),
        ],
        "seealso": ["列表·待完善词条"],
    },
    {
        "slug": "列表·待完善词条",
        "label": "待完善词条",
        "description": "质量为 standard 级别的词条，内容较少，欢迎贡献",
        "tags": ["分类", "待完善", "列表"],
        "intro": "以下词条尚未达到精品标准，内容需要进一步充实。",
        "sections": [
            ("标准级词条（standard）", """title: 标准级词条（standard）
quality: standard
tags_not: [原文]
sort: label
display: list
limit: 300"""),
        ],
        "seealso": ["列表·精选词条"],
    },

    # ── 主题弧线 ────────────────────────────────────────────────────────────
    {
        "slug": "列表·面壁计划",
        "label": "面壁计划相关词条",
        "description": "面壁计划、四名面壁者及破壁人的全部相关词条",
        "tags": ["分类", "面壁计划", "面壁者", "列表"],
        "intro": "面壁计划（Wallfacer Project）是危机纪元中期联合国行星防御理事会授权的秘密反击计划，四名面壁者拥有不受监督的绝对权力。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [面壁计划, 面壁者, 破壁人]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["面壁者", "罗辑", "危机纪元", "列表·危机纪元"],
    },
    {
        "slug": "列表·末日战役",
        "label": "末日战役相关词条",
        "description": "末日战役（水滴攻击联合舰队）的相关人物、战舰、事件与技术",
        "tags": ["分类", "末日战役", "列表"],
        "intro": "末日战役发生于危机纪元末期，三体水滴探测器在几分钟内摧毁了由 2015 艘战舰组成的联合舰队，改变了人类文明的走向。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [末日战役]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["水滴探测器", "末日战役", "章北海", "列表·太空战舰"],
    },
    {
        "slug": "列表·黑暗森林",
        "label": "黑暗森林相关词条",
        "description": "黑暗森林法则、宇宙社会学及其推论的相关词条",
        "tags": ["分类", "黑暗森林", "宇宙社会学", "列表"],
        "intro": "黑暗森林法则是《三体II》的核心理论：宇宙是一片黑暗的森林，每个文明都是携枪的猎人，任何暴露坐标的文明都面临被消灭的命运。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [黑暗森林, 黑暗森林法则, 宇宙社会学]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["黑暗森林法则", "宇宙社会学", "罗辑", "叶文洁"],
    },
    {
        "slug": "列表·危机纪元",
        "label": "危机纪元相关词条",
        "description": "危机纪元（约公元201x—2208年）内的人物、事件与技术",
        "tags": ["分类", "危机纪元", "列表"],
        "intro": "危机纪元是从三体入侵被确认到罗辑建立黑暗森林威慑的约两百年历史时期，涵盖幼稚症、大低谷、面壁计划与末日战役。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [危机纪元]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["危机纪元", "面壁者", "列表·面壁计划", "列表·末日战役"],
    },
    {
        "slug": "列表·威慑纪元",
        "label": "威慑纪元相关词条",
        "description": "威慑纪元（公元2208—2272年）的人物、事件与社会制度",
        "tags": ["分类", "威慑纪元", "列表"],
        "intro": "威慑纪元是罗辑建立黑暗森林威慑后、程心接剑放弃威慑前的六十四年，人类在恒星级毁灭的剑悬头顶下重建了技术文明。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [威慑纪元]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["威慑纪元", "罗辑", "程心", "执剑人"],
    },
    {
        "slug": "列表·掩体纪元",
        "label": "掩体纪元相关词条",
        "description": "掩体纪元（公元2332年后）的相关词条",
        "tags": ["分类", "掩体纪元", "列表"],
        "intro": "掩体纪元始于二向箔降临太阳系、人类躲入巨行星掩体之后，是三体III尾声阶段的历史时期。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [掩体纪元]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["掩体计划", "二向箔", "广播纪元"],
    },
    {
        "slug": "列表·三体游戏",
        "label": "三体游戏相关词条",
        "description": "《三体I》中汪淼参与的三体 VR 游戏内的角色、场景与历史时期",
        "tags": ["分类", "三体游戏", "列表"],
        "intro": "三体游戏是地球三体组织（ETO）制作的 VR 游戏，以三颗太阳的真实运动为背景，汪淼通过游戏接触到三体文明的历史。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [三体游戏]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["三体游戏", "汪淼", "地球三体组织", "三体文明"],
    },
    {
        "slug": "列表·逃亡主义",
        "label": "逃亡主义相关词条",
        "description": "星舰地球、逃亡主义思想及相关人物、战舰的词条",
        "tags": ["分类", "逃亡主义", "列表"],
        "intro": "逃亡主义（Escapism）是末日战役后四艘逃亡舰确立的生存哲学：放弃人类整体，以少数人保存文明火种。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [逃亡主义, 星舰地球]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["章北海", "自然选择号", "蓝色空间号", "列表·太空战舰"],
    },
    {
        "slug": "列表·云天明童话",
        "label": "云天明童话相关词条",
        "description": "云天明三则童话（《国王的新画师》《饕餮海》《深水王子》）的角色、意象与解码",
        "tags": ["分类", "云天明童话", "列表"],
        "intro": "云天明在三体文明中讲述的三则童话，表面是奇幻故事，内核是精确的情报包裹，暗示曲率驱动（光速飞船）与黑域建造方法。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [云天明童话]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["云天明", "程心", "云天明三则童话"],
    },
    {
        "slug": "列表·宇宙社会学",
        "label": "宇宙社会学相关词条",
        "description": "宇宙社会学理论体系、黑暗森林法则、猜疑链与技术爆炸的相关词条",
        "tags": ["分类", "宇宙社会学", "列表"],
        "intro": "宇宙社会学是叶文洁启发、罗辑建立的理论，以「生存是文明的第一需要」和「文明持续增长但宇宙物质总量有限」为两条公理，推导出黑暗森林法则。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [宇宙社会学]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["宇宙社会学", "黑暗森林法则", "叶文洁", "罗辑"],
    },

    # ── 人物中心 ────────────────────────────────────────────────────────────
    {
        "slug": "列表·程心相关",
        "label": "程心相关词条",
        "description": "与程心直接相关的人物、事件、决策与地点",
        "tags": ["分类", "程心", "列表"],
        "intro": "程心是《三体III》的核心人物，曾任阶梯计划工作人员、第二任执剑人、星环城创始人。她的每一次选择都对人类命运产生了深远影响。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [程心]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["程心", "云天明", "关一帆", "执剑人"],
    },
    {
        "slug": "列表·叶文洁相关",
        "label": "叶文洁相关词条",
        "description": "与叶文洁相关的人物、事件、组织与地点",
        "tags": ["分类", "叶文洁", "列表"],
        "intro": "叶文洁是整个三体宇宙命运链的起点——她向三体文明发出的一颗信号，引发了此后数百年的所有故事。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [叶文洁]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["叶文洁", "红岸基地", "地球三体组织", "汪淼"],
    },
    {
        "slug": "列表·章北海相关",
        "label": "章北海相关词条",
        "description": "与章北海相关的人物、事件与战舰",
        "tags": ["分类", "章北海", "列表"],
        "intro": "章北海是危机纪元最具争议的人物之一：他以暗杀、欺骗和冷静的战略理性为代价，保存了人类文明的最后星火。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [章北海]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["章北海", "自然选择号", "末日战役", "逃亡主义"],
    },
    {
        "slug": "列表·罗辑相关",
        "label": "罗辑相关词条",
        "description": "与罗辑相关的人物、事件与概念",
        "tags": ["分类", "罗辑", "列表"],
        "intro": "罗辑是面壁计划中唯一成功的面壁者，以宇宙社会学逻辑而非武力迫使三体停止推进，成为历史上在职时间最长的执剑人。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [罗辑]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["罗辑", "面壁者", "执剑人", "黑暗森林法则"],
    },
    {
        "slug": "列表·智子相关",
        "label": "智子相关词条",
        "description": "三体智子（质子展开体）的技术、监控作用与相关事件",
        "tags": ["分类", "智子", "列表"],
        "intro": "智子是三体文明将质子展开到二维平面后蚀刻的超级计算机，以光速传递信息、监听地球通讯，并在三体II/III中以人型形态登场。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [智子]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["智子", "三体文明", "引力波广播"],
    },

    # ── 技术专题 ────────────────────────────────────────────────────────────
    {
        "slug": "列表·太空战舰",
        "label": "太空战舰与飞船",
        "description": "三体宇宙中出现的战舰、飞船与太空飞行器",
        "tags": ["分类", "科技", "飞船", "列表"],
        "intro": "三体三部曲中出现了从危机纪元的恒星级战舰到星舰地球逃亡舰、广播纪元曲率驱动飞船的各类太空飞行器。",
        "sections": [
            ("战舰与飞船", """title: 战舰与飞船
tags_any: [飞船, 战舰, 太空军, 自然选择号]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
            ("全部科技词条（含飞行器相关）", """title: 全部科技词条
type_any: [technology]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["分类·科技", "末日战役", "章北海", "列表·逃亡主义"],
    },
    {
        "slug": "列表·名场面",
        "label": "三体名场面",
        "description": "三体三部曲中的经典场景与高光时刻（type=scene 或 tag=名场面）",
        "tags": ["分类", "名场面", "列表"],
        "intro": "以下词条记录了三部曲中最具代表性的叙事场景，均有原文 PN 引文支撑。",
        "sections": [
            ("全部名场面", """title: 全部名场面
tags_any: [名场面]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["列表·精选词条", "叶文洁", "章北海", "程心"],
    },
    {
        "slug": "列表·四维空间",
        "label": "四维空间与降维相关词条",
        "description": "四维空间探索、降维打击与高维宇宙的相关词条",
        "tags": ["分类", "四维空间", "列表"],
        "intro": "《三体III》中蓝色空间号进入四维空间，揭示宇宙的高维结构；二向箔降维打击是大宇宙维度战争的组成部分。",
        "sections": [
            ("全部相关词条", """title: 全部相关词条
tags_any: [四维空间]
tags_not: [原文]
sort: label
display: list
limit: 200"""),
        ],
        "seealso": ["二向箔", "蓝色空间号", "大宇宙", "小宇宙"],
    },
]


def build_page(entry: dict) -> str:
    slug = entry["slug"]
    label = entry["label"]
    desc = entry["description"]
    tags = entry["tags"]
    intro = entry.get("intro", "")
    sections = entry.get("sections", [])
    seealso = entry.get("seealso", [])

    tags_yaml = "[" + ", ".join(tags) + "]"

    lines = [
        "---",
        f"id: {slug}",
        "type: list",
        f"label: {label}",
        f"aliases: [{label}]",
        f"tags: {tags_yaml}",
        f"description: {desc}",
        "books: [三体I, 三体II, 三体III]",
        "quality: standard",
        "---",
        f"# {label}",
        "",
        intro,
        "",
    ]

    for item in sections:
        heading, query_yaml = item
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(qblock(query_yaml))
        lines.append("")

    if seealso:
        lines.append("## 相关词条")
        lines.append("")
        for ref in seealso:
            lines.append(f"- [[{ref}]]")
        lines.append("")

    return "\n".join(lines)


def main():
    created = []
    for entry in LIST_PAGES:
        content = build_page(entry)
        slug = entry["slug"]
        out_path = PAGES_DIR / f"{slug}.md"
        out_path.write_text(content, encoding="utf-8")
        print(f"  {out_path.name}")
        created.append(str(out_path))

    print(f"\nGenerated {len(created)} list pages.")
    return created


if __name__ == "__main__":
    main()
