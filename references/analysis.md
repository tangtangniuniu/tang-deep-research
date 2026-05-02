# Stage 2 + Stage 3 — 分析、切片、主题专属 prompt

本阶段会落出三件产物：

1. `analysis/outline.md` — 人类可读的分析综述。
2. `analysis/slides.json` — 机器可读的逐页计划（Stage 4/5 直接消费）。
3. `out/<主题>深度分析ppt生成prompt.md` — **由 `references/outline_template.md` 细化得到的主题专属提示词**，是 Stage 4 渲染时的唯一可信输入。

---

## `outline.md` 模板

```markdown
# <主题> — 深度分析

## 执行摘要
- <要点 1，≤25 字>
- <要点 2>
- <要点 3>
- <要点 4>
- <要点 5>

## 跨切主题
1. **<主题名>** — 是什么，在 raw/ 哪些文件里出现，为何重要。
2. **<主题名>** — ...
3. **<主题名>** — ...

## 张力与未解
- **<张力>** — 来源 A 说 X，来源 B 说 Y；分歧的影响是 Z。
- ...

## 推荐叙事弧
1. 框定问题（1–2 页）
2. 定义关键术语（1–2 页）
3. 现状与对手（3–5 页）
4. 玩家与生态（2–4 页）
5. 客户与采用信号（1–2 页）
6. 关键技术与成熟度（2–3 页）
7. 落地与里程碑（2–3 页）
8. 总结与建议（1–2 页）

## 来源覆盖矩阵
| 子题 | 强来源 | 薄/缺 |
|---|---|---|
| ... | ... | ... |
```

---

## `slides.json` schema（含双渲染分支）

```json
[
  {
    "n": 1,
    "title": "封面标题",
    "subtitle": "可选副标题 / 时间 / 团队",
    "bullets": [],
    "render": "imagegen",
    "html": null,
    "visual": {
      "type": "hero",
      "prompt": "Detailed imagegen prompt — see references/imagegen.md",
      "palette": "navy / cyan / off-white  #0B2545 #43B0F1 #F5F7FA",
      "aspect": "16:9"
    },
    "speaker_notes": "演讲者要说的内容；必须用 [raw/<file>.md] 标注来源。"
  },
  {
    "n": 14,
    "title": "关键技术雷达",
    "bullets": [],
    "render": "html",
    "html": {
      "template": "matrix-radar",
      "data": {
        "axes": ["可控性", "成熟度", "成本", "商业价值", "生态"],
        "items": [
          {"label": "RAG", "scores": [4, 5, 4, 5, 5]},
          {"label": "MCP", "scores": [3, 3, 4, 4, 4]}
        ]
      }
    },
    "visual": { "palette": "navy / cyan / off-white", "aspect": "16:9" },
    "speaker_notes": "..."
  }
]
```

### 字段说明

- `n` — 1-indexed 页码。
- `title` — 显示在幻灯片上的标题。
- `bullets` — 0–5 条要点；hero/quote/cover 多为空。
- `render` — `"html"` 或 `"imagegen"`，决定 Stage 4 走哪条分支。
- `html.template` — 仅 `render=="html"` 时必填，对应 `html/templates/<id>.html.j2`。
- `html.data` — 模板上下文（雷达分数、表格行、时间线节点等）。
- `visual.type` — `hero | diagram | chart | quote | timeline | matrix`，主要给 imagegen 用。
- `visual.prompt` — 完整 imagegen prompt body（STYLE GUARD 由脚本统一前置）。
- `visual.palette` — 调色板，**整套幻灯片必须一致**。
- `visual.aspect` — 默认 `"16:9"`。
- `speaker_notes` — 60–150 字，**必须** 用 `[raw/<file>.md]` 标注每条要点的来源。

### 默认渲染分支选择

| archetype | 默认 render | 说明 |
|---|---|---|
| cover、agenda、section-divider | `imagegen` | 视觉冲击 |
| data-point（单一大数字） | `imagegen` | 同上 |
| quote（引文页） | `imagegen` | 同上 |
| definition、architecture、landscape | `html` | 文本/图示精确 |
| matrix、timeline、chart、comparison | `html` | 数据驱动 |
| recommendations、references | `html` | 排版可控 |

`run.config.json:render_mode = "mixed"` 时按上表，`= "html"` 时全 html，`= "imagegen"` 时全 imagegen。

---

## Stage 3 — 由通用大纲细化为主题专属 prompt

### 流程

1. **打开** `references/outline_template.md`。
2. **逐节复制骨架**，逐占位符替换：
   - `<主题>` → 用户给的主题
   - `<PRIMARY/ACCENT/NEUTRAL/POSITIVE/WARN>` → 选定的调色板 hex
   - 章节名（默认"趋势分析 / 趋势判断 / 趋势动作"）按主题改写
   - 每页的"视觉描述"翻译/改写为本主题的具体画面
3. **生成英文 visual_prompt**：每页同步给一份英文版（imagegen 友好），即便该页 `render=="html"` 也写——日后切换分支时可用。
4. **填入要点与数据**：从 `raw/` 摘取，每条要点末尾追加 `[raw/<file>.md]` 引文标记。
5. **写出 `out/<主题>深度分析ppt生成prompt.md`**。
6. **同步回写 `analysis/slides.json`**：让两份产物每个字段都对得上（手工调一份后必须把另一份同步刷新）。

### 主题专属 prompt 的最小目录结构

````markdown
# <主题>深度分析 PPT 生成提示词

## 全局风格
- 主色: #0B2545（科技蓝）
- 强调色: #43B0F1（青蓝）
- 中性: #F5F7FA（极简白）
- 对比色: #2BB673 / #FF6B6B
- 字体: 标题 思源黑体 Heavy 36pt；正文 苹方 Regular 18pt；英文 Inter
- 风格基调: 扁平化 + 微拟物；多用节点网络、容器沙箱、流程箭头；克制留白
- Style guard (English, for imagegen): "Flat vector illustration, geometric shapes,
  crisp edges, no gradients or photographic noise, palette #0B2545 #43B0F1 #F5F7FA
  with #2BB673/#FF6B6B accents, generous negative space, sans-serif geometric type."

## 渲染模式
- mode: mixed
- 输出语言: zh-CN
- 篇幅: 25 页

## 渲染指令清单（Stage 4 checklist）
| 页 | 标题 | archetype | render | 模板 / prompt 摘要 |
|---|---|---|---|---|
| 1 | 封面 | cover | imagegen | "navy hero with neural-net globe" |
| 2 | 目录 | agenda | html | tpl: agenda-3col |
| ... | ... | ... | ... | ... |

## 逐页提示词

### 幻灯片 1：封面页
- archetype: cover
- 渲染分支: imagegen
- 布局: 居中标题大字号；左下角时间与团队；左 1/3 留白给标题。
- 视觉描述（中文）: 深蓝科技背景，发光的分布式网络节点连线，象征<主题英文关键词>。
- visual_prompt (English):
  > <STYLE GUARD>
  > HERO IMAGE for the cover of a deck about <topic in English>.
  > Composition: glowing distributed-graph globe, left third reserved as empty
  > negative space for the title. Mood: authoritative, forward-looking. No on-image text.
- 主标题: **<主题>深度分析报告**
- 副标题: <一句话主张>
- 关键要点: —
- 数据/引文: —
- speaker_notes: 一段 80–120 字开场，引用 [raw/01-definitions.md]。

### 幻灯片 2：目录页
- archetype: agenda
- 渲染分支: html
- 布局: 三栏卡片，每栏对应一段。
- visual_prompt (HTML 模板): tpl: agenda-3col；data 见 slides.json[1].html.data
- 主标题: 目录
- 关键要点: ["趋势分析", "趋势判断", "趋势动作"]
- speaker_notes: ...

...（共 N 页）
````

### 校验

- [ ] 每页都给出 `archetype / 渲染分支 / 布局 / 视觉描述 / visual_prompt(英文)`。
- [ ] 每条要点尾部都有 `[raw/<file>.md]` 引文标记。
- [ ] 调色板 hex 与字体只在"全局风格"出现一次，逐页不再单独写。
- [ ] 渲染指令清单与 `slides.json` 的 `n / render / template / visual.prompt` 完全对得上。
- [ ] 简体中文为主；引文与一手术语保留原语种。

---

## 切片档位（默认 25 页）

| 档位 | 页数 | 适用场景 |
|---|---|---|
| 高管简报 | 8–12 | 快读、决策点速览 |
| 标准深度分析 | 15–25 | **默认**；专题报告 |
| 完整白皮书形态 | 25–35 | 投资级 / 学术级 |

`run.config.json:slides_n` 决定档位；不要在不同 Stage 之间偷偷改篇幅。

---

## Stage 2/3 完成后的联检清单

- [ ] `outline.md / slides.json / out/<主题>深度分析ppt生成prompt.md` 三份产物都已写出。
- [ ] 每页要点都有来源回链。
- [ ] 调色板与字体一致；任意相邻两页不连续使用同一 archetype。
- [ ] `speaker_notes` 全部写齐。
- [ ] 与用户最后做一次内容对齐再进入 Stage 4。
