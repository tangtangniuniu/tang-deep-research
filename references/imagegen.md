# Stage 3 — Image generation with imagegen

> **默认语言约定**：幻灯片上的可读文字默认 **简体中文**（标题、要点、备注）；
> 但**喂给 imagegen 的 prompt 一律英文**——这是出图引擎的偏好。
> 所以本文档里的 prompt scaffold 全部保留英文，落到画面里的中文文字应交给
> Stage 5（PPTX 装配）的文本框去画，而不是写进 imagegen prompt。

Goal: produce one PNG per slide at 1920×1080, saved to `images/png/slide-<NN>.png`, and the prompt used saved to `images/png/slide-<NN>.prompt.txt`.

## Style guard (prepend to every prompt)

A consistent style across the deck is non-negotiable: it makes the deck feel designed *and* it makes Stage 4 vectorization far cleaner. Prepend this block to every imagegen call (tune palette per deck):

```
STYLE GUARD — apply to entire image:
- Flat vector illustration, geometric shapes, crisp edges, no gradients or photographic noise.
- Limited palette: <PALETTE — e.g. deep navy #0B2545, cyan #43B0F1, off-white #F5F7FA, soft coral accent #FF6B6B>.
- Generous negative space; composition reads at thumbnail size.
- Sans-serif geometric type if any text appears (Inter / Söhne style).
- No watermarks, no signatures, no UI chrome, no stock-photo aesthetic.
- Aspect ratio 16:9, 1920x1080.
```

The exact palette + style adjectives stay identical across all slides of the deck. Only the per-slide content changes.

## Per-archetype prompt scaffolds

### `hero` (cover, data point, recommendations)

```
<STYLE GUARD>
HERO IMAGE for the cover slide of a deck about <topic>.
Composition: <central metaphor — e.g. "abstract neural-network globe with data pulses">,
left third reserved as empty negative space for a title overlay.
Mood: <e.g. authoritative, forward-looking>.
No on-image text.
```

### `diagram`

```
<STYLE GUARD>
SYSTEM DIAGRAM showing <what>: <component A> on the left feeds into <component B>
in the center, which produces <output> on the right. Use labeled boxes connected
by arrows. Keep labels short. Background: subtle dotted grid in 8% opacity.
```

For diagrams, prefer to keep textual labels off the image and add them via the slide's text frame in Stage 5 — this avoids OCR-quality issues after vectorization.

### `chart`

```
<STYLE GUARD>
BAR CHART (or LINE / RADAR) visualizing <metric> across <categories>.
Use the deck palette. No axis labels — those are added on the slide layer.
Composition fills the right two-thirds; left third is blank for callouts.
```

### `quote`

```
<STYLE GUARD>
DECORATIVE BACKGROUND for a pull quote. Large oversized quotation-mark
glyph in palette accent color, lower-right. Otherwise mostly empty canvas.
No text.
```

### `timeline`

```
<STYLE GUARD>
HORIZONTAL TIMELINE graphic. Spine runs left-to-right at the vertical center.
<N> milestone markers spaced evenly. Each marker a labeled circle node;
keep marker labels short (≤2 words). Years above the spine, descriptions below.
```

### `matrix`

```
<STYLE GUARD>
2x2 MATRIX (Gartner-magic-quadrant style). Axes labeled <X-axis> (horizontal)
and <Y-axis> (vertical). Four quadrants subtly tinted in the deck palette.
Place <N> labeled bubbles for the players: <list>. Bubbles sized by <metric>.
```

## Vectorization-friendly prompt rules

These traits make Stage 4 much cleaner:

- **Flat colors > gradients.** vtracer collapses gradients into many tiny color regions.
- **Crisp edges > soft shadows.** Soft drop-shadows become noisy halos in SVG.
- **Solid fills > textures.** Cross-hatching, paper texture, film grain all blow up the SVG path count.
- **Few colors > many colors.** 4–6 palette colors keep the SVG small and editable.
- **Big shapes > tiny details.** Small details below ~8px get lost or noisy after tracing.

Add this negative-prompt suffix:

```
NEGATIVE: photorealism, photographic texture, gradient mesh, film grain,
soft shadow, glow, lens flare, paper texture, noise, watermark, signature.
```

## Reproducibility

For each slide write the exact prompt you used (style guard + body + negative) to `images/png/slide-<NN>.prompt.txt`. If the user later asks "regenerate slide 7 with a different metaphor", the diff is obvious.

## Checkpoint

Render all PNGs, then show the user a contact sheet (e.g. via `montage` or a simple HTML index) before vectorizing. Re-rendering a single PNG is cheap; re-doing the whole pipeline after the PPTX is built is not.
