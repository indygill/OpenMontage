# GUI Concept: Read-Only Project Observer (v1)

> Status: **Concept note** | Date: 2026-06-05 | Speculative — not scheduled
>
> Captures a deliberately minimal first GUI for OpenMontage. **This changes
> nothing about how OpenMontage works.** It is a separate, read-only layer that
> renders the files OpenMontage already writes and notifies you at gates. The
> agent (Claude Code / Agent SDK) remains the sole orchestrator and the sole
> writer.

---

## Scope (v1)

One live, **read-only** dashboard over `projects/` + `pipelines/` that does two
jobs — both powered by the same thing: *reading the on-disk state.*

1. **Replace the Finder / QuickTime / text-editor shuffle.** Browse projects,
   preview the render inline, see assets as a gallery, read artifacts (script,
   scene_plan, brand_kit, …) as friendly views, watch the cost gauge. Project
   management without spelunking folders.
2. **Surface + alert the human gate.** Watch checkpoint status; when a stage
   flips to `awaiting_human`, light it up ("scene plan needs you") and show the
   artifact summary + reviewer findings + cost snapshot.

Job 1 = *"show me the project."* Job 2 = *"tell me when it needs me."*

## Hard constraints (what keeps this trivial)

- **No changes to OpenMontage.** Pipelines, skills, tools, schemas, and the
  agent contract are untouched. Every file the GUI reads already exists.
- **Read-only. The GUI never writes** a checkpoint or artifact, never injects a
  message, never controls the agent.
- **Single writer = the agent.** Because the GUI never writes, it cannot race a
  live session. Approval still happens **in the conversation** — the user types
  "approve" / feedback to the agent, exactly as today.

## What it reads (the on-disk surfaces)

| Surface | Path | Rendered as |
|---|---|---|
| Project list | `projects/<name>/` | dashboard cards |
| Stage state | `pipelines/<project_id>/checkpoint_<stage>.json` (`status: completed \| failed \| awaiting_human \| in_progress`) | the stage stepper + gate alerts |
| Artifacts | `projects/<name>/artifacts/*.json` (brief, story_bible, cast, locations, script, scene_plan, asset_manifest, edit_decisions, render_report, brand_kit) | schema-driven viewers |
| Media | `projects/<name>/assets/{images,video,audio,music}/`, `subtitles.srt` | gallery / players |
| Deliverable | `projects/<name>/renders/final.mp4` (+ `role: derivative` variants) | inline player w/ platform tabs |
| Cost / decisions | `cost_log`, `decision_log` artifacts | budget gauge, audit trail |
| Capabilities | `registry.provider_menu_summary()` | settings / "what's configured" |

Existing read helpers it would call (no new APIs required):
`lib/pipeline_loader` (`list_pipelines`, `load_pipeline`, `get_stage_order`),
`lib/checkpoint` (`read_checkpoint`, `get_next_stage`), `schemas/artifacts`
(`load_schema` for form generation), `tools/cost_tracker`, `tools/tool_registry`.

## Alert mechanism

Poll the checkpoint files (mirrors how OpenMontage tools already poll, e.g. the
ComfyUI/`/history`-style pull model). On a transition to `awaiting_human`
(or `failed`, or a render appearing), surface a banner/badge — and optionally a
push notification ("go approve in your agent session"). It is always a *"go
look,"* never an *"approve for you."*

## Suggested shape (matches the file-backed ethos)

A small stdlib `http.server` + single-file HTML frontend (no build, no DB),
serving read endpoints like `/api/projects`, `/api/project/<name>`,
`/api/checkpoints/<name>`, `/api/render/<name>`. Same minimalism as a thin
file-backed tool; runs locally alongside the agent.

## Explicitly out of scope for v1 (noted for later)

- **An [Approve] button that drives the agent.** That requires the "glue" hop:
  either (A) inject a message into a live agent session via the Agent SDK, or
  (B) write a decision to disk + relaunch the agent (`get_next_stage` reads it).
  Option B would want one small **additive** approval/decision record (the only
  thing that touches OpenMontage). Deferred — v1 leaves approval in the
  conversation.
- Editing artifacts and regenerating downstream stages from the GUI.
- Multi-user review / comments on artifacts.

## Why start here

It delivers most of the daily value (a project dashboard + "it needs you"
alerts) with **zero integration risk and zero changes to the core** — and it
leaves a clean upgrade path to an interactive cockpit later.
