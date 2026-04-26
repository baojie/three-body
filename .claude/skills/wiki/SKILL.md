---
name: wiki
description: 一键发布三体 Wiki：重建注册表 → 同步 docs/ → git commit → git push。此 skill 明确授权自动 commit 和 push，覆盖项目 CLAUDE.md 中的禁止自动提交/推送限制。
---

# /wiki — 三体 Wiki 一键发布

## 授权声明

**此 skill 明确授权以下操作，覆盖 CLAUDE.md 的通用限制**：
- ✅ 自动执行 `git commit`（无需用户二次确认）
- ✅ 自动执行 `git push`（无需用户二次确认）

## 执行步骤

### Step 0 — 重建注册表（自动检测）

检查是否有新增或修改的页面，若有则重建：

```bash
# 重建 pages.json（注册表）
python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json
```

### Step 1 — 同步 docs/

将 wiki/public/ 同步到 docs/（GitHub Pages 源目录）：

```bash
bash wiki/scripts/publish.sh
```

### Step 2 — Stage

```bash
git add wiki/public docs
```

确认缓存区非空（`git diff --cached --stat`）。若缓存区为空，输出"无变更，跳过"并终止。

### Step 3 — 生成提交消息

1. `git diff --cached --stat` — 查看文件列表
2. `git diff --cached` — 查看具体内容
3. `git log --oneline -5` — 了解 commit 风格
4. 撰写中文消息草稿

消息格式：
```
首行：一句话总结（≤50字）

Wiki:
- 新增/更新 具体词条
```

### Step 4 — Commit + Push

```bash
bash wiki/scripts/wiki_commit.sh "<生成的消息>"
```

## 禁止事项

- ❌ 禁止 `git add -A` / `git add .` / `git add --all`
- ❌ 禁止 `git push --force`
- ❌ 禁止直接修改 corpus/ 下的原文

## 输出格式

```
✓ 发布完成：<commit hash> · <首行消息>
```
