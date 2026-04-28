---
name: skill-butler-5
description: 三体 Wiki Butler 的反思与自改机制。周期性扫 actions/failures 日志，识别八类模式（A-H），提案规则修订，维护 quality_rules.md。每3次W5触发一次Dream Round（H类）：从 reflect 语料归纳动作库空白，提案新的 W2 原子动作或 H 内务动作。本 skill 不修订自己（改 W5 必须人工）。每次反思 ≤ 3 条规则修订。
---

# SKILL W5: 反思与自改

> Butler 的进化发生在这里。W5 是规则层的大脑——它扫描数据、识别模式、提案改进，让 Butler 随时间变聪明。

---

## 一、触发条件

| 触发 | 条件 | 可否跳过 |
|---|---|---|
| **强制周期** | `round_counter.txt % 29 == 0` | **否** |
| **距上次过久** | `(当前 round - 上次 W5 round) > 50` | **否** |
| **连续失败** | actions.jsonl 最近 3 条同 type 均 fail | 否 |
| **手动** | 用户指示 `/reflect butler` | 否 |

触发时**本轮不做原子 action**，整轮用于反思。

---

## 二、反思流程（六步）

### 步骤 1 · 收集素材

```bash
tail -50 wiki/logs/butler/actions.jsonl
cat wiki/logs/butler/failures.jsonl 2>/dev/null | tail -20
cat wiki/logs/butler/queue.md
cat wiki/logs/butler/housekeeping_queue.md 2>/dev/null
cat wiki/logs/butler/round_counter.txt
ls wiki/logs/butler/reflections/ 2>/dev/null | tail -5
cat wiki/logs/butler/quality_rules.md 2>/dev/null
```

---

### 步骤 2 · 模式识别（七类，每次必查 A-G）

#### A. 失败聚集

- 同 action type 连续失败 → 前置条件太松？应禁用？
- 同页面类型反复 fail → W2 规则对该类型不适用？
- 查 failures.jsonl，找高频失败模式

#### B. 成功未规则化

- 某类操作反复成功且页面质量明显提升 → 应写进 W2 常规流程
- 某类 H 任务效率极高 → 应提高 housekeeping_queue 中的优先级

#### C. 阈值失调

- queue.md 积压超 50 条未处理 → W1 探索频率是否过高
- stub 页占全库 > 40% → discover 任务是否过多，应转向 H2 enrich
- housekeeping_queue 积压 > 20 条 → H-P2 插入频率是否过低

#### D. 随机质量抽查（每次必做）

随机抽取 5 个页面（recent 3 + random 2）逐项 Q-check：

```python
import json, random
from pathlib import Path

actions = []
try:
    for line in open('wiki/logs/butler/actions.jsonl'):
        try:
            a = json.loads(line)
            if a.get('page'): actions.append(a['page'])
        except: pass
except: pass

recent3 = list(dict.fromkeys(reversed(actions)))[:3]
all_pages = [p.stem for p in Path('wiki/public/pages').glob('*.md')
             if not p.stem.startswith('三体')]
random2 = random.sample(all_pages, min(2, len(all_pages)))
sample = list(dict.fromkeys(recent3 + random2))[:5]
for p in sample: print(p)
```

每个页面检查（7 项）：

| # | 检查项 | 通过标准 |
|---|--------|----------|
| Q1 | frontmatter 必要字段 | id/type/label/description 均存在且非空 |
| Q2 | type 字段合法 | 在 W3 定义的合法 type 列表中 |
| Q3 | books 字段 | 至少有一个 [三体I/II/III] |
| Q4 | 无捏造内容 | 核心事实断言可在 corpus_search 中找到依据 |
| Q5 | wikilink | >= 1 个 `[[...]]`（stub 豁免） |
| Q6 | 相关词条节 | 有 `## 相关词条`（standard+ 页面） |
| Q7 | PN 格式合法 | 若有 PN，格式为 `（B-CC-PPP）` |

问题分类处理：
- 单页偶发 → 加入 housekeeping_queue.md H-P2 直接修复
- >= 2 页同类问题 → 写入修订提案 + 追加到 quality_rules.md

#### E. 跨项目技能借鉴检查（每次必做）

扫描 shiji-kb butler skills，对比三体 wiki 当前能力：

```bash
ls /home/baojie/work/knowledge/shiji-kb/skills/ | grep SKILL | sort
ls /home/baojie/work/knowledge/three-body/skills/ | sort
```

每次评估 <= 5 个 shiji-kb skill（按 mtime 从新到旧）：

| 评估维度 | 说明 |
|----------|------|
| 功能描述 | 这个 skill 解决什么问题？ |
| 三体适用性 | 三体 wiki 是否有相同/类似痛点？ |
| 移植成本 | 需改哪些路径/字段？复杂度如何？ |
| 优先级 | 高/中/低 |

**决策规则**：
- 适用性高 + 移植成本低 → **立即提案**（不计入 <=3 条修订限额）
- 适用性中/成本高 → 写入 `wiki/logs/butler/skill_borrow_watchlist.md`
- 已排除 → 写入"已排除"节，避免重复评估

#### F. 编辑错误检查

检查近期 actions 中是否出现以下已知错误类型：

- `record_action.py --round R17`（字符串而非整数）→ 提醒使用整数
- 捏造 PN 编号 → 检查近期 add-quote 的 PN 是否可在 corpus_search 验证
- 覆盖已有页面内容（不是追加）→ 检查 diff 是否有删除行

发现任何 F 类错误 → 立即写入修订提案，在 W2 对应动作的"后置检查"中加入防范规则。

---

#### F2. Wikify 标注边界正确性检查（每次 W5 必做）

历史教训：`肯`（单字）作为"肯博士"别名，导致全三册 106 章共 186 处"肯定/不肯"被错误链接；`黑洞` 匹配"黑洞洞的枪口"。

**核心思路**：alias 越短，误匹配风险越高。把所有短 alias 按风险分层，优先核查高危项，低危项进入白名单免检。

##### 风险分层

| 层级 | 判断标准 | 策略 |
|------|----------|------|
| 🔴 **禁止**（代码拦截）| 单字符 alias | `wikify_chapters.py` 已硬编码拒绝，无需手动检查 |
| 🟠 **高危**（每次必查）| 2 字 alias 且属于"常用词"：动词/形容词/副词/代词，或是更长常用词的前缀 | `corpus_search` 验证所有命中是否均指向正确实体 |
| 🟡 **中危**（抽查）| 2 字 alias 为人名缩写或专有名词简称 | 每 3 次 W5 抽查 1 次 |
| 🟢 **低危（白名单）**| 以下任一：① 3 字及以上 alias；② 2 字但已过往 W5 核查通过；③ alias == id（无别名，原名即 alias）| 写入白名单，跳过重复核查 |

##### 高危 alias 识别规则

2 字 alias 符合下列任一条件 → 标记为高危：

1. alias 是常见动词/形容词语素，单独使用时有独立含义（"威慑"、"冬眠"、"视界"、"知青"、"倒计时"）
2. alias 是更长常用词的前缀（"黑洞" ⊆ "黑洞洞"；"批斗" ⊆ "批斗会"）
3. alias 末字在中文中常被重叠使用（洞→洞洞、星→星星、点→点点）

##### 每次 W5 的执行步骤

```python
import json
from pathlib import Path

data = json.loads(Path("wiki/public/pages.json").read_text())
pages = data["pages"]

# 加载白名单
whitelist_path = Path("wiki/logs/butler/alias_whitelist.json")
whitelist = json.loads(whitelist_path.read_text()) if whitelist_path.exists() else []

# 提取所有 2 字非 ASCII alias（排除白名单）
candidates = []
for pid, info in pages.items():
    if info.get("type") == "chapter":
        continue
    for alias in info.get("aliases", []):
        if (isinstance(alias, str) and len(alias) == 2
                and not alias.isascii() and alias not in whitelist):
            candidates.append((alias, pid))

# 按"高危"优先排序（可扩展更细的评分）
print(f"待核查 2 字 alias：{len(candidates)} 个")
for alias, pid in sorted(candidates)[:20]:  # 每次最多核查 20 个
    print(f"  [{alias}] → {pid}")
```

对每个高危候选：
```bash
python3 wiki/scripts/butler/corpus_search.py "<alias>" --max 15
```

**判断标准**：
- 全部命中均为目标实体语境 → 写入白名单 `alias_whitelist.json`，下次跳过
- 有任意一条命中是无关语境 → **立即**从该页面 frontmatter 删除此 alias，并扫描章节页面修复已有错误链接

##### 白名单维护

文件：`wiki/logs/butler/alias_whitelist.json`（字符串数组）

```json
["史强", "大史", "史队", "罗辑", "汪淼", "程心", "智子", "水滴", "冬眠",
 "威慑", "文革", "知青", "歌者", "蓝星", "古筝", "钢印"]
```

规则：
- 通过本轮 corpus_search 核查的 2 字 alias → append 到白名单
- 发现误匹配的 alias → 从 frontmatter 删除（不加白名单，已删除）
- 白名单条目不得超过 100 个；超过时做一次批量 corpus_search 复核，清理过时条目

##### 检查后报告格式

在 W5 反思文件的 F 节追加：

```markdown
### F2 wikify 边界检查
- 本次核查 2 字 alias：N 个
- 新加白名单：[alias1→pid, ...]
- 发现高危并移除：[alias1→pid（原因：命中"XX"为误匹配）]
- 跳过（白名单）：N 个
```

#### H. Dream Round — 动作库自生成（每 3 次 W5 触发一次）

> 普通 W5 修订现有动作的参数；Dream Round 问的是另一个问题：**"是否存在一类反复出现的需求，但当前 W2/H 动作库里没有合适的动作来覆盖它？"**

**触发条件**：每 3 次 W5 反思触发一次（计数写入反思文件头部 `dream_round_counter`），或用户手动 `/dream butler`。

**Dream Round 固定步骤 0：队列归档**

Dream Round 开始时，**必须先**运行队列清理，将 `[x]` 已完成条目归档到 `done.md`：

```bash
python3 wiki/scripts/butler/cleanup_queue.py
```

- `queue.md` 中的 `[x]` → 追加到 `wiki/logs/butler/queue_done.md`
- `housekeeping_queue.md` 中的 `[x]` → 追加到 `wiki/logs/butler/housekeeping_done.md`
- 原文件只保留 `[ ]`（待处理）和 `[~]`（进行中）条目，结构标题保留
- 归档后在反思报告开头记录：`已归档 N 条 → queue_done.md`

**输入素材**（在步骤 1 基础上额外提取）：

```python
import json
from collections import Counter
from pathlib import Path

# 1. 提取所有 reflect 字段
reflects = []
fails = []
try:
    for line in open('wiki/logs/butler/actions.jsonl'):
        try:
            r = json.loads(line)
            if r.get('reflect'):
                reflects.append({'r': r['round'], 'type': r.get('type',''),
                                  'result': r.get('result',''), 'reflect': r['reflect']})
            if r.get('result') == 'fail':
                fails.append(r)
        except: pass
except: pass

# 2. 统计 reflect 中高频关键词（找未满足的需求）
from collections import Counter
words = []
for r in reflects:
    words += r['reflect'].split()
print("高频词 top20:", Counter(words).most_common(20))

# 3. 列出所有 fail 的 type 分布
fail_types = Counter(r.get('type','') for r in fails)
print("fail by type:", fail_types.most_common())

# 4. 列出当前 W2 已有 action type
import subprocess
result = subprocess.run(['grep', '-h', '^| H[0-9]\\|^### [A-H][0-9]',
    'skills/SKILL_W2_Butler原子行动.md'], capture_output=True, text=True)
print("现有动作:", result.stdout[:800])
```

**归纳问题（用这三个问题逐一审视 reflect 语料）**：

| 问题 | 找什么 |
|------|--------|
| "反复需要但没有动作" | reflect 里频繁出现某个操作描述（如"补充人物关系图谱"），但 W2 里没有对应 action |
| "每次手动做的重复步骤" | reflect 里有固定句式（如"顺手修了 X 处 broken link"），说明这个操作隐含在其他 action 里但应独立 |
| "fail 有规律的前置空白" | 某 action type 的 fail 总是同一原因，说明缺少一个"准备型"前置动作 |

**提案格式**（写入 Dream Round 提案节，每次最多 2 个新动作）：

```markdown
## Dream Round 提案（R<N>，第 <K> 次 Dream）

### 提案新动作：[代码] `action-name`（W2 X 组 / H 组）

**来源信号**：
- reflect 中出现 <N> 次类似描述："[具体文字]"
- 或：fail 记录中 <N> 次因"[原因]"失败

**建议规格**：
```
前置条件：[条件]
步骤：[1-3步]
后置检查：[检验]
diff 上限：[行数]
```

**归入**：W2 [X 组] / housekeeping_queue H[N] 类
**等待用户批准后写入 W2/W10**
```

**Dream Round 的保守原则**：
- **每次最多提案 2 个新动作**（避免膨胀）
- **不自动写入 W2/W10**，必须用户 review 后才能落地
- **同一需求在 reflect 中至少出现 3 次**才有资格提案（避免一次性需求固化成规则）
- **提案过于复杂（步骤 > 5 步）的不写**，先拆解

**Dream Round 已提案记录**（累积，防止重复提案）：

写入 `wiki/logs/butler/dream_proposals.md`，每条格式：
```
- [R<N> 提案 / 待批准] action-name：[一句话描述]
- [R<N> 批准 / 已入 W2] action-name：[一句话描述]
- [R<N> 已排除] action-name：[排除原因]
```

---

#### G. 架构提案与规模检查

评估 wiki 整体规模与结构健康：

```bash
ls wiki/public/pages/*.md | grep -v "三体[I]" | wc -l
python3 wiki/scripts/compute_quality.py --report 2>/dev/null | grep -E "stub|basic|standard|featured"
python3 wiki/scripts/butler/discover_wanted.py --top 30 2>/dev/null | head -20
```

架构检查维度：

| 维度 | 健康阈值 | 触发提案的信号 |
|------|---------|--------------|
| 总页面数 | 增长趋势 | 连续 3 次反思无新页面 → 建议加大 create 频率 |
| stub 占比 | < 30% | > 40% → 建议增加 H2 任务频率 |
| featured 占比 | > 10% | < 5% 且总页 > 30 → 建议 add-quote 专项轮次 |
| 三部曲覆盖 | 各册均有 | 某册 wanted > 10 → 建议专项发现轮 |

G 类提案可包括：
- 新增 skill（如发现某类操作需要新 H 类型）
- 调整 W0 周期参数
- 调整 W1 trail/explore 阈值

**G 类提案需用户 review**（自动暂停并展示提案）。

---

### 步骤 3 · 提案

写 `wiki/logs/butler/reflections/YYYY-MM-DD_RNNNN_W5.md`：

```markdown
# 反思 YYYY-MM-DD（round=NNNN，第 <K> 次 W5，dream_round=是/否）

## 素材
- actions 最近 50 条（R<A>–R<B>），fail <n> 条
- queue.md: P1=<n> P2=<n> | housekeeping_queue: H-P1=<n> H-P2=<n>
- 上次反思：<日期/轮次>

## 模式识别

### A 失败聚集
（空 = 本次未发现）

### B 成功规则化
（空 = 本次未发现）

### C 阈值
- queue.md P2 积压：<n> 条
- stub 占比：<n>%

### D 随机质量抽查
- 抽样页面：[5 页名]
- Q1–Q7 通过率：<n>/5
- 发现问题：[具体描述]
- 处理：[直接修复 / 写入提案 / 写入 quality_rules.md]

### E 跨项目借鉴
- 本次评估：[最多5个 skill 名]
- 建议引入：[skill 名] — 理由：[一句话]
- 记入 watchlist：[skill 名] — 原因：[高成本/低适用]
- 已排除：[skill 名] — 原因：[三体无此需求/已有类似]

### F 编辑错误
（空 = 本次未发现）

### G 架构检查
- 总页面：<n>（较上次 +<n>）
- stub 占比：<n>%，featured 占比：<n>%
- 待建（discover top 5）：[列出]
- 提案：[若有架构建议] → **需用户 review**

### H Dream Round（仅当 dream_round=是 时填写）
- 扫描 reflect 语料：共 <N> 条，高频词：[top 5]
- fail 分布：[type → 次数]
- 提案新动作 1：[action-name] — 来源：reflect 中出现 <N> 次"[描述]"
- 提案新动作 2：[action-name] — 来源：[同上]
- 不足 3 次信号、已排除：[列出]

## 修订清单（<=3 条，不含 skill 借鉴、G 类架构、H 类 Dream 提案）
1. [W1/W2 具体修改内容]
2. ...

## Dream Round 提案（不计入修订限额，需用户 review 后落地）
- [ ] 新动作 [action-name]：[规格草稿，归入 W2 X 组 / H 组]

## 引入的借鉴 skill（不计入修订限额）
- [ ] 移植 [skill 名]：具体步骤/适配点

## quality_rules.md 追加（若有 D 类发现）
- QR-<序号>：[具体规则]

## 已排除
- [一次性偶发错误，不做修订]
```

---

### 步骤 4 · 应用修订

逐条应用（G 类和 H Dream 类除外），每条记录到 `wiki/logs/butler/skill_changes.md`：

```markdown
2026-04-27  W2 v0.1→v0.2  A2 enrich-page 前置条件放松为"正文 ≤ 20 行"
2026-04-27  W3 质量规则   新增 QR-001：person 页 standard 级必须有"命运"节
2026-05-10  W2 新增 A3    Dream R87: add-infobox 动作（用户批准后落地）
```

若有 G 类架构提案 → **暂停 loop，展示提案，等待用户 review**。

若有 H Dream 提案 → 将提案写入 `wiki/logs/butler/dream_proposals.md`，状态标 `待批准`，**不暂停 loop**（继续正常工作），下次用户查看时再确认。

---

### 步骤 5 · quality_rules.md 写回

将 D 类发现的系统性质量规则追加到 `wiki/logs/butler/quality_rules.md`：

```markdown
## 规则 QR-<N>（YYYY-MM-DD 从 W5 R<round> 反思）

**适用类型**：[type]
**问题**：[描述问题]
**规则**：[具体规则]
**来源**：R<round> W5 反思，抽查 N 页中 M 页缺失
```

---

### 步骤 6 · 更新 watchlist 与健康快照

```bash
# 更新 skill_borrow_watchlist.md（移除已决策，追加新候选）

# 写健康快照到 health_report.jsonl
python3 - << 'PYEOF'
import json, datetime
from pathlib import Path

pages = list(Path('wiki/public/pages').glob('*.md'))
try:
    data = json.load(open('wiki/public/pages.json'))
except:
    data = {}
quality_dist = {}
for p in data.get('pages', []):
    q = p.get('quality', 'stub')
    quality_dist[q] = quality_dist.get(q, 0) + 1

snapshot = {
    "date": datetime.date.today().isoformat(),
    "round": int(open('wiki/logs/butler/round_counter.txt').read().strip()),
    "type": "w5-reflect",
    "total_pages": len(pages),
    "quality": quality_dist,
}
with open('wiki/logs/butler/health_report.jsonl', 'a') as f:
    f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')
print("health snapshot written")
PYEOF
```

---

## 三、保守原则

- **每次反思 <=3 条规则修订**（skill 借鉴另计，G 类另计，H Dream 类另计）
- **优先改阈值，次之改流程，最后改结构**
- **不改 W0 的六个不变量**——那是契约，只能人工 review
- **不改 W5 自己**——自改自容易死循环，W5 升级需用户 review
- **G 类架构提案必须暂停等用户确认**——架构变动影响全局
- **H Dream 提案不暂停 loop，但不自动落地**——写入 `dream_proposals.md` 待用户批准；批准前 Butler 可先在 queue.md 加一条"实验性"任务测试该动作
- **Dream 提案同一信号至少 3 次才提案**——避免单次观察固化为规则

---

## 四、跨项目技能借鉴专项说明

### shiji-kb skills 候选池（初始评估）

| skill | 功能 | 三体适用性 | 建议 |
|-------|------|-----------|------|
| `SKILL_W10_内务整理` | H1-H20 内务任务调度 | **高** | 已引入（本 W10） |
| `SKILL_W3_质量标准` | 质量等级定义与升级路径 | **高** | 已引入（本 W3） |
| `SKILL_W9_页面图式反思` | 检查页面结构是否符合模板 | 中 — 待页面数 > 100 | watchlist |
| `SKILL_W11_概念分类元反思` | type 字段一致性检查 | 中 — 三体 type 已规范 | watchlist |
| `/map` | 地图裁切 | **不适用** — 三体无地图资源 | 已排除 |

watchlist 初始内容：`wiki/logs/butler/skill_borrow_watchlist.md`

---

## 五、相关文件

- [W0 总则](SKILL_W0_Butler总则.md)
- [W1 探索与队列](SKILL_W1_Butler探索与队列.md)
- [W2 原子行动](SKILL_W2_Butler原子行动.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md)
- [W10 内务整理](SKILL_W10_Butler内务整理.md)
- `wiki/logs/butler/reflections/` — 反思输出
- `wiki/logs/butler/skill_changes.md` — 修订 changelog
- `wiki/logs/butler/skill_borrow_watchlist.md` — 跨项目借鉴候选池
- `wiki/logs/butler/quality_rules.md` — 质量规则 KB
- `wiki/logs/butler/health_report.jsonl` — 健康快照时间线
- `wiki/logs/butler/failures.jsonl` — 失败记录
- `wiki/logs/butler/dream_proposals.md` — Dream Round 提案池（待批准/已批准/已排除）
