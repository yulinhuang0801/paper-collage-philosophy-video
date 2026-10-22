"""Sentence and subtitle-chunk splitting, for CJK and Latin scripts.

`kind` is "cjk" (Chinese) or "latin" (English and similar), set per language
in episode.json. Sentence durations are proportional to char_len, so the
same measure must be used everywhere timing is computed.
"""
import re


def char_len(s, kind):
    return len(s.replace(" ", "")) if kind == "cjk" else len(s)


def sentences(text, kind):
    if kind == "cjk":
        parts = re.findall(r"[^。！？]*[。！？]", text)
        rest = text[len("".join(parts)):]
        if rest.strip():
            parts.append(rest)
        return [p.strip() for p in parts if p.strip()]
    parts = re.split(r"(?<=[.!?])\s+|(?<=[.!?\"])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]


def chunks(sent, kind, max_chars):
    """Split a sentence into subtitle lines at clause boundaries."""
    if len(sent) <= max_chars:
        return [sent]
    if kind == "cjk":
        pieces = [p for p in re.findall(r"[^，、：；]*[，、：；]?", sent) if p]
        sep = ""
    else:
        pieces = re.split(r"(?<=,)\s+", sent)
        sep = " "
    out, cur = [], ""
    for p in pieces:
        if not cur or len(cur) + len(sep) + len(p) <= max_chars:
            cur = cur + sep + p if cur else p
        else:
            out.append(cur)
            cur = p
    if cur:
        out.append(cur)
    # a clause that is itself too long: hard-wrap (at a space for Latin)
    final = []
    for c in out:
        while len(c) > max_chars:
            cut = max_chars
            if kind != "cjk":
                sp = c.rfind(" ", 0, max_chars)
                cut = sp if sp >= 20 else max_chars
            final.append(c[:cut].strip())
            c = c[cut:].strip()
        if c:
            final.append(c)
    return final
