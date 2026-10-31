"""Narration with VoxCPM2: delivery direction (tone, pauses, stress) -> one file per segment.

The direction lives in <episode>/voice.json. VoxCPM2 has no SSML, so:
  - tone is a natural-language style prefix, "(calm, unhurried)text", per chunk
  - pauses are real silence inserted between chunks, not punctuation tricks
  - stress is a style hint ("stress the word ...") plus the wording itself;
    the model follows it only some of the time, so listen and re-take
A segment is cut into chunks wherever the tone changes or a line has its own
pause, and every chunk is cloned from the same reference clip so the voice
stays one voice. Needs the voxcpm package (Python 3.10-3.12) and its weights.
"""
import json
import os
import subprocess
import sys

from .mix import narration_files
from .text import sentences

TRIM_DB = -45  # level below which leading/trailing audio counts as silence


def load_direction(ep):
    path = os.path.join(ep.dir, "voice.json")
    if not os.path.exists(path):
        sys.exit(f"no {path}: write the voice direction first (see episodes/ep01-chinese-room/voice.json)")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_model(cfg):
    try:
        from voxcpm import VoxCPM
    except ImportError:
        sys.exit("voice needs the voxcpm package: pip install voxcpm soundfile (Python 3.10-3.12)")
    return VoxCPM.from_pretrained(cfg.get("model", "openbmb/VoxCPM2"), load_denoiser=False)


def sep(kind):
    return "，" if kind == "cjk" else ", "


def plan(text, kind, seg_dir, defaults):
    """Sentences -> chunks of (text, tone, pause_after)."""
    lines = seg_dir.get("lines", [])
    chunks = []
    for s in sentences(text, kind):
        line = next((ln for ln in lines if s.startswith(ln["match"])), {})
        tone = line.get("tone", seg_dir.get("tone", ""))
        if line.get("stress"):
            hint = f"重读“{line['stress']}”" if kind == "cjk" else f"stress the word “{line['stress']}”"
            tone = sep(kind).join(x for x in (tone, hint) if x)
        q = s.rstrip("”\"'").endswith(("?", "？"))
        pause = line.get("pause", defaults["question" if q else "sentence"])
        prev = chunks[-1] if chunks else None
        # a directed line gets a chunk of its own, so its tone and pause land exactly on it
        if prev and prev["tone"] == tone and not prev["directed"] and not line:
            prev["text"] += ("" if kind == "cjk" else " ") + s
            prev["pause"] = pause
        else:
            chunks.append({"text": s, "tone": tone, "pause": pause, "directed": bool(line)})
    return chunks


def trim(wav, sr, margin=0.05):
    import numpy as np
    level = 10 ** (TRIM_DB / 20)
    loud = np.flatnonzero(np.abs(wav) > level)
    if not len(loud):
        return wav
    pad = int(margin * sr)
    return wav[max(0, loud[0] - pad):loud[-1] + pad]


def generate(model, cfg, L, text, tone, seed, kind):
    style = sep(kind).join(x for x in ([] if L.get("reference") else [L.get("voice", "")]) + [tone] if x)
    kw = dict(text=f"({style}){text}" if style else text,
              cfg_value=cfg.get("cfg_value", 2.0),
              inference_timesteps=cfg.get("inference_timesteps", 10), seed=seed)
    if L.get("reference"):
        kw["reference_wav_path"] = L["reference"]
        if L.get("reference_text"):
            kw["prompt_wav_path"], kw["prompt_text"] = L["reference"], L["reference_text"]
    return model.generate(**kw)


def write_audio(wav, sr, path):
    import soundfile as sf
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".wav"):
        sf.write(path, wav, sr)
        return
    tmp = os.path.splitext(path)[0] + ".tmp.wav"
    sf.write(tmp, wav, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-ar", str(sr),
                    "-b:a", "256k", path], check=True)
    os.remove(tmp)


def resolve_reference(ep, lang, L):
    # without a reference every chunk would get a freshly designed, different voice
    if not L.get("reference"):
        sys.exit(f"{lang}: no reference voice in voice.json; run `voice --design`, listen, and set reference")
    L = dict(L, reference=ep.media_path(L["reference"]))
    if not os.path.exists(L["reference"]):
        sys.exit(f"reference voice not found: {L['reference']}")
    return L


def design(ep, lang, takes=3):
    """Read the opening lines in each described voice, a few takes each, to pick a reference."""
    import numpy as np  # noqa: F401  (fail early if the audio stack is missing)
    cfg = load_direction(ep)
    L = cfg[lang]
    voices = L["voice"] if isinstance(L["voice"], list) else [L["voice"]]
    kind = ep.lang(lang)["script"]
    sample = (L.get("design_text") or
              ("" if kind == "cjk" else " ").join(sentences(ep.segments[lang][0]["audio"], kind)[:2]))
    model = load_model(cfg)
    sr = model.tts_model.sample_rate
    out = []
    for i, v in enumerate(voices, 1):
        for t in range(takes):
            seed = cfg.get("seed", 42) + t
            wav = generate(model, cfg, {"voice": v}, sample, "", seed, kind)
            path = ep.media_path(f"voice/{lang}-design-{i}-seed{seed}.wav")
            write_audio(trim(wav, sr), sr, path)
            out.append(path)
    with open(ep.media_path(f"voice/{lang}-design.txt"), "w", encoding="utf-8") as f:
        f.write(sample + "\n")
    return out


def show_plan(ep, lang, only=None):
    """Print the chunks, tones and pauses without loading the model; warn on lines that match nothing."""
    cfg = load_direction(ep)
    kind = ep.lang(lang)["script"]
    defaults = {"sentence": 0.3, "question": 0.5, **cfg.get("pause", {})}
    for n, (seg, seg_dir) in enumerate(zip(ep.segments[lang], cfg[lang].get("segments", [])), 1):
        if only and n not in only:
            continue
        sents = sentences(seg["audio"], kind)
        for ln in seg_dir.get("lines", []):
            if not any(s.startswith(ln["match"]) for s in sents):
                print(f"  ! seg{n:02d}: no sentence starts with {ln['match']!r}")
        print(f"{lang} seg{n:02d}")
        for c in plan(seg["audio"], kind, seg_dir, defaults):
            print(f"  ({c['tone']}) {c['text']}  [{c['pause']}s]")


def render(ep, lang, only=None, force=False):
    """One narration file per segment, plus <file>.chunks.json with every chunk's time."""
    import numpy as np
    cfg = load_direction(ep)
    L = resolve_reference(ep, lang, cfg[lang])
    kind = ep.lang(lang)["script"]
    defaults = {"sentence": 0.3, "question": 0.5, **cfg.get("pause", {})}
    files = narration_files(ep, lang)
    targets = [n for n in range(1, len(files) + 1) if not only or n in only]
    clash = [files[n - 1] for n in targets if os.path.exists(files[n - 1])]
    if clash and not force:
        sys.exit(f"{lang}: narration already exists (pass --force to replace):\n  " + "\n  ".join(clash))
    model = load_model(cfg)
    sr = model.tts_model.sample_rate
    seg_dirs = L.get("segments", [])
    out = []
    for n in targets:
        seg_dir = seg_dirs[n - 1] if n - 1 < len(seg_dirs) else {}
        chunks = plan(ep.segments[lang][n - 1]["audio"], kind, seg_dir, defaults)
        parts, log, t = [], [], 0.0
        for i, c in enumerate(chunks):
            seed = seg_dir.get("seed", cfg.get("seed", 42))
            wav = trim(generate(model, cfg, L, c["text"], c["tone"], seed, kind), sr)
            parts.append(wav)
            log.append({"text": c["text"], "tone": c["tone"], "start": round(t, 3),
                        "end": round(t + len(wav) / sr, 3)})
            t += len(wav) / sr
            if i < len(chunks) - 1:
                parts.append(np.zeros(int(c["pause"] * sr), dtype=wav.dtype))
                t += c["pause"]
        path = files[n - 1]
        write_audio(np.concatenate(parts), sr, path)
        with open(path + ".chunks.json", "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=1)
        out.append(path)
        print(f"{lang} seg{n:02d}: {len(chunks)} chunks, {t:.1f}s -> {path}")
    return out
