# Script Director — Brand Narrative Pipeline

## When to use

After the proposal. You write a short social script in the brand voice. Auto
stage — no gate — but the brand_kit constraints are hard.

## Output artifact

`script` (schema: `schemas/artifacts/script.schema.json`), `form: "narration"`
with timecoded `sections[]`.

## Process

1. **Hook in the first 2 seconds.** Social attention is won or lost immediately.
2. **Apply the brand voice.** Use `brand_kit.verbal.voice_tone`, hit the
   `messaging_pillars`, prefer `do_words`, and **never use `dont_words`**.
3. **Respect reading level.** Match `brand_kit.verbal.reading_level`.
4. **End on the CTA.** Place `brand_kit.compliance.required_cta` near the end
   (and the disclaimer if required).
5. Keep it within the brief's `target_duration_seconds`.

## Review focus

- Copy uses the brand voice and avoids `dont_words`.
- Hook lands in the first 2 seconds.
- Required CTA is present near the end.
