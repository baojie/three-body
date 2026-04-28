---
name: chapter-scan
description: 逐章反思，一次只扫一章，发现原文章节中遗漏的实体页面和改进建议。工作目录：/home/baojie/work/knowledge/three-body。
---

# /chapter-scan — 逐章反思 Skill

## 核心约束

**一次只扫一章，绝对禁止合并多章处理。**

每次调用只处理进度文件中的下一章，完成后更新进度，等待下次调用。

## 工作目录

```
/home/baojie/work/knowledge/three-body
```

## 启动流程

```
步骤 1 · 检查进度
──────────────────────────────────
python3 wiki/scripts/chapter_scan.py status
→ 显示当前进度和下一章
→ 若输出 ALL_DONE → 报告已全部完成，停止

步骤 2 · 获取本章信息
──────────────────────────────────
CHAPTER=$(python3 wiki/scripts/chapter_scan.py next)
python3 wiki/scripts/chapter_scan.py scan

→ 输出包含：
  - CHAPTER: 章节名
  - BROKEN_WIKILINKS: 已有但无页的链接（立即处理）
  - KNOWN_ENTITIES: 已知实体列表（参考用）
  - CHAPTER_TEXT: 全文（PN格式）

步骤 3 · Claude 实体反思（核心步骤）
──────────────────────────────────
仔细阅读 CHAPTER_TEXT，识别所有**具名实体**：

扫描维度（按重要性）：
A. 人物姓名 — 有姓名的角色（含配角、一次性人物）
B. 组织机构 — 单位、部门、项目、计划名称
C. 地名/设施 — 建筑、城市、基地、特定场所
D. 科技/设备 — 装置、武器、材料、系统
E. 概念/理论 — 学说、法则、现象、术语
F. 事件/时代 — 有专名的事件或历史阶段
G. 作品/文献 — 提到的书名、报告名

**识别规则**：
- 凡文中出现的专有名词，无论是否已有 `[[wikilink]]` 标记
- 重点关注**没有** `[[...]]` 标记的专名
- 跳过：过于泛化的词（"政府"、"军队"、"人类"等）
- 跳过：现实世界通识名词（除非在书中有特殊含义）

步骤 4 · 逐一核查
──────────────────────────────────
对识别出的每个实体候选：

a. 检查 pages.json alias_index 是否存在：
   python3 -c "
   import json
   ai = json.load(open('wiki/public/pages.json'))['alias_index']
   for name in ['实体A', '实体B', ...]:
       print(name, '→', ai.get(name, 'MISSING'))
   "

b. 若 MISSING：运行 corpus_search 评估引用量：
   python3 wiki/scripts/butler/corpus_search.py "实体名" --max 8

c. 按命中数分类：
   - ≥5 hits → P1（重要遗漏，优先建页）
   - 2-4 hits → P2（有价值，建 stub）
   - 1 hit  → P3（次要，建极简 stub）
   - 0 hits → 跳过（可能非书中实体）

步骤 5 · 处理 BROKEN_WIKILINKS
──────────────────────────────────
BROKEN_WIKILINKS 是**已经被 wikilink 引用但没有页面**的实体，优先级最高。
对每个 broken link 运行 corpus_search，决定：
- 命中 ≥1 → 立即在本步骤建立 stub 页面
- 命中 0 → 记录为"错误链接"（章节页面中的链接有误）

步骤 6 · 输出反思报告
──────────────────────────────────
格式：

```
## 📖 [章节名] 反思报告

### 遗漏实体

| 实体 | 类别 | corpus命中 | 建议 |
|------|------|-----------|------|
| XX   | 人物 | 7         | P1 新建 |
| YY   | 科技 | 3         | P2 stub |
| ZZ   | 事件 | 1         | P3 极简stub |

### Broken Wikilinks（本章链接已建页处理）
- [[XX]] → 已建stub / 已有别名XX在YY页（修正链接）

### 现有遗漏（需改进但非新页）
- 现有 XX 页缺少本章引文 （3-NN-NNN）
- 建议在 XX 页补充章节视角

### 判断为"无需建页"的候选
- AAA（过于泛化/现实通识）
- BBB（仅出现1次且无独立意义）
```

步骤 7 · 写入队列（仅P1/P2）
──────────────────────────────────
对 P1/P2 实体，追加至 wiki/logs/butler/queue.md：

格式：`- [ ] P<级别> stub | <实体名> | 来自章节反思 <章节名>`

步骤 8 · 记录进度并推进
──────────────────────────────────
python3 wiki/scripts/chapter_scan.py record-found --found <总发现数> --queued <加入队列数>
python3 wiki/scripts/chapter_scan.py advance
```
→ 进度推进到下一章，报告本章结果
```

## 禁止事项

- ❌ **禁止一次处理多章**（哪怕章节很短）
- ❌ **禁止跳章**（必须按顺序处理）
- ❌ **禁止在本 skill 中直接建页**（只写队列，建页由 /butler 执行）
  - 唯一例外：BROKEN_WIKILINKS 的 stub 可以在步骤 5 立即建立
- ❌ **禁止 git commit**（scan结果不触发commit）

## 输出格式（每次调用末尾）

```
✓ 已扫描 [章节名]（[当前进度]/137 章）
  发现遗漏：X 个（P1:N P2:N P3:N）
  加入队列：N 个
  下一章：[章节名]
```

## 可用工具

| 工具 | 命令 |
|------|------|
| 进度状态 | `python3 wiki/scripts/chapter_scan.py status` |
| 下一章 | `python3 wiki/scripts/chapter_scan.py next` |
| 扫描章节 | `python3 wiki/scripts/chapter_scan.py scan` |
| 推进进度 | `python3 wiki/scripts/chapter_scan.py advance` |
| 记录统计 | `python3 wiki/scripts/chapter_scan.py record-found --found N --queued N` |
| 语料搜索 | `python3 wiki/scripts/butler/corpus_search.py "词" --max 8` |
| 查alias | `python3 -c "import json; ai=json.load(open('wiki/public/pages.json'))['alias_index']; print(ai.get('词', 'MISSING'))"` |

## 参数

| 参数 | 说明 |
|------|------|
| `--chapter 三体I-05` | 强制扫描指定章节（不推进进度，用于调试） |
| `--reset` | 重置进度（慎用） |
