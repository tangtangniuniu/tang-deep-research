# Stage 1 — Gathering raw materials

资料收集有 **三条互斥的路径**，由 Stage 0（在 `SKILL.md` 中）询问用户后决定走哪一条：

| 分支 | 触发条件 | 行为 |
|---|---|---|
| **A. 参考文档目录** | 用户提供了 `--refs <dir>` 或在对话中给出文档目录路径 | 直接读取该目录下所有 `*.md / *.pdf / *.docx / *.txt / *.html`，结构化为 `raw/<NN>-<slug>.md` |
| **B. 本地资料库** | 用户指明"使用本地资料"但未给出明确目录 | 询问目录，落到分支 A |
| **C. 联网调研（默认）** | 用户未提供任何资料 | 走 `deep-research` 子技能，按下文 1.3 的方式映射输出到 `raw/` |

无论走哪条路径，**所有下游阶段（分析 / 切片 / 渲染 / 装配）都只读 `raw/` 目录**。这条不变量保证不同来源的主题处理流程完全一致。

`WebSearch` / `WebFetch` 直接调用仅用作 **gap-filling**：用户审阅 `raw/` 后要求补强某子题时再用。

## 分支 A — 直接分析参考文档目录

当用户在 Stage 0 给出 `--refs <dir>`（或在交互中指定一个本地目录），跳过 `deep-research` 调用，直接处理该目录。

### A.1 入口检查

```bash
test -d "$REFS_DIR" && find "$REFS_DIR" -maxdepth 3 -type f \
  \( -iname '*.md' -o -iname '*.markdown' -o -iname '*.txt' \
     -o -iname '*.pdf' -o -iname '*.docx' -o -iname '*.html' -o -iname '*.htm' \) \
  | sort
```

把命中的清单回报给用户，让用户确认或剔除文件。

### A.2 文档解析

按文件类型选择读取方式：

| 类型 | 读取方式 |
|---|---|
| `.md / .txt / .markdown` | `Read` 工具直接读 |
| `.pdf` | 调用 `pdf` skill 抽取正文与表格 |
| `.docx` | 调用 `docx` skill 抽取正文 |
| `.html / .htm` | 用 `Read` 读取，简单去标签即可（保留链接） |
| `.xlsx / .csv` | 调用 `xlsx` skill；通常只在数据型主题用到 |

读取时 **保留原文章节标题**，方便后续按章节切桶。

### A.3 主题与子题判定

依据用户给出的 `--topic` 与已读到的目录摘要，先草拟一份 **子题分桶表**（默认 6 桶，可根据实际内容增删）：

```
01-definitions   — 定义、范畴、术语对齐
02-methods       — 方法、技术路线、模型/算法
03-standards     — 标准、规范、法规
04-vendors       — 厂商/产品/方案
05-adoption      — 用户/案例/规模化采用
06-challenges    — 挑战、争议、未解问题
```

子题表先和用户确认，再开始整理。

### A.4 写出 `raw/<NN>-<slug>.md`

对每一桶，按 `example.md` 风格组织成单文件：

```markdown
### <N>. <子题标题（中文）>

<2–4 段综述。来自参考文档 1/2/3 的关键论点融合后改写；
保留专有名词原文并括注译名；保留原文公式与关键数字。>

#### 关键来源
- <文档名 / 章节> — <相对路径>  (<一句话要点>)
- ...

#### 重要引文 / 数据点
> "<原文引文>"
> — <文档名>，<页码 / 章节>

#### 引用清单
- <作者/机构>, "<标题>", <出处>, <年份>. <DOI / URL>     [src: <doc-id>]

#### 相关公司 / 项目（如适用）
- <名称> — <一句话定位> — <URL 或文档定位>
```

> **doc-id 约定**：用文件名去后缀小写化作为 `doc-id`（例：`whitepaper-2025q4` → `src: whitepaper-2025q4`）。Stage 2 的 `speaker_notes` 必须用这个 id 回链。

### A.5 manifest

```json
{
  "topic": "...",
  "language": "zh-CN",
  "source_mode": "refs",
  "refs_root": "/abs/path/to/refs/",
  "documents": [
    {"doc_id": "whitepaper-2025q4", "path": "whitepaper.pdf", "pages": 38, "summary": "..."},
    ...
  ],
  "buckets": [
    {"file": "raw/01-definitions.md", "title": "...", "doc_ids": ["whitepaper-2025q4", ...]}
  ]
}
```

写入 `raw/_manifest.json`。

### A.6 校验

- [ ] 每个 `raw/<NN>-<slug>.md` 至少 2 处来源，否则在 manifest 标 `thin: true` 并提示用户是否需要联网补充（此时切到分支 C 做"靶向补查"）。
- [ ] 不丢失任何带数字/年份/标准号的原文片段。
- [ ] 引文一律保留原语种。

---

## 分支 B — 本地资料库（无明确目录）

当用户说"用本地资料"但没指明目录时：

1. 列出常见候选位置，让用户挑：`./refs`、`./docs`、`~/Documents`、`~/Downloads`、用户明确给出的路径。
2. 选定后回到分支 A。
3. 若用户最终决定不使用本地资料，切到分支 C。

---

## 分支 C — 联网调研（委派给 `deep-research` 子技能）

当用户没有提供任何参考资料时，走这条默认路径。下文与原版一致。

```bash
ls ~/.claude/skills/deep-research/SKILL.md 2>/dev/null \
  && echo "deep-research: installed" \
  || npx skills add https://github.com/199-biotechnologies/claude-deep-research-skill --skill deep-research
```

If `npx skills add` fails (no marketplace plugin / offline), fall back to:

```bash
git clone https://github.com/199-biotechnologies/claude-deep-research-skill ~/.claude/skills/deep-research
pip install -r ~/.claude/skills/deep-research/requirements.txt
```

A fresh install requires reloading Claude Code so the Skill tool sees it. Tell the user.

## Invocation contract

Always pass the user's topic verbatim plus a scoping block. Recommended prompt skeleton:

```
Topic: <user-supplied topic, untranslated>
Audience: <e.g. CTO and chief architects, mixed technical depth>
Language: zh-CN（默认；保留原语种引文与一手术语）
Time horizon: <e.g. last 2 years; include landmark older papers>
Mode: <quick | standard | deep | ultradeep>   # default: standard
Coverage requirements:
  - Definitions / taxonomy of the field
  - Technical methods & state of the art (academic + arXiv)
  - Standards bodies & specs (3GPP, ETSI, TM Forum, ITU-T, IEEE, CCSA, etc.)
  - Vendor / company landscape (whitepapers, datasheets)
  - Operator / customer adoption (case studies)
  - Open challenges & research frontier
```

Mode picks:

| Mode | When |
|---|---|
| `quick` | exploratory first pass, scope-checking |
| `standard` | default for deck production |
| `deep` | board-level / investment-grade decks |
| `ultradeep` | full white paper + 30+ slide deck |

## Output paths

`deep-research` writes to `~/Documents/<Topic>_Research_<YYYYMMDD>/`. Capture this path as `$DR_OUT`. Key files:

| File | What it contains |
|---|---|
| `*.md` | assembled report (Executive Summary, Findings, Synthesis, Limitations, Recs, Bibliography) |
| `sources.jsonl` | canonical source registry — `{id, title, url, kind, year, authors, ...}` |
| `evidence.jsonl` | one row per quote/data-point — `{claim_id, source_id, quote, locator, ...}` |
| `claims.jsonl` | atomic claims with support status |
| `run_manifest.json` | query, mode, assumptions, provider config |

## Mapping `$DR_OUT` → `raw/`

The goal is a `raw/` directory that *reads like a longer, richer `example.md`*. Each subtopic is its own file. Algorithm:

1. **Decide the subtopic taxonomy.** Default 6 buckets (rename / add / drop based on the topic):
   - `01-definitions.md`
   - `02-methods.md`
   - `03-standards.md`
   - `04-vendors.md`
   - `05-adoption.md`
   - `06-challenges.md`
2. **Walk the report `*.md`** in `$DR_OUT`. Section-by-section, decide which bucket each section belongs to. A long "Findings" section in the report typically splits across multiple buckets.
3. **For each bucket**, build a single Markdown file with this template (mirrors `example.md`):

   ```markdown
   ### <N>. <subtopic title in user's target language>

   <2–4 paragraph synthesis stitched from the matching report sections.
   Keep claim numbers `[N]` from the report; translate prose; preserve
   technical terms in the original language in parentheses on first use.>

   #### Key sources
   - <Source.title> — <Source.url>  (<one-line takeaway>)
   - ...

   #### Notable quotes / data points
   > "<Evidence.quote in original language>"
   > — <Source.title>, <Source.year> [<Source.id>]

   #### Citations
   - <Authors>, "<Title>", <Venue>, <Year>. <DOI / arXiv ID / URL>     [id: <Source.id>]

   #### Related companies / projects
   - <Name> — <one-line description> — <URL>
   ```

4. **Filter `sources.jsonl` per bucket.** Use the `claim → source` mapping in `claims.jsonl` + `evidence.jsonl`: only list sources that actually back a claim appearing in this bucket. Keep `Source.id` as a stable key — Stage 2 (analysis) will reuse it in `speaker_notes`.
5. **Pull quotes from `evidence.jsonl`.** Pick the 2–4 most-cited evidence rows per bucket; keep the original-language quote intact, render attribution in the user's target language.
6. **Write `raw/_manifest.json`** with:
   ```json
   {
     "topic": "...",
     "language": "zh-CN",
     "source_mode": "deep-research",
     "deep_research_run": "/abs/path/to/$DR_OUT",
     "deep_research_manifest": "<copy of run_manifest.json>",
     "buckets": [
       {"file": "raw/01-definitions.md", "title": "...", "source_ids": ["s12","s47"]}
     ]
   }
   ```
   This makes every claim in `raw/` traceable back to a row in `evidence.jsonl`.

7. **Do not delete `$DR_OUT`.** Stages 2 and beyond may need to chase a specific evidence row.

## Source-quality heuristics

`deep-research` already enforces "10+ sources, 3+ per major claim, cluster-independent". When mapping to `raw/`, additionally prefer (in order):

1. **Peer-reviewed papers** — TKDE, NeurIPS, ICLR, KDD, INFOCOM, JSAC, etc.
2. **Standards documents** — 3GPP TS/TR, ETSI ISG specs, TM Forum IGs, IEEE standards. Cite spec ID + release.
3. **Vendor primary docs** — whitepapers / datasheets from the vendor's own domain. Note publication date.
4. **Reputable analyst summaries** — Gartner, IDC, Omdia, McKinsey, BCG.
5. **Trade press** — Light Reading, RCR Wireless, Telecoms.com, 通信世界, C114.

Demote in `raw/` (or drop): undated blogs, SEO content farms, AI-generated summary sites with no original reporting.

## Gap-filling pass (optional)

If after mapping the user identifies a thin bucket:

- Prefer **re-invoking `deep-research`** with a focused sub-query (e.g. *"Deep dive: 3GPP Release 18 SA5 management & orchestration AI/ML items"*). Append its outputs into `$DR_OUT` and re-run the mapping for the affected bucket only.
- Only fall back to direct `WebSearch` + `WebFetch` for very narrow, time-sensitive lookups (e.g. a press release from yesterday). When you do, append rows to `sources.jsonl` and `evidence.jsonl` manually so the citation chain stays intact.

## Anti-patterns

- **Don't paraphrase the assembled report into `raw/` without preserving citation IDs.** Stage 2's `speaker_notes` rule depends on those IDs.
- **Don't merge buckets** prematurely; keep one file per subtopic so analysis can re-balance later.
- **Don't write conclusions yet** — that is Stage 2.
- **Don't run direct web searches as the primary gathering path** — that's what the upstream skill is for. Doing both leads to duplicate, conflicting evidence stores.

## Checkpoint

After `raw/` is populated, list the files for the user with a one-line summary of each, flag thin buckets, and ask whether to broaden coverage before moving to analysis.
