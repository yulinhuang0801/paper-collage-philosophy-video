# Paper Collage Philosophy Video

A production method and pipeline for short bilingual philosophy explainers in a torn-paper collage style. Each episode is about 6 minutes long, with a Chinese version for Bilibili and an English version for YouTube, both built from one script and one set of pictures.

Episode 1: [Could a Machine Understand You? — The Chinese Room](https://www.youtube.com/watch?v=_cFOyDM56DM)

- `SKILL.md` is the method: content rules, approval gates, visual style, storyboard grammar, timing rules, QA and publishing. An AI agent or a person can follow it.
- `pipeline/` is the code: from narration to finished, checked videos.
- `episodes/ep01-chinese-room/` holds episode 1's data (`segments.json`, `episode.json`) and the generated timing tables. `episodes/_template/` is the starting point for the next episode.
- `references/` holds the episode 1 script, storyboard and original hand-made timing tables, plus the original one-off scripts.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # plus ffmpeg on PATH
.venv/bin/python -m unittest discover tests
.venv/bin/python -m pipeline timing episodes/ep01-chinese-room
```

Rendering needs the episode's media (frames, clips, audio) in `episodes/<episode>/media/` or under `--media DIR`. Media is not in git.

## Technical problems it solves

**One picture track, two narrations of different lengths.** Chinese and English narration differ in length sentence by sentence; in episode 1 the English runs 7 s longer overall. Each shot is defined by the sentences it illustrates, not by timecodes. The timing model then places every sentence in each recorded language: segment starts come from the mix model, and sentence times are proportional to character counts. The same 39 shots therefore land on the right words in both languages, and a re-recorded line moves only the shots after it. On episode 1 the model reproduces the delivered Chinese cut to within two frames.

**Pacing rules enforced in code.** Pictures held over 14 s lose viewers, and very short shots feel like mistakes unless they're deliberate. The timing step flags both. It refuses to build until each one has internal stages or a stated reason. It also protects "guard points", deliberate pauses that must not be squeezed, by pushing the next shot later instead.

**Text that never breaks the frame.** All on-screen text is an overlay, so both languages share base pictures that contain no words. Before rendering, every title, label and subtitle is measured in the real font. The build stops if any of them would leave the frame or cover another. This check found two layout defects in the published episode 1.

**Cost control for AI images.** New art is expensive and drifts in style. The storyboard reuses approved frames as crops, pans and composites. Newly drawn area stays under 40% of each composite.

**Render integrity.** Long ffmpeg renders can die halfway and still leave a file that looks finished. QA checks the streams, size and length, decodes the last seconds to catch truncated writes, and saves a review frame from every overlay window. Overlays can be redone without re-rendering the 39 shots.

## Status

- Episode 1 is published on YouTube (October 21, 2026). The Bilibili upload is not recorded here yet.
- Tested: the timing model against episode 1 (`tests/`), and full renders of both languages, mix and QA, run on stand-in media. The episode 1 renders have not been re-made from the real media with this pipeline yet.
- The image, video, voice and music tools used for episode 1 are not yet recorded (see "Tool stack" in `SKILL.md`).
