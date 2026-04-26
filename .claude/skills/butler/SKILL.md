---
name: butler
description: 启动三体 Wiki 管家的永续 loop。每轮执行一个原子动作（选任务→读语料→写页面→记账），完成后立即进入下一轮，无需用户逐轮确认。每 17 轮自动发布。
---

# /butler — 三体 Wiki 管家永续 Loop

## 授权声明

**此 skill 明确授权以下操作，覆盖 CLAUDE.md 的通用限制**：
- ✅ 自动循环多轮，无需用户逐轮确认
- ✅ 每 17 轮自动执行 `git commit` + `git push`（通过 `/wiki` skill）
- ✅ 自动 `git add <明确路径>`（单个文件，禁止 `-A`/`.`）

---

## 启动流程

```
1. 读取当前状态
   cat wiki/logs/butler/round_counter.txt
   cat wiki/logs/butler/queue.md
   tail -20 wiki/logs/butler/actions.jsonl

2. 扫描 wanted pages（可选，每 11 轮做一次）
   python3 wiki/scripts/butler/discover_wanted.py --top 20

3. 进入永续 loop（W1→W2→W3→记账→下一轮）
```

---

## 核心哲学（不变量）

1. **小步**：每轮只做一个页面的一个操作（create / enrich / stub / fix-links）
2. **有源**：每个写入 wiki 的断言必须来自 `corpus/` 原文或已有页面；不捏造细节
3. **留痕**：每轮结束必须调用 `record_action.py` 写入 `actions.jsonl`
4. **追加**：对已有页面只追加新节或新内容，不覆盖已有内容
5. **永续**：完成一轮后立即进入下一轮，不等用户确认

**触犯任一立即停止，记 fail，继续下一轮。**

---

## 永续 Loop 详解

### W1 — 选任务

按优先级从 `wiki/logs/butler/queue.md` 选一条未完成任务（`- [ ]`）：

```
P1 → P2 → P3（发现型任务每 11 轮才做一次）
```

若队列为空或全为发现型：
1. 运行 `python3 wiki/scripts/butler/discover_wanted.py --top 20`
2. 将 top 5 wanted pages 作为 `P2 stub` 任务写入队列

### W2 — 执行

根据任务类型执行：

#### `create-page PAGE`
1. 用 corpus_search 搜索页面名称：
   ```bash
   python3 wiki/scripts/butler/corpus_search.py "PAGE" --max 15
   ```
2. 阅读搜索结果，提炼：
   - 人物：身份、出场书册、关键事件、关联人物
   - 概念/法则：定义、来源、在故事中的作用
   - 事件：时间线、参与者、影响
3. 写入 `wiki/public/pages/PAGE.md`（参见页面格式）
4. 页面最少包含：frontmatter + 1段导语 + 2个正文节 + 相关词条

#### `enrich-page PAGE`
1. 读取现有页面：`cat wiki/public/pages/PAGE.md`
2. 搜索语料补充内容：
   ```bash
   python3 wiki/scripts/butler/corpus_search.py "PAGE" --max 20
   ```
3. 找出页面缺失的节（缺少引用段落 / 缺少背景 / 缺少相关词条）
4. 追加新节，不替换已有内容

#### `stub PAGE`
创建最小存根，让 broken link 变为有效页面：
```markdown
---
id: PAGE
type: unknown
label: PAGE
aliases: []
tags: []
description: （待补充）
---

# PAGE

（页面待建设。）

## 相关词条
```

#### `fix-links PAGE`
1. 读取页面
2. 找出 broken wikilinks（`[[TARGET]]` 但 TARGET 无对应页面）
3. 对每个 broken target：若 target 已在 `queue.md`，跳过；否则加入 P2 stub 队列

#### `discover CORPUS`
1. 运行 `python3 wiki/scripts/butler/discover_wanted.py --top 30`
2. 选 top 10 wanted pages 中尚未在队列的，加入 P2 create 队列
3. 本轮计为 discover 动作

### W3 — 评估

执行后自查：
- **accept**：写入内容有源，不含捏造，格式正确（frontmatter 有 id/type/label）
- **fail**：无源、格式错误、空页面、写入被拒
- **skip**：任务已过时（页面已存在）

### 记账

每轮结束必须：

```bash
# 1. 更新轮次计数
echo $(($(cat wiki/logs/butler/round_counter.txt) + 1)) > wiki/logs/butler/round_counter.txt

# 2. 记录 action
python3 wiki/scripts/butler/record_action.py \
  --round <R> --type <type> --page <page> --result <result> --desc "<描述>"

# 3. 在 queue.md 中将该任务标为完成
# 将 "- [ ] P? type | PAGE | ..." 改为 "- [x] P? type | PAGE | ..."
```

---

## 每轮输出格式（单行）

```
[R1] create-page | 汪淼 | accept | 从三体I提炼人物简介，创建人物页，含身份/出场/关联人物
[R2] create-page | 面壁者 | accept | 创建制度页，含4位面壁者列表和结局
[R3] stub | 费米悖论 | accept | 创建存根，因黑暗森林法则页面引用
[R17] /wiki 发布 → commit abc1234 · R1→17 新建9页
```

---

## 每 17 轮发布

```bash
# 检查是否到达发布轮次
R=$(cat wiki/logs/butler/round_counter.txt)
if [ $((R % 17)) -eq 0 ]; then
  # 调用 /wiki skill 发布
fi
```

---

## 暂停条件

- 用户说"停止"/"pause"/"stop"
- 连续 5 轮全部 fail
- 上下文窗口将满（约剩 10k token 时停止，说明原因）

---

## 页面格式参考

```yaml
---
id: 词条名
type: person|concept|law|technology|weapon|event|organization|place|civilization|book
label: 显示名
aliases: [别名1, Alias]
tags: [标签, 书册]  # 书册: 三体I / 三体II / 三体III
description: 一句话描述（≤50字）
books: [三体I]
---

# 词条名

导语（1-2句定义）。

## 背景

## 在故事中的作用

## 相关词条

- [[词条A]]
- [[词条B]]
```

---

## 可用工具

| 工具 | 用法 |
|------|------|
| corpus_search.py | `python3 wiki/scripts/butler/corpus_search.py "关键词" --max 15` |
| discover_wanted.py | `python3 wiki/scripts/butler/discover_wanted.py --top 20` |
| record_action.py | `python3 wiki/scripts/butler/record_action.py --round R --type T --page P --result accept --desc "..."` |
| build_registry.py | `python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json` |
| /wiki skill | 每 17 轮发布 |

---

## 工作目录

```
/home/baojie/work/knowledge/three-body
```

所有路径均相对于此目录。语料位于 `corpus/三体I：地球往事.txt` 等。
