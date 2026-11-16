"""Build the 3D obsidian odachi "Ryukiri" in Blockbench and export a Java item model.

Design references: the purpose-built 3D atlas (dark_tachi_3d_atlas_v2.png) and the
region table in dark_tachi_3d_layout_v2.json.  The 2D hand-drawn sprite is NOT used
for modelling decisions.

Stages:
  plan     draw the exact box silhouettes as a 2D scheme (no Blockbench)
  build    create the Blockbench project, cubes, export + patch the Java model
  preview  render the Blockbench viewport to PNG files
  all      plan + build + preview

Geometry: 22 body segments + 7 kissaki segments following a quadratic tachi curve,
a separate glowing edge bar per segment, an octagonal gold guard cut out of the
transparent tsuba region, a slim wrapped tsuka with fuchi / kashira / pommel plate.
"""
import base64
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
OUT_MODEL = ROOT / "src/main/resources/assets/weapon/models/item"
OUT_TEX = ROOT / "src/main/resources/assets/weapon/textures/item"
ATLAS = ART / "dark_tachi_3d_atlas_pixel.png"
LAYOUT = ART / "dark_tachi_3d_layout_v2.json"

sys.path.insert(0, r"C:/Users/Administrator/AppData/Local/Temp")
import bb_mcp  # noqa: E402

SIZE = 256
UVD = 16.0  # 256 px / 16 UV units
REG = json.loads(LAYOUT.read_text(encoding="utf-8"))["regions"]

# ---------------------------------------------------------------- UV helpers


def uvw(x1, y1, x2, y2, flipv=False, flipu=False):
    if flipu:
        x1, x2 = x2, x1
    if flipv:
        y1, y2 = y2, y1
    return [round(x1 / UVD, 4), round(y1 / UVD, 4),
            round(x2 / UVD, 4), round(y2 / UVD, 4)]


def blade_uv(t0, t1, u1=0.0, u2=48.0, flipv=True, flipu=False):
    x1, y1, x2, y2 = REG["blade_body"]
    return uvw(x1 + u1, y1 + t0 * (y2 - y1), x1 + u2, y1 + t1 * (y2 - y1),
               flipv=flipv, flipu=flipu)


def edge_uv(t0, t1, u1=0.0, u2=16.0, flipv=True, flipu=False):
    x1, y1, x2, y2 = REG["blade_edge"]
    return uvw(x1 + u1, y1 + t0 * (y2 - y1), x1 + u2, y1 + t1 * (y2 - y1),
               flipv=flipv, flipu=flipu)


def spine_uv(t0, t1, u1=0.0, u2=16.0, flipv=True):
    x1, y1, x2, y2 = REG["blade_spine"]
    return uvw(x1 + u1, y1 + t0 * (y2 - y1), x1 + u2, y1 + t1 * (y2 - y1),
               flipv=flipv)


def full(name, flipv=False, flipu=False):
    return uvw(*REG[name], flipv=flipv, flipu=flipu)


def sub(name, fx1=0.0, fy1=0.0, fx2=1.0, fy2=1.0, flipv=False, flipu=False):
    x1, y1, x2, y2 = REG[name]
    w, h = x2 - x1, y2 - y1
    return uvw(x1 + fx1 * w, y1 + fy1 * h, x1 + fx2 * w, y1 + fy2 * h,
               flipv=flipv, flipu=flipu)


TRANSPARENT = uvw(10, 240, 11, 241)

# ---------------------------------------------------------------- curve

BLADE_LEN = 10.4
ANG_BASE = 47.0
ANG_TIP = 74.0
BASE = (6.80, 5.75)
TIP_START = 0.845
N_BODY = 30
N_TIP = 9
W0, W1 = 1.58, 0.02
TH0, TH1 = 0.46, 0.30
Z_C = 8.0
GUARD_BACK = 0.06           # guard half thickness
HABAKI_START = 0.48         # from guard centre, along blade
BLADE_START = 0.76


def _bezier(p0, p1, p2, n=400):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def _arclen(pts):
    total = [0.0]
    for a, b in zip(pts, pts[1:]):
        total.append(total[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return total


def _tangent_intersection(p0, a0, p2, a1):
    d0 = (math.cos(math.radians(a0)), math.sin(math.radians(a0)))
    d1 = (math.cos(math.radians(a1)), math.sin(math.radians(a1)))
    det = d0[0] * d1[1] - d1[0] * d0[1]
    rx, ry = p2[0] - p0[0], p2[1] - p0[1]
    t = (rx * d1[1] - d1[0] * ry) / det
    return (p0[0] + t * d0[0], p0[1] + t * d0[1])


def make_curve(chord=10.0):
    mid = (ANG_BASE + ANG_TIP) * 0.5
    p2u = (BASE[0] + chord * math.cos(math.radians(mid)),
           BASE[1] + chord * math.sin(math.radians(mid)))
    p1u = _tangent_intersection(BASE, ANG_BASE, p2u, ANG_TIP)
    pts, al = _bezier(BASE, p1u, p2u), None
    al = _arclen(pts)
    k = BLADE_LEN / al[-1]
    p2 = (BASE[0] + (p2u[0] - BASE[0]) * k, BASE[1] + (p2u[1] - BASE[1]) * k)
    p1 = (BASE[0] + (p1u[0] - BASE[0]) * k, BASE[1] + (p1u[1] - BASE[1]) * k)
    pts = _bezier(BASE, p1, p2)
    return pts, _arclen(pts), p1, p2


CURVE, CURVE_AL, CTRL, TIP_PT = make_curve()


def sample(t):
    """point + unit tangent at normalised arc length t (0 base, 1 tip)."""
    target = min(max(t, 0.0), 1.0) * CURVE_AL[-1]
    lo, hi = 0, len(CURVE_AL) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if CURVE_AL[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    i = max(1, lo)
    a, b = CURVE[i - 1], CURVE[i]
    seg = (CURVE_AL[i] - CURVE_AL[i - 1]) or 1e-9
    f = (target - CURVE_AL[i - 1]) / seg
    p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1e-9
    return p, (dx / ln, dy / ln)


def width_at(t):
    if t <= TIP_START:
        f = t / TIP_START
        return W0 + (0.46 - W0) * (f ** 0.88)
    f = (t - TIP_START) / (1.0 - TIP_START)
    return 0.46 * ((1.0 - f) ** 1.25) + 0.02


def thickness_at(t):
    return TH0 + (TH1 - TH0) * t


def strip_width(t):
    # the glowing bar narrows with the blade so the kissaki ends in a point,
    # not in a bright whisker sticking past the steel
    w = width_at(t)
    return min(0.16, max(0.006, w * 0.60))


# ---------------------------------------------------------------- elements

def el(name, frm, to, origin, rot, faces):
    return {"name": name,
            "from": [round(v, 4) for v in frm],
            "to": [round(v, 4) for v in to],
            "origin": [round(v, 4) for v in origin],
            "rot": round(rot, 4),
            "faces": faces}


def box(name, cx, cy, w, l, z0, z1, rot, faces):
    """Axis-aligned box centred on (cx, cy), rotated about its own centre.

    Blockbench/Java store from/to in absolute model space; rotation happens
    around `origin`, so the pivot is the box centre and from/to are absolute.
    """
    return el(name,
              (cx - w / 2.0, cy - l / 2.0, z0),
              (cx + w / 2.0, cy + l / 2.0, z1),
              (cx, cy, (z0 + z1) / 2.0),
              rot, faces)


def blade_elements():
    out = []
    n = N_BODY + N_TIP
    for i in range(n):
        t0 = (i / N_BODY) * TIP_START if i < N_BODY else TIP_START + (i - N_BODY) / N_TIP * (1 - TIP_START)
        t1 = ((i + 1) / N_BODY) * TIP_START if i < N_BODY else TIP_START + (i - N_BODY + 1) / N_TIP * (1 - TIP_START)
        ov = 0.05 if i < N_BODY else 0.022
        ta = max(0.0, t0 - ov / BLADE_LEN)
        tb = min(1.0, t1 + ov / BLADE_LEN)
        pa, _ = sample(ta)
        pb, _ = sample(tb)
        cx, cy = (pa[0] + pb[0]) * 0.5, (pa[1] + pb[1]) * 0.5
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        ln = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx))
        th = thickness_at((t0 + t1) * 0.5)
        w = width_at((t0 + t1) * 0.5)
        name = f"blade_{i:02d}"
        faces = {
            "north": {"uv": blade_uv(t0, t1), "texture": "#0"},
            "south": {"uv": blade_uv(t0, t1), "texture": "#0"},
            "east": {"uv": blade_uv(t0, t1, 43.0, 48.0), "texture": "#0"},
            "west": {"uv": spine_uv(t0, t1), "texture": "#0"},
            "up": {"uv": sub("blade_body", 0.0, 0.0, 0.17, 0.035), "texture": "#0"},
            "down": {"uv": sub("blade_body", 0.0, 0.0, 0.17, 0.035), "texture": "#0"},
        }
        if i == n - 1:
            faces["up"] = {"uv": sub("blade_tip", 0.75, 0.0, 1.0, 0.25), "texture": "#0"}
        out.append(box(name, cx, cy, w, ln, Z_C - th / 2, Z_C + th / 2,
                       ang - 90.0, faces))

        # glowing edge bar, centred exactly on the cutting edge so it reads as
        # a bright line from both sides while staying inside the blade depth.
        nx = math.cos(math.radians(ang - 90.0))
        ny = math.sin(math.radians(ang - 90.0))
        ex = cx + nx * (w * 0.5)
        ey = cy + ny * (w * 0.5)
        sw = strip_width((t0 + t1) * 0.5)
        sth = th + 0.016
        efaces = {
            "north": {"uv": edge_uv(t0, t1), "texture": "#0"},
            "south": {"uv": edge_uv(t0, t1), "texture": "#0"},
            "east": {"uv": edge_uv(t0, t1, 12.0, 16.0), "texture": "#0"},
            "west": {"uv": edge_uv(t0, t1, 0.0, 2.0), "texture": "#0"},
            "up": {"uv": sub("blade_edge", 0.0, 0.0, 1.0, 0.03), "texture": "#0"},
            "down": {"uv": sub("blade_edge", 0.0, 0.0, 1.0, 0.03), "texture": "#0"},
        }
        if i == n - 1:
            efaces["north"] = {"uv": full("glow"), "texture": "#0"}
            efaces["south"] = {"uv": full("glow"), "texture": "#0"}
            efaces["east"] = {"uv": full("glow"), "texture": "#0"}
            efaces["up"] = {"uv": full("glow"), "texture": "#0"}
            efaces["down"] = {"uv": full("glow"), "texture": "#0"}
        out.append(box(f"edge_{i:02d}", ex, ey, sw, ln,
                       Z_C - sth / 2, Z_C + sth / 2, ang - 90.0, efaces))
    return out


def guard_centre():
    u = (math.cos(math.radians(ANG_BASE)), math.sin(math.radians(ANG_BASE)))
    return (BASE[0] - u[0] * BLADE_START, BASE[1] - u[1] * BLADE_START)


T = guard_centre()
UH = (math.cos(math.radians(ANG_BASE)), math.sin(math.radians(ANG_BASE)))


def at(dist):
    return (T[0] + UH[0] * dist, T[1] + UH[1] * dist)


def gface(name, rot=0.0):
    return {"uv": full(name), "texture": "#0"}


def gold_faces():
    return {d: gface("gold_trim") for d in
            ("north", "south", "east", "west", "up", "down")}


def fitting_elements():
    out = []
    # habaki (gold blade collar)
    hc = at((HABAKI_START + BLADE_START - 0.02) * 0.5)
    out.append(box("habaki", hc[0], hc[1], 1.62, BLADE_START - 0.02 - HABAKI_START,
                   Z_C - 0.25, Z_C + 0.25, ANG_BASE - 90.0, gold_faces()))
    sc = at((GUARD_BACK + HABAKI_START) * 0.5)
    out.append(box("seppa", sc[0], sc[1], 1.10, HABAKI_START - GUARD_BACK,
                   Z_C - 0.36, Z_C - 0.02, ANG_BASE - 90.0, gold_faces()))
    lip = at(BLADE_START - 0.03)
    out.append(box("habaki_lip", lip[0], lip[1], 1.68, 0.10,
                   Z_C - 0.27, Z_C + 0.27, ANG_BASE - 90.0, gold_faces()))

    # tsuba: a thin plate whose front/back show the transparent octagonal
    # texture; all four side faces are fully transparent so the silhouette is
    # a clean octagon instead of a rectangle with clipped corners.
    tsuba_faces = {}
    for d in ("north", "south"):
        tsuba_faces[d] = {"uv": full("tsuba"), "texture": "#0"}
    for d in ("east", "west", "up", "down"):
        tsuba_faces[d] = {"uv": TRANSPARENT, "texture": "#0"}
    out.append(box("tsuba", T[0], T[1], 2.70, 2.25,
                   Z_C - GUARD_BACK, Z_C + GUARD_BACK, 0.0, tsuba_faces))

    # tsuka
    fc = at(-0.25)
    out.append(box("fuchi", fc[0], fc[1], 0.82, 0.42,
                   Z_C - 0.44, Z_C + 0.44, ANG_BASE - 90.0, gold_faces()))
    hc2 = at(-1.61)
    handle_uv = uvw(124, 0, 156, 96)
    handle_faces = {d: {"uv": handle_uv, "texture": "#0"} for d in
                    ("north", "south", "east", "west")}
    handle_faces["up"] = {"uv": TRANSPARENT, "texture": "#0"}
    handle_faces["down"] = {"uv": TRANSPARENT, "texture": "#0"}
    out.append(box("tsuka", hc2[0], hc2[1], 0.64, 3.00,
                   Z_C - 0.36, Z_C + 0.36, ANG_BASE - 90.0, handle_faces))
    kc = at(-3.34)
    out.append(box("kashira", kc[0], kc[1], 0.78, 0.42,
                   Z_C - 0.42, Z_C + 0.42, ANG_BASE - 90.0, gold_faces()))
    pc = at(-3.36)
    pommel_faces = {}
    for d in ("north", "south"):
        pommel_faces[d] = {"uv": full("pommel"), "texture": "#0"}
    for d in ("east", "west", "up", "down"):
        pommel_faces[d] = {"uv": TRANSPARENT, "texture": "#0"}
    out.append(box("kashira_plate", pc[0], pc[1], 0.60, 0.60,
                   Z_C + 0.40, Z_C + 0.47, 0.0, pommel_faces))
    return out


def all_elements():
    return blade_elements() + fitting_elements()


def bbox(elements):
    xs, ys = [], []
    for e in elements:
        x1, y1, _ = e["from"]
        x2, y2, _ = e["to"]
        ang = math.radians(e["rot"])
        ox, oy, _ = e["origin"]
        for qx, qy in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            lx, ly = qx - ox, qy - oy
            rx = lx * math.cos(ang) - ly * math.sin(ang) + ox
            ry = lx * math.sin(ang) + ly * math.cos(ang) + oy
            xs.append(rx)
            ys.append(ry)
    return min(xs), min(ys), max(xs), max(ys)


def shift_elements(elements, dx, dy):
    for e in elements:
        for key in ("from", "to", "origin"):
            e[key][0] += dx
            e[key][1] += dy
    return elements


# ---------------------------------------------------------------- 2D plan

def draw_plan(elements, path):
    W = 18 * 70
    img = Image.new("RGB", (W, W), (22, 21, 28))
    d = ImageDraw.Draw(img)

    def P(p):
        return ((p[0] + 1.2) * 70, (17.0 - p[1]) * 70)

    def quad(e, fill, outline=(255, 255, 255, 40)):
        x1, y1, _ = e["from"]
        x2, y2, _ = e["to"]
        ang = math.radians(e["rot"])
        ox, oy, _ = e["origin"]
        pts = []
        for qx, qy in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            pts.append(P((qx * math.cos(ang) - qy * math.sin(ang) + ox,
                          qx * math.sin(ang) + qy * math.cos(ang) + oy)))
        d.polygon(pts, fill=fill, outline=outline)

    for e in elements:
        n = e["name"]
        if n.startswith("blade_"):
            quad(e, (44, 37, 60))
        elif n.startswith("edge_"):
            quad(e, (150, 92, 238))
        elif n in ("tsuka", "fuchi", "kashira"):
            quad(e, (34, 29, 42), (150, 130, 90))
        elif n in ("tsuba", "kashira_plate"):
            quad(e, (120, 96, 45), (240, 210, 130))
        elif n == "tsuba_gem":
            quad(e, (200, 30, 70), (255, 150, 170))
        else:
            quad(e, (190, 150, 70), (255, 220, 140))
    d.rectangle([P((0, 16)), P((16, 0))], outline=(90, 90, 110))
    img.save(path)


# ---------------------------------------------------------------- Blockbench

def init_mcp():
    bb_mcp.rpc("initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "zcode", "version": "1.0"},
    })
    bb_mcp.rpc("notifications/initialized", notify=True)


def js(code):
    r = bb_mcp.call_tool("risky_eval", {"code": code}, timeout=180)
    txt = r["result"]["content"][0]["text"]
    return json.loads(txt)


def build_in_blockbench(elements):
    print(bb_mcp.call_tool("create_project",
                           {"name": "dark_tachi_3d_v2", "format": "java_block"})
          ["result"]["content"][0]["text"][:120])
    tex = bb_mcp.call_tool("create_texture",
                           {"name": "dark_tachi_3d", "width": SIZE, "height": SIZE,
                            "data": str(ATLAS).replace("\\", "/")})
    print("texture:", tex["result"]["content"][0].get("text", "")[:200])
    info = js("const t=Texture.all[0]; JSON.stringify({n:t.name,w:t.width,h:t.height})")
    print("texture object:", info)

    for i in range(0, len(elements), 16):
        batch = elements[i:i + 16]
        payload = json.dumps(batch, separators=(",", ":"))
        code = f"""
const defs = {payload};
const tex = Texture.all[0];
for (const def of defs) {{
  const c = new Cube({{name: def.name, from: def.from, to: def.to,
    origin: def.origin, rotation: [0, 0, def.rot], box_uv: false, autouv: 0}}).init();
  c.rotation = [0, 0, def.rot];
  c.origin = def.origin;
  for (const dir of ['north', 'south', 'east', 'west', 'up', 'down']) {{
    const f = c.faces[dir];
    f.uv = def.faces[dir].uv;
    f.texture = tex;
  }}
}}
Canvas.updateAllFaces();
Canvas.updateAll();
JSON.stringify({{cubes: Cube.all.length}})
"""
        print("batch", i // 16 + 1, js(code))

    raw = ART / "dark_tachi_3d_raw.json"
    code = f"""
const out = Codecs.java_block.compile({{}});
require('fs').writeFileSync({json.dumps(str(raw).replace(chr(92), '/'))}, out);
'exported'
"""
    print(js(code))
    return raw


def norm_rotation(rot):
    if not rot:
        return None
    if "angle" in rot and "axis" in rot:
        if abs(float(rot["angle"])) < 1e-6:
            return None
        return {"origin": [round(v, 4) for v in rot["origin"]],
                "axis": rot["axis"], "angle": round(rot["angle"], 4)}
    vals = {k: float(rot.get(k, 0.0)) for k in ("x", "y", "z")}
    axis = max(vals, key=lambda k: abs(vals[k]))
    if abs(vals[axis]) < 1e-6:
        return None
    return {"origin": [round(v, 4) for v in rot["origin"]],
            "axis": axis, "angle": round(vals[axis], 4)}


def patch_model(raw_path, model_path):
    data = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    out = []
    for e in data["elements"]:
        faces = {}
        for name in ("north", "south", "east", "west", "up", "down"):
            src = e["faces"][name]
            faces[name] = {"uv": [round(float(v), 4) for v in src["uv"]],
                           "texture": "#0"}
        item = {"from": [round(float(v), 4) for v in e["from"]],
                "to": [round(float(v), 4) for v in e["to"]],
                "faces": faces}
        rot = norm_rotation(e.get("rotation"))
        if rot:
            item["rotation"] = rot
        out.append(item)
    model = {
        "textures": {"0": "weapon:item/dark_tachi_3d",
                     "particle": "weapon:item/dark_tachi_3d"},
        "elements": out,
        "display": {
            "thirdperson_righthand": {"rotation": [0, -90, 55],
                                      "translation": [0, 4, 0.5],
                                      "scale": [1.69, 1.69, 1.69]},
            "thirdperson_lefthand": {"rotation": [0, 90, -55],
                                     "translation": [0, 4, 0.5],
                                     "scale": [1.3, 1.3, 1.3]},
            "firstperson_righthand": {"rotation": [0, -90, 25],
                                      "translation": [1.13, 3.2, 1.13],
                                      "scale": [1.365, 1.365, 1.365]},
            "firstperson_lefthand": {"rotation": [0, 90, -25],
                                     "translation": [1.13, 3.2, 1.13],
                                     "scale": [1.05, 1.05, 1.05]},
            "gui": {"rotation": [0, 0, 0],
                    "translation": [0, 0, 0],
                    "scale": [1.56, 1.56, 1.56]},
            "ground": {"rotation": [0, 0, 0],
                       "translation": [0, 4, 0],
                       "scale": [0.78, 0.78, 0.78]},
            "fixed": {"rotation": [0, 0, 0],
                      "translation": [0, 0, 0],
                      "scale": [1.04, 1.04, 1.04]},
            "head": {"rotation": [0, 180, 0],
                     "translation": [0, 13, 7],
                     "scale": [1.3, 1.3, 1.3]},
        },
    }
    # Keep the full arbitrary-angle model as the editable source.
    (ART / "dark_tachi_3d_full.json").write_text(
        json.dumps(model, indent=2), encoding="utf-8")

    # Vanilla only accepts -45/-22.5/0/22.5/45 degrees.  Snap each slice and
    # add a little overlap so the faceted silhouette stays closed.
    allowed = (-45.0, -22.5, 0.0, 22.5, 45.0)
    for i, e in enumerate(out):
        rot = e.get("rotation")
        if rot:
            rot["angle"] = min(allowed, key=lambda a: abs(a - rot["angle"]))
        if i < 78:
            e["from"][1] = round(e["from"][1] - 0.08, 4)
            e["to"][1] = round(e["to"][1] + 0.08, 4)
    model["elements"] = out
    Path(model_path).write_text(json.dumps(model, indent=2), encoding="utf-8")
    return model


def validate(model_path):
    data = json.loads(Path(model_path).read_text(encoding="utf-8"))
    problems = []
    for i, e in enumerate(data["elements"]):
        if len(e["faces"]) != 6:
            problems.append(f"el{i}: {len(e['faces'])} faces")
        for d, f in e["faces"].items():
            uv = f["uv"]
            if any(v < -0.0001 or v > 16.0001 for v in uv):
                problems.append(f"el{i} {d} uv out of range {uv}")
            if f.get("texture") != "#0":
                problems.append(f"el{i} {d} texture {f.get('texture')}")
        if e["from"][0] > e["to"][0] or e["from"][1] > e["to"][1] or e["from"][2] > e["to"][2]:
            problems.append(f"el{i} from>to")
        if "rotation" in e:
            r = e["rotation"]
            if r["axis"] != "z" or r["angle"] not in (-45, -22.5, 0, 22.5, 45):
                problems.append(f"el{i} rotation {r}")
    xs, ys = [], []
    for e in data["elements"]:
        rot = e.get("rotation")
        ang = math.radians(rot["angle"]) if rot else 0.0
        if rot:
            px, py = rot["origin"][0], rot["origin"][1]
        else:
            px = (e["from"][0] + e["to"][0]) / 2.0
            py = (e["from"][1] + e["to"][1]) / 2.0
        for qx, qy in ((e["from"][0], e["from"][1]), (e["to"][0], e["from"][1]),
                       (e["to"][0], e["to"][1]), (e["from"][0], e["to"][1])):
            lx, ly = qx - px, qy - py
            xs.append(lx * math.cos(ang) - ly * math.sin(ang) + px)
            ys.append(lx * math.sin(ang) + ly * math.cos(ang) + py)
    print(f"validate: {len(data['elements'])} elements, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, "
          f"problems={len(problems)}")
    for p in problems[:12]:
        print("  !!", p)
    return problems


# ---------------------------------------------------------------- preview

def render(path, cam, target=(8, 8, 8), fov=30, w=853, h=684):
    code = f"""
const p = Preview.selected;
const c = p.camera;
p.renderer.setPixelRatio(1.25);
p.renderer.setSize({w}, {h}, false);
p.renderer.setViewport(0, 0, {w}, {h});
c.position.set({cam[0]}, {cam[1]}, {cam[2]});
p.controls.target.set({target[0]}, {target[1]}, {target[2]});
c.lookAt({target[0]}, {target[1]}, {target[2]});
p.controls.update();
c.fov = {fov};
c.aspect = p.canvas.width / p.canvas.height;
c.updateProjectionMatrix();
p.render();
const d = p.canvas.toDataURL('image/png');
require('fs').writeFileSync({json.dumps(str(path).replace(chr(92), '/'))},
  Buffer.from(d.split(',')[1], 'base64'));
'ok'
"""
    return js(code)


def _alpha_box(path):
    rgba = Image.open(path).convert("RGBA")
    alpha = rgba.getchannel("A").point(lambda a: 255 if a > 12 else 0)
    bb = alpha.getbbox()
    if not bb:
        raise SystemExit(f"empty render: {path}")
    return bb, rgba.size


def _vec(a, b, op):
    return tuple(op(x, y) for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(v):
    ln = math.sqrt(sum(x * x for x in v)) or 1e-9
    return tuple(x / ln for x in v)


def frame_model(path, direction, target=(8, 8, 8), fov=30, fill=0.72,
                canvas=(853, 684), iterations=4):
    """Blockbench's preview renders off-centre in its canvas; measure the
    alpha bbox and pan/zoom the camera until the model is centred and sized."""
    d = _norm(direction)
    target = list(target)
    cam = [target[0] + d[0] * 50, target[1] + d[1] * 50, target[2] + d[2] * 50]
    want = fill * canvas[1]
    for _ in range(iterations):
        render(path, cam, target=tuple(target), fov=fov, w=canvas[0], h=canvas[1])
        (x0, y0, x1, y1), (cw, ch) = _alpha_box(path)
        h = y1 - y0
        cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        dist = math.sqrt(sum((cam[i] - target[i]) ** 2 for i in range(3))) or 1e-9
        vis_h = 2.0 * dist * math.tan(math.radians(fov) * 0.5)
        vis_w = vis_h * (cw / ch)
        wx, wy = vis_w / cw, vis_h / ch
        fwd = _norm(_vec(target, cam, lambda a, b: b - a))
        right = _norm(_cross(fwd, (0.0, 1.0, 0.0)))
        up = _norm(_cross(right, fwd))
        dx = (cx - cw * 0.5) * wx
        dy = (cy - ch * 0.5) * wy
        pan = _vec(_vec((0.0, 0.0, 0.0), right, lambda a, b: b * dx),
                   up, lambda a, b: a - b * dy)
        for i in range(3):
            cam[i] += pan[i]
            target[i] += pan[i]
        nd = dist * (h / want)
        fwd2 = _norm(_vec(target, cam, lambda a, b: b - a))
        cam = [target[0] + fwd2[0] * nd, target[1] + fwd2[1] * nd,
               target[2] + fwd2[2] * nd]
    render(path, cam, target=tuple(target), fov=fov, w=canvas[0], h=canvas[1])
    (x0, y0, x1, y1), _ = _alpha_box(path)
    print(f"  framed {path.name}: bbox {(x0, y0, x1, y1)} h={y1 - y0}")
    return cam, target


def big_shot(path, direction, dist, target=(8.0, 8.0, 8.0), fov=30,
             canvas=(1800, 1350)):
    """Render large; Blockbench's viewport is off-centre, so the PNG is cropped
    afterwards.  Enlarge the distance if the model touches the canvas edge."""
    d = _norm(direction)
    for attempt in range(4):
        cam = (target[0] + d[0] * dist, target[1] + d[1] * dist,
               target[2] + d[2] * dist)
        render(path, cam, target=target, fov=fov, w=canvas[0], h=canvas[1])
        bb, size = _alpha_box(path)
        print(f"  {path.name} try{attempt} bbox={bb} dist={dist:.1f}")
        if bb[0] > 24 and bb[1] > 24 and bb[2] < size[0] - 24 and bb[3] < size[1] - 24:
            return cam
        dist *= 1.25
    return cam


def clean_framing(src, dst, size=1000, fill=0.62, bg=(255, 255, 255)):
    rgba = Image.open(src).convert("RGBA")
    alpha = rgba.getchannel("A")
    # the Blockbench canvas is transparent outside the model; use alpha so a
    # black background or a faint grid does not swallow the framing.
    bbox = alpha.point(lambda a: 255 if a > 12 else 0).getbbox()
    if not bbox:
        raise SystemExit("empty render")
    x0, y0, x1, y1 = bbox
    im = Image.new("RGB", rgba.size, bg)
    im.paste(rgba, mask=alpha)
    box = im.crop((x0, y0, x1, y1))
    scale = (size * fill) / max(box.size)
    bw, bh = int(box.size[0] * scale), int(box.size[1] * scale)
    box = box.resize((bw, bh), Image.LANCZOS)
    out = Image.new("RGB", (size, size), bg)
    out.paste(box, ((size - bw) // 2, (size - bh) // 2))
    out.save(dst)
    return (x0, y0, x1, y1), (bw, bh)


def _load_art(path, white=(255, 255, 255)):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", im.size, white)
    bg.paste(im, mask=im.getchannel("A"))
    return bg


def _content_crop(im, pad=10):
    gray = im.convert("L")
    mask = gray.point(lambda v: 255 if v < 250 else 0)
    bb = mask.getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.size[0], x1 + pad), min(im.size[1], y1 + pad)))


def make_compare2(dst, art2d, art3d):
    """Two-panel 2D vs 3D sheet in the spirit of the earlier comparison."""
    W, H = 1600, 900
    BG = (245, 244, 250)
    INK = (43, 36, 58)
    MUTED = (106, 98, 128)
    CARD = (255, 255, 255)
    LINE = (224, 220, 238)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    bold = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 44)
    semi = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 26)
    body = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 21)
    small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)

    def center(text, font, y, fill):
        bb = d.textbbox((0, 0), text, font=font)
        d.text(((W - (bb[2] - bb[0])) / 2, y), text, font=font, fill=fill)

    center("黑暗太刀「龙切」", bold, 34, INK)
    center("2D 像素手绘  ×  3D 像素风建模（Blockbench · Java 物品模型）", body, 96, MUTED)

    panels = [(70, 150, 760, 830), (840, 150, 1530, 830)]
    for (x0, y0, x1, y1) in panels:
        d.rounded_rectangle((x0 + 5, y0 + 7, x1 + 5, y1 + 7), 26, fill=(228, 225, 240))
        d.rounded_rectangle((x0, y0, x1, y1), 26, fill=CARD, outline=LINE, width=2)

    a2 = _content_crop(_load_art(art2d))
    a3 = _content_crop(_load_art(art3d))
    target_h = 545
    for (x0, y0, x1, y1), art in ((panels[0], a2), (panels[1], a3)):
        sc = target_h / art.size[1]
        w, h = int(art.size[0] * sc), target_h
        art = art.resize((w, h), Image.LANCZOS)
        cx = (x0 + x1) // 2
        img.paste(art, (cx - w // 2, y0 + 42))

    d.text((70 + 30, 742), "2D 手绘版", font=semi, fill=INK)
    d.text((70 + 30, 780), "64 × 64 贴图 · 8 帧紫色流光动画", font=small, fill=MUTED)
    d.text((840 + 30, 742), "3D 像素建模版", font=semi, fill=INK)
    d.text((840 + 30, 780), "86 个元素 · 39 段刀身 · 64 × 64 像素图集", font=small, fill=MUTED)

    badge = "NEW"
    bb = d.textbbox((0, 0), badge, font=small)
    bw = bb[2] - bb[0] + 22
    d.rounded_rectangle((1530 - bw - 18, 168, 1524, 196), 14, fill=(206, 168, 88))
    d.text((1530 - bw - 18 + 11, 171), badge, font=small, fill=(40, 30, 12))

    center("weapon:dark_tachi  ·  item/handheld  ·  0..16 UV 空间  ·  预览：Blockbench", small, 856, (132, 126, 150))
    img.save(dst)
    print("compare ->", dst)


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "plan"
    els = all_elements()
    x0, y0, x1, y1 = bbox(els)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    shift_elements(els, 8.0 - cx, 8.0 - cy)
    x0, y0, x1, y1 = bbox(els)
    print(f"elements={len(els)} bbox x {x0:.2f}..{x1:.2f}  y {y0:.2f}..{y1:.2f}")
    print(f"blade tip {TIP_PT[0] + 8.0 - cx:.2f},{TIP_PT[1] + 8.0 - cy:.2f} "
          f"guard {T[0] + 8.0 - cx:.2f},{T[1] + 8.0 - cy:.2f}")

    if stage in ("plan", "all"):
        draw_plan(els, ART / "dev_layout_v2.png")
        print("plan ->", ART / "dev_layout_v2.png")
    if stage in ("build", "all"):
        init_mcp()
        raw = build_in_blockbench(els)
        model = patch_model(raw, OUT_MODEL / "dark_tachi.json")
        validate(OUT_MODEL / "dark_tachi.json")
        shutil.copyfile(ATLAS, OUT_TEX / "dark_tachi_3d.png")
        print("wrote", OUT_MODEL / "dark_tachi_3d.json", len(model["elements"]))
    if stage in ("final", "all"):
        init_mcp()
        big_shot(ART / "dev_final_front.png", (0.0, 0.09, 1.0), 48.0)
        clean_framing(ART / "dev_final_front.png", ART / "dark_tachi_3d_final.png",
                      size=1000, fill=0.62)
        big_shot(ART / "dev_final_threequarter.png", (0.30, 0.20, 1.0), 46.0)
        clean_framing(ART / "dev_final_threequarter.png",
                      ART / "dark_tachi_3d_threequarter.png", size=1000, fill=0.62)
        make_compare2(ART / "dark_tachi_compare2.png",
                      ART / "dark_tachi_preview.png",
                      ART / "dark_tachi_3d_final.png")
    if stage in ("preview", "all"):
        init_mcp()
        for tag, direction, dist in [
            ("front", (0.0, 0.09, 1.0), 48.0),
            ("threequarter", (0.32, 0.20, 1.0), 46.0),
            ("back", (0.0, 0.16, -1.0), 48.0),
        ]:
            rawp = ART / f"dev_shot_{tag}.png"
            big_shot(rawp, direction, dist)
            info = clean_framing(rawp, ART / f"dev_clean_{tag}.png")
            print(tag, info)


if __name__ == "__main__":
    main()
