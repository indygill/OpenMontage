# Compose Director — Narrative Film Pipeline

## When to use

The final render. You compose the edit into the deliverable and produce a
`render_report` and `final_review`. Technical stage; auto-proceeds — but the
runtime contract is enforced here as a backstop.

## Output artifacts

`render_report` (schema: `schemas/artifacts/render_report.schema.json`) and
`final_review` (schema: `schemas/artifacts/final_review.schema.json`).

## Runtime routing (enforced)

`video_compose` routes by `edit_decisions.render_runtime` — the value locked at
proposal and carried through edit unchanged. Routing is automatic
(`_remotion_render`, `_render_via_hyperframes`, `_render_via_ffmpeg`), but you
must verify the contract:

1. **Read `render_runtime` from `edit_decisions`.** It must equal the value
   locked in the proposal. A mismatch is a CRITICAL governance violation — do not
   proceed; surface it.
2. **If the locked runtime is unavailable at render time** (e.g. `render_runtime`
   is `remotion` but Remotion isn't installed, or `hyperframes` but Node < 22 /
   `npx`/`ffmpeg` missing / `hyperframes doctor` fails): **do NOT silently swap**
   to another engine. Escalate with a structured blocker (what was attempted,
   what failed, options, recommendation) and wait for user approval.
3. **Motion-required deliverables:** never downgrade a motion-led film to a
   still-led animatic or FFmpeg Ken Burns to "get something out". Escalate.

| Runtime | Used for | Requires |
|---|---|---|
| **Remotion** | React scene composition, motion clips via `<OffthreadVideo>`, word-level captions, `CinematicRenderer` | Node + `remotion-composer/` + `node_modules` |
| **HyperFrames** | HTML/CSS/GSAP kinetic titles, SVG character rigs, shader transitions | Node ≥ 22 + FFmpeg + `npx hyperframes` |
| **FFmpeg** | Cuts, concat, subtitle burn, simple source assembly | `ffmpeg` (always available) |

## Per-sequence renders (optional)

If the proposal opted into per-sequence renders, emit one clip per sequence in
addition to the full film:

1. Group the `edit_decisions` cuts by sequence using the `scene_plan` shots'
   `sequence_id` (each shot maps to a sequence; cuts reference those shots/assets).
2. Render each group as its own output, in `sequence_plan.order`.
3. Record every output in `render_report.outputs[]` with a `role`: the complete
   film as `role: "hero"` (or `"full"`), each sequence clip as
   `role: "per_sequence"` with its `sequence_id`. Aspect/platform variants use
   `role: "derivative"`.

All clips use the same locked `render_runtime`. If only the full film was
requested, emit a single `role: "hero"` output as usual.

## Verify

Run `ffprobe` on every output; record encoding profile, duration, and resolution
in `render_report`. Confirm the output matches the approved tone and grade.

## Review focus

- Output mood matches the intended tone and grade.
- Motion-required delivery preserved without silent fallback.
- `render_runtime` in `edit_decisions` matches the locked choice.
