"""Build 3D pixel-art item models for the eight 2D weapons of the weapon mod.

Every weapon gets:
  * a hand-painted 64x64 pixel atlas (64x512 + .mcmeta for animated blades)
  * a vanilla-legal item model with elements written directly into the JSON
    (no parent), all rotations in {-45, -22.5, 0, 22.5, 45}
  * a Blockbench viewport preview and a cleaned 1000x1000 PNG

Usage:
    python art/build_weapon_models.py --only iron_rapier --stage all
    python art/build_weapon_models.py --stage all
    python art/build_weapon_models.py --stage overview

Stages: atlas, model, preview, overview, all

Preview rendering needs Blockbench running with the MCP bridge on
http://127.0.0.1:3000/bb-mcp and the helper C:/Users/Administrator/AppData/
Local/Temp/bb_mcp.py.  Final model JSON and atlases are written directly from
the tables in this file; Blockbench is only used for the viewport previews.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
MODELS = ROOT / "src/main/resources/assets/weapon/models/item"
TEXTURES = ROOT / "src/main/resources/assets/weapon/textures/item"

sys.path.insert(0, r"C:/Users/Administrator/AppData/Local/Temp")
import bb_mcp  # noqa: E402

ALLOWED = (-45.0, -22.5, 0.0, 22.5, 45.0)
PXUV = 4.0  # 64 px atlas / 16 UV units


# --------------------------------------------------------------------------
# palette / atlas helpers
# --------------------------------------------------------------------------

def P(*rgb):
    return (rgb[0], rgb[1], rgb[2], 255)


class Atlas:
    """Tiny char-cell painter so every weapon palette stays explicit."""

    def __init__(self, palette, size=64):
        self.palette = palette
        self.im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def px(self, x, y, c):
        self.im.putpixel((int(x), int(y)), self.palette[c])

    def rect(self, x1, y1, x2, y2, c):
        self.d.rectangle([x1, y1, x2 - 1, y2 - 1], fill=self.palette[c])

    def vline(self, x, y1, y2, c):
        self.d.line([x, y1, x, y2 - 1], fill=self.palette[c])

    def hline(self, x1, x2, y, c):
        self.d.line([x1, y, x2 - 1, y], fill=self.palette[c])

    def border(self, x1, y1, x2, y2, c):
        self.rect(x1, y1, x2, y1 + 1, c)
        self.rect(x1, y2 - 1, x2, y2, c)
        self.rect(x1, y1, x1 + 1, y2, c)
        self.rect(x2 - 1, y1, x2, y2, c)

    def cols(self, x1, y1, x2, y2, chars, offset=0):
        """Vertical shade columns; chars is one colour per x."""
        for x in range(x1, x2):
            c = chars[(x - x1 + offset) % len(chars)]
            self.vline(x, y1, y2, c)

    def fleck(self, x1, y1, x2, y2, chars, period=29, salt=0):
        n = len(chars)
        for y in range(y1, y2):
            for x in range(x1, x2):
                h = (x * 7 + y * 13 + salt * 31) % period
                if h == 0:
                    self.px(x, y, chars[(x + y) % n])

    def frame_phase(self, phase):
        return None


def region_uv(reg, fx1=0.0, fy1=0.0, fx2=1.0, fy2=1.0,
              flipu=False, flipv=False):
    x1, y1, x2, y2 = reg
    X1 = x1 + fx1 * (x2 - x1)
    X2 = x1 + fx2 * (x2 - x1)
    Y1 = y1 + fy1 * (y2 - y1)
    Y2 = y1 + fy2 * (y2 - y1)
    if flipu:
        X1, X2 = X2, X1
    if flipv:
        Y1, Y2 = Y2, Y1
    return [round(X1 / PXUV, 4), round(Y1 / PXUV, 4),
            round(X2 / PXUV, 4), round(Y2 / PXUV, 4)]


def faces_all(uv):
    return {d: {"uv": list(uv), "texture": "#0"} for d in
            ("north", "south", "east", "west", "up", "down")}


def v_slice_faces(reg, side_reg, t0, t1, cap_reg=None, u0=0.0, u1=1.0):
    """Faces for a vertical box whose long axis is local +Y.

    The region is painted with the tip at the top (small v) and the guard at
    the bottom, matching Minecraft's face v direction (v=0 = top).
    """
    x1, y1, x2, y2 = reg
    ua = x1 + u0 * (x2 - x1)
    ub = x1 + u1 * (x2 - x1)
    va = y2 - t1 * (y2 - y1)
    vb = y2 - t0 * (y2 - y1)
    main = [round(ua / PXUV, 4), round(va / PXUV, 4),
            round(ub / PXUV, 4), round(vb / PXUV, 4)]
    sx1, sy1, sx2, sy2 = side_reg
    s_va = sy2 - t1 * (sy2 - sy1)
    s_vb = sy2 - t0 * (sy2 - sy1)
    side = [round(sx1 / PXUV, 4), round(s_va / PXUV, 4),
            round(sx2 / PXUV, 4), round(s_vb / PXUV, 4)]
    cap = region_uv(cap_reg) if cap_reg else main
    f = {
        "north": {"uv": list(main), "texture": "#0"},
        "south": {"uv": list(main), "texture": "#0"},
        "east": {"uv": list(side), "texture": "#0"},
        "west": {"uv": list(side), "texture": "#0"},
        "up": {"uv": list(cap), "texture": "#0"},
        "down": {"uv": list(cap), "texture": "#0"},
    }
    return f


def h_slice_faces(reg, side_reg, t0, t1, cap_reg=None, v0=0.0, v1=1.0,
                  flipu=False):
    """Faces for a horizontal box (long axis local X).

    Region is painted with the length along x and the width along y.
    """
    x1, y1, x2, y2 = reg
    ua = x1 + t0 * (x2 - x1)
    ub = x1 + t1 * (x2 - x1)
    va = y1 + v0 * (y2 - y1)
    vb = y1 + v1 * (y2 - y1)
    if flipu:
        ua, ub = ub, ua
    main = [round(ua / PXUV, 4), round(va / PXUV, 4),
            round(ub / PXUV, 4), round(vb / PXUV, 4)]
    sx1, sy1, sx2, sy2 = side_reg
    s_ua = sx1 + t0 * (sx2 - sx1)
    s_ub = sx1 + t1 * (sx2 - sx1)
    s_va = sy1 + v0 * (sy2 - sy1)
    s_vb = sy1 + v1 * (sy2 - sy1)
    if flipu:
        s_ua, s_ub = s_ub, s_ua
    side = [round(s_ua / PXUV, 4), round(s_va / PXUV, 4),
            round(s_ub / PXUV, 4), round(s_vb / PXUV, 4)]
    cap = region_uv(cap_reg) if cap_reg else main
    return {
        "north": {"uv": list(main), "texture": "#0"},
        "south": {"uv": list(main), "texture": "#0"},
        "east": {"uv": list(side), "texture": "#0"},
        "west": {"uv": list(side), "texture": "#0"},
        "up": {"uv": list(cap), "texture": "#0"},
        "down": {"uv": list(cap), "texture": "#0"},
    }


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def rotp(p, pivot, deg):
    a = math.radians(deg)
    dx, dy = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + dx * math.cos(a) - dy * math.sin(a),
            pivot[1] + dx * math.sin(a) + dy * math.cos(a))


def snap_angle(deg):
    """Nearest legal rotation and the box axis needed to express it."""
    n = round(deg / 22.5) * 22.5
    n = ((n + 180.0) % 360.0) - 180.0
    if n > 90.0:
        n -= 180.0
    if n < -90.0:
        n += 180.0
    return n


def seg_element(name, p0, p1, width, z0, z1, faces_fn, ext=0.0,
                force_h=False):
    """A closed box between two points, long axis p0->p1.

    `faces_fn(kind, len_rev)` receives kind 'h' (long axis is box X) or 'v'
    (long axis is box Y) and whether the box's canonical +axis points back
    toward p0.  Box orientation is chosen from the segment slope so blade UVs
    always run along the long axis.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    if ln < 1e-6:
        raise ValueError(name)
    ux, uy = dx / ln, dy / ln
    q0 = (p0[0] - ux * ext, p0[1] - uy * ext)
    q1 = (p1[0] + ux * ext, p1[1] + uy * ext)
    length = ln + ext * 2.0
    cx, cy = (q0[0] + q1[0]) * 0.5, (q0[1] + q1[1]) * 0.5
    phi = math.degrees(math.atan2(dy, dx))
    a = snap_angle(phi)
    if force_h:
        kind = "h"
        rot = a
        w, h = length, width
        len_rev = math.cos(math.radians(phi - rot)) < 0.0
    elif abs(a) > 45.0 + 1e-6:
        kind = "v"
        rot = a - 90.0 if a > 0 else a + 90.0
        w, h = width, length
        len_rev = math.cos(math.radians(phi - (rot + 90.0))) < 0.0
    elif abs(a) >= 45.0 - 1e-6 and abs(dy) + 1e-6 >= abs(dx):
        kind = "v"
        rot = -45.0 if a > 0 else 45.0
        w, h = width, length
        len_rev = math.cos(math.radians(phi - (rot + 90.0))) < 0.0
    else:
        kind = "h"
        rot = a
        w, h = length, width
        len_rev = math.cos(math.radians(phi - rot)) < 0.0
    if abs(rot) < 1e-6:
        rot = 0.0
    faces = faces_fn(kind, len_rev)
    item = {
        "name": name,
        "from": [round(cx - w / 2, 4), round(cy - h / 2, 4), round(z0, 4)],
        "to": [round(cx + w / 2, 4), round(cy + h / 2, 4), round(z1, 4)],
        "origin": [round(cx, 4), round(cy, 4), round((z0 + z1) / 2, 4)],
        "rot": rot,
        "faces": faces,
    }
    return item


def transformed_seg(name, pivot, p0, p1, width, z0, z1, faces_fn, ext=0.0):
    """Build in upright local space, then rotate the whole piece -45 deg."""
    return seg_element(name, rotp(p0, pivot, -45.0), rotp(p1, pivot, -45.0),
                       width, z0, z1, faces_fn, ext=ext)


def element_bbox(elements):
    xs, ys = [], []
    for e in elements:
        ang = math.radians(e["rot"])
        ox, oy = e["origin"][0], e["origin"][1]
        for qx, qy in ((e["from"][0], e["from"][1]),
                       (e["to"][0], e["from"][1]),
                       (e["to"][0], e["to"][1]),
                       (e["from"][0], e["to"][1])):
            lx, ly = qx - ox, qy - oy
            xs.append(ox + lx * math.cos(ang) - ly * math.sin(ang))
            ys.append(oy + lx * math.sin(ang) + ly * math.cos(ang))
    return min(xs), min(ys), max(xs), max(ys)


def center_elements(elements, target=(8.0, 8.0)):
    x0, y0, x1, y1 = element_bbox(elements)
    dx = target[0] - (x0 + x1) / 2.0
    dy = target[1] - (y0 + y1) / 2.0
    for e in elements:
        for k in ("from", "to", "origin"):
            e[k][0] = round(e[k][0] + dx, 4)
            e[k][1] = round(e[k][1] + dy, 4)
    return elements


DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, -90, 55],
                              "translation": [0, 4, 0.5],
                              "scale": [1.69, 1.69, 1.69]},
    "thirdperson_lefthand": {"rotation": [0, 90, -55],
                             "translation": [0, 4, 0.5],
                             "scale": [1.69, 1.69, 1.69]},
    "firstperson_righthand": {"rotation": [0, -90, 25],
                              "translation": [1.13, 3.2, 1.13],
                              "scale": [1.365, 1.365, 1.365]},
    "firstperson_lefthand": {"rotation": [0, 90, -25],
                             "translation": [1.13, 3.2, 1.13],
                             "scale": [1.365, 1.365, 1.365]},
    "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0],
            "scale": [1.56, 1.56, 1.56]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 4, 0],
               "scale": [0.78, 0.78, 0.78]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0],
              "scale": [1.04, 1.04, 1.04]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7],
             "scale": [1.3, 1.3, 1.3]},
}


def make_model(elements, tex_id, display=None):
    center_elements(elements)
    out = {
        "textures": {"0": f"weapon:item/{tex_id}",
                     "particle": f"weapon:item/{tex_id}"},
        "elements": [{"from": e["from"], "to": e["to"],
                      "faces": e["faces"],
                      **({"rotation": {"origin": e["origin"], "axis": "z",
                                       "angle": e["rot"]}}
                         if abs(e["rot"]) > 1e-9 else {})}
                     for e in elements],
        "display": display or DISPLAY,
    }
    return out


def validate(model, label):
    problems = []
    for i, e in enumerate(model["elements"]):
        if len(e["faces"]) != 6:
            problems.append(f"el{i}: {len(e['faces'])} faces")
        for d, f in e["faces"].items():
            uv = f["uv"]
            if len(uv) != 4 or any(v < -1e-4 or v > 16.0001 for v in uv):
                problems.append(f"el{i} {d} uv {uv}")
            if f.get("texture") != "#0":
                problems.append(f"el{i} {d} texture {f.get('texture')}")
        if any(e["from"][k] > e["to"][k] for k in range(3)):
            problems.append(f"el{i} from>to")
        if "rotation" in e:
            r = e["rotation"]
            if r["axis"] != "z" or r["angle"] not in ALLOWED:
                problems.append(f"el{i} rotation {r}")
    if "parent" in model:
        problems.append("model has parent")
    for key in ("thirdperson_righthand", "thirdperson_lefthand",
                "firstperson_righthand", "firstperson_lefthand",
                "gui", "ground", "fixed", "head"):
        if key not in model.get("display", {}):
            problems.append(f"missing display {key}")
    x0, y0, x1, y1 = element_bbox([
        {"from": e["from"], "to": e["to"],
         "origin": e.get("rotation", {}).get("origin",
                                             [0, 0, 0]),
         "rot": e.get("rotation", {}).get("angle", 0.0)}
        for e in model["elements"]])
    angles = sorted({e.get("rotation", {}).get("angle", 0.0)
                     for e in model["elements"]})
    print(f"  {label}: {len(model['elements'])} elements | "
          f"angles {angles} | bbox x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f} | "
          f"problems {len(problems)}")
    for p in problems[:10]:
        print("   !!", p)
    return problems


# --------------------------------------------------------------------------
# Blockbench preview
# --------------------------------------------------------------------------

def init_mcp():
    bb_mcp.SID = None
    bb_mcp.rpc("initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "zcode", "version": "1.0"},
    })
    bb_mcp.rpc("notifications/initialized", notify=True)


def js(code, timeout=120):
    r = bb_mcp.call_tool("risky_eval", {"code": code}, timeout=timeout)
    text = r["result"]["content"][0]["text"]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def bb_start(name, atlas_path):
    init_mcp()
    bb_mcp.call_tool("create_project", {"name": name, "format": "java_block"})
    time.sleep(3.0)
    print("  project:", js("try{JSON.stringify({p:Project.name,f:Format.id})}"
                           "catch(e){JSON.stringify({err:String(e)})}"))
    atlas_path = Path(atlas_path)
    meta = Path(str(atlas_path) + ".mcmeta")
    if not meta.exists():
        meta.write_text("{}", encoding="utf-8")
    p = str(atlas_path).replace("\\", "/")
    code = ("try{const t=new Texture({name:'atlas'});t.add(false);"
            f"t.fromPath('{p}', q=>require('fs').readFileSync(q));'ok'"
            "}catch(e){JSON.stringify({err:String(e)})}")
    print("  texture load:", js(code, timeout=180))
    time.sleep(1.5)
    info = js("try{JSON.stringify(Texture.all.map(t=>({n:t.name,w:t.width,h:t.height})))"
              "}catch(e){JSON.stringify({err:String(e)})}")
    print("  preview texture:", info)


def bb_cubes(elements):
    for i in range(0, len(elements), 12):
        batch = elements[i:i + 12]
        payload = json.dumps([{k: e[k] for k in
                               ("name", "from", "to", "origin", "rot", "faces")}
                              for e in batch], separators=(",", ":"))
        code = f"""
try {{
 const defs = {payload};
 const tex = Texture.all[0];
 for (const def of defs) {{
  const c = new Cube({{name: def.name, from: def.from, to: def.to,
    origin: def.origin, rotation: [0, 0, def.rot], box_uv: false,
    autouv: 0}}).init();
  c.rotation = [0, 0, def.rot];
  c.origin = def.origin;
  for (const dir of ['north','south','east','west','up','down']) {{
   c.faces[dir].uv = def.faces[dir].uv;
   c.faces[dir].texture = tex;
  }}
 }}
 Canvas.updateAllFaces(); Canvas.updateAll();
 JSON.stringify({{cubes: Cube.all.length}})
}} catch(e) {{ JSON.stringify({{err:String(e), stack:String(e.stack).slice(0,300)}}) }}
"""
        print("  cubes", js(code, timeout=180))


def bb_render(path, cam, target=(8.0, 8.0, 8.0), fov=30, w=1200, h=1200):
    code = f"""
try {{
 const p = Preview.selected; const c = p.camera;
 p.renderer.setPixelRatio(1); p.renderer.setSize({w}, {h}, false);
 p.renderer.setViewport(0, 0, {w}, {h});
 c.position.set({cam[0]}, {cam[1]}, {cam[2]});
 p.controls.target.set({target[0]}, {target[1]}, {target[2]});
 c.lookAt({target[0]}, {target[1]}, {target[2]});
 p.controls.update(); c.fov = {fov}; c.aspect = {w}/{h};
 c.updateProjectionMatrix(); p.render();
 const d = p.canvas.toDataURL('image/png');
 require('fs').writeFileSync({json.dumps(str(path).replace(chr(92), '/'))},
   Buffer.from(d.split(',')[1], 'base64'));
 JSON.stringify({{ok:1, pos:c.position.toArray()}})
}} catch(e) {{ JSON.stringify({{err:String(e)}}) }}
"""
    return js(code, timeout=180)


def alpha_bbox(path):
    im = Image.open(path).convert("RGBA")
    bb = im.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
    if not bb:
        raise RuntimeError(f"empty render: {path}")
    return bb, im.size


def big_shot(path, direction, dist, target=(8.0, 8.0, 8.0), fov=30,
             canvas=(1600, 1200)):
    n = math.sqrt(sum(v * v for v in direction)) or 1.0
    d = tuple(v / n for v in direction)
    cam = tuple(target[i] + d[i] * dist for i in range(3))
    for attempt in range(3):
        bb_render(path, cam, target=target, fov=fov,
                  w=canvas[0], h=canvas[1])
        bb, size = alpha_bbox(path)
        print(f"  raw {path.name} bbox={bb} dist={dist:.1f}")
        if bb[0] > 12 and bb[1] > 12 and bb[2] < size[0] - 12 and bb[3] < size[1] - 12:
            return cam
        cam = tuple(target[i] + d[i] * dist * 1.22 for i in range(3))
        dist *= 1.22
    return cam


def clean_framing(src, dst, size=1000, fill=0.72, bg=(244, 245, 249)):
    rgba = Image.open(src).convert("RGBA")
    alpha = rgba.getchannel("A")
    bb = alpha.point(lambda a: 255 if a > 10 else 0).getbbox()
    if not bb:
        raise RuntimeError("empty render")
    x0, y0, x1, y1 = bb
    im = Image.new("RGB", rgba.size, bg)
    im.paste(rgba, mask=alpha)
    box = im.crop((x0, y0, x1, y1))
    sc = (size * fill) / max(box.size)
    bw, bh = int(box.size[0] * sc), int(box.size[1] * sc)
    box = box.resize((bw, bh), Image.LANCZOS)
    out = Image.new("RGB", (size, size), bg)
    out.paste(box, ((size - bw) // 2, (size - bh) // 2))
    out.save(dst)
    return (x0, y0, x1, y1), (bw, bh)


def preview_weapon(wid, atlas_path, elements, shots=None):
    bb_start(f"wf_{wid}", atlas_path)
    bb_cubes(elements)
    shots = shots or [("front", (0.0, 0.10, 1.0), 46.0),
                      ("threequarter", (0.38, 0.22, 1.0), 46.0)]
    raws = []
    for tag, direction, dist in shots:
        raw = ART / f"_raw_{wid}_{tag}.png"
        big_shot(raw, direction, dist)
        raws.append(raw)
    clean_framing(raws[0], ART / f"weapon_preview_{wid}.png", size=1000,
                  fill=0.74)
    clean_framing(raws[1], ART / f"weapon_preview_{wid}_3q.png", size=1000,
                  fill=0.74)
    print("  preview ->", ART / f"weapon_preview_{wid}.png")


# --------------------------------------------------------------------------
# texture writing
# --------------------------------------------------------------------------

def save_texture(wid, frames, animated):
    if animated:
        strip = Image.new("RGBA", (64, 64 * len(frames)), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            strip.paste(f, (0, i * 64))
        strip.save(TEXTURES / f"{wid}_3d.png")
        (TEXTURES / f"{wid}_3d.png.mcmeta").write_text(
            json.dumps({"animation": {"frametime": 2}}, indent=2),
            encoding="utf-8")
    else:
        frames[0].save(TEXTURES / f"{wid}_3d.png")
    return frames[0]


def write_model(wid, elements, model_id=None):
    model_id = model_id or wid
    model = make_model(elements, f"{wid}_3d")
    path = MODELS / f"{model_id}.json"
    path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    validate(model, model_id)
    return model


def backup_2d(wid):
    path = MODELS / f"{wid}.json"
    bak = MODELS / f"{wid}_2d.json"
    if path.exists() and not bak.exists():
        shutil.copyfile(path, bak)
        print("  backed up 2D ->", bak.name)


# --------------------------------------------------------------------------
# 1. iron_rapier
# --------------------------------------------------------------------------

IRON_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(20, 23, 32), "K": P(40, 45, 58), "i": P(68, 76, 92),
    "I": P(104, 114, 132), "S": P(146, 158, 178), "W": P(196, 208, 224),
    "w": P(236, 244, 252),
    "g": P(98, 70, 24), "G": P(156, 116, 42), "Y": P(214, 174, 84),
    "y": P(250, 228, 154),
    "l": P(46, 32, 24), "L": P(76, 52, 36), "h": P(26, 18, 14),
    "b": P(30, 72, 142), "B": P(72, 132, 216), "C": P(150, 204, 255),
    "c": P(210, 240, 255),
}
IRON_REG = {
    "blade": (0, 0, 16, 44),
    "edge": (16, 0, 22, 44),
    "side": (22, 0, 28, 44),
    "guard": (28, 0, 44, 18),
    "grip": (28, 18, 44, 42),
    "pommel": (28, 42, 44, 56),
    "ring": (44, 16, 64, 36),
    "gem": (44, 36, 52, 44),
    "glow": (44, 0, 60, 16),
    "tipcap": (52, 36, 60, 44),
    "dark": (60, 36, 64, 44),
}


def paint_iron_rapier(phase=0):
    a = Atlas(IRON_PAL)
    bx1, by1, bx2, by2 = IRON_REG["blade"]
    # slim double-edged rapier: symmetric polished steel with a centre ridge
    cols = ["k", "I", "S", "W", "w", "w", "W", "S",
            "S", "W", "w", "w", "W", "S", "I", "k"]
    a.cols(bx1, by1, bx2, by2, cols)
    for y in range(by1, by2):
        for x in range(bx1, bx2):
            h = (x * 5 + y * 11) % 37
            if h == 0:
                a.px(x, y, "w")
            elif h == 3 and x in (2, 13):
                a.px(x, y, "I")
        # subtle fuller grooves just inside the edges
        if y > 6:
            a.px(bx1 + 2, y, "S")
            a.px(bx2 - 3, y, "S")
    # bright converging point at the top (tip)
    for y in range(by1, by1 + 7):
        t = y - by1
        for x in range(bx1 + 3 + t // 2, bx2 - 3 - t // 2):
            a.px(x, y, "w" if x in (7, 8) else "W")
    # edge strip: near-white cutting steel
    ex1, ey1, ex2, ey2 = IRON_REG["edge"]
    a.cols(ex1, ey1, ex2, ey2, ["S", "W", "w", "w", "W", "S"])
    for y in range(ey1, ey2, 6):
        a.px(ex1 + 2, y, "S")
        a.px(ex1 + 3, y + 1, "S")
    # side / thickness
    sx1, sy1, sx2, sy2 = IRON_REG["side"]
    a.cols(sx1, sy1, sx2, sy2, ["K", "i", "I", "I", "i", "K"])
    # gold guard plate with bevel and rivets
    gx1, gy1, gx2, gy2 = IRON_REG["guard"]
    a.rect(gx1, gy1, gx2, gy2, "g")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "G")
    a.rect(gx1 + 2, gy1 + 2, gx2 - 2, gy2 - 5, "Y")
    a.hline(gx1 + 2, gx2 - 2, gy1 + 2, "y")
    a.vline(gx1 + 2, gy1 + 2, gy2 - 3, "y")
    for rx in (gx1 + 4, gx2 - 5):
        for ry in (gy1 + 8, gy1 + 12):
            a.px(rx, ry, "g")
            a.px(rx + 1, ry, "Y")
    a.hline(gx1 + 3, gx2 - 3, gy2 - 3, "g")
    # wrapped leather grip with silver wire
    rx1, ry1, rx2, ry2 = IRON_REG["grip"]
    a.rect(rx1, ry1, rx2, ry2, "l")
    a.rect(rx1, ry1, rx2, ry1 + 2, "h")
    a.rect(rx1, ry2 - 2, rx2, ry2, "h")
    for y in range(ry1 + 3, ry2 - 3):
        x = rx1 + 1 + ((y - ry1) * 2) % (rx2 - rx1 - 2)
        a.px(x, y, "W")
        a.px(x + 1, y, "S")
        x2 = rx1 + 1 + ((y - ry1) * 2 + 7) % (rx2 - rx1 - 2)
        a.px(x2, y, "i")
        a.px(x2 + 1, y, "I")
    a.hline(rx1, rx2, ry1 + 3, "g")
    a.hline(rx1, rx2, ry2 - 4, "g")
    # pommel: faceted gold with dark grooves
    px1, py1, px2, py2 = IRON_REG["pommel"]
    a.rect(px1, py1, px2, py2, "g")
    a.rect(px1 + 1, py1 + 1, px2 - 1, py2 - 1, "G")
    a.rect(px1 + 3, py1 + 2, px2 - 3, py2 - 3, "Y")
    for k in range(4):
        a.hline(px1 + 3 + k, px2 - 4 - k, py1 + 3 + k, "y")
    a.hline(px1 + 1, px2 - 1, py2 - 2, "g")
    # ring guard plate: transparent middle, gold oval, four sapphires
    ox1, oy1, ox2, oy2 = IRON_REG["ring"]
    a.rect(ox1, oy1, ox2, oy2, ".")
    cx, cy = (ox1 + ox2) / 2.0, (oy1 + oy2) / 2.0
    for y in range(oy1, oy2):
        for x in range(ox1, ox2):
            dx, dy = (x - cx) / 8.5, (y - cy) / 8.5
            d = math.sqrt(dx * dx + dy * dy)
            if 0.74 <= d <= 1.0:
                a.px(x, y, "g" if d < 0.8 else "G")
            elif 0.80 <= d < 0.86 and (x + y) % 2 == 0:
                a.px(x, y, "Y")
    for gx, gy in ((cx, oy1 + 1), (cx, oy2 - 2), (ox1 + 1, cy), (ox2 - 2, cy)):
        a.px(gx - 1, gy, "B")
        a.px(gx, gy, "C")
        a.px(gx + 1, gy, "b")
        a.px(gx, gy - 1 if gy > cy else gy + 1, "C")
    # sapphire: diamond-cut gem with transparent corners
    gx1, gy1, gx2, gy2 = IRON_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            dx = abs(x - (gx1 + gx2 - 1) / 2.0)
            dy = abs(y - (gy1 + gy2 - 1) / 2.0)
            if dx + dy <= 4.0:
                if dx + dy <= 1.0:
                    a.px(x, y, "c")
                elif dx + dy <= 2.6:
                    a.px(x, y, "C")
                elif x < (gx1 + gx2) / 2 and y < (gy1 + gy2) / 2:
                    a.px(x, y, "B")
                else:
                    a.px(x, y, "b")
    # tip cap
    tx1, ty1, tx2, ty2 = IRON_REG["tipcap"]
    a.rect(tx1, ty1, tx2, ty2, "W")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "w")
    return a.im


def build_iron_rapier():
    pal, reg = IRON_PAL, IRON_REG
    G = 5.6
    pivot = (8.0, G, 8.0)
    els = []
    zc = 8.0
    blade_y0, blade_y1 = 6.15, 17.55
    bounds = [0.0, 0.15, 0.30, 0.45, 0.60, 0.74, 0.86, 0.94, 1.0]

    def width_at(t):
        return 0.62 - 0.20 * t - 0.12 * t ** 3

    def thick_at(t):
        return 0.26 - 0.08 * t

    n = len(bounds) - 1
    for i in range(n):
        t0, t1 = bounds[i], bounds[i + 1]
        y0 = blade_y0 + (blade_y1 - blade_y0) * t0
        y1 = blade_y0 + (blade_y1 - blade_y0) * t1
        tm = (t0 + t1) / 2
        w = (width_at(t0) + width_at(t1)) / 2.0
        th = (thick_at(t0) + thick_at(t1)) / 2.0
        faces = lambda kind, rev, t0=t0, t1=t1: v_slice_faces(
            reg["blade"], reg["side"], t0, t1, reg["tipcap"])
        els.append(transformed_seg(f"blade_{i:02d}", pivot,
                                   (8.0, y0), (8.0, y1), w,
                                   zc - th / 2, zc + th / 2, faces,
                                   ext=0.05))
    # two cutting edges, split into three tapered sections per side
    for side, sign in (("l", -1), ("r", 1)):
        for j, (t0, t1) in enumerate(((0.0, 0.45), (0.45, 0.80), (0.80, 1.0))):
            y0 = blade_y0 + (blade_y1 - blade_y0) * t0
            y1 = blade_y0 + (blade_y1 - blade_y0) * t1
            xoff = sign * (width_at((t0 + t1) / 2) / 2.0 - 0.01)
            th = thick_at((t0 + t1) / 2) + 0.035
            faces = lambda kind, rev: faces_all(region_uv(reg["edge"]))
            els.append(transformed_seg(f"edge_{side}{j}", pivot,
                                       (8.0 + xoff, y0), (8.0 + xoff, y1),
                                       0.11, zc - th / 2, zc + th / 2,
                                       faces, ext=0.04))
    # raised centre ridge on both faces (bright steel, not a dark spine)
    for side, zz in (("f", zc + 0.145), ("b", zc - 0.17)):
        faces = lambda kind, rev: faces_all(region_uv(reg["edge"], 0, 0.1, 1, 0.9))
        els.append(transformed_seg(f"ridge_{side}", pivot,
                                   (8.0, blade_y0 + 0.1),
                                   (8.0, blade_y1 - 0.55), 0.11,
                                   zz, zz + 0.025, faces, ext=0.0))
    # needle point: three shrink steps + a tiny cap
    tip_specs = ((blade_y1, 17.86, 0.255, 0.20),
                 (17.86, 18.04, 0.145, 0.14),
                 (18.04, 18.16, 0.075, 0.075))
    for k, (ya, yb, tw, td) in enumerate(tip_specs):
        tf = lambda kind, rev: faces_all(region_uv(reg["tipcap"]))
        els.append(transformed_seg(f"tip_{k}", pivot, (8.0, ya), (8.0, yb),
                                   tw, zc - td / 2, zc + td / 2, tf, ext=0.01))
    # gold ricasso collar
    faces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.2, 0.55, 0.8, 0.95))
    els.append(transformed_seg("ricasso", pivot, (8.0, 5.93), (8.0, 6.28),
                               0.80, zc - 0.36, zc + 0.36, faces, ext=0.0))
    # guard block + ring plate
    faces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.1, 0.1, 0.9, 0.9))
    els.append(transformed_seg("guard_core", pivot, (8.0, G - 0.24),
                               (8.0, G + 0.28), 0.84,
                               zc - 0.38, zc + 0.38, faces, ext=0.0))
    ring_faces = lambda kind, rev: faces_all(region_uv(reg["ring"]))
    # cup guard: a thin octagonal ring plate around the hand
    els.append(transformed_seg("guard_ring", pivot, (8.0, 4.66),
                               (8.0, 6.50), 2.02,
                               zc - 0.07, zc + 0.07, ring_faces, ext=0.0))
    # straight quillons with gold ball tips
    qfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.05, 0.4, 0.95, 0.8))
    for side, sign in (("l", -1), ("r", 1)):
        tip = (8.0 + sign * 1.24, 5.62)
        els.append(transformed_seg(f"quillon_{side}", pivot, (8.0, 5.62),
                                   tip, 0.17,
                                   zc - 0.12, zc + 0.12, qfaces, ext=0.0))
        els.append(transformed_seg(f"quillon_ball_{side}", pivot,
                                   (tip[0], tip[1] - 0.11),
                                   (tip[0], tip[1] + 0.11), 0.24,
                                   zc - 0.14, zc + 0.14, qfaces, ext=0.02))
    # guard sapphire (front and back plates)
    gem_faces = lambda kind, rev: faces_all(region_uv(reg["gem"]))
    for side, zz in (("f", zc + 0.39), ("b", zc - 0.42)):
        els.append(transformed_seg(f"guard_gem_{side}", pivot,
                                   (7.82, 5.36), (8.18, 5.72), 0.36,
                                   zz, zz + 0.03, gem_faces))
    # grip core and wire bands
    gfaces = lambda kind, rev: faces_all(region_uv(reg["grip"]))
    els.append(transformed_seg("grip", pivot, (8.0, 2.18), (8.0, 5.38),
                               0.60, zc - 0.30, zc + 0.30, gfaces, ext=0.0))
    bfaces = lambda kind, rev: faces_all(region_uv(reg["edge"], 0, 0, 1, 0.18))
    for k in range(8):
        y = 2.38 + k * 0.36
        els.append(transformed_seg(f"wrap_{k}", pivot, (7.68, y), (8.32, y),
                                   0.075, zc - 0.32, zc + 0.32, bfaces,
                                   ext=0.0))
    # pommel and sapphire
    pfaces = lambda kind, rev: faces_all(region_uv(reg["pommel"]))
    els.append(transformed_seg("pommel", pivot, (8.0, 1.36), (8.0, 1.94),
                               0.84, zc - 0.42, zc + 0.42, pfaces, ext=0.0))
    capf = lambda kind, rev: faces_all(region_uv(reg["tipcap"]))
    els.append(transformed_seg("pommel_cap", pivot, (8.0, 1.14), (8.0, 1.38),
                               0.52, zc - 0.26, zc + 0.26, capf, ext=0.0))
    for side, zz in (("f", zc + 0.43), ("b", zc - 0.46)):
        els.append(transformed_seg(f"pommel_gem_{side}", pivot,
                                   (7.81, 1.48), (8.19, 1.84), 0.38,
                                   zz, zz + 0.025, gem_faces))
    return els


# --------------------------------------------------------------------------
# generic straight-sword pieces
# --------------------------------------------------------------------------

def blade_stack(els, pivot, zc, y0, y1, bounds, width_fn, thick_fn, reg,
                edge_w=0.10, edges=("l", "r"), edge_sections=3,
                spine_side=None, spine_w=0.12, ridge=False,
                tip_len=0.42, tip_steps=3, prefix="blade",
                edge_uv=None, spine_uv=None, skip_edges=()):
    def blade_faces(t0, t1):
        return v_slice_faces(reg["blade"], reg["side"], t0, t1, reg["tip"])

    for i in range(len(bounds) - 1):
        t0, t1 = bounds[i], bounds[i + 1]
        ya = y0 + (y1 - y0) * t0
        yb = y0 + (y1 - y0) * t1
        w = (width_fn(t0) + width_fn(t1)) / 2.0
        th = (thick_fn(t0) + thick_fn(t1)) / 2.0
        els.append(transformed_seg(f"{prefix}_{i:02d}", pivot, (8.0, ya),
                                   (8.0, yb), w, zc - th / 2, zc + th / 2,
                                   lambda kind, rev, a=t0, b=t1:
                                   blade_faces(a, b), ext=0.05))
    efaces = (lambda kind, rev: faces_all(edge_uv)) if edge_uv else \
        (lambda kind, rev: faces_all(region_uv(reg["edge"])))
    for side, sign in (("l", -1), ("r", 1)):
        if side not in edges:
            continue
        for j in range(edge_sections):
            if (side, j) in skip_edges:
                continue
            t0 = j / edge_sections
            t1 = (j + 1) / edge_sections
            ya = y0 + (y1 - y0) * t0
            yb = y0 + (y1 - y0) * t1
            xoff = sign * (width_fn((t0 + t1) / 2) / 2.0 - 0.012)
            th = thick_fn((t0 + t1) / 2) + 0.035
            els.append(transformed_seg(f"edge_{side}{j}", pivot,
                                       (8.0 + xoff, ya), (8.0 + xoff, yb),
                                       edge_w, zc - th / 2, zc + th / 2,
                                       efaces, ext=0.04))
    if spine_side:
        sfaces = (lambda kind, rev: faces_all(spine_uv)) if spine_uv else \
            (lambda kind, rev: faces_all(region_uv(reg["spine"])))
        sign = -1 if spine_side == "l" else 1
        for j in range(2):
            t0, t1 = j * 0.5, (j + 1) * 0.5
            ya = y0 + (y1 - y0) * t0
            yb = y0 + (y1 - y0) * t1
            xoff = sign * (width_fn((t0 + t1) / 2) / 2.0 - 0.01)
            th = thick_fn((t0 + t1) / 2) + 0.02
            els.append(transformed_seg(f"spine_{j}", pivot,
                                       (8.0 + xoff, ya), (8.0 + xoff, yb),
                                       spine_w, zc - th / 2, zc + th / 2,
                                       sfaces, ext=0.05))
    if ridge:
        rfaces = lambda kind, rev: faces_all(region_uv(reg["edge"], 0, 0, 1, 0.22))
        for side, zz in (("f", zc + 0.145), ("b", zc - 0.17)):
            els.append(transformed_seg(f"ridge_{side}", pivot,
                                       (8.0, y0 + 0.1), (8.0, y1 - 0.5),
                                       0.13, zz, zz + 0.025, rfaces))
    # taper the final point with three shrinking steps
    w_end = width_fn(1.0)
    th_end = thick_fn(1.0)
    for k in range(tip_steps):
        fa = k / tip_steps
        fb = (k + 1) / tip_steps
        ya = y1 + tip_len * fa
        yb = y1 + tip_len * fb
        tw = w_end * (1.0 - 0.94 * (k + 1) / tip_steps)
        td = max(0.06, th_end * (1.0 - 0.55 * (k + 1) / tip_steps))
        tfaces = lambda kind, rev: faces_all(region_uv(reg["tip"]))
        els.append(transformed_seg(f"tip_{k}", pivot, (8.0, ya), (8.0, yb),
                                   max(0.07, tw), zc - td / 2, zc + td / 2,
                                   tfaces, ext=0.01))
    return y1 + tip_len


def grip_stack(els, pivot, zc, y_bottom, y_top, w, depth, reg,
               bands=6, band_region="edge", band_w=0.08,
               pommel=True, gem=True, gem_size=0.36, pommel_w=0.42,
               prefix="grip"):
    gfaces = lambda kind, rev: faces_all(region_uv(reg["grip"]))
    els.append(transformed_seg(prefix, pivot, (8.0, y_bottom),
                               (8.0, y_top), w, zc - depth / 2,
                               zc + depth / 2, gfaces, ext=0.0))
    bfaces = lambda kind, rev: faces_all(region_uv(reg[band_region], 0, 0, 1, 0.2))
    for k in range(bands):
        y = y_bottom + 0.22 + (y_top - y_bottom - 0.44) * (k / max(1, bands - 1))
        els.append(transformed_seg(f"{prefix}_band_{k}", pivot,
                                   (8.0 - w / 2.0 - 0.03, y),
                                   (8.0 + w / 2.0 + 0.03, y), band_w,
                                   zc - depth / 2 - 0.02, zc + depth / 2 + 0.02,
                                   bfaces, ext=0.0))
    if pommel:
        pfaces = lambda kind, rev: faces_all(region_uv(reg["pommel"]))
        els.append(transformed_seg("pommel", pivot,
                                   (8.0, y_bottom - 0.62),
                                   (8.0, y_bottom), w + pommel_w * 0.2,
                                   zc - depth / 2 - 0.10,
                                   zc + depth / 2 + 0.10, pfaces, ext=0.0))
        capf = lambda kind, rev: faces_all(region_uv(reg["edge"], 0, 0, 1, 0.25))
        els.append(transformed_seg("pommel_cap", pivot,
                                   (8.0, y_bottom - 0.82),
                                   (8.0, y_bottom - 0.60), w * 0.66,
                                   zc - depth / 3, zc + depth / 3, capf,
                                   ext=0.0))
        if gem:
            gfaces2 = lambda kind, rev: faces_all(region_uv(reg["gem"]))
            gy = y_bottom - 0.45
            for side, zz in (("f", zc + depth / 2 + 0.11),
                             ("b", zc - depth / 2 - 0.14)):
                els.append(transformed_seg(f"pommel_gem_{side}", pivot,
                                           (8.0 - gem_size / 2, gy - gem_size / 2),
                                           (8.0 + gem_size / 2, gy + gem_size / 2),
                                           gem_size, zz, zz + 0.025, gfaces2,
                                           ext=0.0))


def _chain(els, pivot, start, deltas, width, depth, zc, faces, prefix):
    p = start
    for k, (dx, dy) in enumerate(deltas):
        q = (p[0] + dx, p[1] + dy)
        els.append(transformed_seg(f"{prefix}_{k}", pivot, p, q, width,
                                   zc - depth / 2, zc + depth / 2, faces,
                                   ext=0.02))
        p = q
    return p


# --------------------------------------------------------------------------
# 2. venom_rapier
# --------------------------------------------------------------------------

VENOM_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(8, 28, 18), "e": P(18, 54, 32), "E": P(36, 92, 52),
    "g": P(64, 142, 72), "G": P(112, 202, 104), "v": P(170, 242, 142),
    "V": P(220, 255, 196),
    "K": P(26, 38, 32), "I": P(54, 74, 60), "S": P(96, 120, 98),
    "o": P(96, 70, 24), "O": P(156, 118, 44), "Y": P(214, 176, 88),
    "y": P(248, 228, 148),
    "m": P(8, 88, 58), "M": P(26, 158, 96), "N": P(80, 226, 152),
    "n": P(184, 255, 218),
    "r": P(190, 34, 44), "w": P(238, 248, 230),
}
VENOM_REG = {
    "blade": (0, 0, 16, 44), "edge": (16, 0, 22, 44),
    "side": (22, 0, 28, 44), "spine": (22, 0, 28, 44),
    "guard": (28, 0, 44, 18),
    "grip": (28, 18, 44, 42), "pommel": (28, 42, 44, 56),
    "gem": (44, 16, 52, 24), "snake": (44, 24, 60, 40),
    "glow": (44, 0, 60, 16), "tip": (52, 40, 60, 48),
    "drop": (56, 40, 60, 44),
}


def paint_venom_rapier(phase=0):
    a = Atlas(VENOM_PAL)
    bx1, by1, bx2, by2 = VENOM_REG["blade"]
    a.cols(bx1, by1, bx2, by2,
           ["k", "e", "E", "g", "G", "G", "g", "E",
            "E", "g", "G", "G", "g", "E", "e", "k"])
    # serpentine vein down the middle and poison flecks
    for y in range(by1, by2):
        x = 8 + int(1.6 * math.sin(y / 4.2))
        a.px(x, y, "k")
        a.px(x + 1, y, "e")
        a.px(x - 1, y, "G")
        h = (y * 13) % 29
        if h == 0:
            a.px(4 + (y * 7) % 8, y, "v")
        if h == 6:
            a.px(3 + (y * 5) % 10, y, "m")
        if y > 6:
            a.px(bx1 + 1, y, "e")
            a.px(bx2 - 2, y, "e")
    for y in range(by1, by1 + 6):
        t = y - by1
        for x in range(bx1 + 4 + t // 2, bx2 - 4 - t // 2):
            a.px(x, y, "v" if x in (7, 8) else "G")
    # acid edge
    ex1, ey1, ex2, ey2 = VENOM_REG["edge"]
    a.cols(ex1, ey1, ex2, ey2, ["E", "g", "G", "v", "G", "g"])
    for y in range(ey1, ey2, 7):
        a.px(ex1 + 2, y, "V")
        a.px(ex1 + 3, y + 1, "V")
    # dark green metal sides
    sx1, sy1, sx2, sy2 = VENOM_REG["side"]
    a.cols(sx1, sy1, sx2, sy2, ["k", "K", "I", "I", "K", "k"])
    # guard: dark bronze-green with gold filigree
    gx1, gy1, gx2, gy2 = VENOM_REG["guard"]
    a.rect(gx1, gy1, gx2, gy2, "K")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "I")
    a.hline(gx1 + 2, gx2 - 2, gy1 + 2, "S")
    a.hline(gx1 + 2, gx2 - 2, gy2 - 3, "k")
    for k in range(0, 12, 4):
        a.vline(gx1 + 3 + k, gy1 + 5, gy2 - 5, "O")
        a.px(gx1 + 4 + k, gy1 + 7, "Y")
    for rx in (gx1 + 3, gx2 - 4):
        a.px(rx, gy1 + 9, "Y")
        a.px(rx, gy1 + 12, "O")
    # snake scales for the guard arms
    sx1, sy1, sx2, sy2 = VENOM_REG["snake"]
    for y in range(sy1, sy2):
        for x in range(sx1, sx2):
            c = "k" if (x + y) % 4 == 0 else "e"
            if (x * 3 + y * 5) % 17 == 0:
                c = "G"
            if (x + y) % 7 == 0:
                c = "E"
            a.px(x, y, c)
    a.rect(sx1, sy1, sx2, sy1 + 1, "K")
    a.rect(sx1, sy2 - 1, sx2, sy2, "K")
    # grip: dark leather + gold wire
    rx1, ry1, rx2, ry2 = VENOM_REG["grip"]
    a.rect(rx1, ry1, rx2, ry2, "K")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "e")
    for y in range(ry1 + 3, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 2) % (rx2 - rx1 - 2)
        a.px(x, y, "Y")
        a.px(x + 1, y, "O")
    for yy in (ry1 + 2, ry2 - 3):
        a.hline(rx1 + 1, rx2 - 1, yy, "O")
    # pommel
    px1, py1, px2, py2 = VENOM_REG["pommel"]
    a.rect(px1, py1, px2, py2, "o")
    a.rect(px1 + 1, py1 + 1, px2 - 1, py2 - 1, "O")
    a.rect(px1 + 3, py1 + 2, px2 - 3, py2 - 2, "Y")
    a.hline(px1 + 3, px2 - 4, py1 + 2, "y")
    # emerald gem
    gx1, gy1, gx2, gy2 = VENOM_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 4:
                a.px(x, y, "n" if d <= 1 else "N" if d <= 2.6 else
                     "M" if x < (gx1 + gx2) / 2 else "m")
    # green venom glow
    gx1, gy1, gx2, gy2 = VENOM_REG["glow"]
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = math.hypot(x - (gx1 + gx2) / 2, y - (gy1 + gy2) / 2)
            a.px(x, y, "V" if d < 2 else "v" if d < 4 else
                 "G" if d < 6 else "g" if d < 7.5 else ".")
    # acid tip and drip
    tx1, ty1, tx2, ty2 = VENOM_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "V")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "v")
    dx1, dy1, dx2, dy2 = VENOM_REG["drop"]
    a.rect(dx1, dy1, dx2, dy2, "G")
    a.px(dx1 + 1, dy1 + 1, "V")
    a.px(dx2 - 2, dy2 - 2, "g")
    return a.im


def build_venom_rapier():
    pal, reg = VENOM_PAL, VENOM_REG
    G = 5.65
    pivot = (8.0, G, 8.0)
    zc = 8.0
    y0, y1 = 6.05, 17.25
    bounds = [0.0, 0.15, 0.31, 0.47, 0.62, 0.76, 0.88, 0.95, 1.0]

    def width_at(t):
        return 0.74 - 0.16 * t - 0.24 * t ** 3

    def thick_at(t):
        return 0.25 - 0.09 * t

    els = []
    blade_stack(els, pivot, zc, y0, y1, bounds, width_at, thick_at, reg,
                edge_w=0.11, edges=("l", "r"), edge_sections=3,
                spine_side="l", spine_w=0.10, tip_len=0.44)
    # snake-form guard arms: a smooth 22.5-degree S-curve on each side
    sfaces = lambda kind, rev: faces_all(region_uv(reg["snake"]))
    for side, sign in (("l", -1), ("r", 1)):
        a22, b22 = math.cos(math.radians(22.5)), math.sin(math.radians(22.5))
        a45 = math.cos(math.radians(45.0))
        deltas = [(sign * 0.46, 0.0),
                  (sign * 0.40 * a22, 0.40 * b22),
                  (sign * 0.38 * a45, 0.38 * a45),
                  (sign * 0.36 * a22, 0.36 * b22),
                  (sign * 0.26 * a22, -0.26 * b22)]
        head = _chain(els, pivot, (8.0, 5.62), deltas, 0.155, 0.26, zc,
                      sfaces, f"snake_{side}")
        # flattened head + red eye
        hf = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.15, 0.3, 0.85, 0.8))
        els.append(transformed_seg(f"snake_head_{side}", pivot,
                                   (head[0], head[1] - 0.06),
                                   (head[0] + sign * 0.24, head[1] + 0.06),
                                   0.20, zc - 0.15, zc + 0.15, hf, ext=0.02))
        ef = lambda kind, rev: faces_all(region_uv(reg["drop"]))
        els.append(transformed_seg(f"snake_eye_{side}", pivot,
                                   (head[0] + sign * 0.14, head[1] - 0.02),
                                   (head[0] + sign * 0.19, head[1] + 0.03),
                                   0.07, zc + 0.15, zc + 0.17, ef))
        df = lambda kind, rev: faces_all(region_uv(reg["drop"]))
        els.append(transformed_seg(f"venom_drop_{side}", pivot,
                                   (head[0], head[1] - 0.10),
                                   (head[0], head[1] - 0.40), 0.12,
                                   zc - 0.07, zc + 0.07, df, ext=0.0))
    # guard core and emerald
    cfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.2, 0.2, 0.8, 0.8))
    els.append(transformed_seg("guard_core", pivot, (8.0, 5.38), (8.0, 5.92),
                               0.90, zc - 0.34, zc + 0.34, cfaces, ext=0.0))
    gfaces = lambda kind, rev: faces_all(region_uv(reg["gem"]))
    for side, zz in (("f", zc + 0.35), ("b", zc - 0.38)):
        els.append(transformed_seg(f"guard_gem_{side}", pivot,
                                   (7.81, 5.46), (8.19, 5.84), 0.38,
                                   zz, zz + 0.03, gfaces))
    # grip, pommel, emerald
    grip_stack(els, pivot, zc, 2.12, 5.42, 0.58, 0.58, reg,
               bands=7, band_region="edge", band_w=0.07,
               gem_size=0.36, pommel_w=0.40)
    return els


# --------------------------------------------------------------------------
# 3. alloy_sword
# --------------------------------------------------------------------------

ALLOY_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(30, 28, 30), "i": P(62, 60, 64), "I": P(104, 102, 108),
    "S": P(150, 150, 158), "W": P(198, 200, 208), "w": P(236, 240, 246),
    "c": P(102, 52, 28), "C": P(158, 86, 44), "X": P(210, 128, 70),
    "x": P(246, 176, 112),
    "o": P(98, 70, 24), "O": P(158, 118, 44), "Y": P(216, 176, 88),
    "y": P(250, 228, 150),
    "l": P(44, 30, 22), "L": P(74, 50, 34),
    "a": P(170, 84, 20), "A": P(242, 150, 42), "b": P(255, 214, 120),
}
ALLOY_REG = {
    "blade": (0, 0, 16, 44), "edge": (16, 0, 22, 44),
    "spine": (22, 0, 28, 44), "side": (22, 0, 28, 44),
    "guard": (28, 0, 44, 18),
    "grip": (28, 18, 44, 42), "pommel": (28, 42, 44, 56),
    "gem": (44, 16, 52, 24), "copper": (44, 24, 60, 40),
    "glow": (44, 0, 60, 16), "tip": (52, 40, 60, 48),
    "tip2": (56, 40, 60, 44),
}


def paint_alloy_sword(phase=0):
    a = Atlas(ALLOY_PAL)
    bx1, by1, bx2, by2 = ALLOY_REG["blade"]
    # layered alloy: thin copper rims, gold pin-stripes, bright steel core
    a.cols(bx1, by1, bx2, by2,
           ["c", "C", "X", "S", "W", "W", "S", "W",
            "W", "S", "W", "W", "S", "X", "C", "c"])
    for y in range(by1, by2):
        if y % 6 == 0:
            a.px(bx1 + 2, y, "y")
            a.px(bx2 - 3, y, "y")
        if y % 9 == 0:
            a.px(bx1 + 4, y, "S")
            a.px(bx2 - 5, y, "S")
        if y > 5:
            a.px(bx1, y, "C")
            a.px(bx2 - 1, y, "C")
    for y in range(by1, by1 + 6):
        t = y - by1
        for x in range(bx1 + 4 + t // 2, bx2 - 4 - t // 2):
            a.px(x, y, "w" if x in (7, 8) else "W")
    ex1, ey1, ex2, ey2 = ALLOY_REG["edge"]
    a.cols(ex1, ey1, ex2, ey2, ["I", "S", "W", "w", "W", "S"])
    sx1, sy1, sx2, sy2 = ALLOY_REG["spine"]
    a.cols(sx1, sy1, sx2, sy2, ["c", "C", "X", "C", "c", "c"])
    for y in range(sy1, sy2, 5):
        a.px(sx1 + 2, y, "x")
    # gold guard with copper inlay and rivets
    gx1, gy1, gx2, gy2 = ALLOY_REG["guard"]
    a.rect(gx1, gy1, gx2, gy2, "o")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "O")
    a.rect(gx1 + 2, gy1 + 2, gx2 - 2, gy2 - 4, "Y")
    a.hline(gx1 + 2, gx2 - 2, gy1 + 2, "y")
    a.rect(gx1 + 4, gy1 + 6, gx2 - 4, gy1 + 9, "C")
    a.hline(gx1 + 4, gx2 - 4, gy1 + 7, "X")
    for rx in (gx1 + 3, gx2 - 4):
        for ry in (gy1 + 4, gy1 + 11):
            a.px(rx, ry, "y")
            a.px(rx + 1, ry, "O")
    # copper weave grip
    rx1, ry1, rx2, ry2 = ALLOY_REG["grip"]
    a.rect(rx1, ry1, rx2, ry2, "l")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "L")
    for y in range(ry1 + 2, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 3) % (rx2 - rx1 - 2)
        a.px(x, y, "X")
        a.px(x + 1, y, "C")
    for yy in (ry1 + 2, ry2 - 3):
        a.hline(rx1 + 1, rx2 - 1, yy, "O")
        a.hline(rx1 + 1, rx2 - 1, yy + 1, "o")
    # copper band region / glow
    cx1, cy1, cx2, cy2 = ALLOY_REG["copper"]
    for y in range(cy1, cy2):
        for x in range(cx1, cx2):
            a.px(x, y, "C" if (x + y) % 5 else "X")
    a.hline(cx1, cx2, cy1, "x")
    a.hline(cx1, cx2, cy2 - 1, "c")
    # pommel + amber gem
    px1, py1, px2, py2 = ALLOY_REG["pommel"]
    a.rect(px1, py1, px2, py2, "o")
    a.rect(px1 + 1, py1 + 1, px2 - 1, py2 - 1, "O")
    a.rect(px1 + 3, py1 + 2, px2 - 3, py2 - 2, "Y")
    a.hline(px1 + 3, px2 - 4, py1 + 2, "y")
    gx1, gy1, gx2, gy2 = ALLOY_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 4:
                a.px(x, y, "b" if d <= 1 else "A" if d <= 2.6 else
                     "a" if x < (gx1 + gx2) / 2 else "X")
    tx1, ty1, tx2, ty2 = ALLOY_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "W")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "w")
    a.px(tx1 + 2, ty1 + 2, "w")
    return a.im


def build_alloy_sword():
    pal, reg = ALLOY_PAL, ALLOY_REG
    G = 5.55
    pivot = (8.0, G, 8.0)
    zc = 8.0
    y0, y1 = 6.00, 17.10
    bounds = [0.0, 0.16, 0.33, 0.50, 0.66, 0.80, 0.91, 0.97, 1.0]

    def width_at(t):
        return 1.82 - 0.30 * t - 0.36 * t ** 3

    def thick_at(t):
        return 0.48 - 0.14 * t

    els = []
    blade_stack(els, pivot, zc, y0, y1, bounds, width_at, thick_at, reg,
                edge_w=0.11, edges=("l", "r"), edge_sections=3,
                spine_side="l", spine_w=0.14, ridge=False, tip_len=0.55,
                tip_steps=4)
    # raised copper / gold bands running along the wide face
    band_faces = lambda kind, rev: faces_all(region_uv(reg["copper"]))
    for side, xx in (("l", 7.62), ("r", 8.38)):
        for face, zz in (("f", zc + 0.255), ("b", zc - 0.285)):
            els.append(transformed_seg(f"band_{side}_{face}", pivot,
                                       (xx, y0 + 0.22), (xx, y1 - 1.0),
                                       0.17, zz, zz + 0.025, band_faces))
    # gold crossguard: core, straight arms and stepped tips
    gfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.1, 0.1, 0.9, 0.9))
    els.append(transformed_seg("guard_core", pivot, (8.0, G - 0.30),
                               (8.0, G + 0.34), 1.05,
                               zc - 0.42, zc + 0.42, gfaces, ext=0.0))
    for side, sign in (("l", -1), ("r", 1)):
        p = (8.0 + sign * 0.52, G + 0.02)
        q = (p[0] + sign * 1.35, p[1])
        els.append(transformed_seg(f"guard_arm_{side}", pivot, p, q, 0.24,
                                   zc - 0.20, zc + 0.20, gfaces, ext=0.03))
        r = (q[0] + sign * 0.42 * math.cos(math.radians(22.5)),
             q[1] + 0.42 * math.sin(math.radians(22.5)))
        els.append(transformed_seg(f"guard_tip_{side}", pivot, q, r, 0.28,
                                   zc - 0.22, zc + 0.22, gfaces, ext=0.02))
        b = (r[0] + sign * 0.10, r[1] + 0.16)
        els.append(transformed_seg(f"guard_knob_{side}", pivot, r, b, 0.20,
                                   zc - 0.18, zc + 0.18, gfaces, ext=0.02))
    # copper inlay collar on the guard
    cf = lambda kind, rev: faces_all(region_uv(reg["copper"]))
    els.append(transformed_seg("guard_inlay", pivot, (7.20, G + 0.04),
                               (8.80, G + 0.04), 0.16,
                               zc + 0.425, zc + 0.455, cf, ext=0.0))
    # grip / pommel / amber gem
    grip_stack(els, pivot, zc, 1.96, 5.36, 0.72, 0.72, reg,
               bands=6, band_region="copper", band_w=0.09,
               gem_size=0.40, pommel_w=0.48)
    return els


# --------------------------------------------------------------------------
# 4. blaze_sword
# --------------------------------------------------------------------------

BLAZE_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(46, 14, 10), "r": P(112, 26, 16), "R": P(178, 48, 18),
    "o": P(222, 88, 20), "O": P(248, 134, 30), "Y": P(255, 186, 54),
    "y": P(255, 232, 136), "W": P(255, 250, 222),
    "d": P(34, 24, 22), "D": P(62, 46, 40), "e": P(96, 74, 62),
    "g": P(98, 70, 24), "G": P(158, 118, 44), "H": P(216, 176, 88),
    "h": P(250, 228, 150),
    "i": P(28, 28, 34), "I": P(64, 62, 70), "S": P(122, 116, 120),
    "m": P(170, 28, 42), "M": P(240, 78, 58), "N": P(255, 150, 92),
}
BLAZE_REG = {
    "blade": (0, 0, 16, 44), "edge": (16, 0, 22, 44),
    "side": (22, 0, 28, 44), "guard": (28, 0, 44, 18),
    "grip": (28, 18, 44, 42), "pommel": (28, 42, 44, 56),
    "glow": (44, 0, 60, 16), "gem": (44, 16, 52, 24),
    "tongue": (52, 16, 60, 24), "tip": (44, 24, 60, 40),
    "tip2": (52, 40, 60, 48),
}
FIRE_EDGE = [
    ["R", "o", "O", "Y", "Y", "O"],
    ["o", "O", "Y", "y", "y", "Y"],
    ["O", "Y", "y", "Y", "Y", "y"],
    ["Y", "y", "Y", "O", "O", "Y"],
    ["y", "Y", "O", "R", "o", "O"],
    ["Y", "O", "R", "o", "O", "Y"],
    ["O", "R", "o", "O", "Y", "y"],
    ["R", "o", "O", "Y", "y", "Y"],
]


def paint_blaze_sword(phase=0):
    a = Atlas(BLAZE_PAL)
    bx1, by1, bx2, by2 = BLAZE_REG["blade"]
    a.cols(bx1, by1, bx2, by2,
           ["k", "r", "R", "o", "O", "Y", "y", "Y",
            "Y", "y", "Y", "O", "o", "R", "r", "k"])
    for y in range(by1, by2):
        for x in range(bx1, bx2):
            h = (x * 11 + y * 7) % 41
            if h == 0:
                a.px(x, y, "W")
            elif h == 5:
                a.px(x, y, "O")
            elif h == 9 and x in (5, 10):
                a.px(x, y, "k")
        # sparse dark scale chevrons near the spine
        if y % 11 in (0, 1):
            for x in range(bx1 + 2, bx2 - 6, 4):
                a.px(x, y, "k")
    for y in range(by1, by1 + 6):
        t = y - by1
        for x in range(bx1 + 4 + t // 2, bx2 - 4 - t // 2):
            a.px(x, y, "y" if x in (7, 8) else "Y")
    # animated flame edge
    ex1, ey1, ex2, ey2 = BLAZE_REG["edge"]
    cols = FIRE_EDGE[phase % len(FIRE_EDGE)]
    for y in range(ey1, ey2):
        shift = (y // 3 + phase) % len(FIRE_EDGE)
        row = FIRE_EDGE[shift]
        for i, c in enumerate(row):
            a.px(ex1 + i, y, c)
        if (y + phase) % 5 == 0:
            a.px(ex1 + 2, y, "W")
    sx1, sy1, sx2, sy2 = BLAZE_REG["side"]
    a.cols(sx1, sy1, sx2, sy2, ["k", "i", "I", "I", "i", "k"])
    # guard: black iron with gold flame rails
    gx1, gy1, gx2, gy2 = BLAZE_REG["guard"]
    a.rect(gx1, gy1, gx2, gy2, "d")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "D")
    a.hline(gx1 + 2, gx2 - 2, gy1 + 2, "e")
    a.hline(gx1 + 2, gx2 - 2, gy2 - 3, "k")
    for k in range(2, 15, 4):
        a.vline(gx1 + k, gy1 + 5, gy2 - 5, "G")
        a.px(gx1 + k + 1, gy1 + 6, "H")
        a.px(gx1 + k - 1, gy2 - 6, "g")
    # animated ember glow
    gx1, gy1, gx2, gy2 = BLAZE_REG["glow"]
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = math.hypot(x - (gx1 + gx2) / 2, y - (gy1 + gy2) / 2)
            if d < 2 + (phase % 3):
                c = "W"
            elif d < 4 + (phase % 2):
                c = "y"
            elif d < 6:
                c = "Y"
            elif d < 7:
                c = "O"
            else:
                c = "."
            a.px(x, y, c)
    # charred grip with ember bands
    rx1, ry1, rx2, ry2 = BLAZE_REG["grip"]
    a.rect(rx1, ry1, rx2, ry2, "d")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "D")
    for y in range(ry1 + 2, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 3) % (rx2 - rx1 - 2)
        a.px(x, y, "k")
        a.px(x + 1, y, "e")
    for k, yy in enumerate((ry1 + 4, ry1 + 10, ry1 + 16, ry2 - 5)):
        a.hline(rx1 + 1, rx2 - 1, yy, "o")
        a.hline(rx1 + 1, rx2 - 1, yy + 1, "O")
        a.px(rx1 + 6, yy, "y")
    # pommel
    px1, py1, px2, py2 = BLAZE_REG["pommel"]
    a.rect(px1, py1, px2, py2, "d")
    a.rect(px1 + 1, py1 + 1, px2 - 1, py2 - 1, "D")
    a.rect(px1 + 3, py1 + 2, px2 - 3, py2 - 2, "g")
    a.hline(px1 + 3, px2 - 4, py1 + 2, "H")
    a.px(px1 + 5, py1 + 4, "Y")
    # ember gem
    gx1, gy1, gx2, gy2 = BLAZE_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 4:
                a.px(x, y, "W" if d <= 1 else "y" if d <= 2.6 else
                     "O" if x < (gx1 + gx2) / 2 else "R")
    # flame tongue region: solid fire colours so guard teeth read as flame
    tx1, ty1, tx2, ty2 = BLAZE_REG["tongue"]
    cx = (tx1 + tx2 - 1) / 2.0
    for y in range(ty1, ty2):
        for x in range(tx1, tx2):
            d = abs(x - cx)
            a.px(x, y, "W" if d < 1 else "y" if d < 2 else
                 "O" if d < 3 else "R")
    # bright tip
    tx1, ty1, tx2, ty2 = BLAZE_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "Y")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "y")
    return a.im


def build_blaze_sword():
    pal, reg = BLAZE_PAL, BLAZE_REG
    G = 5.55
    pivot = (8.0, G, 8.0)
    zc = 8.0
    y0, y1 = 6.00, 16.40
    bounds = [0.0, 0.16, 0.33, 0.50, 0.65, 0.79, 0.90, 0.96, 1.0]

    def width_at(t):
        return 2.10 - 0.55 * t - 0.35 * t ** 3

    def thick_at(t):
        return 0.48 - 0.16 * t

    els = []
    blade_stack(els, pivot, zc, y0, y1, bounds, width_at, thick_at, reg,
                edge_w=0.12, edges=("l", "r"), edge_sections=3,
                spine_side=None, ridge=False, tip_len=0.48)
    # flame teeth along the cutting edge
    tfaces = lambda kind, rev: faces_all(region_uv(reg["tongue"]))
    for k, t in enumerate((0.30, 0.62)):
        yy = y0 + (y1 - y0) * t
        xx = 8.0 + width_at(t) / 2.0 - 0.02
        p1 = (xx + 0.36, yy + 0.36)
        p2 = (p1[0] + 0.17, p1[1] + 0.41)
        els.append(transformed_seg(f"tooth_{k}a", pivot, (xx, yy), p1, 0.18,
                                   zc - 0.14, zc + 0.14, tfaces, ext=0.01))
        els.append(transformed_seg(f"tooth_{k}b", pivot, p1, p2, 0.14,
                                   zc - 0.11, zc + 0.11, tfaces, ext=0.01))
    # flame guard: central iron block + two rising flame arms
    gfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.1, 0.1, 0.9, 0.9))
    els.append(transformed_seg("guard_core", pivot, (8.0, G - 0.28),
                               (8.0, G + 0.32), 0.92,
                               zc - 0.44, zc + 0.44, gfaces, ext=0.0))
    for side, sign in (("l", -1), ("r", 1)):
        deltas = [(sign * 0.84, 0.0), (sign * 0.55, 0.55),
                  (sign * 0.30, 0.55)]
        # dark iron backing + fire-coloured inner rail, so the guard reads
        # as a flame silhouette instead of a plain plate
        _chain(els, pivot, (8.0, G + 0.04), deltas, 0.26, 0.18, zc,
               gfaces, f"flameguard_back_{side}")
        end = _chain(els, pivot, (8.0, G + 0.04), deltas, 0.17, 0.26, zc,
                     tfaces, f"flameguard_{side}")
        els.append(transformed_seg(f"flameguard_tip_{side}", pivot,
                                   (end[0], end[1]),
                                   (end[0] + sign * 0.34, end[1] + 0.34),
                                   0.13, zc - 0.13, zc + 0.13, tfaces,
                                   ext=0.01))
        # lower flame prong under the guard
        low = [(sign * 0.52, -0.30), (sign * 0.38, -0.30)]
        _chain(els, pivot, (8.0, G - 0.10), low, 0.20, 0.20, zc,
               tfaces, f"flameguard_low_{side}")
    # charred grip / gold pommel / ember gem
    grip_stack(els, pivot, zc, 2.00, 5.36, 0.68, 0.68, reg,
               bands=6, band_region="edge", band_w=0.075,
               gem_size=0.38, pommel_w=0.44)
    return els


def paint_blaze_frames():
    return [paint_blaze_sword(p) for p in range(8)]


# --------------------------------------------------------------------------
# 5. greatsword
# --------------------------------------------------------------------------

GREAT_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(16, 16, 20), "K": P(38, 38, 46), "i": P(64, 66, 76),
    "I": P(96, 100, 112), "S": P(134, 138, 150), "W": P(180, 184, 196),
    "w": P(222, 226, 236),
    "g": P(94, 66, 22), "G": P(156, 116, 42), "H": P(214, 174, 84),
    "h": P(248, 226, 148),
    "l": P(48, 32, 22), "L": P(82, 54, 36), "d": P(26, 17, 13),
    "n": P(10, 10, 14), "r": P(118, 28, 28), "R": P(190, 58, 46),
}
GREAT_REG = {
    "blade": (0, 0, 16, 44), "edge": (16, 0, 22, 44),
    "spine": (22, 0, 28, 44), "side": (16, 0, 22, 44),
    "guard": (28, 0, 44, 18),
    "grip": (28, 18, 44, 42), "pommel": (28, 42, 44, 56),
    "gem": (44, 16, 52, 24), "glow": (44, 0, 60, 16),
    "tip": (44, 24, 60, 40), "notch": (52, 40, 60, 48),
}


def paint_greatsword(phase=0):
    a = Atlas(GREAT_PAL)
    bx1, by1, bx2, by2 = GREAT_REG["blade"]
    # heavy iron blade: bright steel with a fine dark fuller
    a.cols(bx1, by1, bx2, by2,
           ["k", "S", "W", "w", "w", "w", "W", "i",
            "i", "W", "w", "w", "w", "W", "S", "k"])
    for y in range(by1, by2):
        a.px(bx1 + 7, y, "i")
        a.px(bx1 + 8, y, "i")
        a.px(bx1 + 6, y, "S")
        a.px(bx1 + 9, y, "S")
        # hammered scratches and pitting
        h = (y * 17) % 43
        if h == 0:
            a.px(bx1 + 4, y, "w")
            a.px(bx1 + 5, y, "W")
        elif h == 7:
            a.px(bx2 - 6, y, "I")
        elif h == 13:
            a.px(bx1 + 10, y, "w")
        if y % 13 == 0:
            a.px(bx1 + 2, y, "I")
            a.px(bx2 - 3, y, "I")
    # notched cutting edge near the guard: dark bite out of the texture
    a.rect(bx2 - 2, by2 - 8, bx2, by2 - 5, "n")
    a.rect(bx2 - 1, by2 - 7, bx2, by2 - 6, "k")
    for y in range(by1, by1 + 6):
        t = y - by1
        for x in range(bx1 + 4 + t // 2, bx2 - 4 - t // 2):
            a.px(x, y, "w" if x in (7, 8) else "W")
    ex1, ey1, ex2, ey2 = GREAT_REG["edge"]
    a.cols(ex1, ey1, ex2, ey2, ["S", "W", "w", "w", "W", "S"])
    for y in range(ey1, ey2, 9):
        a.px(ex1 + 2, y, "W")
        a.px(ex1 + 3, y + 1, "W")
    sx1, sy1, sx2, sy2 = GREAT_REG["spine"]
    a.cols(sx1, sy1, sx2, sy2, ["k", "K", "i", "i", "K", "k"])
    # rough iron guard with brass bands and rivets
    gx1, gy1, gx2, gy2 = GREAT_REG["guard"]
    a.rect(gx1, gy1, gx2, gy2, "K")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "i")
    a.rect(gx1 + 2, gy1 + 2, gx2 - 2, gy2 - 5, "I")
    a.hline(gx1 + 2, gx2 - 2, gy1 + 2, "S")
    a.rect(gx1 + 4, gy1 + 7, gx2 - 4, gy1 + 10, "g")
    a.hline(gx1 + 4, gx2 - 4, gy1 + 8, "H")
    for rx in (gx1 + 3, gx2 - 4):
        for ry in (gy1 + 4, gy1 + 12):
            a.px(rx, ry, "h")
            a.px(rx + 1, ry, "G")
    # leather grip with black wrap and brass ferrules
    rx1, ry1, rx2, ry2 = GREAT_REG["grip"]
    a.rect(rx1, ry1, rx2, ry2, "l")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "L")
    for y in range(ry1 + 2, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 3) % (rx2 - rx1 - 2)
        a.px(x, y, "d")
        a.px(x + 1, y, "l")
    for yy in (ry1 + 2, ry2 - 3):
        a.hline(rx1 + 1, rx2 - 1, yy, "G")
        a.hline(rx1 + 1, rx2 - 1, yy + 1, "g")
    # iron pommel with brass ring
    px1, py1, px2, py2 = GREAT_REG["pommel"]
    a.rect(px1, py1, px2, py2, "K")
    a.rect(px1 + 1, py1 + 1, px2 - 1, py2 - 1, "i")
    a.rect(px1 + 3, py1 + 2, px2 - 3, py2 - 2, "I")
    a.hline(px1 + 3, px2 - 4, py1 + 2, "S")
    a.hline(px1 + 2, px2 - 3, py1 + 9, "G")
    a.hline(px1 + 2, px2 - 3, py1 + 10, "g")
    # bright tip and dark notch swatch
    tx1, ty1, tx2, ty2 = GREAT_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "W")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "w")
    nx1, ny1, nx2, ny2 = GREAT_REG["notch"]
    a.rect(nx1, ny1, nx2, ny2, "n")
    a.hline(nx1 + 1, nx2 - 2, ny1 + 1, "k")
    # tiny red garnet (reused by two guard rivets)
    gx1, gy1, gx2, gy2 = GREAT_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 3:
                a.px(x, y, "R" if d <= 1 else "r")
    return a.im


def build_greatsword():
    pal, reg = GREAT_PAL, GREAT_REG
    G = 5.50
    pivot = (8.0, G, 8.0)
    zc = 8.0
    y0, y1 = 5.95, 18.15
    bounds = [0.0, 0.13, 0.27, 0.42, 0.57, 0.71, 0.84, 0.94, 1.0]

    def width_at(t):
        return 3.20 - 0.42 * t - 0.58 * t ** 3

    def thick_at(t):
        return 0.94 - 0.30 * t

    els = []
    blade_stack(els, pivot, zc, y0, y1, bounds, width_at, thick_at, reg,
                edge_w=0.13, edges=("l", "r"), edge_sections=4,
                spine_side="l", spine_w=0.18, ridge=False, tip_len=0.60,
                tip_steps=4)
    # physical nick: a dark chip sitting over the edge near the guard
    nf = lambda kind, rev: faces_all(region_uv(reg["notch"]))
    ny = y0 + (y1 - y0) * 0.15
    els.append(transformed_seg("edge_notch", pivot,
                               (8.0 + width_at(0.15) / 2.0 - 0.08, ny),
                               (8.0 + width_at(0.15) / 2.0 + 0.14, ny),
                               0.30, zc - 0.50, zc + 0.50, nf, ext=0.0))
    # two raised bevels per face
    bf = lambda kind, rev: faces_all(region_uv(reg["edge"]))
    for side, xx in (("l", 7.18), ("r", 8.82)):
        for face, zz in (("f", zc + 0.44), ("b", zc - 0.47)):
            els.append(transformed_seg(f"bevel_{side}_{face}", pivot,
                                       (xx, y0 + 0.35), (xx, y1 - 1.3),
                                       0.26, zz, zz + 0.03, bf, ext=0.0))
    # massive crossguard
    gfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.1, 0.1, 0.9, 0.9))
    els.append(transformed_seg("guard_core", pivot, (8.0, G - 0.34),
                               (8.0, G + 0.38), 1.45,
                               zc - 0.50, zc + 0.50, gfaces, ext=0.0))
    for side, sign in (("l", -1), ("r", 1)):
        p = (8.0 + sign * 0.60, G + 0.02)
        q = (p[0] + sign * 1.55, p[1])
        els.append(transformed_seg(f"guard_arm_{side}", pivot, p, q, 0.42,
                                   zc - 0.24, zc + 0.24, gfaces, ext=0.05))
        r = (q[0] + sign * 0.55 * math.cos(math.radians(22.5)),
             q[1] + 0.55 * math.sin(math.radians(22.5)))
        els.append(transformed_seg(f"guard_tip_{side}", pivot, q, r, 0.44,
                                   zc - 0.26, zc + 0.26, gfaces, ext=0.03))
        els.append(transformed_seg(f"guard_knob_{side}", pivot, r,
                                   (r[0] + sign * 0.12, r[1] + 0.20), 0.30,
                                   zc - 0.20, zc + 0.20, gfaces, ext=0.02))
        # brass rivets on the guard face
        rf = lambda kind, rev: faces_all(region_uv(reg["gem"]))
        els.append(transformed_seg(f"guard_rivet_{side}", pivot,
                                   (8.0 + sign * 0.45, G + 0.08),
                                   (8.0 + sign * 0.33, G + 0.20), 0.16,
                                   zc + 0.505, zc + 0.525, rf))
    # brass band across the guard
    bfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.3, 0.6, 0.7, 0.9))
    els.append(transformed_seg("guard_band", pivot, (7.10, G + 0.02),
                               (8.90, G + 0.02), 0.16,
                               zc + 0.505, zc + 0.535, bfaces, ext=0.0))
    # long grip and iron pommel
    grip_stack(els, pivot, zc, 1.28, 5.28, 0.92, 0.92, reg,
               bands=5, band_region="guard", band_w=0.10,
               pommel=True, gem=False, pommel_w=0.55)
    pfaces = lambda kind, rev: faces_all(region_uv(reg["pommel"], 0.2, 0.6, 0.8, 0.9))
    els.append(transformed_seg("pommel_ring", pivot, (7.50, 0.98),
                               (8.50, 0.98), 0.16,
                               zc - 0.52, zc + 0.52, pfaces, ext=0.0))
    return els


# --------------------------------------------------------------------------
# 6. storm_greatsword
# --------------------------------------------------------------------------

STORM_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(28, 38, 52), "K": P(52, 66, 84), "i": P(80, 100, 122),
    "I": P(114, 138, 160), "S": P(152, 180, 200), "W": P(202, 224, 238),
    "w": P(240, 250, 255),
    "g": P(96, 70, 24), "G": P(158, 118, 44), "H": P(216, 176, 88),
    "h": P(250, 228, 150),
    "c": P(18, 112, 162), "C": P(56, 186, 228), "D": P(148, 238, 255),
    "E": P(230, 254, 255),
    "b": P(18, 58, 146), "B": P(58, 118, 218), "N": P(138, 198, 255),
    "l": P(38, 50, 70), "L": P(68, 88, 118),
}
STORM_REG = {
    "blade": (0, 0, 16, 44), "edge": (16, 0, 22, 44),
    "side": (22, 0, 28, 44), "guard": (28, 0, 44, 18),
    "grip": (28, 18, 44, 42), "pommel": (28, 42, 44, 56),
    "gem": (44, 16, 52, 24), "glow": (44, 0, 60, 16),
    "rune": (44, 24, 60, 56), "tip": (44, 56, 60, 64),
    "void": (63, 63, 64, 64),
}


def paint_storm_greatsword(phase=0):
    a = Atlas(STORM_PAL)
    bx1, by1, bx2, by2 = STORM_REG["blade"]
    a.cols(bx1, by1, bx2, by2,
           ["k", "K", "i", "I", "S", "W", "w", "W",
            "W", "w", "W", "S", "I", "i", "K", "k"])
    for y in range(by1, by2):
        if y % 5 == 0:
            a.px(bx1 + 5, y, "S")
            a.px(bx2 - 6, y, "S")
        if y % 9 == 0:
            a.px(bx1 + 4, y, "W")
            a.px(bx2 - 5, y, "W")
        if y % 11 == 0:
            a.px(bx1 + 8, y, "C")
        if y % 7 == 0:
            a.px(bx1 + 2, y, "H")
            a.px(bx2 - 3, y, "H")
    # gold filigree rails near the edges
    for y in range(by1, by2, 2):
        a.px(bx1 + 2, y, "G" if y % 4 else "H")
        a.px(bx2 - 3, y, "G" if y % 4 else "H")
    for y in range(by1, by1 + 6):
        t = y - by1
        for x in range(bx1 + 4 + t // 2, bx2 - 4 - t // 2):
            a.px(x, y, "E" if x in (7, 8) else "w")
    ex1, ey1, ex2, ey2 = STORM_REG["edge"]
    a.cols(ex1, ey1, ex2, ey2, ["S", "W", "w", "E", "w", "W"])
    for y in range(ey1, ey2, 6):
        a.px(ex1 + 2, y, "D")
        a.px(ex1 + 3, y + 1, "D")
    sx1, sy1, sx2, sy2 = STORM_REG["side"]
    a.cols(sx1, sy1, sx2, sy2, ["K", "i", "I", "I", "i", "K"])
    # gold wing guard plate
    gx1, gy1, gx2, gy2 = STORM_REG["guard"]
    a.rect(gx1, gy1, gx2, gy2, "g")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "G")
    a.rect(gx1 + 2, gy1 + 2, gx2 - 2, gy2 - 4, "H")
    a.hline(gx1 + 2, gx2 - 2, gy1 + 2, "h")
    a.hline(gx1 + 2, gx2 - 2, gy2 - 3, "g")
    for k in range(3, 14, 3):
        a.vline(gx1 + k, gy1 + 5, gy2 - 5, "G")
        a.px(gx1 + k + 1, gy1 + 6, "h")
    # sky-blue leather grip with gold wire
    rx1, ry1, rx2, ry2 = STORM_REG["grip"]
    a.rect(rx1, ry1, rx2, ry2, "l")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "L")
    for y in range(ry1 + 2, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 3) % (rx2 - rx1 - 2)
        a.px(x, y, "H")
        a.px(x + 1, y, "G")
    for yy in (ry1 + 2, ry2 - 3):
        a.hline(rx1 + 1, rx2 - 1, yy, "G")
        a.hline(rx1 + 1, rx2 - 1, yy + 1, "g")
    # gold pommel
    px1, py1, px2, py2 = STORM_REG["pommel"]
    a.rect(px1, py1, px2, py2, "g")
    a.rect(px1 + 1, py1 + 1, px2 - 1, py2 - 1, "G")
    a.rect(px1 + 3, py1 + 2, px2 - 3, py2 - 2, "H")
    a.hline(px1 + 3, px2 - 4, py1 + 2, "h")
    # sapphire
    gx1, gy1, gx2, gy2 = STORM_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 4:
                a.px(x, y, "E" if d <= 1 else "N" if d <= 2.6 else
                     "B" if x < (gx1 + gx2) / 2 else "b")
    # animated lightning glow
    gx1, gy1, gx2, gy2 = STORM_REG["glow"]
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = math.hypot(x - (gx1 + gx2) / 2, y - (gy1 + gy2) / 2)
            if d < 2 + (phase % 2):
                a.px(x, y, "E")
            elif d < 4:
                a.px(x, y, "D")
            elif d < 6:
                a.px(x, y, "C")
            else:
                a.px(x, y, ".")
    # rune overlay: transparent field + angular sky-runes, brightness pulses
    rxp = STORM_REG["rune"]
    rune_cols = ("C", "D", "E", "D", "C", "D", "E", "C")
    ry = rxp[1] + 2
    while ry < rxp[3] - 4:
        col = rune_cols[(phase + (ry // 7)) % len(rune_cols)]
        cx = rxp[0] + 8
        a.px(cx, ry, col)
        a.px(cx, ry + 1, col)
        a.px(cx - 2, ry + 1, col)
        a.px(cx + 2, ry + 2, col)
        a.px(cx, ry + 3, col)
        a.px(cx - 1, ry + 4, col)
        a.px(cx + 1, ry + 4, col)
        a.px(cx + 3, ry + 1, "D" if phase % 2 else "C")
        a.px(cx - 3, ry + 3, "D" if phase % 3 else "C")
        if phase % 2 == 0:
            a.px(cx + 4, ry, "E")
            a.px(cx - 4, ry + 2, "E")
        ry += 7
    # bright blue tip, void pixel stays transparent
    tx1, ty1, tx2, ty2 = STORM_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "w")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "E")
    return a.im


def paint_storm_frames():
    return [paint_storm_greatsword(p) for p in range(8)]


def overlay_faces(main_uv, void_uv):
    return {
        "north": {"uv": list(main_uv), "texture": "#0"},
        "south": {"uv": list(main_uv), "texture": "#0"},
        "east": {"uv": list(void_uv), "texture": "#0"},
        "west": {"uv": list(void_uv), "texture": "#0"},
        "up": {"uv": list(void_uv), "texture": "#0"},
        "down": {"uv": list(void_uv), "texture": "#0"},
    }


def build_storm_greatsword():
    pal, reg = STORM_PAL, STORM_REG
    G = 5.50
    pivot = (8.0, G, 8.0)
    zc = 8.0
    y0, y1 = 5.95, 18.35
    bounds = [0.0, 0.12, 0.26, 0.41, 0.56, 0.70, 0.83, 0.93, 1.0]

    def width_at(t):
        return 2.55 - 0.34 * t - 0.51 * t ** 3

    def thick_at(t):
        return 0.68 - 0.23 * t

    els = []
    blade_stack(els, pivot, zc, y0, y1, bounds, width_at, thick_at, reg,
                edge_w=0.12, edges=("l", "r"), edge_sections=3,
                spine_side=None, ridge=True, tip_len=0.58, tip_steps=4)
    # animated rune plates on both wide faces
    rune_uv = region_uv(reg["rune"])
    void_uv = region_uv(reg["void"])
    rf = overlay_faces(rune_uv, void_uv)
    rfaces = lambda kind, rev: rf
    for face, zz in (("f", zc + 0.30), ("b", zc - 0.33)):
        els.append(transformed_seg(f"rune_{face}", pivot,
                                   (8.0, y0 + 1.5), (8.0, y1 - 1.7),
                                   1.42, zz, zz + 0.025, rfaces, ext=0.0))
    # gold wing guard: central block, swept arms, three feather layers
    gfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.1, 0.1, 0.9, 0.9))
    els.append(transformed_seg("guard_core", pivot, (8.0, G - 0.30),
                               (8.0, G + 0.34), 1.16,
                               zc - 0.46, zc + 0.46, gfaces, ext=0.0))
    els.append(transformed_seg("wing_base", pivot, (8.0, G - 0.10),
                               (8.0, G + 0.42), 2.55,
                               zc - 0.16, zc + 0.16, gfaces, ext=0.0))
    for side, sign in (("l", -1), ("r", 1)):
        deltas = [(sign * 1.00, 0.0), (sign * 0.60, 0.40),
                  (sign * 0.45, 0.40)]
        end = _chain(els, pivot, (8.0, G + 0.05), deltas, 0.40, 0.26, zc,
                     gfaces, f"wing_arm_{side}")
        els.append(transformed_seg(f"wing_tip_{side}", pivot, end,
                                   (end[0] + sign * 0.30, end[1] + 0.26),
                                   0.24, zc - 0.16, zc + 0.16, gfaces,
                                   ext=0.02))
        # layered feather bars under the wing arm
        feathers = (
            ((8.0 + sign * 0.50, G - 0.02), (8.0 + sign * 1.38, G + 0.10), 0.26),
            ((8.0 + sign * 0.74, G + 0.22), (8.0 + sign * 1.66, G + 0.30), 0.24),
            ((8.0 + sign * 0.98, G + 0.46), (8.0 + sign * 1.86, G + 0.52), 0.21),
            ((8.0 + sign * 0.34, G - 0.16), (8.0 + sign * 1.08, G - 0.28), 0.20),
        )
        for k, (pa, pb, ww) in enumerate(feathers):
            els.append(transformed_seg(f"wing_feather_{side}{k}", pivot,
                                       pa, pb, ww, zc - 0.18, zc + 0.18,
                                       gfaces, ext=0.02))
    # guard gem (front and back)
    gemf = lambda kind, rev: faces_all(region_uv(reg["gem"]))
    for side, zz in (("f", zc + 0.47), ("b", zc - 0.50)):
        els.append(transformed_seg(f"guard_gem_{side}", pivot,
                                   (7.78, G - 0.08), (8.22, G + 0.36),
                                   0.44, zz, zz + 0.03, gemf))
    # gold collar at the blade root
    cfaces = lambda kind, rev: faces_all(region_uv(reg["guard"], 0.15, 0.55, 0.85, 0.92))
    els.append(transformed_seg("blade_collar", pivot, (8.0, 5.94),
                               (8.0, 6.34), 1.42,
                               zc - 0.36, zc + 0.36, cfaces, ext=0.0))
    # grip, pommel and large sapphire
    grip_stack(els, pivot, zc, 1.30, 5.32, 0.78, 0.78, reg,
               bands=7, band_region="guard", band_w=0.075,
               gem=True, gem_size=0.42, pommel_w=0.50)
    return els


# --------------------------------------------------------------------------
# 7. sickle
# --------------------------------------------------------------------------

SICKLE_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(22, 22, 28), "K": P(46, 48, 58), "i": P(76, 80, 92),
    "I": P(114, 120, 134), "S": P(154, 162, 176), "W": P(198, 208, 222),
    "w": P(238, 244, 252),
    "b": P(56, 36, 20), "B": P(88, 58, 32), "c": P(122, 84, 46),
    "C": P(158, 116, 70), "d": P(40, 25, 15),
    "g": P(78, 78, 86), "G": P(118, 118, 128), "H": P(164, 166, 176),
    "l": P(36, 27, 21), "L": P(64, 47, 33), "e": P(92, 70, 50),
    "r": P(116, 52, 32), "q": P(34, 74, 120), "Q": P(80, 150, 210),
    "T": P(160, 226, 255),
}
SICKLE_REG = {
    "blade": (0, 0, 40, 13), "edge": (0, 13, 40, 19),
    "spine": (0, 19, 40, 25), "wood": (0, 26, 16, 48),
    "metal": (16, 26, 32, 48), "wrap": (32, 26, 48, 48),
    "socket": (48, 26, 64, 40), "glow": (48, 0, 64, 16),
    "tip": (48, 40, 64, 48), "gem": (48, 48, 56, 56),
    "side": (0, 13, 40, 19),
}


def paint_sickle(phase=0):
    a = Atlas(SICKLE_PAL)
    # curved silver blade, length along x, width along y
    bx1, by1, bx2, by2 = SICKLE_REG["blade"]
    width_cols = ["W", "w", "W", "S", "S", "I", "I", "S",
                  "S", "I", "K", "K", "i"]
    for x in range(bx1, bx2):
        for y in range(by1, by2):
            c = width_cols[y - by1]
            h = (x * 7 + y * 5) % 37
            if h == 0 and y < 8:
                c = "w"
            elif h == 5 and 3 < y < 10:
                c = "K"
            elif h == 11:
                c = "S" if y < 6 else "I"
            a.px(x, y, c)
    # small notches on the cutting edge
    for nx in (7, 21, 33):
        a.px(nx, by1, "I")
        a.px(nx + 1, by1, "K")
        a.px(nx, by1 + 1, "I")
    # bright edge / dark spine strips
    ex1, ey1, ex2, ey2 = SICKLE_REG["edge"]
    for x in range(ex1, ex2):
        for y in range(ey1, ey2):
            a.px(x, y, "w" if (x + y) % 7 else "W")
    sx1, sy1, sx2, sy2 = SICKLE_REG["spine"]
    for x in range(sx1, sx2):
        for y in range(sy1, sy2):
            a.px(x, y, "k" if (x * 3 + y) % 5 else "K")
    # wooden shaft, grain runs along v
    wx1, wy1, wx2, wy2 = SICKLE_REG["wood"]
    for y in range(wy1, wy2):
        for x in range(wx1, wx2):
            c = "B" if (x + y // 3) % 4 else "c"
            if x in (2, 9, 13):
                c = "b"
            if (x * 5 + y * 3) % 47 == 0:
                c = "d"
            a.px(x, y, c)
    a.vline(wx1 + 5, wy1, wy2, "C")
    a.vline(wx1 + 10, wy1, wy2, "d")
    # iron fittings
    gx1, gy1, gx2, gy2 = SICKLE_REG["metal"]
    a.rect(gx1, gy1, gx2, gy2, "g")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "G")
    for yy in range(gy1 + 2, gy2, 5):
        a.hline(gx1 + 1, gx2 - 1, yy, "H")
        a.hline(gx1 + 1, gx2 - 1, yy + 1, "g")
    # leather grip wrap
    rx1, ry1, rx2, ry2 = SICKLE_REG["wrap"]
    a.rect(rx1, ry1, rx2, ry2, "l")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "L")
    for y in range(ry1 + 2, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 3) % (rx2 - rx1 - 2)
        a.px(x, y, "d")
        a.px(x + 1, y, "e")
    # socket
    sx1, sy1, sx2, sy2 = SICKLE_REG["socket"]
    a.rect(sx1, sy1, sx2, sy2, "k")
    a.rect(sx1 + 1, sy1 + 1, sx2 - 1, sy2 - 1, "K")
    for k in range(2, 16, 4):
        a.vline(sx1 + k, sy1 + 2, sy2 - 2, "G")
        a.px(sx1 + k + 1, sy1 + 4, "H")
    a.hline(sx1 + 1, sx2 - 1, sy1 + 2, "G")
    a.hline(sx1 + 1, sx2 - 1, sy2 - 3, "G")
    # bright tip
    tx1, ty1, tx2, ty2 = SICKLE_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "w")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "W")
    # small socket gem
    gx1, gy1, gx2, gy2 = SICKLE_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 3:
                a.px(x, y, "T" if d <= 1 else "Q" if d <= 2.2 else "q")
    return a.im


def scythe_shaft(els, reg, B=(3.10, 2.00), length=13.2, w=0.55, d=0.55,
                 bands=(0.07, 0.50, 0.87), grip_span=(0.14, 0.32),
                 prefix="scythe", butt_spike=True):
    ux, uy = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
    T = (B[0] + ux * length, B[1] + uy * length)
    zc = 8.0
    shaft_faces = lambda kind, rev: v_slice_faces(
        reg["wood"], reg["metal"], 0.0, 1.0, reg["metal"])
    els.append(seg_element(f"{prefix}_shaft", B, T, w,
                           zc - d / 2, zc + d / 2, shaft_faces))
    mf = lambda kind, rev: faces_all(region_uv(reg["metal"]))
    for k, t in enumerate(bands):
        px, py = B[0] + ux * length * t, B[1] + uy * length * t
        nx, ny = -uy, ux
        els.append(seg_element(f"{prefix}_band_{k}",
                               (px - nx * 0.34, py - ny * 0.34),
                               (px + nx * 0.34, py + ny * 0.34),
                               0.13, zc - d / 2 - 0.03, zc + d / 2 + 0.03,
                               mf, force_h=True))
    g0, g1 = grip_span
    gp0 = (B[0] + ux * length * g0, B[1] + uy * length * g0)
    gp1 = (B[0] + ux * length * g1, B[1] + uy * length * g1)
    wf = lambda kind, rev: v_slice_faces(reg["wrap"], reg["wrap"], 0.0, 1.0,
                                         reg["wrap"])
    els.append(seg_element(f"{prefix}_grip", gp0, gp1, w + 0.09,
                           zc - d / 2 - 0.045, zc + d / 2 + 0.045, wf))
    # socket sleeve + butt cap
    s0 = (B[0] + ux * length * 0.90, B[1] + uy * length * 0.90)
    s1 = (T[0] + ux * 0.22, T[1] + uy * 0.22)
    kf = lambda kind, rev: v_slice_faces(reg["socket"], reg["socket"],
                                         0.0, 1.0, reg["metal"])
    els.append(seg_element(f"{prefix}_socket", s0, s1, w + 0.18,
                           zc - d / 2 - 0.09, zc + d / 2 + 0.09, kf))
    b1 = (B[0] + ux * 0.26, B[1] + uy * 0.26)
    els.append(seg_element(f"{prefix}_butt", B, b1, w + 0.14,
                           zc - d / 2 - 0.07, zc + d / 2 + 0.07, mf))
    if butt_spike:
        sp = (B[0] - ux * 0.72, B[1] - uy * 0.72)
        els.append(seg_element(f"{prefix}_spike", sp, B, 0.22,
                               zc - 0.11, zc + 0.11, mf))
    return B, T


def scythe_blade(els, reg, start, width0=1.55, width1=0.42, th=0.40,
                 seg_len=0.95, dirs=(135, 157.5, 180, 202.5, 225), reps=2,
                 prefix="blade", edge_w=0.13, spine_w=0.15):
    zc = 8.0
    seq = []
    for d in dirs:
        seq.extend([d] * reps)
    total = seg_len * len(seq)
    p = start
    acc = 0.0
    samples = []
    for i, ang in enumerate(seq):
        rad = math.radians(ang)
        q = (p[0] + math.cos(rad) * seg_len, p[1] + math.sin(rad) * seg_len)
        t0, t1 = acc / total, (acc + seg_len) / total
        w = (width0 + (width1 - width0) * t1 ** 1.25
             + 0.14 * math.sin(math.pi * t1))
        bf = lambda kind, rev, a=t0, b=t1: h_slice_faces(
            reg["blade"], reg["side"], a, b, reg["tip"])
        els.append(seg_element(f"{prefix}_{i:02d}", p, q, w,
                               zc - th / 2, zc + th / 2, bf, ext=0.05,
                               force_h=True))
        # inner (concave) edge = cutting edge
        nx, ny = math.cos(rad + math.pi / 2), math.sin(rad + math.pi / 2)
        eo = w / 2 - 0.02
        ef = lambda kind, rev: faces_all(region_uv(reg["edge"]))
        els.append(seg_element(f"{prefix}_edge_{i:02d}",
                               (p[0] + nx * eo, p[1] + ny * eo),
                               (q[0] + nx * eo, q[1] + ny * eo),
                               edge_w, zc - th / 2 - 0.025,
                               zc + th / 2 + 0.025, ef, ext=0.055,
                               force_h=True))
        # outer (convex) spine
        so = w / 2 - 0.02
        sf = lambda kind, rev: faces_all(region_uv(reg["spine"]))
        els.append(seg_element(f"{prefix}_spine_{i:02d}",
                               (p[0] - nx * so, p[1] - ny * so),
                               (q[0] - nx * so, q[1] - ny * so),
                               spine_w, zc - th / 2 - 0.01,
                               zc + th / 2 + 0.01, sf, ext=0.05,
                               force_h=True))
        samples.append((p, q, ang, w))
        p = q
        acc += seg_len
    # pointed continuation of the curve, with the bright edge carried to the point
    last_ang = math.radians(seq[-1])
    ntx, nty = math.cos(last_ang + math.pi / 2), math.sin(last_ang + math.pi / 2)
    for k, (ln, ww) in enumerate(((0.55, width1 * 0.85), (0.42, width1 * 0.35))):
        q = (p[0] + math.cos(last_ang) * ln, p[1] + math.sin(last_ang) * ln)
        tf = lambda kind, rev: faces_all(region_uv(reg["tip"]))
        els.append(seg_element(f"{prefix}_tip_{k}", p, q, ww,
                               zc - th / 2 + 0.02, zc + th / 2 - 0.02, tf,
                               ext=0.02, force_h=True))
        eo = ww / 2 - 0.01
        ef = lambda kind, rev: faces_all(region_uv(reg["edge"]))
        els.append(seg_element(f"{prefix}_tip_edge_{k}",
                               (p[0] + ntx * eo, p[1] + nty * eo),
                               (q[0] + ntx * eo, q[1] + nty * eo),
                               0.10, zc - th / 2 + 0.01, zc + th / 2 - 0.01,
                               ef, ext=0.03, force_h=True))
        sf = lambda kind, rev: faces_all(region_uv(reg["spine"]))
        els.append(seg_element(f"{prefix}_tip_spine_{k}",
                               (p[0] - ntx * eo, p[1] - nty * eo),
                               (q[0] - ntx * eo, q[1] - nty * eo),
                               0.10, zc - th / 2 + 0.01, zc + th / 2 - 0.01,
                               sf, ext=0.03, force_h=True))
        p = q
    return p, samples


def build_sickle():
    pal, reg = SICKLE_PAL, SICKLE_REG
    els = []
    B, T = scythe_shaft(els, reg)
    ux, uy = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
    start = (T[0] + ux * 0.30, T[1] + uy * 0.30)
    # metal collar where the blade meets the shaft
    cf = lambda kind, rev: faces_all(region_uv(reg["metal"]))
    els.append(seg_element("blade_collar",
                           (start[0] - ux * 0.16, start[1] - uy * 0.16),
                           (start[0] + ux * 0.30, start[1] + uy * 0.30),
                           1.05, 8.0 - 0.30, 8.0 + 0.30, cf, force_h=False))
    tip, samples = scythe_blade(els, reg, start)
    # socket gem on both sides
    gfaces = lambda kind, rev: faces_all(region_uv(reg["gem"]))
    for face, zz in (("f", 8.0 + 0.34), ("b", 8.0 - 0.37)):
        els.append(seg_element(f"socket_gem_{face}",
                               (T[0] - ux * 0.55 - 0.22, T[1] - uy * 0.55 - 0.22),
                               (T[0] - ux * 0.55 + 0.22, T[1] - uy * 0.55 + 0.22),
                               0.44, zz, zz + 0.03, gfaces, force_h=True))
    return els


# --------------------------------------------------------------------------
# 8. hell_sickle
# --------------------------------------------------------------------------

HELL_PAL = {
    ".": (0, 0, 0, 0),
    "k": P(6, 4, 10), "K": P(18, 13, 26), "i": P(34, 25, 48),
    "I": P(58, 42, 78), "P": P(94, 60, 132), "p": P(146, 94, 198),
    "n": P(32, 20, 18), "N": P(56, 37, 30), "m": P(84, 58, 42),
    "r": P(118, 18, 14), "R": P(194, 48, 16), "o": P(240, 100, 18),
    "O": P(255, 158, 36), "Y": P(255, 210, 96), "W": P(255, 246, 198),
    "q": P(66, 18, 88), "Q": P(128, 46, 158), "V": P(190, 106, 220),
    "U": P(236, 190, 252),
    "g": P(70, 70, 80), "G": P(110, 110, 122), "H": P(158, 158, 170),
    "b": P(150, 20, 70), "B": P(232, 60, 130), "D": P(255, 160, 210),
    "l": P(24, 18, 18), "L": P(46, 34, 32),
}
HELL_REG = {
    "blade": (0, 0, 40, 13), "edge": (0, 13, 40, 19),
    "spine": (0, 19, 40, 25), "wood": (0, 26, 16, 48),
    "metal": (16, 26, 32, 48), "wrap": (32, 26, 48, 48),
    "socket": (48, 26, 64, 40), "glow": (48, 0, 64, 16),
    "tip": (48, 40, 64, 48), "gem": (48, 48, 56, 56),
    "side": (0, 13, 40, 19),
}


def paint_hell_sickle(phase=0):
    a = Atlas(HELL_PAL)
    # obsidian blade with purple veins, length along x
    bx1, by1, bx2, by2 = HELL_REG["blade"]
    width_cols = ["r", "R", "o", "O", "Y", "I", "P", "p",
                  "P", "i", "K", "k", "k"]
    for x in range(bx1, bx2):
        for y in range(by1, by2):
            c = width_cols[y - by1]
            if (x * 5 + y * 9) % 23 == 0 and y < 8:
                c = "V"
            elif (x * 3 + y * 7) % 31 == 0:
                c = "Q"
            elif (x + y * 2) % 19 == 0:
                c = "k"
            a.px(x, y, c)
    # purple cracks
    for cx in range(4, 40, 7):
        a.px(cx, by1 + 5, "Q")
        a.px(cx + 1, by1 + 6, "V")
        a.px(cx + 1, by1 + 7, "p")
        a.px(cx, by1 + 8, "i")
    # animated fire edge
    ex1, ey1, ex2, ey2 = HELL_REG["edge"]
    fire = ("R", "o", "O", "Y", "W", "Y", "O", "o", "R")
    for x in range(ex1, ex2):
        for y in range(ey1, ey2):
            idx = (x // 2 + y + phase) % len(fire)
            a.px(x, y, fire[idx])
            if (x + phase) % 9 == 0:
                a.px(x, y, "q" if y % 2 else "Q")
    sx1, sy1, sx2, sy2 = HELL_REG["spine"]
    for x in range(sx1, sx2):
        for y in range(sy1, sy2):
            a.px(x, y, "k" if (x * 3 + y) % 4 else "K")
    # netherite shaft
    wx1, wy1, wx2, wy2 = HELL_REG["wood"]
    for y in range(wy1, wy2):
        for x in range(wx1, wx2):
            c = "n" if (x + y // 3) % 4 else "N"
            if x in (3, 10, 13):
                c = "k"
            if (x * 5 + y * 3) % 41 == 0:
                c = "m"
            a.px(x, y, c)
    a.vline(wx1 + 6, wy1, wy2, "m")
    a.vline(wx1 + 11, wy1, wy2, "k")
    # dark iron fittings
    gx1, gy1, gx2, gy2 = HELL_REG["metal"]
    a.rect(gx1, gy1, gx2, gy2, "k")
    a.rect(gx1 + 1, gy1 + 1, gx2 - 1, gy2 - 1, "K")
    for yy in range(gy1 + 2, gy2, 5):
        a.hline(gx1 + 1, gx2 - 1, yy, "G")
        a.hline(gx1 + 1, gx2 - 1, yy + 1, "g")
    for k in range(3, 15, 5):
        a.px(gx1 + k, gy1 + 5, "p")
    # black leather wrap
    rx1, ry1, rx2, ry2 = HELL_REG["wrap"]
    a.rect(rx1, ry1, rx2, ry2, "l")
    a.rect(rx1 + 1, ry1 + 1, rx2 - 1, ry2 - 1, "L")
    for y in range(ry1 + 2, ry2 - 2):
        x = rx1 + 1 + ((y - ry1) * 3) % (rx2 - rx1 - 2)
        a.px(x, y, "K")
        a.px(x + 1, y, "i")
    # socket with purple cracks and rivets
    sx1, sy1, sx2, sy2 = HELL_REG["socket"]
    a.rect(sx1, sy1, sx2, sy2, "k")
    a.rect(sx1 + 1, sy1 + 1, sx2 - 1, sy2 - 1, "K")
    for k in range(2, 16, 4):
        a.vline(sx1 + k, sy1 + 2, sy2 - 2, "I")
        a.px(sx1 + k + 1, sy1 + 4, "P")
    a.hline(sx1 + 1, sx2 - 1, sy1 + 2, "G")
    a.hline(sx1 + 1, sx2 - 1, sy2 - 3, "G")
    # animated glow / fire core
    gx1, gy1, gx2, gy2 = HELL_REG["glow"]
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = math.hypot(x - (gx1 + gx2) / 2, y - (gy1 + gy2) / 2)
            if d < 2 + (phase % 2):
                a.px(x, y, "W")
            elif d < 4:
                a.px(x, y, "O")
            elif d < 6:
                a.px(x, y, "Q")
            elif d < 7:
                a.px(x, y, "q")
            else:
                a.px(x, y, ".")
    # fire tip
    tx1, ty1, tx2, ty2 = HELL_REG["tip"]
    a.rect(tx1, ty1, tx2, ty2, "Y")
    a.rect(tx1 + 1, ty1 + 1, tx2 - 1, ty2 - 1, "O")
    # magenta gem
    gx1, gy1, gx2, gy2 = HELL_REG["gem"]
    a.rect(gx1, gy1, gx2, gy2, ".")
    for y in range(gy1, gy2):
        for x in range(gx1, gx2):
            d = abs(x - (gx1 + gx2 - 1) / 2.0) + abs(y - (gy1 + gy2 - 1) / 2.0)
            if d <= 3:
                a.px(x, y, "D" if d <= 1 else "B" if d <= 2.2 else "b")
    return a.im


def paint_hell_frames():
    return [paint_hell_sickle(p) for p in range(8)]


def build_hell_sickle():
    pal, reg = HELL_PAL, HELL_REG
    els = []
    B, T = scythe_shaft(els, reg, B=(3.00, 1.80), length=13.6, w=0.66,
                        d=0.66, bands=(0.06, 0.48, 0.88),
                        grip_span=(0.13, 0.33), prefix="hell")
    ux, uy = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
    start = (T[0] + ux * 0.32, T[1] + uy * 0.32)
    cf = lambda kind, rev: faces_all(region_uv(reg["socket"]))
    els.append(seg_element("hell_collar",
                           (start[0] - ux * 0.18, start[1] - uy * 0.18),
                           (start[0] + ux * 0.34, start[1] + uy * 0.34),
                           1.18, 8.0 - 0.34, 8.0 + 0.34, cf, force_h=False))
    tip, samples = scythe_blade(els, reg, start, width0=1.85, width1=0.50,
                                th=0.46, seg_len=1.00,
                                dirs=(135, 157.5, 180, 202.5, 225),
                                reps=2, prefix="hblade",
                                edge_w=0.15, spine_w=0.18)
    # obsidian spikes along the convex spine
    sf = lambda kind, rev: faces_all(region_uv(reg["spine"]))
    for k, idx in enumerate((3, 6, 9)):
        p0, p1, ang, w = samples[idx]
        rad = math.radians(ang)
        nx, ny = math.cos(rad - math.pi / 2), math.sin(rad - math.pi / 2)
        base = ((p0[0] + p1[0]) / 2 + nx * (w / 2), (p0[1] + p1[1]) / 2 + ny * (w / 2))
        tipp = (base[0] + nx * (0.65 - 0.08 * k), base[1] + ny * (0.65 - 0.08 * k))
        mid = (base[0] + (tipp[0] - base[0]) * 0.62,
               base[1] + (tipp[1] - base[1]) * 0.62)
        els.append(seg_element(f"spine_spike_{k}", base, mid, 0.30,
                               8.0 - 0.16, 8.0 + 0.16, sf, ext=0.02))
        els.append(seg_element(f"spine_spike_tip_{k}", mid, tipp, 0.14,
                               8.0 - 0.10, 8.0 + 0.10, sf, ext=0.02))
        wf = lambda kind, rev: faces_all(region_uv(reg["gem"]))
        els.append(seg_element(f"spike_gem_{k}", tipp,
                               (tipp[0] - nx * 0.16, tipp[1] - ny * 0.16),
                               0.20, 8.0 - 0.10, 8.0 + 0.10, wf))
    # horn-like spikes rising from the socket
    for side, sign in (("l", -1), ("r", 1)):
        h0 = (T[0] + sign * 0.28, T[1] + 0.20)
        h1 = (h0[0] + sign * 0.55, h0[1] + 0.55)
        h2 = (h1[0] + sign * 0.18, h1[1] + 0.55)
        els.append(seg_element(f"horn_{side}a", h0, h1, 0.28,
                               8.0 - 0.16, 8.0 + 0.16, cf, ext=0.02))
        els.append(seg_element(f"horn_{side}b", h1, h2, 0.16,
                               8.0 - 0.12, 8.0 + 0.12, cf, ext=0.02))
        gf = lambda kind, rev: faces_all(region_uv(reg["gem"]))
        els.append(seg_element(f"horn_gem_{side}", h2,
                               (h2[0] + sign * 0.12, h2[1] + 0.12),
                               0.18, 8.0 - 0.09, 8.0 + 0.09, gf))
    # large socket gem
    gfaces = lambda kind, rev: faces_all(region_uv(reg["gem"]))
    for face, zz in (("f", 8.0 + 0.40), ("b", 8.0 - 0.43)):
        els.append(seg_element(f"hell_gem_{face}",
                               (T[0] - ux * 0.55 - 0.26, T[1] - uy * 0.55 - 0.26),
                               (T[0] - ux * 0.55 + 0.26, T[1] - uy * 0.55 + 0.26),
                               0.52, zz, zz + 0.03, gfaces, force_h=True))
    return els


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

WEAPONS = {
    "iron_rapier": {
        "paint": paint_iron_rapier,
        "build": build_iron_rapier,
        "animated": False,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "venom_rapier": {
        "paint": paint_venom_rapier,
        "build": build_venom_rapier,
        "animated": False,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "alloy_sword": {
        "paint": paint_alloy_sword,
        "build": build_alloy_sword,
        "animated": False,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "blaze_sword": {
        "paint": paint_blaze_frames,
        "build": build_blaze_sword,
        "animated": True,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "greatsword": {
        "paint": paint_greatsword,
        "build": build_greatsword,
        "animated": False,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "storm_greatsword": {
        "paint": paint_storm_frames,
        "build": build_storm_greatsword,
        "animated": True,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "sickle": {
        "paint": paint_sickle,
        "build": build_sickle,
        "animated": False,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
    "hell_sickle": {
        "paint": paint_hell_frames,
        "build": build_hell_sickle,
        "animated": True,
        "shots": [("front", (0.0, 0.10, 1.0), 46.0),
                  ("threequarter", (0.42, 0.24, 1.0), 46.0)],
    },
}


def run_one(wid, stage):
    spec = WEAPONS[wid]
    print(f"== {wid} ==")
    frames = spec["paint"]()
    if isinstance(frames, Image.Image):
        frames = [frames]
    atlas0 = save_texture(wid, frames, spec.get("animated", False))
    if stage in ("atlas",):
        return
    els = spec["build"]()
    backup_2d(wid)
    write_model(wid, els)
    if stage in ("model",):
        return
    atlas_for_preview = ART / f"_atlas_{wid}.png"
    atlas0.save(atlas_for_preview)
    preview_weapon(wid, atlas_for_preview, els, spec.get("shots"))


def make_overview(dst=None):
    dst = dst or (ART / "all_weapons_3d.png")
    meta = {
        "iron_rapier": ("铁细剑", "IRON RAPIER", "5.5 伤害 · 极快"),
        "venom_rapier": ("蛇毒细剑", "VENOM RAPIER", "7 伤害 · 蛇形护手"),
        "alloy_sword": ("合金剑", "ALLOY SWORD", "8 伤害 · 层叠合金"),
        "blaze_sword": ("烈焰剑", "BLAZE SWORD", "8 伤害 · 点燃 · 8 帧火焰"),
        "greatsword": ("巨剑", "GREATSWORD", "13 伤害 · 缓慢 · 刃根缺口"),
        "storm_greatsword": ("风暴大剑", "STORM GREATSWORD",
                             "15 伤害 · Boss 掉落 · 8 帧符文"),
        "sickle": ("死神镰刀", "SICKLE", "7 伤害 · 长攻击距离"),
        "hell_sickle": ("地狱镰刀", "HELL SICKLE",
                        "12 伤害 · 橙紫火刃 · 8 帧"),
    }
    order = ["iron_rapier", "venom_rapier", "alloy_sword", "blaze_sword",
             "greatsword", "storm_greatsword", "sickle", "hell_sickle"]
    W, H = 1960, 1330
    BG = (246, 247, 251)
    INK = (34, 32, 44)
    MUTED = (104, 102, 122)
    CARD = (255, 255, 255)
    LINE = (225, 224, 236)
    GOLD = (196, 158, 76)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    bold = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 46)
    semi = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 25)
    body = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 19)
    small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 17)
    d.text((70, 38), "weapon 模组 · 3D 武器图鉴", font=bold, fill=INK)
    d.text((72, 96),
           "8 把 2D 像素武器升级为原版合法 3D 物品模型 · 独立 64×64 像素图集",
           font=body, fill=MUTED)
    cols, rows = 4, 2
    cell_w, cell_h = 440, 505
    x0, y0 = 60, 150
    for idx, wid in enumerate(order):
        cx = x0 + (idx % cols) * (cell_w + 30)
        cy = y0 + (idx // cols) * (cell_h + 34)
        d.rounded_rectangle((cx + 4, cy + 6, cx + cell_w + 4, cy + cell_h + 6),
                            20, fill=(232, 231, 240))
        d.rounded_rectangle((cx, cy, cx + cell_w, cy + cell_h), 20,
                            fill=CARD, outline=LINE, width=2)
        prev = ART / f"weapon_preview_{wid}.png"
        if prev.exists():
            im = Image.open(prev).convert("RGB").resize((390, 390),
                                                        Image.LANCZOS)
            img.paste(im, (cx + 25, cy + 18))
        model = json.loads((MODELS / f"{wid}.json").read_text(encoding="utf-8"))
        tex = TEXTURES / f"{wid}_3d.png"
        tim = Image.open(tex)
        frames = tim.size[1] // tim.size[0] if tim.size[1] > tim.size[0] else 1
        name, en, stats = meta[wid]
        d.text((cx + 28, cy + 414), name, font=semi, fill=INK)
        d.text((cx + 28, cy + 447), en, font=small, fill=GOLD)
        d.text((cx + 28, cy + 470), stats, font=small, fill=MUTED)
        d.text((cx + cell_w - 28, cy + 448),
               f"{len(model['elements'])} el · {tim.size[0]}×{tim.size[1]}",
               font=small, fill=MUTED, anchor="ra")
    d.rounded_rectangle((60, 1246, W - 60, 1300), 14, fill=(237, 236, 245))
    d.text((84, 1260),
           "全部模型：无 parent · elements 直接内嵌 · 旋转仅 -45/-22.5/0/22.5/45 · UV 0..16 · 6 面 #0",
           font=small, fill=(72, 70, 90))
    d.text((W - 84, 1260), "Blockbench 预览 · Fabric 1.21.1",
           font=small, fill=(120, 116, 140), anchor="ra")
    img.save(dst)
    print("overview ->", dst)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--stage", default="all",
                    choices=("atlas", "model", "preview", "overview", "all"))
    args = ap.parse_args()
    if args.stage == "overview":
        make_overview()
        return
    names = [args.only] if args.only else list(WEAPONS)
    for wid in names:
        run_one(wid, args.stage)
    if not args.only and args.stage == "all":
        make_overview()


if __name__ == "__main__":
    main()
