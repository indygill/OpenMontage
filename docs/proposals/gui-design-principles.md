# GUI Design Principles (Read-Only Observer)

> Status: **Agreed direction** | Date: 2026-06-05
>
> The north star for the OpenMontage GUI. Pairs with
> `gui-readonly-observer.md` (scope + the files it reads) and the screen list
> therein. Figma frames are designed against this doc.

---

## The one fact that drives everything

The GUI is an **honest, read-only mirror of a file-backed, agent-driven, *gated*
production system.** It does not run the show — it reflects it and summons you
when needed. Every design decision falls out of taking that seriously.

## Principles

1. **Honest mirror — never imply control you don't have.** v1 renders truth from
   disk; no buttons that fake agency. If the GUI can't do a thing, it shows no
   control for it. A future [Approve] button earns its place only by *actually*
   doing something.
2. **Glanceable first, deep on demand.** Home answers *"what's running, what's
   done, what needs me"* in two seconds. Everything else is one click of
   progressive disclosure.
3. **Calm until it needs you.** Ambient and low-noise while the agent works. The
   **gate is the one moment it raises its voice** — unmissable, focused. Nothing
   else competes for that signal.
4. **Content-forward.** It's about the video. Renders, frames, storyboards get
   the room; chrome recedes. A dark, calm surface so imagery pops.
5. **Transparency is the feature.** Provenance, cost, provider/model, decisions —
   all visible. OpenMontage's governance ethos becomes the UI.
6. **Structure mirrors the data.** UI generated from the same artifacts/schemas
   the agent uses; layout reflects the production's real shape. No metaphors that
   fight the artifacts.
7. **Minimal, fast, file-backed.** An instrument, not an app suite — matching
   OpenMontage's own minimalism and the Studio ethos.

## Chosen direction

| Fork | Decision |
|---|---|
| **Aesthetic register** | **Editing-suite** — dark, cinematic, media-forward |
| **Orientation** | **Dashboard-first** (multi-project), drilling into one production |
| **Personality** | **Professional instrument** with a *subtle* production accent in language (film-strip stepper, "needs you") — flavor, not gimmick |
| **Liveness** | **Live / auto-updating** — it should feel like watching the crew work |

## Visual language — starting point (to refine in Figma)

A hypothesis for the frames, not a locked spec:

- **Surface:** dark charcoal base (near-black, not pure black), layered neutral
  greys for panels/cards; depth via subtle elevation, not heavy borders.
- **Accent:** a single warm signal colour (amber/gold direction) reserved for the
  *"needs you"* gate and primary status — used sparingly so it always means
  "look here." Everything else stays neutral.
- **Status language (consistent everywhere):** running, **needs-you** (accent),
  done, failed — one colour per state, used on the stepper, cards, and inbox
  identically.
- **Type:** clean humanist sans for UI; **monospace** for technical/data
  (paths, cost, model ids, seeds) to signal "this is real machine state."
- **Media:** let renders/frames/storyboards breathe — generous, edge-to-edge
  where it helps; chrome thin and quiet around them.
- **Motion:** restrained. Live updates fade in gently; the gate alert is the only
  element allowed to draw the eye.
- **Density:** comfortable, not cramped. Dashboard scannable; detail spacious.

## Out of scope for the look (v1)

Light mode, heavy theming, and brand-customisation are deferred — one confident
dark instrument first.
