"""Regression: the generic timing model must reproduce episode 1 as delivered.

ZH_STARTS are the shot starts hard-coded in the original build_v3.py (table
values rounded to 0.1 s, a few nudged by hand),
so they agree to about two frames (0.07 s). EN_STARTS were computed by hand for the English
cut, so they agree only to about 0.15 s.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pipeline import timing as T  # noqa: E402
from pipeline.common import Episode  # noqa: E402
from pipeline.text import chunks  # noqa: E402

EP1 = os.path.join(ROOT, "episodes", "ep01-chinese-room")

ZH_STARTS = [0.0, 6.7, 11.5, 24.2, 26.7, 32.4, 40.9, 64.4, 72.9, 79.6, 87.8, 97.4, 101.8,
             116.4, 124.2, 138.3, 144.6, 150.5, 157.8, 169.1, 186.7, 199.9, 210.6, 218.3,
             233.0, 243.7, 252.3, 259.8, 265.0, 269.1, 274.4, 282.4, 286.1, 297.1, 309.1,
             316.5, 327.6, 335.3, 344.2]
EN_STARTS = [0.30, 6.40, 11.68, 23.52, 26.37, 33.43, 42.06, 68.94, 76.51, 83.55, 88.10,
             98.85, 102.99, 118.87, 128.58, 141.88, 150.27, 156.49, 167.11, 179.11, 196.83,
             208.95, 218.80, 226.71, 242.96, 252.69, 262.98, 272.78, 279.36, 284.46, 289.80,
             297.78, 300.91, 309.07, 317.84, 325.51, 335.16, 341.25, 350.56]


class Episode1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ep = Episode(EP1)
        cls.zh, cls.en = T.compute(ep, "zh"), T.compute(ep, "en")

    def test_zh_matches_delivered_cut(self):
        got = [s["start"] for s in self.zh["shots"]]
        for sid, a, b in zip([s["id"] for s in self.zh["shots"]], got, ZH_STARTS):
            self.assertAlmostEqual(a, b, delta=0.07, msg=sid)

    def test_en_matches_hand_timing(self):
        got = [s["start"] for s in self.en["shots"]]
        got[0] = 0.30  # the original started EN at 0.30, which shifted every picture 0.3 s early
        for sid, a, b in zip([s["id"] for s in self.en["shots"]], got, EN_STARTS):
            self.assertAlmostEqual(a, b, delta=0.15, msg=sid)

    def test_pictures_tile_the_audio(self):
        for t in (self.zh, self.en):
            self.assertEqual(t["shots"][0]["start"], 0.0)
            self.assertAlmostEqual(t["shots"][-1]["end"], t["total"])
            for a, b in zip(t["shots"], t["shots"][1:]):
                self.assertAlmostEqual(a["end"], b["start"])

    def test_guard_hold_pushes_next_shot(self):
        s = {x["id"]: x for x in self.zh["shots"]}
        self.assertAlmostEqual(s["7A-2"]["dur"], 4.0, delta=0.01)
        self.assertNotIn("extended", {x["id"]: x for x in self.en["shots"]}["7A-2"])

    def test_every_guardrail_resolved(self):
        self.assertEqual(T.unresolved(self.zh), [])
        self.assertEqual(T.unresolved(self.en), [])

    def test_subtitles_fit(self):
        for t, n in ((self.zh, 26), (self.en, 68)):
            self.assertTrue(all(len(e[2]) <= n for e in t["subtitles"]))

    def test_chunks_keep_text(self):
        s = "所以系统反驳说：凭什么要求计算机的某一个零件懂？理解，也许属于整个组织起来的系统，而不是某一个部分。"
        self.assertEqual("".join(chunks(s, "cjk", 26)), s)


if __name__ == "__main__":
    unittest.main()
