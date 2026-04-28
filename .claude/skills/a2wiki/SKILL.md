---
name: a2wiki
description: 将任意文本源（书籍、文档、笔记、语料）转化为结构化 wiki 百科页面。识别并提取三种知识：fact（列表/表格型）、narrative（叙述型实体页）、skill（程序型 how-to 页）。通过 add_page.py 写入 wiki。支持永续迭代模式，自动追踪进度、捕获跨域洞察。
---

# /a2wiki — Anything to Wiki Lite

将任意文本源转化为结构化 wiki 百科页面。支持单次运行和**永续迭代**两种模式。

---

## 核心概念：三种知识类型

在 wiki 中，所有知识都归属三种形态之一。理解这三种类型是本 skill 的基础。

| 类型 | 回答的问题 | 典型内容 | Wiki 呈现 |
|------|-----------|---------|----------|
| **narrative** | 这是什么？它是谁？发生了什么？ | 人物传记、事件经过、地点介绍、概念解释 | 实体百科页（person/concept/event/place/…） |
| **fact** | 有哪些？数据是什么？清单如何？ | 数据表格、属性列表、关系清单、统计数字 | 列表页（list）或任意页内的结构化数据节 |
| **skill** | 怎么做？流程是什么？如何判断？ | 操作步骤、分析框架、决策流程、最佳实践 | 程序型页（concept 类型，结构化步骤正文） |

**判断优先级**：
- 若内容描述"某个实体的完整面貌" → narrative
- 若内容是"若干项目的并列清单/数据" → fact
- 若内容是"完成某件事的步骤" → skill
- 同一来源文本通常同时包含三种类型，分别提取

**MECE 原则**：勘察表应**完全覆盖**来源文本中的所有实体——不仅选"有趣的"，而是穷举。互不重叠，不遗漏。

---

## 两种运行模式

| 模式 | 触发方式 | 特点 |
|------|---------|------|
| **单次模式** | `/a2wiki <文件路径或粘贴文本>` | 处理完整输入，适合短文本（< 10 万字符） |
| **永续迭代模式** | `/a2wiki --loop <文件路径>` | 分批处理长文本，维护进度文件，每批后暂停或继续 |

---

## 执行流程（单次 / 永续通用）

### 步骤 0 · 初始化进度文件（永续模式专用）

永续模式首次启动时，创建进度追踪文件：

```
wiki/logs/a2wiki/<source-slug>/
├── progress.md      # 进度：已处理批次、剩余批次
├── coverage.md      # 勘察表（累积，每批追加）
└── insights.md      # 跨域洞察（eureka，累积）
```

进度文件格式：

```markdown
# a2wiki 进度：<source-slug>

- **来源文件**：<路径>
- **总批次**：N
- **已完成批次**：0 / N
- **已建词条**：0

## 待处理批次

- [ ] 批次1：字符 0–20000
- [ ] 批次2：字符 20000–40000
- …

## 已完成批次

（空）
```

---

### 步骤 1 · 读取源文本

接受以下任何形式的输入：
- 文件路径（`.txt`、`.md`、`.pdf`、`.docx`）
- URL（网页正文）
- 直接粘贴的文本

读完后，**在回复中用一段话概括内容**，确认理解正确再继续。

超过 10 万字符时按段落边界切分为若干批次，每批不少于 2 万字符，依次处理。

永续模式：读进度文件，跳过已完成批次，从下一个未完成批次开始。

---

### 步骤 2 · 勘察：列出知识单元

**每批必做三遍扫描**，分别针对三种知识类型：

**① Narrative 扫描** — 批次中出现了哪些实体？（人物/地点/事件/概念/理论/组织/器物/时代/文本）

**② Fact 扫描** — 批次中是否有多项并列的清单、表格、属性对比、统计数据？

**③ Skill 扫描**（常被遗漏，必须独立完成）— 批次中是否描述了以下任何一种？
- 推理/演绎过程（从前提出发，一步步得出结论，如黑暗森林推导）
- 决策框架（在什么条件下选择A vs B，如执剑人是否触发威慑的判断）
- 策略设计原则（如何构建满足某种约束的方案，如面壁者策略设计）
- 操作/技术方法（执行某件事的步骤或技巧，如双层隐喻编码法）

若 Skill 扫描有命中 → 候选 slug 以方法名或动词短语命名（"X-推导框架"、"如何-设计-Y"），type = skill

产出一张**知识单元勘察表**：

```
| 序号 | 候选标题（wiki slug） | 类型 | 理由摘要（≤30字） |
|------|---------------------|------|-----------------|
| 1    | 某人物名             | narrative | 主角，有传记细节  |
| 2    | 某概念-某事件对比表   | fact   | 多个事件并列属性  |
| 3    | 如何-做某事          | skill  | 含步骤和判断条件  |
```

规则：
- 一个 wiki 页面 = 一个知识单元（slug = 页面文件名，无扩展名）
- 同一实体只列一次（即使文中多次出现）
- **穷举原则**：先列最重要的 10 个，询问用户是否继续全量提取
- 永续模式：将勘察表追加到 `coverage.md`

---

### 步骤 3 · 检查已有页面（三层查重）

对勘察表中的每个候选 slug，依次执行三层检查，任一层命中即为"已存在"：

**批量查重 + 质量扫描（一次运行，输出全部候选决策）**

```python
import json
d = json.load(open('wiki/public/pages.json', encoding='utf-8'))
pages, ai = d['pages'], d.get('alias_index', {})

def check_page(candidate):
    """返回 (match_type, canonical_slug, quality)"""
    def _q(slug):
        return pages.get(slug, {}).get('quality', '?')

    if candidate in pages:
        return 'exact', candidate, _q(candidate)
    if candidate in ai:
        return 'alias', ai[candidate], _q(ai[candidate])
    hits = [(k,v) for k,v in ai.items()
            if (candidate in k or k in candidate) and len(k)>=3]
    if hits:
        slug = max(hits, key=lambda x: len(x[0]))[1]
        return 'fuzzy', slug, _q(slug)
    frags = [candidate[i:i+2] for i in range(len(candidate)-1)]
    scores = {}
    for f in frags:
        for k,v in ai.items():
            if f in k and len(k)>=4:
                scores[v] = scores.get(v,0)+1
    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            return 'fragment', best, _q(best)
    return 'missing', None, None

# 对所有候选批量输出
candidates = ['候选1', '候选2', ...]
for c in candidates:
    match, slug, quality = check_page(c)
    if match == 'missing':
        print(f'[CREATE ] {c}')
    elif quality in ('stub', 'basic'):
        print(f'[ENRICH ] {c} → {slug} [{quality}]')
    else:
        print(f'[SKIP   ] {c} → {slug} [{quality}]')
```

**输出示例**：
```
[CREATE ] 监听部
[ENRICH ] 红岸系统 → 红岸系统 [basic]
[SKIP   ] 叶文洁 → 叶文洁 [featured]
[SKIP   ] 乱纪元 → 乱纪元 [featured]
```

**层3 · 内容归属检查**（防止子概念重复建页，仅对 MISSING 候选执行）

若候选是某 featured 页的一个已有章节，不单独建页：
```bash
grep -rl "<关键词>" wiki/public/pages/*.md
```

**判断结果**：
- `[CREATE]`（三层未命中，层3也无归属）→ `add_page.py`
- `[ENRICH]`（quality = stub/basic）→ Read 已有页面，按步骤4策略增补
- `[SKIP]`（quality = standard/featured）→ 内容大概率已覆盖，仅在有明确新内容时精准追加，否则直接跳过

---

### 步骤 4 · 逐页生成内容

按勘察表顺序，对每个知识单元：

1. 确定 wiki `type`（见下方"页面类型映射"）
2. 按 create / enrich 分支处理（见下方策略）
3. 执行写入命令

#### create 分支

撰写完整 frontmatter + 正文（见下方三种模板），执行：

```bash
python3 wiki/scripts/add_page.py <SLUG> - --summary "<一句话说明>" --author a2wiki << 'EOF'
<frontmatter+正文>
EOF
```

#### enrich 分支（已有页面的四种策略）

**先 Read 已有页面，判断 quality，再选策略**：

| 已有 quality | 新来源信息量 | 操作 |
|-------------|------------|------|
| `stub`（< 5行正文） | 充足 | **替换**：用新内容完整重写，质量升级 |
| `basic` | 有新节或新引文 | **增补**：在现有结构末尾插入新节，原有节不动 |
| `standard` / `featured` | 有 1-2 处补充 | **精准追加**：仅在最相关的节内加引文或句子 |
| `standard` / `featured` | 与现有内容重复 | **跳过**：写 `skip` 到 coverage.md，不执行写入 |

**核心原则**：`edit_page.py` 是全页替换，不是 append。增补时须先在内存中合并（Read → 插入新节 → 写回完整文件），不得用新内容覆盖来源中未涉及的已有内容。

```bash
python3 wiki/scripts/edit_page.py <SLUG> - --summary "<一句话说明>" --author a2wiki << 'EOF'
<合并后完整页面>
EOF
```

每页写入后，`git add wiki/public/pages/<SLUG>.md`。

---

### 步骤 5 · 捕获跨域洞察（insights.md）

每批处理完毕，审阅本批内容，判断是否有值得记录的**跨域洞察**：

**合格的洞察必须满足以下条件之一**：
1. 识别出跨越多个实体/领域的交叉模式
2. 揭示看似无关概念之间的意外联系
3. 提出可复用的结构性原则
4. 提出重新构建理解的根本性问题

**不合格**：内容的直接应用、重复已知事实、单领域内的观察。

大多数批次不会产生洞察——这是正常的，不更新就是正确行为。质量重于数量。

将合格洞察追加到 `wiki/logs/a2wiki/<source-slug>/insights.md`：

```markdown
## <洞察标题>

<一句话核心观点。>[<来源批次>]
```

---

### 步骤 6 · 更新进度（永续模式专用）

```markdown
# 更新 progress.md：
- [ ] → [x] 标记当前批次已完成
- 更新"已建词条"计数
- 写入本批次摘要（新建N页，丰富M页，洞察K条）
```

若还有未完成批次 → 询问用户是否继续（或在自动模式下直接继续）。

所有批次完成后，输出汇总报告：
```
✓ <source-slug> 全量处理完成
  - 总批次：N
  - 新建词条：X
  - 丰富词条：Y
  - 跨域洞察：Z 条
  - 进度文件：wiki/logs/a2wiki/<source-slug>/progress.md
```

---

### 步骤 7 · 自改（每轮必做）

每轮结束后，**对本轮执行过程做一次反思**，找出一个具体可改进的地方，并立即写回本 SKILL.md。

**反思问题**（回答其中一个）：
- 本轮有没有漏检的重复页？漏检原因是什么？步骤3能补哪个规则？
- 有没有某个判断花了很长时间？能写成更快的检查规则？
- 有没有创建了事后发现不值得的页面？勘察表的过滤标准应该收紧哪里？
- 有没有遗漏了明显应该建页的实体？MECE 覆盖哪里有盲点？
- 有没有页面内容质量偏低？模板或质量标准哪里需要调整？

**改进写入格式**：每轮在 `.claude/skills/a2wiki/CHANGELOG.md` 追加一条记录：

```markdown
## R<批次号> · <YYYY-MM-DD> · <一句话改进描述>

**问题**：<本轮发生了什么具体问题，要有复现场景>
**改进**：<修改了SKILL.md的哪个步骤，加入了什么规则>
**无改进时**：写 `R<批次号> · <日期> · 无改进（原因：<一句话>）`
```

每轮只改一处，不求完美，只求持续进步。改进日志见 `CHANGELOG.md`。

---

## 页面类型映射

### 知识类型 → Wiki type

| 知识类型 | 适用场景 | Wiki type 建议 |
|---------|---------|--------------|
| narrative — 人物 | 真实或虚构的个体，有传记信息 | `person` |
| narrative — 概念 | 抽象思想、理论、原则 | `concept` |
| narrative — 事件 | 有时间线的历史/情节事件 | `event` |
| narrative — 地点 | 真实或虚构的地理位置 | `place` |
| narrative — 组织 | 机构、团体、派别 | `organization` |
| narrative — 技术/器物 | 发明、设备、工具、方法 | `technology` |
| narrative — 时代/纪元 | 历史阶段、时间段 | `era` |
| narrative — 文本 | 书籍、典籍、文件 | `book` |
| fact — 独立清单页 | 多个实体的属性对比 | `list` |
| fact — 内嵌表格 | 嵌入 narrative/skill 页中的数据节 | （任意 type，表格在正文中） |
| skill — 操作流程 | 步骤性知识，有明确"如何做" | `skill` |

---

## 模板一：Narrative 页面

```markdown
---
id: <slug>
type: <见类型映射>
label: <中文显示名>
aliases: [<别名1>, <别名2>]
tags: [<标签>]
description: <一句话描述，回答"这是什么"，≤50字>
books: [<来源文本名>]
quality: stub
---
# <显示名>

<开篇段：1-2句定位这个实体在来源文本中的角色或意义。>

## <核心章节1>

<正文段落，包含从来源文本中提取的关键信息。>

> <引用原文（如有原文可引用时使用）>
> （<来源标注>）

## <核心章节2>

<...>

## 相关词条

- [[<关联词条1>]]
- [[<关联词条2>]]
```

**质量标准**：
- `stub`：只有定义段，< 5 行正文
- `basic`：有 2+ 节，有 1+ 引文，≥ 15 行
- `standard`：有 3+ 节，有 3+ 引文，≥ 30 行
- `featured`：有 5+ 节，引文充实，内容权威，≥ 60 行

---

## 模板二：Fact 页面（独立列表页）

```markdown
---
id: <slug>
type: list
label: <中文显示名>
aliases: []
tags: [<标签>]
description: <一句话描述，说明这张表覆盖了什么范围>
books: [<来源文本名>]
quality: standard
---
# <显示名>

<1-2句说明本页面的内容范围和来源。>

## <分组标题1>

| 字段A | 字段B | 字段C |
|------|------|------|
| 值   | 值   | 值   |

## <分组标题2>

- **项目1**：说明
- **项目2**：说明

## 相关词条

- [[<关联词条>]]
```

**何时使用独立 list 页面**：当同类实体超过 5 个且有可比属性时，单独建页；否则将表格嵌入相关 narrative 页的某一节。

---

## 模板三：Skill 页面（程序型知识）

```markdown
---
id: <slug>
type: skill
label: <中文显示名>
aliases: []
tags: [<标签>]
description: <一句话描述，说明"在什么情境下执行这个流程"，≤50字>
books: [<来源文本名>]
quality: standard
---
# <显示名>

<开篇段：说明这个流程的目标和适用场景。>

## 前提条件

- <执行此流程需要满足的条件>

## 步骤

### 1. <步骤名>

<说明>

### 2. <步骤名>

<说明>

### 3. <步骤名>

<说明>

## 决策点

**如果 <条件A>** → <执行路径A>

**如果 <条件B>** → <执行路径B>

## 预期结果

- <完成后应达到的状态>
- <可验证的输出>

## 相关词条

- [[<关联词条>]]
```

---

## Wikilink 规范

所有页面中，出现其他已知实体时使用 `[[词条名]]` 格式内链。不要内链外部 URL。

若显示名与 slug 不同：`[[slug|显示文字]]`。

---

## 批量执行策略

当知识单元 > 10 个时，按以下优先级排序依次执行：

1. **核心实体的 narrative 页**（人物、核心概念）— 最先建立，其他页面可以链接到它们
2. **重要事件的 narrative 页**
3. **Fact 列表页**（通常依赖 narrative 页已建立）
4. **Skill 页面**（最后，因为通常引用大量其他页面）

每批最多处理 **10 个页面**，写完一批后暂停，展示结果并询问是否继续。

---

## 质量自检

每页写入前，对照以下清单检查：

- [ ] frontmatter 字段完整（id / type / label / description 必填）
- [ ] description 不超过 50 字，不含 frontmatter 之外的内容
- [ ] 正文有至少一个内链 `[[...]]`
- [ ] 无捏造内容——所有事实均可追溯至来源文本
- [ ] 对于 narrative 页：有明确的开篇定位段
- [ ] 对于 skill 页：有编号步骤，有预期结果

---

## 永续迭代模式详解

永续迭代模式将 a2wiki 变成一个可以持续运行的 Butler 实例，逐章处理整本书。

### 状态机

```
INIT → READING → SURVEYING → WRITING → INSIGHT → PROGRESS → READING（下一批）
                                                     ↓（全部完成）
                                                   DONE
```

### 每轮目标

- 处理 1–3 个章节（约 2–5 万字符）
- 新建/丰富 5–15 个页面
- 捕获 0–2 条跨域洞察
- 更新进度文件

### 与 Butler 集成

若在 Butler 工作流中调用：

- `--author` 使用 Butler 实例名（如 `幸存者`）
- 每页写入后 `git add wiki/public/pages/<SLUG>.md`
- 批量完成后通过 `record_action.py` 记账（type: `create-page` 或 `enrich-page`）
- 未处理的批次写入 `wiki/logs/butler/queue.md`（P2 优先级，格式：`- [ ] [P2] a2wiki <source-slug> 批次<N> create`）
- 进度文件存放在 `wiki/logs/a2wiki/<source-slug>/`

### 断点续传

下次调用 `/a2wiki --loop <文件路径>` 时，自动读取 `progress.md`，从上次中断处继续：

```bash
# 检查是否有未完成的 a2wiki 任务
ls wiki/logs/a2wiki/
cat wiki/logs/a2wiki/<source-slug>/progress.md
```

---

## 不适合生成 wiki 页面的内容

以下内容**跳过，不建页**：

- 过渡性叙述（"下一节我们将讨论……"）
- 作者的主观评价/读后感（除非评价本身是知识点）
- 索引、目录、版权页
- 重复段落（已有内容的近似重述）
- 信息量不足以支撑独立词条的零散提及（文中仅一两字带过）
