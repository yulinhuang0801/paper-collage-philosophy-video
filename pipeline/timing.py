"""Re-anchor every shot to the recorded narration of one language.

Segment starts follow the mix model (lead, gap, pauses, tail). Inside a
segment, sentences get time in proportion to their character counts, and
each shot spans the sentences episode.json assigns to it in that language.
Shots tile the picture timeline: the first starts at 0, each one ends where
the next begins, and a guard point that lands short of its hold pushes the
next shot later by the difference.
"""
import json
import os

from .text import char_len, chunks, sentences

SHORT_KINDS = ("transition", "introduction", "performance", "event", "motion", "loop")


class TimingError(Exception):
    pass


def segment_starts(speech, model):
    starts, t = [], model["lead"]
    for i, d in enumerate(speech, start=1):
        starts.append(t)
        t += d + model["gap"] + model.get("pause_after", {}).get(str(i), 0.0)
    total = starts[-1] + speech[-1] + model["tail"]
    return starts, total


def _per_lang(value, lang):
    return value.get(lang) if isinstance(value, dict) else value


def _staged(spec):
    return spec.get("t") == "sub" and len(spec.get("parts", [])) >= 2


class Narration:
    """Sentence-level timing of one language's recorded narration."""

    def __init__(self, ep, lang):
        L = ep.lang(lang)
        if not L.get("speech"):
            raise TimingError(f"{lang}: no measured speech durations; run `measure` first")
        self.kind = L["script"]
        self.speech = L["speech"]
        segs = ep.segments[lang]
        if len(segs) != len(self.speech):
            raise TimingError(f"{lang}: {len(segs)} segments but {len(self.speech)} durations")
        self.starts, total = segment_starts(self.speech, ep["timing"])
        self.total = L.get("total") or total
        self.sents, self.bounds = [], []
        for i, seg in enumerate(segs):
            ss = sentences(seg["audio"], self.kind)
            tot = sum(char_len(s, self.kind) for s in ss)
            acc, b = self.starts[i], []
            for s in ss:
                d = self.speech[i] * char_len(s, self.kind) / tot
                b.append((acc, acc + d))
                acc += d
            self.sents.append(ss)
            self.bounds.append(b)

    def phrase_time(self, phrase, segment=None):
        """Estimated time the narrator starts saying `phrase`."""
        segs = [segment - 1] if segment else range(len(self.sents))
        for si in segs:
            for j, s in enumerate(self.sents[si]):
                k = s.find(phrase)
                if k >= 0:
                    a, b = self.bounds[si][j]
                    frac = char_len(s[:k], self.kind) / char_len(s, self.kind)
                    return a + (b - a) * frac
        raise TimingError(f"phrase not found in narration: {phrase!r}")


def compute(ep, lang):
    nar = Narration(ep, lang)
    L = ep.lang(lang)
    rules = ep["timing"]
    max_s, min_s = rules.get("max_shot", 14.0), rules.get("min_shot", 6.0)

    # 1. anchors from sentences
    shots, covered = [], {}
    for sh in ep["shots"]:
        si = sh["segment"] - 1
        rng = _per_lang(sh["sentences"], lang)
        n = len(nar.sents[si])
        first, last = rng[0] % n, rng[-1] % n
        covered.setdefault(si, set()).update(range(first, last + 1))
        a, b = nar.bounds[si][first][0], nar.bounds[si][last][1]
        if sh.get("start_at"):
            a = nar.phrase_time(_per_lang(sh["start_at"], lang), sh["segment"])
        if sh.get("end_at"):
            b = nar.phrase_time(_per_lang(sh["end_at"], lang), sh["segment"])
        text = "；".join(nar.sents[si][k][:24] + "…" for k in range(first, min(last, first + 1) + 1))
        shots.append({"id": sh["id"], "anchor": [a, b], "text": text, "src": sh})
    for si, ss in enumerate(nar.sents):
        missing = sorted(set(range(len(ss))) - covered.get(si, set()))
        if missing:
            raise TimingError(f"{lang} S{si + 1}: sentences {missing} belong to no shot: "
                              + " / ".join(ss[k][:30] for k in missing))

    # 2. tile the picture timeline, honouring guard holds
    starts = [0.0] + [s["anchor"][0] for s in shots[1:]]
    for i, s in enumerate(shots):
        end = starts[i + 1] if i + 1 < len(shots) else nar.total
        hold = s["src"].get("hold")
        if hold and end - starts[i] < hold:
            if i + 1 == len(shots):
                raise TimingError(f"{s['id']}: final shot shorter than its {hold}s hold")
            s["extended"] = hold - (end - starts[i])
            starts[i + 1] += s["extended"]
    for i, s in enumerate(shots):
        s["start"] = starts[i]
        s["end"] = starts[i + 1] if i + 1 < len(shots) else nar.total
        s["dur"] = s["end"] - s["start"]
        if s["dur"] <= 0.5:
            raise TimingError(f"{lang} {s['id']}: {s['dur']:.2f}s, shots overlap")

    # 3. guardrails
    flags = []
    for s in shots:
        src, d = s["src"], s["dur"]
        if d > max_s:
            ok = _staged(src["spec"]) or src.get("staged")
            flags.append((s["id"], f"{d:.1f}s > {max_s:.0f}s",
                          "internal stages" if ok else None))
        elif d < min_s:
            short = src.get("short")
            if short and short.get("kind") in SHORT_KINDS:
                why = short["kind"] + ": " + (_per_lang(short.get("note", ""), lang) or "")
            elif s.get("extended") is not None or src.get("hold"):
                why = "guard point"
            else:
                why = None
            flags.append((s["id"], f"{d:.1f}s < {min_s:.0f}s", why))
        if s.get("extended"):
            flags.append((s["id"], f"guard hold {src['hold']}s",
                          f"held {s['extended']:.2f}s past its narration; next shot starts late"))

    shot_index = {s["id"]: s for s in shots}

    def at(anchor):
        if isinstance(anchor, (int, float)):
            return float(anchor)
        off = anchor.get("offset", 0.0)
        if "t" in anchor:
            return anchor["t"] + off
        if "total" in anchor:
            return nar.total + anchor["total"]
        if "shot" in anchor:
            s = shot_index[anchor["shot"]]
            return s["end" if anchor.get("at") == "end" else "start"] + off
        if "phrase" in anchor:
            return nar.phrase_time(anchor["phrase"]) + off
        raise TimingError(f"bad anchor {anchor}")

    overlays = []
    for o in L.get("overlays", []):
        r = dict(o, start=at(o["start"]), end=at(o["end"]))
        if r["end"] <= r["start"]:
            raise TimingError(f"{lang} overlay {o['id']}: ends before it starts")
        overlays.append(r)

    sub = L.get("subtitles", {})
    max_chars = sub.get("max_chars", 26 if nar.kind == "cjk" else 68)
    events = []
    for si, ss in enumerate(nar.sents):
        for s, (a, b) in zip(ss, nar.bounds[si]):
            cs = chunks(s, nar.kind, max_chars)
            tot = sum(len(c) for c in cs) or 1
            acc = a
            for c in cs:
                d = (b - a) * len(c) / tot
                events.append([round(acc, 3), round(acc + d, 3), c])
                acc += d

    return {
        "lang": lang,
        "total": nar.total,
        "segment_starts": nar.starts,
        "shots": [_shot_out(s) for s in shots],
        "flags": [{"shot": i, "issue": what, "resolution": why} for i, what, why in flags],
        "subtitles": events,
        "overlays": overlays,
    }


def _shot_out(s):
    out = {k: s[k] for k in ("id", "start", "end", "dur", "anchor", "text")}
    if s.get("extended"):
        out["extended"] = s["extended"]
    return out


def unresolved(timing):
    return [f for f in timing["flags"] if not f["resolution"]]


def fmt(x):
    return f"{int(x // 60)}:{x % 60:04.1f}"


def table_md(ep, timing):
    t = timing
    lines = [f"# {ep['title']}: {t['lang']} shot timing", "",
             f"Generated by `python3 -m pipeline timing`. Total {fmt(t['total'])}, "
             f"{len(t['shots'])} shots. Do not edit by hand; change episode.json and regenerate.", "",
             "| Shot | Start | End | Length | Narration anchor |", "|---|---|---|---|---|"]
    for s in t["shots"]:
        lines.append(f"| {s['id']} | {fmt(s['start'])} | {fmt(s['end'])} | {s['dur']:.1f}s | {s['text']} |")
    lines += ["", "## Guardrails", ""]
    if not t["flags"]:
        lines.append("- No shot outside the limits.")
    for f in t["flags"]:
        lines.append(f"- {f['shot']}: {f['issue']} → {f['resolution'] or '**UNRESOLVED**'}")
    lines += ["", "## Overlays", ""]
    for o in t["overlays"]:
        label = o.get("text") or o.get("image")
        lines.append(f"- {o['id']}: {fmt(o['start'])}–{fmt(o['end'])} {label}")
    return "\n".join(lines) + "\n"


def write(ep, timing):
    lang = timing["lang"]
    with open(os.path.join(ep.build_dir(lang), "timing.json"), "w", encoding="utf-8") as f:
        json.dump(timing, f, ensure_ascii=False, indent=1)
    md = os.path.join(ep.dir, f"timing-{lang}.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(table_md(ep, timing))
    return md
