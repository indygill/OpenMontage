# Edit Director — Narrative Film Pipeline

## When to use

After assets exist. You make concrete cut decisions — order, durations,
transitions, overlays, subtitle and music timing — and record them in
`edit_decisions`. Technical stage; auto-proceeds.

## Output artifact

`edit_decisions` (schema: `schemas/artifacts/edit_decisions.schema.json`).

## Process

1. **Preserve dramatic pacing.** Cut to serve each sequence's emotional movement;
   don't overcut hero/reveal shots. Respect the sequence ordering from
   `sequence_plan`.
2. **Carry `render_runtime` unchanged.** Copy the `render_runtime` locked at
   proposal into `edit_decisions` verbatim. A silent runtime swap here is a
   CRITICAL governance violation.
3. **Audio & titles.** Time title cards and music cues to reinforce beats. Keep
   dialogue/narration intelligible over music.
4. Cover the full planned runtime; no gaps.

## Ingest at altitude

If the user supplies a rough cut / EDL / timeline XML, ingest it into
`edit_decisions` (`origin: user_provided`) rather than re-cutting from scratch;
locked cuts are used verbatim.

## Review focus

- Pacing preserved; strong moments not overcut.
- `render_runtime` carried unchanged from the locked choice.
- Edit decisions cover the full runtime.
