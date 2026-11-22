#!/usr/bin/env python3
"""Genera los fondos de pantalla de Ocelote OS (diseno propio).
Uso: python3 tools/mkwallpapers.py <carpeta_de_salida>"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1200
PALETAS = {
    "aurora":  dict(top=(14,8,44),  mid=(70,28,120), bot=(20,40,110),
                    glows=[(.72,.35,420,(150,80,220),.55),(.25,.70,520,(60,90,230),.45),(.5,.15,380,(200,120,255),.25)],
                    cintas=[(190,150,255),(130,170,255),(230,170,255),(110,140,255)]),
    "aqua":    dict(top=(6,20,48),  mid=(14,80,140), bot=(8,50,110),
                    glows=[(.72,.35,420,(80,200,255),.50),(.25,.70,520,(40,120,230),.45),(.5,.15,380,(150,230,255),.25)],
                    cintas=[(150,220,255),(120,190,255),(190,240,255),(100,170,240)]),
    "grafito": dict(top=(18,18,22), mid=(58,60,70), bot=(30,32,40),
                    glows=[(.72,.35,420,(160,165,180),.40),(.25,.70,520,(110,115,130),.40),(.5,.15,380,(200,205,215),.22)],
                    cintas=[(200,205,215),(150,155,170),(230,232,240),(120,125,140)]),
    "jade":    dict(top=(4,28,26),  mid=(14,96,82), bot=(8,60,70),
                    glows=[(.72,.35,420,(70,220,170),.50),(.25,.70,520,(60,160,200),.42),(.5,.15,380,(140,240,200),.25)],
                    cintas=[(150,240,200),(110,210,190),(190,250,220),(90,190,170)]),
}

def generar(p, semilla=7):
    rng = np.random.default_rng(semilla)
    img = np.zeros((H, W, 3), float)
    top, mid, bot = (np.array(p[k]) for k in ("top", "mid", "bot"))
    for i in range(H):
        f = i / (H - 1)
        img[i, :, :] = top + (mid - top) * (f / 0.55) if f < 0.55 else mid + (bot - mid) * ((f - 0.55) / 0.45)
    yy, xx = np.mgrid[0:H, 0:W]
    for gx, gy, r, col, a in p["glows"]:
        d = ((xx - W * gx) ** 2 + (yy - H * gy) ** 2) / (r * r)
        img += np.exp(-d)[..., None] * np.array(col)[None, None, :] * a
    base = Image.fromarray(np.clip(img, 0, 255).astype("uint8"))
    layer = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(layer)
    xs = np.arange(0, W, 4)
    for k, (amp, ph, off, col) in enumerate(zip((120, 90, 150, 70), (0.0, 1.2, 2.1, 3.0), (.62, .68, .58, .72), p["cintas"])):
        for j in range(7):
            pts = [(int(x), int(H*off + amp*np.sin(x/W*2*np.pi*1.1 + ph + j*0.18) + j*9 + 40*np.sin(x/W*2*np.pi*2.3 + k))) for x in xs]
            a = 0.5 - j * 0.06
            d.line(pts, fill=tuple(int(c * a) for c in col), width=2)
    soft = layer.filter(ImageFilter.GaussianBlur(6)); sharp = layer.filter(ImageFilter.GaussianBlur(1.2))
    out = np.clip(np.array(base, float) + np.array(soft, float) * 1.1 + np.array(sharp, float) * 0.6, 0, 255)
    for _ in range(500):
        sx, sy = rng.integers(0, W), rng.integers(0, int(H * 0.7)); b = rng.integers(120, 255)
        out[sy, sx, :] = np.maximum(out[sy, sx, :], b)
        if rng.random() < 0.15 and 1 < sx < W-2 and 1 < sy < H-2:
            out[sy, sx-1:sx+2, :] = np.maximum(out[sy, sx-1:sx+2, :], b*0.6)
            out[sy-1:sy+2, sx, :] = np.maximum(out[sy-1:sy+2, sx, :], b*0.6)
    return Image.fromarray(np.clip(out, 0, 255).astype("uint8"))

if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(dest, exist_ok=True)
    for nombre, pal in PALETAS.items():
        im = generar(pal)
        if nombre == "aurora":
            im.save(os.path.join(dest, "aurora.png"), optimize=True)
        else:
            im.save(os.path.join(dest, nombre + ".jpg"), quality=90, optimize=True)
        print("fondo", nombre)
