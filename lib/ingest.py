"""Ingest-at-altitude helpers for the narrative-film pipeline.

Lets a user enter the pipeline at any stage with existing material, and lets the
agent derive upstream artifacts by extraction ("derive upward, generate
downward"). Deterministic and dependency-free (stdlib only): the creative
refinement stays with the agent/director skills — this module only does the
mechanical normalization and extraction.

Three capabilities:

1. Provided-material convention — `load_provided_manifest()` / `entry_plan()`:
   declare existing files with a mode (lock / seed / reference) and compute the
   stage to enter at plus which upstream artifacts must be derived.
2. Ingestion adapters — turn external formats into canonical artifacts:
   `script_from_file()` (.fdx / .fountain / .txt / .json),
   `image_folder_to_reference_assets()`.
3. Reverse-derivation — `derive_breakdown()`: extract cast, locations, and a
   sequence_plan FROM a screenplay-shaped script.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Provided-material convention
# ---------------------------------------------------------------------------

# narrative-film stage order (must match pipeline_defs/narrative-film.yaml)
PIPELINE_STAGE_ORDER = [
    "concept", "proposal", "characters", "story", "script",
    "breakdown", "scene_plan", "assets", "edit", "compose", "publish",
]

# Which stage produces each artifact (the stage you "enter at" when you provide it)
STAGE_OF_ARTIFACT = {
    "story_bible": "concept",
    "proposal_packet": "proposal",
    "cast": "characters",
    "story": "story",
    "script": "script",
    "locations": "breakdown",
    "sequence_plan": "breakdown",
    "scene_plan": "scene_plan",
    "asset_manifest": "assets",
    "edit_decisions": "edit",
    "render_report": "compose",
}

VALID_MODES = frozenset({"lock", "seed", "reference"})


def load_provided_manifest(project_dir: str | Path) -> list[dict[str, Any]]:
    """Read a project's provided-material manifest.

    Looks for ``<project_dir>/provided/manifest.json``. Each entry is
    ``{"artifact": <name>, "path": <relpath>, "mode": lock|seed|reference,
    "format": <optional>}``. Returns [] if the manifest is absent.
    """
    project_dir = Path(project_dir)
    manifest = project_dir / "provided" / "manifest.json"
    if not manifest.is_file():
        return []
    with open(manifest, encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("provided", data) if isinstance(data, dict) else data
    out: list[dict[str, Any]] = []
    for e in entries:
        mode = e.get("mode", "seed")
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid provided mode {mode!r}; expected one of {sorted(VALID_MODES)}")
        if e.get("artifact") not in STAGE_OF_ARTIFACT:
            raise ValueError(f"Unknown provided artifact {e.get('artifact')!r}")
        out.append({"artifact": e["artifact"], "path": e.get("path"),
                    "mode": mode, "format": e.get("format")})
    return out


def entry_plan(provided: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the entry stage and the derive-upward / generate-downward split.

    Given provided material, the pipeline enters at the EARLIEST provided stage,
    derives every stage above it by extraction, and generates every stage below.
    Reference-mode material informs but does not set the entry point.
    """
    setting = [p for p in provided if p["mode"] in ("lock", "seed")]
    if not setting:
        return {"entry_stage": PIPELINE_STAGE_ORDER[0],
                "derive_upstream": [], "generate_downstream": PIPELINE_STAGE_ORDER[:]}
    idxs = [PIPELINE_STAGE_ORDER.index(STAGE_OF_ARTIFACT[p["artifact"]]) for p in setting]
    entry_idx = min(idxs)
    entry_stage = PIPELINE_STAGE_ORDER[entry_idx]
    return {
        "entry_stage": entry_stage,
        "derive_upstream": PIPELINE_STAGE_ORDER[:entry_idx],
        "generate_downstream": PIPELINE_STAGE_ORDER[entry_idx + 1:],
        "locked": [p["artifact"] for p in provided if p["mode"] == "lock"],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return s or "x"


_SLUG_PREFIX_RE = re.compile(r"^\s*(INT\.?/EXT\.?|EXT\.?/INT\.?|INT\.?|EXT\.?|EST\.?|I/E)\s+", re.I)


def parse_slugline(slugline: str) -> dict[str, Optional[str]]:
    """Split a slugline into location name and time of day.

    'EXT. ISLAND JETTY - DAY' -> {'location': 'ISLAND JETTY', 'time_of_day': 'DAY'}
    """
    body = _SLUG_PREFIX_RE.sub("", slugline).strip()
    time_of_day = None
    # Time is conventionally after the last ' - ' / ' — ' separator.
    m = re.split(r"\s+[-–—]\s+", body)
    if len(m) > 1:
        location = m[0].strip()
        time_of_day = m[-1].strip()
    else:
        location = body
    return {"location": location or None, "time_of_day": time_of_day}


# ---------------------------------------------------------------------------
# Ingestion adapters -> script artifact (screenplay shape)
# ---------------------------------------------------------------------------

def _new_scene(idx: int, slugline: str) -> dict[str, Any]:
    return {"id": f"sc_{idx:03d}", "slugline": slugline.strip(),
            "location_id": _slug(parse_slugline(slugline)["location"] or f"loc_{idx}"),
            "action": "", "cast": [], "dialogue": []}


def fdx_to_script(path: str | Path, title: Optional[str] = None) -> dict[str, Any]:
    """Parse a Final Draft (.fdx) file into a screenplay-shaped script artifact."""
    root = ET.parse(path).getroot()
    scenes: list[dict[str, Any]] = []
    cur: Optional[dict[str, Any]] = None
    pending_character: Optional[str] = None
    pending_paren: Optional[str] = None

    for para in root.iter("Paragraph"):
        ptype = (para.get("Type") or "").strip()
        text = "".join(t.text or "" for t in para.iter("Text")).strip()
        if not text and ptype != "Scene Heading":
            continue
        if ptype == "Scene Heading":
            cur = _new_scene(len(scenes) + 1, text)
            scenes.append(cur)
            pending_character = pending_paren = None
        elif cur is None:
            continue
        elif ptype == "Action":
            cur["action"] = (cur["action"] + " " + text).strip()
        elif ptype == "Character":
            pending_character = text
            cid = _slug(text)
            if cid not in cur["cast"]:
                cur["cast"].append(cid)
        elif ptype == "Parenthetical":
            pending_paren = text.strip("()")
        elif ptype == "Dialogue" and pending_character:
            line = {"character_id": _slug(pending_character), "line": text}
            if pending_paren:
                line["parenthetical"] = pending_paren
            cur["dialogue"].append(line)
            pending_paren = None
    return _finalize_script(scenes, title or Path(path).stem)


_FOUNTAIN_SCENE_RE = re.compile(r"^(\.|INT\.?|EXT\.?|EST\.?|INT\.?/EXT\.?|EXT\.?/INT\.?|I/E)\b", re.I)


def fountain_to_script(text: str, title: Optional[str] = None) -> dict[str, Any]:
    """Parse Fountain-style screenplay plain text into a script artifact."""
    lines = text.splitlines()
    scenes: list[dict[str, Any]] = []
    cur: Optional[dict[str, Any]] = None
    pending_character: Optional[str] = None
    pending_paren: Optional[str] = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1
        if not line:
            pending_character = None
            continue
        if _FOUNTAIN_SCENE_RE.match(line):
            heading = line[1:].strip() if line.startswith(".") else line
            cur = _new_scene(len(scenes) + 1, heading)
            scenes.append(cur)
            pending_character = pending_paren = None
        elif cur is None:
            continue
        elif line.startswith("(") and line.endswith(")"):
            pending_paren = line.strip("()")
        elif pending_character:
            cline = {"character_id": _slug(pending_character), "line": line}
            if pending_paren:
                cline["parenthetical"] = pending_paren
            cur["dialogue"].append(cline)
            pending_paren = None
        elif line.isupper() and len(line) <= 40 and not line.endswith("."):
            # A character cue: UPPERCASE line introducing dialogue.
            name = re.sub(r"\s*\(.*\)\s*$", "", line)
            pending_character = name
            cid = _slug(name)
            if cid not in cur["cast"]:
                cur["cast"].append(cid)
        else:
            cur["action"] = (cur["action"] + " " + line).strip()
    return _finalize_script(scenes, title or "Imported Screenplay")


def _finalize_script(scenes: list[dict[str, Any]], title: str) -> dict[str, Any]:
    for s in scenes:
        if not s["action"]:
            s["action"] = s["slugline"]
        for key in ("cast", "dialogue"):
            if not s[key]:
                del s[key]
    return {"version": "1.0", "title": title, "form": "screenplay",
            "origin": "user_provided", "scenes": scenes}


def script_from_file(path: str | Path, title: Optional[str] = None) -> dict[str, Any]:
    """Dispatch a screenplay file to the right adapter by extension."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".fdx":
        return fdx_to_script(path, title)
    if ext in (".fountain", ".txt"):
        return fountain_to_script(path.read_text(encoding="utf-8"), title)
    if ext == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if ext == ".pdf":
        raise NotImplementedError(
            "PDF screenplay ingestion needs text extraction. Install a PDF text "
            "extractor (e.g. `pip install pypdf`), extract the text, then pass it "
            "to fountain_to_script()."
        )
    raise ValueError(f"Unsupported screenplay format: {ext}")


def image_folder_to_reference_assets(folder: str | Path,
                                     project_dir: Optional[str | Path] = None) -> list[str]:
    """Enumerate image files in a folder as reference-asset paths.

    Returns paths relative to ``project_dir`` when given (matching how cast /
    locations store reference_assets), else absolute.
    """
    folder = Path(folder)
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in exts)
    if project_dir is not None:
        base = Path(project_dir)
        return [str(p.relative_to(base)) if base in p.parents else str(p) for p in files]
    return [str(p) for p in files]


# ---------------------------------------------------------------------------
# Reverse-derivation: script -> breakdown (cast, locations, sequence_plan)
# ---------------------------------------------------------------------------

def derive_breakdown(script: dict[str, Any],
                     existing_cast: Optional[dict[str, Any]] = None
                     ) -> dict[str, dict[str, Any]]:
    """Extract cast, locations, and a sequence_plan FROM a screenplay script.

    This is the mechanical 1st-AD pass. The breakdown-director refines the result
    (roles, descriptions, sequence boundaries). Principals already in
    ``existing_cast`` are preserved; new speaking parts are added as
    tier='breakdown'.
    """
    scenes = script.get("scenes")
    if not scenes:
        raise ValueError("derive_breakdown requires a screenplay-shaped script (scenes[])")

    # --- locations: unique by slugified name, in first-seen order ---
    locations: dict[str, dict[str, Any]] = {}
    for s in scenes:
        parsed = parse_slugline(s.get("slugline", ""))
        name = parsed["location"]
        if not name:
            continue
        lid = s.get("location_id") or _slug(name)
        if lid not in locations:
            locations[lid] = {
                "id": lid, "display_name": name.title(),
                "description": f"Derived from slugline: {s.get('slugline', '').strip()}",
                "origin": "user_provided",
            }
            if parsed["time_of_day"]:
                locations[lid]["time_of_day"] = parsed["time_of_day"].title()

    # --- cast: principals preserved, speaking parts added as breakdown ---
    chars: dict[str, dict[str, Any]] = {}
    if existing_cast:
        for c in existing_cast.get("characters", []):
            chars[c["id"]] = dict(c)
    for s in scenes:
        for d in s.get("dialogue", []):
            cid = d["character_id"]
            if cid not in chars:
                chars[cid] = {"id": cid, "display_name": cid.replace("_", " ").title(),
                              "role": "minor", "tier": "breakdown", "origin": "user_provided"}

    # --- sequences: contiguous runs of the same location ---
    sequences: list[dict[str, Any]] = []
    order = 0
    for s in scenes:
        lid = s.get("location_id") or _slug(parse_slugline(s.get("slugline", ""))["location"] or "loc")
        if sequences and sequences[-1]["primary_location_id"] == lid:
            sequences[-1]["scene_ids"].append(s["id"])
            for cid in s.get("cast", []):
                if cid not in sequences[-1]["cast_ids"]:
                    sequences[-1]["cast_ids"].append(cid)
        else:
            order += 1
            label = locations.get(lid, {}).get("display_name", lid.replace("_", " ").title())
            sequences.append({
                "id": f"seq_{order:02d}", "order": order, "label": label,
                "primary_location_id": lid, "cast_ids": list(s.get("cast", [])),
                "scene_ids": [s["id"]],
            })

    return {
        "cast": {"version": "1.0", "characters": list(chars.values())},
        "locations": {"version": "1.0", "locations": list(locations.values())},
        "sequence_plan": {"version": "1.0", "origin": "user_provided", "sequences": sequences},
    }
