# Proposal Director — Brand Narrative Pipeline

## When to use

After the brief. You lock the production plan: tool path, cost, music, the target
platforms / aspect variants, and the composition runtime.

## Output artifacts

`proposal_packet` (schema: `schemas/artifacts/proposal_packet.schema.json`) and
`decision_log` (schema: `schemas/artifacts/decision_log.schema.json`).

## Runtime Selection (required field — `render_runtime`)

Read `skills/meta/animation-runtime-selector.md` and `skills/core/hyperframes.md`
for the decision matrix, and `AGENT_GUIDE.md` → "Present Both Composition
Runtimes (HARD RULE)".

**MANDATORY — present both runtimes, don't silently default:**

1. Query `video_compose.get_info()["render_engines"]`. If both `remotion` and
   `hyperframes` are `True`, proceed to step 2.
2. **Present both runtimes** with brand-specific analysis:
   - **HyperFrames** — one line on fit (HTML/CSS/GSAP kinetic typography, product
     promos, launch reels, logo-stinger motion — the usual brand/social fit), one
     line on tradeoff.
   - **Remotion** — one line on fit (React scene stack, data/stat cards,
     `<OffthreadVideo>` for motion clips, word-level captions), one line on tradeoff.
3. Recommend one, tied to the brief and brand_kit `motion_signature`. Brand/social
   promos often lean **HyperFrames**; data-driven brand explainers lean Remotion.
4. Wait for explicit approval. Do NOT write `render_runtime` into
   `proposal_packet.production_plan` before approval.
5. Log a `render_runtime_selection` decision in `decision_log` with BOTH runtimes
   in `options_considered` (plus `ffmpeg` if realistic).

A `render_runtime_selection` decision with only one option considered when both
were available is a CRITICAL reviewer finding. If only one runtime is available,
say so and record the unavailable option as `rejected_because: "runtime not
available on this machine"`.

## Platforms & aspect variants

List the target platforms from the brief and map each to a profile in
`lib/media_profiles.py` (`instagram_reels` 9:16, `instagram_feed` 1:1,
`youtube_shorts` 9:16, `tiktok` 9:16, landscape 16:9). Compose renders a master
plus one `role: "derivative"` output per platform.

## Music

Use the brand_kit `audio.music_style` to pick or generate music; confirm the
source and cost.

## Review focus

- Both runtimes presented; `render_runtime` locked; decision logged.
- Target platforms and aspect variants listed.
- Music plan resolved; cost estimate has a per-item breakdown.
