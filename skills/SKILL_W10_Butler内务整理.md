---
name: skill-butler-10
description: 三体 Wiki Butler 内务整理——定义 H1-H10 十类内务任务、触发条件、执行步骤、housekeeping_queue.md 维护规则。内务任务不创建新内容，只修复/提升现有页面质量。
---

# SKILL W10: 内务整理

> 内务（Housekeeping）是质量的守护者。Butler 的工作不只是"加内容"，还要定期扫描整个 wiki，修复缺陷，填补漏洞，让整体质量随时间稳步提升。

---

## 一、内务任务类型表（H1–H10）

| 代码 | 名称 | 触发信号 | 优先级 |
|------|------|---------|--------|
| H1 | fix-links | 页面有 broken `[[TARGET]]`，TARGET 页已存在（需修正链接）| H-P1 |
| H2 | enrich-stub | stub 页面正文 < 100 字，corpus 有更多内容 | H-P2 |
| H3 | add-quote | standard 页面无 PN 引文，corpus 有代表性段落 | H-P2 |
| H4 | add-alias | broken link TARGET 与现有页面是同一概念，需加 alias | H-P2 |
| H5 | add-related | 页面无 `## 相关词条` 节，或相关节为空 | H-P2 |
| H6 | quality-audit | 随机抽查 5 页，逐项 Q-check，记录问题 | H-P3 |
| H7 | add-section | standard 页面缺少某类型的必要节（见 W3 第五节）| H-P2 |
| H8 | cross-link | 两页内容高度相关但互不链接 | H-P2 |
| H9 | update-description | description 字段为空或"（待补充）"| H-P2 |
| H10 | housekeeping-scan | 全库扫描，发现上述问题写入 housekeeping_queue.md | H-P3（每11轮） |

---

## 二、H10 全库扫描（每 11 轮触发）

H10 是内务整理的"发现"入口，本身不修改任何页面，只填充 `housekeeping_queue.md`。

### 执行步骤

```bash
# Step 1: 找 broken links（需创建 stub → queue.md P2）
python3 wiki/scripts/butler/discover_wanted.py --top 20

# Step 2: 找 stub 页面
python3 - << 'PYEOF'
import json
data = json.load(open('wiki/public/pages.json'))
stubs = [p for p in data.get('pages', []) if p.get('quality') == 'stub']
for s in stubs[:10]:
    print(f"H2 enrich-stub | {s['id']} | stub页，正文待补充")
PYEOF

# Step 3: 找无相关词条节的页面
grep -rL "## 相关词条" wiki/public/pages/*.md | head -10 | xargs -I{} basename {} .md | sed 's/^/H5 add-related | /'

# Step 4: 找 description 为空或待补充的页面
grep -rl "description: （待补充）\|description: ''\|description: \"\"" wiki/public/pages/*.md | head -10 | xargs -I{} basename {} .md | sed 's/^/H9 update-description | /'
```

### 写入 housekeeping_queue.md

每次 H10 扫描后，将发现的问题按优先级写入 `wiki/logs/butler/housekeeping_queue.md`：

```markdown
## H-P1 — 立即内务
- [ ] H1 fix-links | 宇宙社会学 | 3处 broken link（[[罗辑]]已建，需修正大小写）

## H-P2 — 常规内务
- [ ] H2 enrich-stub | 宇宙闪烁 | stub页，corpus有5段相关内容
- [ ] H3 add-quote | 黑暗森林法则 | standard页无PN引文
- [ ] H5 add-related | 光速飞船 | 无相关词条节
- [ ] H9 update-description | 冬眠技术 | description为"（待补充）"
```

去重规则：同一页面同一类型问题，只保留 1 条；已标 [x] 不重复写入。

---

## 三、各 H 任务详规

### H1 · fix-links

**前置**：页面有 `[[TARGET]]` 但 TARGET 无对应页面 → 且实际上 TARGET 只是链接写法问题（大小写/繁简/别名）

**步骤**：
1. 读取页面，找所有 `[[...]]`
2. 对每个 TARGET 检查：
   - TARGET 页面是否存在（区分大小写）
   - TARGET 的别名是否有匹配的现有页面
3. 若有别名匹配 → 修改 `[[TARGET]]` 为 `[[正确页面名|TARGET]]`
4. 若无任何匹配 → 加入 queue.md P2 stub（不是本轮任务）

**diff 上限**：≤ 5 行

---

### H2 · enrich-stub

**前置**：页面 quality = stub + corpus 有该词条内容

**步骤**：
1. 读现有页面（确认是 stub）
2. `corpus_search.py "PAGE" --max 15 --context 3`
3. 从结果提炼 2 个正文节（背景 + 作用/意义）
4. 追加到页面末尾（保留已有内容）

执行后页面应达到 basic 级（正文 ≥ 200 字）。

**diff 上限**：≤ 25 行

---

### H3 · add-quote

**前置**：页面 quality ≥ standard + 无 PN 引文 `（B-CC-PPP）`

**步骤**：
1. `corpus_search.py "PAGE" --max 10 --context 120`
2. 选 1 段最具代表性的原文（≤ 200 字），记录 PN
3. 追加 `## 原文片段` 节（若已有则追加到该节下）

**diff 上限**：≤ 10 行

---

### H4 · add-alias

**前置**：broken link TARGET + corpus 确认 TARGET 与某现有页面是同一概念

**步骤**：
1. 确认 TARGET 在 corpus 中确实是同一概念的不同叫法
2. 在现有页面 frontmatter 的 `aliases:` 中追加 TARGET
3. 不修改正文

**diff 上限**：1 行

---

### H5 · add-related

**前置**：页面无 `## 相关词条` 节，或该节为空

**步骤**：
1. 读取页面，找所有 `[[wikilink]]`（正文中的）
2. 整理出 3–6 个最相关的词条
3. 追加或补充 `## 相关词条` 节

**diff 上限**：≤ 8 行

---

### H6 · quality-audit（随机抽查）

**触发**：每次 W5 反思时强制执行；也可在 H-P3 队列中周期触发

**步骤**：
```python
import json, random
from pathlib import Path
data = json.load(open('wiki/public/pages.json'))
pages = [p['id'] for p in data.get('pages', [])]
sample = random.sample(pages, min(5, len(pages)))
for p in sample:
    print(p)
```

对每个抽样页面过 W3 Q1–Q7 检查，记录问题，写入 H-P2 任务。

---

### H7 · add-section

**前置**：页面缺少其类型必须的正文节（见 W3 第五节）

**步骤**：
1. 确认页面 type 和现有节
2. 找出缺失的必要节（如 person 缺"背景"节）
3. `corpus_search.py "PAGE" --max 10` 找依据
4. 追加缺失节（内容来自 corpus）

**diff 上限**：≤ 20 行

---

### H8 · cross-link

**前置**：页面 A 正文提到了页面 B（但没有 `[[B]]` 链接），且 B 也没链接 A

**步骤**：
1. 在页面 A 正文中找到提及 B 的位置
2. 把裸文字改为 `[[B]]` wikilink（首次出现即可）
3. 只做 A→B（单向，本轮）

**diff 上限**：≤ 3 行

---

### H9 · update-description

**前置**：frontmatter description 为空 / `（待补充）` / 少于 10 字

**步骤**：
1. 读取页面正文导语
2. 从正文提炼一句话 description（≤ 50 字，含书册+身份+作用）
3. 编辑 frontmatter description 字段

**diff 上限**：1 行

---

## 四、housekeeping_queue.md 维护规则

- **新增**：H10 扫描后追加；每次 W5 quality-audit 后追加
- **完成**：执行完毕后将 `- [ ]` 改为 `- [x] ✓ YYYY-MM-DD`
- **去重**：同一页面同一 H 类型问题只保留 1 条（新扫描不重复写入已有未完成条目）
- **清理**：每次 H10 扫描时，清除 7 天前已完成（[x]）的条目（保持文件简洁）

---

## 五、内务 vs 内容任务的平衡

Butler 不应把所有精力投入内务整理，以下比例供参考：

| 当前状态 | 内务占比 | 内容创建占比 |
|----------|---------|------------|
| stub > 40% | 50% | 50% |
| stub 20–40% | 30% | 70% |
| stub < 20% | 20% | 80% |

内务任务通过 housekeeping_queue.md 的 H-P2 插入频率（每 round % 3 == 0）自然调节。

---

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W1 探索与队列](SKILL_W1_Butler探索与队列.md)
- [W2 原子行动](SKILL_W2_Butler原子行动.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md)
- [W5 反思与自改](SKILL_W5_Butler反思与自改.md)
