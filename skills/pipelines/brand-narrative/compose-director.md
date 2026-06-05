# Compose Director — Brand Narrative Pipeline

## When to use

Final render. You compose the edit into a master plus per-platform derivative
renders, run the **brand-safety gate**, and produce `render_report` +
`final_review`.

## Output artifacts

`render_report` (schema: `schemas/artifacts/render_report.schema.json`) and
`final_review` (schema: `schemas/artifacts/final_review.schema.json`).

## Runtime routing (enforced)

`video_compose` routes by `edit_decisions.render_runtime` — the value locked at
proposal and carried through edit unchanged.

1. **Read `render_runtime` from `edit_decisions`.** It must equal the locked
   proposal value. A mismatch is a CRITICAL governance violation — surface it,
   do not proceed.
2. **If the locked runtime is unavailable** (e.g. `render_runtime: "hyperframes"`
   but Node < 22 / missing `ffmpeg`/`npx` / `hyperframes doctor` fails; or
   `"remotion"` but Remotion isn't installed): **do NOT silently swap.** Escalate
   a structured blocker and wait for approval.

| Runtime | Brand/social fit | Requires |
|---|---|---|
| **HyperFrames** | Kinetic typography, logo stingers, product promos, launch reels | Node ≥ 22 + FFmpeg + `npx hyperframes` |
| **Remotion** | Data/stat cards, motion-clip composition, word-level captions | Node + `remotion-composer/` + `node_modules` |
| **FFmpeg** | Simple concat / subtitle burn | `ffmpeg` (always) |

## Multi-aspect derivative renders

Render the master, then one output per target platform from the proposal, using
`lib/media_profiles.py` profiles. Record each in `render_report.outputs[]`: the
master as `role: "hero"`, each platform variant as `role: "derivative"` (and
`platform_target` set). Re-position the logo per aspect so it always respects the
brand safe-area.

## Brand-safety gate (must pass)

Before declaring success, verify against the `brand_kit`:

- **Logo** present, on-brand variant, within `safe_area_pct` and ≥ `min_size_px`
  in every aspect → missing/misplaced logo = CRITICAL.
- **Required CTA and disclaimer** present where compliance demands → absent = CRITICAL.
- **Contrast** of text over background meets the playbook a11y color rules →
  failing = SUGGESTION.
- No `dont_words` in burned-in copy → present = SUGGESTION.

Record gate results in `final_review`.

## Verify

`ffprobe` every output; record encoding, duration, resolution, and
`platform_target` in `render_report`.

## Review focus

- Brand-safety gate passed.
- Per-platform derivative renders produced for each target aspect.
- `render_runtime` matches the locked choice.
