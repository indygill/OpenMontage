# Brief Director — Brand Narrative Pipeline

## When to use

The lightweight per-video ask. You turn a short request ("a 15s reel announcing
feature X for Instagram") into a `brief`, applying the brand_kit so the brand
owner doesn't restate identity every time.

## Output artifact

`brief` (schema: `schemas/artifacts/brief.schema.json`) — reused as-is. It is
already marketing-shaped (`hook`, `key_points`, `core_message`, `cta`, `tone`,
`style`, `target_platform`, `target_duration_seconds`).

## Process

1. **Objective + key message** → `core_message` and `key_points`.
2. **Hook** → a scroll-stopping opener (social lives or dies in 2 seconds).
3. **Platform(s) + duration** → `target_platform` and `target_duration_seconds`.
   Multiple platforms are fine; the proposal turns them into aspect variants.
4. **CTA** → default to the brand_kit `compliance.required_cta` unless the user
   overrides it.
5. **Tone + style** → inherit from the brand_kit (`verbal.voice_tone`,
   `visual.style_playbook`). Do not invent a tone that conflicts with the brand.

Keep this fast. The brief is a thin ask; the brand_kit carries the identity.

## Review focus

- Objective, key message, and CTA are clear and on-brand.
- Platform(s) and duration are realistic for the message.
- The brief obeys the brand voice and references the brand_kit.
