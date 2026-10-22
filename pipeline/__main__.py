"""python3 -m pipeline <command> <episode folder> [--lang zh|en|all]

  new       copy the template into a new episode folder
  tts-text  write one .txt per narration segment for your TTS tool
  measure   read the recorded segment lengths into episode.json
  timing    re-anchor shots to the narration; writes timing-<lang>.md
  mix       narration + music -> build/<lang>/mix.m4a
  build     render build/<folder>-<lang>.mp4
  qa        check streams, length and tail; extract review frames
"""
import argparse
import os
import shutil
import sys

from . import build as B
from . import mix as M
from . import qa as Q
from . import timing as T
from .common import Episode, find_font

TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "episodes", "_template")


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m pipeline", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["new", "tts-text", "measure", "timing", "mix", "build", "qa"])
    p.add_argument("episode", help="episode folder, e.g. episodes/ep02-trolley")
    p.add_argument("--lang", default="all")
    p.add_argument("--media", help="media folder (default: <episode>/media, or $EPISODE_MEDIA)")
    p.add_argument("--font", help="CJK font file for overlays and subtitles")
    p.add_argument("--limit", type=int, help="build: render only the first N shots")
    p.add_argument("--final-only", action="store_true", help="build: reuse silent.mp4, redo overlays")
    p.add_argument("--force", action="store_true", help="build anyway with unresolved guardrails or overflowing text")
    a = p.parse_args(argv)

    if a.command == "new":
        if os.path.exists(a.episode):
            sys.exit(f"{a.episode} already exists")
        shutil.copytree(TEMPLATE, a.episode)
        print(f"created {a.episode}: fill segments.json, then storyboard.md, then the shots in episode.json")
        return

    ep = Episode(a.episode, a.media)
    failed = False
    for lang in ep.languages(a.lang):
        if a.command == "tts-text":
            for f in M.tts_text(ep, lang):
                print(f)
            continue
        if a.command == "measure":
            print(lang, M.measure(ep, lang))
            continue
        if a.command == "mix":
            out, total = M.mix(ep, lang)
            print(f"{lang}: {out} ({total:.2f}s)")
            continue
        try:
            t = T.compute(ep, lang)
        except T.TimingError as e:
            sys.exit(f"timing: {e}")
        md = T.write(ep, t)
        bad = T.unresolved(t)
        if a.command == "timing":
            print(f"{lang}: {len(t['shots'])} shots, {T.fmt(t['total'])} -> {md}")
            for f in t["flags"]:
                print(f"  {f['shot']}: {f['issue']} -> {f['resolution'] or 'UNRESOLVED'}")
            for line in Q.check_text_fit(ep, lang, t, find_font(a.font)):
                print("  text:", line)
            failed |= bool(bad)
        elif a.command == "build":
            if bad and not a.force:
                sys.exit(f"{lang}: unresolved guardrails {[f['shot'] for f in bad]}; "
                         "give those shots internal stages or a `short` reason, or pass --force")
            B.build(ep, lang, t, a.font, a.limit, a.final_only, a.force)
        elif a.command == "qa":
            path = os.path.join(ep.build, f"{os.path.basename(ep.dir)}-{lang}.mp4")
            report, frames = Q.verify(ep, lang, t, path)
            for name, ok, detail in report:
                print(f"  [{'ok' if ok else 'FAIL'}] {name}: {detail}")
                failed |= not ok
            print(f"  {len(frames)} review frames in {os.path.dirname(frames[0]) if frames else '-'}"
                  " - open and look at every one before delivering")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
