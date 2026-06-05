"""Contract tests for narrative-film ingest-at-altitude helpers (Phase 3).

Covers the provided-material convention, ingestion adapters (.fdx / fountain /
image folder), and reverse-derivation (script -> cast/locations/sequence_plan).
Every produced artifact is validated against its schema.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib import ingest
from schemas.artifacts import validate_artifact


FDX_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<FinalDraft DocumentType="Script" Template="No" Version="1">
 <Content>
  <Paragraph Type="Scene Heading"><Text>EXT. ISLAND JETTY - DAY</Text></Paragraph>
  <Paragraph Type="Action"><Text>The supply boat pulls away.</Text></Paragraph>
  <Paragraph Type="Character"><Text>THOMAS</Text></Paragraph>
  <Paragraph Type="Parenthetical"><Text>(to himself)</Text></Paragraph>
  <Paragraph Type="Dialogue"><Text>Just me, then.</Text></Paragraph>
  <Paragraph Type="Scene Heading"><Text>INT. LAMP ROOM - NIGHT</Text></Paragraph>
  <Paragraph Type="Action"><Text>The lens turns. Thomas climbs the iron stair.</Text></Paragraph>
  <Paragraph Type="Character"><Text>THE LIGHT</Text></Paragraph>
  <Paragraph Type="Dialogue"><Text>You came back.</Text></Paragraph>
 </Content>
</FinalDraft>
"""

FOUNTAIN_SAMPLE = """\
EXT. ISLAND JETTY - DAY

The supply boat pulls away.

THOMAS
(to himself)
Just me, then.

INT. LAMP ROOM - NIGHT

The lens turns.

THE LIGHT
You came back.
"""


# ---- Adapters ----

def test_fdx_to_script_validates(tmp_path):
    f = tmp_path / "film.fdx"
    f.write_text(FDX_SAMPLE, encoding="utf-8")
    script = ingest.script_from_file(f)
    validate_artifact("script", script)
    assert script["form"] == "screenplay"
    assert script["origin"] == "user_provided"
    assert [s["slugline"] for s in script["scenes"]] == [
        "EXT. ISLAND JETTY - DAY", "INT. LAMP ROOM - NIGHT"]
    assert script["scenes"][0]["dialogue"][0] == {
        "character_id": "thomas", "line": "Just me, then.", "parenthetical": "to himself"}


def test_fountain_to_script_validates():
    script = ingest.fountain_to_script(FOUNTAIN_SAMPLE, title="The Lighthouse Keeper")
    validate_artifact("script", script)
    assert script["form"] == "screenplay"
    assert len(script["scenes"]) == 2
    assert "the_light" in script["scenes"][1]["cast"]


def test_script_from_file_rejects_unknown_ext(tmp_path):
    f = tmp_path / "x.docx"
    f.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError):
        ingest.script_from_file(f)


def test_pdf_raises_helpful_error(tmp_path):
    f = tmp_path / "x.pdf"
    f.write_bytes(b"%PDF-1.4")
    with pytest.raises(NotImplementedError):
        ingest.script_from_file(f)


def test_image_folder_to_reference_assets(tmp_path):
    proj = tmp_path / "proj"
    refs = proj / "assets" / "cast" / "thomas"
    refs.mkdir(parents=True)
    (refs / "ref01.png").write_bytes(b"x")
    (refs / "ref02.jpg").write_bytes(b"x")
    (refs / "notes.txt").write_text("ignore me")
    out = ingest.image_folder_to_reference_assets(refs, project_dir=proj)
    assert out == ["assets/cast/thomas/ref01.png", "assets/cast/thomas/ref02.jpg"]


# ---- Slugline parsing ----

@pytest.mark.parametrize("slug,loc,tod", [
    ("EXT. ISLAND JETTY - DAY", "ISLAND JETTY", "DAY"),
    ("INT. LAMP ROOM - NIGHT", "LAMP ROOM", "NIGHT"),
    ("INT./EXT. CAR - CONTINUOUS", "CAR", "CONTINUOUS"),
    ("EST. THE LIGHTHOUSE", "THE LIGHTHOUSE", None),
])
def test_parse_slugline(slug, loc, tod):
    parsed = ingest.parse_slugline(slug)
    assert parsed["location"] == loc
    assert parsed["time_of_day"] == tod


# ---- Reverse-derivation ----

def test_derive_breakdown_validates_and_resolves():
    script = ingest.fountain_to_script(FOUNTAIN_SAMPLE)
    out = ingest.derive_breakdown(script)

    validate_artifact("cast", out["cast"])
    validate_artifact("locations", out["locations"])
    validate_artifact("sequence_plan", out["sequence_plan"])

    loc_ids = {l["id"] for l in out["locations"]["locations"]}
    cast_ids = {c["id"] for c in out["cast"]["characters"]}
    assert {"island_jetty", "lamp_room"}.issubset(loc_ids)
    assert {"thomas", "the_light"}.issubset(cast_ids)

    # every sequence references a real location, and every scene is covered once
    all_scene_ids = [sid for seq in out["sequence_plan"]["sequences"] for sid in seq["scene_ids"]]
    assert sorted(all_scene_ids) == [s["id"] for s in script["scenes"]]
    for seq in out["sequence_plan"]["sequences"]:
        assert seq["primary_location_id"] in loc_ids


def test_derive_breakdown_preserves_principals():
    script = ingest.fountain_to_script(FOUNTAIN_SAMPLE)
    existing = {"version": "1.0", "characters": [{
        "id": "thomas", "display_name": "Thomas Wake", "role": "protagonist",
        "tier": "principal", "consistency_anchors": ["salt-grey beard"]}]}
    out = ingest.derive_breakdown(script, existing_cast=existing)
    validate_artifact("cast", out["cast"])
    thomas = next(c for c in out["cast"]["characters"] if c["id"] == "thomas")
    assert thomas["tier"] == "principal"           # principal preserved, not overwritten
    assert thomas["role"] == "protagonist"
    the_light = next(c for c in out["cast"]["characters"] if c["id"] == "the_light")
    assert the_light["tier"] == "breakdown"        # new speaking part added


def test_derive_breakdown_requires_screenplay():
    narration = {"version": "1.0", "title": "x", "total_duration_seconds": 5,
                 "sections": [{"id": "s", "text": "hi", "start_seconds": 0, "end_seconds": 1}]}
    with pytest.raises(ValueError):
        ingest.derive_breakdown(narration)


# ---- Provided-material convention ----

def test_entry_plan_no_material():
    plan = ingest.entry_plan([])
    assert plan["entry_stage"] == "concept"
    assert plan["derive_upstream"] == []


def test_entry_plan_enters_at_script_and_derives_upstream():
    plan = ingest.entry_plan([{"artifact": "script", "path": "p.fdx", "mode": "lock"}])
    assert plan["entry_stage"] == "script"
    assert "concept" in plan["derive_upstream"] and "story" in plan["derive_upstream"]
    assert "breakdown" in plan["generate_downstream"]
    assert plan["locked"] == ["script"]


def test_entry_plan_reference_mode_does_not_set_entry():
    plan = ingest.entry_plan([{"artifact": "scene_plan", "path": "x", "mode": "reference"}])
    assert plan["entry_stage"] == "concept"


def test_load_provided_manifest(tmp_path):
    proj = tmp_path / "proj"
    (proj / "provided").mkdir(parents=True)
    (proj / "provided" / "manifest.json").write_text(
        '{"provided": [{"artifact": "script", "path": "in.fdx", "mode": "lock"}]}',
        encoding="utf-8")
    entries = ingest.load_provided_manifest(proj)
    assert entries == [{"artifact": "script", "path": "in.fdx", "mode": "lock", "format": None}]


def test_load_provided_manifest_rejects_bad_mode(tmp_path):
    proj = tmp_path / "proj"
    (proj / "provided").mkdir(parents=True)
    (proj / "provided" / "manifest.json").write_text(
        '[{"artifact": "script", "mode": "overwrite"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        ingest.load_provided_manifest(proj)


def test_load_provided_manifest_absent(tmp_path):
    assert ingest.load_provided_manifest(tmp_path) == []
