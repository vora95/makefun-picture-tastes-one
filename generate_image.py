#!/usr/bin/env python3
"""Generate entry.png: one ripe strawberry, hero shot.

One ingredient only: a single glossy strawberry (whole) + one halved
strawberry showing its juicy flesh, on a dark warm slate with soft light.
Drawn procedurally with PIL + numpy — no photos, no network, no stock.
Output: 1024x1024 PNG, < 1 MiB.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2048  # supersample, downscaled to 1024 at the end
rng = random.Random(20261122)
np_rng = np.random.default_rng(20261122)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vertical_gradient(size, top, bottom):
    w, h = size
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top_a = np.array(top, dtype=np.float32)
    bot_a = np.array(bottom, dtype=np.float32)
    arr = top_a + (bot_a - top_a) * t
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def radial_glow(size, center, radius, color, peak):
    """Soft radial glow, returns RGBA overlay."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * peak
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def bez(p0, p1, p2, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


# ---------- canvas: warm dark background + glow ----------
img = vertical_gradient((S, S), (26, 14, 10), (52, 28, 16)).convert("RGBA")
img.alpha_composite(radial_glow((S, S), (S // 2, 820), 1150, (150, 84, 36), 0.55))
img.alpha_composite(radial_glow((S, S), (S // 2, 820), 520, (255, 170, 90), 0.28))

# ---------- table surface ----------
surf = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(surf)
sd.rectangle([0, 1560, S, S], fill=(38, 22, 13, 255))
sd.rectangle([0, 1560, S, 1572], fill=(120, 70, 36, 160))
img.alpha_composite(surf)
img.alpha_composite(radial_glow((S, S), (S // 2, 1700), 900, (120, 66, 30), 0.35))

# soft shadows are drawn later, just before the halved berry (see below),
# so no shadow can show through a rotated shape

# ---------- strawberry body ----------
cx, top_y, rx, ry = 1024, 520, 585, 800
tip = (cx, top_y + ry + 60)
# outline: top ellipse arc + two quadratic sides to the tip
outline = []
for i in range(61):
    th = math.pi + i * math.pi / 60  # left -> right over the top
    outline.append((cx + rx * math.cos(th), top_y + 300 * math.sin(th)))
outline += bez((cx + rx, top_y), (cx + rx * 0.98, top_y + 620), tip, 60)[1:]
outline += bez(tip, (cx - rx * 0.98, top_y + 620), (cx - rx, top_y), 60)[1:]

mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
md.polygon(outline, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(2))

# flesh: per-pixel gradient, light from top-left
yy, xx = np.mgrid[0:S, 0:S]
nx = (xx - cx) / rx
ny = (yy - top_y) / ry
light = np.clip(0.72 - 0.55 * nx - 0.45 * ny + 0.18 * np_rng.random((S, S)), 0, 1)
deep = np.array([122, 8, 18], dtype=np.float32)
mid = np.array([214, 28, 38], dtype=np.float32)
bright = np.array([255, 88, 66], dtype=np.float32)
t = np.clip(light, 0, 1)
col = np.where((t < 0.5)[..., None], deep + (mid - deep) * (t * 2)[..., None],
               mid + (bright - mid) * ((t - 0.5) * 2)[..., None])
# subtle vertical streaks
streak = (np.sin(xx * 0.02 + np.sin(yy * 0.008) * 2.0) * 0.5 + 0.5) * 10
col = np.clip(col + streak[..., None], 0, 255)
flesh = Image.fromarray(col.astype(np.uint8), "RGB").convert("RGBA")
img.paste(flesh, (0, 0), mask)

# soft sheen top-left + rim light right edge
sheen = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sh = ImageDraw.Draw(sheen)
sh.ellipse([560, 560, 1080, 1080], fill=(255, 190, 160, 90))
sh.ellipse([640, 620, 1000, 980], fill=(255, 220, 200, 70))
sheen = sheen.filter(ImageFilter.GaussianBlur(90))
tmp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
tmp.paste(sheen, (0, 0), mask)
img.alpha_composite(tmp)

rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rd = ImageDraw.Draw(rim)
rd.line(outline, fill=(255, 140, 110, 130), width=14)
rim = rim.filter(ImageFilter.GaussianBlur(10))
tmp2 = Image.new("RGBA", (S, S), (0, 0, 0, 0))
tmp2.paste(rim, (0, 0), mask)
img.alpha_composite(tmp2)

# ---------- seeds (achenes), in rows following the taper ----------
seeds = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd2 = ImageDraw.Draw(seeds)
row_y = top_y + 150
row = 0
while row_y < top_y + ry - 40:
    frac = (row_y - top_y) / ry
    half_w = rx * (1 - frac ** 1.7) ** 0.6 * 0.92
    n = max(3, int(half_w / 105))
    offset = (row % 2) * (half_w / n)
    for i in range(n):
        x = cx - half_w + offset + (2 * half_w / n) * i + rng.uniform(-14, 14)
        y = row_y + rng.uniform(-10, 10)
        if abs(x - cx) > half_w - 30:
            continue
        tilt = math.degrees(math.atan2(x - cx, 420)) * 0.6
        sd2.ellipse([x - 13, y - 20, x + 13, y + 20], fill=(150, 20, 26, 130))
        sd2.ellipse([x - 16, y - 24, x + 10, y + 16], fill=(255, 232, 160, 235))
        sd2.ellipse([x - 9, y - 16, x + 3, y + 2], fill=(255, 248, 205, 255))
    row_y += 118
    row += 1
tmp3 = Image.new("RGBA", (S, S), (0, 0, 0, 0))
tmp3.paste(seeds, (0, 0), mask)
img.alpha_composite(tmp3)

# ---------- water droplets on the berry ----------
drops = Image.new("RGBA", (S, S), (0, 0, 0, 0))
dd = ImageDraw.Draw(drops)
for _ in range(34):
    x = rng.uniform(cx - 430, cx + 430)
    y = rng.uniform(top_y + 180, top_y + ry - 60)
    frac = (y - top_y) / ry
    half_w = rx * (1 - frac ** 1.7) ** 0.6 * 0.9
    if abs(x - cx) > half_w - 60:
        continue
    r = rng.uniform(9, 26)
    dd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 55))
    dd.ellipse([x - r * 0.45, y - r * 0.55, x + r * 0.1, y - r * 0.05],
               fill=(255, 255, 255, 200))
tmp4 = Image.new("RGBA", (S, S), (0, 0, 0, 0))
tmp4.paste(drops, (0, 0), mask)
img.alpha_composite(tmp4)

# ---------- calyx leaves + stem ----------
leaves = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ld = ImageDraw.Draw(leaves)
leaf_angles = [-78, -42, -8, 26, 62, 88]
for ang in leaf_angles:
    a = math.radians(ang - 90)
    base = (cx + rng.uniform(-30, 30), top_y + 30)
    length = rng.uniform(300, 430)
    tipx = base[0] + math.cos(a) * length
    tipy = base[1] + math.sin(a) * length
    perp = (math.cos(a + math.pi / 2), math.sin(a + math.pi / 2))
    wdt = rng.uniform(85, 115)
    midx = base[0] + math.cos(a) * length * 0.55 + perp[0] * wdt * 0.35
    midy = base[1] + math.sin(a) * length * 0.55 + perp[1] * wdt * 0.35
    mid2x = base[0] + math.cos(a) * length * 0.55 - perp[0] * wdt * 0.35
    mid2y = base[1] + math.sin(a) * length * 0.55 - perp[1] * wdt * 0.35
    ld.polygon([base, (midx, midy), (tipx, tipy), (mid2x, mid2y)],
               fill=(46, 122, 58, 255), outline=(24, 80, 34, 255))
    ld.line([base, (tipx, tipy)], fill=(140, 200, 110, 160), width=7)
# stem
ld.polygon([(cx - 26, top_y - 150), (cx + 26, top_y - 150),
            (cx + 14, top_y + 40), (cx - 14, top_y + 40)], fill=(96, 74, 40, 255))
img.alpha_composite(leaves)

# ---------- soft shadows on the table, under the berries ----------
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
shd = ImageDraw.Draw(shadow)
shd.ellipse([680, 1400, 1380, 1500], fill=(0, 0, 0, 110))
shd.ellipse([1240, 1790, 1820, 1910], fill=(0, 0, 0, 110))
shadow = shadow.filter(ImageFilter.GaussianBlur(40))
img.alpha_composite(shadow)

# ---------- halved strawberry, bottom-right: juicy cross-section ----------
hx, hy, hrx, hry = 1520, 1620, 300, 235
half = Image.new("RGBA", (S, S), (0, 0, 0, 0))
hd = ImageDraw.Draw(half)
hd.ellipse([hx - hrx, hy - hry, hx + hrx, hy + hry], fill=(226, 42, 54, 255))
hd.ellipse([hx - hrx + 26, hy - hry + 22, hx + hrx - 26, hy + hry - 22],
           fill=(255, 150, 150, 255))
hd.ellipse([hx - hrx + 70, hy - hry + 60, hx + hrx - 70, hy + hry - 60],
           fill=(255, 205, 200, 255))
# white core star
core = []
for i in range(10):
    ang = math.pi / 2 + i * math.pi / 5
    r = 95 if i % 2 == 0 else 38
    core.append((hx + r * math.cos(ang), hy + r * math.sin(ang) * 0.8))
hd.polygon(core, fill=(255, 244, 238, 255))
# juice vesicles: tiny dots radiating
for i in range(90):
    ang = rng.uniform(0, 2 * math.pi)
    rr = rng.uniform(120, 240)
    x = hx + rr * math.cos(ang)
    y = hy + rr * math.sin(ang) * 0.78
    r = rng.uniform(4, 9)
    hd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 120, 120, 200))
# seeds on the rim
for i in range(16):
    ang = i * 2 * math.pi / 16 + 0.2
    x = hx + (hrx - 8) * math.cos(ang)
    y = hy + (hry - 8) * math.sin(ang)
    hd.ellipse([x - 11, y - 15, x + 11, y + 15], fill=(255, 232, 160, 255))
# gloss highlight on the cut (separate overlay: ImageDraw on RGBA replaces
# pixels instead of blending, so a low-alpha fill would punch a hole)
gloss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(gloss)
gd.ellipse([hx - 180, hy - 170, hx + 40, hy - 40], fill=(255, 255, 255, 70))
gloss = gloss.filter(ImageFilter.GaussianBlur(12))
half.alpha_composite(gloss)
half = half.filter(ImageFilter.GaussianBlur(1))
img.alpha_composite(half)

# ---------- vignette + fine grain ----------
vig = radial_glow((S, S), (S // 2, S // 2), 1500, (0, 0, 0), 0.0)
img = img.convert("RGB")
arr = np.asarray(img).astype(np.float32)
yy2, xx2 = np.mgrid[0:S, 0:S]
d = np.sqrt((xx2 - S / 2) ** 2 + (yy2 - S / 2) ** 2) / (S * 0.72)
arr *= np.clip(1 - 0.22 * np.clip(d - 0.55, 0, 1) ** 2, 0.78, 1)[..., None]
arr += np_rng.normal(0, 3.0, arr.shape)
img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

# ---------- text: name the one ingredient ----------
img = img.resize((1024, 1024), Image.LANCZOS)
d = ImageDraw.Draw(img, "RGBA")
try:
    f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
    f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 27)
except OSError:
    f_big = ImageFont.load_default()
    f_small = ImageFont.load_default()
label = "S T R A W B E R R Y"
sub = "one ingredient — nothing else"
for f, txt, y in ((f_big, label, 908), (f_small, sub, 968)):
    bb = d.textbbox((0, 0), txt, font=f)
    w = bb[2] - bb[0]
    d.text(((1024 - w) / 2 + 2, y + 2), txt, font=f, fill=(0, 0, 0, 140))
    d.text(((1024 - w) / 2, y), txt, font=f, fill=(245, 230, 200, 255))
d.line([312, 896, 712, 896], fill=(245, 230, 200, 180), width=2)

img.save(OUT, "JPEG", quality=90, optimize=True)  # JPEG bytes, name stays entry.png (gate reads magic bytes)
print("saved", OUT, os.path.getsize(OUT), "bytes")
