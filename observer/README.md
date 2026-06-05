# OpenMontage Observer

A **read-only** dashboard over `projects/` + `pipelines/`. It renders the screens
designed in Figma — Projects dashboard, Project overview — directly from the
files OpenMontage already writes, and **never writes anything itself**. The agent
stays the sole orchestrator and writer; you approve gates in your agent session.
The Observer just *shows you the project* and *tells you when a gate needs you*.

See the design docs: `docs/proposals/gui-readonly-observer.md` (scope) and
`docs/proposals/gui-design-principles.md` (look & feel).

## Run

```bash
python observer/server.py            # → http://localhost:8137
python observer/server.py --port 9000
```

Stdlib only — no build, no dependencies, no database. Open the URL and it polls
`/api/state` every few seconds. If no projects exist on disk yet, it falls back
to bundled **sample data** so it renders out of the box.

## How it works

```
browser (app/index.html)  ──poll──>  /api/state  ──reads──>  projects/ + pipelines/
        renders components                (server.py)         (checkpoints, artifacts)
```

- **`server.py`** — stdlib `http.server`. Serves the single-file frontend and a
  read-only `/api/state` that reflects on-disk state. Reuses `lib.checkpoint`
  (`get_pipeline_stages`, `CANONICAL_STAGE_ARTIFACTS`) to map checkpoints →
  per-stage status. Never writes; one bad project can't break the dashboard.
- **`app/index.html`** — single file: the dark editing-suite design system (CSS
  tokens) + a component library + the screens, rendered from data. No framework,
  no build step.
- **`app/sample.js`** — sample `window.SAMPLE_STATE` (same shape as `/api/state`)
  so the UI works standalone.

## Component architecture

Reused-once → component; loop output → component (cards → `Card`). Everything is
a small factory function returning a DOM node, composed with the `h()` helper:

| Component | Reused as |
|---|---|
| `Dot`, `Pill`, `StatusPill`, `PipelinePill` | status/provenance chips everywhere |
| `Thumb` | filmic gradient thumbnails |
| `MiniStepper` / `BigStepper` | the film-strip pipeline at card- and page-scale |
| `NavItem`, `Rail` | the left nav |
| `Panel`, `FactRow` | sidebar cards |
| **`ProjectCard`** | the dashboard grid's loop output |
| **`GateHero`** | the loud "needs you" gate |

Screens (`DashboardScreen`, `ProjectScreen`) are composed entirely from those.

## API

| Method | Path | Returns |
|---|---|---|
| GET | `/api/state` | `{ projects: [...] }` — read-only snapshot |
| GET | `/api/health` | `{ ok: true, readonly: true }` |
| GET | `/` , `/sample.js` | the frontend |

## Screens (all wired)

App-level routes plus a tabbed project workspace — every Figma screen is in:

| Route | Screen |
|---|---|
| `#/` | Dashboard (needs-you hero + project grid) |
| `#/inbox` | Inbox (cross-project alert queue) |
| `#/renders` | Renders (finished-deliverable grid) |
| `#/capabilities` | Capabilities (runtimes, provider ratios, quick setup) |
| `#/p/<name>/overview` | Project — stepper + gate + sidebar |
| `#/p/<name>/shots` | Storyboard (scene_plan shot grid) |
| `#/p/<name>/assets` | Assets gallery (provenance badges, waveforms) |
| `#/p/<name>/render` | Render/Player (player + variant tabs + outputs) |
| `#/p/<name>/cost` | Cost & Decisions (gauge, line items, decision log) |
| `#/p/<name>/activity` | Activity (live agent feed) |

Tabs with no data yet fall back to an honest empty state (e.g. "No render yet —
production is at assets."). A headless render harness exercises all routes.

> Out of scope for v1 (by design): any **[Approve]** button. Approving from the
> GUI would require the agent-glue described in
> `docs/proposals/gui-readonly-observer.md` (§ deferred). For now you approve in
> the agent session; the Observer surfaces the gate.
