# AI video generation: research notes for this series

Researched 2026-10-23 with web search. **Most sources are vendor or affiliate blogs that disagree with each other, so treat model rankings and prices as leads to verify on the vendors' own pages, not as facts.** Nothing here was tested on our own frames.

## What episode 1 actually needed from video generation
Computed from `episodes/ep01-chinese-room/episode.json`:
- 13 of 39 shots use an AI clip, about 110 s of 356 s of screen time (31%). Every other shot is a still with a push, pan or crop.
- 13 distinct clips of about 10 s each, all with faces or a figure; the hook (1A, 1C) is made of clips.
- So the need is narrow: **short, gentle motion of a flat paper-collage face from an approved still, with the style locked.** It is not general text-to-video, long takes, dialogue or lip sync (the voice-over is separate).

## Findings
1. **No source documents holding a paper-cut style across clips.** Paper-cut "templates" (Magic Hour, Morphic, Wavemaker) are presets on one image, not style control across a series. The only way to know a model holds our look is to test it on our own approved frames.
2. **Models cited for character consistency / image-to-video** (reviews disagree; all secondary): Kling 3.0 (identity retention, multi-shot "elements"), Seedance 2.x (many reference inputs), Runway Gen-4.5 (reference images, camera control), Veo 3.1 (reference control, audio; one review says softer on close-up faces), Wan (open weights, can be self-hosted). Prices below are per second at 720p, from aggregator blogs: Kling about $0.08–0.13, Veo 3.1 Fast about $0.10, Veo 3.1 Standard about $0.40 (8 s maximum clip), Seedance about $0.03–0.30 depending on the source. Runway's API price was not found. Sora's API was reported retired on 2026-09-24.
3. **Rough cost of episode 1's clips** (my arithmetic, not a quote): 13 clips x 10 s = 130 s of generation per pass, so about $4–40 per pass depending on the model, before regenerations. Episode 1 needed at least some regenerations (1 reported). Cost is not the constraint; **style drift and review time are.**
4. **A non-AI alternative fits this style:** 2.5D parallax. Split a still into layers (cut-out pieces are already layers in a collage), then move the layers at different rates for a camera move. This is documented as a standard technique (depth maps, After Effects, Blender, DaVinci Fusion, LeiaPix). Paper collage is the best case for it: flat pieces, torn edges, no face to warp. No source compared it with image-to-video for this style; this is a hypothesis to test.
5. **Platform rules (secondary sources, check official pages):**
   - YouTube: disclosure is required for realistic content a viewer could mistake for real; clearly unrealistic or animated content and AI-assisted scripts and captions are exempt (YouTube blog, March 2024). July 2026 coverage says AI use is still monetizable but "inauthentic" (templated, mass-produced) content is not. Our collage style is plainly non-photorealistic, but templated series should show real variation in each episode.
   - Bilibili: AI-generated content must carry the creator's AI label (since 2023); China's national AIGC labelling measures also apply. No 2026-specific Bilibili update was found. Keep ticking the AI disclosure.

## Limits of this research
- No hands-on test with our frames; no vendor docs read directly; prices and model versions conflict across sources.
- The search tool returned few primary sources. Before spending money, open each vendor's pricing and terms page.

## Sources
- https://thebrandhopper.com/learning-resources/best-ai-video-models-for-character-consistency/
- https://www.elser.ai/blog/best-ai-video-model-character-consistency-2026
- https://ropewalk.ai/blog/best-ai-image-to-video-generator-2026
- https://higgsfield.ai/blog/5-Best-AI-Video-Models-2026-Tested-Compared
- https://devtk.ai/en/blog/ai-video-generation-pricing-2026/
- https://fal.ai/learn/tools/best-image-to-video-apis-2026
- https://magichour.ai/templates/details/cmp2rykc402z35210954pcad3-paper-cut-diorama
- https://morphic.com/ai-glossary/parallax-effect
- https://blog.youtube/news-and-events/disclosing-ai-generated-content
- https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/
- https://www.sixthtone.com/news/1013759
- https://technode.com/2023/09/15/bilibili-requires-users-to-tag-ai-generated-content
