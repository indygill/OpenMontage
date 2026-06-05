# Publish Director — Brand Narrative Pipeline

## When to use

After the renders pass the brand-safety gate. You package the per-platform
deliverables with on-brand captions and metadata. Gated — confirm before any
external publish.

## Output artifact

`publish_log` (schema: `schemas/artifacts/publish_log.schema.json`).

## Process

1. **One package per platform.** Pair each `role: "derivative"` render with its
   platform.
2. **Captions from the brand_kit compliance facet.** Use
   `brand_kit.compliance.hashtags`, the per-platform `handles`, and ensure the
   `required_cta` appears in every caption. Apply the brand voice.
3. **Disclaimer** where required.
4. **Confirm before external publish.** Posting is outward-facing — get explicit
   user approval first.

## Review focus

- Per-platform copy, hashtags, and handles come from the brand_kit.
- Required CTA present in every caption.
- Export package contains per-platform videos and metadata.
