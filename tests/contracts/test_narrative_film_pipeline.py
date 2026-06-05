"""Contract tests for the narrative-film pipeline (Phase 1: schemas + manifest).

Covers the new artifacts (story_bible, cast, locations, story, sequence_plan),
the dual-shape script extension (narration + screenplay), the additive scene_plan
fields (sequence_id, location_id, cast), and the manifest stage order.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.pipeline_loader import get_stage_order, list_pipelines, load_pipeline
from schemas.artifacts import ARTIFACT_NAMES, load_schema, validate_artifact


# ---- Manifest ----

def test_narrative_film_manifest_loads_and_validates():
    # load_pipeline validates against the manifest schema; raises on failure.
    manifest = load_pipeline("narrative-film")
    assert manifest["name"] == "narrative-film"
    assert "narrative-film" in list_pipelines()


def test_narrative_film_stage_order():
    manifest = load_pipeline("narrative-film")
    assert get_stage_order(manifest) == [
        "concept",
        "proposal",
        "characters",
        "story",
        "script",
        "breakdown",
        "scene_plan",
        "assets",
        "edit",
        "compose",
        "publish",
    ]


def test_script_precedes_scene_plan():
    """The script is the spine: it must come before the shot list."""
    order = get_stage_order(load_pipeline("narrative-film"))
    assert order.index("script") < order.index("scene_plan")
    assert order.index("script") < order.index("breakdown")


def test_all_referenced_skills_exist():
    manifest = load_pipeline("narrative-film")
    skills_dir = PROJECT_ROOT / "skills"
    refs = [s["skill"] for s in manifest["stages"] if s.get("skill")]
    refs += [r for r in manifest.get("required_skills", []) if r.startswith("pipelines/narrative-film/")]
    for ref in refs:
        assert (skills_dir / f"{ref}.md").is_file(), f"missing skill: {ref}"


def test_creative_stages_gated():
    manifest = load_pipeline("narrative-film")
    gates = {s["name"]: s.get("human_approval_default", False) for s in manifest["stages"]}
    for stage in ["concept", "characters", "story", "script", "breakdown", "scene_plan"]:
        assert gates[stage] is True, f"{stage} should require human approval"
    for stage in ["assets", "edit", "compose"]:
        assert gates[stage] is False, f"{stage} should auto-proceed"


# ---- Artifact registration ----

def test_narrative_artifacts_registered():
    assert {
        "story_bible",
        "cast",
        "locations",
        "story",
        "sequence_plan",
    }.issubset(set(ARTIFACT_NAMES))


@pytest.mark.parametrize(
    "name", ["story_bible", "cast", "locations", "story", "sequence_plan"]
)
def test_new_schemas_are_loadable(name):
    schema = load_schema(name)
    assert "$schema" in schema
    assert schema["$id"].endswith(name)


# ---- Sample artifacts validate ----

def test_story_bible_validates():
    validate_artifact("story_bible", {
        "version": "1.0",
        "title": "The Lighthouse Keeper",
        "logline": "A grieving keeper discovers the light is talking back.",
        "synopsis": "Thomas takes a remote posting and slowly unravels.",
        "tone": "slow-burn folk horror",
        "format": {"kind": "short_film", "target_duration_seconds": 240, "aspect_ratio": "2.39:1"},
        "world": {"setting": "a remote North Atlantic island", "era": "1890s",
                  "rules": ["the light must never go out"], "style_playbook": "clean-professional"},
    })


def test_story_bible_rejects_missing_world():
    with pytest.raises(Exception):
        validate_artifact("story_bible", {
            "version": "1.0", "title": "x", "logline": "y", "synopsis": "z",
            "tone": "t", "format": {"kind": "short_film", "target_duration_seconds": 60},
        })


def test_cast_validates():
    validate_artifact("cast", {
        "version": "1.0",
        "characters": [{
            "id": "thomas", "display_name": "Thomas Wake", "role": "protagonist",
            "tier": "principal", "identity_method": "reference_image",
            "reference_assets": ["assets/cast/thomas/ref01.png"],
            "consistency_anchors": ["deep-set eyes", "scar over left brow"],
            "origin": "user_provided",
        }],
    })


def test_cast_rejects_bad_role():
    with pytest.raises(Exception):
        validate_artifact("cast", {
            "version": "1.0",
            "characters": [{"id": "x", "display_name": "X", "role": "hero", "tier": "principal"}],
        })


def test_locations_validates():
    validate_artifact("locations", {
        "version": "1.0",
        "locations": [{
            "id": "lamp_room", "display_name": "The Lamp Room",
            "description": "cramped iron gallery around the rotating lens",
            "time_of_day": "night", "weather": "storm",
        }],
    })


def test_story_validates():
    validate_artifact("story", {
        "version": "1.0",
        "structure": "three_act",
        "acts": [{
            "id": "act_1", "label": "Arrival", "summary": "Thomas takes the post.",
            "beats": [{"id": "b1", "summary": "Boat leaves; he is alone.", "function": "establish"}],
        }],
    })


def test_sequence_plan_validates():
    validate_artifact("sequence_plan", {
        "version": "1.0",
        "sequences": [{
            "id": "seq_arrival", "order": 1, "label": "The Arrival", "act_id": "act_1",
            "primary_location_id": "lamp_room", "cast_ids": ["thomas"],
            "scene_ids": ["sc_001", "sc_002"],
        }],
    })


# ---- Script dual-shape (backward compatibility is critical) ----

def test_script_legacy_narration_still_validates():
    """Existing narration scripts (no `form`) must still validate."""
    validate_artifact("script", {
        "version": "1.0", "title": "Old Explainer", "total_duration_seconds": 60,
        "sections": [{"id": "s1", "text": "Hello", "start_seconds": 0, "end_seconds": 5}],
    })


def test_script_explicit_narration_validates():
    validate_artifact("script", {
        "version": "1.0", "title": "Narrated", "form": "narration",
        "total_duration_seconds": 60,
        "sections": [{"id": "s1", "text": "Hi", "start_seconds": 0, "end_seconds": 5}],
    })


def test_script_screenplay_validates():
    validate_artifact("script", {
        "version": "1.0", "title": "The Lighthouse Keeper", "form": "screenplay",
        "scenes": [{
            "id": "sc_001", "sequence_id": "seq_arrival",
            "slugline": "EXT. ISLAND JETTY - DAY", "location_id": "lamp_room",
            "action": "The supply boat pulls away. Thomas stands alone.",
            "cast": ["thomas"],
            "dialogue": [{"character_id": "thomas", "line": "Just me, then.", "parenthetical": "to himself"}],
        }],
    })


def test_script_screenplay_requires_scenes():
    with pytest.raises(Exception):
        validate_artifact("script", {
            "version": "1.0", "title": "Broken", "form": "screenplay",
            "total_duration_seconds": 60,
            "sections": [{"id": "s1", "text": "x", "start_seconds": 0, "end_seconds": 1}],
        })


def test_script_narration_requires_sections_and_duration():
    with pytest.raises(Exception):
        validate_artifact("script", {"version": "1.0", "title": "Empty"})


# ---- scene_plan additive fields ----

def test_scene_plan_accepts_narrative_fields():
    validate_artifact("scene_plan", {
        "version": "1.0",
        "scenes": [{
            "id": "sc_001", "type": "generated",
            "description": "Thomas alone on the jetty",
            "start_seconds": 0, "end_seconds": 6,
            "sequence_id": "seq_arrival", "location_id": "lamp_room", "cast": ["thomas"],
        }],
    })


def test_scene_plan_legacy_without_narrative_fields_still_validates():
    validate_artifact("scene_plan", {
        "version": "1.0",
        "scenes": [{
            "id": "sc_001", "type": "text_card", "description": "title",
            "start_seconds": 0, "end_seconds": 3,
        }],
    })


# ---- render_report per-sequence outputs (additive, backward-compatible) ----

def test_render_report_per_sequence_outputs_validate():
    validate_artifact("render_report", {
        "version": "1.0",
        "outputs": [
            {"path": "renders/final.mp4", "format": "mp4", "resolution": "1920x800",
             "duration_seconds": 240, "role": "hero"},
            {"path": "renders/seq_arrival.mp4", "format": "mp4", "resolution": "1920x800",
             "duration_seconds": 48, "role": "per_sequence", "sequence_id": "seq_arrival"},
        ],
    })


def test_render_report_legacy_outputs_still_validate():
    validate_artifact("render_report", {
        "version": "1.0",
        "outputs": [{"path": "renders/final.mp4", "format": "mp4",
                     "resolution": "1920x1080", "duration_seconds": 60}],
    })


def test_render_report_rejects_bad_role():
    with pytest.raises(Exception):
        validate_artifact("render_report", {
            "version": "1.0",
            "outputs": [{"path": "x.mp4", "format": "mp4", "resolution": "1x1",
                         "duration_seconds": 1, "role": "teaser"}],
        })
