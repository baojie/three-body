---
name: skill-butler-2
description: 三体 Wiki Butler 的原子行动目录——8种标准操作的前置条件、执行步骤、后置检查、diff上限。每轮只执行一个动作。禁止自由发挥，只能从此目录选。
---

# SKILL W2: 原子行动目录

> 每轮从本目录选一种动作执行。选哪种由 W1 决定。执行后必须 W3 自评（accept/fail）并记账。

---

## 通用约定

- 每轮 **只做一个页面** 的一个操作
- 写入 diff ≤ 30 行（新建页面例外，但仍尽量 ≤ 60 行）
- accept → `git add wiki/public/pages/<PAGE>.md`（暂存但不 commit）
- fail → 停止，记 fail，进入下一轮
- **每轮结束必须**调用 `record_action.py` 写 `actions.jsonl`

---

## A 组 · 页面创建

### A1 `create-page PAGE`

**前置**：wiki/public/pages/PAGE.md 不存在 + corpus 中可搜索到该词条

**步骤**：
1. 搜索语料
   ```bash
   python3 wiki/scripts/butler/corpus_search.py "PAGE" --max 15 --context 3
   ```
2. 从结果提炼：身份/定义、出场书册、关键事件/作用、关联词条
3. 写入 `wiki/public/pages/PAGE.md`，格式见下方模板
4. 页面最少包含：frontmatter + 1段导语 + 2个正文节 + 相关词条

**后置检查**：
- frontmatter 含 id/type/label/description
- 无捏造内容（每个断言能在 corpus 搜索结果中找到依据）
- 至少 2 条 `[[wikilink]]` 指向已有页面

**diff 上限**：≤ 60 行（新页面）

---

### A2 `enrich-page PAGE`

**前置**：PAGE 已存在 + 正文 ≤ 15 行实质内容 + corpus 有更多信息

**步骤**：
1. 读现有页面：`cat wiki/public/pages/PAGE.md`
2. 搜索更多内容：
   ```bash
   python3 wiki/scripts/butler/corpus_search.py "PAGE" --max 20 --context 4
   ```
3. 找出缺失的节（背景/关键事件/影响/性格分析/相关等）
4. 追加一个新节，不替换任何已有内容

**后置检查**：已有内容完整保留，新节有原文依据

**diff 上限**：≤ 25 行

---

## B 组 · 引文与原文

### B1 `add-quote PAGE`

为页面追加一段《三体》原文引用块。

**前置**：PAGE 已存在 + corpus 有该词条相关的精彩段落

**步骤**：
1. 搜索代表性段落：
   ```bash
   python3 wiki/scripts/butler/corpus_search.py "PAGE" --max 10 --context 5
   ```
2. 选1–2段关键原文（≤ 200字/段）
3. 以 blockquote 追加到页面末尾：
   ```markdown
   ## 原文片段
   
   > 「原文引用」
   >
   > ——《三体II：黑暗森林》
   ```

**后置检查**：引用内容可在 corpus 搜索结果中原样找到

**diff 上限**：≤ 10 行

---

## C 组 · 存根与链接

### C1 `stub PAGE`

为 broken wikilink 创建最小存根，让断链变有效。

**前置**：PAGE 在 `discover_wanted.py` 输出中 + wiki/public/pages/PAGE.md 不存在

**步骤**：创建以下内容：
```markdown
---
id: PAGE
type: unknown
label: PAGE
aliases: []
tags: []
description: （待补充）
---

# PAGE

（页面待建设，内容将从《三体》三部曲提取。）

## 相关词条
```

**后置检查**：文件存在，frontmatter 有效

**diff 上限**：≤ 12 行

---

### C2 `fix-links PAGE`

修复页面中的 broken wikilinks。

**前置**：PAGE 存在 + 其中有 broken link（`[[TARGET]]` 但 TARGET 无对应页）

**步骤**：
1. 读取页面
2. 对每个 broken target：
   - 若 target 已有别名可对应现有页面 → 修正链接文字
   - 若 target 完全没有对应页 → 加入 queue.md P2 stub
3. 本轮只修复 broken 链接，不修改其他内容

**后置检查**：修复后的链接目标存在于 pages.json

**diff 上限**：≤ 5 行

---

### C3 `add-alias PAGE ALIAS`

为页面添加别名，让更多链接能正确解析。

**前置**：ALIAS 是 broken link + 在 corpus 中确认与 PAGE 是同一概念

**步骤**：在 PAGE 的 frontmatter `aliases:` 中追加 ALIAS

**diff 上限**：1 行

---

## D 组 · 探索

### D1 `discover`

探索 corpus 或 broken links，发现新词条，写入 queue.md。

**步骤**：
1. 运行：
   ```bash
   python3 wiki/scripts/butler/discover_wanted.py --top 20
   ```
2. 选 5 条尚未在 queue.md 的 wanted pages
3. 按优先级写入 queue.md（≥ 3 引用 → P1，1–2 引用 → P2）
4. 本轮不新建/修改任何 wiki 页面

**diff 上限**：只改 queue.md，≤ 10 行

---

## 自评标准（W3）

每轮执行后自查：

| 结果 | 条件 |
|------|------|
| **accept** | 写入内容有原文依据，格式正确，无捏造 |
| **fail** | 无源断言 / 格式错误 / 写入失败 / 违反不变量 |
| **skip** | 任务已过时（页面已存在且内容充分）|

---

## 记账（每轮必做）

```bash
# 1. 轮次+1
echo $(($(cat wiki/logs/butler/round_counter.txt) + 1)) > wiki/logs/butler/round_counter.txt

# 2. 记 action
python3 wiki/scripts/butler/record_action.py \
  --round <R> --type <type> --page <PAGE> --result accept --desc "从corpus三体X提炼..."

# 3. 在 queue.md 标记 [x]（将 "- [ ]" 改为 "- [x]"）
```

---

## 页面格式模板

```yaml
---
id: 词条名
type: person|concept|law|technology|weapon|event|organization|place|civilization|book
label: 显示名
aliases: [别名1, English]
tags: [标签]
description: 一句话描述（≤50字）
books: [三体I]     # 出场书册
---

# 词条名

导语（1–2句，定义该词条在《三体》宇宙中的角色）。

## 背景

## 在故事中的作用

## 相关词条

- [[词条A]]
- [[词条B]]
```

---

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W1 探索与队列](SKILL_W1_Butler探索与队列.md)
