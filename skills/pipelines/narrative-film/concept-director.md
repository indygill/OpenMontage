# Concept Director — Narrative Film Pipeline

## When to use

The opening creative gate. You turn the user's idea into a **story bible**:
logline, synopsis, themes, tone, format, and world. This is the narrative
equivalent of the `idea` stage — it replaces the marketing-shaped `brief`.

## Output artifact

`story_bible` (schema: `schemas/artifacts/story_bible.schema.json`).

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/story_bible.schema.json` | Artifact validation |
| Style | `styles/*.yaml` | The `world.style_playbook` links here |
| Tools | `web_search` | Light research for grounding the world |
| Optional | `source_media_review` | If the user provided reference material |

## Process

1. **Logline.** One specific sentence with a dramatic hook — a character, a
   want, and a complication. Reject vague premises.
2. **Synopsis.** 1–3 paragraphs covering the *full arc*, not just the setup.
3. **Themes & tone.** Name the themes the story is about and a precise tone
   (e.g. "slow-burn folk horror", not "dramatic").
4. **Format.** `kind` (short_film / feature / episode / teaser),
   `target_duration_seconds`, and `aspect_ratio`.
5. **World.** Concrete `setting`, `era`, and `rules` the story must obey, a
   prose `visual_bible`, and the `style_playbook` that best matches the tone.

## Ingest at altitude

If the user supplies a treatment, premise doc, or world bible: adopt it as the
`story_bible` (`origin: user_provided`). If they supply it as `lock`, validate
and use it verbatim — do not rewrite it; you may only fill genuinely missing
required fields and must flag what you added.

## Review focus

- Logline is one specific sentence with a clear hook.
- Synopsis conveys the full arc.
- World has concrete setting, era, and rules.
- Tone and format are explicit and consistent.
