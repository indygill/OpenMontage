"""Contract tests for the brand-narrative pipeline (Phase 1+2).

Covers the new brand_kit artifact, the manifest (low-input stage order, reuse of
the existing brief), referenced-skill existence, and gating.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.pipeline_loader import get_stage_order, list_pipelines, load_pipeline
from schemas.artifacts import ARTIFACT_NAMES, load_schema, validate_artifact


# ---- Manifest ----

def test_brand_narrative_manifest_loads_and_validates():
    manifest = load_pipeline("brand-narrative")
    assert manifest["name"] == "brand-narrative"
    assert "brand-narrative" in list_pipelines()


def test_brand_narrative_stage_order():
    manifest = load_pipeline("brand-narrative")
    assert get_stage_order(manifest) == [
        "brand_setup", "brief", "proposal", "script", "scene_plan",
        "assets", "edit", "compose", "publish",
    ]


def test_reuses_existing_brief_artifact():
    """brand-narrative should reuse the marketing-shaped brief, not a new schema."""
    manifest = load_pipeline("brand-narrative")
    brief_stage = next(s for s in manifest["stages"] if s["name"] == "brief")
    assert "brief" in brief_stage["produces"]


def test_low_input_gating():
    """Only brand_setup, brief, proposal, and publish are gated; the rest auto."""
    manifest = load_pipeline("brand-narrative")
    gates = {s["name"]: s.get("human_approval_default", False) for s in manifest["stages"]}
    assert gates["brand_setup"] is True
    assert gates["brief"] is True
    assert gates["proposal"] is True
    assert gates["publish"] is True
    for stage in ["script", "scene_plan", "assets", "edit", "compose"]:
        assert gates[stage] is False, f"{stage} should auto-proceed (low-input)"


def test_all_referenced_skills_exist():
    manifest = load_pipeline("brand-narrative")
    skills_dir = PROJECT_ROOT / "skills"
    refs = [s["skill"] for s in manifest["stages"] if s.get("skill")]
    refs += [r for r in manifest.get("required_skills", []) if r.startswith("pipelines/brand-narrative/")]
    for ref in refs:
        assert (skills_dir / f"{ref}.md").is_file(), f"missing skill: {ref}"


# ---- brand_kit artifact ----

def test_brand_kit_registered():
    assert "brand_kit" in ARTIFACT_NAMES


def test_brand_kit_schema_loadable():
    schema = load_schema("brand_kit")
    assert schema["$id"].endswith("brand_kit")


def test_brand_kit_full_validates():
    validate_artifact("brand_kit", {
        "version": "1.0",
        "brand_name": "Northwind",
        "visual": {
            "logo": {
                "variants": [{"kind": "full", "path": "assets/brand/logo_full.svg"},
                             {"kind": "mono", "path": "assets/brand/logo_mono.svg"}],
                "safe_area_pct": 8, "min_size_px": 96, "default_placement": "bottom_right",
            },
            "colors": [
                {"role": "primary", "hex": "#0B3D2E", "usage": "backgrounds"},
                {"role": "accent", "hex": "#F2A900", "usage": "CTAs"},
            ],
            "typography": {"heading_font": "Söhne", "body_font": "Inter", "weights": [400, 800]},
            "style_playbook": "northwind-brand",
            "motion_signature": "snappy, 200ms eases",
        },
        "verbal": {
            "voice_tone": "confident, warm, plain-spoken",
            "tagline": "Built for the long haul.",
            "messaging_pillars": ["durability", "craft"],
            "do_words": ["built", "lasts"], "dont_words": ["cheap", "synergy"],
            "reading_level": "grade 7",
        },
        "audio": {
            "tts_voice": {"provider": "elevenlabs", "voice_id": "abc123"},
            "music_style": "warm acoustic", "sonic_logo_path": "assets/brand/sonic.wav",
        },
        "compliance": {
            "required_cta": "Shop now at northwind.com",
            "disclaimer": "Warranty subject to terms.",
            "hashtags": ["#BuiltForTheLongHaul"],
            "handles": {"instagram": "@northwind", "tiktok": "@northwind"},
        },
        "origin": "user_provided",
    })


def test_brand_kit_minimal_validates():
    validate_artifact("brand_kit", {
        "version": "1.0", "brand_name": "X",
        "visual": {"colors": [{"role": "primary", "hex": "#000000"}]},
    })


def test_brand_kit_requires_visual():
    with pytest.raises(Exception):
        validate_artifact("brand_kit", {"version": "1.0", "brand_name": "X"})


def test_brand_kit_requires_colors_in_visual():
    with pytest.raises(Exception):
        validate_artifact("brand_kit", {
            "version": "1.0", "brand_name": "X",
            "visual": {"typography": {"heading_font": "Inter"}},
        })


def test_brand_kit_rejects_bad_logo_variant():
    with pytest.raises(Exception):
        validate_artifact("brand_kit", {
            "version": "1.0", "brand_name": "X",
            "visual": {
                "colors": [{"role": "primary", "hex": "#000000"}],
                "logo": {"variants": [{"kind": "watermark", "path": "x.svg"}]},
            },
        })
