---
name: skill-butler-2
description: 三体 Wiki Butler 的原子行动目录——A/B/C/D/E/H 组标准操作的前置条件、执行步骤、后置检查、diff上限。每轮只执行一个动作。禁止自由发挥，只能从此目录选。H 组内务整理任务详规见 W10。
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

## PN 引文系统

每段原文都有全局唯一的 PN 编号，格式 `B-CC-PPP`：
- B = 书号（1=地球往事，2=黑暗森林，3=死神永生）
- CC = 章节序号（书内递增，两位数字）
- PPP = 段落序号（章内递增，三位数字）

**搜索时自动获得 PN**：
```bash
python3 wiki/scripts/butler/corpus_search.py "关键词" --max 10
# 每条结果直接输出 → 引用格式：（1-02-015）
```

**在文章正文中引用**（行内引文，优先使用）：
```markdown
叶文洁目睹父亲被迫害致死（1-02-052），这一经历动摇了她对人类文明的信心。
```

**在原文引用块中标注**：
```markdown
> 「引用原文」

（1-02-052）
```

引文链接由 `pn-citation` 插件自动渲染为可点击跳转链接。**禁止捏造 PN**，必须从 corpus_search 结果中复制。

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

为页面追加一段《三体》原文引用块，**必须附 PN 编号**。

**前置**：PAGE 已存在 + corpus 有该词条相关的精彩段落

**步骤**：
1. 搜索代表性段落（结果直接附 PN）：
   ```bash
   python3 wiki/scripts/butler/corpus_search.py "PAGE" --max 10 --context 120
   ```
2. 选1–2段关键原文（≤ 200字/段），记录其 PN
3. 以 blockquote + PN 引文追加到页面末尾：
   ```markdown
   ## 原文片段

   > 「原文引用」

   （1-02-052）
   ```

**后置检查**：
- 引用内容可在 corpus 搜索结果中原样找到
- PN 编号来自搜索结果，未捏造

**diff 上限**：≤ 10 行

---

### B2 `add-pn-citations PAGE`

在页面叙述性正文中补充 PN 行内引文，提升可溯源性。

**前置**：PAGE 已存在 + 正文有可追溯到原文的具体事件描述

**步骤**：
1. 读取页面，找 2–4 处具体事件陈述（如"叶文洁目睹了……"）
2. 对每处事件用 corpus_search 找到对应原文段落及 PN
3. 在陈述句末尾（句号前）插入 PN 引文 `（B-CC-PPP）`
4. 不修改正文内容，只追加引文标注

**示例**：
```markdown
# 修改前
叶文洁目睹父亲被迫害致死，这一经历动摇了她对人类的信心。

# 修改后
叶文洁目睹父亲被迫害致死（1-02-052），这一经历动摇了她对人类的信心。
```

**后置检查**：每个 PN 都能在 corpus_search 结果中验证内容匹配

**diff 上限**：≤ 8 行

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

# 2. 记 action（--reflect 为每轮一句话观察，必填）
python3 wiki/scripts/butler/record_action.py \
  --round <R> --type <type> --page <PAGE> --result accept \
  --desc "从corpus三体X提炼..." \
  --reflect "一句话观察"

# 3. 在 queue.md 标记 [x]（将 "- [ ]" 改为 "- [x]"）
```

### `--reflect` 填写规范

每轮必须写一句话，记录**这轮执行中真实观察到的信息**，供 W5 反思扫描。

| 场景 | 示例 |
|------|------|
| 语料命中好 | `"corpus_search 命中 18 条，人物形象清晰，覆盖三部书"` |
| 语料稀少 | `"搜索结果仅 3 条，该词条在corpus中出现很少，内容偏薄"` |
| 遇到 broken link | `"发现 [[三体文明]] [[红岸基地]] 2 条 broken link，已加入 queue"` |
| 页面已有内容冲突 | `"原有描述与新搜索结果矛盾，暂只追加，不覆盖"` |
| 执行失败 | `"corpus_search 无结果，无法有源创建，标 fail"` |
| 无特殊观察 | `"正常执行，无异常"` |

**禁止**：空字符串、`"无"`、`"ok"`——这些对 W5 没有价值。

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

叶文洁目睹父亲被迫害致死（1-02-052），这一经历动摇了她对人类的信心。
<!-- ↑ 重要事件陈述后附 PN 引文，引文来自 corpus_search 结果 -->

## 在故事中的作用

## 原文片段

> 「关键段落原文」

（1-02-052）

## 相关词条

- [[词条A]]
- [[词条B]]
```

> PN 引文规则：`（B-CC-PPP）` 全角括号，B=书号，CC=章节序，PPP=段落序。
> 必须从 `corpus_search.py` 结果中复制，禁止猜测或捏造。

---

## E 组 · 章节链接化

### E1 `wikify-chapters`

每次 **新增实体页面后**，重新对章节原文做链接化（幂等操作）。

**触发时机**：create-page / stub 操作完成后，当天第一次即可，无需每轮执行。

**步骤**：
```bash
python3 wiki/scripts/wikify_chapters.py
```

**规则**：
- 每个实体在每章首次出现时链接，后续出现不重复
- 已有 `[[wikilink]]` 不重复处理（幂等）
- PN 标签 `[1-02-001]` 和引文 `（1-02-001）` 不受影响

**diff 上限**：章节文件批量更新，不计入单轮限制；accept 后 `git add wiki/public/pages/三体*.md`

---

---

## H 组 · 内务整理（详规见 W10）

H 组任务来自 `housekeeping_queue.md`，由 W1 三队列选取算法调度。执行规则与记账方式与 A-E 组相同，但 target 为已有页面（不创建新页面）。

| 代码 | 名称 | 简述 |
|------|------|------|
| H1 | fix-links | 修复大小写/别名导致的 broken link |
| H2 | enrich-stub | 为 stub 页补充 corpus 内容 |
| H3 | add-quote | 为 standard 页面补 PN 引文 |
| H4 | add-alias | 为概念补别名（已有页面） |
| H5 | add-related | 补充 `## 相关词条` 节 |
| H6 | quality-audit | 随机抽查 5 页逐项 Q-check |
| H7 | add-section | 补充类型必要节（如 person 的"命运"节）|
| H8 | cross-link | 为互相提及但未链接的页面补 wikilink |
| H9 | update-description | 补充空/占位的 description 字段 |
| H10 | housekeeping-scan | 全库扫描，生成 housekeeping_queue |

**记账时 type 字段使用 `H<n>-<名称>`，如 `H2-enrich-stub`。**

---

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W1 探索与队列](SKILL_W1_Butler探索与队列.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md)
- [W10 内务整理](SKILL_W10_Butler内务整理.md)
