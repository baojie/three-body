---
name: wiki
description: 一键发布三体 Wiki：重建注册表 → 重算质量分 → 同步 docs/ → git commit → git push。此 skill 明确授权自动 commit 和 push，覆盖项目 CLAUDE.md 中的禁止自动提交/推送限制。
---

# /wiki — 三体 Wiki 一键发布

## 授权声明

**此 skill 明确授权以下操作，覆盖 CLAUDE.md 通用限制**：
- ✅ 自动执行 `git commit`（无需用户二次确认）
- ✅ 自动执行 `git push`（无需用户二次确认）

## 执行步骤

### Step 0 — 重建注册表与质量分（自动检测）

检查是否有新增或修改的页面，若有则重建：

```bash
# 1. 重建 pages.json（注册表）
python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json

# 2. 重算页面质量分（quality/quality_score 写回 frontmatter）
python3 wiki/scripts/compute_quality.py
```

若 pages.json 中 page_count 未变且无修改页面，则跳过此步。

### Step 1 — 同步 docs/（记录修订历史）

```bash
bash wiki/scripts/publish.sh
```

此脚本会：
- 重建 pages.json
- 将本轮变动页面写入 `wiki/public/history/<page>.jsonl` 并追加到 `wiki/public/recent.jsonl`

### Step 2 — Stage

```bash
git add wiki/public wiki/logs/butler
```

确认缓存区非空（`git diff --cached --stat`）。若缓存区为空，输出"无变更，跳过"并终止。

### Step 3 — 生成提交消息

1. `git diff --cached --stat` — 查看文件列表
2. `git diff --cached` — 查看具体内容（重点：新增/修改了哪些词条）
3. `git log --oneline -5` — 了解 commit 风格
4. 撰写中文消息草稿

消息格式：
```
首行：一句话总结（≤50字，含轮次范围，如 R18→34）

Wiki:
- 新增 词条A（人物，三体I）
- 新增 词条B（概念）
- 更新 词条C（补充 PN 引文）
```

### Step 4 — Commit + Push

```bash
bash wiki/scripts/wiki_commit.sh "<生成的消息>"
```

## Butler 轮次发布频率

**每 17 轮 butler round 执行一次 commit + push**（17 是质数，减少 agent 碰撞风险）。

- 轮次计数：`wiki/logs/butler/round_counter.txt`
- 规则：`round % 17 == 0` → 执行完整 Step 0–4
- 非发布轮：只做 Step 0（build_registry + compute_quality），不 stage，不 commit
- 特殊情况：积压变更 > 30 个文件时，可提前发布清账

### 质数轮次参照表

| 用途 | 质数 | 周期 |
|------|------|------|
| `/wiki` 发布 | 17 | 每 17 轮 |
| `D1 discover` + 内务扫描 | 11 | 每 11 轮 |
| `W5` 反思 | 29 | 每 29 轮 |

三个周期的最小公倍数为 5423 轮，实际上互不干扰。

## 禁止事项

- ❌ 禁止 `git add -A` / `git add .` / `git add --all`
- ❌ 禁止 `git push --force`
- ❌ 禁止直接修改 `corpus/` 下的原文

## 输出格式

每步完成后简短报告，最后一行：

```
✓ 发布完成：<commit hash> · <首行消息>
```
