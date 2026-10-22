"""Shared helpers: loading an episode, resolving media, ffmpeg calls, fonts."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/**/NotoSansCJK*.ttc",
    "/usr/share/fonts/**/NotoSansSC*.otf",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
]


class Episode:
    """episode.json + segments.json of one episode folder."""

    def __init__(self, folder, media=None):
        self.dir = os.path.abspath(folder)
        self.path = os.path.join(self.dir, "episode.json")
        with open(self.path, encoding="utf-8") as f:
            self.data = json.load(f)
        with open(os.path.join(self.dir, "segments.json"), encoding="utf-8") as f:
            self.segments = json.load(f)
        self.media = os.path.abspath(media or os.environ.get("EPISODE_MEDIA")
                                     or os.path.join(self.dir, self.data.get("media_dir", "media")))
        self.build = os.path.join(self.dir, "build")

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    @property
    def canvas(self):
        c = self.data["canvas"]
        return c["width"], c["height"], c["fps"]

    def lang(self, lang):
        return self.data["languages"][lang]

    def languages(self, which="all"):
        names = list(self.data["languages"])
        if which in (None, "all"):
            return names
        if which not in names:
            sys.exit(f"unknown language {which!r}; this episode has {names}")
        return [which]

    def media_path(self, rel):
        return rel if os.path.isabs(rel) else os.path.join(self.media, rel)

    def build_dir(self, lang):
        d = os.path.join(self.build, lang)
        os.makedirs(d, exist_ok=True)
        return d

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            f.write("\n")


def need(tool):
    if not shutil.which(tool):
        sys.exit(f"{tool} not found. Install ffmpeg, e.g. `brew install ffmpeg` on macOS, "
                 "`apt install ffmpeg` on Linux, or `pip install imageio-ffmpeg` and put its binary on PATH.")


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd)[:300], file=sys.stderr)
        print(r.stderr[-2500:], file=sys.stderr)
        sys.exit(1)
    return r


def probe(path, strict=True):
    """Duration and streams of a media file, read from `ffmpeg -i` (no ffprobe needed).

    With strict=False an unreadable file returns (None, []) instead of exiting.
    """
    need("ffmpeg")
    if not os.path.exists(path):
        sys.exit(f"missing file: {path}")
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:
        if not strict:
            return None, []
        sys.exit(f"cannot read {path}:\n{err[-500:]}")
    h, mi, sec = m.groups()
    streams = []
    for kind, rest in re.findall(r"Stream #\S+.*?: (Video|Audio): (.*)", err):
        size = re.search(r"\b(\d{2,5})x(\d{2,5})\b", rest) if kind == "Video" else None
        streams.append((kind.lower(), size.groups() if size else None))
    return int(h) * 3600 + int(mi) * 60 + float(sec), streams


def duration(path):
    return probe(path)[0]


def find_font(preferred=None):
    for pat in ([preferred] if preferred else []) + FONT_CANDIDATES:
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    sys.exit("No CJK font found. Pass --font /path/to/font.ttc (it must cover Chinese).")
