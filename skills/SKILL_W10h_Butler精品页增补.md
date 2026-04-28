---
name: skill-butler-w10h
description: 三体 Wiki H22 精品页增补——识别 featured 页中有潜力升 premium 的候选，评估叙事深度/PN密度/结构完整性，写入 H-P2 enrich 队列，供后续 A2/A3 处理。
---

# SKILL W10h: H22 精品页增补（精品页候选识别）

> 当 featured 页积累充足时，精中选精：识别哪些 featured 页已具备 premium 潜力，集中火力提升。

---

## 一、触发时机

| 触发 | 条件 |
|------|------|
| 周期触发 | `round % 29 == 0`（与 W5/W9 同轮，在 W9 之后执行） |
| 手动触发 | 用户指定，或 H10 housekeeping-scan 发现批量候选 |
| 自动条件 | featured 页数 ≥ 200（当前：511，已满足） |

---

## 二、识别标准

### Premium 候选判断（须同时满足）

| 标准 | 阈值 | 备注 |
|------|------|------|
| **PN 密度** | ≥ 6 条 | 引文充足，有原文支撑 |
| **叙事分析节** | ≥ 1 个分析型段落 | 非纯事实罗列，有"意义/地位/评价"类内容 |
| **相关词条** | ≥ 4 个 `[[]]` 链接 | 与 Wiki 深度整合 |
| **字数** | ≥ 600 字（正文，不含 frontmatter） |  |
| **结构完整** | 有类型必要节（见 W9 §三） | person 须有生平+叙事意义；event 须有经过+后果 |

### 快速排除（以下情况跳过）

- quality 字段不是 `featured`
- 为章节页（id 以 `三体I-/三体II-/三体III-` 开头）
- 上次 H22 扫描时已评估且写入队列（避免重复）

---

## 三、执行流程

### 步骤 1 · 扫描 featured 页，计算得分

```python
import re
from pathlib import Path

pages_dir = Path('wiki/public/pages')
chapter_prefix = ('三体I-', '三体II-', '三体III-')
candidates = []

for f in pages_dir.glob('*.md'):
    if any(f.stem.startswith(p) for p in chapter_prefix):
        continue
    text = f.read_text(encoding='utf-8')
    # 检查 quality: featured
    if not re.search(r'^quality:\s*featured', text, re.M):
        continue

    # 计算各项指标
    pn_count = len(re.findall(r'（[1-3]-\d{2}-\d{3}）', text))
    wikilinks = len(re.findall(r'\[\[.+?\]\]', text))
    has_related = '## 相关词条' in text
    # 叙事分析：含"意义""地位""评价""作用""象征""影响"等关键词的段落
    has_analysis = bool(re.search(r'(意义|叙事地位|历史评价|象征|作用|影响|命运反讽|宇宙学意义)', text))
    # 正文字数（去 frontmatter）
    body = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
    prose_chars = len(body.replace(' ', '').replace('\n', ''))

    score = (
        (pn_count >= 6) +
        has_analysis +
        (wikilinks >= 4) +
        (prose_chars >= 600) +
        has_related
    )
    candidates.append({
        'slug': f.stem,
        'score': score,
        'pn': pn_count,
        'wikilinks': wikilinks,
        'analysis': has_analysis,
        'prose': prose_chars,
        'related': has_related
    })

# 按得分排序，取前 20 个
top = sorted([c for c in candidates if c['score'] >= 4], key=lambda x: -x['score'])
print(f"Premium 候选（score≥4）共 {len(top)} 页，展示前 20：")
for c in top[:20]:
    print(f"  {c['slug']:30s} score={c['score']} PN={c['pn']} wikilinks={c['wikilinks']} prose={c['prose']}")
```

### 步骤 2 · 对候选逐页评估缺口

对 score=4（缺一项）的候选，确认缺的是哪一项：

```python
# 对每个 score=4 候选输出缺口
for c in top[:20]:
    if c['score'] == 4:
        gaps = []
        if c['pn'] < 6: gaps.append(f"PN不足（{c['pn']}<6）→ A2 enrich-page 补引文")
        if not c['analysis']: gaps.append("缺叙事分析节 → A2 prose优先路径")
        if c['wikilinks'] < 4: gaps.append(f"wikilink不足（{c['wikilinks']}<4）→ H24 词汇链接化")
        if c['prose'] < 600: gaps.append(f"正文偏短（{c['prose']}<600字）→ A2 enrich-page")
        if not c['related']: gaps.append("缺相关词条节 → H5 add-related")
        print(f"  {c['slug']}: {'; '.join(gaps)}")
```

### 步骤 3 · 写入 housekeeping_queue.md

对评估后确认的候选，写入 H-P2 队列：

```
- [ ] H22 premium-enrich | 叶文洁 | featured，PN=5（差1）→ 补1条引文可达premium
- [ ] H22 premium-enrich | 罗辑 | featured，缺叙事分析节 → prose优先路径补段落
- [ ] H22 premium-enrich | 程心 | featured，wikilink=3 → H24词汇链接化
```

每次写入 **5-10 条**，不超过 10 条（避免队列膨胀）。

### 步骤 4 · 记录本次扫描

在 `wiki/logs/butler/actions.jsonl` 中记录（通过 `record_action.py`）：

```bash
python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --instance $INSTANCE \
    --type H22-premium-scan \
    --page "" \
    --result accept \
    --desc "H22精品页增补扫描：共${TOTAL}页featured，发现${FOUND}个premium候选，写入${WRITTEN}条H-P2" \
    --reflect "score分布：5分=${CNT5}页，4分=${CNT4}页；最常见缺口：${TOP_GAP}" \
    --skip-lock-check
```

---

## 四、执行动作映射

H22 只识别候选，不执行内容编辑。队列中的 `H22 premium-enrich` 项由以下动作处理：

| 缺口类型 | 执行动作 |
|---------|---------|
| PN 不足（差 1-2 条） | A2 enrich-page（corpus路径，专门补引文） |
| 缺叙事分析节 | A2 enrich-page（prose优先路径） |
| wikilink 不足 | H24 词汇链接化 |
| 缺相关词条节 | H5 add-related |
| 正文偏短（<600字） | A2 enrich-page（corpus路径） |

---

## 五、与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| W3 | premium 标准基于 W3 质量层级，H22 是 featured→premium 的升级通道 |
| W9 | W9 发现类型级别的结构缺口，H22 针对单页做精细评估 |
| W2 A2 | H22 写入队列后，由 W2 A2 执行实际内容补充 |
| H24 | wikilink 不足时转交 H24 处理 |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H22 候选写入 H-P2
- `wiki/logs/butler/actions.jsonl` — H22 扫描记录
