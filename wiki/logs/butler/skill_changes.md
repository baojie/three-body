# Skill Changes Changelog

Butler 规则修订记录。每次 W5 反思应用修订后追加此文件。

格式：`日期  Skill版本  修订内容`

---

2026-04-27  W0 v1.0→v2.0  重构为6不变量+三队列+10步闭环+周期调度(mod11/17/29)
2026-04-27  W1 v1.0→v2.0  新增 housekeeping_queue 感知，三队列选取算法
2026-04-27  W2 v1.0→v2.0  新增 H 组内务整理引用（详规在 W10）
2026-04-27  W3 v1.0        新建：四级质量标准（stub/basic/standard/featured）
2026-04-27  W5 v1.0→v2.0  反思模式从5类扩展为7类（+F编辑错误 +G架构提案）
2026-04-27  W10 v1.0       新建：H1-H10 内务整理任务调度

2026-04-27  W2 v2→v2.1  A1 create-page 搜索策略：命中<3条时改用侧面词（功能词/别名/关联实体），示例：搜"三体游戏"→改搜"V装具"+"游戏"
2026-04-27  W3 v1→v1.1  person页standard级新增QR-001：核心多纪元人物须有"历史结局"或"命运反讽"节
2026-04-27  quality_rules  新增QR-001（R29 W5反思）

2026-04-27  W2 v2.1→v2.2  PN引文系统：明确 PN 必须在 blockquote 内部（`> （PN）`），放外面属格式错误，自评降 fail（R87 W5反思，B1修订）
2026-04-27  W2 v2.2→v2.3  新增「脚本 API 备忘」节：record_action --round 必须整数，record_revision 第一参数必须 slug（R87 W5反思，F类修订）
