---
name: butler
description: 启动三体 Wiki 管家永续 loop。每轮：W1选任务→W2执行→记账，无需用户逐轮确认。每17轮自动 /wiki 发布。工作目录：/home/baojie/work/knowledge/three-body
---

# /butler — 三体 Wiki 管家

## 授权声明

**此 skill 明确授权，覆盖 CLAUDE.md 通用限制**：
- ✅ 永续循环，无需逐轮确认
- ✅ 每 17 轮自动 `git commit` + `git push`（通过 `/wiki` skill）
- ✅ `git add wiki/public/pages/<单个文件>`

## 工作目录

```
/home/baojie/work/knowledge/three-body
```

所有相对路径均基于此。语料：`corpus/三体*.txt`（GB18030 编码）。

## 启动流程

```
1. 读取状态
   cat wiki/logs/butler/round_counter.txt
   cat wiki/logs/butler/queue.md
   tail -10 wiki/logs/butler/actions.jsonl

2. 读规范（每次启动必读）
   skills/SKILL_W0_Butler总则.md   ← 不变量、闭环、暂停条件
   skills/SKILL_W1_Butler探索与队列.md
   skills/SKILL_W2_Butler原子行动.md

3. 进入永续 loop
```

## 每轮流程（W1→W2→记账）

```
W1 选任务：按 P1→P2→P3 从 queue.md 取一条
W2 执行：根据任务类型（create/enrich/stub/fix-links/add-quote/discover）执行
记账：round_counter+1 + record_action.py + queue.md 标[x]
每17轮：/wiki 发布
```

## 每轮输出格式

```
[R1] create-page | 汪淼 | accept | 从三体I提炼主角信息，创建人物页
[R2] stub | 费米悖论 | accept | 黑暗森林法则页 broken link，创建存根
[R17] /wiki 发布 → commit abc1234 · R1→17 新建9页
```

## 暂停条件

- 用户说"停止"/"pause"
- 连续 5 轮 fail
- 上下文将满（剩 ~10k token 时停止）

## 可用工具

| 工具 | 用法 |
|------|------|
| `corpus_search.py` | `python3 wiki/scripts/butler/corpus_search.py "词条" --max 15` |
| `discover_wanted.py` | `python3 wiki/scripts/butler/discover_wanted.py --top 20` |
| `record_action.py` | `python3 wiki/scripts/butler/record_action.py --round R --type T --page P --result accept --desc "..."` |

## 详细规范

- [W0 总则](../../../skills/SKILL_W0_Butler总则.md)
- [W1 探索与队列](../../../skills/SKILL_W1_Butler探索与队列.md)
- [W2 原子行动](../../../skills/SKILL_W2_Butler原子行动.md)
