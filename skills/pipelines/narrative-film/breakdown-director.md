# Breakdown Director — Narrative Film Pipeline

## When to use

After the screenplay. This is the **script breakdown** — the pre-production step
where you extract production elements *from the finished script*: locations,
supporting/minor cast, and sequences. This is exactly what a 1st AD does.

## Output artifacts

- `locations` (schema: `schemas/artifacts/locations.schema.json`)
- `sequence_plan` (schema: `schemas/artifacts/sequence_plan.schema.json`)
- updated `cast` (schema: `schemas/artifacts/cast.schema.json`) — add
  `tier: breakdown` characters discovered in the script.

## Process — derive from the script, don't invent

1. **Locations.** Walk every screenplay slugline. Create one `locations` entry
   per distinct place, with `time_of_day` and `weather` where the script implies
   them. Every `location_id` referenced by the script must exist here.
2. **Supporting/minor cast.** Add every speaking part not already a principal,
   as `tier: breakdown`. Principals from the `characters` stage are preserved.
3. **Sequences.** Group screenplay scenes into ordered `sequences` (a sequence is
   a chapter of story — a continuous dramatic movement). Reference the owning
   `act_id`, the `primary_location_id`, the `cast_ids`, and the screenplay
   `scene_ids` it covers.

## Reverse-derivation (ingest at altitude)

If the script was user-provided (`origin: user_provided`), this stage is the
back-fill: everything here is **extracted from that script**. Do not fabricate
locations or characters the script doesn't contain, and surface contradictions
(e.g. a character in the bible who never appears in a locked script) as a finding
rather than silently resolving them.

## Review focus

- Every script-referenced location exists in `locations`.
- All speaking parts are in `cast`.
- Sequences group scenes coherently and reference valid acts.
- When the script was provided, the breakdown was derived from it.
