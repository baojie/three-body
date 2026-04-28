---
name: skill-butler-10
description: 三体 Wiki Butler 内务整理——定义 H1-H25 二十五类内务任务、触发条件、执行步骤、housekeeping_queue.md 维护规则。内务任务不创建新内容，只修复/提升现有页面质量。
---

# SKILL W10: 内务整理

> 内务（Housekeeping）是质量的守护者。Butler 的工作不只是"加内容"，还要定期扫描整个 wiki，修复缺陷，填补漏洞，让整体质量随时间稳步提升。

---

## 一、内务任务类型表（H1–H25）

| 代码 | 名称 | WU | batch_n | 触发信号 | 优先级 |
|------|------|----|---------|---------|--------|
| H1 | fix-links | 10 | 50 | 页面有 broken `[[TARGET]]`，TARGET 页已存在（需修正链接）| H-P1 |
| H2 | enrich-stub | 40 | 12 | stub 页面正文 < 100 字，corpus 有更多内容 | H-P2 |
| H3 | add-quote | 20 | 25 | standard 页面无 PN 引文，corpus 有代表性段落 | H-P2 |
| H4 | add-alias | 5 | 100 | broken link TARGET 与现有页面是同一概念，需加 alias | H-P2 |
| H5 | add-related | 10 | 50 | 页面无 `## 相关词条` 节，或相关节为空 | H-P2 |
| H6 | quality-audit | 100 | 5 | 随机抽查 5 页，逐项 Q-check，记录问题 | H-P3 |
| H7 | add-section | 20 | 25 | standard 页面缺少某类型的必要节（见 W3 第五节）| H-P2 |
| H8 | cross-link | 10 | 50 | 两页内容高度相关但互不链接 | H-P2 |
| H9 | update-description | 5 | 100 | description 字段为空或"（待补充）"| H-P2 |
| H10 | housekeeping-scan | 200 | 2 | 全库扫描，发现上述问题写入 housekeeping_queue.md | H-P3（每11轮） |
| H11 | reclassify | 5 | 100 | type 字段与内容明显不符（如概念被标为 person）| H-P2 |
| H12 | add-tags | 5 | 100 | tags 为空或只有 1 个标签，信息量不足 | H-P2 |
| H13 | format-check | 5 | 100 | 缺 `# 标题行`、books 字段为空、YAML 缩进错误 | H-P1 |
| H14 | pn-placement-fix | 15 | 33 | PN 编号放在 blockquote 外面（渲染错位）| H-P1 |
| H15 | deduplicate | 50 | 10 | 两页内容高度重叠，需合并或建立重定向 | H-P1 |
| H16 | add-redirect | 5 | 100 | broken link 明显是现有页面别名，需建立独立重定向页 | H-P2 |
| H17 | coverage-scan | 200 | 2 | 每 37 轮：扫描三部曲章节，发现未建实体，补充 queue | H-P3（每37轮）|
| H18 | stub-triage | 30 | 17 | 重新评估存根优先级，高引用（≥3次）存根升 P1 | H-P3 |
| H19 | books-field | 5 | 100 | books 字段缺失或为空，需从 corpus 判断出场书册 | H-P2 |
| H20 | list-update | 30 | 17 | 列表/索引页（人物列表/技术列表等）未包含最新词条 | H-P2 |
| H21 | wikify-chapter | 20 | 25 | 章节页面有大量裸实体名未链接，一次处理一章多处；名场面用锚点法（见 H21-S）| H-P2 |
| H22 | premium-scan | 100 | 5 | 扫描 featured 页评估 premium 候选，写入 H-P2 队列（每29轮）| H-P3（每29轮）|
| H23 | pn-audit | 100 | 5 | 全库扫描 PN 编号格式/范围，写入 H-P1/H-P2 修复队列（每29轮）| H-P3（每29轮）|
| H24 | wikify | 20 | 25 | 正文裸实体名补充 `[[]]` wikilink（每页补 3-10 处）| H-P2 |
| H25 | list-build | 100 | 5 | 建立缺失的 type=list 汇总页（每37轮）| H-P3（每37轮）|

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

# Step 5 [新]: 找 books 字段为空的页面（H19）
python3 - << 'PYEOF'
import re
from pathlib import Path
for p in sorted(Path('wiki/public/pages').glob('*.md'))[:100]:
    text = p.read_text(encoding='utf-8')
    if re.search(r'^books:\s*\[\]', text, re.MULTILINE) or not re.search(r'^books:', text, re.MULTILINE):
        print(f"H19 books-field | {p.stem} | books字段缺失或为空")
PYEOF

# Step 6 [新]: 找 PN 在 blockquote 外的页面（H14）
grep -n "^（[1-3]-[0-9][0-9]-[0-9][0-9][0-9]）" wiki/public/pages/*.md | head -10 | \
  sed 's|wiki/public/pages/||; s|\.md:.*|H14 pn-placement-fix|' | \
  awk -F: '{print $3 " | " $1 " | PN在blockquote外，渲染错位"}'

# Step 7 [新]: 找 tags 为空的页面（H12）
grep -rl "^tags: \[\]" wiki/public/pages/*.md | head -10 | xargs -I{} basename {} .md | sed 's/^/H12 add-tags | /'

# Step 8 [新]: 找缺 # 标题行的页面（H13）
python3 - << 'PYEOF'
import re
from pathlib import Path
for p in sorted(Path('wiki/public/pages').glob('*.md'))[:100]:
    text = p.read_text(encoding='utf-8')
    # 去掉 frontmatter 后检查第一个 H1
    body = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
    if not re.match(r'^#\s+\S', body.strip()):
        print(f"H13 format-check | {p.stem} | 缺少H1标题行")
PYEOF
```

### 写入 housekeeping_queue.md

每次 H10 扫描后，将发现的问题按优先级写入 `wiki/logs/butler/housekeeping_queue.md`：

```markdown
## H-P1 — 立即内务
- [ ] H1 fix-links | 宇宙社会学 | 3处 broken link（[[罗辑]]已建，需修正大小写）
- [ ] H13 format-check | 冬眠技术 | 缺少H1标题行
- [ ] H14 pn-placement-fix | 叶文洁 | 2处PN在blockquote外

## H-P2 — 常规内务
- [ ] H2 enrich-stub | 宇宙闪烁 | stub页，corpus有5段相关内容
- [ ] H3 add-quote | 黑暗森林法则 | standard页无PN引文
- [ ] H5 add-related | 光速飞船 | 无相关词条节
- [ ] H9 update-description | 冬眠技术 | description为"（待补充）"
- [ ] H12 add-tags | 水滴 | tags为空
- [ ] H19 books-field | 古筝行动 | books字段缺失
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

### H11 · reclassify

**前置**：页面 type 字段与实际内容明显不符

**常见错误**：
- 宇宙法则（如"黑暗森林法则"）标为 concept，应为 law
- 武器/飞船（如"水滴"）标为 technology，应为 weapon
- 组织（如"ETO"）标为 concept，应为 organization
- 事件（如"古筝行动"）标为 concept，应为 event

**步骤**：
1. 读取页面，确认当前 type
2. 对照 CLAUDE.md 中的 type 枚举判断正确类型
3. 修改 frontmatter type 字段（仅此一行）

**diff 上限**：1 行

---

### H12 · add-tags

**前置**：frontmatter `tags:` 为空数组 `[]` 或只有 1 个标签

**步骤**：
1. 读取页面，确认当前标签
2. 根据页面 type 和正文内容，补充 2–4 个有意义标签
3. 标签示例：`[三体文明, 宇宙社会学, 黑暗森林]`、`[人物, 天体物理学家, 反叛者]`
4. 只修改 frontmatter tags 行

**原则**：标签应覆盖 type 分类、所属阵营/概念圈、关键主题

**diff 上限**：1 行

---

### H13 · format-check

**前置**：页面存在以下任一基础格式问题

**检测项**（按严重度排列）：
| 问题 | 修复方式 |
|------|---------|
| 无 `# 页面名` 标题行（frontmatter 后第一行应为 H1）| 在 frontmatter 后插入 `# <label>` |
| `books:` 字段缺失 | 从 corpus 判断出场书册，追加 frontmatter 字段 |
| `books: []` 为空 | 同上 |
| YAML 值未加引号导致解析异常（如含冒号的 description）| 加引号 |

**步骤**：
1. 读取页面
2. 逐项检测上表中的问题
3. 修复**最严重的一项**（本轮只修一项，下轮继续）
4. 用 `edit_page.py` 写入

**diff 上限**：≤ 3 行

---

### H14 · pn-placement-fix

**前置**：页面中存在 PN 编号 `（B-CC-PPP）` 放在 blockquote 外面的情况

**错误模式**（渲染错位）：
```markdown
> 「引用原文」

（1-02-052）     ← ❌ 在 blockquote 外，会渲染为普通段落
```

**正确模式**：
```markdown
> 「引用原文」
> （1-02-052）   ← ✅ 在 blockquote 内最后一行
```

**检测命令**：
```bash
# 找出 PN 在空行之后（即 blockquote 外）的页面
grep -n "^（[1-3]-[0-9]\{2\}-[0-9]\{3\}）" wiki/public/pages/*.md
```

**步骤**：
1. 找出 PN 外置的位置
2. 检查其上方是否有对应的 blockquote
3. 将 PN 行移入 blockquote 内（在最后一个 `> ` 行之后，仍保持 `> ` 前缀）
4. 删除孤立的 PN 行（原位置）

**diff 上限**：≤ 6 行（每次修复 1–2 处）

---

### H15 · deduplicate

**前置**：两个页面描述同一实体/概念，内容高度重叠

**常见场景**：
- "黑暗森林" 和 "黑暗森林法则" 若内容几乎相同
- "三体文明" 和 "三体人" 若指同一概念
- 简称页（如 "ETO"）和全称页（如 "地球三体组织"）各有实质内容

**步骤**：
1. 读取两页，判断重叠程度
2. 决定保留哪一页为"主页"（标准：更规范的名称、更多内容）
3. 将副页的独有内容合并到主页（用 edit_page.py 追加）
4. 将副页改为重定向（`delete_page.py --redirect-to 主页名`）

**diff 上限**：合并内容 ≤ 30 行 + 1 个重定向文件

⚠️ **合并前必须确认**：两页确实指同一概念（用 corpus_search 验证）

---

### H16 · add-redirect

**前置**：存在 broken link，目标明显是某现有页面的别名，但 H4 add-alias 不适用（原页面别名列表已有，或需要独立文件供导航）

**与 H4 的区别**：
- H4 在现有页面 frontmatter 中追加 alias 字段（修改已有文件）
- H16 新建一个独立的 `别名.md` 重定向文件（不修改已有文件）

**步骤**：
1. 确认 TARGET 是某现有页面 SOURCE 的别名
2. 用 `add_page.py` 创建重定向文件：
   ```bash
   python3 wiki/scripts/add_page.py TARGET - \
     --summary "add-redirect: TARGET → SOURCE" --author butler << 'EOF'
   ---
   id: TARGET
   type: redirect
   label: TARGET
   redirect_to: SOURCE
   ---
   
   # TARGET
   
   > 重定向至 [[SOURCE]]
   EOF
   ```
3. 不修改 SOURCE 页面

**diff 上限**：≤ 10 行（新文件）

---

### H17 · coverage-scan（每 37 轮）

**前置**：`round % 37 == 0`（H10 housekeeping-scan 的补充，专注三部曲书册覆盖）

**与 H10 的区别**：H10 扫描 wiki 已有页面的缺陷；H17 扫描 corpus 原文，找 wiki 尚未建页的重要实体

**步骤**：
```python
# Step 1: 随机选一部书，读取其前 N 章
import random, re
from pathlib import Path

books = list(Path('corpus/utf8').glob('*.txt'))
book = random.choice(books)
text = book.read_text(encoding='utf-8')

# Step 2: 提取章节标题和专有名词（用书名号《》和专名号「」）
existing = {p.stem for p in Path('wiki/public/pages').glob('*.md')}
candidates = set()
for m in re.findall(r'「([^」]{2,10})」', text[:50000]):
    candidates.add(m)
for m in re.findall(r'《([^》]{2,12})》', text[:50000]):
    candidates.add(m)

missing = sorted(candidates - existing)
print(f"[coverage-scan] {book.name} 前50k字，未建页候选（{len(missing)}个）：")
for m in missing[:15]:
    print(f"  {m}")
```

**步骤 3**：从候选中选 3–5 个重要实体，写入 `queue.md P2`（不立即执行）

**diff 上限**：只改 queue.md，≤ 10 行

---

### H18 · stub-triage（存根优先排序）

**前置**：`round % 37 == 19`（与 H17 错开，每 37 轮执行一次）

**目标**：确保高引用存根排在 queue.md 前面

**步骤**：
```bash
# 找出当前所有 stub 页及其被引用次数
python3 wiki/scripts/butler/discover_wanted.py --top 30
```

对照输出结果，检查 `queue.md`：
- 若某 stub 被引用 ≥ 3 次，但在 P2 中 → 升级为 P1
- 若某 stub 根本不在 queue 中 → 写入 P1

**diff 上限**：只改 queue.md，≤ 10 行

---

### H19 · books-field

**前置**：页面 frontmatter 中 `books:` 字段缺失，或 `books: []` 为空

**步骤**：
1. 读取页面，确认 books 字段状态
2. 用 corpus_search 搜索该词条，观察搜索结果中的书号（B=1/2/3）
3. 根据命中书号确定出场书册：
   - 1 → 三体I
   - 2 → 三体II
   - 3 → 三体III
4. 修改 frontmatter books 字段（如 `books: [三体I, 三体II]`）

**diff 上限**：1 行

---

### H20 · list-update

**前置**：wiki 中存在列表/索引页（如 `人物列表.md`、`技术列表.md`），且近期新建了该类别的词条但未加入列表页

**触发信号**：H10 扫描时检测到某列表页的最后修改时间比该类别最新词条的创建时间早

**步骤**：
1. 确定需更新的列表页（如 `人物列表`）
2. 读取列表页，找出当前已列出的所有词条
3. 扫描 `pages.json`，找同类型（type=person）的词条中，不在列表页的
4. 将新词条追加到列表页对应分类节中，格式：`- [[词条名]] — 一句话描述`

**diff 上限**：≤ 10 行

---

### H21 · wikify-chapter（单章链接化）

**前置**：某章节页面中大量实体名以裸文字出现，未被 `[[链接]]` 包裹

**适合执剑人**：批量处理多个实体，一次一章，可包含未建页实体（生成 broken link）

**步骤**：
```bash
# Step 1: 查看某章现有 wikilinks（了解覆盖度）
grep -c '\[\[' wiki/public/pages/三体II-42-下部第12节.md

# Step 2: dry-run 查看待添加链接（已建页实体）
python3 wiki/scripts/wikify_chapters.py --chapter 三体II-42-下部第12节 --dry-run

# Step 3: 对未建页实体，用 --entities 补充（如末日战役舰船群）
python3 wiki/scripts/wikify_chapters.py \
    --chapter 三体II-42-下部第12节 \
    --entities 远方号 雾角号 南极洲号 极限号 恒河号 牛顿号 纳尔逊号 \
    --dry-run

# Step 4: 确认无误后去掉 --dry-run 写入
python3 wiki/scripts/wikify_chapters.py \
    --chapter 三体II-42-下部第12节 \
    --entities 远方号 雾角号 南极洲号 极限号 恒河号 牛顿号 纳尔逊号
```

**规则**：
- 一次只处理一章（--chapter 精确匹配章节文件名前缀）
- 每个实体在本章**首次出现**时链接，后续不重复
- `--entities` 里的实体即使无对应页面也会生成 `[[实体名]]`（wiki 显示为待建红链）
- 处理完成后用 `edit_page.py` 记录 revision（wikify_chapters.py 本身不记录）

**WU**：20（每章）

---

### H21-S · 名场面/动作/故事词条的 wikify（锚点法）

**核心原则**：**绝对不修改原文任何可见文字**，只允许给已有文字加链接。

名场面/动作/故事词条（如"叶文洁第一次发射"、"章北海枪杀行动"）在原文中没有固定的单一名词短语，因此不能直接用 wikify_chapters.py 自动匹配。正确方法是**锚点法**：

#### 锚点选择规则

| 类型 | 锚点选取方式 | 示例 |
|------|------------|------|
| **事件有正式名称** | 直接用名称在 aliases 中 | `aliases: [古筝行动]` → 原文"古筝行动"自动链接 |
| **事件无固定名称** | 找原文中最贴近该场景的标志性短语，加入 aliases | `aliases: [向宇宙发出信号]` → 原文该短语自动链接 |
| **场景有代表性引语** | 截取引语中最具识别性的片段作为 alias | `aliases: [黑暗森林法则]` → 或从该法则的表述句中选关键短语 |

#### 操作步骤

```bash
# 1. 在 corpus 中找到该场景的原文标志性短语
python3 wiki/scripts/butler/corpus_search.py "向宇宙发送" --max 5

# 2. 确认该短语在原文中是唯一的、有代表性的
# 3. 在词条页面 frontmatter 中加入该短语作为 alias
#    例：aliases: [叶文洁发射, 向宇宙发送信号]

# 4. 运行 wikify_chapters.py，它会自动把原文中的该短语变为链接
python3 wiki/scripts/wikify_chapters.py --entities 叶文洁发射

# 结果：原文「向宇宙发送信号」变为「[[叶文洁发射|向宇宙发送信号]]」
#       可见文字不变，仅加了链接属性
```

#### 锚点质量标准

- ✅ **好锚点**：原文中唯一出现、语义完整、2–8 字的短语
  - `向宇宙广播了坐标` → 指向"宇宙坐标广播事件"
  - `人造太阳照耀地球` → 指向某具体事件页
- ❌ **坏锚点**：太短（易误匹配）、太通用、不唯一
  - `发射` / `信号` / `事件` → 太短，会误链接其他段落
  - `说` / `走` / `看` → 虚词，无意义

#### ⚠️ Alias 安全规则（防止误链接）

wikify_chapters.py 使用字符串前缀匹配，若 alias 设置不当会产生**严重的系统性误链接**（历史教训：`肯` 作为"肯博士"别名，导致全三册 106 章共 186 处"肯定/不肯"被错误链接）。

**必须遵守**：

| 规则 | 说明 | 反例 |
|------|------|------|
| **alias ≥ 2 个汉字** | 脚本已硬编码拒绝单字符别名 | `肯`→肯博士：误匹配"肯定" |
| **避免叠词末字** | 若 alias 末字 == 紧随字符，为叠词形式不匹配 | `黑洞`→黑洞：误匹配"黑洞洞的枪口" |
| **alias 不得是常用词** | 如"威慑"、"倒计时"作为 alias 会广泛误链接 | `威慑` 在绝大多数语境指抽象概念，非特定页面 |
| **添加 alias 前必须验证** | `corpus_search "alias" --max 20` 检查是否误匹配常见语境 | — |

**添加 alias 的正确流程**：
```bash
# 1. 搜索候选 alias 的所有出现位置
python3 wiki/scripts/butler/corpus_search.py "候选alias" --max 20

# 2. 人工判断：每条命中是否都在指向该词条？
#    若有≥1条命中是无关语境 → 此 alias 不可用

# 3. 通过检验后才加入 frontmatter aliases 字段
```

#### 注意事项

- 若原文短语有歧义（多处出现），**不能**用作 alias（会导致不相关段落被链接）
- wikify_chapters.py 只链接**首次出现**，后续出现保持原样
- 链接格式为 `[[词条名|原始短语]]`，原始短语在页面渲染后完全可见，无任何修改
- 场景页的 aliases 设计需要阅读原文——这是人工判断环节，无法自动化

**WU**：30（锚点设计 + wikify，含阅读原文定位）

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
- [W9 页面图式反思](SKILL_W9_Butler页面图式反思.md)（H22/H23/H25 同轮触发）
- [W10h H22 精品页增补](SKILL_W10h_Butler精品页增补.md)
- [W10l H23 引文PN一致性](SKILL_W10l_Butler引文PN一致性.md)
- [W10c H24 词汇链接化](SKILL_W10c_Butler词汇链接化.md)
- [W10j H25 列表页建设](SKILL_W10j_Butler列表页建设.md)
