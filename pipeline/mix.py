"""Narration files: export the TTS text, measure the recordings, mix with music."""
import os
import sys

from .common import duration, need, run
from .timing import segment_starts


def narration_files(ep, lang):
    pattern = ep["mix"]["narration"]
    return [ep.media_path(pattern.format(lang=lang, n=n))
            for n in range(1, len(ep.segments[lang]) + 1)]


def tts_text(ep, lang):
    """One .txt per segment, the exact text the TTS should read."""
    out = []
    for path, seg in zip(narration_files(ep, lang), ep.segments[lang]):
        txt = os.path.splitext(path)[0] + ".txt"
        os.makedirs(os.path.dirname(txt), exist_ok=True)
        with open(txt, "w", encoding="utf-8") as f:
            f.write(seg["audio"] + "\n")
        out.append(txt)
    return out


def measure(ep, lang):
    """Store each recorded segment's length in episode.json (languages.<lang>.speech)."""
    files = narration_files(ep, lang)
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        sys.exit(f"{lang}: missing narration:\n  " + "\n  ".join(missing))
    speech = [round(duration(f), 2) for f in files]
    L = ep.lang(lang)
    L["speech"] = speech
    L.pop("total", None)  # a pinned total belonged to the old recording
    ep.save()
    return speech


def mix(ep, lang):
    """Place each segment at its start and lay the music under it at a fixed ratio."""
    need("ffmpeg")
    m = ep["mix"]
    files = narration_files(ep, lang)
    speech = ep.lang(lang).get("speech") or sys.exit(f"{lang}: run `measure` first")
    starts, total = segment_starts(speech, ep["timing"])
    music = ep.media_path(m["music"])
    if not os.path.exists(music):
        sys.exit(f"missing music: {music}")
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for f in files:
        cmd += ["-i", f]
    cmd += ["-stream_loop", "-1", "-i", music]
    n = len(files)
    fc = [f"[{i}:a]aresample=48000,adelay={int(s * 1000)}:all=1[n{i}]" for i, s in enumerate(starts)]
    fc.append(f"[{n}:a]aresample=48000,volume={m.get('music_ratio', 0.16)},"
              f"afade=t=out:st={max(total - 2.5, 0):.2f}:d=2.5[bg]")
    fc.append("".join(f"[n{i}]" for i in range(n)) + f"[bg]amix=inputs={n + 1}:normalize=0:duration=longest[a]")
    out = os.path.join(ep.build_dir(lang), "mix.m4a")
    run(cmd + ["-filter_complex", ";".join(fc), "-map", "[a]", "-t", f"{total:.3f}",
               "-c:a", "aac", "-b:a", "192k", out])
    return out, total
