# 三体 Wiki

刘慈欣《三体》三部曲（《地球往事》《黑暗森林》《死神永生》）的中文百科 Wiki。

**在线访问**：https://threebody.memify.wiki

---

## 项目概览

| 项目 | 数量 |
|------|------|
| 词条页面 | 1,200+ 个（概念·人物·科技·事件·组织·地点等） |
| 精品词条 | 950+ 个（质量达 featured 级别） |
| 分类列表 | 10 个类型分类 + 23 个主题列表 |
| 原文章节 | 137 章（三体I×37、三体II×50、三体III×50） |
| 原文段落编号（PN） | 每段落全局唯一编号，支持精确引用 |
| 知识量（K 值） | 59,000+ |
| 页面质量分级 | 5 级：存根→基础→标准→精品→旗舰 |

## 功能

- **百科词条**：人物、概念、物理法则、科技装备、事件、组织等
- **原文阅读**：三部曲全文分章节导入，章节间可前后跳转
- **PN 引文系统**：每段落有唯一编号（格式 `1-02-015`），词条正文中的 PN 标注可点击跳转到原文对应位置
- **Wikilink**：词条间双向链接，原文章节中实体名称自动链接到对应词条
- **分类列表**：按类型（人物/科技/事件等）或主题（面壁计划/末日战役/黑暗森林等）浏览词条
- **语义查询**：`::: query` 块支持按类型、标签、质量等动态筛选，生成表格或列表
- **分面搜索**：按类型、出场书册、标签、质量级别筛选词条

## 目录结构

```
three-body/
├── corpus/
│   ├── *.txt              # 原始 GBK 编码原文（只读）
│   └── utf8/              # UTF-8 转码版（供脚本使用）
├── wiki/
│   ├── public/            # SPA 前端
│   │   ├── index.html
│   │   ├── css/main.css
│   │   ├── js/renderer.js
│   │   ├── plugins/       # 插件（pn-citation、footnote、semantic-query 等）
│   │   ├── pages/         # 词条 Markdown 文件（含章节页）
│   │   ├── pages.json     # 页面注册表（由脚本生成）
│   │   └── recent.jsonl   # 最近修订记录（append-only，前端直接读取）
│   └── scripts/           # 构建与维护脚本
│       ├── build_registry.py        # 重建 pages.json
│       ├── build_category_pages.py  # 生成 分类·X.md（按类型）
│       ├── build_list_pages.py      # 生成 列表·X.md（按主题）
│       └── publish.sh               # 同步 wiki/public → docs/
├── docs/                  # GitHub Pages 输出（发布目录）
└── .claude/skills/        # Claude Code skill 定义
    ├── butler/            # /butler — 自动化管家永续 loop
    ├── beaver/            # /beaver — 文本提取为 wiki 页面
    ├── editor/            # /editor — 编委审稿
    ├── serendipity/       # /serendipity — 随机种子搜寻缺失词条
    └── wiki/              # /wiki — 一键发布
```

## 本地开发

```bash
# 默认端口 1453
./wiki/wiki.sh

# 指定端口
./wiki/wiki.sh 9001
```

启动后访问 http://localhost:1453（脚本会自动重建 pages.json 再启动 Node 静态服务器）。

## 发布流程

```bash
# 一键发布（重建注册表 → 重算质量分 → 记录修订 → commit + push）
/wiki
```

或手动：

```bash
python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json
python3 wiki/scripts/compute_quality.py
bash wiki/scripts/publish.sh
git add wiki/public docs
git commit -m "wiki: ..."
git push
```

重新生成分类/列表页（类型或主题变化时运行）：

```bash
python3 wiki/scripts/build_category_pages.py  # 分类·人物、分类·科技……
python3 wiki/scripts/build_list_pages.py       # 列表·面壁计划、列表·黑暗森林……
```

## PN 引文系统

每个原文段落有全局唯一编号，格式 `B-CC-PPP`：

- `B`：书号（1=地球往事，2=黑暗森林，3=死神永生）
- `CC`：章节序号（书内递增，两位数字）
- `PPP`：段落序号（章内递增，三位数字）

例：`（1-02-015）` 表示《地球往事》第2章第15段。词条正文中的 PN 引文可点击跳转到原文对应位置。

## 词条质量分级

| 级别 | 标准 |
|------|------|
| 旗舰 | 配图 + 正文≥1000字 + ≥5个二级标题 + ≥8条PN引文 |
| 精品 | 正文≥200字 + ≥3个二级标题 + ≥3条PN引文 |
| 标准 | 正文≥500字 + ≥2个二级标题 |
| 基础 | 正文≥100字 |
| 存根 | 占位页面，待补充 |

## Butler 自动化管家

`/butler` skill 启动永续 loop，每轮以 **工作单位（WU）** 计量（≥1000 WU/轮），按质数轮次自动执行：

- 每 **11** 轮：发现新词条（扫描 broken wikilinks + corpus 高频词）
- 每 **17** 轮：`/wiki` 发布
- 每 **29** 轮：W5 反思，分析执行模式，提出改进

六命名实例可同时并发运行，通过 `claim_round.py` / `release_round.py` 实现轮次锁，防止页面写入冲突。

## 参与方式

**本 Wiki 不接受直接的人工编辑**——所有词条由 AI 管家自动生成和维护，以确保内容风格与引文体系的一致性。

如果你发现错误、遗漏，或有新词条的想法，欢迎提交 Issue（banner 右上角"提想法"直达）：

- 标题写明你的想法即可，正文填 `RT`（如题）就行
- 有详细补充或原文引用的话也非常欢迎

---

## Wiki 建设技术手段

本 Wiki 的词条内容由 AI 管家自动生成，以原著文本为唯一依据，不从通用知识库抓取，所有引文均精确定位到原文段落编号（PN）。

### 语料库与引文

三部曲原文以 UTF-8 编码存放于 `corpus/utf8/`，每段落在预处理阶段分配全局唯一 PN 编号（`B-CC-PPP`）。词条写作时通过 `corpus_search.py` 全文检索定位原文引文，确保每条 PN 引用都来自原文精确位置，而非概括或改写。

### Butler 永续管家循环

`/butler` 是核心自动化引擎，基于 Claude Code SDK 实现"永续 loop"：

1. **发现（D1 Discover）**：扫描现有页面中的 broken wikilinks 和 `corpus_search` 高频词，生成新词条候选写入 `queue.md`
2. **创建（A1 Create）**：从 corpus 提取相关段落，以 `add_page.py` 写入带 frontmatter 的 Markdown 文件，自动记录修订历史
3. **丰富（A2 Enrich）**：对已有 stub/basic 页面，从 corpus 补充引文、添加章节和叙事分析，升级质量等级
4. **内务（H 系列）**：定期扫描 broken links、质量漂移、孤立页面，批量修复
5. **发布（/wiki）**：每 17 轮自动重建注册表、同步 `docs/`、commit + push

每轮以 **工作单位（WU）** 计量，目标 ≥1000 WU/轮（新建页 100 WU，丰富页 50 WU），通过 `claim_round.py` / `release_round.py` 实现多实例并发锁，防止幽灵轮次。

### 语义查询插件

页面中可嵌入 `::: query` 块，在运行时从 `pages.json` 注册表动态筛选词条并渲染为表格或列表：

```
::: query
type_any: [person]
tags: 危机纪元
quality: featured
sort: quality_score
order: desc
display: table
fields: [label, tags, quality_score]
:::
```

支持的过滤参数包括：`type` / `type_any`、`tags` / `tags_any` / `tags_not`、`quality`、`quality_score_min`、`total_refs_min` 等。

### 分类与列表页生成

两类批量生成脚本按需重建所有导航页：

- `build_category_pages.py`：生成 **分类·人物**、**分类·科技** 等 10 个类型分类页，条目按首次出现书册分组
- `build_list_pages.py`：生成 **列表·面壁计划**、**列表·黑暗森林** 等 23 个主题列表页，内部使用 `::: query` 块动态查询

## GitHub Pages 配置

- 源目录：`/docs`
- 分支：`main`
- 地址：https://threebody.memify.wiki

---

## 版权与许可

**Wiki 内容**（词条正文、注释、分析文字）以 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.zh) 授权发布。转载或修改时须注明来源并以相同协议发布。

**原著引文**：《三体》三部曲版权归刘慈欣及其出版方所有。本站引用原文仅作学术研究与资料整理用途，遵循合理使用原则，不构成商业行为。

**代码**（`wiki/scripts/`、`wiki/public/js/`、`wiki/public/plugins/`）以 [MIT License](https://opensource.org/licenses/MIT) 授权。
