# Proposal Director — Narrative Film Pipeline

## When to use

After the `story_bible` is approved. You lock the **production plan**: visual
treatment, tool path, cost estimate, music plan, and the composition runtime.
This is the planning gate where `render_runtime` is decided and locked.

## Output artifacts

`proposal_packet` (schema: `schemas/artifacts/proposal_packet.schema.json`) and
`decision_log` (schema: `schemas/artifacts/decision_log.schema.json`).

## Runtime Selection (required field — `render_runtime`)

Read `skills/meta/animation-runtime-selector.md` and `skills/core/hyperframes.md`
for the decision matrix, and `AGENT_GUIDE.md` → "Present Both Composition
Runtimes (HARD RULE)" for the governance contract.

**MANDATORY workflow — present both runtimes, don't silently default:**

1. Query `video_compose.get_info()["render_engines"]`. If both `remotion` and
   `hyperframes` are `True`, proceed to step 2.
2. **Present both runtimes** to the user with brief-specific analysis:
   - **Remotion** — one line on fit (React scene stack, `CinematicRenderer`,
     `<OffthreadVideo>` for motion clips, word-level captions), one line on tradeoff.
   - **HyperFrames** — one line on fit (HTML/CSS/GSAP kinetic title sequences,
     SVG character rigs, registry shader transitions), one line on tradeoff.
3. Recommend one with rationale tied to the `story_bible` tone, format, and
   whether the delivery depends on motion.
4. Wait for explicit user approval. Do NOT write `render_runtime` into
   `proposal_packet.production_plan` before approval.
5. Log a `render_runtime_selection` decision in `decision_log` with BOTH runtimes
   in `options_considered`, plus `ffmpeg` if it was a realistic option.

A `render_runtime_selection` decision with only one option considered when both
were available is a CRITICAL reviewer finding. If only one runtime is available,
say so explicitly and record the unavailable option as `rejected_because:
"runtime not available on this machine"`.

**Motion-required deliverables:** if the treatment depends on moving shots, the
chosen runtime is a commitment. Silent downgrade to a still-led animatic or
FFmpeg Ken Burns is forbidden; if the runtime becomes unavailable at compose
time, escalate rather than substitute.

## Render scope

Ask whether the deliverable is the **full film only** (default) or **also
per-sequence clips** (each sequence rendered as its own clip — useful for social
cutdowns or chaptered release). Record the choice in the production plan; compose
honors it. Both use the same locked `render_runtime`.

## Music plan (mandatory)

Resolve music now, not at the asset stage. Check `music_library/` first, then
music-generation tools via the registry, then offer "bring your own" or "no
music". Record the choice in the proposal.

## Cost

Provide a per-item cost estimate (image/video/TTS/music) using
`tools/cost_tracker.py`. Announce provider and model for any paid generation.

## Ingest at altitude

If the user arrives with existing material (script, footage, rough cut),
acknowledge it here: state which stage they enter at, what will be derived
upstream by extraction, and what remains to generate downstream. Record provided
material and its mode (`lock`/`seed`/`reference`) in the proposal.

## Review focus

- Production plan matches the story_bible's tone, format, and world.
- Both runtimes presented; `render_runtime` locked; decision logged.
- Music plan resolved; cost estimate has a per-item breakdown.
