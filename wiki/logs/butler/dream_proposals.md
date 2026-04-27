# Dream Round 提案池

Butler W5 Dream Round 提案记录。每条包含来源、规格、状态。

格式：
- [R<N> 提案 / 待批准] action-name：描述
- [R<N> 批准 / 已入 W2] action-name：描述
- [R<N> 已排除] action-name：原因

---

## 第1次 Dream（R087）

（无提案——当时 featured 占比仅 30%，动作库已足够覆盖 stub/basic 升级需求）

---

## 第2次 Dream（R203）

- [R203 提案 / 待批准] `B5: audit-score-batch`：批量扫描全库 frontmatter quality_score，修正偏差 >1 的页面（当前 47 页）。规格：脚本扫描→Edit 修正→git add all→重扫确认 0 偏差；diff 上限 20 页/轮；归 W2 B 组。
- [R203 提案 / 待批准] `A6: fix-tags`：为 tags<4 的页面补充到 4 个标签（当前 14 页）。规格：读页面内容→推断 2 个交叉引用标签→更新 frontmatter；1 页/轮；归 W2 A 组。
- [R203 提案 / 待批准] 引入 W8 premium 层级：在 W3 增加 premium 质量级别（score≥65，pn≥6，ql≥8，prose≥1000，h2≥5，wl≥8），为下一阶段提供目标。移植自 shiji-kb SKILL_W8。

---

## 第3次 Dream（R483）

- [R483 提案 / 待批准] `H19: auto-enrich-smallest`：empty_fallback 时扫描最小5个页面，有 corpus 补充空间的加入 H-P2 队列。来源：11次 enrich 中 8 次为空队列期间手动找小页面。
- [R483 提案 / 待批准] `W1-rule: ship-creation-threshold`：舰船页有效提及 >=5 条才建独立页，否则并入父页面（末日战役/星舰地球等）。来源：远方号/雾角号/南极洲号均只有3条过场提及。
