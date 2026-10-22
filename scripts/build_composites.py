#!/usr/bin/env python3
"""Build the 4 collage-based v3 frames (7C, 8C, 8D1, 9B) from existing art.
New-drawn area stays under 40%: panels/figures are crops of K-frames;
only beams, doors, dividers and bubbles are drawn."""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import glob

V2 = "/home/hatch/workspace/chinese-room-video/frames-v2"
V3 = "/home/hatch/workspace/chinese-room-video/frames-v3"
W, H = 1152, 768
INK = (18, 20, 18)

def load(p):
    return Image.open(p).convert("RGB")

def cover(img, box, tw, th):
    """Crop box (relative) from img and resize to cover tw x th."""
    w, h = img.size
    x0, y0, x1, y1 = int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)
    c = img.crop((x0, y0, x1, y1))
    s = max(tw / c.width, th / c.height)
    c = c.resize((int(c.width*s)+1, int(c.height*s)+1))
    x = (c.width - tw)//2; y = (c.height - th)//2
    return c.crop((x, y, x+tw, y+th))

def tint(img, color, alpha):
    ov = Image.new("RGB", img.size, color)
    return Image.blend(img, ov, alpha)

def paste_framed(base, img, xy, border=7):
    x, y = xy
    d = ImageDraw.Draw(base)
    d.rectangle([x-border, y-border, x+img.width+border, y+img.height+border], fill=INK)
    base.paste(img, (x, y))

def font(sz):
    for pat in ("/usr/share/fonts/**/NotoSansCJK*.ttc", "/usr/share/fonts/**/NotoSans*.ttf",
                "/usr/share/fonts/**/DejaVuSans*.ttf"):
        hits = glob.glob(pat, recursive=True)
        if hits:
            try:
                return ImageFont.truetype(hits[0], sz)
            except Exception:
                pass
    return ImageFont.load_default()

K2, K6, K7, K8, K9, K11, K12 = (load(f"{V2}/K{n}.png") for n in (2, 6, 7, 8, 9, 11, 12))

# ---------- 8C: split screen, human inside (warm) vs machine geometry (cold)
left = cover(K12, (0.16, 0.04, 0.60, 0.66), W//2, H)
left = tint(ImageEnhance.Color(left).enhance(1.08), (255, 176, 92), 0.13)
right = cover(K6, (0.30, 0.18, 0.86, 0.86), W//2, H)
right = tint(ImageEnhance.Color(right).enhance(1.05), (64, 110, 200), 0.13)
img8c = Image.new("RGB", (W, H))
img8c.paste(left, (0, 0)); img8c.paste(right, (W//2, 0))
d = ImageDraw.Draw(img8c)
d.rectangle([W//2-2, 0, W//2+2, H], fill=INK)
d.rectangle([0, 0, W-1, H-1], outline=INK, width=10)
img8c.save(f"{V3}/8C.png")

# ---------- 7C: balance — K6 network pan vs K7 halo figure pan
bg = cover(K11, (0.05, 0.05, 0.95, 0.95), W, H)
bg = tint(bg, (10, 16, 30), 0.22)
tex = tint(cover(K8, (0.1, 0.1, 0.9, 0.9), W, H), (4, 8, 16), 0.52)
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
cx = W//2
md.polygon([(cx-26, 150), (cx+26, 150), (cx+13, 660), (cx-13, 660)], fill=255)      # post
md.polygon([(120, 128), (1032, 104), (1032, 142), (120, 166)], fill=255)              # beam (slight tilt)
md.polygon([(cx-95, 660), (cx+95, 660), (cx+130, 692), (cx-130, 692)], fill=255)     # base
md.ellipse([cx-24, 96, cx+24, 144], fill=255)                                        # pivot knob
bg.paste(tex, (0, 0), mask)
d = ImageDraw.Draw(bg)
for x, ytop in ((215, 152), (937, 128)):                                             # strings
    d.line([x, ytop, x-78, 300], fill=INK, width=6)
    d.line([x, ytop, x+78, 300], fill=INK, width=6)
panL = cover(K6, (0.28, 0.16, 0.88, 0.88), 300, 200)
panR = cover(K7, (0.30, 0.05, 0.72, 0.60), 300, 200)
paste_framed(bg, panL, (62, 302))
paste_framed(bg, panR, (790, 302))
d.arc([52, 470, 382, 560], 0, 180, fill=INK, width=8)                                # pan dishes
d.arc([780, 470, 1110, 560], 0, 180, fill=INK, width=8)
bg.save(f"{V3}/7C.png")

# ---------- 8D1: two doors on a patchwork wall tiled from K8/K11 sky pieces
# (no source frame has a large clean wall; tiling small sky crops guarantees
# a face-free paper-patchwork wall. S8 palette is deep blue, so doors are blue.)
import random
random.seed(8)
sky_srcs = [cover(K8, b, 220, 220) for b in
            ((0.0, 0.0, 0.35, 0.22), (0.35, 0.0, 0.7, 0.22), (0.65, 0.0, 1.0, 0.28),
             (0.1, 0.02, 0.45, 0.26), (0.5, 0.0, 0.85, 0.2))] + \
           [cover(K11, b, 220, 220) for b in
            ((0.0, 0.0, 0.2, 0.2), (0.8, 0.0, 1.0, 0.2), (0.0, 0.8, 0.2, 1.0))]
def mosaic(tw, th, tile, dark=0.0):
    m = Image.new("RGB", (tw, th), INK)
    for yy in range(0, th, tile):
        for xx in range(0, tw, tile):
            t = random.choice(sky_srcs).resize((tile, tile))
            if dark:
                t = tint(t, (5, 10, 24), dark)
            m.paste(t, (xx, yy))
    dm = ImageDraw.Draw(m)
    for xx in range(0, tw + 1, tile):
        dm.line([xx, 0, xx, th], fill=INK, width=5)
    for yy in range(0, th + 1, tile):
        dm.line([0, yy, tw, yy], fill=INK, width=5)
    return m
bg = mosaic(W, H, 192)
door_tex = mosaic(340, 540, 170, dark=0.30)
for x in (150, 662):
    paste_framed(bg, door_tex, (x, 130), border=9)
d = ImageDraw.Draw(bg)
for x in (150, 662):                                                                 # inner door panel
    d.rectangle([x+34, 170, x+306, 630], outline=INK, width=6)
for x in (150, 662):                                                                 # light slit + knob
    d.rectangle([x+318, 150, x+326, 650], fill=(250, 240, 200))
    d.ellipse([x+282, 420, x+302, 440], fill=(240, 230, 190), outline=INK, width=4)
f = font(120)
d.text((W//2, 84), "?", font=f, fill=(245, 240, 215), anchor="mm",
       stroke_width=3, stroke_fill=INK)
bg.save(f"{V3}/8D1.png")

# ---------- 9B: K9 face + two thought bubbles (network / pipeline)
img9b = K9.resize((W, H))
d = ImageDraw.Draw(img9b)
def bubble(cx, cy, w, h):
    x0, y0, x1, y1 = cx-w//2, cy-h//2, cx+w//2, cy+h//2
    d.rounded_rectangle([x0, y0, x1, y1], radius=46, fill=(246, 242, 228), outline=INK, width=7)
    d.polygon([(cx-16, y1-6), (cx+22, y1-6), (cx+2, y1+44)], fill=(246, 242, 228), outline=INK, width=6)
    d.rectangle([cx-20, y1-12, cx+26, y1+2], fill=(246, 242, 228))
    return (x0+16, y0+16, x1-16, y1-16)
b1 = bubble(238, 148, 380, 216)
net = cover(K6, (0.30, 0.18, 0.86, 0.86), b1[2]-b1[0], b1[3]-b1[1])
img9b.paste(net, (b1[0], b1[1]))
b2 = bubble(914, 148, 380, 216)
slip = cover(K2, (0.78, 0.30, 1.0, 0.72), 100, 150)
book = cover(K2, (0.52, 0.38, 0.80, 0.80), 100, 150)
bx = b2[0] + 12
for i, t in enumerate((slip, book, slip)):
    img9b.paste(t, (bx + i*118, b2[1] + 18))
d = ImageDraw.Draw(img9b)
for ax in (bx+104, bx+222):
    d.polygon([(ax, 138), (ax+16, 148), (ax, 158)], fill=INK)
img9b.save(f"{V3}/9B.png")
print("composites done: 7C 8C 8D1 9B")
