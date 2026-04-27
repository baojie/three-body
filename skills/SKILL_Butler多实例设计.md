# Butler 多实例并发设计

## 背景

单个 butler 实例受上下文窗口限制，每批约完成 15–20 轮后需暂停。多实例并发可以：
- 让不同职责的 agent 同时工作，缩短整体周期
- 按 focus 分工，减少跨类型的注意力损耗

---

## 并发安全机制

### 任务不重复领取

`claim_task.py` 使用 `fcntl.flock` 排他锁：
1. 打开 `queue.md`，加排他锁
2. 找第一条 `[ ]` 任务 → 改为 `[~]`（标注实例名）
3. 写回文件，释放锁

两个实例同时调用时，后者会阻塞等待，读到已被标记的任务后自动跳过。

### 轮号不冲突

`increment_round.py` 同样使用 `fcntl.flock`：每次调用返回全局唯一递增整数。两实例的轮号不会相同，也不会跳号（如 R364、R365 分属不同实例）。

### revision 记录不丢失

`record_revision.py` 对 `history/<page>.jsonl` 加 flock；`recent.jsonl` 使用 `O_APPEND` 原子追加。两者均安全支持多进程并发写入。

### pending_revision.json 的轻微竞态

两实例同时写 `pending_revision.json` 会互相覆盖（last-write-wins）。由于 `claim_task.py` 保证两实例不会同时处理同一页面，覆盖只在极端时序下发生（两实例恰好在同一毫秒写不同页面），且后果仅为 author 字段归属错误，不影响内容正确性。可接受。

---

## 命名实例体系

| 实例名 | `--focus` | 职责 | 角色隐喻 |
|--------|-----------|------|----------|
| **统帅** | `all` | 通用，领取任意任务 | 无参数启动时的默认身份 |
| **幸存者** | `create` | 新建词条 | 末日后延续记录的人 |
| **破壁人** | `enrich` | 丰富内容，突破存根 | 突破面壁计划的无名对手 |
| **执剑人** | `housekeeping` | 清链接、修质量、内务 | 独守威慑、日复一日 |
| **广播员** | `publish` | 定期 `/wiki` 发布 | 发出坐标的那个人 |
| **监听员** | `discover` | 扫描语料，发现新词条 | 红岸基地第一个听到回信的人 |

实例名通过 `--instance <名字>` 传入，写入 `pending_revision.json` 的 `author` 字段，最终出现在 `recent.jsonl` 中，便于追踪每条修订由哪个管家完成。

---

## recent.jsonl 记录格式对比

**改进前**
```json
{"page": "叶哲泰", "author": "hook", "summary": "auto: direct Write/Edit (bypassed script)", ...}
```

**改进后**
```json
{"page": "庄颜", "author": "幸存者", "summary": "R364 create-page 罗辑的伴侣，贯穿黑暗森林情感线", ...}
```

---

## 启动示例

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

---

## 已知限制

1. **`pending_revision.json` 竞态**：见上文，概率极低，影响仅限 author 归属
2. **周期任务（discover/publish）重复触发**：多实例同时到达 `round % 17 == 0` 时均会尝试发布。目前靠 `wiki_commit.sh` 的 git 状态检测跳过空提交，后续可考虑加"发布锁"文件
3. **W5 反思各自独立**：多实例的 W5 反思结论不共享。若需全局视角，应由统帅单独执行 W5
