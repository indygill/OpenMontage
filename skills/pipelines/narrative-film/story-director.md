# Story Director — Narrative Film Pipeline

## When to use

After principal cast. You build the **narrative spine's outline**: acts and
beats. This is the *what-happens* structure; the screenplay is written from it
in the next stage. No timecode here.

## Output artifact

`story` (schema: `schemas/artifacts/story.schema.json`).

## Process

1. **Pick a structure** appropriate to the format and duration: `three_act`,
   `five_act`, `eight_sequence`, `hero_journey`, or `freeform`.
2. **Write acts** — each with a clear `summary` of its dramatic movement.
3. **Write beats** within acts — ordered, each with a `summary` and a dramatic
   `function` (establish, inciting_incident, turn, midpoint, climax, resolution).
4. **Escalate.** Each beat should raise stakes toward a clear climax. Beats must
   serve the logline and themes from the story_bible, not decorate.

## Ingest at altitude

If the user supplies a beat sheet or outline, adopt it as `story`
(`origin: user_provided`). If a full script is provided instead, skip this stage —
the `story` can be extracted during breakdown or left implicit; do not invent a
conflicting outline.

## Review focus

- Structure matches format and duration.
- Beats escalate cleanly toward a clear climax.
- Beats serve the logline and theme.
