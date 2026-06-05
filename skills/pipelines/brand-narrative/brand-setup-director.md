# Brand Setup Director — Brand Narrative Pipeline

## When to use

The one-time brand onboarding. You build the **`brand_kit`** that every future
video for this brand will reuse. **Skip this stage entirely if
`brands/<brand>/brand_kit.json` already exists** — load it and move to the brief.

## Output artifact

`brand_kit` (schema: `schemas/artifacts/brand_kit.schema.json`), stored at
`brands/<brand>/brand_kit.json` (shared across projects).

## v1 = manual entry

The user supplies the identity directly. Capture all four facets:

1. **Visual** — logo files (variants: full / mark / mono / reversed / icon),
   `safe_area_pct`, `min_size_px`, default placement; the color palette as
   `{role, hex, usage}` entries (at least primary/secondary/accent);
   typography (heading/body fonts + weights). Generate a style playbook from
   these tokens (`lib/playbook_generator.py`) and record its name in
   `visual.style_playbook` so the rest of the pipeline styles through the
   existing playbook system.
2. **Verbal** — `voice_tone`, `tagline`, `messaging_pillars`, `do_words`,
   `dont_words`, `reading_level`.
3. **Audio** — a locked brand TTS voice (`{provider, voice_id}` — v1 uses an
   existing voice id, not cloning), `music_style`, optional `sonic_logo_path`.
4. **Compliance** — `required_cta`, `disclaimer`, `hashtags`, and per-platform
   `handles`.

## Future enhancement (not v1)

Auto-extraction from a website URL or PDF brand guide via the `visual-style`
Layer 3 skill + `playbook_generator` — the biggest further cut to user input.
Flag it as available if the user would rather not enter everything by hand.

## Review focus

- Logo variants, color roles, and typography are complete and consistent.
- Verbal identity is concrete (voice, do/don't words, messaging).
- A brand TTS voice and music style are set.
- Compliance items captured.
