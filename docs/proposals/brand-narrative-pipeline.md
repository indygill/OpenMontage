# Design Proposal: `brand-narrative` Pipeline

> Status: **Draft for review** | Author: agent-assisted design | Date: 2026-06-05
>
> Purpose: a **low-input, identity-first** pipeline that produces a *stream* of
> on-brand short social videos from a reusable **brand kit** (logo, colors,
> fonts, voice, messaging, compliance). The opposite end of the spectrum from
> `narrative-film`: little per-video input, high volume, brand consistency as the
> primary quality bar. Closer to OpenMontage's core prompt-to-video flow, but
> governed by the user's existing brand assets.

---

## 1. How it differs from `narrative-film`

| Axis | narrative-film | **brand-narrative** |
|---|---|---|
| User input | High — gates at every creative layer | **Low** — set up the brand once, then brief → auto-applied → render |
| Persistence | One project = one film | One **brand** = a stream of videos; the brand kit is reused across all of them |
| Driver | Fictional story/world | **Brand kit** (identity) + a factual/promotional message |
| Output | One film (± per-sequence clips) | **Many short social variants** per concept — 9:16 / 1:1 / 16:9 |
| Quality bar | Dramatic coherence | **Brand consistency + compliance** (logo safe-area, contrast, required CTA/disclaimer) |

It is **identity-first with little input, high volume** — not story-first.

## 2. Reuse map — most of this already exists

brand-narrative is largely an *assembly* of existing OpenMontage parts, plus one
new artifact. What we reuse unchanged:

- **`brief` artifact** — already marketing-shaped: `hook`, `key_points`,
  `core_message`, `cta`, `tone`, `style`, `target_platform`,
  `target_duration_seconds`. **No new brief schema needed.**
- **Style playbook system** (`schemas/styles/playbook.schema.json`,
  `lib/playbook_generator.py`) — holds the *visual tokens* (palette, typography,
  motion, audio, a11y/color rules). The brand kit links to a generated playbook.
- **`lib/media_profiles.py`** — already ships `youtube_shorts`,
  `instagram_reels`, `instagram_feed` (1:1), `tiktok`, landscape profiles. This
  is the multi-aspect output engine.
- **`render_report.outputs[].role: "derivative"`** (added in the narrative-film
  Phase 4) — multi-aspect variants are already expressible.
- **HyperFrames** runtime — built for "product promos, launch reels,
  website-to-video, kinetic typography" — the natural fit for brand/social.
- **Selectors** (`image_selector`, `video_selector`, `tts_selector`), checkpoint
  system, reviewer, cost tracker, and the `script` / `scene_plan` /
  `asset_manifest` / `edit_decisions` / `publish_log` artifacts.

**Net-new is small:** one `brand_kit` artifact, one manifest, the director
skills, and a brand-safety review gate.

## 3. The `brand_kit` artifact (new) — the only new schema

A persistent, asset-backed identity, created once and reused across every video.
v1 is **manually entered** (precise control); auto-extraction from a URL/brand
guide via the `visual-style` skill is a noted future enhancement (§7).

```jsonc
{
  "version": "1.0",
  "brand_name": "Northwind",
  "visual": {
    "logo": {
      "variants": [
        { "kind": "full",     "path": "assets/brand/logo_full.svg" },
        { "kind": "mark",     "path": "assets/brand/logo_mark.svg" },
        { "kind": "mono",     "path": "assets/brand/logo_mono.svg" },
        { "kind": "reversed", "path": "assets/brand/logo_rev.svg" }
      ],
      "safe_area_pct": 8,
      "min_size_px": 96,
      "default_placement": "bottom_right"
    },
    "colors": [
      { "role": "primary",   "hex": "#0B3D2E", "usage": "backgrounds, logo" },
      { "role": "secondary", "hex": "#E8F0EB", "usage": "text on dark" },
      { "role": "accent",    "hex": "#F2A900", "usage": "CTAs, highlights" }
    ],
    "typography": { "heading_font": "Söhne", "body_font": "Inter", "weights": [400, 600, 800] },
    "style_playbook": "northwind-brand",        // generated playbook name
    "motion_signature": "snappy, 200ms eases, no bounce"
  },
  "verbal": {
    "voice_tone": "confident, warm, plain-spoken; no jargon",
    "tagline": "Built for the long haul.",
    "messaging_pillars": ["durability", "craft", "value"],
    "do_words": ["built", "honest", "lasts"],
    "dont_words": ["cheap", "revolutionary", "synergy"],
    "reading_level": "grade 7"
  },
  "audio": {
    "tts_voice": { "provider": "elevenlabs", "voice_id": "..." },  // locked brand narrator
    "music_style": "warm acoustic, mid-tempo",
    "sonic_logo_path": "assets/brand/sonic_logo.wav"
  },
  "compliance": {
    "required_cta": "Shop now at northwind.com",
    "disclaimer": "Lifetime warranty subject to terms.",
    "hashtags": ["#BuiltForTheLongHaul"],
    "handles": { "instagram": "@northwind", "tiktok": "@northwind", "youtube": "@northwind" }
  },
  "origin": "user_provided",
  "metadata": {}
}
```

Facets map to pipeline behavior: **visual** → playbook + logo overlay at compose;
**verbal** → script/on-screen copy constraints; **audio** → locked TTS voice +
music selection; **compliance** → enforced at compose by the brand-safety gate.

## 4. Pipeline shape (low-input)

Few gates by design: set the brand up once, approve the brief+plan, review at the
end. Everything between is automatic.

| Stage | Produces | Gate | Notes |
|---|---|---|---|
| `brand_setup` | `brand_kit` | **true** | One-time; **skipped if a brand_kit already exists** for this brand. |
| `brief` | `brief` (reused) | **true** | Light: platform(s), objective, key message, duration, CTA. References the brand_kit. |
| `proposal` | `proposal_packet`, `decision_log` | **true** | Locks `render_runtime` (present both), confirms platform/aspect variants, music. |
| `script` | `script` | false | Auto; brand `voice_tone` + do/don't words applied. |
| `scene_plan` | `scene_plan` | false | Auto; template-driven, playbook-styled. |
| `assets` | `asset_manifest` | false | Auto; locked brand TTS voice, on-brand visuals, logo asset. |
| `edit` | `edit_decisions` | false | Auto. |
| `compose` | `render_report`, `final_review` | false | Multi-aspect **derivative** renders; **brand-safety gate** runs here. |
| `publish` | `publish_log` | **true** | Per-platform copy, hashtags, @handles, CTA from compliance. |

Three human touch-points (brand_kit once, brief+proposal, publish) — the rest is
hands-off. That is the "less input, closer to core OpenMontage" experience.

### Multi-aspect output

The `proposal` selects target platforms; `compose` renders one master then emits
a `role: "derivative"` output per platform via `lib/media_profiles.py`
(`instagram_reels` 9:16, `instagram_feed` 1:1, `youtube_shorts` 9:16, etc.),
each respecting the logo safe-area for that aspect.

## 5. Brand-safety gate (new behavior, at compose)

A reviewer check (added to `skills/meta/reviewer.md` focus for this pipeline, or
a small `lib/brand_safety.py` helper) that flags as findings:

- logo missing, off-brand, or violating `safe_area_pct` / `min_size_px`;
- text/background pairs failing contrast (reuse the playbook a11y color rules);
- a `dont_words` term present in script or on-screen copy;
- required CTA or disclaimer absent when compliance demands it.

CTA/disclaimer/logo absence = CRITICAL; contrast/word-list = SUGGESTION.

## 6. Reuse vs net-new (scope summary)

**Net-new:**
- 1 schema: `brand_kit`.
- 1 manifest: `brand-narrative.yaml`.
- ~9 director skills (`brand-setup-director` is the only genuinely novel one).
- brand-safety gate (reviewer focus + optional `lib/brand_safety.py`).
- contract tests.

**Reused unchanged:** `brief`, `script`, `scene_plan`, `asset_manifest`,
`edit_decisions`, `render_report` (with `derivative` role), `publish_log`, the
style-playbook system + `playbook_generator`, `media_profiles`, selectors,
checkpoints, reviewer, cost tracker, composition runtimes.

## 7. Open questions for the reviewer

1. **Onboarding.** — **resolved: manual entry for v1.** Auto-extract from a
   website / PDF brand guide via the `visual-style` skill + `playbook_generator`
   is a future enhancement (it directly serves the "less input" goal, so worth
   doing in a Phase 3).
2. **Brand kit scope.** — **resolved: all four facets** (visual, verbal, audio,
   compliance).
3. **brand_kit location.** Per-brand reusable across projects: store at
   `brands/<brand>/brand_kit.json` (shared) vs. inside each `projects/<name>/`?
   *Recommendation: a shared `brands/<brand>/` workspace, referenced by project.*
   **← needs your call.**
4. **Brand TTS voice.** v1 uses an existing `voice_id`; voice **cloning** as a
   later add. *Recommendation: existing voice_id for v1.*
5. **Campaign layer.** Group multiple videos under a campaign sharing one brief
   theme? *Defer to a later enhancement; v1 is one brief → one (multi-aspect)
   deliverable.*

## 8. Suggested implementation phases

- **Phase 1 — schema + manifest:** `brand_kit.schema.json`,
  `pipeline_defs/brand-narrative.yaml` (reusing `brief` et al.), register the
  artifact, contract tests. Discoverable and validating.
- **Phase 2 — director skills + brand-safety gate:** the ~9 stage skills
  (proposal/compose carry the runtime contract) and the compose-time brand-safety
  checks; wire multi-aspect derivative renders.
- **Phase 3 — auto-onboarding (optional):** extract a brand_kit from a URL/brand
  guide via the `visual-style` skill — the biggest further cut to user input.
- **Phase 4 — dogfood + docs:** run a brand brief end-to-end across 3 aspects;
  register `brand-narrative` in the pipeline tables.

---

*Design document only — no schemas, manifests, or skills created yet. §7.1
(manual onboarding) and §7.2 (all four facets) resolved. Open: §7.3 (brand_kit
location) and §7.4 (TTS voice) before Phase 1.*
