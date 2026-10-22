# Paper Collage Philosophy Video Production

## Shape of an episode

- Produce each episode in two language versions from one script, Chinese for Bilibili and English for YouTube, at 4 to 6 minutes per version.

- Open with a hook in the first seconds, a concrete question the viewer cannot shake off.

- Strip the thought experiment of strict academic preconditions, because they raise the thinking cost for the viewer. Keep the core idea simple and direct.

- Leave the viewer room to think along, and end open with one unified question so the comment section can argue.

- Present the strongest argument from both sides before the ending question. Never stack the deck toward one answer.

## Write the script

- Write the narration as segment data, one dict per segment with a keyframe id and the exact text the TTS will read. Keep punctuation light in the audio text, because the TTS reads it literally.

- Give the episode one unified question that the opening, the on screen text and the pinned comment all share, worded once per language.

- Write the publishing pack with the script, not after it. The pack holds the platform titles, the pinned comment with one strongest argument per side, and a short description built from the hook.

- Read the finished script once for fluency before production. Fix wording problems at this stage, because every later stage keys off this text.

## Design the storyboard

- Design the episode as shots of about 10 seconds each, never as one picture per paragraph. Viewers start drifting when a single picture holds much past 15 seconds.

- Assign every shot a motion strategy from a small grammar, such as a natural motion clip, a slow push in, a staged internal sequence, a split screen, or a pan across a tall strip image.

- Plan a color arc as a series of small pushes across the segments, with no whole segment color jump between neighboring shots.

- Mark the guard points in the storyboard and treat them as uncompressible. Episode 1 used a music only tail of about 4 seconds with only a question mark breathing, and a halo still held for 4 seconds.

- Write the storyboard to a file and get the user to confirm it before generating any images.

## Produce the images and clips

- Generate the keyframes first and get the user to approve the anchor face frame before any video generation, because the face shots inherit from it.

- Hold the visual comfort rule above style. Faces must look pleasant and gentle, and nothing grotesque or unsettling ships.

- Cut the count of genuinely new images hard before generating. Reuse existing frames, crop regions out of them, and build composites whose newly drawn area stays under 40 percent, taking the base material from frames the user already approved.

- Route shots that contain faces through AI video generation so the faces get natural motion. Use stills with camera moves for objects, rooms and diagrams.

- Check a midframe of every generated clip before accepting it. AI video drifts toward realistic fleshy faces on this style, so regenerate a drifted clip with a stronger flat style constraint and check the replacement the same way.

- Record a written disposition for every deviation from the storyboard, such as a motion that became a push in, so the delivery note can disclose it honestly.

## Re-anchor timing to the recorded narration

- Never build to the storyboard timecodes. Record the narration first, measure each segment duration with `ffprobe`, and hang every shot boundary on the recorded sentences of each language separately.

- Compute segment starts with a lead of 0.3 seconds, a gap of 0.45 seconds between segments, an extra 3.5 second music pause after the personal segment, and a 1.3 second tail.

- Split each segment into shots at sentence boundaries, timing sentences in proportion to their character counts within the segment.

- Apply the guardrails after splitting. Any shot over 14 seconds must split inside the sentence with internal stages and no new art, and any shot under 6 seconds stays only when it works as a transition beat, an introduction beat or a performance beat, with the reason written into the timing table.

- Give each guard point its full hold. When a still guard lands shorter than its hold on the narration anchor, extend the picture visually and start the next shot late by the same amount.

- Save the finished timing table per language as a markdown file beside the storyboard, in the shape of the episode 1 tables in the references folder.

## Build the video

- Build from a data driven shot table, one spec per shot, using the builder in the scripts folder. The spec types cover clips, stills with a push, frozen stills, horizontal pans, vertical pans for tall strip images, and sub shots that chain weighted parts with crossfades.

- Check the source image layout before writing crop regions. Episode 1 lost time to a four panel image that turned out to be four vertical strips, which the builder handles as vertical pans instead of quadrant crops.

- Reuse the final narration and music mix when one already exists for that language, and extract it to a standalone audio file for the build. Otherwise mix the placed narration with the background track at a static ratio of about 0.16 with the voice clearly dominant.

- Regenerate subtitles from the same sentence timing model as the shot table. Chunk long sentences at clause boundaries, and keep chunks within the width the subtitle font can show on one line, about 26 Chinese characters or about 68 Latin characters at size 30.

- Keep every text the viewer reads as an overlay layer, never baked into a picture. Titles, years, door labels, staged sentence reveals, the closing question and the floating question mark all belong to the overlay pass, so both languages share the same base pictures.

- Keep the silent picture only render as a separate file. When a build dies during the final overlay pass, rerun only that pass from the silent file instead of rendering every shot again.

## Check the render

- Extract sample frames at every overlay window and at a few ordinary shots, and read them before delivering. Check that overlay text sits fully inside the frame, because a line placed by estimated width can overflow the edge.

- Center paired overlay lines inside their own halves of the frame instead of trusting fixed x positions.

- Verify the finished file with `ffprobe` for duration and streams, and decode the tail to prove the file is complete. A file with a missing moov atom is a truncated write, not a finished render.

- Deliver with an honest note that lists every downgrade from the storyboard, such as a pop in that became a push in, so the user rules on real information.

## Publish

- Upload the Chinese version to Bilibili and the English version to YouTube, and decide the TikTok format with the user first, because the master is landscape and TikTok is vertical.

- Fill each platform from the publishing pack written with the script. Declare the work as original, and tick the AI generated content disclosure where the form offers one, because the pictures and the narration are AI made.

- Post the pinned comment from the pack right after publishing, and pin it where the platform allows.

- Expect platform limits on a brand new channel and report them plainly instead of working around them. On episode 1, YouTube refused comment pinning until the channel builds history, and custom thumbnails stayed locked until the user verifies a phone number in YouTube Studio.

- Expect the Bilibili file picker to resist automated upload. When it does, hand the live browser to the user to pick the file by hand, then take back control and finish the form.

## Episode 1 record

- Episode 1 is The Chinese Room, delivered at 355.5 seconds in Chinese and 362.5 seconds in English with 39 shots per version, and published to YouTube. Its script, storyboard and both timing tables live in the references folder of this skill, and its builders live in the scripts folder.

- Treat the episode 1 files as worked examples of every rule above. Copy their shapes for a new episode, and replace the content rather than the method.
