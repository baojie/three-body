---
name: skill-butler-1
description: 三体 Wiki Butler 的任务选取与探索策略。四食物源（broken links、语料频率、队列手动条目、叙事场景扫描）、三队列系统（content/housekeeping）、trail/explore 动态配比。每轮按本 skill 选出目标，交由 W2 执行。
---

# SKILL W1: 探索与队列管理

> Butler 每轮从队列或探索中选出一个目标。本 skill 规定"选什么、从哪找、如何排优先"——不规定怎么做（W2 负责）。

---

## 一、四大食物源

### 源 A · corpus/ 原文（语料驱动）

**工具**：`corpus_search.py`（搜索特定词）、`discover_corpus.py`（频率扫描全库）

```bash
# 频率扫描：发现语料中高频但未建页的实体（每次用较大的 --top）
python3 wiki/scripts/butler/discover_corpus.py --top 60 --min-freq 2
```

**探查信号**：
- `discover_corpus.py` 输出的舰船名/后缀型/引号型 → 高优先 create
- 现有页面内容稀薄（< 15 行正文）+ corpus 搜索有多个命中段落 → enrich

**消化**：`create-page` / `enrich-page`（见 W2 A 组）

### 源 B · Broken Wikilinks（链接驱动）

**工具**：`discover_wanted.py`（自动 fallback 到语料扫描，见下）

```bash
python3 wiki/scripts/butler/discover_wanted.py --top 60
# 无 broken links 时自动切换到语料频率模式（Phase 2）
```

**探查信号**：
- 引用次数 ≥ 2 → P1 create
- 引用次数 = 1 → P2 stub

**消化**：`create-page` / `stub`（见 W2 C 组）

### 源 C · queue.md 手动条目

queue.md 中可能存在**人工加入的未完成任务**，包括按重要性手动列举的人物/概念/事件。
这些条目可能出现在各种节标题下（"P1 — 新增人物词条"、"P1 — 新增科技词条" 等）。

**⚠️ 关键：扫描 queue.md 时必须遍历整个文件**——不能只看第一个 "P1" 段落。
实现方式：搜索文件内所有 `- [ ] P1` 和 `- [ ] P2` 行，不论它们在哪个 section 下。

### 源 D · 叙事场景扫描（名场面发现）

**工具**：人工阅读 + `corpus_search.py` 验证

名场面不会被 `discover_wanted.py` 发现（没有破碎 wikilink），也不会被 `discover_corpus.py` 高频命中（场景描述词不是高频实体名）。需要通过**叙事记忆**主动识别，再用语料验证。

**识别方法（每次 D2 scene-scan 执行一轮）**：

```
Step 1 · 头脑风暴候选：
  从以下维度各列 3–5 个尚未建页的场景：
  - 三体I 名场面（物理危机、三体游戏、红岸）
  - 三体II 名场面（面壁计划、黑暗战役、章北海）
  - 三体III 名场面（威慑对峙、降维打击、宇宙末年）
  - 人物决策转折点（改变故事走向的单一行动）
  - 视觉冲击性场景（有强烈画面感的描写）

Step 2 · 排除已建页面：
  ls wiki/public/pages/*.md | xargs -I{} basename {} .md | sort

Step 3 · corpus 验证（每个候选）：
  python3 wiki/scripts/butler/corpus_search.py "场景关键词" --max 5
  → ≥ 1 条命中 → 确认，记录 PN
  → 0 命中 → 换关键词重试；仍无 → 跳过

Step 4 · 写入 queue.md P1：
  - [ ] P1 create | 场景名 | 名场面：一句话描述（PN）
  每批写入 10–20 条
```

**优先选取标准**：

| 优先级 | 判断依据 |
|--------|---------|
| P1 | 读者强共鸣场景；改变故事走向的决定性时刻；三部曲中最常被引用/讨论的段落 |
| P2 | 有趣但非决定性的配角场景；游戏关卡中次要情节 |
| 跳过 | 与已有词条高度重叠（已建页面已充分覆盖）；仅是对白，无场景画面 |

**消化**：`create-page`（W2 A1，使用名场面专用模板，见 W2 §名场面模板）

---

## 二、三队列系统与选取算法

### 队列优先级

```
H-P1（内务紧急） > P1（内容高优） > H-P2（内务常规，每 3 轮插 1 次）> P2（内容中优）> P3（发现型）
```

### 选取算法（每轮执行一次）

```
0. 快速扫描 queue.md 全文，找出所有 "- [ ] P1" 行 → p1_pending（不限 section）
   快速扫描 queue.md 全文，找出所有 "- [ ] P2" 行 → p2_pending

1. 若 housekeeping_queue.md 中有 "- [ ] H-P1" 行 → 选最上一条
2. 否则若 p1_pending 不为空 → 选第一条 P1 未完成任务
3. 否则若 round % 3 == 0 且 H-P2 有未完成任务 → 选 H-P2 最上一条
4. 否则若 p2_pending 不为空 → 选第一条 P2 未完成任务
5. 否则若 len(p2_pending) < 5 → 主动补货（不等 round % 11）：
   a. 运行 discover_wanted.py --top 60（自动 fallback 到语料扫描）
   b. 运行 discover_corpus.py --top 60 --min-freq 2（补充语料候选）
   c. 去重后将新候选写入 queue.md 对应优先级段落
   d. 运行 H10 housekeeping-scan，写入 housekeeping_queue
   e. 若任一有新条目 → 回到步骤 0 重新选取
   f. 若均无新条目 → empty_fallback（W0 第七节）
```

**关键**：
- 步骤 0 是每轮开始的强制全文扫描，防止遗漏嵌套在子 section 的未完成任务
- **P2 跌破 5 条就主动补货**（不等 round 11），保持队列充足
- 补货时用更大的 `--top 60` + `--min-freq 2`，捕获更多候选

### Trail vs Explore 配比

| P2 队列规模 | trail:explore | 策略 |
|------------|--------------|------|
| > 20 条    | 3:1          | 消费队列为主 |
| 10–20 条   | 2:1          | 平衡（默认）|
| 5–10 条    | 1:1          | 加大探索 |
| < 5 条     | 0:1 + 主动补货 | 立即触发步骤 5 补货 |

**trail** = 从现有页面出发，处理 broken link / 丰富稀薄页  
**explore** = 运行 discover_wanted.py / discover_corpus.py 找新词条

---

## 三、入队规则

每次补货可写入 **5–15 条候选**（批量写入，保持队列充足）；每轮只执行 1 条（或 1 批同类任务）。

- **P1 条件**：broken link 被引用 ≥ 3 次，或语料频率 ≥ 15 次的舰船/核心概念，或主角关联词条
- **P2 条件**：broken link 被引用 1–2 次，或语料频率 3–14 次的候选
- **P3 条件**：全局扫描类探索任务、语料频率 2 次的低频候选

去重：同一 target + 同一动作类型，只入一次。

---

## 四、discover_wanted / discover_corpus 结果转入队列示例

```bash
# 场景1：有 broken links（加大 --top）
python3 wiki/scripts/butler/discover_wanted.py --top 60
# 输出 → 4x 执剑人 → 写入 P1；其余写 P2/P3

# 场景2：无 broken links（自动语料模式，加大 --top）
python3 wiki/scripts/butler/discover_wanted.py --top 60
# 输出 → 85x 星环号[舰船] → 写入 P1

# 场景3：直接语料扫描（补充，降低频率门槛）
python3 wiki/scripts/butler/discover_corpus.py --top 60 --min-freq 2
```

转入 queue.md（批量追加，每次 5–15 条，保持队列充足）：
```markdown
- [ ] P1 create | 星环号 | R650-D1：语料85次，三体III核心舰船
- [ ] P1 create | 自然选择号 | R650-D1：语料59次，章北海所在战舰
- [ ] P2 create | 群星计划 | R650-D1：语料12次，威慑纪元太空移民计划
- [ ] P2 create | 幸存派 | R650-D1：3x broken link + 3x corpus；三体叛军第三派
- [ ] P3 create | 自由女神像 | R650-D1：2x corpus；希恩斯信念中心场景
```

---

## 五、W1 输出格式（交给 W2）

```json
{
  "target": "自然选择号",
  "action": "create-page",
  "source": "corpus-frequency",
  "mode": "explore",
  "priority": "P1",
  "rationale": "语料59次，章北海所在战舰，三体II核心"
}
```

---

## 六、质量驱动策略

每次启动先查当前质量分布：

```bash
python3 wiki/scripts/compute_quality.py --report
```

### 策略阈值

| 精品+旗舰比例 | 策略 | 每轮配比 |
|-------------|------|---------|
| < 10% | 深度优先 | 60% enrich/add-quote/add-pn-citations，40% create |
| 10%–30% | 均衡 | 各 50% |
| > 30% | **广度优先** | **20% enrich，80% create**（当前状态：65页全精品，应大量创建新页） |

> ⚠️ **当前（2026-04）所有65个实体页均为 featured（精品），比例100%**。
> 必须处于"广度优先"模式，优先消耗 queue.md 中的 create 任务，不应做 enrich-quality。

### 单页提升路径

```
stub     → basic    : enrich-page（正文 ≥500 字 + 2个 h2）
basic    → standard : enrich-page + add-pn-citations
standard → featured : add-pn-citations（≥3 PN）+ add-quote + 补第3个 h2
featured → premium  : 配图（image 字段）+ PN/引文累计 ≥8 条
```

### P1/P2 分配原则

- `quality=stub` 且被 ≥2 页引用 → P1（高优先补全）
- `quality=basic` 有 PN 扩充空间 → P2 enrich
- `quality=standard` 离 featured 只差 PN 数 → P2 add-pn-citations
- 每完成一批 create 后，运行一次 `wikify_chapters.py` 补章节链接

---

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W2 原子行动](SKILL_W2_Butler原子行动.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md)
- [W10 内务整理](SKILL_W10_Butler内务整理.md)
