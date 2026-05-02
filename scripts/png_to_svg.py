#!/usr/bin/env python3
"""
PNG -> SVG converter for the deep-research skill.

Tries, in order: vtracer (color), potrace (1-bit), wrapper (PNG-in-SVG).
Writes one SVG per input PNG and a _report.json summarizing which backend
was used per slide.

Usage:
    python png_to_svg.py <png_dir> <svg_dir>
    python png_to_svg.py images/png images/svg
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def try_vtracer(png: Path, svg: Path) -> bool:
    """vtracer CLI. Returns True on success."""
    if not have("vtracer"):
        return False
    cmd = [
        "vtracer",
        "--input", str(png),
        "--output", str(svg),
        "--mode", "polygon",
        "--filter-speckle", "4",
        "--color-precision", "6",
        "--gradient-step", "16",
        "--corner-threshold", "60",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return r.returncode == 0 and svg.exists() and svg.stat().st_size > 0
    except Exception:
        return False


def try_potrace(png: Path, svg: Path) -> bool:
    """potrace pipeline: PNG -> 1-bit PBM -> SVG."""
    if not have("potrace"):
        return False
    try:
        from PIL import Image
    except ImportError:
        return False
    try:
        pbm = svg.with_suffix(".pbm")
        img = Image.open(png).convert("L")
        # threshold at 128
        bw = img.point(lambda p: 255 if p > 128 else 0, mode="1")
        bw.save(pbm)
        cmd = ["potrace", str(pbm), "-s", "-o", str(svg)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        try:
            pbm.unlink()
        except OSError:
            pass
        return r.returncode == 0 and svg.exists() and svg.stat().st_size > 0
    except Exception:
        return False


def wrap_png(png: Path, svg: Path) -> bool:
    """Always-available fallback: embed the PNG as a base64 <image> in an <svg>."""
    try:
        try:
            from PIL import Image
            with Image.open(png) as im:
                w, h = im.size
        except Exception:
            w, h = 1920, 1080
        b64 = base64.b64encode(png.read_bytes()).decode("ascii")
        out = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
            f'  <image href="data:image/png;base64,{b64}" '
            f'width="{w}" height="{h}"/>\n'
            f'</svg>\n'
        )
        svg.write_text(out, encoding="utf-8")
        return True
    except Exception as e:
        print(f"[wrapper] failed for {png}: {e}", file=sys.stderr)
        return False


def kb(p: Path) -> int:
    try:
        return round(p.stat().st_size / 1024)
    except OSError:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="PNG -> SVG converter")
    ap.add_argument("png_dir", type=Path)
    ap.add_argument("svg_dir", type=Path)
    ap.add_argument(
        "--prefer",
        choices=["vtracer", "potrace", "wrapper"],
        default="vtracer",
        help="Preferred backend; falls back if unavailable.",
    )
    args = ap.parse_args()

    png_dir: Path = args.png_dir
    svg_dir: Path = args.svg_dir
    if not png_dir.is_dir():
        print(f"png_dir not found: {png_dir}", file=sys.stderr)
        return 2
    svg_dir.mkdir(parents=True, exist_ok=True)

    # Try preferred first, then the rest.
    order_default = ["vtracer", "potrace", "wrapper"]
    order = [args.prefer] + [b for b in order_default if b != args.prefer]
    backends = {"vtracer": try_vtracer, "potrace": try_potrace, "wrapper": wrap_png}

    report = []
    pngs = sorted(p for p in png_dir.iterdir() if p.suffix.lower() == ".png")
    if not pngs:
        print(f"no .png files in {png_dir}", file=sys.stderr)
        return 1

    for png in pngs:
        svg = svg_dir / (png.stem + ".svg")
        used = None
        for backend in order:
            ok = backends[backend](png, svg)
            if ok:
                used = backend
                break
        if used is None:
            print(f"[FAIL] {png.name} — no backend produced output", file=sys.stderr)
            continue
        print(f"[{used:>7}] {png.name} -> {svg.name}  ({kb(png)} KB -> {kb(svg)} KB)")
        report.append(
            {
                "slide": png.stem,
                "backend": used,
                "input_kb": kb(png),
                "output_kb": kb(svg),
            }
        )

    (svg_dir / "_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
