#!/usr/bin/env python3
"""OpenMontage Observer — a read-only dashboard over projects/ + pipelines/.

Stdlib only. Serves the single-file frontend in app/ and a read-only /api/state
endpoint that reflects on-disk production state. It NEVER writes — the agent is
the sole writer; you approve gates in your agent session. When no projects exist
on disk it returns an empty list and the frontend falls back to bundled sample
data, so it renders out of the box.

    python observer/server.py            # http://localhost:8137
    python observer/server.py --port 9000
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # repo root
APP_DIR = HERE / "app"
PROJECTS_DIR = ROOT / "projects"
PIPELINES_DIR = ROOT / "pipelines"
sys.path.insert(0, str(ROOT))

_PIPE_THUMB = {
    "narrative-film": ["#2a2236", "#0c0a12"], "brand-narrative": ["#2a2010", "#0c0a06"],
    "cinematic": ["#2a1a16", "#0c0706"], "animation": ["#0e2630", "#060a0c"],
}


def _stage_artifacts():
    """{stage: canonical_artifact} — falls back to a static map if lib is unavailable."""
    try:
        from lib.checkpoint import CANONICAL_STAGE_ARTIFACTS
        return CANONICAL_STAGE_ARTIFACTS
    except Exception:
        return {}


def _stage_order(pipeline_type):
    try:
        from lib.checkpoint import get_pipeline_stages
        return get_pipeline_stages(pipeline_type)
    except Exception:
        return ["research", "proposal", "script", "scene_plan", "assets", "edit", "compose", "publish"]


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _checkpoints(name):
    """Read this project's checkpoints as {stage: checkpoint_dict}."""
    out = {}
    d = PIPELINES_DIR / name
    if not d.is_dir():
        return out
    for p in d.glob("checkpoint_*.json"):
        cp = _read_json(p)
        if isinstance(cp, dict) and cp.get("stage"):
            out[cp["stage"]] = cp
    return out


def _title(name):
    art = PROJECTS_DIR / name / "artifacts"
    for fn in ("story_bible.json", "brief.json"):
        data = _read_json(art / fn)
        if isinstance(data, dict) and data.get("title"):
            return data["title"]
    return name.replace("-", " ").title()


def _cost(name):
    for cand in (PROJECTS_DIR / name / "artifacts" / "cost_log.json",
                 PIPELINES_DIR / name / "cost_log.json"):
        data = _read_json(cand)
        if isinstance(data, dict):
            for key in ("total_usd", "spent_usd", "total"):
                if isinstance(data.get(key), (int, float)):
                    return f"${data[key]:.2f}"
    return "$0.00"


def _build_project(name):
    cps = _checkpoints(name)
    if not cps:
        return None
    pipeline = next((cp.get("pipeline_type") for cp in cps.values() if cp.get("pipeline_type")), "unknown")
    order = _stage_order(pipeline)
    awaiting = next((s for s in order if cps.get(s, {}).get("status") == "awaiting_human"), None)
    failed = next((s for s in order if cps.get(s, {}).get("status") == "failed"), None)
    done_stages = {s for s in order if cps.get(s, {}).get("status") == "completed"}

    if awaiting:
        status = "awaiting"
    elif failed:
        status = "failed"
    elif done_stages == set(order):
        status = "done"
    else:
        status = "running"

    # next stage to run (first not completed) — highlight as running/failed
    nxt = next((s for s in order if s not in done_stages), None)
    stages = []
    for s in order:
        st = ("done" if s in done_stages else
              "needs" if s == awaiting else
              "failed" if s == failed else
              ("running" if (s == nxt and status == "running") else "pending"))
        stages.append({"name": s, "status": st})

    proj = {
        "name": name, "title": _title(name), "pipeline": pipeline, "status": status,
        "cost": _cost(name), "updated": "", "stageLabel": (awaiting or failed or nxt or "done"),
        "dur": "", "thumb": _PIPE_THUMB.get(pipeline, ["#1b2230", "#0a0b0d"]), "stages": stages,
    }
    if awaiting:
        proj["gate"] = {"stage": awaiting,
                        "title": f"{awaiting} awaiting your approval",
                        "message": f"{awaiting} awaiting your approval"}
    return proj


def build_state():
    if not PROJECTS_DIR.is_dir():
        return {"projects": [], "generated_at": "no projects/"}
    projects = []
    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        try:
            p = _build_project(d.name)
            if p:
                projects.append(p)
        except Exception as exc:  # never let one bad project break the dashboard
            projects.append({"name": d.name, "title": d.name, "pipeline": "unknown",
                             "status": "failed", "cost": "$0.00", "updated": "",
                             "stages": [], "error": str(exc)})
    return {"projects": projects, "generated_at": "live"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/state":
            return self._send(200, json.dumps(build_state()).encode(), "application/json")
        if path == "/api/health":
            return self._send(200, b'{"ok":true,"readonly":true}', "application/json")
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        fpath = (APP_DIR / rel).resolve()
        if APP_DIR not in fpath.parents and fpath != APP_DIR or not fpath.is_file():
            return self._send(404, b"not found", "text/plain")
        ctype = {"html": "text/html", "js": "application/javascript",
                 "css": "text/css", "json": "application/json"}.get(fpath.suffix.lstrip("."), "text/plain")
        return self._send(200, fpath.read_bytes(), ctype + "; charset=utf-8")


def main():
    ap = argparse.ArgumentParser(description="OpenMontage Observer (read-only)")
    ap.add_argument("--port", type=int, default=8137)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"OpenMontage Observer (read-only) → http://{args.host}:{args.port}")
    print(f"  reading: {PROJECTS_DIR}  +  {PIPELINES_DIR}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
