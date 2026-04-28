# a2wiki Skill Memory

经验积累索引。每条是一个从实战中归纳的规则，供后续轮次直接查用。

---

## pages.json 数据结构（必读）

```python
d = json.load(open('wiki/public/pages.json', encoding='utf-8'))
pages = d['pages']       # dict: slug → page_obj（不是列表！）
ai    = d['alias_index'] # dict: alias → canonical_slug
```

**坑**：`d` 本身也是 dict，键为 `['pages', 'alias_index', 'page_count', 'generated']`。不要直接迭代 `d`。

---

## 三层查重 + 质量扫描（步骤3核心，每个候选必跑）

返回 `(match_type, slug, quality)` 三元组，一次调用同时得出决策。

```python
def check_page(candidate):
    def _q(slug): return pages.get(slug, {}).get('quality', '?')
    if candidate in pages: return 'exact', candidate, _q(candidate)
    if candidate in ai: return 'alias', ai[candidate], _q(ai[candidate])
    hits = [(k,v) for k,v in ai.items() if (candidate in k or k in candidate) and len(k)>=3]
    if hits:
        slug = max(hits, key=lambda x: len(x[0]))[1]
        return 'fuzzy', slug, _q(slug)
    frags = [candidate[i:i+2] for i in range(len(candidate)-1)]
    scores = {}
    for f in frags:
        for k,v in ai.items():
            if f in k and len(k)>=4: scores[v] = scores.get(v,0)+1
    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 2: return 'fragment', best, _q(best)
    return 'missing', None, None

# 批量输出决策
for c in candidates:
    match, slug, quality = check_page(c)
    if match == 'missing':
        print(f'[CREATE ] {c}')
    elif quality in ('stub', 'basic'):
        print(f'[ENRICH ] {c} → {slug} [{quality}]')
    else:
        print(f'[SKIP   ] {c} → {slug} [{quality}]')
```

**层2c（二字碎片）** 是关键，捕获「台球实验 vs 台球桌实验」这类名称变体。

---

## 知识类型 → Wiki type 映射

| 知识类型 | Wiki type |
|---------|-----------|
| narrative — 人物 | `person` |
| narrative — 概念 | `concept` |
| narrative — 事件 | `event` |
| narrative — 地点 | `place` |
| narrative — 组织 | `organization` |
| narrative — 技术/器物 | `technology` |
| narrative — 时代/纪元 | `era` |
| narrative — 文本 | `book` |
| fact — 独立列表 | `list` |
| **skill — 操作流程** | **`skill`（不是 concept！）** |

---

## 已有页面处理四分法（步骤4核心）

| 已有 quality | 新信息量 | 操作 |
|-------------|---------|------|
| `stub`（<5行正文） | 充足 | 替换重写，质量升级 |
| `basic` | 有新节或新引文 | 增补（Read→内存合并→写回完整页） |
| `standard` / `featured` | 有1-2处补充 | 精准追加 |
| `standard` / `featured` | 与现有内容重复 | skip，写入 coverage.md |

**重要**：`edit_page.py` 是全页替换，增补时必须先 Read 现有内容，在内存中合并后再写回。不能用新内容覆盖已有内容。

---

## 三体三部曲 wiki 覆盖规律（三体I批次1-10 + 三体II全量 + 三体III全量实战）

**产出递减规律**：三体I产出8页，三体II产出3页，三体III产出0页。Butler 已将主线词条建设得极为完整，a2wiki 的增量价值随部数递减至零。

**新建词条集中在**：器物（唐号/空天飞机）、地点（默思室/监听部/3K眼镜）、次要概念（恒星呼吸）。

**字符数注意**：Python `len(text)` 给出字符数（约为字节数的 1/3），三体I=200K字符，三体II=341K，三体III=390K，均需按字符数而非字节数规划批次。

---

## 三体I wiki 覆盖规律（来自批次1-5实战）

- 主要人物（叶文洁/汪淼/罗辑等）和核心概念（黑暗森林/智子/水滴等）**全部已是 featured**
- 三体I 上 a2wiki 的主要价值在于**背景层词条**：
  - 组织类（红卫兵派系、军事机构）
  - 历史事件类（文革相关、武装冲突）
  - 次要概念类（游戏机制、器物道具）
  - 次要人物类（叶文雪等仅在他页提及的人）
- 游戏内设定（乱纪元/恒纪元/飞星/三体游戏等）**已全部建好**
- **游戏场景章节**（哥白尼/墨子/牛顿/冯诺依曼等NPC出场章）跳过率100%，基本不产出新词条，可快速处理
- 三体游戏 NPC（周文王/纣王/伏羲/伽利略/亚里士多德/达芬奇/布鲁诺/牛顿/冯诺依曼/秦始皇等）**全部已有 featured 页**

---

## 引文格式规范

从 `corpus_search.py` 复制输出，格式为：
```
> 原文引用
> （卷-章-编号，如 1-02-003）
```

**禁止猜测或改写引文内容**，必须从搜索结果原样复制。

---

## 自改机制要求

- 每轮结束后必须追加一条到 `CHANGELOG.md`（无改进也要留"为何不改"）
- `SKILL.md` 只存当前有效规则，历史变更在 `CHANGELOG.md`
- `MEMORY.md`（本文件）存实战积累的经验规则，不存历史

---

## 进度文件位置

```
wiki/logs/a2wiki/<source-slug>/
├── progress.md    # 批次状态，断点续传
├── coverage.md    # 勘察表累积
└── insights.md    # 跨域洞察
```
