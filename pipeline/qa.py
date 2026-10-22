"""Render checks: text that would leave the frame, file integrity, sample frames."""
import os
import subprocess

from .common import probe, run

BOX_PAD, BORDER, MARGIN = 12, 2, 8


def _measure(font_path):
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    cache = {}

    def width(text, size):
        if size not in cache:
            cache[size] = ImageFont.truetype(font_path, size)
        return cache[size].getlength(text)
    return width


def check_text_fit(ep, lang, timing, font_path):
    """Return a problem line for every overlay or subtitle that leaves its room or covers another."""
    width = _measure(font_path)
    if width is None:
        print("note: Pillow not installed, skipping the text-fit check (pip install pillow)")
        return []
    W, _H, _ = ep.canvas
    problems, boxes = [], []
    for o in timing["overlays"]:
        if not o.get("text"):
            continue
        pad = BORDER + (BOX_PAD if o.get("box", True) else 0)
        w = width(o["text"], o["size"]) + 2 * pad
        x = o["x"]
        if x == "center":
            lo, hi = (W - w) / 2, (W + w) / 2
        elif x in ("left-half", "right-half"):
            half = W / 2
            base = 0 if x == "left-half" else half
            lo, hi = base + (half - w) / 2, base + (half + w) / 2
            if w > half:
                problems.append(f"{lang} {o['id']}: {w:.0f}px wide, more than its half frame ({half:.0f}px)")
                continue
        elif isinstance(x, dict):
            lo, hi = x["center_at"] - w / 2, x["center_at"] + w / 2
        else:
            lo, hi = float(x) - pad, float(x) + w - pad
        if lo < MARGIN or hi > W - MARGIN:
            problems.append(f"{lang} {o['id']}: spans x {lo:.0f}..{hi:.0f}, frame is 0..{W}  ({o['text']!r})")
        top = float(o["y"]) - pad
        boxes.append((o, lo, hi, top, top + o["size"] * 1.2 + 2 * pad))
    # boxes on screen at the same time must not overlap (the 42% backgrounds stack into a dark band)
    for i, (a, al, ah, at, ab) in enumerate(boxes):
        for b, bl, bh, bt, bb in boxes[i + 1:]:
            if (a["start"] < b["end"] and b["start"] < a["end"]
                    and al < bh and bl < ah and at < bb and bt < ab):
                problems.append(f"{lang} {a['id']} and {b['id']} overlap on screen; move one by "
                                f"{min(ab - bt, bb - at):.0f}px")
    size = ep.lang(lang).get("subtitles", {}).get("size", 30)
    for a, _b, t in timing["subtitles"]:
        w = width(t, size) + 2 * BORDER
        if w > W - 2 * MARGIN:
            problems.append(f"{lang} subtitle at {a:.1f}s is {w:.0f}px wide: {t!r}")
    return problems


def verify(ep, lang, timing, path, frames=True):
    """Check streams, size and length, decode the tail, pull review frames."""
    W, H, _ = ep.canvas
    report = []
    d, streams = probe(path, strict=False)
    if d is None:
        return [("readable", False, "ffmpeg cannot open it: a truncated write (missing moov atom), not a finished render")], []
    kinds = [k for k, _ in streams]
    report.append(("streams", kinds.count("video") == 1 and kinds.count("audio") == 1, ", ".join(kinds)))
    size = next((sz for k, sz in streams if k == "video"), None)
    if size:
        report.append(("size", size == (str(W), str(H)), "x".join(size)))
    report.append(("length", abs(d - timing["total"]) < 0.2, f"{d:.2f}s, expected {timing['total']:.2f}s"))
    # A truncated write (e.g. a missing moov atom) fails here even when the header still reads.
    tail = subprocess.run(
        ["ffmpeg", "-v", "error", "-sseof", "-3", "-i", path, "-f", "null", "-"],
        capture_output=True, text=True)
    report.append(("tail decodes", tail.returncode == 0 and not tail.stderr.strip(),
                   tail.stderr.strip()[:200] or "clean"))
    shots_out = []
    if frames:
        qdir = os.path.join(ep.build_dir(lang), "qa")
        os.makedirs(qdir, exist_ok=True)
        moments = [(f"overlay-{o['id']}", (o["start"] + o["end"]) / 2) for o in timing["overlays"]]
        moments += [(f"shot-{s['id']}", (s["start"] + s["end"]) / 2) for s in timing["shots"][::4]]
        for name, t in moments:
            out = os.path.join(qdir, f"{t:06.1f}-{name}.jpg")
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-q:v", "3", out])
            shots_out.append(out)
    return report, shots_out
