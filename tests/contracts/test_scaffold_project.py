"""Contract tests for scaffold_project (backfill-an-existing-project / ingest-at-altitude).

Verifies the deterministic assembly: raw files -> canonical artifacts ->
completed checkpoints -> a correct resume point via get_next_stage.
"""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib import ingest
from lib.checkpoint import read_checkpoint, write_checkpoint, get_next_stage
from lib.scaffold import scaffold_project


FOUNTAIN = """\
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


# ---- The checkpoint fix: new stages must be checkpointable ----

@pytest.mark.parametrize("stage,artifact_name,artifact", [
    ("concept", "story_bible", {
        "version": "1.0", "title": "T", "logline": "L", "synopsis": "S", "tone": "t",
        "format": {"kind": "short_film", "target_duration_seconds": 60},
        "world": {"setting": "x"}}),
    ("characters", "cast", {
        "version": "1.0", "characters": [
            {"id": "a", "display_name": "A", "role": "protagonist", "tier": "principal"}]}),
    ("breakdown", "sequence_plan", {
        "version": "1.0", "sequences": [{"id": "s1", "order": 1, "label": "L"}]}),
    ("brand_setup", "brand_kit", {
        "version": "1.0", "brand_name": "B",
        "visual": {"colors": [{"role": "primary", "hex": "#000000"}]}}),
])
def test_new_stages_are_checkpointable(tmp_path, stage, artifact_name, artifact):
    """Regression: CANONICAL_STAGE_ARTIFACTS must know the new pipeline stages."""
    pipeline = "brand-narrative" if stage == "brand_setup" else "narrative-film"
    write_checkpoint(tmp_path, "p", stage, "completed", {artifact_name: artifact},
                     pipeline_type=pipeline)
    cp = read_checkpoint(tmp_path, "p", stage)
    assert cp["status"] == "completed"


# ---- scaffold: script + cast refs ----

def test_scaffold_from_script_and_refs(tmp_path):
    # arrange: a screenplay file + a folder of face refs
    script = tmp_path / "lighthouse.fountain"
    script.write_text(FOUNTAIN, encoding="utf-8")
    refs = tmp_path / "thomas_refs"
    refs.mkdir()
    (refs / "ref01.png").write_bytes(b"x")
    (refs / "ref02.jpg").write_bytes(b"x")

    out = scaffold_project(
        "lighthouse", "narrative-film",
        script_file=script,
        cast_reference_dirs={"thomas": refs},
        projects_root=tmp_path / "projects",
        pipelines_root=tmp_path / "pipelines",
    )

    # artifacts materialized + on disk
    assert set(out["artifacts_written"]) >= {"script", "cast", "locations", "sequence_plan"}
    adir = tmp_path / "projects" / "lighthouse" / "artifacts"
    for name in ["script", "cast", "locations", "sequence_plan"]:
        assert (adir / f"{name}.json").is_file()

    # the provided refs were copied into the project and attached to thomas
    cast = json.loads((adir / "cast.json").read_text())
    thomas = next(c for c in cast["characters"] if c["id"] == "thomas")
    assert thomas["tier"] == "principal"
    assert thomas["reference_assets"] == ["assets/cast/thomas/ref01.png",
                                          "assets/cast/thomas/ref02.jpg"]
    assert (tmp_path / "projects" / "lighthouse" / "assets" / "cast" / "thomas" / "ref01.png").is_file()
    # the_light (a speaking part from the script) was added as a breakdown character
    assert any(c["id"] == "the_light" and c["tier"] == "breakdown"
               for c in cast["characters"])

    # checkpoints written for the stages we have canonical artifacts for
    assert set(out["backfilled_stages"]) == {"characters", "script", "breakdown"}

    # resume lands at the first gap: concept (the agent still authors the bible,
    # locks render_runtime at proposal, etc. — then honors the locked script)
    assert out["resume_stage"] == "concept"


# ---- scaffold: providing upstream creative artifacts advances the resume point ----

def test_scaffold_with_story_bible_resumes_at_proposal(tmp_path):
    script = tmp_path / "s.fountain"
    script.write_text(FOUNTAIN, encoding="utf-8")
    story_bible = {
        "version": "1.0", "title": "Lighthouse", "logline": "L", "synopsis": "S",
        "tone": "folk horror",
        "format": {"kind": "short_film", "target_duration_seconds": 240},
        "world": {"setting": "an island"}}
    story = {"version": "1.0", "acts": [{"id": "act_1", "summary": "Arrival."}]}

    out = scaffold_project(
        "lh2", "narrative-film",
        artifacts={"story_bible": story_bible, "story": story},
        script_file=script,
        projects_root=tmp_path / "projects",
        pipelines_root=tmp_path / "pipelines",
    )
    # concept, characters, story, script, breakdown filled — proposal is the gap
    assert "concept" in out["backfilled_stages"]
    assert out["resume_stage"] == "proposal"


# ---- scaffold: brand-narrative reuses the same machinery ----

def test_scaffold_brand_narrative(tmp_path):
    brand_kit = {"version": "1.0", "brand_name": "Northwind",
                 "visual": {"colors": [{"role": "primary", "hex": "#0B3D2E"}]}}
    brief = {"version": "1.0", "title": "Promo", "hook": "Built to last",
             "key_points": ["durable"], "tone": "confident", "style": "flat-motion-graphics",
             "target_platform": "instagram", "target_duration_seconds": 15}

    out = scaffold_project(
        "northwind-promo", "brand-narrative",
        artifacts={"brand_kit": brand_kit, "brief": brief},
        projects_root=tmp_path / "projects",
        pipelines_root=tmp_path / "pipelines",
    )
    assert set(out["backfilled_stages"]) == {"brand_setup", "brief"}
    # brand_setup + brief done -> resume at proposal
    assert out["resume_stage"] == "proposal"


def test_scaffold_writes_provided_manifest(tmp_path):
    script = tmp_path / "s.fdx"
    script.write_text(
        '<?xml version="1.0"?><FinalDraft><Content>'
        '<Paragraph Type="Scene Heading"><Text>EXT. PIER - DAY</Text></Paragraph>'
        '<Paragraph Type="Action"><Text>Waves.</Text></Paragraph>'
        '</Content></FinalDraft>', encoding="utf-8")
    out = scaffold_project(
        "pm", "narrative-film", script_file=script,
        projects_root=tmp_path / "projects", pipelines_root=tmp_path / "pipelines")
    pm = json.loads(
        (tmp_path / "projects" / "pm" / "provided" / "manifest.json").read_text())
    entries = {e["artifact"]: e for e in pm["provided"]}
    assert entries["script"]["mode"] == "lock"
    assert entries["script"]["path"] == "provided/s.fdx"
