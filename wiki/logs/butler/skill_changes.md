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
2026-04-27  W2 v2.x→v2.x+1  A1 步骤5前置检查：批量ls检查候选是否已存在，提前替换，避免持锁期发现冲突（R580 W5反思）
2026-04-27  W0 周期调度    W5距上次>50轮触发条件：每轮步骤4检查，不等round%29（R580 W5反思，R494→R580相差86轮）
2026-04-27  W2 A1扩展路径  三体游戏人物/地点→宇宙物理天文→末日纪元地名技术（三层扩展路径规范化，R580 W5反思）

2026-04-28  多实例设计文档  SKILL_Butler多实例设计.md 完整重写：旧版 claim_task/increment_round/pending_revision 机制 → 新版 claim_round+lock_manager 双层锁架构；批次模式（1000WU/轮）；周期任务锁豁免（--skip-lock-check）；并发安全矩阵
2026-04-28  W0 v2→v2.1    六不变量第1条：「每轮只操作1页」→「每轮1000WU，batch_n=ceil(1000/WU)」（与实际批次模式对齐）
2026-04-28  W0 周期调度    D1 discover 参数标注 --top 60
2026-04-28  W1 v2→v2.1    discover_wanted/discover_corpus --top 20→60，--min-freq 3→2；P2<5条触发主动补货（不等 round%11）；Trail:Explore 阈值调整（> 20/10-20/5-10/< 5）；每次入队 5-15 条
2026-04-28  新增脚本       wiki/scripts/butler/cleanup_queue.py：Dream Round 用，归档 queue.md/housekeeping_queue.md 的 [x] 条目到 queue_done.md/housekeeping_done.md
2026-04-28  W5 v2→v2.1    Dream Round 新增固定步骤0：先执行 cleanup_queue.py 归档已完成条目，归档数记入反思报告

2026-04-28  W2 A2 v2→v2.1  enrich-page 增加「prose优先路径」判断分支：basic页 prose_chars<500 且已有PN≥1 时，直接添加叙事分析节，不强制新 corpus 搜索（R699 W5 Dream #5 B1修订；5次reflect验证prose不足是featured瓶颈）
2026-04-28  watchlist      新增8个新 shiji-kb skill 评估（W10h/W10x/W10r/W12/W10e/W10b/W10m/W10f/W10i）；W9/W10j/W10h升高优先级；W12/W10r/W10f/W10x排除；整理错位条目
2026-04-28  W0 v→  G-001批准  D1发现频率从round%11降为round%29（与W5合并同轮，W5优先）；discover_wanted连续枯竭（最近5次≤4条），高频空转无益

2026-04-28  W9 v1.0        新建：SKILL_W9_Butler页面图式反思.md；round%29触发（W5后执行）；4步流程（抽样→type分组→schema对比→输出反思文件）；三体type表8类（person/concept/law/technology/weapon/event/era/civilization/organization/place）
2026-04-28  W10 v→v2.1     内务任务表扩展：H1-H21 → H1-H25；新增H22(premium-scan)/H23(pn-audit)/H24(wikify)/H25(list-build)；更新描述/触发条件/相关Skill节
2026-04-28  W10h v1.0      新建：SKILL_W10h_Butler精品页增补.md（H22）；扫描featured页评估premium候选（score≥4/5：PN≥6+叙事分析+wikilink≥4+prose≥600+相关词条）；round%29触发；写入H-P2队列5-10条
2026-04-28  W10l v1.0      新建：SKILL_W10l_Butler引文PN一致性.md（H23）；正则扫描PN编号（B-CC-PPP）；B∉{1,2,3}→H-P1；CC>50或PPP>350→H-P2；round%29触发；修复时须corpus_search确认正确值
2026-04-28  W10c v1.0      新建：SKILL_W10c_Butler词汇链接化.md（H24）；alias_index来自pages.json；每词只替换首次出现；alias长度≥2字；H-P2每3轮插入；WU=20/页
2026-04-28  W10j v1.0      新建：SKILL_W10j_Butler列表页建设.md（H25）；静态Markdown列表页（不依赖:::query插件）；round%37触发；候选：舰船/面壁者/纪元/文明/技术/武器/组织/事件；WU=100/页
2026-04-28  watchlist      W9/W10h/W10l/W10c/W10j 从"高优先级候选"移入"已引入"；高优先级候选清零；中优先级移除W10c/W10l（已引入）

2026-04-28  W1 v2.1→v2.2  四大食物源：新增「源 D · 叙事场景扫描（名场面发现）」；D2 scene-scan 识别流程（三维度候选→排重→corpus验证→写入P1）；优先纳入标准（决定性行动/冲击性场景/高情感浓度/高引用段落）
2026-04-28  W2 D组+模板   新增 D2 scene-scan（WU 50）动作规范；WU速查表增加D2条目；页面格式模板后新增「名场面专用模板」（三段式：场景经过/象征意义/叙事地位）及7项自评checklist（含:::seealso要求）
