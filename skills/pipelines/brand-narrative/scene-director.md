# Scene Director — Brand Narrative Pipeline

## When to use

After the script. You plan the shots, styled by the brand playbook and built for
short-form social. Auto stage.

## Output artifact

`scene_plan` (schema: `schemas/artifacts/scene_plan.schema.json`).

## Process

1. **Style through the playbook.** Use `brand_kit.visual.style_playbook` for
   palette, typography, and motion — every shot must read as this brand.
2. **Reserve the logo safe-area.** Plan overlays so they never collide with the
   logo placement (`brand_kit.visual.logo.default_placement` + `safe_area_pct`),
   and keep key content inside the safe zone for the tightest target aspect.
3. **Pace for social.** Short shots, quick cuts, motion in the first beat. Use
   the brand `motion_signature`.
4. Keep the on-screen copy short and on-brand (it will be checked against
   `dont_words` at compose).

## Review focus

- Shots are styled by the brand playbook.
- Logo placement respects the brand safe-area.
- Pacing suits short-form social.
