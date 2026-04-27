# 三体 Wiki

刘慈欣《三体》三部曲（《地球往事》《黑暗森林》《死神永生》）的中文百科 Wiki。

**在线访问**：https://baojie.github.io/three-body/

---

## 项目概览

| 项目 | 数量 |
|------|------|
| 词条页面 | 33 个（人物、概念、法则、科技、事件等） |
| 原文章节 | 137 章（三体I×37、三体II×50、三体III×50） |
| 原文段落编号（PN） | 每段落全局唯一编号，支持精确引用 |
| 页面质量分级 | 5 级：存根→基础→标准→精品→旗舰 |

## 功能

- **百科词条**：人物、概念、物理法则、科技装备、事件、组织等
- **原文阅读**：三部曲全文分章节导入，章节间可前后跳转
- **PN 引文系统**：每段落有唯一编号（格式 `1-02-015`），词条正文中的 PN 标注可点击跳转到原文对应位置
- **Wikilink**：词条间双向链接，原文章节中实体名称自动链接到对应词条
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
│   │   ├── plugins/       # 插件（pn-citation、footnote、math 等）
│   │   ├── pages/         # 词条 Markdown 文件（含章节页）
│   │   ├── pages.json     # 页面注册表（由脚本生成）
│   │   └── recent.jsonl   # 最近修订记录（append-only，前端直接读取）
│   └── scripts/           # 构建与维护脚本
├── docs/                  # GitHub Pages 输出（发布目录）
├── skills/                # Butler 管家行动规范
└── .claude/skills/        # Claude Code skill 定义
    ├── butler/            # /butler — 自动化词条创建
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

`/butler` skill 启动永续 loop，按质数轮次自动执行：

- 每 **11** 轮：探索 broken wikilinks，发现新词条
- 每 **17** 轮：`/wiki` 发布
- 每 **29** 轮：W5 反思，分析执行模式，提出改进

## GitHub Pages 配置

- 源目录：`/docs`
- 分支：`main`
- 地址：https://baojie.github.io/three-body/
