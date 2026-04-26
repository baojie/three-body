---
name: skill-butler-1
description: 三体 Wiki Butler 的任务选取与探索策略。定义两大食物源（corpus 原文、broken wikilink）、queue.md 三级优先队列、trail/explore 动态配比。每轮 invocation 按本 skill 选出一个目标，交由 W2 执行。
---

# SKILL W1: 探索与队列管理

> Butler 每轮从队列或探索中选出一个目标。本 skill 规定"选什么、从哪找、如何排优先"——不规定怎么做（W2 负责）。

---

## 一、两大食物源

### 源 A · corpus/ 原文

**路径**：`corpus/三体I：地球往事.txt`、`corpus/三体II：黑暗森林.txt`、`corpus/三体III：死神永生.txt`

**注意**：文件编码为 GB18030，使用 `corpus_search.py` 访问。

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

## 二、三级优先队列

```
P1 (立即处理) → P2 (本周) → P3 (发现型，每11轮)
```

### 选取算法

```
1. 若 P1 中有未完成任务 → 选 P1 最上一条
2. 否则若 round % 11 ≠ 0 → 选 P2 最上一条（trail 或 explore 按配比）
3. 若 round % 11 == 0 → 优先做 P3 discover，再选 P2
4. 所有队列为空 → 运行 discover_wanted.py，将 top 5 加入 P2
```

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

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W2 原子行动](SKILL_W2_Butler原子行动.md)
