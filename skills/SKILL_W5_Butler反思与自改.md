---
name: skill-butler-5
description: 三体 Wiki Butler 的反思与自改机制。周期性扫 actions/failures 日志，识别七类模式（A-G），提案规则修订，维护 quality_rules.md。每次必含跨项目借鉴检查（E）和架构规模检查（G）。本 skill 不修订自己（改 W5 必须人工）。每次反思 ≤ 3 条规则修订。
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
# 反思 YYYY-MM-DD（round=NNNN）

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

## 修订清单（<=3 条，不含 skill 借鉴和 G 类架构提案）
1. [W1/W2 具体修改内容]
2. ...

## 引入的借鉴 skill（不计入修订限额）
- [ ] 移植 [skill 名]：具体步骤/适配点

## quality_rules.md 追加（若有 D 类发现）
- QR-<序号>：[具体规则]

## 已排除
- [一次性偶发错误，不做修订]
```

---

### 步骤 4 · 应用修订

逐条应用（G 类除外），每条记录到 `wiki/logs/butler/skill_changes.md`：

```markdown
2026-04-27  W2 v0.1→v0.2  A2 enrich-page 前置条件放松为"正文 ≤ 20 行"
2026-04-27  W3 质量规则   新增 QR-001：person 页 standard 级必须有"命运"节
```

若有 G 类架构提案 → **暂停 loop，展示提案，等待用户 review**。

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

- **每次反思 <=3 条规则修订**（skill 借鉴另计，G 类另计）
- **优先改阈值，次之改流程，最后改结构**
- **不改 W0 的六个不变量**——那是契约，只能人工 review
- **不改 W5 自己**——自改自容易死循环，W5 升级需用户 review
- **G 类架构提案必须暂停等用户确认**——架构变动影响全局

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
