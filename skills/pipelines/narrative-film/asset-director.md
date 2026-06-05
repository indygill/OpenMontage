# Asset Director — Narrative Film Pipeline

## When to use

After the shot list is approved. You generate or gather every asset the
`scene_plan` requires and record them in an `asset_manifest`. Technical stage —
auto-proceeds, but announce provider/model/cost before any paid generation.

## Output artifact

`asset_manifest` (schema: `schemas/artifacts/asset_manifest.schema.json`).

## Process

1. **Read Layer 3 skills first.** For every generation tool, read its
   `agent_skills` before writing prompts (provider-specific prompt structure and
   quality techniques). Route through selectors: `image_selector`,
   `video_selector`, `tts_selector`.
2. **Preserve character identity.** For every shot a character appears in, carry
   that character's `consistency_anchors` (and reference images if
   `identity_method: reference_image`) into the prompt verbatim. Consistency
   across shots is the top quality bar for narrative work.
3. **Reuse provided assets.** Honor `required_assets[].source`:
   - `provided` → use the user's file; do not regenerate.
   - `source` → pull from reviewed source media (`source_media_review`).
   - `generate` / `record` → create it.
4. **Record provenance** for every asset: `source_tool`, `subtype`
   (`generated`/`stock`/`provided`), `license` (`user-provided` for user files),
   and `original_url` where applicable. Link each asset to its `scene_id`.
5. **Music** per the proposal's music plan (library track, generated, or none).

## Review focus

- Character identity is consistent across each character's shots.
- Provided assets are reused with correct provenance.
- Motion-required beats use real clips, not still-image substitutes.
- All referenced files exist on disk.
