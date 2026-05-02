# Stages 4 & 5 — 矢量化与 PPTX 装配

> **默认输出语言**：幻灯片正文与备注一律 **简体中文**；引文保留原语种。
> 字体推荐：中文 思源黑体 / 苹方；英文 Inter / Söhne。
> SVG 路径只服务 imagegen 分支；HTML 路径直接用截图作背景，跳过 SVG。

## Vectorization — PNG → SVG

`scripts/png_to_svg.py` tries three backends in order, picking the first one available on the system. PowerPoint 2016+ accepts all three formats and lets the user right-click → *Convert to Shape* to make the SVG fully editable as native PPT shapes.

### Backend 1 — `vtracer` (preferred, color)

Best for the flat illustrations Stage 3 produces. Produces multi-color path SVGs.

```bash
# Install once:
cargo install vtracer        # or: pip install vtracer
```

Tuning knobs that matter:

| Flag | Default in script | Effect |
|---|---|---|
| `--mode polygon` | `polygon` | crisp polygons (vs. `spline` for curves) |
| `--filter-speckle 4` | `4` | drops noise smaller than N px |
| `--color-precision 6` | `6` | quantization bits per channel; lower = fewer colors |
| `--gradient-step 16` | `16` | merges similar colors |
| `--corner-threshold 60` | `60` | how aggressively to keep corners |

If the PNG has gradients, raise `--gradient-step` to 24–32. If output is ballooning past ~2 MB per slide, lower `--color-precision` to 4.

### Backend 2 — `potrace` (1-bit, line-art only)

```bash
sudo apt-get install potrace
```

The script first thresholds the PNG to 1-bit, then runs potrace. Use only if vtracer is unavailable and the image is monochrome line art.

### Backend 3 — Wrapper SVG (always works, no deps)

Wraps the PNG as a base64-embedded `<image>` inside an `<svg>`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080">
  <image href="data:image/png;base64,..." width="1920" height="1080"/>
</svg>
```

This is always editable in the sense that PowerPoint can crop, recolor, and overlay shapes on it. It is *not* truly editable as vectors — the user gets the original raster inside an SVG envelope. Mark the slide as `wrapped` in `_report.json` so the user knows.

### Output report

The script writes `images/svg/_report.json`:

```json
[
  {"slide": 1, "backend": "vtracer", "input_kb": 421, "output_kb": 188},
  {"slide": 2, "backend": "wrapper", "input_kb": 380, "output_kb": 510},
  ...
]
```

Slides that fell back to `wrapper` are candidates for re-rendering with a more vector-friendly prompt and re-tracing.

## PPTX assembly

`scripts/build_pptx.py` uses `python-pptx` plus a small lxml shim to register `image/svg+xml` so PowerPoint, Keynote, and LibreOffice all open the file cleanly.

### Layout

- 16:9, 13.333" × 7.5" (PowerPoint default widescreen).
- Each slide:
  1. Background: full-bleed SVG (`images/svg/slide-<NN>.svg`).
  2. Foreground:
     - Title text frame at top-left, ~9" wide.
     - Bullets text frame below the title, aligned to whichever third of the slide the visual prompt left empty.
     - Footer with deck title (left) and slide number (right).
  3. Notes pane: `speaker_notes` from `slides.json`.

### Theme

- Title font: 36 pt, bold, palette primary.
- Body font: 18 pt, palette neutral.
- Footer font: 10 pt, 60% opacity.
- Color theme matches the palette declared in `slides.json[0].visual.palette`.

If the user wants a custom master, drop a `template.pptx` next to `build_pptx.py` and pass `--template template.pptx`. The script will use its slide masters and only inject content + SVG.

### Editability checklist (after opening the .pptx)

1. SVG appears as a single picture per slide.
2. Right-click on the SVG → *Convert to Shape* converts vtracer output to native, editable PPT shapes (color, stroke, individual element selection).
3. Title and bullet text are real text frames, not flattened into the image.
4. Speaker notes are populated.
5. Slide masters carry the theme colors, so a global recolor only touches the master.

### Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| SVG renders as a gray box in PowerPoint | Missing content-type override | The script inserts `<Default Extension="svg" ContentType="image/svg+xml"/>` — verify it's present |
| "Convert to Shape" disabled | SVG is wrapper-mode (PNG inside SVG) | Re-render the slide with a more vector-friendly prompt and re-trace with vtracer |
| Title overlaps the illustration | Visual prompt didn't reserve negative space | Update the prompt's "left third reserved" instruction and re-render |
| File size > 50 MB | Too many SVG paths | Lower vtracer `--color-precision` and re-trace |

### Final deliverable

`out/<topic>.pptx` plus, optionally:

- `out/<topic>-handout.pdf` — exported via `libreoffice --headless --convert-to pdf`.
- `out/<topic>-thumbnails.png` — contact sheet for review.
