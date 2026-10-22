"""Render one language version from episode.json and the computed timing.

Pass 1 renders every shot to a silent clip of its exact length and joins
them into build/<lang>/silent.mp4. Pass 2 lays every text overlay, the
subtitles and image overlays on top and muxes the audio. When pass 2 fails,
rerun with --final-only to reuse the silent file.
"""
import math
import os
import shutil
import sys

from . import qa
from .common import duration, find_font, need, run
from .timing import fmt

X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p"]


class Renderer:
    def __init__(self, ep, out_dir):
        self.ep = ep
        self.W, self.H, self.FPS = ep.canvas
        self.out_dir = out_dir
        self._dur = {}

    def crop(self, box):
        if not box:
            return ""
        if isinstance(box, str):
            box = self.ep["crops"][box]
        x, y, x2, y2 = box
        return f"crop=iw*{x2 - x:.3f}:ih*{y2 - y:.3f}:iw*{x:.3f}:ih*{y:.3f},"

    def clip_len(self, src):
        if src not in self._dur:
            self._dur[src] = duration(src)
        return self._dur[src]

    def visual(self, spec, dur, out):
        """spec -> silent mp4 of exactly dur seconds."""
        W, H, FPS = self.W, self.H, self.FPS
        t, src = spec["t"], self.ep.media_path(spec["src"])
        pre = self.crop(spec.get("crop"))
        sat = f",eq=saturation={spec['sat']}" if spec.get("sat") else ""
        if t == "clip":
            # Fit any source length: trim, slow down up to 36%, else loop.
            D = self.clip_len(src)
            inp = ["-i", src]
            speed = ""
            if dur > D + 0.05:
                if dur <= D * 1.36:
                    speed = f"setpts={dur / D:.4f}*PTS,"
                else:
                    inp = ["-stream_loop", str(math.ceil(dur / D) - 1), "-i", src]
            vf = pre + speed + f"scale={W}:{H},fps={FPS}{sat},format=yuv420p"
            run(["ffmpeg", "-y", "-v", "error"] + inp + ["-vf", vf, "-t", f"{dur:.3f}"] + X264 + [out])
            return
        frames = max(1, int(round(dur * FPS)))
        last = max(frames - 1, 1)
        if t == "vpan":
            # tall strip: scale to width W, then a window slides down the strip
            vf = pre + f"scale={W}:-2,crop={W}:{H}:0:'(ih-{H})*n/{last}',fps={FPS}{sat}"
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", src, "-vf", vf,
                 "-t", f"{dur:.3f}"] + X264 + [out])
            return
        centre = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        if t == "freeze":
            zp = f"z=1:{centre}"
        elif t == "pan":
            z = spec.get("zoom", 1.10)
            zp = f"z={z}:x='(iw-iw/zoom)*on/{last}':y='ih/2-(ih/zoom/2)'"
        elif t == "still":
            z0, z1 = spec.get("z", (1.0, 1.05))
            zp = f"z='{z0}+({z1}-{z0})*on/{last}':{centre}"
        else:
            sys.exit(f"unknown shot type {t!r} (clip, still, freeze, pan, vpan, sub)")
        # single-frame input: zoompan turns that one frame into `frames` outputs
        vf = pre + f"scale={W * 2}:{H * 2},zoompan={zp}:d={frames}:fps={FPS}:s={W}x{H}{sat},format=yuv420p"
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-t", f"{dur:.3f}"] + X264 + [out])

    def shot(self, idx, sid, spec, dur):
        out = os.path.join(self.out_dir, f"shot-{idx:02d}-{sid}.mp4")
        if spec["t"] != "sub":
            self.visual(spec, dur, out)
            return out
        parts = spec["parts"]  # [[spec, weight], ...], weights sum to 1
        xf = spec.get("xf", 0.3)
        n = len(parts)
        inner = dur + xf * (n - 1)
        durs = [inner * w for _, w in parts]
        files = []
        for j, (pspec, _w) in enumerate(parts):
            pf = os.path.join(self.out_dir, f"shot-{idx:02d}-{sid}-p{j}.mp4")
            self.visual(pspec, durs[j], pf)
            files.append(pf)
        if n == 2 and xf <= 0.08:  # near-hard cut: plain concat of the two parts
            lst = out + ".txt"
            with open(lst, "w") as f:
                f.write("".join(f"file '{p}'\n" for p in files))
            run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                 "-t", f"{dur:.3f}"] + X264 + [out])
            return out
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for p in files:
            cmd += ["-i", p]
        fc, prev, acc = [], "[0:v]", durs[0]
        for k in range(1, n):
            fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={xf}:offset={acc - xf:.3f}[x{k}]")
            prev = f"[x{k}]"
            acc += durs[k] - xf
        fc.append(f"{prev}format=yuv420p[v]")
        run(cmd + ["-filter_complex", ";".join(fc), "-map", "[v]", "-t", f"{dur:.3f}"] + X264 + [out])
        return out


def x_expr(x, W):
    if x == "center":
        return "(w-text_w)/2"
    if x == "left-half":
        return f"({W // 2}-text_w)/2"
    if x == "right-half":
        return f"{W // 2}+({W // 2}-text_w)/2"
    if isinstance(x, dict) and "center_at" in x:
        return f"{x['center_at']}-text_w/2"
    return str(x)


def media_needed(ep, lang):
    paths = set()

    def walk(spec):
        if spec.get("t") == "sub":
            for p, _w in spec["parts"]:
                walk(p)
        elif spec.get("src"):
            paths.add(spec["src"])
    for sh in ep["shots"]:
        walk(sh["spec"])
    for o in ep.lang(lang).get("overlays", []):
        if o.get("image"):
            paths.add(o["image"])
    return sorted(paths)


def audio_for(ep, lang):
    mixed = os.path.join(ep.build_dir(lang), "mix.m4a")
    if os.path.exists(mixed):
        return mixed
    given = ep.lang(lang).get("audio")
    return ep.media_path(given) if given else None


def build(ep, lang, timing, font=None, limit=None, final_only=False, force=False):
    need("ffmpeg")
    W, H, _ = ep.canvas
    bdir = ep.build_dir(lang)
    font = find_font(font)

    missing = [p for p in media_needed(ep, lang) if not os.path.exists(ep.media_path(p))]
    audio = audio_for(ep, lang)
    if not audio or not os.path.exists(audio):
        missing.append(audio or f"(no audio: run `mix`, or set languages.{lang}.audio)")
    if missing:
        sys.exit(f"{lang}: {len(missing)} media file(s) missing under {ep.media}:\n  "
                 + "\n  ".join(missing))
    problems = qa.check_text_fit(ep, lang, timing, font)
    if problems and not force:
        sys.exit("Overlay text would leave the frame (fix episode.json or pass --force):\n  "
                 + "\n  ".join(problems))

    silent = os.path.join(bdir, "silent.mp4")
    if not final_only or not os.path.exists(silent):
        shots_dir = os.path.join(bdir, "shots")
        os.makedirs(shots_dir, exist_ok=True)
        r = Renderer(ep, shots_dir)
        specs = {s["id"]: s["spec"] for s in ep["shots"]}
        files = []
        for i, s in enumerate(timing["shots"]):
            if limit and i >= limit:
                break
            print(f"[{lang} {s['id']}] {fmt(s['start'])}-{fmt(s['end'])} ({s['dur']:.1f}s)", flush=True)
            files.append(r.shot(i, s["id"], specs[s["id"]], s["dur"]))
        lst = os.path.join(bdir, "concat.txt")
        with open(lst, "w") as f:
            f.write("".join(f"file '{p}'\n" for p in files))
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst] + X264 + [silent])
        if limit:
            print("partial silent build:", silent)
            return silent

    # ---- overlay pass: run inside bdir so every filter path is short and plain ----
    txt = os.path.join(bdir, "txt")
    shutil.rmtree(txt, ignore_errors=True)
    os.makedirs(txt)
    font_link = os.path.join(bdir, "font" + os.path.splitext(font)[1])
    if os.path.lexists(font_link):
        os.remove(font_link)
    os.symlink(font, font_link)
    fname = os.path.basename(font_link)

    def dt(name, text, size, x, y, a, b, color="white", box=True):
        with open(os.path.join(txt, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
        bx = ":box=1:boxcolor=black@0.42:boxborderw=12" if box else ""
        return (f"drawtext=fontfile={fname}:textfile=txt/{name}.txt:fontsize={size}:fontcolor={color}"
                f":borderw=2:bordercolor=black{bx}:x={x_expr(x, W)}:y={y}:enable='between(t,{a:.2f},{b:.2f})'")

    L = ep.lang(lang)
    sub = L.get("subtitles", {})
    filters = [dt(f"sub{j:03d}", t, sub.get("size", 30), "center", f"h-{sub.get('bottom', 64)}", a, b, box=False)
               for j, (a, b, t) in enumerate(timing["subtitles"])]
    images = []
    for o in timing["overlays"]:
        if o.get("image"):
            images.append(o)
        else:
            filters.append(dt(o["id"], o["text"], o["size"], o["x"], o["y"], o["start"], o["end"],
                              color=o.get("color", "white"), box=o.get("box", True)))
    graph = f"[0:v]{','.join(filters)}[v0]"
    inputs = ["-i", silent, "-i", audio]
    for k, o in enumerate(images):
        inputs += ["-loop", "1", "-i", ep.media_path(o["image"])]
        amp, period = o.get("bob", (0, 1))
        y = f"{o['y']}+{amp}*sin(2*PI*t/{period})" if amp else str(o["y"])
        graph += (f";[{k + 2}:v]format=rgba,scale={o['width']}:-1[i{k}]"
                  f";[v{k}][i{k}]overlay=x={o['x']}:y='{y}':enable='between(t,{o['start']:.2f},{o['end']:.2f})'"
                  f":shortest=1[v{k + 1}]")
    with open(os.path.join(bdir, "overlay.filter"), "w", encoding="utf-8") as f:
        f.write(graph)  # kept for debugging a failed pass
    out = os.path.join(ep.build, f"{os.path.basename(ep.dir)}-{lang}.mp4")
    run(["ffmpeg", "-y", "-v", "error"] + inputs +
        ["-filter_complex", graph, "-map", f"[v{len(images)}]", "-map", "1:a"] + X264 +
        ["-c:a", "aac", "-b:a", "192k", "-t", f"{timing['total']:.3f}", out], cwd=bdir)
    print("built", out)
    return out
