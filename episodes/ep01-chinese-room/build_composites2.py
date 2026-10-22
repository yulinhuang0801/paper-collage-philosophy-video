#!/usr/bin/env python3
"""Second batch of v3 assets: 4C split still, 2C degradation states,
question-mark overlay PNG, 8D2 background, 4E blend still."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from pipeline.common import find_font  # noqa: E402

# media folder: argv[1], else $EPISODE_MEDIA, else ./media next to this script
MEDIA = (sys.argv[1] if len(sys.argv) > 1 else
         os.environ.get("EPISODE_MEDIA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")))
V2 = os.path.join(MEDIA, "frames-v2")
V3 = os.path.join(MEDIA, "frames-v3")
W, H = 1152, 768
INK = (18, 20, 18)
CREAM = (243, 238, 222)

def load(p):
    return Image.open(p).convert("RGB")

def cover(img, box, tw, th):
    w, h = img.size
    x0, y0, x1, y1 = int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)
    c = img.crop((x0, y0, x1, y1))
    s = max(tw / c.width, th / c.height)
    c = c.resize((int(c.width*s)+1, int(c.height*s)+1))
    x = (c.width - tw)//2; y = (c.height - th)//2
    return c.crop((x, y, x+tw, y+th))

def font(sz):
    return ImageFont.truetype(find_font(), sz)

K2, K5, K10, K11 = (load(f"{V2}/K{n}.png") for n in (2, 5, 10, 11))
F4D = load(f"{V3}/4D.png")

# ---------- 4C: left pipeline stack, right giant question mark
img = Image.new("RGB", (W, H), INK)
left_bg = cover(K11, (0.05, 0.3, 0.55, 0.95), W//2, H)
img.paste(left_bg, (0, 0))
right_bg = cover(K10, (0.02, 0.02, 0.22, 0.30), W//2, H)  # plain cream corner of K10
img.paste(right_bg, (W//2, 0))
d = ImageDraw.Draw(img)
slip = cover(K2, (0.78, 0.30, 1.0, 0.72), 300, 150)
book = cover(K2, (0.50, 0.36, 0.82, 0.82), 300, 150)
thumbs = [slip, book, slip]
ys = [70, 309, 548]
for t, y in zip(thumbs, ys):
    d.rectangle([128, y-8, 448, y+158], fill=INK)
    img.paste(t, (136, y))
d = ImageDraw.Draw(img)
for ay in (252, 491):
    d.polygon([(278, ay), (306, ay), (288, ay+34)], fill=CREAM)
    d.rectangle([284, ay-16, 292, ay+2], fill=CREAM)
d.text((W//2 + W//4, H//2), "?", font=font(430), fill=(30, 34, 40), anchor="mm")
d.rectangle([W//2-3, 0, W//2+3, H], fill=INK)
img.save(f"{V3}/4C.png")

# ---------- 2C states: glyphs -> broken strokes -> pure shapes
base = cover(K2, (0.33, 0.38, 0.62, 0.70), W, H)
base.save(f"{V3}/2C-1.png")
small = base.resize((W//7, H//7), Image.BILINEAR).resize((W, H), Image.NEAREST)
small = small.quantize(colors=10).convert("RGB")
small.save(f"{V3}/2C-2.png")
random.seed(2)
paper = Image.new("RGB", (W, H), (226, 216, 188))
tex = cover(K2, (0.02, 0.78, 0.30, 0.98), W, H).convert("L")
paper = Image.blend(paper, Image.merge("RGB", (tex, tex, tex)), 0.10)
d = ImageDraw.Draw(paper)
for _ in range(46):
    x, y = random.randint(90, W-170), random.randint(70, H-140)
    s = random.randint(22, 54)
    k = random.randint(0, 4)
    if k == 0:
        d.rectangle([x, y, x+s, y+s*0.7], outline=INK, width=6)
    elif k == 1:
        d.line([x, y, x+s, y], fill=INK, width=6)
        d.line([x, y+14, x+s*0.7, y+14], fill=INK, width=6)
    elif k == 2:
        d.ellipse([x, y, x+15, y+15], fill=INK)
    elif k == 3:
        d.polygon([(x, y+s*0.6), (x+s*0.5, y), (x+s, y+s*0.6)], outline=INK, width=6)
    else:
        d.line([x, y, x+s*0.6, y+s*0.6], fill=INK, width=6)
paper.save(f"{V3}/2C-3.png")

# ---------- question mark overlay (transparent)
q = Image.new("RGBA", (150, 190), (0, 0, 0, 0))
dq = ImageDraw.Draw(q)
dq.text((75, 88), "?", font=font(160), fill=(246, 242, 226, 255), anchor="mm",
        stroke_width=7, stroke_fill=(15, 17, 15, 255))
q.save(f"{V3}/qmark.png")

# ---------- 8D2 background: deep blue calm texture
bg = cover(K11, (0.1, 0.1, 0.9, 0.9), W, H).filter(ImageFilter.GaussianBlur(16))
ov = Image.new("RGB", (W, H), (8, 17, 36))
bg = Image.blend(bg, ov, 0.52)
bg.save(f"{V3}/8D2bg.png")

# ---------- 4E blend: user still with the room ghosting in
k2r = K2.resize((W, H))
f4r = F4D.resize((W, H))
Image.blend(f4r, k2r, 0.38).save(f"{V3}/4E-blend.png")
print("batch2 done: 4C 2C-1/2/3 qmark 8D2bg 4E-blend")
