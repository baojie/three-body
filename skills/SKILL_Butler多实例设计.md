# Butler 多实例并发设计（当前版本）

> 本文记录当前生产架构。历史演进见 CHANGELOG Phase 12+。

---

## 一、设计目标

多个命名实例（统帅 / 幸存者 / 破壁人 / 执剑人 / 广播员 / 监听员）可**完全并发**运行，互不干扰——前提是它们在同一轮内不操作同一页面。

---

## 二、两层锁架构

### 层 1：轮次锁（round-level）

由 `claim_round.py` 管理，保证每个轮次编号全局唯一、不重复分配。

```
ROUND=$(python3 wiki/scripts/butler/claim_round.py --instance 破壁人)
```

底层：`lock_manager.py` 使用自旋 `O_CREAT|O_EXCL` 创建 `round_counter.lock`（极短持有），原子递增 `round_counter.txt`，创建 `round_<N>.lock` 文件。两个实例并发调用时，计数器互斥，各拿到不同轮号，不阻塞。

**锁文件内容示例**：
```json
{"round": 678, "instance": "破壁人", "pid": 12345, "ts": "2026-04-28T10:00:00Z", "pages": ["死柱", "核星", "磁力腰带"]}
```

### 层 2：页面锁（page-level）

候选准备完成后、执行写入前，为每个候选页面注册并检测冲突：

```bash
# 注册：把 slug 写入本轮 lock 文件的 pages 列表
python3 wiki/scripts/butler/lock_manager.py set-page --round $ROUND --page 死柱

# 检测：扫描所有活跃 round_*.lock，若其他轮次已注册同页 → exit 1（冲突）
python3 wiki/scripts/butler/lock_manager.py check-page --page 死柱 --round $ROUND
```

冲突处理：从候选列表移除该页，从缓冲池补充，**不重新搜索**。

---

## 三、轮次锁生命周期

```
claim_round.py          → 创建 round_N.lock（pages=[]）
lock_manager set-page   → pages 追加候选 slug（可多次，步骤5候选准备后批量调用）
lock_manager check-page → 每个候选写前检测（exit 1=冲突）
add_page.py / edit_page.py → 实际写入页面
record_action.py        → 写 actions.jsonl（内部调用 assert_owner 验证锁仍有效）
release_round.py        → 删除 round_N.lock（即使本轮 fail/skip 也必须调用）
```

**严格规则**：持锁期间禁止新的 corpus_search（候选必须在领锁前全部确定）。

---

## 四、批次模式（与旧版"每轮1页"的区别）

| 旧版 | 当前版 |
|------|--------|
| 每轮操作 1 个页面，WU=1 | 每轮目标 1000 WU，批量处理 |
| 1 页 → 记账 → 下一轮 | batch_n=ceil(1000/WU) 页连续处理 |
| enrich 每轮 1 页 | enrich(50WU)→batch_n=20；create(100WU)→batch_n=10 |
| 轮号与页面一一对应 | 一个轮号对应多页，pages 字段记录全部 slug |

---

## 五、命名实例体系

| 实例名 | `--focus` | 职责 | 角色隐喻 |
|--------|-----------|------|----------|
| **统帅** | `all` | 通用，领取任意任务 | 无参数启动时的默认身份 |
| **幸存者** | `create` | 新建词条 | 末日后延续记录的人 |
| **破壁人** | `enrich` | 丰富内容，突破存根 | 突破面壁计划的无名对手 |
| **执剑人** | `housekeeping` | 清链接、修质量、内务 | 独守威慑、日复一日 |
| **广播员** | `publish` | 定期 `/wiki` 发布 | 发出坐标的那个人 |
| **监听员** | `discover` | 扫描语料，发现新词条 | 红岸基地第一个听到回信的人 |

实例名通过 `--instance <名字>` 传入，写入轮次锁和 `actions.jsonl`，便于追踪来源。

---

## 六、重复实例检测

同一实例名不应同时运行两个副本（会争抢同类任务）。启动时必须检测：

```bash
python3 wiki/scripts/butler/claim_round.py --check-only --instance 破壁人
# exit 0 → 无同名实例，可启动
# exit 1 → stdout 输出 "DUPLICATE"，立即停止
```

底层：扫描所有活跃 `round_*.lock`，检查 `instance` 字段是否重复。

---

## 七、周期任务的锁豁免

`/wiki` 发布、W5 反思等周期任务不走正常的 claim_round → release 流程，而是用 `increment_round.py --skip-lock-check` 申请轮号后直接执行，`record_action.py` 使用 `--skip-lock-check` 跳过锁验证：

```bash
ROUND=$(python3 wiki/scripts/butler/increment_round.py --skip-lock-check)
# ... 执行 /wiki 或 W5 ...
python3 wiki/scripts/butler/record_action.py --round $ROUND ... --skip-lock-check
```

原因：周期任务不写 `pages/*.md`，无需页面锁；强制持轮次锁会阻塞其他并发实例。

---

## 八、并发安全矩阵

| 场景 | 是否安全 | 原因 |
|------|----------|------|
| 两实例同时 `claim_round.py` | ✅ | 计数器互斥锁保证唯一轮号 |
| 两实例操作不同页面 | ✅ | check-page 扫描无冲突 |
| 两实例操作同一页面 | ✅（冲突检测） | check-page exit 1，后者跳过该页 |
| `record_revision.py` 并发写 | ✅ | history/*.jsonl 用 flock；recent.jsonl 用 O_APPEND |
| `actions.jsonl` 并发写 | ✅ | O_APPEND 原子追加 |
| 同名实例同时启动 | ✅（启动检测） | --check-only 在步骤1阻止重复启动 |
| 周期任务与普通轮次并发 | ✅ | 周期任务用 --skip-lock-check，不争锁 |

---

## 九、已知限制

1. **周期任务多实例重复触发**：多实例同时到达 `round % 17 == 0` 时均会尝试发布。目前靠 `publish.sh` 检查 git 状态跳过空提交，后续可考虑发布锁文件。
2. **W5 反思各自独立**：多实例的 W5 结论不共享。需全局视角时应由统帅单独执行 W5。
3. **锁超时（10min）**：`round_N.lock` 超过 600 秒被 `cleanup` 视为超时。上下文切换时若持锁时间超过此值，下轮 `record_action.py` 会报锁失效（`assert_owner` 失败），需用 `--skip-lock-check` 补录。

---

## 十、启动示例

```bash
# 单独启动（统帅模式）
/butler

# 并发两实例
/butler --focus create   --instance 幸存者   # agent A
/butler --focus enrich   --instance 破壁人   # agent B（同时启动）

# 全五实例（最大并发）
/butler --focus discover     --instance 监听员
/butler --focus create       --instance 幸存者
/butler --focus enrich       --instance 破壁人
/butler --focus housekeeping --instance 执剑人
/butler --focus publish      --instance 广播员
```
