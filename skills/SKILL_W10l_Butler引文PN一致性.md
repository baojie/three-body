---
name: skill-butler-w10l
description: 三体 Wiki H23 引文PN一致性——正则扫描全库 PN 格式（B-CC-PPP），检测超出范围的编号（B∉{1,2,3}、CC>50、PPP>350），写入 H-P1/H-P2 修复队列。
---

# SKILL W10l: H23 PN 一致性审查

> 引文编号是 Wiki 的"原文血脉"——格式混乱或范围越界的 PN 等于断线，H23 的任务是找到它们并安排修复。

---

## 一、三体 PN 格式规范

```
（B-CC-PPP）
```

| 字段 | 含义 | 合法范围 |
|------|------|---------|
| B | 部 (Book)：1=《三体》，2=《黑暗森林》，3=《死神永生》 | `1`、`2`、`3` |
| CC | 章 (Chapter)，两位数字 | `01`–`50`（不同书章数不同，见下表） |
| PPP | 页（原文段落行号映射），三位数字 | `001`–`350` |

### 各书章数上限（参考）

| 书 | 最大章号 |
|----|---------|
| 三体（B=1） | 约 39 章 |
| 黑暗森林（B=2） | 约 38 章 |
| 死神永生（B=3） | 约 50 章 |

**注**：实际编号以语料文件 `corpus/utf8/` 为准，H23 扫描时可宽松用 CC≤50。

---

## 二、触发时机

| 触发 | 条件 |
|------|------|
| 周期触发 | `round % 29 == 0`（与 W5/W9/W10h 同轮，最后执行） |
| 手动触发 | 用户指定，或 H10 发现批量 PN 问题 |
| 自动条件 | featured 页 PN 总量 ≥ 1000 条（已满足） |

---

## 三、执行流程

### 步骤 1 · 正则扫描全库

```python
import re
from pathlib import Path

pages_dir = Path('wiki/public/pages')
chapter_prefix = ('三体I-', '三体II-', '三体III-')
PN_RE = re.compile(r'（(\d+)-(\d+)-(\d+)）')

issues = []

for f in sorted(pages_dir.glob('*.md')):
    if any(f.stem.startswith(p) for p in chapter_prefix):
        continue
    text = f.read_text(encoding='utf-8')
    for m in PN_RE.finditer(text):
        b, cc, ppp = int(m.group(1)), int(m.group(2)), int(m.group(3))
        errs = []
        if b not in (1, 2, 3):
            errs.append(f"B={b}（须为1/2/3）")
        if cc == 0 or cc > 50:
            errs.append(f"CC={cc:02d}（须01-50）")
        if ppp == 0 or ppp > 350:
            errs.append(f"PPP={ppp:03d}（须001-350）")
        if errs:
            issues.append({
                'slug': f.stem,
                'pn': m.group(0),
                'errors': errs,
                'context': text[max(0, m.start()-30):m.end()+30].replace('\n', '↵')
            })

print(f"发现 {len(issues)} 个 PN 格式问题：")
for i in issues[:30]:
    print(f"  {i['slug']:30s} {i['pn']:15s} {', '.join(i['errors'])}")
    print(f"    上下文: ...{i['context']}...")
```

### 步骤 2 · 分级写入修复队列

```python
# B 字段错误 → H-P1（影响溯源，高优先）
# CC/PPP 越界 → H-P2（格式问题，常规优先）

p1_lines = []
p2_lines = []

for i in issues:
    b_error = any('B=' in e for e in i['errors'])
    line = f"- [ ] H23 pn-fix | {i['slug']} | {i['pn']} {', '.join(i['errors'])}"
    if b_error:
        p1_lines.append(line)
    else:
        p2_lines.append(line)

print(f"\nH-P1（B字段错误）：{len(p1_lines)} 条")
for l in p1_lines[:10]:
    print(l)
print(f"\nH-P2（CC/PPP越界）：{len(p2_lines)} 条")
for l in p2_lines[:10]:
    print(l)
```

将输出追加到 `wiki/logs/butler/housekeeping_queue.md`。

### 步骤 3 · 记录扫描结果

```bash
python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --instance $INSTANCE \
    --type H23-pn-audit \
    --page "" \
    --result accept \
    --desc "H23 PN一致性扫描：扫描${TOTAL}页，发现${FOUND}个格式问题，写入H-P1×${P1_CNT}+H-P2×${P2_CNT}" \
    --reflect "最常见错误类型：${TOP_ERR}；问题集中页面：${PROBLEM_PAGES}" \
    --skip-lock-check
```

---

## 四、修复执行（H23 pn-fix 动作）

当 housekeeping_queue.md 中出现 `H23 pn-fix | SLUG | ...` 条目时，执行：

1. 读原页面，定位错误 PN
2. 用 `corpus_search.py` 验证该段落的正确 PN（必须从 corpus 确认）
3. 用 `edit_page.py` 替换：`python3 wiki/scripts/edit_page.py SLUG - --summary "H23: 修正PN格式 ${OLD}→${NEW}" --author $INSTANCE`
4. 若无法从 corpus 确认正确 PN，改为 `（待考证）` 标注，不猜测

### 常见错误模式

| 错误 | 可能原因 | 修复策略 |
|------|---------|---------|
| B=0 或 B=4 | 手误 | corpus 查原文确认是哪部书 |
| CC=00 | 前导零丢失被解释为 0 | 确认章号，补前导零 |
| PPP=000 | 占位符未填写 | corpus 搜索段落确认真实行号 |
| PPP>350 | 旧格式或笔误 | corpus 确认，超过范围则截断或标注 |

---

## 五、与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| W2 B2 | B2 add-pn 是正常添加新 PN；H23 是修复已有 PN 格式错误 |
| W3 | W3 质量标准要求 PN 在 blockquote 内，H14 修格式；H23 修编号范围 |
| H14 | H14 修 PN 位置（在 blockquote 外）；H23 修 PN 编号内容 |
| H10 | H10 扫描时可顺带发现 PN 格式问题，写入 H23 队列 |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H23 问题写入 H-P1/H-P2
- `corpus/utf8/` — 用于验证 PN 正确值
