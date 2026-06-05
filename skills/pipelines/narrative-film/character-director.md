# Character Director — Narrative Film Pipeline

## When to use

After the proposal. You establish the **principal cast** and lock their visual
identity so generated shots stay consistent across the whole film. Supporting
and minor characters come later, from the script breakdown.

## Output artifact

`cast` (schema: `schemas/artifacts/cast.schema.json`).

## Why this is early (generative consistency)

Unlike live-action, where casting follows the script breakdown, a generative
pipeline must lock principal identity *before* shots are generated — otherwise a
character's face/wardrobe drifts shot to shot. So principals (`tier: principal`)
are defined here; the breakdown stage adds `tier: breakdown` characters later.

## Process

1. **Identify principals** from the story_bible — protagonist, antagonist, key
   supporting roles. Give each a distinct `role` and silhouette.
2. **Choose `identity_method`** per character:
   - `prompt` — identity carried by a repeated, specific text description.
   - `reference_image` — 1+ provided/locked reference images (preferred for
     strong consistency). v1 supports `prompt` and `reference_image`.
   - `lora` / `rig` — forward hooks; only if those toolpaths are configured.
3. **Lock consistency anchors** — verbatim descriptors (eye shape, scar,
   wardrobe) to repeat across shots. These are the single biggest lever on
   cross-shot consistency.
4. Record any provided reference images with `origin: user_provided`.

## Ingest at altitude

If the user supplies character designs or reference images, adopt them
(`origin: user_provided`). For a folder of reference images, use
`lib/ingest.image_folder_to_reference_assets(folder, project_dir)` to enumerate
them into `reference_assets` paths. Locked references must be used verbatim.
Image generation tools may produce identity sheets only with user approval (paid).

## Review focus

- Principals have distinct roles and silhouettes.
- Each principal has consistency anchors or reference images.
- `identity_method` is realistic for available tools.
