---
name: skill-butler-w10j
description: 三体 Wiki H25 列表页建设——识别标签组中缺少 type=list 汇总页的情况，直接建立静态 Markdown 列表页（不依赖 :::query 插件）。每次建 1-3 个列表页。
---

# SKILL W10j: H25 列表页建设

> 当某类词条积累到 5 个以上，读者就需要一个入口页来浏览全集。H25 的任务是发现这些集合缺口，并直接建立静态列表页。

---

## 一、触发时机

| 触发 | 条件 | 备注 |
|------|------|------|
| 周期触发 | `round % 37 == 0`（每 37 轮）| 与 H17 coverage-scan 同轮 |
| 手动触发 | 用户指定 | |
| 自动条件 | 总页数 ≥ 500（当前：759，已满足）| |

---

## 二、三体列表页候选集

以下标签/类型组有明确的列表页需求：

| 标签/类型 | 候选列表页标题 | 预估词条数 | 优先级 |
|---------|-------------|----------|--------|
| `舰船` | 太阳系舰队列表 | ≥ 20 | 高 |
| `面壁者` | 面壁者列表 | 4（全集） | 高（固定4人） |
| `纪元` / type=era | 三体宇宙纪元总览 | ≥ 8 | 高 |
| `宇宙文明` / type=civilization | 宇宙文明列表 | ≥ 5 | 中 |
| `技术` / type=technology | 三体科技列表 | ≥ 30 | 中 |
| `武器` / type=weapon | 武器与打击手段列表 | ≥ 10 | 中 |
| `组织` / type=organization | 重要组织列表 | ≥ 15 | 中 |
| `事件` / type=event | 重大事件年表 | ≥ 20 | 中 |

---

## 三、执行流程

### 步骤 1 · 识别缺口

```python
import re, json
from pathlib import Path

pages_dir = Path('wiki/public/pages')
pages_json = json.loads(Path('wiki/public/pages.json').read_text(encoding='utf-8'))

# 已有的 type=list 页面
existing_lists = [p['id'] for p in pages_json if p.get('type') == 'list']
print(f"已有列表页：{existing_lists}")

# 按 type 统计词条数
type_counts = {}
tag_counts = {}
for p in pages_json:
    t = p.get('type', '')
    if t and not t.startswith('chapter'):
        type_counts[t] = type_counts.get(t, 0) + 1
    for tag in p.get('tags', []):
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

# 找缺列表页的大型分组（≥5个词条）
print("\n各 type 词条数（≥5）：")
for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
    if cnt >= 5:
        print(f"  {t}: {cnt} 个")

print("\n各 tag 词条数（≥5）：")
for tag, cnt in sorted(tag_counts.items(), key=lambda x: -x[1]):
    if cnt >= 5:
        print(f"  #{tag}: {cnt} 个")
```

### 步骤 2 · 生成列表页内容

对选定的类型/标签，从 pages.json 提取页面信息并生成静态 Markdown：

```python
def build_list_page(list_type_or_tag, title, description, is_tag=False):
    """生成列表页内容"""
    pages_json = json.loads(Path('wiki/public/pages.json').read_text(encoding='utf-8'))
    chapter_prefix = ('三体I-', '三体II-', '三体III-')

    if is_tag:
        items = [p for p in pages_json
                 if list_type_or_tag in p.get('tags', [])
                 and not any(p['id'].startswith(pfx) for pfx in chapter_prefix)]
    else:
        items = [p for p in pages_json
                 if p.get('type') == list_type_or_tag
                 and not any(p['id'].startswith(pfx) for pfx in chapter_prefix)]

    # 按 books 字段排序（先I后II后III），同书按 label 字母序
    def sort_key(p):
        books = p.get('books', [])
        book_order = min([{'三体I': 1, '三体II': 2, '三体III': 3}.get(b, 9) for b in books] or [9])
        return (book_order, p.get('label', p['id']))

    items.sort(key=sort_key)
    return items
```

### 步骤 3 · 列表页模板

```markdown
---
id: 太阳系舰队列表
type: list
label: 太阳系舰队列表
tags: [舰船, 列表]
description: 危机纪元至末日战役期间人类建造的主要太空舰船汇总
books: [三体I, 三体II, 三体III]
quality: standard
---

# 太阳系舰队列表

收录危机纪元至末日战役期间人类建造的主要太空舰船，共 XX 艘。

## 危机纪元舰船

| 舰船 | 类型 | 出场书册 | 简介 |
|------|------|---------|------|
| [[自然选择号]] | 核动力战舰 | 三体II | 罗辑乘坐逃离太阳系的旗舰 |
| [[蓝色空间号]] | 探索舰 | 三体II、三体III | 发现四维碎片，在宇宙中漂流 |

## 威慑纪元舰船

（...）

## 末日纪元舰船

（...）

## 相关词条

- [[太空战争技术]]
- [[末日战役]]
- [[人类宇宙舰队]]
```

### 步骤 4 · 建立列表页

```bash
# 通过 add_page.py 建立（不直接 Write，保持记录链）
python3 wiki/scripts/add_page.py "太阳系舰队列表" - \
    --summary "H25: 建立舰船汇总列表页（type=list），收录XX艘舰船" \
    --author $INSTANCE << 'EOF'
（列表页内容）
EOF

git add wiki/public/pages/太阳系舰队列表.md

python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --instance $INSTANCE \
    --type H25-list-build \
    --page "太阳系舰队列表" \
    --result accept \
    --desc "H25列表页建设：新建「太阳系舰队列表」（type=list），收录${CNT}艘舰船" \
    --reflect "发现${MISSING}个分类缺少列表页；舰船类数量最多（${SHIP_CNT}艘），优先建设"
```

---

## 四、列表页质量标准

| 检查项 | 要求 |
|--------|------|
| **覆盖率** | 覆盖该类型/标签 80% 以上的页面（Wiki 中有的） |
| **表格格式** | 用 Markdown 表格，含名称/简介/出场书册 |
| **分节** | 若词条 > 10 个，按纪元或类型分节 |
| **相关词条** | ≥ 3 个 `[[]]` 链接 |
| **更新机制** | 每次 H20 list-update 检查是否有新词条未入表 |

---

## 五、静态列表 vs :::query 插件

> 三体前端未实现 `:::query` 插件，所以 H25 使用**静态 Markdown 列表**方案：
> - 优点：无前端依赖，跨平台渲染正常
> - 缺点：新建词条后需 H20 list-update 手动补充
> - 维护：每次 H20 任务检查列表页是否遗漏新词条

---

## 六、建议建设顺序

1. **太阳系舰队列表**（舰船最多，读者查询需求最高）
2. **面壁者列表**（固定 4 人，内容已全 featured，列表简单但有代表性）
3. **三体宇宙纪元总览**（era 类型，有时间线意义）
4. **重大事件年表**（event 类型，叙事全景视角）
5. **宇宙文明列表**（civilization 类型）

---

## 七、与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| H20 list-update | H25 建列表页；H20 在之后每轮检查是否有新词条未入表 |
| W2 A1 | A1 create-page 新建词条后，H20 负责更新对应列表页 |
| W9 | W9 发现某类型词条多但无列表页时，可提案触发 H25 |

---

## 相关路径

- `wiki/public/pages/` — 列表页存放位置（与普通词条页相同目录）
- `wiki/public/pages.json` — 用于统计各类型词条数
- `wiki/logs/butler/housekeeping_queue.md` — H25 任务队列
