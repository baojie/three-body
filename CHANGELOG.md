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
