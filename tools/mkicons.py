#!/usr/bin/env python3
"""Generador de iconos circulares de Ocelote OS.

Uso:  python3 tools/mkicons.py [salida]     (por defecto: previsualizacion en /tmp)
Genera SVG (lo que usa el sistema) y, si Pillow esta instalado, una hoja de previsualizacion.
Los colores de cada icono estan en BADGES: cambialos para crear recolores/temas.
"""
import os, sys, colorsys

SIZE = 128
THEMES = {  # tema -> color base del circulo de cada icono
    "aurora": {"files":"#2F80ED","browser":"#FE9100","terminal":"#3B3B4A","editor":"#7C5CFA","settings":"#8A8F9C",
               "paint":"#E8508A","installer":"#2DB67C","shield":"#3BA76F","snake":"#66A82B","mines":"#3F51B5",
               "pong":"#26323F","themes":"#9C5CE0"},
    "aqua":   {"files":"#1E88E5","browser":"#FE9100","terminal":"#1F3350","editor":"#3F6FD8","settings":"#6B88A8",
               "paint":"#00ACC1","installer":"#26A69A","shield":"#1E9BD7","snake":"#26A69A","mines":"#3F6FD8",
               "pong":"#1A2F4F","themes":"#4FC3F7"},
    "grafito":{"files":"#7B8794","browser":"#FE9100","terminal":"#2E3038","editor":"#656C78","settings":"#959BA6",
               "paint":"#8B7B97","installer":"#5E8C7B","shield":"#5E8C7B","snake":"#7C8B5A","mines":"#5C6370",
               "pong":"#2B2D33","themes":"#8A8F9C"},
    "jade":   {"files":"#2E9E6E","browser":"#F4A21A","terminal":"#1F3D33","editor":"#4DB6AC","settings":"#7A9A8E",
               "paint":"#8BC34A","installer":"#00897B","shield":"#1F9D6B","snake":"#7CB342","mines":"#00897B",
               "pong":"#1F3D33","themes":"#4DB6AC"},
}
THEME_DIRS = {"aurora": "Ocelote", "aqua": "Ocelote-Aqua", "grafito": "Ocelote-Grafito", "jade": "Ocelote-Jade"}
BADGES = dict(THEMES["aurora"])

def use_theme(name):
    BADGES.clear(); BADGES.update(THEMES[name])
# nombres de icono (freedesktop) con los que se publica cada icono
ALIASES = {
    "files":     ["org.xfce.thunar", "org.xfce.filemanager", "thunar", "Thunar", "system-file-manager"],
    "browser":   ["firefox-esr", "firefox", "web-browser", "internet-web-browser", "ocelote-browser"],
    "terminal":  ["org.xfce.terminal", "org.xfce.terminalemulator", "xfce4-terminal", "utilities-terminal"],
    "editor":    ["org.xfce.mousepad", "mousepad", "accessories-text-editor"],
    "settings":  ["org.xfce.settings.manager", "xfce4-settings-manager", "preferences-system"],
    "paint":     ["ocelote-paint", "applications-graphics"],
    "installer": ["system-software-install", "calamares", "ocelote-installer"],
    "shield":    ["ocelote-escudo"],
    "snake":     ["ocelote-culebrita"],
    "mines":     ["ocelote-minas"],
    "pong":      ["ocelote-pong"],
    "themes":    ["ocelote-apariencia"],
}

def hex2rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def mix(c, t, k):  # mezcla c con el color t en proporcion k
    return tuple(int(round(c[i]*(1-k)+t[i]*k)) for i in range(3))
def rgb2hex(c): return "#%02x%02x%02x" % tuple(c)

W = (255,255,255)

def lin(top, bottom, y0, y1):
    return ("lin", top, bottom, y0, y1)

def scene(name):
    base = hex2rgb(BADGES[name])
    light = mix(base, W, 0.30); dark = mix(base, (0,0,0), 0.25)
    cx = cy = 64
    els = []
    # circulo base con degradado + borde
    els.append(dict(t="circle", cx=cx, cy=cy, r=60, fill=lin(light+(1,), dark+(1,), 4, 124)))
    els.append(dict(t="circle", cx=cx, cy=cy, r=59, fill=None, stroke=mix(dark,(0,0,0),0.4)+(0.55,), sw=2))
    # brillo de cristal (estilo Leopard)
    clip = ("circle", cx, cy, 58)
    els.append(dict(t="ellipse", cx=64, cy=36, rx=46, ry=30, fill=lin(W+(0.80,), W+(0.06,), 8, 66), clip=clip))
    els.append(dict(t="ellipse", cx=64, cy=118, rx=44, ry=18, fill=lin(W+(0.0,), W+(0.28,), 100, 124), clip=clip))
    g = glyph(name, base, dark)
    # sombra suave del glifo
    for e in g:
        s = dict(e); s["shadow"] = True; els.append(s)
    els.extend(g)
    return els

def glyph(name, base, dark):
    w = W + (1,)
    G = []
    if name == "files":
        G.append(dict(t="rrect", x=34, y=40, w=30, h=18, rx=5, fill=W+(0.80,)))
        G.append(dict(t="rrect", x=34, y=48, w=60, h=40, rx=7, fill=w))
        G.append(dict(t="rrect", x=34, y=54, w=60, h=34, rx=7, fill=mix(W,base,0.10)+(1,)))
    elif name == "browser":
        G.append(dict(t="circle", cx=64, cy=64, r=30, fill=None, stroke=w, sw=5))
        G.append(dict(t="ellipse", cx=64, cy=64, rx=13, ry=30, fill=None, stroke=w, sw=3.5))
        G.append(dict(t="line", pts=[(34,64),(94,64)], stroke=w, sw=3.5))
        G.append(dict(t="line", pts=[(38,50),(90,50)], stroke=w, sw=3.5))
        G.append(dict(t="line", pts=[(38,78),(90,78)], stroke=w, sw=3.5))
    elif name == "terminal":
        G.append(dict(t="line", pts=[(40,46),(60,64),(40,82)], stroke=w, sw=9))
        G.append(dict(t="line", pts=[(66,84),(90,84)], stroke=w, sw=9))
    elif name == "editor":
        G.append(dict(t="rrect", x=40, y=32, w=48, h=64, rx=7, fill=w))
        for y in (50, 63, 76):
            G.append(dict(t="line", pts=[(50,y),(78,y)], stroke=dark+(1,), sw=4.5))
    elif name == "settings":
        for y in (45, 64, 83):
            G.append(dict(t="line", pts=[(34,y),(94,y)], stroke=w, sw=5))
        for (x, y) in ((52,45),(76,64),(58,83)):
            G.append(dict(t="circle", cx=x, cy=y, r=8.5, fill=w, stroke=dark+(1,), sw=3))
    elif name == "paint":
        G.append(dict(t="ellipse", cx=64, cy=65, rx=35, ry=30, fill=w))
        for (x, y, c) in ((47,55,"#e53935"),(63,45,"#fdd835"),(82,52,"#43a047"),(88,70,"#1e88e5")):
            G.append(dict(t="circle", cx=x, cy=y, r=6.5, fill=hex2rgb(c)+(1,)))
        G.append(dict(t="circle", cx=60, cy=82, r=8, fill=dark+(1,)))
    elif name == "installer":
        G.append(dict(t="poly", pts=[(55,32),(73,32),(73,56),(88,56),(64,82),(40,56),(55,56)], fill=w))
        G.append(dict(t="line", pts=[(38,87),(38,95),(90,95),(90,87)], stroke=w, sw=6))
    elif name == "shield":
        G.append(dict(t="poly", pts=[(64,30),(92,40),(92,64),(85,83),(64,98),(43,83),(36,64),(36,40)], fill=w))
        G.append(dict(t="line", pts=[(51,63),(61,74),(79,52)], stroke=dark+(1,), sw=8))
    elif name == "snake":
        G.append(dict(t="line", pts=[(34,88),(34,70),(60,70),(60,52),(86,52)], stroke=w, sw=12))
        G.append(dict(t="circle", cx=88, cy=52, r=10, fill=w))
        G.append(dict(t="circle", cx=91, cy=49, r=2.8, fill=dark+(1,)))
        G.append(dict(t="circle", cx=86, cy=86, r=7, fill=(229,57,53,1)))
    elif name == "mines":
        for k in range(8):
            import math
            a = k * math.pi / 4
            G.append(dict(t="line", pts=[(64+14*math.cos(a), 68+14*math.sin(a)), (64+27*math.cos(a), 68+27*math.sin(a))],
                          stroke=(30,30,40,1), sw=6))
        G.append(dict(t="circle", cx=64, cy=68, r=19, fill=(30,30,40,1)))
        G.append(dict(t="circle", cx=57, cy=61, r=5, fill=(255,255,255,0.8)))
        G.append(dict(t="line", pts=[(76,52),(86,40)], stroke=w, sw=4))
        G.append(dict(t="circle", cx=89, cy=37, r=5, fill=(253,216,53,1)))
    elif name == "pong":
        G.append(dict(t="rrect", x=33, y=42, w=10, h=36, rx=4, fill=w))
        G.append(dict(t="rrect", x=85, y=52, w=10, h=36, rx=4, fill=w))
        G.append(dict(t="circle", cx=64, cy=62, r=7.5, fill=w))
    elif name == "themes":
        for (x, y, c) in ((50,50,"#8e24aa"),(78,50,"#1e88e5"),(50,78,"#78909c"),(78,78,"#2e9e6e")):
            G.append(dict(t="circle", cx=x, cy=y, r=14, fill=hex2rgb(c)+(1,), stroke=w, sw=3.5))
    return G

# ------------------------------------------------------------------ SVG
def f(c): return rgb2hex(c[:3])
def svg(name):
    els = scene(name)
    defs, body = [], []
    n = 0
    for e in els:
        n += 1
        fill = e.get("fill"); attrs = []
        extra = ""
        if e.get("shadow"):
            attrs.append('transform="translate(0 2.5)"')
        if e.get("clip"):
            _, ccx, ccy, cr = e["clip"]
            defs.append(f'<clipPath id="c{n}"><circle cx="{ccx}" cy="{ccy}" r="{cr}"/></clipPath>')
            attrs.append(f'clip-path="url(#c{n})"')
        if isinstance(fill, tuple) and fill and fill[0] == "lin":
            _, t, b, y0, y1 = fill
            defs.append(f'<linearGradient id="g{n}" gradientUnits="userSpaceOnUse" x1="0" y1="{y0}" x2="0" y2="{y1}">'
                        f'<stop offset="0" stop-color="{f(t)}" stop-opacity="{t[3]}"/>'
                        f'<stop offset="1" stop-color="{f(b)}" stop-opacity="{b[3]}"/></linearGradient>')
            fa = f'fill="url(#g{n})"'
        elif fill is None:
            fa = 'fill="none"'
        else:
            fa = f'fill="{f(fill)}"' + (f' fill-opacity="{fill[3]}"' if len(fill) > 3 and fill[3] < 1 else "")
        if e.get("shadow"):
            # sombra: mismo trazo en negro translucido
            if fill is not None and not (isinstance(fill, tuple) and fill[0] == "lin"):
                fa = 'fill="#000000" fill-opacity="0.22"'
            else:
                fa = 'fill="none"'
        st = e.get("stroke")
        sa = ""
        if st is not None:
            col = "#000000" if e.get("shadow") else f(st)
            op = 0.22 if e.get("shadow") else (st[3] if len(st) > 3 else 1)
            sa = f'stroke="{col}" stroke-opacity="{op}" stroke-width="{e["sw"]}" stroke-linecap="round" stroke-linejoin="round"'
        a = " ".join(attrs)
        t = e["t"]
        if t == "circle":
            body.append(f'<circle cx="{e["cx"]}" cy="{e["cy"]}" r="{e["r"]}" {fa} {sa} {a}/>')
        elif t == "ellipse":
            body.append(f'<ellipse cx="{e["cx"]}" cy="{e["cy"]}" rx="{e["rx"]}" ry="{e["ry"]}" {fa} {sa} {a}/>')
        elif t == "rrect":
            body.append(f'<rect x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" rx="{e["rx"]}" {fa} {sa} {a}/>')
        elif t == "poly":
            pts = " ".join(f"{x},{y}" for x, y in e["pts"])
            body.append(f'<polygon points="{pts}" {fa} {sa} {a}/>')
        elif t == "line":
            pts = " ".join(f"{x},{y}" for x, y in e["pts"])
            body.append(f'<polyline points="{pts}" fill="none" {sa} {a}/>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">\n'
            f'<defs>{"".join(defs)}</defs>\n' + "\n".join(body) + "\n</svg>\n")

# ------------------------------------------------------------------ vista previa (Pillow)
def preview(outfile):
    import numpy as np
    from PIL import Image, ImageDraw
    SS = 4
    def render(name, px):
        S = SIZE * SS
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        for e in scene(name):
            dy = 2.5 if e.get("shadow") else 0
            def mask_of(draw_fn):
                m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m); draw_fn(d); return m
            fill, st, t = e.get("fill"), e.get("stroke"), e["t"]
            def sh(v): return v * SS
            parts = []  # (mask, rgba-source)
            def shape_fill(d, **kw):
                if t == "circle":
                    d.ellipse([sh(e["cx"]-e["r"]), sh(e["cy"]+dy-e["r"]), sh(e["cx"]+e["r"]), sh(e["cy"]+dy+e["r"])], **kw)
                elif t == "ellipse":
                    d.ellipse([sh(e["cx"]-e["rx"]), sh(e["cy"]+dy-e["ry"]), sh(e["cx"]+e["rx"]), sh(e["cy"]+dy+e["ry"])], **kw)
                elif t == "rrect":
                    d.rounded_rectangle([sh(e["x"]), sh(e["y"]+dy), sh(e["x"]+e["w"]), sh(e["y"]+dy+e["h"])], radius=sh(e["rx"]), **kw)
                elif t == "poly":
                    d.polygon([(sh(x), sh(y+dy)) for x, y in e["pts"]], **kw)
            if fill is not None and t != "line":
                parts.append((mask_of(lambda d: shape_fill(d, fill=255)), fill, False))
            if st is not None:
                if t == "line":
                    def ln(d):
                        pts = [(sh(x), sh(y+dy)) for x, y in e["pts"]]
                        d.line(pts, fill=255, width=int(sh(e["sw"])), joint="curve")
                        r = sh(e["sw"]) / 2
                        for (x, y) in pts: d.ellipse([x-r, y-r, x+r, y+r], fill=255)
                    parts.append((mask_of(ln), st, True))
                else:
                    def ol(d): shape_fill(d, outline=255, width=int(sh(e["sw"])))
                    # contorno centrado sobre el borde de la figura
                    m = mask_of(lambda d: shape_fill(d, fill=255, outline=255, width=int(sh(e["sw"]))))
                    m_in = mask_of(lambda d: None)
                    parts.append((m_out_minus_in(e, shape_fill, mask_of, sh), st, True))
            for mask, col, is_stroke in parts:
                if e.get("clip"):
                    _, ccx, ccy, cr = e["clip"]
                    cm = mask_of(lambda d: d.ellipse([sh(ccx-cr), sh(ccy-cr), sh(ccx+cr), sh(ccy+cr)], fill=255))
                    mask = Image.fromarray((np.array(mask, float) * np.array(cm, float) / 255).astype("uint8"))
                layer = np.zeros((S, S, 4), float)
                if (not is_stroke) and isinstance(col, tuple) and col and col[0] == "lin":
                    _, c0, c1, y0, y1 = col
                    ys = (np.arange(S) / SS - y0) / (y1 - y0); ys = np.clip(ys, 0, 1)[:, None]
                    c0 = np.array([c0[0], c0[1], c0[2], c0[3]*255], float); c1 = np.array([c1[0], c1[1], c1[2], c1[3]*255], float)
                    grad = c0[None, None, :] * (1 - ys[..., None]) + c1[None, None, :] * ys[..., None]
                    layer[:] = np.broadcast_to(grad, (S, S, 4))
                else:
                    rgb = col[:3]; a = (col[3] if len(col) > 3 else 1)
                    layer[..., 0], layer[..., 1], layer[..., 2] = rgb
                    layer[..., 3] = a * 255
                if e.get("shadow"):
                    layer[..., 0:3] = 0; layer[..., 3] = 0.22 * 255
                layer[..., 3] *= np.array(mask, float) / 255
                img = Image.alpha_composite(img, Image.fromarray(layer.astype("uint8"), "RGBA"))
        return img.resize((px, px), Image.LANCZOS)
    names = list(BADGES)
    sheet = Image.new("RGBA", (len(names)*140+20, 128+20+48+40), (120, 80, 170, 255))
    for i, n in enumerate(names):
        sheet.alpha_composite(render(n, 128), (10+i*140, 10))
        sheet.alpha_composite(render(n, 48), (10+i*140+40, 150))
    sheet.save(outfile)

def m_out_minus_in(e, shape_fill, mask_of, sh):
    """Contorno de ancho sw centrado en el borde de la figura."""
    from PIL import Image, ImageChops, ImageDraw
    sw = sh(e["sw"]); 
    S = SIZE * 4
    t = e["t"]
    def grow(d, k):
        ee = dict(e)
        if t == "circle": ee["r"] = e["r"] + k
        elif t == "ellipse": ee["rx"] = e["rx"] + k; ee["ry"] = e["ry"] + k
        return ee
    def draw_with(ee):
        m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m)
        dy = 2.5 if e.get("shadow") else 0
        if t == "circle":
            d.ellipse([sh(ee["cx"]-ee["r"]), sh(ee["cy"]+dy-ee["r"]), sh(ee["cx"]+ee["r"]), sh(ee["cy"]+dy+ee["r"])], fill=255)
        elif t == "ellipse":
            d.ellipse([sh(ee["cx"]-ee["rx"]), sh(ee["cy"]+dy-ee["ry"]), sh(ee["cx"]+ee["rx"]), sh(ee["cy"]+dy+ee["ry"])], fill=255)
        elif t == "rrect":
            d.rounded_rectangle([sh(e["x"]-e["sw"]/2), sh(e["y"]+dy-e["sw"]/2), sh(e["x"]+e["w"]+e["sw"]/2), sh(e["y"]+dy+e["h"]+e["sw"]/2)], radius=sh(e["rx"]+e["sw"]/2), fill=255) if ee is e else None
        return m
    outer = draw_with(grow(e, e["sw"]/2)); inner = draw_with(grow(e, -e["sw"]/2))
    return ImageChops.subtract(outer, inner)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    prev = []
    for tema, carpeta in THEME_DIRS.items():
        use_theme(tema)
        if out:
            d = os.path.join(out, carpeta, "scalable", "apps"); os.makedirs(d, exist_ok=True)
            for name in BADGES:
                data = svg(name)
                for alias in ALIASES[name]:
                    with open(os.path.join(d, alias + ".svg"), "w") as fh: fh.write(data)
            inh = "WhiteSur,hicolor" if tema == "aurora" else "Ocelote,WhiteSur,hicolor"
            with open(os.path.join(out, carpeta, "index.theme"), "w") as fh:
                fh.write("[Icon Theme]\nName=%s\nComment=Iconos circulares de Ocelote OS (%s)\nInherits=%s\n"
                         "Directories=scalable/apps\n\n[scalable/apps]\nSize=128\nMinSize=8\nMaxSize=512\n"
                         "Type=Scalable\nContext=Applications\n" % (carpeta, tema, inh))
        try:
            f = "/tmp/ocelote-iconos-%s.png" % tema
            preview(f); prev.append(f)
        except ImportError:
            pass
    if out: print("temas de iconos escritos en", out)
    for f in prev: print("vista previa:", f)

if __name__ == "__main__":
    main()
