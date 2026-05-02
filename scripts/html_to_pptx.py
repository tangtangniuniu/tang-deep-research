#!/usr/bin/env python3
"""
HTML 渲染分支的辅助脚本，提供三个子命令：

  render   ：从 slides.json + html/templates/<id>.html.j2 渲染出每页 html/slide-NN.html
  shoot    ：用 Playwright 把 html/slide-*.html 截图到 images/png/slide-NN.png
  compose  ：实验性 — 解析 HTML 中的已知组件，直接映射成 PPT 形状

最常用组合：
  python scripts/html_to_pptx.py render --slides analysis/slides.json --html-dir html
  python scripts/html_to_pptx.py shoot  --html-dir html --out-dir images/png

之后再走 scripts/build_pptx.py 装配 PPTX：
  python scripts/build_pptx.py --slides analysis/slides.json --svg-dir images/png --out out/<topic>.pptx

依赖：
  pip install jinja2 playwright python-pptx lxml
  playwright install chromium
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


# ---------- render ----------
def cmd_render(args: argparse.Namespace) -> int:
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        print("缺少依赖：pip install jinja2", file=sys.stderr)
        return 2

    slides_json = Path(args.slides)
    html_dir = Path(args.html_dir)
    tpl_dir = html_dir / "templates"
    out_dir = html_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not tpl_dir.exists():
        print(f"模板目录不存在：{tpl_dir}", file=sys.stderr)
        return 2

    plan = json.loads(slides_json.read_text(encoding="utf-8"))
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    rendered = 0
    for entry in plan:
        if entry.get("render") != "html":
            continue
        n = int(entry["n"])
        html_cfg = entry.get("html") or {}
        tpl_id = html_cfg.get("template")
        if not tpl_id:
            print(f"[skip] slide {n}: render=html 但未声明 html.template")
            continue
        tpl_path = f"{tpl_id}.html.j2"
        try:
            tpl = env.get_template(tpl_path)
        except Exception as e:
            print(f"[err] slide {n}: 模板 {tpl_path} 加载失败：{e}", file=sys.stderr)
            return 3

        ctx = {
            "n": n,
            "total": len(plan),
            "title": entry.get("title", ""),
            "subtitle": entry.get("subtitle", ""),
            "bullets": entry.get("bullets", []),
            "palette": (entry.get("visual") or {}).get("palette", ""),
            "data": html_cfg.get("data") or {},
            "deck_title": args.deck_title or "",
        }
        out_path = out_dir / f"slide-{n:02d}.html"
        out_path.write_text(tpl.render(**ctx), encoding="utf-8")
        rendered += 1
        print(f"[ok] {out_path}")

    print(f"完成：渲染 {rendered} 页 HTML 到 {out_dir}")
    return 0


# ---------- shoot ----------
async def _shoot(html_dir: Path, out_dir: Path, width: int, height: int, scale: int) -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("缺少依赖：pip install playwright && playwright install chromium", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    htmls = sorted(html_dir.glob("slide-*.html"))
    if not htmls:
        print(f"没有发现 {html_dir}/slide-*.html")
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page = await ctx.new_page()
        for html in htmls:
            n = html.stem.split("-")[-1]
            url = html.resolve().as_uri()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            png = out_dir / f"slide-{int(n):02d}.png"
            await page.screenshot(path=str(png), full_page=False, omit_background=False)
            print(f"[ok] {png}")
        await browser.close()
    return 0


def cmd_shoot(args: argparse.Namespace) -> int:
    return asyncio.run(
        _shoot(
            Path(args.html_dir),
            Path(args.out_dir),
            args.width,
            args.height,
            args.scale,
        )
    )


# ---------- compose (experimental) ----------
def cmd_compose(args: argparse.Namespace) -> int:
    print(
        "compose 子命令为实验功能：建议直接走 render + shoot + build_pptx。\n"
        "如需贡献组件解析器，请在 html/templates/ 中加 data-pptx-* 标记，并在此扩展。",
        file=sys.stderr,
    )
    return 1


# ---------- main ----------
def main() -> int:
    ap = argparse.ArgumentParser(description="HTML → PPTX 渲染分支辅助脚本")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("render", help="按 slides.json + Jinja2 模板生成每页 HTML")
    pr.add_argument("--slides", required=True)
    pr.add_argument("--html-dir", default="html")
    pr.add_argument("--deck-title", default="")
    pr.set_defaults(func=cmd_render)

    ps = sub.add_parser("shoot", help="用 Playwright 截图 html/slide-*.html → PNG")
    ps.add_argument("--html-dir", default="html")
    ps.add_argument("--out-dir", default="images/png")
    ps.add_argument("--width", type=int, default=1920)
    ps.add_argument("--height", type=int, default=1080)
    ps.add_argument("--scale", type=int, default=1)
    ps.set_defaults(func=cmd_shoot)

    pc = sub.add_parser("compose", help="实验：把 HTML 直接映射为 PPT 形状")
    pc.set_defaults(func=cmd_compose)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
