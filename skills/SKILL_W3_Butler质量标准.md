---
name: skill-butler-3
description: 三体 Wiki Butler 质量标准——定义 stub/basic/standard/featured 四级质量等级、每级升级条件、Q-check 自评清单、质量驱动的行动选择策略。
---

# SKILL W3: 质量标准

> 质量是 Butler 的"终态"目标——每个页面都应随时间从 stub 爬升到 featured。本 skill 定义什么算好、怎么衡量、何时升级。

---

## 一、四级质量阶梯

| 级别 | 标准名 | 核心特征 | quality_score 参考 |
|------|--------|----------|--------------------|
| `stub` | 存根 | 仅有 frontmatter + 1 句描述，正文实质内容 < 100 字 | 0–15 |
| `basic` | 基础 | 有 1–2 个正文节，内容 ≥ 200 字，至少 1 个 wikilink | 16–30 |
| `standard` | 标准 | 有 ≥ 2 个正文节，内容 ≥ 400 字，≥ 2 wikilinks，有相关词条节 | 31–50 |
| `featured` | 精品 | 内容 ≥ 600 字，≥ 3 个正文节，≥ 1 条原文引用（PN），≥ 3 wikilinks | 51+ |

**注**：`quality` 和 `quality_score` 字段由 `compute_quality.py` 自动计算，Butler 无需手动修改。但 Butler 应知道当前页面处于哪一级，以决定下一步行动。

---

## 二、升级路径

```
stub → basic    ：A2 enrich-page（补正文，使正文 ≥ 200 字，加 2 个 h2 节）
basic → standard：A2 enrich-page + C3 add-alias（确保链接可达）+ D1 discover（补链）
standard → featured：B1 add-quote（原文引用 ≥ 1 条 PN）+ B2 add-pn-citations（行内引文 2–3 处）
```

---

## 三、Q-check 自评清单（每轮执行后必过）

执行完 W2 动作后，对目标页面逐项检查：

| # | 检查项 | 通过标准 | 失败处理 |
|---|--------|----------|----------|
| Q1 | frontmatter 必要字段 | id / type / label / description 均存在且非空 | fail 本轮，不 git add |
| Q2 | type 字段合法 | 在 person/concept/law/technology/weapon/event/organization/place/civilization/book 中 | fail |
| Q3 | books 字段存在 | 至少有一个书册 [三体I/II/III] | fail |
| Q4 | 无捏造内容 | 每个事实断言能在 corpus_search 结果中找到依据 | fail |
| Q5 | wikilink 格式正确 | `[[词条]]` 格式，无空 [[]] | fail |
| Q6 | 相关词条节 | 页面末尾有 `## 相关词条` 节（stub 豁免） | skip（加入 housekeeping_queue） |
| Q7 | PN 来源合法 | 若有 PN 引文，格式为 `（B-CC-PPP）` 且来自 corpus_search | fail（若 PN 捏造） |

Q1–Q4 为**硬检查**（fail → 不 git add，记 fail）。
Q5–Q7 为**软检查**（失败 → skip，加入 housekeeping_queue H-P2 待修复）。

---

## 四、质量驱动行动策略

在 W1 选任务时，参考当前质量分布：

```bash
python3 wiki/scripts/compute_quality.py --report 2>/dev/null | head -20
```

### 阈值与策略

| featured+standard 占比 | 策略 | 每轮重心 |
|------------------------|------|---------|
| < 10% | 深度优先 | 60% enrich/add-quote，40% create |
| 10%–30% | 均衡 | 50/50 |
| > 30% | 广度优先 | 30% enrich，70% create |

### stub 占比预警

- stub 占全库 > 40% → housekeeping_queue 补充 H2 enrich-stub 任务（优先消化 stub）
- stub 占全库 < 10% → 可放宽 create 新页面的频率

---

## 五、页面类型特有质量要求

### person（人物）

| 字段/节 | 要求 |
|--------|------|
| description | 必须包含"出场书册 + 身份 + 核心作用"三要素 |
| 正文 | 必须有"背景"或"人物简介"节 |
| wikilink | 至少链接到 1 个相关概念/组织词条 |
| 历史结局节（QR-001）| standard 级核心人物（跨书册或贯穿多章节）须有"历史结局"或"命运反讽"节，记录最终命运及历史意义 |

### concept / law（概念/法则）

| 字段/节 | 要求 |
|--------|------|
| description | 一句话包含"定义 + 在《三体》宇宙中的意义" |
| 正文 | 必须有"定义"或"核心前提"节 |
| 原文引用 | featured 级必须有 ≥ 1 条 PN 引文 |

### weapon / technology（武器/科技）

| 字段/节 | 要求 |
|--------|------|
| 正文 | 必须有"技术原理"或"外形特征"节 |
| 作战效果 | 若为武器，须有"使用/影响"节 |

---

## 六、quality_rules.md 写回

W5 反思后，若发现某类型页面系统性缺陷，将具体规则追加到：

```
wiki/logs/butler/quality_rules.md
```

格式：
```markdown
## 规则 QR-001（2026-04-27 从 W5 R29 反思）

**适用类型**：person
**问题**：大量人物页缺少"命运/结局"节
**规则**：person 页面 standard 级以上必须有"命运"或"结局"节
**来源**：R29 W5 反思，抽查 5 页中 3 页缺失
```

Butler 每轮执行 Q-check 后，同时比对 `quality_rules.md` 中的自定义规则。

---

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W2 原子行动](SKILL_W2_Butler原子行动.md)
- [W5 反思与自改](SKILL_W5_Butler反思与自改.md)
- [W6 编辑原则](SKILL_W6_编辑原则.md) — 废话三类 + 可读性扣分标准
- [W10 内务整理](SKILL_W10_Butler内务整理.md)
