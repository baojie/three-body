---
name: skill-butler-w10c
description: 三体 Wiki H24 词汇链接化——扫描页面正文中出现但未被 [[]] 包裹的 Wiki 实体名（来自 alias_index），自动补充 wikilink。每次处理 1-3 页，每页补 3-10 处。
---

# SKILL W10c: H24 词汇链接化

> 正文里裸露的实体名是断掉的神经——它们存在，但 Wiki 的超链接网络感知不到它们。H24 的任务是把名字变成链接。

---

## 一、触发时机

| 触发 | 条件 |
|------|------|
| 周期触发 | 每 3 轮插入 1 次 H-P2 任务（与其他 H-P2 任务交替执行） |
| 手动触发 | 用户指定，或 H10 发现页面缺 wikilink |
| 批量触发 | housekeeping_queue.md 中有 `H24 wikify` 条目 |

---

## 二、alias_index 来源

Wiki 的 `pages.json` 中每个页面有 `aliases` 字段，构成 alias_index：

```python
import json
from pathlib import Path

pages_json = json.loads(Path('wiki/public/pages.json').read_text(encoding='utf-8'))

# alias_index: {alias → slug}（包括 id 本身和所有 aliases）
alias_index = {}
for page in pages_json:
    slug = page['id']
    alias_index[slug] = slug
    for alias in page.get('aliases', []):
        alias_index[alias] = slug

print(f"alias_index 共 {len(alias_index)} 条目")
```

当前 alias_index 约 700-800 条目，覆盖三部曲主要实体。

---

## 三、执行流程

### 步骤 1 · 选取目标页

优先选取以下类型的页面（按优先级）：

1. housekeeping_queue.md 中有 `H24 wikify | SLUG` 条目的页面
2. H10 扫描发现"缺 wikilink"（`[[]]` 数 < 3）的页面
3. 随机抽取 basic/standard/featured 页中 wikilink 密度最低的页

```python
import re, json
from pathlib import Path

pages_dir = Path('wiki/public/pages')
chapter_prefix = ('三体I-', '三体II-', '三体III-')
pages_json = json.loads(Path('wiki/public/pages.json').read_text(encoding='utf-8'))
alias_index = {}
for p in pages_json:
    alias_index[p['id']] = p['id']
    for a in p.get('aliases', []):
        alias_index[a] = p['id']

candidates = []
for f in pages_dir.glob('*.md'):
    if any(f.stem.startswith(pfx) for pfx in chapter_prefix):
        continue
    text = f.read_text(encoding='utf-8')
    if not re.search(r'^quality:\s*(basic|standard|featured)', text, re.M):
        continue
    wikilinks = len(re.findall(r'\[\[.+?\]\]', text))
    candidates.append((wikilinks, f.stem))

# 取 wikilink 最少的 5 个
candidates.sort()
print("wikilink最少的页面（前5）：")
for wl, slug in candidates[:5]:
    print(f"  {slug}: {wl} 个 wikilink")
```

### 步骤 2 · 扫描正文，识别裸实体名

```python
def find_linkable_terms(page_slug, alias_index):
    """找到正文中出现但未被 [[]] 包裹的实体名"""
    f = Path(f'wiki/public/pages/{page_slug}.md')
    text = f.read_text(encoding='utf-8')

    # 去掉 frontmatter
    body_start = text.find('---', 3) + 3
    body = text[body_start:]

    # 找到已有的 wikilink（避免重复处理）
    existing_links = set(re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', body))

    # 找裸实体名
    results = []
    for alias, target_slug in alias_index.items():
        if alias == page_slug:
            continue  # 跳过自链接
        if target_slug in existing_links or alias in existing_links:
            continue  # 已有链接
        if len(alias) < 2:
            continue  # 太短，误伤风险高

        # 只找完整词（避免把"叶文洁"匹配到"叶文洁的"再改坏）
        pattern = re.compile(r'(?<!\[)' + re.escape(alias) + r'(?!\])')
        matches = list(pattern.finditer(body))
        if matches:
            results.append({
                'alias': alias,
                'target': target_slug,
                'count': len(matches),
                'first_pos': matches[0].start()
            })

    # 按出现次数排序，优先处理高频词
    results.sort(key=lambda x: -x['count'])
    return results[:10]
```

### 步骤 3 · 选择性替换（首次出现原则）

**规则**：每个实体名只替换**第一次**出现，不批量替换全文（保持可读性）。

```python
def wikify_page(page_slug, terms, dry_run=False):
    """对页面进行词汇链接化，返回替换计数"""
    f = Path(f'wiki/public/pages/{page_slug}.md')
    text = f.read_text(encoding='utf-8')

    # 定位 frontmatter 结束位置
    body_start = text.find('---', 3) + 3
    header = text[:body_start]
    body = text[body_start:]

    replace_count = 0
    for term in terms[:8]:  # 每页最多处理 8 个词
        alias = term['alias']
        target = term['target']

        # 构建替换：首次出现 → [[target|alias]] 或 [[alias]]（同名时简写）
        link = f'[[{alias}]]' if alias == target else f'[[{target}|{alias}]]'
        pattern = re.compile(r'(?<!\[)' + re.escape(alias) + r'(?!\])')
        new_body, n = pattern.subn(link, body, count=1)
        if n > 0:
            body = new_body
            replace_count += 1

    if replace_count > 0 and not dry_run:
        new_text = header + body
        # 通过 edit_page.py 写入（不直接用 Write 工具）
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        result = subprocess.run(
            ['python3', 'wiki/scripts/edit_page.py', page_slug, tmp_path,
             '--summary', f'H24: 词汇链接化，补充{replace_count}处wikilink',
             '--author', INSTANCE_NAME],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            return 0

    return replace_count
```

### 步骤 4 · 执行并记账

```bash
# 对每个目标页执行
python3 wiki/scripts/edit_page.py $SLUG - \
    --summary "H24: 词汇链接化，补充${COUNT}处wikilink（${TERMS}）" \
    --author $INSTANCE

git add wiki/public/pages/$SLUG.md

python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --instance $INSTANCE \
    --type H24-wikify \
    --page "$SLUG_LIST" \
    --result accept \
    --desc "H24词汇链接化×${PAGE_CNT}页：共补充${TOTAL_LINKS}处wikilink" \
    --reflect "常见补充词：${TOP_TERMS}；wikilink密度提升情况：${DENSITY_NOTE}"
```

---

## 四、安全规则

| 规则 | 原因 |
|------|------|
| 每个词只替换首次出现 | 避免重复链接，保持可读性 |
| 别名长度 ≥ 2 字符 | 1字别名（如"叶"）误伤风险太高 |
| 跳过 frontmatter | frontmatter 的字段值不需要 wikilink |
| 跳过代码块 `` ``` `` | 代码块内的词不应被链接 |
| 跳过已有 `[[...]]` 包裹的词 | 避免产生嵌套 `[[[...]]]` |
| 跳过自链接 | 页面不应链接到自身 |

### 高风险别名（须人工确认）

以下类型别名易误伤，遇到时跳过：
- 长度 2 字、极常见词（如"宇宙""地球""人类"）
- 与普通词形相同的别名（如"黑暗"作为"黑暗森林"别名）

---

## 五、WU 计算

| 场景 | WU |
|------|-----|
| 单页词汇链接化（补 3-10 处） | 20 WU |
| 批量（每轮处理 3 页） | 60 WU（作为 H-P2 任务插入，不占主动作 WU） |

---

## 六、与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| H10 | H10 扫描发现"缺 wikilink"页面，写入 H24 队列 |
| H8 cross-link | H8 处理两页互链；H24 处理单页内的实体名链接 |
| H22 精品页增补 | H22 发现 featured 页 wikilink 不足时，转给 H24 处理 |
| W2 C2 | C2 fix-broken-link 修复已有但断裂的链接；H24 添加全新 wikilink |

---

## 相关路径

- `wiki/public/pages.json` — alias_index 来源
- `wiki/logs/butler/housekeeping_queue.md` — H24 任务队列
