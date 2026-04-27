# 三体 Wiki — Claude 工作规则

## 项目简介

本项目是刘慈欣《三体》三部曲（《三体》《黑暗森林》《死神永生》）的中文百科 Wiki，使用纯静态 SPA 前端，发布于 GitHub Pages。

```
three-body/
├── corpus/          # 三部曲原文 txt（只读，不可修改）
├── wiki/
│   ├── public/      # SPA 前端（index.html + css/ + js/ + pages/）
│   └── scripts/     # 构建脚本
├── docs/            # GitHub Pages 输出（由 publish.sh 生成，勿手动编辑）
└── .claude/
    ├── settings.json
    └── skills/wiki/ # /wiki 发布 skill
```

## 绝对禁止事项（CRITICAL）

- ❌ **禁止自动 `git commit`** — 需用户明确要求，或使用 `/wiki` skill
- ❌ **禁止 `git add -A` / `git add .` / `git add --all`** — 只允许显式路径
- ❌ **禁止 `git push --force`**
- ❌ **禁止 `git reset --hard` / `git checkout --` / `git restore`**
- ❌ **禁止修改 `corpus/` 下的原文** — 三部曲文本只读

**唯一例外**：使用 `/wiki` skill 时，自动 commit + push 已被授权。

## Wiki 页面规范

### Frontmatter 字段

```yaml
---
id: 词条名       # 与文件名（不含.md）一致
type: person     # person / concept / law / technology / event / organization / place / civilization / weapon / book
label: 显示名    # 中文显示名
aliases: [别名1, 别名2]
tags: [标签]
description: 一句话描述
featured: true   # 可选，首页精选
books: [三体I, 三体II, 三体III]  # 出现在哪部书
---
```

### 页面类型

| type | 含义 |
|------|------|
| person | 人物 |
| concept | 概念 |
| law | 物理/宇宙法则 |
| technology | 科技/设备 |
| weapon | 武器 |
| event | 事件 |
| organization | 组织 |
| place | 地点 |
| civilization | 文明 |
| era | 纪元（危机纪元/威慑纪元等） |
| book | 书册/卷 |
| chapter | 原文章节 |
| story | 故事（云天明童话等） |
| quote | 名句 |
| overview | 综述 |
| list | 列表 |

### Wikilink 格式

使用 `[[词条名]]` 或 `[[词条名|显示文字]]`。

## 工作流程

### 新建页面

1. 在 `wiki/public/pages/` 下创建 `词条名.md`
2. 写好 frontmatter + 正文
3. 运行 `/wiki` 发布

### 发布

```bash
/wiki
```

或手动：
```bash
python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json
bash wiki/scripts/publish.sh
git add wiki/public docs
git commit -m "wiki: 更新词条"
git push
```

### 本地预览

由于使用 `fetch()` 加载文件，需要 HTTP 服务器（不能直接打开 file://）：

```bash
cd wiki/public && python3 -m http.server 8080
# 访问 http://localhost:8080
```

## GitHub Pages 配置

- 源目录：`/docs`
- 分支：`main`
- 地址：`https://baojie.github.io/three-body/`

首次需要在 GitHub 仓库设置中将 Pages 源设置为 `main` 分支 `/docs` 目录。

## Commit 消息规范

```
wiki: 新增词条「叶文洁」「三体文明」

Wiki:
- 新增 叶文洁（天体物理学家，红岸基地核心人物）
- 新增 三体文明（三星系文明简介）
```
