# CHANGELOG — 三体 Wiki

按功能演进阶段记录，每阶段对应若干 git commit。

---

## Phase 1 · 基础骨架

**commits**: `695b320` → `34c3df6`

- 创建仓库，初始化 SPA 前端（`wiki/public/index.html` + CSS + JS）
- 建立 `docs/` 作为 GitHub Pages 发布目录，配置 `publish.sh`
- 确定目录约定：`corpus/`（只读原文）/ `wiki/public/pages/`（词条）/ `docs/`（输出）
- 写入 `CLAUDE.md`，约定禁止 `git add -A`、禁止修改原文等工作规则

---

## Phase 2 · Butler 管家与插件系统

**commits**: `6f8451e` → `94aea36`

- 引入 `/butler` skill：Claude 作为自动化词条编辑管家
- 新增插件系统（`wiki/public/plugins/`），服务端口统一为 1453
- 重构 butler skill：拆分为精简启动器 + `skills/` 文档体系
- 建立语料工具链（原文导入脚本 `import_corpus.py`）

---

## Phase 3 · 原文系统与 PN 引文

**commits**: `1523f71` → `c9ee6cf`

- 将三部曲全文（三体I×37章、三体II×50章、三体III×50章）导入为 Wiki 页面
- 实现 PN（Paragraph Number）引文系统：每段落分配全局唯一编号（格式 `1-02-015`）
- 词条正文中的 PN 标注可点击跳转到原文对应位置
- 新增初批人物与概念词条，建立 `pages.json` 注册表

---

## Phase 4 · 质量体系与修订历史

**commits**: `dba0a2f` → `9d0b89b`

- Butler R1–R16：新增 16 个核心词条，总页数达 160
- 建立五级质量分级制度：存根(0–29) → 基础(30–49) → 标准(50–64) → 精品(65–79) → 旗舰(80+)
- 新增 `record_revision.py`：每次编辑写入 `wiki/public/history/<page>.json`，追加到 `recent.json`
- 新增 `compute_quality.py`：自动计算并写回 frontmatter 的 `quality_score` 字段
- 新增 `import_corpus.py` + `wikify_chapters.py`：原文章节自动加 Wikilink
- 前端重构：新增质量徽章、"跳转原文"按钮、修订历史标签页

---

## Phase 5 · 三队列调度与页面 CRUD

**commits**: `74085ee` → `b2936b0`

- Butler R18–R34：三队列系统（content / quality / housekeeping）完善
- `/wiki` skill：`build_registry → compute_quality → publish.sh → commit → push` 全流程
- 引入质量分重算（每轮 W4 步骤）与 W5 反思机制（每 11 轮）
- 新增页面 CRUD 脚本：`add_page.py` / `edit_page.py` / `delete_page.py`
- `backfill_history.py`：从 git log 回填历史修订记录

---

## Phase 6 · 大规模内容扩充（R58→R204）

**commits**: `e0fe4d0` → `fed72ad`

- R58–R84：新建 4 页，批量修复 16 页 PN 引文格式，3 页升级为 standard
- R85–R119：新建 9 页，all-featured 里程碑（全部词条 score ≥ 50）
- R120–R153：新建 11 页，四维碎块、197 页全精品
- R154–R187：丰富 25 页；掩体计划、宇宙社会学、程心等核心词条完善；所有 202 页 ≥ 50 分
- R188–R204：W5 第 6 次反思，B5 批量修正 47 页 score，所有非章节页 featured ≥ 50 分

---

## Phase 7 · docs 重构与前端修复

**commits**: `8f4769b` → `1c3fe77`

- `docs/` 改用符号链接指向 `wiki/public/`，消除发布时的文件复制
- 首页自动跳转到 Wiki 入口
- 修复 `recent` 自动更新 bug、butler 队列空时的 fallback 逻辑
- 补全 36 页 revision 历史；执剑人、申玉菲、广播纪元等词条更新

---

## Phase 8 · 持续质量提升（R239→R322）

**commits**: `c869c65` → `2f09a04`

- R239–R272：W5 第 8 次反思，19 页内容丰富，score 普遍升至 60+
- R273–R322：批量丰富 42 页词条，score 提升至 65+，补充大量原文引用
- 费米悖论、宇宙闪烁、引力波广播等概念词条达到 68 分

---

## Phase 9 · 知识图谱统计与 quality_score 动态化

**commits**: `e9422d3` → `56aae7b`

- R323–R356：批量丰富 34 页词条，score 全部达 65+，修正 stale frontmatter
- 新增 `compute_knowledge.py`：生成 `knowledge_latest.json` + 时间线，支持统计页展示
- 修复统计页渲染 bug
- **quality_score 动态化**：从写死到 frontmatter 改为 `build_registry` 运行时动态计算，消除污染源
- R358–R361：score 提升至 69，新建面壁者词条「雷迪亚兹」「希恩斯」

---

## Phase 11 · 多 Butler 并发与命名实例体系

**commits**: `(current)`

- **多实例并发**：同时启动多个 butler agent，通过 `claim_task.py` flock 锁保证任务不重复领取
- **`pending_revision.json` 机制**：butler 在 Write/Edit 前写入上下文文件（round / type / desc / author），hook 消费后写入 `recent.jsonl`，`author` 字段从 `hook` 升级为实例名
- **摘要信息化**：recent 记录从无意义的 `"auto: direct Write/Edit (bypassed script)"` 改为 `"R364 create-page 庄颜"` 格式
- **六命名实例**：固定管家角色体系建立
  - 统帅（`--focus all`，通用兜底）
  - 幸存者（`--focus create`）
  - 破壁人（`--focus enrich`）
  - 执剑人（`--focus housekeeping`）
  - 广播员（`--focus publish`）
  - 监听员（`--focus discover`）
- 设计文档写入 `skills/SKILL_Butler多实例设计.md`

---

## Phase 10 · 自动化深化与 JSONL 迁移

**commits**: `0cfe056` → `b3941cd`

- 新增 `discover_corpus.py`：自动从原文扫描尚未建档的实体，填充 W1 内容队列
- **PostToolUse hook**：Write/Edit 写入 `pages/*.md` 时自动触发 `record_revision.py`，无需手动调用
- **recent.jsonl 迁移**：`recent.json` 改为 `recent.jsonl`（O_APPEND 原子追加），每条记录附带 diff 字段，前端直接读取流式格式
- `history/<page>.json` 全部迁移为 `history/<page>.jsonl`（flock 保护，per-page JSONL）
- `rebuild_recent.py`：从 `recent.jsonl` 或 `history/*.jsonl` 重建快照
- butler 并发三脚本（`claim_task.py` / `complete_task.py` / `record_action.py`）支持多 agent 协作
- 新增 `/commit` skill：按内容分组暂存并生成提交消息
- Butler H1–H20 内务任务表 + H17/H18 周期清理计划完善

---

## Phase 11b · 多实例并发机制升级（task锁 → round+page双层锁）

**核心变化**：并发安全机制从任务级锁升级为轮次+页面双层锁，同时切换为批次模式（1000 WU/轮）。

### 锁架构演进

| 旧版（Phase 11） | 新版（Phase 11b） |
|-----------------|-----------------|
| `claim_task.py` flock 防止同一队列任务被重复领取 | `claim_round.py` 原子递增轮号，创建 `round_N.lock` |
| `increment_round.py` 递增计数器（轮号） | `lock_manager.py set-page` 把候选页面注册到轮次锁 |
| `pending_revision.json` 传递 author（竞态风险） | `lock_manager.py check-page` 写前检测跨轮次页面冲突 |
| 每轮 1 页 | 每轮 batch_n=ceil(1000/WU) 页（enrich→20页，create→10页） |

### 新增脚本

- `claim_round.py` — 领取轮次 + 创建轮次锁（`round_N.lock`）
- `release_round.py` — 释放轮次锁（必须在记账后调用，即使 fail/skip）
- `lock_manager.py` — 统一锁 API：acquire / set-page / check-page / assert-owner / release / cleanup

### 并发规则（summary）

```
启动检查：claim_round.py --check-only --instance NAME → 防止同名重复实例
候选准备：完全在领锁之前完成（持锁期间禁止补充搜索）
页面注册：每个候选 → set-page → check-page（exit 1 = 冲突，移除该页）
写入：     add_page.py / edit_page.py（不可直接 Write/Edit）
记账：     record_action.py（内部 assert_owner 验证锁有效）→ release_round.py
```

### 周期任务豁免

W5 反思、`/wiki` 发布等不写 `pages/*.md` 的周期任务跳过轮次锁（`--skip-lock-check`），避免阻塞并发实例。

---

## Phase 11c · 队列归档与发现力度加强

### 队列归档（queue_done.md）

- 新增 `wiki/scripts/butler/cleanup_queue.py`：将 `queue.md` / `housekeeping_queue.md` 中的 `[x]` 已完成条目批量归档到 `queue_done.md` / `housekeeping_done.md`，原文件只保留待处理条目
- **触发时机**：每次 Dream Round（W5 H类，每 3 次 W5 触发一次）开始时强制执行，清理积压
- 归档条目数记入反思报告开头，便于追踪队列健康状况

### 发现力度加强（W1 + W0）

| 参数 | 旧值 | 新值 |
|------|------|------|
| `discover_wanted --top` | 20 | **60** |
| `discover_corpus --top` | 20 | **60** |
| `discover_corpus --min-freq` | 3 | **2** |
| 每次入队条目数 | 1–5 | **5–15** |
| 主动补货触发阈值（P2 行数） | = 0 | **< 5** |
| Trail:Explore 切换点 | P2 < 5 条 = 全explore | P2 < 5 → 立即补货 |

- D1 周期任务（round % 11）参数同步更新为 `--top 60`
- P2 跌破 5 条即触发补货（不等 round % 11），保持队列持续充足

---

## Phase 12 · 大规模词条扩建（R400→R692）

**词条规模**：202 → 749 页（+547 词条）

- **R400–R500**：幸存者实例主导建档冲刺，批量新建次要人物（面壁者随从、舰船船员、联合政府官员）、科技装备（弹射装置、各型舰船）、宇宙概念（曲率驱动、暗能量）等词条；总页数突破 400
- **R501–R600**：破壁人、统帅、幸存者三实例并发，create + enrich 双线推进；引入轮次锁（`lock_manager.py`）防止页面写入冲突；新建词条覆盖《死神永生》全部主要事件与装备
- **R601–R650**：词条突破 600 页；执剑人周期 H17/H18 清理存根，破壁人专项升级 basic→standard；统帅首次完成大批 standard→featured 升级（25 页/轮）
- **R651–R692**：词条达 749 页，精品率 65%（487/749）；统帅 R687–R690 四轮批量 enrich 将大量 basic 页升至 featured；破壁人 R673/R678 专项丰富无工质推进、死柱、核星等技术词条

**质量分布演进**：

| 里程碑 | 总页数 | featured |
|--------|--------|---------|
| Phase 6 末 | 202 | — |
| R500 | ~400 | ~50% |
| R600 | ~600 | ~55% |
| R692 | 749 | 65% (487) |

---

## Phase 13 · 词条突破千页与新型 skill 体系（R693→R970）

**词条规模**：749 → 1,345 页（含 137 章 + 42 重定向），知识量 K 从 2.6 万 → 5.9 万

### 新型 AI 辅助 skill

从单一但ler扩展到多 skill 协作体系：

- **`/serendipity`**：随机抽取 1–3 个现有页面作为灵感种子，上网搜索相关分析文章，发现 Wiki 真正的缺口并补齐。已创建数十个高质量概念词条
- **`/editor`**：编委审稿，定期检查 butler 工作是否违反质量规范，输出分级违规报告
- **`/beaver`**：将任意文本源（书籍、文档、笔记）转化为结构化 wiki 页面，识别 fact/narrative/skill 三类知识
- **`/chapter-scan`**：逐章反思，发现原文章节中遗漏的实体页面

### 大规模词条扩建（R693→R919）

- **R693–R800**：幸存者实例持续建档，执剑人 H24 周期批量 wikify 章节页；总页数突破 800
- **R801–R850**：概念词条快速增加（社会情感、基础物理、宏观概念），"失去人性失去很多"等名句词条入库
- **R851–R919**：新建 93+80 个概念页（科学/社会/情感/地理系列），覆盖三体世界全部可识别概念；总页数突破 1,000；批量 enrich 101 页 basic→standard

### 质量决战（R920→R970）

- **R920–R935**：大规模 enrich 将数百 basic 页批量升级至 standard；清理 56 个冗余通用概念页改为重定向
- **R936–R952**：新建 80 概念词条 + serendipity 补充名句/典故词条（"不要回答！"等）
- **R953–R970**：新建 8 页 + 批量 enrich 6 页 basic→standard；新建「提想法」banner 按钮直达 GitHub Issues
- **质量里程碑**：featured 953 / 1208 总页 = 78.9%，标准 213，basic 仅 1，存根 41

### 实例体系成熟

- **六大命名实例**：统帅/幸存者/破壁人/执剑人/广播员/监听员，通过轮次锁并发协作
- **发布频率**：每 17 轮自动 /wiki 发布，稳定推送至 GitHub Pages
