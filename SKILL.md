---
name: paper-collage-philosophy-video
description: Produce a bilingual (Chinese for Bilibili, English for YouTube) paper collage philosophy explainer episode end to end, from script and storyboard through AI images and clips, narration-anchored shot timing, rendering and QA, to publishing. Use when asked to make a philosophy or thought-experiment explainer video, a new episode of this series (episode 2, the next episode), or to re-render, re-time or fix episode 1, The Chinese Room.
---

# Paper Collage Philosophy Video Production

Each episode is one folder under `episodes/`: `segments.json` (the narration), `episode.json` (canvas, timing model, shots, overlays) and `storyboard.md`. Media stays outside git in `<episode>/media`. The `pipeline` package turns that folder into finished videos. Episode 1 (`episodes/ep01-chinese-room`) is the worked example of every rule below. Copy its shapes, replace its content, keep the method.

```
python3 -m pipeline new episodes/ep02-<slug>       # from episodes/_template
python3 -m pipeline tts-text episodes/ep02-<slug>  # one .txt per segment for the TTS
python3 -m pipeline measure  episodes/ep02-<slug>  # recorded lengths -> episode.json
python3 -m pipeline timing   episodes/ep02-<slug>  # shots re-anchored; timing-<lang>.md
python3 -m pipeline mix      episodes/ep02-<slug>  # narration + music
python3 -m pipeline build    episodes/ep02-<slug>  # render both languages
python3 -m pipeline qa       episodes/ep02-<slug>  # file checks + review frames
```

Needs Python 3.9+, ffmpeg on PATH, and Pillow (`pip install -r requirements.txt`). Add `--lang zh` or `--lang en` to run a single language.

## Approval gates

Stop and get the user's yes at each gate. Never pass a gate on your own judgment.

1. Topic, unified question and script (both languages) read for fluency.
2. Storyboard file, before any image is generated.
3. Anchor face frame, before any video is generated.
4. Every generated clip, checked at its midframe (see below).
5. The delivery note with every downgrade from the storyboard, before publishing.
6. TikTok format, which needs a vertical cut, before making one.

## Shape of an episode

- One script, two language versions: Chinese for Bilibili and English for YouTube, each 4 to 6 minutes long.
- Open with a hook in the first seconds: a concrete question the viewer can't shake off.
- Strip the thought experiment of strict academic preconditions, because they raise the thinking cost for the viewer. Keep the core idea simple and direct.
- Give the strongest argument for each side before the ending question. Never stack the deck toward one answer.
- End open, on one unified question, so the comment section can argue.

## Visual style

This section is what keeps the episodes looking like one series. Put it in every image and video prompt.

- **Medium:** torn and cut paper collage. Visible paper fibres and torn white edges, layered flat pieces, slight shadows between layers. No 3D rendering, no photographic texture.
- **Figures:** cubist, Picasso-inspired faces built from flat paper planes, with bold black outlines (about 1–2% of frame width) and simple almond eyes. They read as calm and gentle.
- **Rooms and objects:** fragmented, slightly tilted planes. Speech bubbles are cream paper with black outlines.
- **Palette:** cream (#F3EEDE) paper ground and ink black (#121412), plus the episode's colour arc. Episode 1 moved from warm green to cool blue in six small steps (see its storyboard).
- **Frame:** 1152×768 (3:2). Leave the bottom 90 px quiet for subtitles. Keep text out of the pictures, because every word is an overlay.
- **Comfort rule, above style:** faces must look pleasant and gentle. Nothing grotesque, uncanny or fleshy ships.

Prompt skeleton:

> torn paper collage illustration, cubist Picasso-inspired flat paper planes, bold black outlines, visible paper texture and torn white edges, {palette for this segment}, {subject and action}, calm gentle expression, simple composition, 3:2, no text, no letters

Negative / constraint line for video models (they drift toward realism on this style):

> keep flat paper collage style throughout, no realistic skin, no 3D shading, no photographic faces, no morphing into a real person, no text

## Tool stack

Record the actual tools in the episode's `storyboard.md` so the next episode can match the look and voice. Episode 1 did not record them. Fill this table in when you learn them, and treat a change of model or voice as a style change that needs the user's yes.

| Stage | Requirement | Episode 1 |
|---|---|---|
| Keyframes | text-to-image; also image-to-image from approved frames | not recorded |
| Face clips | image-to-video from an approved keyframe, about 5–10 s | not recorded |
| Narration | one voice per language, read from `tts-text` files | not recorded |
| Music | one reflective track, looped under the voice | not recorded |

Export narration at 44.1 or 48 kHz. The delivered Chinese file of episode 1 has 24 kHz mono audio, which sounds dull on headphones.

## Write the script

- Write the narration into `segments.json`: one entry per segment, with a keyframe id and the exact text the TTS reads. Keep punctuation light, because the TTS reads it literally.
- Word the unified question once per language. The opening, the on-screen text, the end card and the pinned comment all use those exact words.
- Write the publishing pack together with the script, not after it: platform titles, a pinned comment with one strongest argument per side, and a short description built from the hook. Put it in `<episode>/publishing.md`.
- Read the finished script once for fluency, then pass gate 1. Every later stage keys off this text.

## Design the storyboard

- Design shots of about 10 seconds, never one picture per paragraph. Viewers start drifting when a single picture holds much past 15 seconds.
- Give every shot a motion strategy from the builder's grammar: `clip` (natural motion), `still` (slow push in), `freeze`, `pan`, `vpan` (tall strip image), and `sub` (staged parts with crossfades).
- Plan the colour arc as small pushes from segment to segment, with no jump of a whole segment's colour between neighbouring shots.
- Mark guard points and treat them as uncompressible. In `episode.json`, give the shot a `hold` (seconds) and a `guard` note. Episode 1 had two: a music-only tail of about 4 s where only a question mark breathes (5E), and a halo still held for 4 s (7A-2).
- Write `storyboard.md` and pass gate 2.

## Produce the images and clips

- Generate keyframes first, and pass gate 3 on the anchor face. Face shots inherit from it.
- Cut the number of genuinely new images hard before generating. Reuse approved frames, crop regions out of them, and build composites whose newly drawn area stays under 40% (`episodes/ep01-chinese-room/build_composites*.py` show how).
- Route shots with faces through image-to-video so the faces move naturally. Use stills with camera moves for objects, rooms and diagrams.
- Check the midframe of every generated clip. If it drifted toward a realistic face, regenerate it with the constraint line above and check the replacement the same way.
- Check a source image's layout before writing crop boxes. Episode 1 lost time to a "four panel" image that was really four vertical strips. Those became `vpan` shots, not quadrant crops.
- Write a disposition for every deviation from the storyboard (for example, a motion that became a push in) so the delivery note can disclose it honestly.

## Re-anchor timing to the recorded narration

`measure` and `timing` do this. The rules they enforce:

- Never build to storyboard timecodes. Record the narration first; `measure` stores each segment's length.
- Segment starts follow the mix model in `episode.json` → `timing`: a lead (0.3 s), a gap between segments (0.45 s), extra pauses (`pause_after`; episode 1 had 3.5 s after the personal segment 5), and a tail (1.3 s).
- Each shot lists, per language, the sentences it covers (`[first, last]`, where -1 means the last sentence). Sentences get time in proportion to their character counts. To cut inside a sentence, use `start_at` / `end_at` with a phrase. `timing` refuses to run if any sentence belongs to no shot.
- Pictures tile the timeline: the first shot starts at 0, and every shot ends where the next begins.
- A guard point shorter than its `hold` is extended, and the next shot starts late by the same amount.
- **Guardrails:** a shot over 14 s must have internal stages (a `sub` spec, or a `staged` note). A shot under 6 s needs a `short` reason whose kind is one of transition, introduction, performance, event, motion or loop, plus a note. `build` refuses unresolved guardrails unless forced.
- `timing` writes `timing-<lang>.md` beside the storyboard. That table is generated; edit `episode.json`, not the table.

## Build the video

- `build` renders each shot to its exact length, joins them into a silent file, then adds subtitles, text overlays and image overlays and muxes the audio. Clips of any source length are trimmed, slowed by up to 36%, or looped.
- If an overlay pass fails, rerun with `--final-only`. It reuses `build/<lang>/silent.mp4` instead of rendering every shot again.
- Audio: `mix` places each narration segment at its start over the music at a ratio of about 0.16, with the voice clearly dominant. If a final mix already exists, set `languages.<lang>.audio` and skip `mix`.
- Subtitles come from the same sentence timing as the shots. Long sentences are split at clause boundaries to at most `max_chars` (26 Chinese or 68 Latin characters at size 30).
- Every text the viewer reads is an overlay in `episode.json`, never baked into a picture, so both languages share the same base pictures. Overlay times use anchors (`{"shot": "8D1", "offset": 0.5}`, `{"shot": "9A", "at": "end"}`, `{"phrase": "…"}`, `{"total": -5.5}`), so they move with a re-recorded narration.
- Place paired lines with `x: "left-half"` / `"right-half"`, single lines with `"center"` or `{"center_at": px}`. Never trust an estimated fixed x.
- Before rendering, `build` measures every overlay and subtitle in the real font and stops if any would leave the frame or cover another box on screen at the same time.

## Check the render

- `qa` checks one video and one audio stream, the frame size, the length against the timing, and that the last 3 s decode. An unreadable file is a truncated write (a missing moov atom), not a finished render.
- `qa` saves a frame from every overlay window and from every fourth shot to `build/<lang>/qa/`. Open and look at every one before delivering.
- Deliver with an honest note listing every downgrade from the storyboard, so the user rules on real information (gate 5).

## Publish

- Upload the Chinese version to Bilibili and the English version to YouTube. Decide the TikTok format with the user first (gate 6), because the master is landscape.
- Fill each platform from `publishing.md`. Declare the work as original, and tick the AI-generated content disclosure wherever the form offers one, because the pictures and the narration are AI made.
- Post the pinned comment right after publishing, and pin it where the platform allows.
- Expect limits on a brand-new channel and report them plainly instead of working around them. On episode 1, YouTube refused comment pinning until the channel built history, and custom thumbnails stayed locked until the user verified a phone number in YouTube Studio.
- The Bilibili file picker may resist automated upload. Hand the live browser to the user to pick the file, then take control back and finish the form.
- Record the published links in `episode.json` → `published`.

## Episode 1 record

- **The Chinese Room** (John Searle, 1980). 355.5 s in Chinese and 362.5 s in English, 39 shots per version, published to YouTube: https://www.youtube.com/watch?v=_cFOyDM56DM
- `references/` holds the full script, the v3 storyboard and the original hand-made timing tables. `references/episode-1-original-scripts/` holds the original one-off builders, kept as a record. They only ran on the machine that made them.
- The generic timing model reproduces the delivered Chinese shot starts to within 0.07 s (two frames) and the hand-timed English starts to within 0.15 s (`tests/test_timing.py`).
- Moving to the pipeline surfaced three defects in the delivered files, all fixed in `episode.json`:
  - The original builder started the English cut's first picture at 0.3 s instead of 0, so every English picture runs 0.3 s ahead of its narration.
  - The Chinese end card was as wide as the frame, so its box touched both edges.
  - In the English cut, the boxes behind the two-line question and the two-line end card overlapped, leaving a darker band.
