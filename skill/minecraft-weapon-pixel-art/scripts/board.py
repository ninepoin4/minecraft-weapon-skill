#!/usr/bin/env python3
"""Fixed 32x32 Minecraft weapon pixel board.

Commands:
  init    Create a blank 32x32 spec with a material theme.
  render  Render a spec to PNG, previews, silhouette and validation.json.

The board is deliberately fixed at 32x32. Do not resize the output to repair
a design; redraw on the board instead.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # Pillow is a hard runtime dependency
    raise SystemExit(
        "board.py needs Pillow, but it is not importable.\n"
        "Install it with:\n"
        f"    {sys.executable} -m pip install -r "
        f"{Path(__file__).resolve().parent.parent / 'requirements.txt'}\n"
        f"(import error: {exc})"
    ) from None

SIZE = 32
ROOT = Path(__file__).resolve().parent.parent
PALETTE_PATH = ROOT / "assets" / "palette.json"
TEMPLATES = ROOT / "templates"
PRIMARY_THEMES = [
    "steel", "deepslate", "emerald", "echo", "sculk", "copper", "redstone",
    "honey", "amber", "crystal", "ender", "amethyst", "magnetite",
    "obsidian", "tidal", "prismarine", "shell", "seaweed", "blaze",
]
TEMPLATE_NAMES = ["crystal_saber"]

PREVIEW_SCALE = 8
BG_MID = (110, 110, 110, 255)
BG_LIGHT = (216, 216, 216, 255)
BG_DARK = (43, 43, 43, 255)


def load_palette() -> dict:
    return json.loads(PALETTE_PATH.read_text(encoding="utf-8"))


def parse_color(value) -> tuple[int, int, int, int]:
    if value is None:
        return (0, 0, 0, 0)
    s = str(value).strip().lstrip("#")
    if len(s) == 6:
        s += "FF"
    if len(s) != 8:
        raise ValueError(f"bad color {value!r}; use #RRGGBB or #RRGGBBAA")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4, 6))


def theme_palette(primary: str, grip: str, secondary: str | None = None) -> dict:
    themes = load_palette()
    if primary not in themes:
        raise SystemExit(f"unknown primary {primary!r}; choose from {sorted(themes)}")
    if grip not in themes:
        raise SystemExit(f"unknown grip {grip!r}; choose from {sorted(themes)}")
    p = themes[primary]
    g = themes["gold"]
    w = themes[grip]
    if "highlight" not in p:
        raise SystemExit(f"theme {primary!r} has no highlight ramp")
    for key in ("deep", "shadow", "base", "light"):
        if key not in w:
            raise SystemExit(f"grip theme {grip!r} lacks {key}")
    palette = {
        "X": "#FF00FF",
        "D": p["deep"],
        "S": p["shadow"],
        "B": p["base"],
        "L": p["light"],
        "H": p["highlight"],
        "G": g["deep"],
        "g": g["shadow"],
        "y": g["base"],
        "Y": g["light"],
        "w": w["deep"],
        "u": w["shadow"],
        "o": w["base"],
        "k": w["light"],
    }
    if secondary:
        if secondary not in themes:
            raise SystemExit(f"unknown secondary {secondary!r}; choose from {sorted(themes)}")
        s = themes[secondary]
        if "highlight" not in s:
            raise SystemExit(f"secondary theme {secondary!r} has no highlight ramp")
        palette.update({
            "d": s["deep"],
            "s": s["shadow"],
            "b": s["base"],
            "l": s["light"],
            "h": s["highlight"],
        })
    return palette


def load_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    rows = spec.get("rows")
    if not isinstance(rows, list) or len(rows) != SIZE:
        raise SystemExit(f"{path}: 'rows' must be a list of exactly {SIZE} strings")
    for i, row in enumerate(rows):
        if not isinstance(row, str) or len(row) != SIZE:
            raise SystemExit(f"{path}: row {i} must be exactly {SIZE} characters")
    palette = spec.get("palette")
    if not isinstance(palette, dict):
        raise SystemExit(f"{path}: missing 'palette' object")
    return spec


def render_image(spec: dict) -> tuple[Image.Image, set[tuple[int, int]]]:
    palette = spec["palette"]
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    placeholder = set()
    for y, row in enumerate(spec["rows"]):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch not in palette:
                raise SystemExit(f"row {y}, column {x}: unknown palette key {ch!r}")
            if ch == "X":
                placeholder.add((x, y))
            im.putpixel((x, y), parse_color(palette[ch]))
    return im, placeholder


def preview(im: Image.Image, out: Path, bg: tuple[int, int, int, int]) -> None:
    canvas = Image.new("RGBA", (SIZE * PREVIEW_SCALE, SIZE * PREVIEW_SCALE), bg)
    scaled = im.resize((SIZE * PREVIEW_SCALE, SIZE * PREVIEW_SCALE), Image.Resampling.NEAREST)
    canvas.alpha_composite(scaled)
    canvas.convert("RGB").save(out)


def silhouette(im: Image.Image, out: Path) -> None:
    preview(silhouette_image(im), out, BG_LIGHT)


def grid_preview(im: Image.Image, out: Path, scale: int = 16) -> None:
    canvas = Image.new("RGBA", (SIZE * scale, SIZE * scale), BG_MID)
    canvas.alpha_composite(im.resize((SIZE * scale, SIZE * scale), Image.Resampling.NEAREST))
    d = ImageDraw.Draw(canvas)
    for i in range(SIZE + 1):
        color = (255, 255, 255, 170) if i % 4 == 0 else (255, 255, 255, 70)
        d.line([(i * scale, 0), (i * scale, SIZE * scale)], fill=color, width=1)
        d.line([(0, i * scale), (SIZE * scale, i * scale)], fill=color, width=1)
    canvas.convert("RGB").save(out)


def font(size: int = 14):
    for path in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def silhouette_image(im: Image.Image) -> Image.Image:
    alpha = im.getchannel("A")
    sil = Image.new("RGBA", im.size, (0, 0, 0, 0))
    black = Image.new("RGBA", im.size, (0, 0, 0, 255))
    sil.paste(black, (0, 0), alpha)
    return sil


def review_sheet(im: Image.Image, out: Path, name: str, report: dict) -> None:
    """One image with all the checks: 8x mid/light/dark, GUI 16px, silhouette."""
    panel = 160
    pad = 8
    top = 40
    label_h = 18
    entries = [
        ("8x mid", im, BG_MID, "8x"),
        ("8x light", im, BG_LIGHT, "8x"),
        ("8x dark", im, BG_DARK, "8x"),
        ("GUI 16px", im, BG_MID, "gui"),
        ("silhouette", silhouette_image(im), BG_LIGHT, "8x"),
    ]
    width = pad + len(entries) * (panel + pad)
    height = top + label_h + panel + pad
    canvas = Image.new("RGBA", (width, height), (245, 245, 245, 255))
    d = ImageDraw.Draw(canvas)
    f_title = font(14)
    f_label = font(13)
    title = (f"{name} — {report['visible_pixels']} px, "
             f"{report['unique_visible_colors']} colors, bbox {report['bbox']}")
    d.text((pad, 6), title, font=f_title, fill=(20, 20, 20, 255))

    for i, (label, src, bg, mode) in enumerate(entries):
        x = pad + i * (panel + pad)
        d.text((x, top - 15), label, font=f_label, fill=(40, 40, 40, 255))
        p = Image.new("RGBA", (panel, panel), bg)
        if mode == "gui":
            scaled = src.resize((16, 16), Image.Resampling.BOX).resize(
                (panel, panel), Image.Resampling.NEAREST
            )
        else:
            scaled = src.resize((panel, panel), Image.Resampling.NEAREST)
        p.alpha_composite(scaled)
        canvas.alpha_composite(p, (x, top + label_h))
        d.rectangle(
            [x, top + label_h, x + panel - 1, top + label_h + panel - 1],
            outline=(180, 180, 180, 255),
        )

    canvas.convert("RGB").save(out)


def write_process_template(path: Path, spec: dict, report: dict) -> None:
    if path.exists():
        return
    text = f"""# {spec.get('name', 'untitled')} — process

## Design anchors
(fill in: axis, blade/head width, guard/socket span, grip length, pommel)

## Rounds
1. Silhouette:
2. Materials:

## Validation
- visible pixels: {report['visible_pixels']}
- visible colors: {report['unique_visible_colors']}
- bbox: {report['bbox']}
- errors: {report['errors']}
- warnings: {report['warnings']}

## Files
candidate.png, preview_8x.png, preview_8x_light.png, preview_8x_dark.png,
silhouette.png, validation.json, spec.json, process.md
"""
    path.write_text(text, encoding="utf-8")


def components(im: Image.Image) -> list[list[tuple[int, int]]]:
    alpha = [[im.getpixel((x, y))[3] > 0 for x in range(SIZE)] for y in range(SIZE)]
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for y in range(SIZE):
        for x in range(SIZE):
            if not alpha[y][x] or (x, y) in seen:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            comp = []
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < SIZE and 0 <= ny < SIZE and alpha[ny][nx] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            comps.append(comp)
    return comps


def validate(spec: dict, im: Image.Image, placeholder: set[tuple[int, int]]) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    px = im.load()
    pixels = [px[x, y] for y in range(SIZE) for x in range(SIZE)]
    visible = [(i % SIZE, i // SIZE) for i, p in enumerate(pixels) if p[3] > 0]
    partial = sum(1 for p in pixels if 0 < p[3] < 255)
    if partial:
        errors.append(f"{partial} pixels have partial alpha; use only 0 or 255")

    if not visible:
        errors.append("no visible pixels")
        bbox = None
    else:
        xs = [p[0] for p in visible]
        ys = [p[1] for p in visible]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
        if bbox[0] < 1 or bbox[1] < 1 or bbox[2] > SIZE - 2 or bbox[3] > SIZE - 2:
            errors.append(f"bbox {bbox} touches the 1px margin; keep coordinates in 1..{SIZE - 2}")

    bottom_right = [
        (x, y) for y in (SIZE - 2, SIZE - 1) for x in (SIZE - 2, SIZE - 1)
        if im.getpixel((x, y))[3] > 0
    ]
    if bottom_right:
        errors.append(f"bottom-right 2x2 must stay transparent; occupied: {bottom_right}")

    comps = components(im)
    if len(comps) > 1:
        sizes = sorted((len(c) for c in comps), reverse=True)
        errors.append(f"{len(comps)} disconnected components (sizes {sizes}); connect them into one object")

    colors = sorted({p for p in pixels if p[3] > 0})
    if len(colors) > 32:
        errors.append(f"{len(colors)} visible colors; keep the palette at 32 or fewer")
    elif len(colors) > 24:
        warnings.append(f"{len(colors)} visible colors; 9-15 is the usual target")

    if placeholder:
        warnings.append(f"{len(placeholder)} placeholder 'X' pixels remain; replace them before final delivery")

    if visible and len(visible) < 60:
        errors.append(f"only {len(visible)} visible pixels; too sparse to read as a 32x32 weapon")
    elif visible and len(visible) < 110:
        warnings.append(
            f"only {len(visible)} visible pixels; likely a 16x16 design scaled up; "
            "widen the blade/guard/grip before final delivery"
        )
    elif len(visible) > 550:
        warnings.append(f"{len(visible)} visible pixels; the board may be overcrowded")

    return {
        "ok": not errors,
        "name": spec.get("name", "untitled"),
        "size": [SIZE, SIZE],
        "bbox": bbox,
        "visible_pixels": len(visible),
        "opaque_pixels": sum(1 for p in pixels if p[3] == 255),
        "partial_alpha_pixels": partial,
        "unique_visible_colors": len(colors),
        "components": [len(c) for c in comps],
        "bottom_right_2x2_transparent": not bottom_right,
        "placeholder_pixels": len(placeholder),
        "errors": errors,
        "warnings": warnings,
    }


def load_template(name: str) -> dict:
    path = TEMPLATES / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"missing template {path}")
    template = json.loads(path.read_text(encoding="utf-8"))
    rows = template.get("rows")
    if not isinstance(rows, list) or len(rows) != SIZE or any(len(r) != SIZE for r in rows):
        raise SystemExit(f"template {path}: rows must be {SIZE} strings of {SIZE} characters")
    return template


def cmd_init(args: argparse.Namespace) -> int:
    out = Path(args.out)
    template = load_template(args.template) if args.template != "none" else None
    primary = args.primary or (template or {}).get("default_primary", "steel")
    grip = args.grip or (template or {}).get("default_grip", "wood")
    secondary = args.secondary or (template or {}).get("default_secondary")
    name = args.name
    if name == "untitled" and template:
        name = template.get("name", name)
    rows = template["rows"] if template else ["." * SIZE for _ in range(SIZE)]
    spec = {
        "name": name,
        "primary": primary,
        "secondary": secondary,
        "grip": grip,
        "template": args.template,
        "palette": theme_palette(primary, grip, secondary),
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({SIZE}x{SIZE}, primary={primary}, secondary={secondary}, "
          f"grip={grip}, template={args.template})")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    spec = load_spec(spec_path)
    im, placeholder = render_image(spec)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    preview_dir = Path(args.preview_dir) if args.preview_dir else out.parent
    preview_dir.mkdir(parents=True, exist_ok=True)

    report = validate(spec, im, placeholder)
    im.save(out, "PNG")

    if not args.fast:
        preview(im, preview_dir / "preview_8x.png", BG_MID)
        preview(im, preview_dir / "preview_8x_light.png", BG_LIGHT)
        preview(im, preview_dir / "preview_8x_dark.png", BG_DARK)
        silhouette(im, preview_dir / "silhouette.png")
    if args.grid:
        grid_preview(im, preview_dir / "grid_16x.png")

    review_sheet(im, preview_dir / "review.png", report["name"], report)
    if args.process_template:
        write_process_template(preview_dir / "process.md", spec, report)

    (preview_dir / "validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    status = "OK" if report["ok"] else "FAIL"
    print(f"{report['name']}: {status}  {report['visible_pixels']} px, "
          f"{report['unique_visible_colors']} colors, bbox {report['bbox']}")
    for error in report["errors"]:
        print("ERROR", error)
    for warning in report["warnings"]:
        print("WARN", warning)
    print(f"wrote {out}")
    print(f"wrote {preview_dir / 'review.png'}")
    if args.ascii:
        print("legend: D/S/B/L/H primary, G/g/y/Y gold, w/u/o/k grip, X placeholder, . transparent")
        for i, row in enumerate(spec["rows"]):
            print(f"{i:02d} {row}")
    return 0 if report["ok"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="create a blank or template 32x32 spec")
    p_init.add_argument("--out", required=True)
    p_init.add_argument("--name", default="untitled")
    p_init.add_argument("--primary", default=None, choices=PRIMARY_THEMES)
    p_init.add_argument("--secondary", default=None, choices=PRIMARY_THEMES)
    p_init.add_argument("--grip", default=None, choices=sorted(load_palette()))
    p_init.add_argument("--template", default="none", choices=["none"] + TEMPLATE_NAMES)
    p_init.set_defaults(func=cmd_init)

    p_render = sub.add_parser("render", help="render a spec and run validation")
    p_render.add_argument("--spec", required=True)
    p_render.add_argument("--out", required=True)
    p_render.add_argument("--preview-dir", default=None)
    p_render.add_argument("--fast", action="store_true",
                          help="only candidate.png, review.png and validation.json")
    p_render.add_argument("--ascii", action="store_true", help="print the 32-row map to stdout")
    p_render.add_argument("--process-template", action="store_true",
                          help="write process.md skeleton if it does not exist")
    p_render.add_argument("--grid", action="store_true", help="also write a 16x grid overlay")
    p_render.set_defaults(func=cmd_render)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
