#!/usr/bin/env python3
"""Chinese Room v3 build (shot mode), ZH first.
Visuals follow shots-zh-timing.md (39 shots). Audio is reused from the
delivered v2 cut (identical narration + BGM mix). Subtitles use the same
sentence timing as v2. Usage: python3 build_v3.py zh [--limit N]"""
import subprocess, sys, os, re, glob

ROOT = "/home/hatch/workspace/chinese-room-video"
V2F, V3F = f"{ROOT}/frames-v2", f"{ROOT}/frames-v3"
C2, C3 = f"{ROOT}/clips-v2", f"{ROOT}/clips-v3"
OUT = f"{ROOT}/build-v3"
W, H, FPS = 1152, 768, 30
TOTAL = 355.53
os.makedirs(OUT, exist_ok=True)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd)[:200])
        print(r.stderr[-2500:])
        sys.exit(1)

def font_path():
    hits = glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True)
    return hits[0] if hits else glob.glob("/usr/share/fonts/**/DejaVuSans*.ttf", recursive=True)[0]
FONT = font_path()

def crop_expr(box):
    if not box:
        return ""
    x, y, x2, y2 = box
    return f"crop=iw*{x2-x:.3f}:ih*{y2-y:.3f}:iw*{x:.3f}:ih*{y:.3f},"

def render_visual(spec, dur, out):
    """spec -> silent mp4 of exactly dur seconds."""
    t = spec["t"]
    if t == "clip":
        src = spec["src"]
        vf = crop_expr(spec.get("crop")) + f"scale={W}:{H},fps={FPS},format=yuv420p"
        if dur <= 10.2:
            run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf,
                 "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", out])
        elif dur <= 13.6:
            vf = crop_expr(spec.get("crop")) + \
                 f"setpts={dur/10.0:.4f}*PTS,scale={W}:{H},fps={FPS},format=yuv420p"
            run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf,
                 "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", out])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "1", "-i", src, "-vf", vf,
                 "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", out])
    elif t in ("still", "freeze", "pan", "vpan"):
        src = spec["src"]
        frames = max(1, int(round(dur * FPS)))
        pre = crop_expr(spec.get("crop"))
        if t == "freeze":
            vf = pre + f"scale={W*2}:{H*2},zoompan=z=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:fps={FPS}:s={W}x{H}"
        elif t == "pan":
            vf = pre + (f"scale={W*2}:{H*2},zoompan=z=1.10:"
                        f"x='(iw-iw/zoom)*on/{max(frames-1,1)}':y='ih/2-(ih/zoom/2)':d={frames}:fps={FPS}:s={W}x{H}")
        elif t == "vpan":
            # tall strip: scale to width W, then a window slides down the strip
            vf = pre + f"scale={W}:-2,crop={W}:{H}:0:'(ih-{H})*n/{max(frames-1,1)}',fps={FPS}"
            if spec.get("sat"):
                vf += f",eq=saturation={spec['sat']}"
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", src, "-vf", vf,
                 "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                 "-pix_fmt", "yuv420p", out])
            return
        else:
            z0, z1 = spec.get("z", (1.0, 1.05))
            vf = pre + (f"scale={W*2}:{H*2},zoompan=z='{z0}+({z1}-{z0})*on/{max(frames-1,1)}':"
                        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:fps={FPS}:s={W}x{H}")
        if spec.get("sat"):
            vf += f",eq=saturation={spec['sat']}"
        vf += ",format=yuv420p"
        # single-frame input: zoompan turns that one frame into `frames` outputs
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf,
             "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", out])
    else:
        raise ValueError(t)

PREFIX = "shot"  # set per language in main()

def render_shot(idx, spec, dur):
    out = f"{OUT}/{PREFIX}-{idx:02d}.mp4"
    if spec["t"] != "sub":
        render_visual(spec, dur, out)
        return out
    parts = spec["parts"]  # [(spec, weight)]
    xf = spec.get("xf", 0.3)
    n = len(parts)
    total_inner = dur + xf * (n - 1)
    files = []
    for j, (pspec, wgt) in enumerate(parts):
        pf = f"{OUT}/{PREFIX}-{idx:02d}-p{j}.mp4"
        render_visual(pspec, total_inner * wgt, pf)
        files.append(pf)
    if n == 2 and xf <= 0.08:  # near-hard cut: plain concat of the two parts
        lst = f"{OUT}/{PREFIX}-{idx:02d}.txt"
        open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", out])
        return out
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for f in files:
        cmd += ["-i", f]
    fc, prev, acc = [], "[0:v]", files and 0
    durs = [total_inner * w for _, w in parts]
    acc = durs[0]
    for k in range(1, n):
        lbl = f"[x{k}]"
        fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={xf}:offset={acc - xf:.3f}{lbl}")
        prev = lbl
        acc += durs[k] - xf
    fc.append(f"{prev}format=yuv420p[v]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", out]
    run(cmd)
    return out

def S(t, src, **kw):
    d = {"t": t, "src": src}
    d.update(kw)
    return d

K1, K2, K4, K5, K6, K7, K8, K9, K10, K11 = (f"{V2F}/K{n}.png" for n in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11))
FIG = (0.28, 0.22, 0.62, 0.75)       # person inside K2
BOOK = (0.46, 0.34, 0.86, 0.86)      # giant book in K2
SLOT = (0.74, 0.26, 1.0, 0.76)       # slot in K2
HANDS = (0.33, 0.40, 0.60, 0.70)     # hands/slips in K2

SHOTS = [  # (id, start, spec); end = next start (last ends at TOTAL)
    ("1A", 0.0, S("clip", f"{C3}/1A.mp4")),
    ("1B", 6.7, S("still", f"{V3F}/1B.png", z=(1.0, 1.07))),
    ("1C", 11.5, S("clip", f"{C3}/1C.mp4")),
    ("2A", 24.2, S("sub", "", parts=[(S("still", K1, z=(1.0, 1.03)), .52),
                                     (S("still", K2, z=(1.0, 1.04)), .48)], xf=.5)),
    ("2B", 26.7, S("still", K2, crop=SLOT, z=(1.0, 1.10))),
    ("2C", 32.4, S("sub", "", parts=[(S("still", f"{V3F}/2C-1.png", z=(1.0, 1.05)), .34),
                                     (S("still", f"{V3F}/2C-2.png", z=(1.0, 1.05)), .33),
                                     (S("still", f"{V3F}/2C-3.png", z=(1.0, 1.03)), .33)], xf=.3)),
    ("2D", 40.9, S("sub", "", parts=[(S("still", K2, z=(1.0, 1.05)), .24),
                                     (S("still", K2, crop=BOOK, z=(1.0, 1.06)), .38),
                                     (S("still", K2, crop=SLOT, z=(1.0, 1.04)), .095),
                                     (S("still", K2, crop=HANDS, z=(1.0, 1.04)), .095),
                                     (S("still", K2, crop=SLOT, z=(1.0, 1.04)), .095),
                                     (S("still", K2, crop=HANDS, z=(1.0, 1.04)), .095)], xf=.25)),
    ("3A", 64.4, S("sub", "", parts=[(S("still", K10, z=(1.0, 1.05)), .5),
                                     (S("clip", f"{C2}/K2.mp4"), .5)], xf=.35)),
    ("3B", 72.9, S("sub", "", parts=[(S("still", K10, crop=(0.03, 0.18, 0.97, 0.85), z=(1.0, 1.04)), .5),
                                     (S("still", K2, crop=BOOK, z=(1.0, 1.04)), .5)], xf=.06)),
    ("3C-1", 79.6, S("still", K10, crop=(0.03, 0.15, 0.97, 0.88), z=(1.0, 1.06))),
    ("3C-2", 87.8, S("sub", "", parts=[(S("still", K2, z=(1.0, 1.05)), .42),
                                       (S("still", K2, crop=FIG, z=(1.0, 1.05)), .58)], xf=.4)),
    ("4A", 97.4, S("clip", f"{C3}/K12.mp4")),
    ("4B", 101.8, S("sub", "", parts=[(S("still", K2, z=(1.0, 1.05)), .34),
                                      (S("clip", f"{C2}/K4.mp4"), .36),
                                      (S("still", K4, crop=(0.55, 0.15, 0.97, 0.75), z=(1.0, 1.05)), .30)], xf=.35)),
    ("4C", 116.4, S("still", f"{V3F}/4C.png", z=(1.0, 1.04))),
    ("4D", 124.2, S("sub", "", parts=[(S("clip", f"{C3}/4D.mp4"), .71),
                                       (S("still", f"{V3F}/4D.png", z=(1.0, 1.05)), .29)], xf=.3)),
    ("4E", 138.3, S("sub", "", parts=[(S("still", f"{V3F}/4D.png", z=(1.0, 1.04)), .45),
                                      (S("still", f"{V3F}/4E-blend.png", z=(1.0, 1.04)), .55)], xf=1.2)),
    ("5A", 144.6, S("clip", f"{C3}/5A.mp4")),
    ("5B", 150.5, S("vpan", K5, crop=(0.005, 0.01, 0.245, 0.99))),
    ("5C", 157.8, S("vpan", K5, crop=(0.255, 0.01, 0.495, 0.99))),
    ("5D1", 169.1, S("sub", "", parts=[(S("still", f"{V3F}/5D1.png", z=(1.0, 1.03)), .17),
                                        (S("still", f"{V3F}/5D1.png", crop=(0.02, 0.05, 0.28, 0.42), z=(1.0, 1.05)), .19),
                                        (S("still", f"{V3F}/5D1.png", crop=(0.71, 0.04, 0.96, 0.44), z=(1.0, 1.05)), .19),
                                        (S("still", f"{V3F}/5D1.png", crop=(0.02, 0.57, 0.27, 0.96), z=(1.0, 1.05)), .19),
                                        (S("still", f"{V3F}/5D1.png", crop=(0.75, 0.61, 0.98, 0.95), z=(1.0, 1.05)), .19),
                                        (S("still", f"{V3F}/5D1.png", z=(1.0, 1.02)), .07)], xf=.35)),
    ("5D2", 186.7, S("vpan", K5, crop=(0.755, 0.01, 0.995, 0.99), sat=0.55)),
    ("5E", 199.9, S("still", K1, crop=(0.24, 0.06, 0.82, 0.86), z=(1.0, 1.045))),
    ("6A", 210.6, S("sub", "", parts=[(S("still", K2, crop=FIG, z=(1.0, 1.03)), .45),
                                      (S("still", K2, z=(1.0, 1.03)), .55)], xf=.4)),
    ("6B", 218.3, S("sub", "", parts=[(S("still", K6, z=(1.0, 1.04)), .20),
                                      (S("still", K6, crop=(0.30, 0.20, 0.80, 0.85), z=(1.0, 1.04)), .27),
                                      (S("still", K6, crop=(0.02, 0.10, 0.45, 0.70), z=(1.0, 1.04)), .27),
                                      (S("still", K6, z=(1.0, 1.03)), .26)], xf=.3)),
    ("6C-1", 233.0, S("clip", f"{C3}/K11.mp4", crop=(0.22, 0.12, 0.78, 0.88))),
    ("6C-2", 243.7, S("sub", "", parts=[(S("still", K11, crop=(0.32, 0.25, 0.68, 0.75), z=(1.0, 1.03)), .4),
                                        (S("still", K11, z=(1.0, 1.03)), .6)], xf=.4)),
    ("6D", 252.3, S("clip", f"{C2}/K6.mp4")),
    ("7A-1", 259.8, S("still", K7, z=(1.0, 1.06))),
    ("7A-2", 265.0, S("freeze", K7)),
    ("7B", 269.1, S("clip", f"{C3}/7B.mp4")),
    ("7C", 274.4, S("still", f"{V3F}/7C.png", z=(1.0, 1.02))),
    ("8A", 282.4, S("clip", f"{C2}/K8.mp4")),
    ("8B", 286.1, S("sub", "", parts=[(S("still", K8, z=(1.0, 1.04)), .25),
                                      (S("still", K8, crop=(0.05, 0.35, 0.50, 0.90), z=(1.0, 1.04)), .25),
                                      (S("still", K8, crop=(0.45, 0.05, 0.95, 0.55), z=(1.0, 1.04)), .25),
                                      (S("still", K8, z=(1.0, 1.03)), .25)], xf=.3)),
    ("8C", 297.1, S("pan", f"{V3F}/8C.png")),
    ("8D1", 309.1, S("still", f"{V3F}/8D1.png", z=(1.0, 1.03))),
    ("8D2", 316.5, S("still", f"{V3F}/8D2bg.png", z=(1.0, 1.02))),
    ("9A", 327.6, S("clip", f"{C3}/9A.mp4")),
    ("9B", 335.3, S("clip", f"{C3}/9B-v2.mp4")),
    ("9C", 344.2, S("still", K9, z=(1.0, 1.06))),
]
K7 = f"{V2F}/K7.png"
K9 = f"{V2F}/K9.png"

# ---------- subtitles (same timing model as v2) ----------
sys.path.insert(0, ROOT)
from segments_v2 import SEGMENTS
SPEECH = [23.5, 39.7, 32.5, 46.8, 62.0, 48.8, 22.2, 44.7, 26.4]
GAP, EXTRA, LEAD = 0.45, 3.5, 0.3
SPEECH_EN = [22.77, 44.97, 29.46, 50.97, 64.58, 53.53, 24.55, 36.93, 26.01]
SPEECH_BY_LANG = {"zh": SPEECH, "en": SPEECH_EN}
# EN shot starts, same shot order as SHOTS (see shots-en-timing.md)
EN_STARTS = [0.30, 6.40, 11.68, 23.52, 26.37, 33.43, 42.06, 68.94, 76.51, 83.55,
             88.10, 98.85, 102.99, 118.87, 128.58, 141.88, 150.27, 156.49, 167.11,
             179.11, 196.83, 208.95, 218.80, 226.71, 242.96, 252.69, 262.98, 272.78,
             279.36, 284.46, 289.80, 297.78, 300.91, 309.07, 317.84, 325.51, 335.16,
             341.25, 350.56]
TOTALS = {"zh": TOTAL, "en": 362.47}

def sents_of(text):
    parts = re.findall(r"[^。！？]*[。！？]", text)
    rest = text[len("".join(parts)):]
    if rest.strip():
        parts.append(rest)
    return [p.strip() for p in parts if p.strip()]

def chunks_of(sent):
    if len(sent) <= 24:
        return [sent]
    raw = re.findall(r"[^，、：；]*[，、：；]?", sent)
    out, cur = [], ""
    for r in raw:
        if not r:
            continue
        if len(cur) + len(r) <= 26:
            cur += r
        else:
            if cur:
                out.append(cur)
            cur = r
    if cur:
        out.append(cur)
    return out

def sents_of_en(text):
    parts = re.split(r"(?<=[.!?])\s+|(?<=[.!?\"])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]

def chunks_of_en(sent):
    if len(sent) <= 68:
        return [sent]
    raw = re.split(r"(?<=,)\s+", sent)
    out, cur = [], ""
    for r in raw:
        if len(cur) + len(r) + 1 <= 68:
            cur = (cur + " " + r).strip() if cur else r
        else:
            if cur:
                out.append(cur)
            cur = r
    if cur:
        out.append(cur)
    final = []
    for c in out:
        while len(c) > 68:
            cut = c.rfind(" ", 0, 68)
            if cut < 20:
                cut = 68
            final.append(c[:cut])
            c = c[cut:].strip()
        if c:
            final.append(c)
    return final

def subtitle_events(lang="zh"):
    speech = SPEECH_BY_LANG[lang]
    evs, t = [], LEAD
    starts = []
    for i, d in enumerate(speech):
        starts.append(t)
        t += d + GAP + (EXTRA if i == 4 else 0)
    for i, seg in enumerate(SEGMENTS[lang]):
        if lang == "zh":
            ss = sents_of(seg["audio"])
            tot = sum(len(s.replace(" ", "")) for s in ss)
            acc = starts[i]
            for s in ss:
                sdur = speech[i] * len(s.replace(" ", "")) / tot
                chs = chunks_of(s)
                ctot = sum(len(c) for c in chs) or 1
                cacc = acc
                for c in chs:
                    cd = sdur * len(c) / ctot
                    evs.append((cacc, cacc + cd, c))
                    cacc += cd
                acc += sdur
        else:
            ss = sents_of_en(seg["audio"])
            tot = sum(len(s) for s in ss) or 1
            acc = starts[i]
            for s in ss:
                sdur = speech[i] * len(s) / tot
                chs = chunks_of_en(s)
                ctot = sum(len(c) for c in chs) or 1
                cacc = acc
                for c in chs:
                    cd = sdur * len(c) / ctot
                    evs.append((cacc, cacc + cd, c))
                    cacc += cd
                acc += sdur
    return evs

def textfile(name, text):
    p = f"{OUT}/txt-{name}.txt"
    open(p, "w").write(text)
    return p

def dt(name, text, size, x, y, a, b, color="white", box=True):
    tf = textfile(name, text)
    bx = ":box=1:boxcolor=black@0.42:boxborderw=12" if box else ""
    return (f"drawtext=fontfile={FONT}:textfile={tf}:fontsize={size}:fontcolor={color}"
            f":borderw=2:bordercolor=black{bx}:x={x}:y={y}:enable='between(t,{a},{b})'")

def main():
    global PREFIX
    lang = "en" if "en" in sys.argv[1:3] else "zh"
    PREFIX = f"{lang}-shot"
    total = TOTALS[lang]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    silent = f"{OUT}/silent-{lang}.mp4"
    if lang == "zh" and os.path.exists(f"{OUT}/silent.mp4") and "--final-only" in sys.argv:
        silent = f"{OUT}/silent.mp4"  # reuse the verified ZH silent from the first build
    if "--final-only" not in sys.argv:
        if lang == "zh":
            shot_list = SHOTS
        else:
            shot_list = [(sid, EN_STARTS[i], spec) for i, (sid, _st, spec) in enumerate(SHOTS)]
        files = []
        for i, (sid, start, spec) in enumerate(shot_list):
            if limit and i >= limit:
                break
            end = shot_list[i + 1][1] if i + 1 < len(shot_list) else total
            dur = end - start
            print(f"[{sid}] {start:.1f}-{end:.1f} ({dur:.1f}s)", flush=True)
            files.append(render_shot(i, spec, dur))
        lst = f"{OUT}/concat-{lang}.txt"
        open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", silent])
        if limit:
            print("LIMIT build done:", silent)
            return
    # ---- final overlay pass ----
    filters = []
    for j, (a, b, txt) in enumerate(subtitle_events(lang)):
        filters.append(dt(f"{lang}sub{j}", txt, 30, "(w-text_w)/2", "h-64", f"{a:.2f}", f"{b:.2f}", box=False))
    if lang == "zh":
        filters.append(dt("title1", "中文房间", 66, "(w-text_w)/2", "228", "0.2", "4.2"))
        filters.append(dt("title2", "当 AI 给出完美回答时，它真的懂吗？", 30, "(w-text_w)/2", "326", "0.2", "4.2"))
        filters.append(dt("y1980", "1980", 46, "56", "48", "97.9", "101.6", color="white"))
        filters.append(dt("door1", "机器永远不会懂", 34, "320-text_w/2", "58", "309.6", "316.5"))
        filters.append(dt("door2", "AI 已经懂了", 34, "832-text_w/2", "58", "309.6", "316.5"))
        filters.append(dt("d2a", "说出对的词", 54, "170", "322", "317.6", "327.6"))
        filters.append(dt("d2b", "知道意思", 54, "700", "322", "321.8", "327.6"))
        filters.append(dt("q9a", "当 AI 给出一个完美的回答，它是理解了，还是只是在遵守规则？", 36,
                          "(w-text_w)/2", "88", "328.6", "335.3"))
        filters.append(dt("end", "当 AI 给出一个完美的回答，它是理解了，还是只是在遵守规则？", 40,
                          "(w-text_w)/2", "322", "350.03", "355.53"))
        qw1, qw2 = (144.6, 150.5), (199.9, 210.6)
    else:
        filters.append(dt("entitle1", "The Chinese Room", 66, "(w-text_w)/2", "228", "0.2", "4.2"))
        filters.append(dt("entitle2", "Could a Machine Understand You?", 30, "(w-text_w)/2", "326", "0.2", "4.2"))
        filters.append(dt("eny1980", "1980", 46, "56", "48", "99.3", "102.9", color="white"))
        filters.append(dt("endoor1", "Machines never understand", 30, "320-text_w/2", "58", "318.3", "325.5"))
        filters.append(dt("endoor2", "AI already understands", 30, "832-text_w/2", "58", "318.3", "325.5"))
        filters.append(dt("end2a", "Saying the right words", 40, "(576-text_w)/2", "322", "326.2", "334.7"))
        filters.append(dt("end2b", "Knowing what they mean", 40, "576+(576-text_w)/2", "322", "332.0", "334.7"))
        filters.append(dt("enq9a1", "When AI gives a perfect answer,", 36, "(w-text_w)/2", "84", "336.2", "341.25"))
        filters.append(dt("enq9a2", "is it understanding, or only following rules?", 36, "(w-text_w)/2", "130", "336.2", "341.25"))
        filters.append(dt("enend1", "When AI gives a perfect answer,", 40, "(w-text_w)/2", "296", "356.97", "362.32"))
        filters.append(dt("enend2", "is it understanding, or only following rules?", 40, "(w-text_w)/2", "348", "356.97", "362.32"))
        qw1, qw2 = (150.27, 156.49), (208.95, 218.80)
    fc = ",".join(filters)
    out_path = f"{ROOT}/chinese-room-v3-{lang}.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", f"{OUT}/audio-{lang}.m4a",
           "-loop", "1", "-i", f"{V3F}/qmark.png",
           "-filter_complex",
           f"[0:v]{fc}[base];[2:v]format=rgba,scale=104:-1[q];[q]split=2[q1][q2];"
           f"[base][q1]overlay=x=748:y='84+6*sin(2*PI*t/3.1)':enable='between(t,{qw1[0]},{qw1[1]})'[b1];"
           f"[b1][q2]overlay=x=748:y='84+6*sin(2*PI*t/3.1)':enable='between(t,{qw2[0]},{qw2[1]})'[vout]",
           "-map", "[vout]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-c:a", "copy", "-shortest", out_path]
    run(cmd)
    print("DONE", out_path)

if __name__ == "__main__":
    main()
