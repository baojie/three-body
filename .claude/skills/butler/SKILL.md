---
name: butler
description: 启动三体 Wiki 管家永续 loop。三队列系统（content/housekeeping）。每轮：W1三队列选任务→W2执行→W3自评→记账，无需用户逐轮确认。每11轮discover+housekeeping-scan，每17轮自动/wiki发布，每29轮W5反思，每33轮H17覆盖扫描/H18存根排序。工作目录：/home/baojie/work/knowledge/three-body。支持 --focus 参数指定任务范围（多实例并发时使用）。
---

# /butler — 三体 Wiki 管家

## 固定实例（命名管家）

五位无名的历史见证者，各司其职：

| 实例 | 启动命令 | 职责 |
|------|----------|------|
| **监听员** | `/butler --focus discover --instance 监听员` | 扫描语料，发现新词条，写入队列 |
| **破壁人** | `/butler --focus enrich --instance 破壁人` | 深挖内容，突破存根，升级质量 |
| **执剑人** | `/butler --focus housekeeping --instance 执剑人` | 日常维护，清链接，修质量分 |
| **广播员** | `/butler --focus publish --instance 广播员` | 定期 `/wiki` 发布，同步 docs/ |
| **幸存者** | `/butler --focus create --instance 幸存者` | 新建词条，留存档案 |

不带参数直接启动 `/butler` 即为**统帅**模式，领取任意类型任务，`author` 显示为 `统帅`。

并发时 `author` 字段会显示实例名，便于在 recent.jsonl 中追踪来源。

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

## 启动参数（可选）

| 参数 | 默认 | 说明 |
|------|------|------|
| `--focus create` | `all` | 只领取 create 类任务（新建词条） |
| `--focus enrich` | `all` | 只领取 enrich 类任务（丰富内容） |
| `--focus housekeeping` | `all` | 只领取内务任务 |
| `--focus publish` | `all` | 只执行发布任务 |
| `--focus all` | `all` | 领取任意类型任务（统帅模式） |
| `--instance NAME` | `统帅` | 实例标识符，显示在 recent.jsonl 的 author 字段 |

示例：`/butler --focus create --instance 幸存者`

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
   round % 33 == 0 → H17 coverage-scan（三部曲覆盖扫描）
   round % 33 == 11 → H18 stub-triage（存根优先排序）

5. 三队列选取（W1）
   H-P1 → P1 → H-P2(每3轮) → P2 → P3 → empty_fallback

6. 执行原子行动（W2）
   ⚠️ 写入页面文件（Write/Edit）前，必须先写 **per-slug** pending 文件：
   ```python
   import json; from pathlib import Path
   # SLUG = 目标页面文件名（不含 .md），每个被写的页面各写一个文件
   Path(f"wiki/logs/butler/pending_revision_{SLUG}.json").write_text(
       json.dumps({"author": INSTANCE_NAME, "round": ROUND, "type": ACTION_TYPE, "desc": ONE_LINE_DESC}, ensure_ascii=False),
       encoding="utf-8"
   )
   ```
   hook 会在 Write/Edit 完成后按 slug 匹配并消费对应文件，写入 recent.jsonl。
   ⚠️ 规则：**每次 Write/Edit 前都必须写 pending 文件**，包括副作用修改的页面。
   ⚠️ 规则：**一轮只修改一个页面**；若必须修改多个，每个都要写 pending 并记独立 action。

7. 自评（W3）→ accept/fail/skip

8. git add（accept 时）

9. 记账：increment_round.py（原子） + record_action.py --instance INSTANCE_NAME + complete_task.py（队列 [~]→[x]）

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
- [W10 内务整理](../../../skills/SKILL_W10_Butler内务整理.md) — H1-H20 内务任务调度
