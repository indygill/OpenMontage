# Asset Director — Brand Narrative Pipeline

## When to use

After the shot plan. You generate/gather on-brand assets and record them in an
`asset_manifest`. Auto stage; announce provider/model/cost before paid calls.

## Output artifact

`asset_manifest` (schema: `schemas/artifacts/asset_manifest.schema.json`).

## Process

1. **Read Layer 3 skills first** for each generation tool (`agent_skills`).
   Route through `image_selector`, `video_selector`, `tts_selector`.
2. **Narration uses the locked brand voice.** Pass `brand_kit.audio.tts_voice`
   (`provider` + `voice_id`) to `tts_selector` — the same voice across every
   brand video.
3. **Visuals on-brand.** Constrain image/video prompts to the brand palette and
   `style_playbook`; carry brand colors and motion signature into prompts.
4. **Reuse brand assets, don't regenerate.** The logo and any provided brand
   files come from the `brand_kit` / `brands/<brand>/` assets — reference them
   with `subtype: "provided"` and `license: "user-provided"`. Never regenerate a
   logo.
5. **Music** from `brand_kit.audio.music_style` per the proposal.
6. Record provenance and link each asset to its `scene_id`.

## Review focus

- Narration uses the locked brand TTS voice.
- Visuals are on-palette and on-style.
- Logo and provided brand assets are reused, not regenerated.
