# Script Director — Narrative Film Pipeline

## When to use

After the story outline. You write the **screenplay** — the spine that the
breakdown and shot list are derived from. This stage produces the `script`
artifact in its **screenplay** shape (`form: "screenplay"`).

## Output artifact

`script` with `form: "screenplay"` (schema: `schemas/artifacts/script.schema.json`).

The `script` artifact is dual-shape: `form: "narration"` carries timecoded
`sections[]` (used by explainer-style pipelines); `form: "screenplay"` carries
scene-based `scenes[]` (used here). Set `form: "screenplay"` and populate
`scenes[]`.

## Process

1. **One screenplay scene per story location/time unit.** Each scene has a
   `slugline` (e.g. `EXT. ISLAND JETTY - DAY`), an `action` description, the
   `cast` present (character ids), and optional `dialogue`.
2. **Map scenes to beats.** Every story beat should be covered by one or more
   screenplay scenes. Keep dialogue purposeful and sparse where the tone calls
   for it.
3. **Reference entities by id.** `cast` ids should resolve against the `cast`
   artifact; `location_id` is filled here when known, or finalized in breakdown.
4. **Give each scene a stable `id`.** These ids are the anchors the breakdown
   (`sequence_plan`) and shot list (`scene_plan`) reference. One screenplay scene
   fans out into multiple shots later.

## Ingest at altitude (high-value entry point)

A finished screenplay is the most common "enter mid-pipeline" case. If the user
supplies a script, normalize it with `lib/ingest.script_from_file(path)` — it
dispatches `.fdx` (Final Draft), `.fountain`/`.txt` (Fountain), and `.json` to
the right adapter and returns a screenplay-shaped `script` artifact
(`origin: user_provided`). For PDF, extract text first, then
`lib/ingest.fountain_to_script(text)`. Then:

- Adopt it with `origin: user_provided`.
- If mode is `lock`, **never rewrite it** — validate only.
- The downstream `breakdown` stage then runs in **reverse-derivation**: cast,
  locations, and sequences are extracted *from* this script.

## Review focus

- `form: "screenplay"` set and `scenes[]` populated.
- Screenplay scenes map cleanly to story beats.
- Sluglines are concrete; dialogue is purposeful.
- Provided/locked scripts are validated, never silently rewritten.
