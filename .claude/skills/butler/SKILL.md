---
name: butler
description: 启动三体 Wiki 管家永续 loop。三队列系统（content/housekeeping）。每轮：W1三队列选任务→W2执行→W3自评→记账，无需用户逐轮确认。每11轮discover+housekeeping-scan，每17轮自动/wiki发布，每29轮W5反思（七类模式，含架构提案）。工作目录：/home/baojie/work/knowledge/three-body
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

所有相对路径均基于此。语料：`corpus/utf8/三体*.txt`（UTF-8，已标注 PN）。

## 启动流程（十步）

```
1. 读取状态
   cat wiki/logs/butler/round_counter.txt
   cat wiki/logs/butler/queue.md
   cat wiki/logs/butler/housekeeping_queue.md
   tail -10 wiki/logs/butler/actions.jsonl

2. 读规范（每次启动必读）
   skills/SKILL_W0_Butler总则.md   ← 不变量、三队列、闭环、周期调度
   skills/SKILL_W1_Butler探索与队列.md
   skills/SKILL_W2_Butler原子行动.md

3. ⚠️ 启动强制 W5 检查（在做任何工作前）：
   距上次 W5 > 50 轮，或 round % 29 == 0 → 立即执行 W5 反思

4. 周期任务检查
   round % 29 == 0 → W5 反思（整轮）
   round % 17 == 0 → /wiki 发布
   round % 11 == 0 → D1 discover + H10 housekeeping-scan

5. 三队列选取（W1）
   H-P1 → P1 → H-P2(每3轮) → P2 → P3 → empty_fallback

6. 执行原子行动（W2）

7. 自评（W3）→ accept/fail/skip

8. git add（accept 时）

9. 记账：round_counter+1 + record_action.py + 队列标[x]

10. → 回到步骤 4（永续）
```

## 每轮输出格式

```
[R18] create-page | 程心 | accept | 从三体III提炼主角信息，创建人物页
[R19] H2-enrich-stub | 宇宙闪烁 | accept | stub页补充corpus内容，升级为basic
[R22] D1-discover | — | accept | 发现5条新wanted页面，写入P2
[R29] W5-reflect | — | — | 模式A：enrich fail率高；提案：放松前置条件
[R34] /wiki-publish → commit abc1234 · R18→34 新建6页，更新4页
```

## 暂停条件

- 用户说"停止"/"pause"
- W5 G 类架构提案（暂停等用户 review）
- 连续 5 轮 fail
- 上下文将满（剩 ~10k token 时停止）

## 可用工具

| 工具 | 用法 |
|------|------|
| `corpus_search.py` | `python3 wiki/scripts/butler/corpus_search.py "词条" --max 15`（结果附 PN 引文格式） |
| `discover_wanted.py` | `python3 wiki/scripts/butler/discover_wanted.py --top 20` |
| `record_action.py` | `python3 wiki/scripts/butler/record_action.py --round <整数> --type T --page P --result accept --desc "..."` |

**注意**：`--round` 参数必须是整数（如 `--round 18`），不能是字符串（如 `--round R18`）。

## 详细规范

- [W0 总则](../../../skills/SKILL_W0_Butler总则.md) — 六不变量、三队列、十步闭环、周期调度
- [W1 探索与队列](../../../skills/SKILL_W1_Butler探索与队列.md) — 三队列选取算法
- [W2 原子行动](../../../skills/SKILL_W2_Butler原子行动.md) — A/B/C/D/E/H 组动作
- [W3 质量标准](../../../skills/SKILL_W3_Butler质量标准.md) — stub/basic/standard/featured 质量规则
- [W5 反思与自改](../../../skills/SKILL_W5_Butler反思与自改.md) — 七类模式识别，每29轮强制
- [W10 内务整理](../../../skills/SKILL_W10_Butler内务整理.md) — H1-H10 内务任务调度
