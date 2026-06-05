"""Backfill a project from existing material so the agent resumes mid-pipeline.

`scaffold_project()` is the one-call "Import existing material" path: it moves a
user's files into the right places, normalizes them into canonical artifacts
(via `lib.ingest`), reverse-derives upstream artifacts, and writes `completed`
checkpoints — so when the agent next runs `get_next_stage()`, it picks up exactly
where the provided material stops and never regenerates what you brought.

This is "tools + persistence" — deterministic assembly only. The creative work
(authoring the story bible, locking render_runtime at proposal) is left to the
agent: provided artifacts mark stages done; the agent fills the gaps and honors
the locked material.

Key mechanic: `get_next_stage()` returns the first stage *in pipeline order*
without a completed checkpoint. So scaffold marks every stage it has a valid
canonical artifact for; the resume point falls out as the earliest gap. Providing
a downstream artifact (a script) without the upstream ones means the agent still
authors the upstream creative stages first, then adopts your locked script.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Optional

from lib import ingest
from lib.checkpoint import CANONICAL_STAGE_ARTIFACTS, get_next_stage, write_checkpoint
from lib.pipeline_loader import get_stage_order, load_pipeline
from schemas.artifacts import validate_artifact

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def _copy_images(src: Path, dest: Path) -> list[Path]:
    """Copy image files from src into dest (created). Returns copied paths."""
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for p in sorted(src.iterdir()):
        if p.suffix.lower() in _IMAGE_EXTS:
            target = dest / p.name
            shutil.copy2(p, target)
            copied.append(target)
    return copied


def _cast_from_refs(
    cast_reference_dirs: dict[str, str | Path], project_dir: Path
) -> dict[str, Any]:
    """Copy each character's reference images into the project and build a cast."""
    characters = []
    for cid, folder in cast_reference_dirs.items():
        dest = project_dir / "assets" / "cast" / cid
        copied = _copy_images(Path(folder), dest)
        characters.append({
            "id": cid,
            "display_name": cid.replace("_", " ").title(),
            "role": "supporting",
            "tier": "principal",
            "identity_method": "reference_image",
            "reference_assets": [str(p.relative_to(project_dir)) for p in copied],
            "origin": "user_provided",
        })
    return {"version": "1.0", "characters": characters}


def scaffold_project(
    project_name: str,
    pipeline: str,
    *,
    artifacts: Optional[dict[str, Any]] = None,
    script_file: Optional[str | Path] = None,
    cast_reference_dirs: Optional[dict[str, str | Path]] = None,
    derive_breakdown: bool = True,
    projects_root: str | Path = "projects",
    pipelines_root: str | Path = "pipelines",
) -> dict[str, Any]:
    """Scaffold a resumable project from existing material.

    Args:
        project_name: kebab-case project id.
        pipeline: manifest name (e.g. "narrative-film").
        artifacts: pre-built canonical artifacts by name (e.g. a provided
            ``story_bible`` dict) to fill upstream stages.
        script_file: a raw screenplay (.fdx / .fountain / .txt / .json) to
            normalize into the ``script`` artifact.
        cast_reference_dirs: ``character_id -> folder of reference images``;
            images are copied into the project and become principal cast.
        derive_breakdown: if a screenplay script is present, reverse-derive
            ``cast`` / ``locations`` / ``sequence_plan`` from it.

    Returns a summary including ``resume_stage`` — where the agent will pick up.
    """
    manifest = load_pipeline(pipeline)  # validates the pipeline exists
    stage_order = get_stage_order(manifest)
    produces_by_stage = {s["name"]: s.get("produces", []) for s in manifest["stages"]}

    project_dir = Path(projects_root) / project_name
    pipelines_dir = Path(pipelines_root)
    for sub in ("artifacts", "assets/images", "assets/video", "assets/audio",
                "assets/music", "renders", "provided"):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    art: dict[str, Any] = dict(artifacts or {})
    provided_manifest: list[dict[str, Any]] = []

    # 1. Cast reference images -> principal cast (copied into the project).
    if cast_reference_dirs:
        ref_cast = _cast_from_refs(cast_reference_dirs, project_dir)
        # merge with any provided cast (provided entries win on id collision)
        if "cast" in art:
            existing_ids = {c["id"] for c in art["cast"]["characters"]}
            art["cast"]["characters"].extend(
                c for c in ref_cast["characters"] if c["id"] not in existing_ids)
        else:
            art["cast"] = ref_cast
        provided_manifest.append({"artifact": "cast", "path": "assets/cast/", "mode": "lock"})

    # 2. Raw screenplay -> script artifact (copied into provided/).
    if script_file is not None:
        src = Path(script_file)
        dest = project_dir / "provided" / src.name
        shutil.copy2(src, dest)
        art["script"] = ingest.script_from_file(dest)
        provided_manifest.append({
            "artifact": "script", "path": f"provided/{src.name}", "mode": "lock"})

    # 3. Reverse-derive the breakdown from a screenplay script.
    if derive_breakdown and art.get("script", {}).get("form") == "screenplay":
        derived = ingest.derive_breakdown(art["script"], existing_cast=art.get("cast"))
        art["cast"] = derived["cast"]            # preserves principals, adds speaking parts
        art.setdefault("locations", derived["locations"])
        art.setdefault("sequence_plan", derived["sequence_plan"])

    # 4. Validate + write every artifact to projects/<name>/artifacts/.
    artifacts_written: list[str] = []
    for name, data in art.items():
        validate_artifact(name, data)
        with open(project_dir / "artifacts" / f"{name}.json", "w") as f:
            json.dump(data, f, indent=2)
        artifacts_written.append(name)
        if name not in {e["artifact"] for e in provided_manifest}:
            provided_manifest.append({
                "artifact": name, "path": f"artifacts/{name}.json", "mode": "seed"})

    # 5. Write a completed checkpoint for every stage whose canonical artifact
    #    we have (carrying that stage's full produced set).
    backfilled_stages: list[str] = []
    for stage in stage_order:
        canonical = CANONICAL_STAGE_ARTIFACTS.get(stage)
        if not canonical or canonical not in art:
            continue
        stage_artifacts = {a: art[a] for a in produces_by_stage.get(stage, [canonical])
                           if a in art}
        stage_artifacts.setdefault(canonical, art[canonical])
        write_checkpoint(
            pipelines_dir, project_name, stage, "completed", stage_artifacts,
            pipeline_type=pipeline, human_approved=True,
            metadata={"origin": "scaffold", "provided": True},
        )
        backfilled_stages.append(stage)

    # 6. Record the provided-material manifest.
    with open(project_dir / "provided" / "manifest.json", "w") as f:
        json.dump({"provided": provided_manifest}, f, indent=2)

    resume_stage = get_next_stage(pipelines_dir, project_name, pipeline)
    return {
        "project_name": project_name,
        "pipeline": pipeline,
        "project_dir": str(project_dir),
        "checkpoint_dir": str(pipelines_dir / project_name),
        "artifacts_written": artifacts_written,
        "backfilled_stages": backfilled_stages,
        "resume_stage": resume_stage,
        "provided": provided_manifest,
    }
