# Stage 3 替代路径 — 通过 HTML 渲染生成幻灯片

这是 imagegen 路径之外的第二条渲染分支。两条路径共用同一份 `analysis/slides.json` 与
`out/<主题>深度分析ppt生成prompt.md`，区别只在"每页用什么生成"：

| 路径 | 单页媒介 | 适合的 archetype | 优点 | 缺点 |
|---|---|---|---|---|
| **imagegen2** | PNG → SVG | hero、quote、装饰背景 | 视觉冲击力强 | 文字部分需在 PPT 层叠加 |
| **HTML**（本路径） | HTML → PNG / 直接 → PPTX | diagram、chart、matrix、timeline、comparison、recommendations | 文字与排版精确可控、可直接编辑 | 创意视觉表现力弱于 imagegen |

实际工程里**两条路径混用是默认推荐**：封面/章节扉页/数据点 用 imagegen，正文页（架构图、对比表、雷达图等）用 HTML。
`slides.json` 每条增加 `render: "html"|"imagegen"` 字段即可让 Stage 4 自动分流。

---

## 渲染流水

```
slides.json (含 render 标记)
   └─> Stage 3a (imagegen): images/png/slide-NN.png
   └─> Stage 3b (html):
         html/slide-NN.html
            └─> images/png/slide-NN.png （Playwright 截图）
            └─> 直接由 build_pptx.py 嵌入文本 + 截图
```

---

## 3b.1 生成单页 HTML

每页一个独立 HTML 文件 `html/slide-<NN>.html`，结构：

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>slide-<NN></title>
  <link rel="stylesheet" href="../html/_deck.css">
</head>
<body class="slide" data-archetype="<archetype>" data-n="<NN>">
  <header class="slide__title">
    <h1><!-- 主标题 --></h1>
    <p class="subtitle"><!-- 副标题（可选） --></p>
  </header>
  <main class="slide__body">
    <!-- 按 archetype 渲染：bullet 列表 / 表格 / SVG 图 / 时间线 / 矩阵 -->
  </main>
  <footer class="slide__footer">
    <span class="deck-title"><!-- 主题 --></span>
    <span class="page"><!-- N / total --></span>
  </footer>
</body>
</html>
```

`html/_deck.css` 一份模板，定义全局调色板、字体、栅格，保证整套幻灯片视觉一致。
**禁止在每页重复定义颜色与字体**——只允许调整布局。

### 推荐组件库

- **Tailwind CSS（CDN）** — 快速布局、间距、栅格。
- **Chart.js / ECharts** — 图表（柱状、折线、雷达、桑基）。
- **mermaid** — 流程图、时序图、ER。
- **D3** — 自定义可视化（雷达、力导图、产业链分层）。
- 字体：思源黑体 / 苹方 / Inter（Google Fonts CDN）。

> 离线场景下，先把上述资源缓存到 `html/vendor/` 再引用。

### 单页大小规范

```css
.slide { width: 1920px; height: 1080px; }  /* 16:9 */
```

转换时按 1× 截图即可；如果想要 Retina 清晰度，截图时用 deviceScaleFactor=2。

---

## 3b.2 HTML → PNG（截图）

用 Playwright 作为默认引擎（也可换 Puppeteer / wkhtmltopdf）：

```bash
python scripts/html_to_pptx.py shoot \
  --html-dir html \
  --out-dir images/png \
  --width 1920 --height 1080 --scale 2
```

脚本会：
1. 启动无头 Chromium。
2. 按文件名排序遍历 `html/slide-*.html`。
3. 截图为 `images/png/slide-<NN>.png`。

---

## 3b.3 直接组装为 PPTX（不经 SVG 也可）

HTML 路径有两种装配策略：

### 策略 A — 截图作背景，PPT 文本层叠加（推荐）

与 imagegen 路径一致：HTML 渲染出来的 PNG 直接当背景图，标题/要点交给 `build_pptx.py` 用真正的文本框绘制。这样文字保持可编辑，色彩与排版由 HTML 决定。

需要在 `slides.json` 中保留 `title / bullets`，并把 `visual.prompt` 改成 HTML 模板的 ID（如 `tpl: matrix-2x2`）。

### 策略 B — 整页截图，无文本层

仅在视觉非常密集（如复杂关系图）且不需后期手改文字时使用。`title / bullets` 留空即可。

### 策略 C — 不截图，直接把 HTML 内容映射到 PPT 形状

实验性。`scripts/html_to_pptx.py compose` 会解析 HTML 的若干"已知组件"（`<table>`、`<ul>`、
特定 class 的卡片块），生成对应的 python-pptx 形状。优点是完全可编辑，缺点是只支持有限组件，不
要在复杂自定义可视化上使用。

---

## 3b.4 与 `slides.json` 的契约

```json
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
        {"label": "MCP",  "scores": [3, 3, 4, 4, 4]}
      ]
    }
  },
  "visual": { "palette": "navy / cyan / off-white", "aspect": "16:9" },
  "speaker_notes": "...来源: [raw/02-methods.md]"
}
```

`html.template` 指向 `html/templates/<id>.html.j2`（Jinja2 模板）；`html.data` 是渲染上下文。
脚本 `scripts/html_to_pptx.py render` 会把模板 + 数据渲染为 `html/slide-<NN>.html`，再走 3b.2/3b.3。

模板库初始集合（按需扩充）：

- `cover-hero` — 封面
- `agenda-3col` — 三栏目录
- `section-divider` — 章节扉页
- `definition-2col` — 左定义右图示
- `landscape-cards` — 卡片墙
- `matrix-2x2` — 四象限
- `matrix-radar` — 雷达图
- `timeline-horizontal` — 横向时间线
- `architecture-layered` — 分层架构
- `comparison-table` — 三/四列对比
- `chart-bar`、`chart-line`、`chart-stacked`
- `recommendations-3` — 三条主张
- `data-point-hero` — 单一大数字
- `quote-pull` — 引文
- `references` — 引用清单

---

## 3b.5 校验

- [ ] 每页 HTML 在 1920×1080 范围内不出现滚动条。
- [ ] 字体已加载（不出现回退字体的方框/锯齿）。
- [ ] 颜色与 `slides.json[*].visual.palette` 一致。
- [ ] 截图后的 PNG 在 PPT 中按 16:9 满幅插入，无白边。
- [ ] 策略 A 下，PPT 文本层不挡住 HTML 中的关键视觉。

---

## 3b.6 何时选 HTML、何时选 imagegen

经验法则：

- 主张密集、需要表格 / 雷达 / 流程 / 时间线 / 对比矩阵 ⇒ **HTML**
- 封面、章节扉页、单一大数字、情绪化引文、装饰背景 ⇒ **imagegen**
- 拿不准时先 HTML（成本低、可改）；首页与扉页再用 imagegen 升一档质感。
