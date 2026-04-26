---
name: skill-butler-1
description: 三体 Wiki Butler 的任务选取与探索策略。定义两大食物源（corpus 原文、broken wikilink）、三队列系统（content/housekeeping）、trail/explore 动态配比。每轮 invocation 按本 skill 选出一个目标，交由 W2 执行。
---

# SKILL W1: 探索与队列管理

> Butler 每轮从队列或探索中选出一个目标。本 skill 规定"选什么、从哪找、如何排优先"——不规定怎么做（W2 负责）。

---

## 一、两大食物源

### 源 A · corpus/ 原文

**路径**：`corpus/utf8/三体I：地球往事.txt`、`corpus/utf8/三体II：黑暗森林.txt`、`corpus/utf8/三体III：死神永生.txt`（UTF-8）

原始 GBK 文件保留在 `corpus/` 供备份，不直接使用。使用 `corpus_search.py` 访问，输出直接附 PN 引文格式。

**探查信号**：
- `discover_wanted.py` 发现 broken link → 该词条大概率在原文有出现 → create
- 现有页面内容稀薄（< 15 行正文）+ corpus 搜索有多个命中段落 → enrich
- 扫 queue.md P3 discover 任务，从原文提取尚未入队的词条名

**消化**：`create-page` / `enrich-page`（见 W2 A/B 组）

### 源 B · Broken Wikilinks

**来源**：`discover_wanted.py` 扫描所有 `[[target]]` 找出无对应页面的 target

**探查信号**：
- 引用次数 ≥ 2 → P1 create 或 P2 stub
- 引用次数 = 1 → P3 stub

**消化**：`stub` / `create-page`（见 W2 C 组）

---

## 二、三队列系统与选取算法

### 队列优先级

```
H-P1（内务紧急） > P1（内容高优） > H-P2（内务常规，每 3 轮插 1 次）> P2（内容中优）> P3（发现型）
```

### 选取算法（每轮执行一次）

```
1. 若 housekeeping_queue.md H-P1 有未完成任务 → 选 H-P1 最上一条
2. 否则若 queue.md P1 有未完成任务 → 选 P1 最上一条
3. 否则若 round % 3 == 0 且 H-P2 有未完成任务 → 选 H-P2 最上一条
4. 否则若 queue.md P2 有未完成任务 → 选 P2 最上一条（trail/explore 按配比）
5. 否则 P2 为空（或 round % 11 == 0）→ 先补货再干活：
   a. 运行 D1 discover（discover_wanted.py --top 20），去重后写入 P2
   b. 运行 H10 housekeeping-scan，写入 housekeeping_queue
   c. 若上述任一有新条目 → 回到步骤 1 重新选取
   d. 若均无新条目 → empty_fallback（W0 第七节）
```

**关键**：P2 一旦清空就主动补货（步骤 5），不等 round 11。round 11 只是额外的强制补货触发，不是唯一触发。

### Trail vs Explore 配比

| P2 队列规模 | trail:explore | 策略 |
|------------|--------------|------|
| > 10 条    | 3:1          | 消费队列为主 |
| 5–10 条    | 2:1          | 平衡（默认）|
| < 5 条     | 1:1          | 加大探索 |
| = 0 条     | 全 explore   | 仅探索 |

**trail** = 从现有页面出发，处理 broken link / 丰富稀薄页
**explore** = 运行 discover_wanted.py 或扫描 corpus 找新词条

看 `actions.jsonl` 最后 (比例分母) 条的 `mode` 字段决定本轮 trail 还是 explore。

---

## 三、入队规则

每轮可 **discover 1–3 条候选** 写入 queue.md，但本轮只执行 1 条。

- **P1 条件**：broken link 被引用 ≥ 3 次，或主角人物（叶文洁/罗辑/程心/章北海/汪淼）的关键关联词条
- **P2 条件**：broken link 被引用 1–2 次，或 corpus 扫描发现的重要概念
- **P3 条件**：全局扫描类探索任务（discover）

去重：同一 target + 同一动作类型，只入一次。

---

## 四、discover_wanted 结果转入队列示例

```bash
python3 wiki/scripts/butler/discover_wanted.py --top 15
```

输出：
```
4x  执剑人
4x  水滴探测器
3x  面壁者
```

转入 queue.md：
```markdown
- [ ] P1 create | 执剑人 | 被4个页面引用，制度概念页
- [ ] P1 create | 水滴探测器 | 被4个页面引用，三体武器
- [ ] P2 create | 面壁者 | 被3个页面引用，人类战略制度
```

---

## 五、W1 输出格式（交给 W2）

```json
{
  "target": "执剑人",
  "action": "create-page",
  "source": "corpus + broken-links",
  "mode": "trail",
  "priority": "P1",
  "rationale": "被4个页面引用，corpus中有关键内容"
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
| > 30% | 广度优先 | 30% enrich，70% create |

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
