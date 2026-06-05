# Scene Director (Shot List) — Narrative Film Pipeline

## When to use

After the breakdown. You turn each **screenplay scene** into a **shot list** —
the `scene_plan` artifact. Note the terminology: a screenplay *scene* (one
slugline) fans out into several *shots*; each item in `scene_plan.scenes[]` is a
shot/board, not a screenplay scene.

## Output artifact

`scene_plan` (schema: `schemas/artifacts/scene_plan.schema.json`).

## Process

1. **Fan out each screenplay scene** into deliberate shots. Vary shot size and
   movement to serve the drama — don't cover everything in one wide.
2. **Specify full `shot_language`** per shot: `shot_size`, `camera_movement`,
   `lens_mm`, `lighting_key`, `depth_of_field`, `color_temperature`. Add
   `shot_intent` (why this shot exists) and `narrative_role`.
3. **Link entities (narrative-film fields):**
   - `sequence_id` → a valid sequence in `sequence_plan`.
   - `location_id` → a valid entry in `locations`.
   - `cast` → character ids in `cast`; use `character_actions[].character_id`
     for acting beats.
   - **Unresolved cast/location references are a CRITICAL finding.**
4. **Mark hero/reveal moments** with `hero_moment: true`.
5. Use `required_assets[].source` to declare provenance: `generate`, `source`,
   `provided` (user material), or `record`.

## 5-aspect shot checklist

Every shot must specify: **Subject**, **Subject Motion**, **Scene** (overlays /
POV / setting / time), **Spatial Framing** (shot size / position / depth), and
**Camera** (speed / lens / height / angle / focus / movement). Marking an aspect
N/A is allowed but must be explicit; silent omission is forbidden.

## Ingest at altitude

If the user supplies storyboards or a shot list, reverse-map them into
`scene_plan` (`required_assets[].source: "provided"`), resolving cast/location
ids against the existing artifacts.

## Review focus

- Each screenplay scene fans out into deliberate shots with full shot_language.
- Every shot resolves cast and location ids and carries a `sequence_id`.
- Hero/reveal moments are explicit.
