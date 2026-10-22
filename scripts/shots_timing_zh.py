#!/usr/bin/env python3
"""Re-anchor v3 shots to the recorded ZH narration (sentence-based timing).
Segment speech durations are the calibrated ones from the delivered build.
Guardrail (James, 2026-10-21): any shot >14s must split inside the sentence
(push-in / detail crop / internal stages, no new art); any shot <6s may merge
with a neighbour when visually sensible."""
import re
from segments_v2 import SEGMENTS

SPEECH = [23.5, 39.7, 32.5, 46.8, 62.0, 48.8, 22.2, 44.7, 26.4]  # calibrated, per build output
GAP, EXTRA_AFTER_S5, LEAD = 0.45, 3.5, 0.3

def sentences(text):
    parts = re.findall(r"[^。！？]*[。！？]", text)
    rest = text[len("".join(parts)):]
    if rest.strip():
        parts.append(rest)
    return [p.strip() for p in parts if p.strip()]

def clen(s):
    return len(s.replace(" ", ""))

# shot -> sentence index ranges (0-based, inclusive), per segment
MAP = {
    1: [("1A", [0]), ("1B", [1]), ("1C", [2, 3])],
    2: [("2A", [0]), ("2B", [1]), ("2C", [2, 3]), ("2D", [4, 5, 6, 7, 8, 9])],
    3: [("3A", [0, 1]), ("3B", [2, 3]), ("3C-1", [4, 5, 6]), ("3C-2", [7, 8])],
    4: [("4A", [0]), ("4B", [1, 2, 3]), ("4C", [4, 5]), ("4D", [6, 7]), ("4E", [8])],
    5: [("5A", [0, 1]), ("5B", [2, 3]), ("5C", [4, 5, 6]), ("5D1", [7, 8, 9, 10]),
        ("5D2", [11, 12, 13]), ("5E", [14, 15, 16])],
    6: [("6A", [0, 1, 2]), ("6B", [3, 4, 5]), ("6C-1", [6, 7, 8, 9]), ("6C-2", [10]),
        ("6D", [11, 12])],
    7: [("7A-1", [0]), ("7A-2", [0]), ("7B", [1, 2]), ("7C", [3, 4])],  # 7A split inside s0 below
    8: [("8A", [0]), ("8B", [1]), ("8C", [2, 3]), ("8D1", [4, 5]), ("8D2", [6, 7])],
    9: [("9A", [0]), ("9B", [1, 2]), ("9C", [3, 4])],
}
STAGED = {"2D": "流水线快切（内部多段）", "4B": "元素替换三段（纸→代码→气泡）",
          "5D1": "记忆蒙太奇四格（内部多段）", "6B": "四部件高亮接力（内部多段）",
          "8B": "四组连线依次成立（内部多段）", "4D": "打字机逐字+屏幕光渐亮（内部递进）"}
DISPOSITION = {
    "1B": "保留：三个气泡依次亮起，4.8s 正好是【表演】节奏",
    "2A": "保留：盒→房变形是转场镜，2.5s 成立，不与 2B 合并",
    "2B": "保留：纸片滑入循环×3 填满 5.6s",
    "4A": "保留：塞尔出场是引入镜，4.4s 成立",
    "4E": "保留：叠影拉远收束镜，5.9s 成立",
    "5A": "保留：转向观众+问号，5.9s 成立",
    "7A-1": "保留：书页螺旋飞入是运动镜，5.2s 成立",
    "7A-2": "视觉延续：静帧在旁白锚点外多停 0.6s，凑满 4.0s 守点，7B 画面晚入 0.6s",
    "7B": "保留：6.0s 边界值，搬符号循环成立",
    "8A": "保留：墙倒下是事件镜，与 8B 同底图连续，3.6s 成立",
}

starts, t = [], LEAD
for i, d in enumerate(SPEECH):
    starts.append(t)
    t += d + GAP + (EXTRA_AFTER_S5 if i == 4 else 0)
TOTAL = 355.53

def fmt(x):
    return f"{int(x // 60)}:{x % 60:04.1f}"

rows, flags = [], []
for si, seg in enumerate(SEGMENTS["zh"], start=1):
    text = seg["audio"]
    sents = sentences(text)
    total_chars = sum(clen(s) for s in sents)
    # sentence boundaries within the segment
    bounds, acc = [], starts[si - 1]
    for s in sents:
        dur = SPEECH[si - 1] * clen(s) / total_chars
        bounds.append((acc, acc + dur))
        acc += dur
    shots = MAP[si]
    covered = sorted({i for _, idxs in shots for i in idxs})
    assert covered == list(range(len(sents))), f"S{si}: coverage {covered} vs {len(sents)} sentences"
    for name, idxs in shots:
        a = bounds[idxs[0]][0]
        b = bounds[idxs[-1]][1]
        if name == "7A-1":
            s0 = sents[0]
            cut = s0.index("一个人扮演了整个系统")
            b = a + SPEECH[6] * clen(s0[:cut]) / total_chars
        if name == "7A-2":
            s0 = sents[0]
            cut = s0.index("一个人扮演了整个系统")
            a = bounds[0][0] + SPEECH[6] * clen(s0[:cut]) / total_chars
        if name == "5E":
            b = starts[5]  # extends through the 3.5s music pause to S6 start
        if name == "9C":
            b = TOTAL
        dur = b - a
        note = STAGED.get(name, "")
        if dur > 14 and name not in STAGED:
            flags.append(f"{name}: {dur:.1f}s 超过 14s 且无内部切分，需要处理")
        if dur < 6:
            flags.append(f"{name}: {dur:.1f}s 低于 6s（护栏允许合并或视觉延续）")
        rows.append((name, a, b, dur, "；".join(sents[i][:14] + "…" for i in idxs[:2]), note))

out = ["# 中文版镜头时间表（按已录旁白句界重落，v3 设计）", "",
       f"总长 {fmt(TOTAL)}，共 {len(rows)} 个镜头。护栏：单镜 >14s 必须内切，<6s 可合并或视觉延续。", "",
       "| 镜头 | 起 | 止 | 时长 | 旁白锚点 | 备注 |", "|---|---|---|---|---|---|"]
for name, a, b, dur, anchor, note in rows:
    out.append(f"| {name} | {fmt(a)} | {fmt(b)} | {dur:.1f}s | {anchor} | {note} |")
out += ["", "## 护栏校验"]
unresolved = [f for f in flags if not any(f.startswith(k + ":") for k in DISPOSITION)]
for f in flags:
    key = f.split(":")[0]
    suffix = f" → 处理：{DISPOSITION[key]}" if key in DISPOSITION else " → 未处理"
    out.append(f"- {f}{suffix}")
if not flags:
    out.append("- 无超限镜头。")
out += ["", "## 守点",
        "- 5E：3:19.9 起回到观众脸，最后约 4 秒（3:26.6–3:30.6）旁白结束、纯音乐留白，画面只保留问号呼吸。",
        "- 7A-2：4:25.0 起光环静帧，旁白锚点 3.4s，构建时视觉延续 0.6s 凑满 4.0s 守点（7B 晚入），静帧落在「一个人扮演了整个系统，你还是不懂中文」。",
        "- 9C：最后 5.5 秒叠加统一问题卡（与 8D1 门上文字、8D2、9A 的文字均为叠加层，双语共用底图）。"]
open("shots-zh-timing.md", "w").write("\n".join(out) + "\n")
print(f"shots={len(rows)}")
for name, a, b, dur, _, _ in rows:
    print(f"{name:6s} {fmt(a)}-{fmt(b)}  {dur:5.1f}s")
print("FLAGS:", flags if flags else "none unresolved")
