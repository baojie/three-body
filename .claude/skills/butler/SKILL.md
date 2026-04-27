---
name: butler
description: 启动三体 Wiki 管家永续 loop。三队列系统（content/housekeeping）。每轮：W1三队列选任务→W2执行→W3自评→记账，无需用户逐轮确认。每11轮discover+housekeeping-scan，每17轮自动/wiki发布，每29轮W5反思，每37轮H17覆盖扫描/H18存根排序。工作目录：/home/baojie/work/knowledge/three-body。支持 --focus 参数指定任务范围（多实例并发时使用）。
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

## 启动流程

```
步骤 1 · 读取状态 + 重复实例检测
──────────────────────────────────
cat wiki/logs/butler/round_counter.txt
cat wiki/logs/butler/queue.md
cat wiki/logs/butler/housekeeping_queue.md
tail -10 wiki/logs/butler/actions.jsonl

python3 wiki/scripts/butler/claim_round.py --check-only --instance INSTANCE_NAME
→ exit 1 / stdout "DUPLICATE" → 立即停止，报告重复
→ exit 0 → 继续（其他实例并发是允许的）

步骤 2 · 读规范（每次启动必读）
──────────────────────────────────
skills/SKILL_W0_Butler总则.md   ← 不变量、三队列、闭环、周期调度
skills/SKILL_W1_Butler探索与队列.md
skills/SKILL_W2_Butler原子行动.md

步骤 3 · 启动强制 W5 检查
──────────────────────────────────
距上次 W5 > 50 轮，或 round % 29 == 0 → 立即执行 W5 反思（整轮，用 increment_round.py）

◆ 以下步骤 4–10 构成永续循环 ◆

步骤 4 · 周期任务检查（在领锁之前）
──────────────────────────────────
round % 29 == 0  → W5 反思（整轮，用 increment_round.py + --skip-lock-check）
round % 17 == 0  → /wiki 发布（整轮，用 increment_round.py + --skip-lock-check）
round % 11 == 0  → D1 discover + H10 housekeeping-scan（整轮）
round % 37 == 0  → H17 coverage-scan
round % 37 == 19 → H18 stub-triage
以上任一触发 → 执行后回到步骤 4（不进入步骤 5–10）

步骤 5 · 候选准备——在领锁之前完成
──────────────────────────────────
⚠️ 必须在步骤 6（领锁）之前完全完成，不得在持锁期间补充搜索。

a. 选定本轮主动作类型（A1/A2/A3/B1/C1/C2/H2/…）
b. 计算 batch_n = ceil(1000 / WU)
c. 列出候选：
   - 先从 queue.md P1/P2/P3 选取
   - 再运行 discover_wanted.py --top 60 补充
   - 对每个候选做 corpus_search 验证（命中 ≥ 2 条即纳入）
d. ⚠️ 候选不足时的扩展规则（禁止提前收手）：
   若候选数 < batch_n，必须按顺序尝试：
   1. 扩大 discover_wanted --top 100，对所有新结果做 corpus_search
   2. 对已有页面中的 broken wikilinks 做 corpus_search（常有未建词条）
   3. 降低门槛至命中 ≥ 1 条（接受 basic 级内容）
   "穷尽"的可验证标准：
   - discover_wanted --top 100 返回的所有词条均已做过 corpus_search
   - 命中 ≥ 1 条的全部纳入，仍不够 batch_n → 才算穷尽
   （不得只搜一遍就声称"已穷尽"）

   只有穷尽后候选仍不足时，才允许在本轮内切换为低 WU 补充动作：
   → 主动作候选 N 页（N × WU₁） + 低WU动作补足至 ≥ 1000 WU
   （例：A1 create-page 7页=700WU + H2 enrich-stub 8页=320WU = 1020WU ✓）
   混合轮的两类候选页面都需在步骤 6 统一注册 set-page + check-page。
   此时本轮为**混合动作轮**，输出格式中用"+"分隔，详见"每轮输出格式"。

e. 准备 **batch_n × 1.5 个**候选作为冲突缓冲池（步骤 6 冲突时直接从缓冲池补充，不重新搜索）
f. 确认最终候选列表（含页面 slug 和动作类型），准备锁定

步骤 6 · 领取轮次锁
──────────────────────────────────
ROUND=$(python3 wiki/scripts/butler/claim_round.py --instance INSTANCE_NAME)

# 对步骤 5 确定的全部候选页面，批量注册 + 冲突检查：
for SLUG in <全部候选>:
    python3 wiki/scripts/butler/lock_manager.py set-page --round $ROUND --page SLUG
    python3 wiki/scripts/butler/lock_manager.py check-page --page SLUG --round $ROUND
    → exit 1（冲突）→ 从本轮候选列表移除此页，继续检查其余页
# 若冲突导致有效候选 < batch_n，用步骤 5d 规则补充（此时可从 discover 结果中取备用候选）

步骤 7 · 执行原子行动（W2）
──────────────────────────────────
⚠️ 禁止直接用 Write/Edit 工具写 wiki/public/pages/ 下的文件。
   所有页面操作必须通过脚本（脚本自动记录 revision）：
   新建：python3 wiki/scripts/add_page.py SLUG - --summary "..." --author INSTANCE_NAME
   编辑：python3 wiki/scripts/edit_page.py SLUG - --summary "..." --author INSTANCE_NAME
   （直接用 Write/Edit 会触发 hook 重复递增轮次计数器，产生幽灵轮次）

total_wu = 0; accept_cnt = 0; consec_fail = 0

for each SLUG in confirmed_candidates:
    a. 执行动作（脚本写入）
    b. W3 自评：
       accept → total_wu += WU; accept_cnt += 1; consec_fail = 0
                git add wiki/public/pages/SLUG.md
       fail   → consec_fail += 1
       skip   → 不计任何计数器
    c. consec_fail ≥ 3 → 退出循环
    d. total_wu ≥ 1000 → 退出循环

步骤 8 · 记账 + 释放轮次锁（严格按序）
──────────────────────────────────
# 1. 写 action 汇总行
python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --instance INSTANCE_NAME \
    --type <type> --page "<slug列表>" \
    --result accept \
    --desc "<action>×<accept_cnt>页，<total_wu>WU，<简要说明>" \
    --reflect "<本轮真实观察，禁止写'无'或'ok'>"

# 2. 队列标记：对本轮每个成功页面独立判断
#    该页在 queue.md 中有 [~] SLUG 标记 → complete_task.py --page SLUG --date $(date +%Y-%m-%d)
#    该页来自 discover_wanted（queue.md 中没有对应行）→ 跳过 complete_task.py
#    （同一轮内可能部分来自 queue，部分来自 discover，分别处理）

# 3. 释放锁（最后执行，即使本轮 fail/skip 也必须释放）
python3 wiki/scripts/butler/release_round.py $ROUND

步骤 9 → 回到步骤 4（永续）
```

## 关键规则（违反任何一条即为流程错误）

| # | 规则 | 违反后果 |
|---|------|---------|
| R1 | `claim_round.py` 在步骤 6，所有写操作之前 | 幽灵轮次、计数器漂移 |
| R2 | `release_round.py` 在步骤 8 末尾，即使 fail/skip | 死锁，阻塞下一轮 |
| R3 | 候选准备（步骤 5）在领锁（步骤 6）之前全部完成 | 持锁期间搜索，锁时长膨胀 |
| R4 | 候选 < batch_n 时必须先穷尽三步扩展，再考虑混合动作 | 1000WU 未达标即收手 |
| R5 | 页面写入必须通过 add_page.py / edit_page.py | 直接 Write/Edit 触发 hook 双重计数 |
| R6 | 每条 PN 引文必须从 corpus_search 结果复制，禁止猜测 | 捏造引文，内容失真 |
| R7 | `claim_round.py` 返回 `RACE` → 立即停止并告知用户 | 轮次竞争，数据覆盖 |

## 每轮输出格式

```
# 单动作轮（正常）
[R531] create-page×10 | 茶道谈话/红色联合/… | accept×10 fail×0 | 1000WU

# 混合动作轮（主动作候选不足，补充低WU动作）
[R532] create-page×7 + H2-enrich-stub×8 | 绍琳/… + 宇宙探测器/… | accept×14 fail×1 | 700+320=1020WU

# 周期任务轮
[R533] D1-discover + H10-scan | — | accept | 发现8条新wanted，写入P2/P3
[R534] /wiki-publish → commit abc1234 · R518→534 新建12页，更新7页
[R536] W5-reflect | — | — | 模式B：create候选频繁不足；提案：降低门槛默认≥2条
```

## 暂停条件

- 用户说"停止"/"pause"
- W5 G 类架构提案（暂停等用户 review）
- 连续 5 轮 fail
- 上下文将满（剩 ~10k token 时停止）

## 可用工具

| 工具 | 用法 |
|------|------|
| `claim_round.py` | `ROUND=$(python3 wiki/scripts/butler/claim_round.py --instance NAME)` |
| `claim_round.py --check-only` | 检测同名重复实例（启动时用） |
| `release_round.py` | `python3 wiki/scripts/butler/release_round.py $ROUND` |
| `lock_manager.py set-page` | `python3 ... set-page --round $ROUND --page SLUG` |
| `lock_manager.py check-page` | `python3 ... check-page --page SLUG --round $ROUND` → exit 1=冲突 |
| `lock_manager.py status` | 列出所有活跃轮次锁（含 page 字段） |
| `lock_manager.py cleanup` | 清理超时残留锁 |
| `corpus_search.py` | `python3 wiki/scripts/butler/corpus_search.py "词条" --max 15` |
| `discover_wanted.py` | `python3 wiki/scripts/butler/discover_wanted.py --top 60` |
| `record_action.py` | `--round` 必须是整数；`--skip-lock-check` 仅用于周期任务轮 |
| `add_page.py` | 新建页面（自动记录 revision，自动更新 pages.json） |
| `edit_page.py` | 编辑页面（保护 frontmatter；缩减 >40% 需加 `--allow-shrink`） |

## 详细规范

- [W0 总则](../../../skills/SKILL_W0_Butler总则.md) — 六不变量、三队列、十步闭环、周期调度
- [W1 探索与队列](../../../skills/SKILL_W1_Butler探索与队列.md) — 三队列选取算法
- [W2 原子行动](../../../skills/SKILL_W2_Butler原子行动.md) — A/B/C/D/E/H 组动作，候选不足扩展规则
- [W3 质量标准](../../../skills/SKILL_W3_Butler质量标准.md) — stub/basic/standard/featured 质量规则
- [W5 反思与自改](../../../skills/SKILL_W5_Butler反思与自改.md) — 七类模式识别，每29轮强制
- [W10 内务整理](../../../skills/SKILL_W10_Butler内务整理.md) — H1-H20 内务任务调度
