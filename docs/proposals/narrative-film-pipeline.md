# Design Proposal: `narrative-film` Pipeline

> Status: **Draft for review** | Author: agent-assisted design | Date: 2026-06-05
>
> Purpose: add a film-production hierarchy to OpenMontage so a user can drive a
> project the way a director thinks — *project → logline & synopsis → world →
> characters & locations → story → sequence → scene* — instead of the current
> single, linear, time-coded deliverable model.

---

## 1. Motivation

OpenMontage today models a production as **one linear, time-coded deliverable**:
a flat `scene_plan.scenes[]` list on a single timeline, fed by a marketing-shaped
`brief` (`hook`, `key_points`, `cta`, `target_platform`). That is excellent for
explainers, trailers, and short-form social cuts.

It does **not** model the persistent, reusable, nested structure of a narrative
film project:

- a **world** (setting, era, rules, tone) that all scenes inherit,
- **characters** and **locations** as first-class, reusable entities referenced
  by ID across many scenes,
- a **Story → Sequence → Scene** tree rather than a flat scene list.

This proposal adds that structure **as a new pipeline**, the OpenMontage-native
extension point — not as a rewrite of the existing pipelines. Everything reuses
the current machinery: checkpoints, approval gates, the reviewer meta-skill, the
tool registry/selectors, the cost tracker, and the already-rich `scene_plan`
shot vocabulary.

## 2. Target user experience

```
New project: "The Lighthouse Keeper"
  ├─ Logline & synopsis      → one sentence + a paragraph, themes, tone
  ├─ World                   → setting, era, rules, visual + narrative bible
  ├─ Characters & Locations  → reusable cast + place entities (with refs)
  ├─ Story                   → act/beat structure across the whole piece
  ├─ Sequences               → ordered groups of scenes (a "chapter" of story)
  └─ Scenes                  → individual shots, each referencing cast + location
```

The user tunes at **every** gate (approve / revise / abort), exactly like the
existing creative stages. Existing assets (footage, stills, music) inject through
the same `source_media_review` + `required_assets.source: "provided"` path the
footage-led pipelines already use.

## 3. Mapping: desired hierarchy → OpenMontage artifacts

| User-facing layer | Artifact | New / existing | Notes |
|---|---|---|---|
| New Project | `projects/<name>/` workspace | **existing** | No change. |
| Logline & synopsis | `story_bible` (§4.1) | **new** | Replaces marketing-shaped `brief` for this pipeline. |
| World | `story_bible.world` (§4.1) | **new** | Narrative world; pairs with a visual **style playbook**. |
| Characters | `cast` (§4.2) | **new** | Generalizes the existing `character_design` schema (which is rigged-cartoon-specific). |
| Locations | `locations` (§4.3) | **new** | No equivalent exists today. |
| Story | `story` (§4.4) | **new** | Act/beat structure; distinct from the timecoded `script`. |
| Sequence | `sequence_plan` (§4.5) | **new** | Grouping layer between story and scenes. |
| Scene | `scene_plan` (§4.6) | **extend existing** | Add `cast`, `location_id`, `sequence_id`. Already has `character_actions[].character_id` and `required_assets[].source:"provided"`. |
| Assets / Edit / Compose | `asset_manifest` / `edit_decisions` / `render_report` | **existing** | Unchanged; reused as-is. |

**Key reuse wins already present in the codebase:**

- `scene_plan.scenes[].character_actions[].character_id` already exists → cast
  references are a natural extension, not a new concept.
- `scene_plan.scenes[].required_assets[].source` already enumerates
  `["generate", "source", "provided", "record"]` → user-supplied assets are
  already a modeled provenance.
- `character_design.schema.json` is a working precedent for an entity-array
  artifact; `cast` follows the same shape with film-oriented fields.
- `lib/source_media_review.py` + the reviewer's CRITICAL gate already enforce
  "inspect user media before planning" — no new enforcement logic needed.

## 4. New & extended artifacts

> All schemas live in `schemas/artifacts/` and follow the existing conventions:
> `version: "1.0"` const, `additionalProperties: false`, a trailing `metadata`
> object, and entity arrays keyed by a string `id`.

### 4.1 `story_bible` (new) — replaces `brief` for this pipeline

```jsonc
{
  "version": "1.0",
  "title": "The Lighthouse Keeper",
  "logline": "A grieving keeper discovers the light is talking back.",
  "synopsis": "<1–3 paragraph prose summary>",
  "themes": ["isolation", "grief", "duty"],
  "tone": "slow-burn folk horror",
  "format": { "kind": "short_film", "target_duration_seconds": 240, "aspect_ratio": "2.39:1" },
  "world": {
    "setting": "a remote North Atlantic island",
    "era": "1890s",
    "rules": ["no electricity", "the light must never go out"],
    "visual_bible": "cold blues, oil-lamp warmth, heavy grain",
    "style_playbook": "clean-professional"          // links to styles/*.yaml
  },
  "reference_material": ["https://..."],             // reuses existing convention
  "metadata": {}
}
```

Required: `version, title, logline, synopsis, tone, format, world`.

### 4.2 `cast` (new) — reusable characters

Generalizes `character_design` so it covers live-action / generated / rigged
characters, not just SVG rigs.

```jsonc
{
  "version": "1.0",
  "characters": [
    {
      "id": "thomas",
      "display_name": "Thomas Wake",
      "role": "protagonist",
      "description": "weathered keeper, 60s, salt-grey beard",
      "identity_method": "prompt",        // prompt | reference_image | lora | rig
      "reference_assets": ["assets/cast/thomas/ref01.png"],   // optional, provided
      "wardrobe": ["oilskin coat", "wool cap"],
      "consistency_anchors": ["deep-set eyes", "scar over left brow"],
      "constraints": ["always lit warm"],
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

`identity_method` is deliberately open: `prompt` and `reference_image` work with
today's image/video generators; `lora` / `rig` are forward-looking hooks (the
latter bridges to the existing character-animation pipeline).

### 4.3 `locations` (new)

```jsonc
{
  "version": "1.0",
  "locations": [
    {
      "id": "lamp_room",
      "display_name": "The Lamp Room",
      "description": "cramped iron gallery around the rotating lens",
      "time_of_day": "night",
      "weather": "storm",
      "reference_assets": ["assets/locations/lamp_room/ref01.jpg"],  // optional, provided
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

### 4.4 `story` (new) — narrative structure, not timecode

```jsonc
{
  "version": "1.0",
  "structure": "three_act",
  "acts": [
    {
      "id": "act_1",
      "label": "Arrival",
      "summary": "Thomas takes the post; the light unsettles him.",
      "beats": [
        { "id": "b1", "summary": "Boat leaves; he is alone.", "function": "establish" }
      ]
    }
  ],
  "metadata": {}
}
```

Distinct from `script`: `story` is the *what-happens* spine; the timecoded
`script` (narration/dialogue/title-cards) is generated **from** it later, reusing
the existing `script` artifact unchanged.

### 4.5 `sequence_plan` (new) — the grouping layer

```jsonc
{
  "version": "1.0",
  "sequences": [
    {
      "id": "seq_arrival",
      "order": 1,
      "label": "The Arrival",
      "act_id": "act_1",
      "summary": "Thomas reaches the island and climbs to the lamp.",
      "primary_location_id": "lamp_room",
      "cast_ids": ["thomas"],
      "scene_ids": ["sc_001", "sc_002"]      // populated when scene_plan is built
    }
  ],
  "metadata": {}
}
```

### 4.6 `scene_plan` (extend existing)

Add three optional fields to each item in `scene_plan.scenes[]` — **additive and
backward-compatible** (existing pipelines ignore them):

```jsonc
{
  "sequence_id": "seq_arrival",       // NEW — which sequence this scene belongs to
  "location_id": "lamp_room",         // NEW — reference into locations artifact
  "cast": ["thomas"]                  // NEW — character ids present in this scene
  // ...all existing fields (shot_language, narrative_role, character_actions,
  //    required_assets, start/end_seconds) remain unchanged
}
```

No existing field is removed or made required. `character_actions[].character_id`
continues to work and should validate against `cast`.

## 5. New pipeline manifest: `pipeline_defs/narrative-film.yaml`

Follows the cinematic manifest structure (orchestration block, `required_skills`,
`compatible_playbooks`, `stages[]` with `produces` / `required_artifacts_in` /
`human_approval_default` / `review_focus` / `success_criteria`).

| Stage | Produces | Gate (`human_approval_default`) |
|---|---|---|
| `concept` | `story_bible` (logline, synopsis, world) | **true** |
| `world_and_cast` | `cast`, `locations` | **true** |
| `story` | `story` (acts/beats) | **true** |
| `sequence_breakdown` | `sequence_plan` | **true** |
| `scene_plan` | `scene_plan` (extended) | **true** |
| `script` | `script` (timecoded, from story) | **true** |
| `assets` | `asset_manifest` | false |
| `edit` | `edit_decisions` | false |
| `compose` | `render_report`, `final_review` | false |
| `publish` | `publish_log` | true |

Notes:
- `reference_input.supported: true` (reuse the reference-video analyst path).
- `source_media_review` listed in `world_and_cast` and `scene_plan` stage
  `tools_available`, so provided footage/stills are inspected before planning.
- Five creative gates up front is intentional — this pipeline is for users who
  *want* to shape each layer. A `default_checkpoint_policy: guided` keeps it that
  way; a future "fast" policy could auto-advance early gates.

## 6. New director skills

One per stage, under `skills/pipelines/narrative-film/`, matching the existing
director-skill format (When To Use / Prerequisites table / Process / checklist):

```
executive-producer.md      concept-director.md        world-cast-director.md
story-director.md          sequence-director.md       scene-director.md
script-director.md         asset-director.md          edit-director.md
compose-director.md        publish-director.md
```

The `scene-director.md` reuses the existing 5-aspect shot checklist and adds:
"resolve every `cast` id against the `cast` artifact and every `location_id`
against `locations`; unresolved references are a CRITICAL finding."

## 7. Existing-asset injection (no new mechanism)

This is fully covered by what's already in the repo:

1. User drops files in the project (footage/stills) and/or music in `music_library/`.
2. `world_and_cast` + `scene_plan` stages run `lib/source_media_review.review_source_media()`;
   the reviewer raises CRITICAL if user media exists but wasn't inspected.
3. `cast[].reference_assets` / `locations[].reference_assets` capture provided refs.
4. `scene_plan.scenes[].required_assets[].source: "provided"` marks them in-plan.
5. `asset_manifest` records provenance (`subtype`, `license: "user-provided"`,
   `original_url`) — already supported.

## 8. Reuse vs. net-new (scope summary)

**Net-new (the actual work):**
- 5 new schemas: `story_bible`, `cast`, `locations`, `story`, `sequence_plan`.
- 3 additive fields on `scene_plan.schema.json`.
- 1 manifest: `narrative-film.yaml`.
- ~11 director skills.
- Contract tests in `tests/contracts/` + schema fixtures.

**Reused unchanged:** checkpoint system, reviewer, cost tracker, tool registry,
selectors, `script` / `asset_manifest` / `edit_decisions` / `render_report` /
`publish_log` artifacts, `source_media_review`, style playbooks, composition
runtimes (Remotion / HyperFrames / FFmpeg).

## 9. Open questions for the reviewer (you)

1. **Bible vs. brief.** Should `story_bible` be its own artifact (proposed), or
   should we extend `brief` with optional narrative fields? Separate artifact is
   cleaner but adds a schema; extending `brief` reuses more but muddies the
   marketing-oriented schema. *Recommendation: separate artifact.*
2. **Story vs. script separation.** Keep `story` (beats) and `script` (timecode)
   as two stages (proposed), or collapse into one? Two stages give a cleaner
   "what happens" → "how it's narrated" gate. *Recommendation: keep separate.*
3. **Cast identity methods.** For v1, support only `prompt` + `reference_image`
   (works with current generators), and stub `lora` / `rig` as forward hooks?
   *Recommendation: yes — ship the two that work today.*
4. **Multi-deliverable scope.** This proposal keeps one render output per project
   (like today). Do you also want per-sequence renders (each sequence as its own
   clip)? That's a compose-stage extension we can add later.
5. **Naming.** `narrative-film` vs `film` vs `story` as the pipeline name.

## 10. Suggested implementation phases

- **Phase 1 (schemas + manifest):** land the 5 schemas, the `scene_plan`
  extension, and `narrative-film.yaml` with contract tests. Pipeline is
  discoverable and validates, even before all skills are polished.
- **Phase 2 (director skills):** author the 11 stage skills; wire the reference
  and source-media paths.
- **Phase 3 (dogfood):** run a short film end-to-end, tune the gates, document in
  `README.md` / `PROJECT_CONTEXT.md` / `AGENT_GUIDE.md` pipeline tables.

---

*This is a design document only — no schemas, manifests, or skills have been
created yet. Review §9 decisions before implementation begins.*
