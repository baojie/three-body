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

---

## 第4次 Dream（R609）

- [R609 提案 / 待批准] `H20: pn-audit-scan`：批量扫描页面 PN 格式（正则`（\d+-\d+-\d+）`），检测格式错误（括号类型/范围超限）及疑似错误编号，违规写入 housekeeping_queue H-P2；不修改页面本身。WU=5/页，batch_n=40。移植自 shiji-kb `SKILL_W10l`，适配三体 B-CC-PPP 格式（B∈{1,2,3}，CC∈01-50，PPP∈001-350）。来源：reflect 中5次提及早期页面缺PN/PN质量参差不齐。
- [R609 提案 / 待批准] `W1-rule: A1-shortage-fast-switch`：discover_wanted 有效 A1 候选（命中≥2且页面不存在）<5 时，跳过混合动作评估，直接切 H2 整轮（25页×40WU=1000WU）。来源：R596/R601/R594 三次出现A1候选不足→混合拼凑效率低于整轮H2。

**补充提案（R611 幸存者W5分析）**：

- [R611 提案 / 待批准] `H21: scan-label-conflicts`：扫描全库 pages，找出 label≠id 且 label 存在于 alias_index 的页面，写入 H-P2 修复任务。来源：R594/R601/R606 三次触发 label 字段冲突，每次均靠手动发现；WU=2/页，触发频率每 29 轮，批量处理。
- [R611 提案 / 待批准] `D3: thematic-catalog`：当 discover_wanted 枯竭（有效候选 <5）时，一次性对语料库按 7-10 个主题组（太空技术/人物/历史军事/物理概念等）批量 corpus_search，生成 100-150 个候选写入 queue.md P3，预期够用 15-20 轮，避免每轮重复手动扩展。来源：R597/R599/R602/R608 四次描述枯竭后手动语义扩展，固定模式但无规范记录。
- [R611 提案 / 待批准] 引入 `SKILL_W10c_词汇链接化` → H22: scan-unlinked-entities：扫描正文中出现的实体词（alias_index 命中），补充未加 `[[]]` 的 wikilink。来源：shiji-kb skill_borrow_watchlist 高优先级候选，Three-Body 已有 500 页 alias_index，移植成本低。
