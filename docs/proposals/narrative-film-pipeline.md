# Design Proposal: `narrative-film` Pipeline

> Status: **Approved design (rev 3)** | Author: agent-assisted design | Date: 2026-06-05
>
> Purpose: add a film-production hierarchy to OpenMontage so a user can drive a
> project the way a director thinks — *project → logline & synopsis → world →
> characters → story → script → breakdown → sequence → shot* — instead of the
> current single, linear, time-coded deliverable model. The pipeline must also
> let a user **enter or override at any altitude** with existing material.

---

## 1. Motivation

OpenMontage today models a production as **one linear, time-coded deliverable**:
a flat `scene_plan.scenes[]` list on a single timeline, fed by a marketing-shaped
`brief` (`hook`, `key_points`, `cta`, `target_platform`). Excellent for
explainers, trailers, and short-form social cuts.

It does **not** model the persistent, reusable, nested structure of a narrative
film project:

- a **world** (setting, era, rules, tone) that all scenes inherit,
- **characters** and **locations** as first-class, reusable entities,
- a **Story → Script → Sequence → Shot** chain rather than a flat scene list,
- the ability to **bring existing material in at any stage**, not just footage.

This adds that structure **as a new pipeline**, the OpenMontage-native extension
point — reusing checkpoints, approval gates, the reviewer meta-skill, the tool
registry/selectors, the cost tracker, and the already-rich `scene_plan` shot
vocabulary.

## 2. Pipeline order — grounded in professional practice

The order follows how real productions sequence work. Two principles drive it:

1. **The script is the spine.** A storyboard / shot list is a *visual
   interpretation of an already-written script*. So `script` precedes
   `scene_plan`. (OpenMontage's existing pipelines already do `script →
   scene_plan`; rev 1 of this doc wrongly inverted it.)
2. **Cast and locations are a *breakdown of the script*.** In live-action the
   1st AD extracts every speaking part and location *from the finished script*.
   But this is a **generative** pipeline, where character identity (reference
   images, consistency anchors) must be **locked before generation** — so we
   establish **principal cast + world** early (visual development), then run a
   fuller **breakdown** (locations, supporting cast, sequences) *after* the
   script. This is exactly how animation studios actually work ("Option B").

```
New project: "The Lighthouse Keeper"
  ├─ Concept        → logline, synopsis, world bible
  ├─ Characters     → principal cast + visual identity (locked for consistency)
  ├─ Story          → act / beat structure (the spine's outline)
  ├─ Script         → screenplay (THE spine — scenes, action, dialogue)
  ├─ Breakdown      → locations + supporting cast + sequences, derived FROM script
  ├─ Shot list      → individual shots per scene (the "scene_plan" artifact)
  └─ Produce → Edit → Finish → Publish
```

### Terminology note (decide deliberately)

In a screenplay a **scene** = one location/time unit (one slugline). OpenMontage's
`scene_plan` is really a **shot list / storyboard** — it breaks each script scene
into individual *shots* with camera/lens/lighting. The precise chain is:

```
story → script(scenes) → sequences(groups of scenes) → shots(scene_plan items)
```

What the artifact calls a "scene" is closer to a **shot / board**. Director skills
should use "shot" in user-facing language to avoid confusing a real director.

## 3. Mapping: desired hierarchy → OpenMontage artifacts

| User-facing layer | Artifact | New / existing | Notes |
|---|---|---|---|
| New Project | `projects/<name>/` workspace | **existing** | No change. |
| Logline & synopsis | `story_bible` (§4.1) | **new** | Replaces marketing `brief` for this pipeline. |
| World | `story_bible.world` (§4.1) | **new** | Narrative world; pairs with a visual style playbook. |
| Characters | `cast` (§4.2) | **new** | Generalizes the rigged-cartoon `character_design` schema. |
| Story | `story` (§4.4) | **new** | Act/beat outline; precedes the screenplay. |
| Script | `script` (extended, dual-shape) | **extend** | Carries BOTH timecoded `sections[]` (narration) and screenplay `scenes[]` (§4.7). |
| Locations | `locations` (§4.3) | **new** | Derived in breakdown. |
| Sequence | `sequence_plan` (§4.5) | **new** | Grouping layer, derived from script. |
| Shot | `scene_plan` (§4.6) | **extend** | Add `cast`, `location_id`, `sequence_id`. |
| Assets / Edit / Compose / Publish | `asset_manifest` / `edit_decisions` / `render_report` / `publish_log` | **existing** | Reused as-is. |

**Reuse wins already in the codebase:**

- `scene_plan.scenes[].character_actions[].character_id` already exists → cast
  references are a natural extension.
- `scene_plan.scenes[].required_assets[].source` already enumerates
  `["generate", "source", "provided", "record"]` → user-supplied assets are
  already a modeled provenance.
- `character_design.schema.json` is a working precedent for an entity-array
  artifact; `cast` follows the same shape.
- `lib/source_media_review.py` + the reviewer's CRITICAL gate already enforce
  "inspect user media before planning."

## 4. New & extended artifacts

> All schemas live in `schemas/artifacts/`, following existing conventions:
> `version: "1.0"` const, `additionalProperties: false`, a trailing `metadata`
> object, entity arrays keyed by a string `id`.

### 4.1 `story_bible` (new)

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
    "style_playbook": "clean-professional"
  },
  "reference_material": ["https://..."],
  "metadata": {}
}
```

Required: `version, title, logline, synopsis, tone, format, world`.

### 4.2 `cast` (new)

```jsonc
{
  "version": "1.0",
  "characters": [
    {
      "id": "thomas",
      "display_name": "Thomas Wake",
      "role": "protagonist",          // protagonist | supporting | minor | extra
      "tier": "principal",            // principal (early) | breakdown (from script)
      "description": "weathered keeper, 60s, salt-grey beard",
      "identity_method": "prompt",    // prompt | reference_image | lora | rig
      "reference_assets": ["assets/cast/thomas/ref01.png"],
      "wardrobe": ["oilskin coat", "wool cap"],
      "consistency_anchors": ["deep-set eyes", "scar over left brow"],
      "constraints": ["always lit warm"],
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

`tier` distinguishes principals (locked early for generative consistency) from
characters added during the script breakdown. `identity_method` v1 ships `prompt`
+ `reference_image`; `lora`/`rig` are forward hooks (the latter bridges to the
character-animation pipeline).

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
      "reference_assets": ["assets/locations/lamp_room/ref01.jpg"],
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

### 4.5 `sequence_plan` (new) — grouping layer, derived from the script

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
      "scene_ids": ["sc_001", "sc_002"]
    }
  ],
  "metadata": {}
}
```

### 4.6 `scene_plan` (extend existing) — the shot list

Add three optional, **backward-compatible** fields to each `scene_plan.scenes[]`
item (existing pipelines ignore them):

```jsonc
{
  "sequence_id": "seq_arrival",   // NEW — owning sequence
  "location_id": "lamp_room",     // NEW — reference into locations
  "cast": ["thomas"]              // NEW — character ids in this shot
  // all existing fields (shot_language, narrative_role, character_actions,
  //   required_assets, start/end_seconds) unchanged
}
```

No existing field is removed or made required.

### 4.7 `script` (extend existing) — dual-shape, supports both forms

The existing `script` artifact is timecoded narration: `sections[]` with
`start/end_seconds`, `text`, `enhancement_cues`. A screenplay is scene-based
(slugline / action / dialogue) and has no timecode. **We support both** in one
artifact so a single schema serves the explainer family *and* the narrative-film
family. `form` declares which shape is authoritative; the other may be present
(e.g. narration auto-derived from a screenplay).

```jsonc
{
  "version": "1.0",
  "title": "The Lighthouse Keeper",
  "form": "screenplay",              // "narration" | "screenplay"
  "total_duration_seconds": 240,     // required for narration; optional for screenplay
  "sections": [ /* existing timecoded narration shape — unchanged */ ],
  "scenes": [                         // NEW — screenplay shape
    {
      "id": "sc_001",
      "sequence_id": "seq_arrival",
      "slugline": "EXT. ISLAND JETTY - DAY",
      "location_id": "lamp_room",     // resolves against locations
      "action": "The supply boat pulls away. Thomas stands alone with his trunk.",
      "cast": ["thomas"],             // resolves against cast
      "dialogue": [
        { "character_id": "thomas", "line": "Just me, then.", "parenthetical": "to himself" }
      ]
    }
  ],
  "metadata": {}
}
```

Rules: exactly one of `sections[]` / `scenes[]` must be non-empty and must match
`form`. Screenplay `scenes[].id` are the anchors the `breakdown` and `scene_plan`
(shot list) stages reference — i.e. one screenplay scene fans out into multiple
shots. Existing pipelines set `form: "narration"` and are unaffected.

## 5. Pipeline manifest: `pipeline_defs/narrative-film.yaml`

Follows the cinematic manifest structure (orchestration block, `required_skills`,
`compatible_playbooks`, `stages[]`). Stage order = Option B:

| Stage | Produces | Gate (`human_approval_default`) | Key inputs |
|---|---|---|---|
| `concept` | `story_bible` | **true** | (idea) |
| `characters` | `cast` (principals + identity) | **true** | story_bible |
| `story` | `story` (acts/beats) | **true** | story_bible, cast |
| `script` | `script` (screenplay) | **true** | story, cast |
| `breakdown` | `locations`, `sequence_plan`, finalized `cast` | **true** | script |
| `scene_plan` | `scene_plan` (shot list) | **true** | script, breakdown |
| `assets` | `asset_manifest` | false | scene_plan |
| `edit` | `edit_decisions` | false | scene_plan, asset_manifest |
| `compose` | `render_report`, `final_review` | false | edit_decisions |
| `publish` | `publish_log` | true | render_report |

Notes:
- Six creative gates up front is intentional — this pipeline is for users who
  *want* to shape every layer. `default_checkpoint_policy: guided`. A future
  "fast" policy could auto-advance early gates.
- `reference_input.supported: true` (reuse the reference-video analyst path).
- `breakdown` and `scene_plan` list `source_media_review` in `tools_available`,
  so provided footage/stills are inspected before planning.

## 6. Director skills (`skills/pipelines/narrative-film/`)

```
executive-producer.md   concept-director.md     character-director.md
story-director.md        script-director.md      breakdown-director.md
scene-director.md        asset-director.md       edit-director.md
compose-director.md      publish-director.md
```

`scene-director.md` reuses the existing 5-aspect shot checklist and adds:
"resolve every `cast` id against `cast` and every `location_id` against
`locations`; unresolved references are a CRITICAL finding."

## 7. Ingest at any altitude (existing-material support)

**Principle: every artifact is both an entry point and an override point.**
Professionally, people join a production at any phase holding the prior phase's
deliverables. The pipeline must support: *ingest at altitude N → derive
everything above N by extraction → generate everything below N.*

### 7.1 Entry-point matrix

| You bring | Enter at | Back-fill upstream by | Pipeline still does |
|---|---|---|---|
| just an idea | `concept` | — | everything |
| treatment / world bible | `story` | adopt as `story_bible` | story → … |
| character designs + refs | (seeds `cast`) | — | the rest |
| **a finished script** | `breakdown` | **extract cast / locations / sequences FROM the script** | board → produce → finish |
| storyboards / shot list | `scene_plan` | reverse-map boards → `scene_plan` | produce → finish |
| footage / stills / VO / music | `assets` | `source_media_review` (exists) | edit → finish |
| a rough cut / EDL / timeline XML | `edit` | ingest timeline → `edit_decisions` | finish / color / titles |
| a near-final | `compose` | — | color, titles, delivery |

The critical row is **"a finished script"**: entering there must run the
**breakdown in reverse** — derive cast/locations/sequences *by extraction* —
rather than leaving the upstream entities empty. "Derive upward, generate
downward."

### 7.2 Three modes of "provided"

Provided material carries intent; the agent must honor it:

| Mode | Meaning | Agent behavior |
|---|---|---|
| **lock** | "This is THE script / cast / cut — don't touch it." | Validate, adopt verbatim, **never regenerate or silently overwrite.** |
| **seed** | "Here's a draft — refine it." | Use as the starting artifact, improve, gate as normal. |
| **reference** | "Inform the work, not the deliverable." | Influences only (like the existing reference-video / temp-score pattern); never copied. |

### 7.3 Mechanics to add

1. **Provided-artifact convention** — drop a finished/partial artifact (or raw
   material) into the project with a manifest entry `{ artifact, mode }`.
   Provenance recorded as `origin: user_provided`, visible downstream.
2. **Ingestion adapters** *(the real net-new work)* — normalize external formats
   into canonical artifacts: `.fdx` / Final Draft / PDF → `script`; storyboard
   image folder → `scene_plan`; EDL / Premiere/FCP XML → `edit_decisions`; image
   folder → `cast` / `locations` refs.
3. **Reverse-derivation skills** — script → breakdown (cast/locations/sequences);
   cut → scene list. So entering mid-pipeline still populates upstream context.
4. **Lock enforcement + conflict reconciliation** — a `locked` artifact is never
   regenerated; if provided pieces contradict (a character in the bible who
   never appears in the locked script), the reviewer raises a finding instead of
   silently choosing.

### 7.4 What's already free

- `checkpoint.get_next_stage()` — resuming mid-pipeline is the core loop; entering
  at stage N is the same mechanism.
- `source_media_review` — media ingestion + "inspect before planning" gate exists.
- `required_artifacts_in` / `optional_artifacts_in` — a provided artifact simply
  satisfies a stage input early.
- Governance "No Unilateral Substitutions / no silent swaps" already forbids
  overwriting user creative material — lock semantics extend a rule that exists.

## 8. Reuse vs. net-new (scope summary)

**Net-new:**
- 5 new schemas: `story_bible`, `cast`, `locations`, `story`, `sequence_plan`.
- `script` screenplay extension + 3 additive `scene_plan` fields.
- 1 manifest: `narrative-film.yaml`.
- ~11 director skills + ingestion/reverse-derivation skills.
- Ingestion adapters (parsers) for `.fdx`/PDF, storyboard folders, EDL/XML.
- Provided-artifact provenance/mode convention.
- Contract tests in `tests/contracts/` + schema fixtures.

**Reused unchanged:** checkpoint system, reviewer, cost tracker, tool registry,
selectors, `asset_manifest` / `edit_decisions` / `render_report` / `publish_log`,
`source_media_review`, style playbooks, composition runtimes (Remotion /
HyperFrames / FFmpeg).

## 9. Open questions for the reviewer

1. **Bible vs. brief.** `story_bible` as its own artifact (proposed) vs. extending
   `brief`. *Recommendation: separate artifact.* — **agreed: separate.**
2. **Script as screenplay.** — **resolved: support both.** One `script` artifact
   carries both shapes (§4.7): existing timecoded `sections[]` (narration) plus a
   new screenplay `scenes[]` block, selected by `form`. No separate `screenplay`
   artifact.
3. **Cast identity methods.** v1 ships `prompt` + `reference_image`; stub
   `lora`/`rig`. *Recommendation: yes.* — **agreed (Option B).**
4. **Multi-deliverable scope.** One render per project (like today) vs. optional
   per-sequence renders. *Defer to a later compose-stage extension.*
5. **Pipeline name.** `narrative-film` vs `film` vs `story`.
6. **Ingestion adapter scope for v1.** — **resolved.** Ship `.fdx`/PDF → script
   and image-folder → `cast`/`locations` refs first; EDL / timeline-XML cut
   ingestion in a later phase.

## 10. Suggested implementation phases

- **Phase 1 — schemas + manifest:** 5 schemas, the `scene_plan` + `script`
  extensions, `narrative-film.yaml`, contract tests. Pipeline is discoverable and
  validates.
- **Phase 2 — director skills:** author the stage skills; wire reference +
  source-media paths.
- **Phase 3 — ingest at altitude:** provided-artifact convention, the first
  ingestion adapters (§9.6), and reverse-derivation skills (script → breakdown).
- **Phase 4 — dogfood:** run a short film end-to-end; tune gates; document in
  `README.md` / `PROJECT_CONTEXT.md` / `AGENT_GUIDE.md` pipeline tables.

---

*Design document only — no schemas, manifests, or skills created yet. §9.2
(dual-shape script) and §9.6 (adapter priority) are resolved. Remaining open:
§9.4 (per-sequence renders, deferred) and §9.5 (pipeline name). Phase 1 is ready
to begin.*
