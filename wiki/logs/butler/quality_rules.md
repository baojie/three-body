# Quality Rules KB

Butler 从 W5 反思中提炼的页面质量自定义规则。每轮执行 Q-check 时，在 W3 标准基础上同时比对这些规则。

格式：每条规则用 `QR-<序号>` 标识，包含适用类型、问题描述、规则、来源。

---

## 规则 QR-001（2026-04-27 从 W5 R29 反思）

**适用类型**：person
**问题**：贯穿多纪元的核心人物（如维德）若缺少最终命运节，叙事不完整
**规则**：person 页 standard 级以上，若该人物跨越书册或多个纪元，必须包含"历史结局"或"命运反讽"节
**来源**：R29 W5 反思，R28 维德词条中命运反讽节显著提升页面叙事完整性

## 规则 QR-002（2026-04-27 从 W5 R203 反思）

**适用类型**：全部
**问题**：enrich-page 完成后 frontmatter quality_score 未更新，导致全库 47 页偏差 >1 分
**规则**：每次 enrich-page accept 后，**必须**在同一轮重算实际 score 并更新 frontmatter quality_score，不允许保留旧值
**来源**：R203 W5 反思，全库扫描发现 47/65 页偏差，均为 actual > frontmatter

## 规则 QR-003（2026-04-27 从 W5 R232 反思）

**适用类型**：butler 操作规范
**问题**：rebuild_recent.py 被误作常规步骤调用，将 recent.json 从 249 条压缩至 202 条（每页取最新版），永久丢失历史修订条目
**规则**：`rebuild_recent.py` 是破坏性操作，**严禁**作为常规步骤调用。仅当 recent.json 文件完全损坏（无法 JSON 解析）时才可使用，且使用前必须备份。常规情况下只调用 `record_revision.py` 追加单条修订。
**来源**：R232 W5 反思，R221 session 恢复后误调 rebuild_recent 导致 47 条历史丢失

## 规则 QR-004（2026-04-27 从 W5 R261 反思）

**适用类型**：butler 操作规范
**问题**：session 恢复后 working tree 的 quality_score 可能因脚本副作用回退到旧值（低于 HEAD 已提交值），导致全库数据不一致
**规则**：每次 butler session 启动（或 W5 步骤1）执行 `git diff HEAD --name-only wiki/public/pages/` 检查回退：disk < HEAD 者立即用 Python 脚本修复还原（不使用 git restore，而是直接写文件），disk > HEAD 者视为合法改进保留；两种情况均暂存
**来源**：R261 W5 反思，发现 17 页 quality_score 回退（光粒 54→65，幽灵倒计时 55→61 等），另有 11 页 staged vs working tree 分歧
