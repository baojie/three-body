---
name: skill-butler-9
description: 三体 Wiki 页面图式反思——每 29 轮从近期 featured 页中抽样，按 type 横向对比结构完整性，识别 schema 缺口，提案模板更新。输出沉淀到 wiki/logs/butler/schema_patterns/，供后续 enrich 动作复用。
---

# SKILL W9: 页面图式反思

> W5 改进 Butler 规则，W9 改进页面结构本身——两者互补，不重叠。

---

## 一、触发时机

| 触发 | 条件 |
|------|------|
| 周期触发 | `round % 29 == 0`（与 W5 同轮；W5 先执行，W9 在 W5 之后） |
| 手动 | 用户指定 `/reflect schema` |

W9 **不阻塞**下一轮，不写 failures.jsonl，只写 schema_patterns/ 目录。

---

## 二、反思流程（4 步）

### 步骤 1 · 收集样本

取近期（最近 3 轮）新增/升级的 featured 页，加随机 2 页：

```python
import json, random
from pathlib import Path

actions = []
for line in open('wiki/logs/butler/actions.jsonl'):
    import json as j
    try:
        a = j.loads(line)
        if a.get('page') and a.get('result') == 'accept':
            for p in a['page'].replace(',', ' ').replace('/', ' ').split():
                if p.strip(): actions.append(p.strip())
    except: pass

recent3 = list(dict.fromkeys(reversed(actions)))[:3]
all_pages = [p.stem for p in Path('wiki/public/pages').glob('*.md')
             if not p.stem.startswith(('三体I', '三体II', '三体III', '三体（'))]
random2 = random.sample(all_pages, 2)
sample = list(dict.fromkeys(recent3 + random2))[:5]
print("样本:", sample)
```

### 步骤 2 · 按 type 分组，横向对比

对每个样本，读取 `type` 字段，归入**细分类型表**（见§四）。
对每种 type，抽取同类已有 featured 页 3-5 个做横向对比：

```python
import json, re
from pathlib import Path

TARGET_TYPE = "person"  # 替换为当前 type
pages_dir = Path('wiki/public/pages')
same_type = []
for f in pages_dir.glob('*.md'):
    content = f.read_text(encoding='utf-8')
    m = re.search(r'^type:\s*(.+)$', content, re.M)
    q = re.search(r'^quality:\s*(.+)$', content, re.M)
    if m and m.group(1).strip() == TARGET_TYPE and q and q.group(1).strip() == 'featured':
        same_type.append(f.stem)
print(f"{TARGET_TYPE} featured 页共 {len(same_type)} 个，抽样:", same_type[:5])
```

### 步骤 3 · Schema 差距分析

对同类型 3-6 个 featured 页，检查：

| 检查项 | 三体各类型理想状态 |
|--------|-----------------|
| **必有节** | 各 type 的标准 sections 完整（见§四） |
| **PN 密度** | featured 页 ≥ 3 条 PN，person/event 类应 ≥ 5 条 |
| **引文块** | 核心场景用 `> 原文（PN）` 格式 |
| **相关词条节** | 有 `## 相关词条` 且链接数 ≥ 3 |
| **叙事分析节** | 有至少一个分析型段落（非纯事实罗列） |
| **链接密度** | 正文含 `[[]]` wikilink ≥ 3 |

### 步骤 4 · 输出反思文件

写 `wiki/logs/butler/schema_patterns/YYYY-MM-DD-R<N>.md`：

```markdown
# 图式反思 YYYY-MM-DD R<N>

## 样本
- [[页面1]]（type: person）
- [[页面2]]（type: concept）

## 横向对比

### type: person（本次抽样 3 页，同类 featured 共 NN 页）

| 检查项 | 有 | 缺 |
|--------|----|----|
| ## 生平/经历 | 3/3 | — |
| ## 历史意义/评价 | 2/3 | 1 缺 |
| 叙事分析节 | 3/3 | — |
| PN ≥ 5 | 2/3 | 1 不足（仅 3 条）|
| 相关词条 ≥ 3 链接 | 2/3 | 1 缺 |

**发现**：person 页缺"命运反讽/结局"分析节的仍有约 15%。

**提案**：enrich 时为 person 页补充"叙事地位"分析节，聚焦其在三部曲宏观叙事中的功能。

## 新类型识别

（无）

## 已稳定类型，本轮无新发现
- type: concept — schema 稳定
```

若某类型有 ≥5 个 featured 页且发现重大缺口 → **立即写/更新** `wiki/logs/butler/schema_patterns/templates/<type>.md`。

---

## 三、三体 type 细分类型表

| type | 核心节 | 特有节 | PN 目标 |
|------|--------|--------|---------|
| `person` | 生平、叙事意义/叙事地位 | 命运反讽或历史评价 | ≥ 5 |
| `concept` / `law` | 定义、机制说明、与黑暗森林的关联 | 宇宙学意义 | ≥ 3 |
| `technology` / `weapon` | 技术原理、战略价值 | 历史评价或叙事作用 | ≥ 3 |
| `event` | 经过、后果 | 叙事转折意义 | ≥ 4 |
| `era` | 时间段定义、社会特征 | 与威慑/黑暗森林的关系 | ≥ 3 |
| `civilization` | 特征、与人类关系 | 宇宙学地位 | ≥ 3 |
| `organization` | 职能、历史沿革 | 在三部曲中的决策作用 | ≥ 2 |
| `place` | 地理/物理特征、叙事中的出现 | — | ≥ 2 |

---

## 四、模板文件规范

模板存于 `wiki/logs/butler/schema_patterns/templates/<type>.md`：

```markdown
---
type: <type>
created: YYYY-MM-DD
updated: YYYY-MM-DD
sample_pages: [page1, page2]
---

# 模板：<type>

## 适用判断
frontmatter type == <type>

## 必有节（缺一加入 H-P2 enrich 队列）
1. ## [核心内容节]（如：生平经历 / 技术原理）
2. ## [叙事意义节]（分析此词条在三部曲叙事中的功能）
3. ## 相关词条

## 推荐节（有则更好）
- ## [类型特有节]（见 §三 特有节）

## PN 目标
≥ N 条（见 §三）

## 反面示例（避免）
- 纯事实罗列，无叙事分析
- 相关词条少于 3 个
```

---

## 五、积累规则

1. **每次 W9 写一个** `schema_patterns/YYYY-MM-DD-R<N>.md`
2. 某 type 累计 ≥ 5 个 featured 页且无模板 → 本轮建模板
3. 模板修订写入 `wiki/logs/butler/skill_changes.md`

---

## 六、与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| W5 | W5 改规则，W9 改结构；W9 发现的系统性缺口可提案给 W5 |
| W2 A2 | enrich-page 执行前参考 W9 模板，确保补充内容符合 type schema |
| W3 | W9 发现的必有节缺失 → 可提案更新 W3 质量标准（如加 PN 目标） |

---

## 相关路径

- `wiki/logs/butler/schema_patterns/` — 每轮反思输出（草稿）
- `wiki/logs/butler/schema_patterns/templates/` — 稳定 type 模板
- `wiki/logs/butler/skill_changes.md` — 模板修订记录
