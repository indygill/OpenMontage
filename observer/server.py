#!/usr/bin/env python3
"""OpenMontage Observer — a read-only dashboard over projects/ + pipelines/.

Stdlib only. Serves the single-file frontend in app/ and a read-only /api/state
endpoint that reflects on-disk production state — dashboard, project overview,
and every per-project tab (shots, assets, render, cost, activity) plus the Inbox
and Capabilities, all read from real artifacts/checkpoints/registry. It NEVER
writes — the agent is the sole writer; you approve gates in your agent session.
When no projects exist it returns an empty list and the frontend falls back to
bundled sample data, so it renders out of the box.

    python observer/server.py            # http://localhost:8137
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
APP_DIR = HERE / "app"
PROJECTS_DIR = ROOT / "projects"
PIPELINES_DIR = ROOT / "pipelines"
sys.path.insert(0, str(ROOT))

_PIPE_THUMB = {
    "narrative-film": ["#2a2236", "#0c0a12"], "brand-narrative": ["#2a2010", "#0c0a06"],
    "cinematic": ["#2a1a16", "#0c0706"], "animation": ["#0e2630", "#060a0c"],
    "animated-explainer": ["#10202e", "#06090c"],
}
_GRADS = [["#26303a", "#0a0d10"], ["#2a2620", "#0c0a06"], ["#241c14", "#0a0806"],
          ["#2a2236", "#0a0810"], ["#1e2630", "#080a0d"], ["#2a201a", "#0c0906"],
          ["#10202e", "#06090c"], ["#241a26", "#0a0810"], ["#10243a", "#06090d"],
          ["#1a1030", "#08060c"], ["#10302a", "#06080c"], ["#2a1020", "#0c0608"]]
_TYPE_SHORT = {"image": "IMG", "video": "VID", "audio": "AUD", "narration": "VO",
               "music": "MUS", "sfx": "SFX", "diagram": "DIA", "animation": "ANI",
               "subtitle": "SRT", "code_snippet": "CODE"}
_WAVE = {"audio", "narration", "music", "sfx"}
_grad = lambda i: _GRADS[i % len(_GRADS)]


# ---- small readers / formatters -------------------------------------------
def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _art(name, stem):
    return _read_json(PROJECTS_DIR / name / "artifacts" / f"{stem}.json")


def _fmtdur(sec):
    try:
        sec = int(round(float(sec)))
        return f"{sec // 60}:{sec % 60:02d}"
    except Exception:
        return ""


def _size(b):
    try:
        b = float(b)
        for u in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"
    except Exception:
        return ""


def _ago(iso):
    if not iso:
        return ""
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        s = (datetime.now(timezone.utc) - t).total_seconds()
        if s < 60:
            return "now"
        if s < 3600:
            return f"{int(s // 60)}m ago"
        if s < 86400:
            return f"{int(s // 3600)}h ago"
        return f"{int(s // 86400)}d ago"
    except Exception:
        return ""


def _stage_artifacts():
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


def _checkpoints(name):
    out = {}
    d = PIPELINES_DIR / name
    if d.is_dir():
        for p in d.glob("checkpoint_*.json"):
            cp = _read_json(p)
            if isinstance(cp, dict) and cp.get("stage"):
                out[cp["stage"]] = cp
    return out


def _title(name):
    for fn in ("story_bible", "brief"):
        data = _art(name, fn)
        if isinstance(data, dict) and data.get("title"):
            return data["title"]
    return name.replace("-", " ").title()


# ---- detail builders (one per tab) ----------------------------------------
def _shotlist(name):
    sp = _art(name, "scene_plan")
    if not sp or not sp.get("scenes"):
        return None
    out = []
    for i, s in enumerate(sp["scenes"]):
        sl = s.get("shot_language") or {}
        lang = []
        if sl.get("shot_size"):
            lang.append(sl["shot_size"].replace("_", "-").upper())
        if sl.get("lens_mm"):
            lang.append(f"{sl['lens_mm']}mm")
        if sl.get("lighting_key"):
            lang.append(sl["lighting_key"].replace("_", "-"))
        if sl.get("camera_movement"):
            lang.append(sl["camera_movement"].replace("_", "-"))
        if not lang and s.get("framing"):
            lang.append(s["framing"])
        try:
            d = int(round(float(s["end_seconds"]) - float(s["start_seconds"])))
            dur = f"{d // 60}:{d % 60:02d}"
        except Exception:
            dur = ""
        out.append({"n": i + 1, "seq": s.get("sequence_id") or s.get("type") or "",
                    "desc": s.get("description", ""), "lang": lang or ["shot"],
                    "dur": dur, "thumb": _grad(i)})
    return out


def _assets(name):
    am = _art(name, "asset_manifest")
    if not am or not am.get("assets"):
        return None
    out = []
    for i, a in enumerate(am["assets"]):
        t = a.get("type", "image")
        lic = (a.get("license") or "").lower()
        prov = ("provided" if "user" in lic else
                "stock" if (a.get("subtype") == "stock" or a.get("original_url")) else "generated")
        item = {"type": _TYPE_SHORT.get(t, t[:3].upper()),
                "file": (a.get("path", "asset")).split("/")[-1],
                "tool": a.get("source_tool") or a.get("provider") or "", "prov": prov}
        if t in _WAVE:
            item["kind"] = "wave"
            item["wc"] = "#4DA3FF" if t in ("audio", "narration") else "#646b78"
        else:
            item["kind"] = "img"
            item["thumb"] = _grad(i)
        out.append(item)
    return out


def _render(name):
    rr = _art(name, "render_report")
    if not rr or not rr.get("outputs"):
        return None
    outs = rr["outputs"]
    outputs = [{"role": o.get("role", "output"),
                "aspect": (o.get("role", "output").capitalize() + " " + (o.get("resolution", ""))).strip(),
                "res": o.get("resolution", ""), "size": _size(o.get("file_size_bytes")),
                "thumb": _grad(i)} for i, o in enumerate(outs)]
    variants = [{"label": o.get("role", "out").capitalize(), "sub": o.get("resolution", "")} for o in outs]
    hero = outs[0]
    facts = (f"{hero.get('path', 'final.mp4')}   ·   {hero.get('codec', 'h264')} · "
             f"{hero.get('resolution', '')} · {hero.get('fps', '')}fps · "
             f"{_fmtdur(hero.get('duration_seconds'))} · {_size(hero.get('file_size_bytes'))}   ·   ✓ ffprobe verified")
    rt = rr.get("render_time_seconds")
    facts2 = {"Runtime": (rr.get("render_grammar") or "").split("-")[0].capitalize() or "—",
              "Render time": (f"{int(rt)}s" if isinstance(rt, (int, float)) else ""),
              "Encoding": " · ".join(x for x in (hero.get("codec"), hero.get("audio_codec")) if x)}
    return {"dur": _fmtdur(hero.get("duration_seconds")), "variants": variants,
            "outputs": outputs, "facts": facts, "facts2": {k: v for k, v in facts2.items() if v}}


def _budget_total():
    try:
        from lib.config_model import OpenMontageConfig
        return float(OpenMontageConfig.load().budget.total_usd)
    except Exception:
        return 2.0


def _cost_data(name):
    cl = _art(name, "cost_log") or _read_json(PIPELINES_DIR / name / "cost_log.json")
    spent, items = 0.0, []
    if cl:
        for e in cl.get("entries", []):
            c = e.get("actual_usd") or e.get("reserved_usd") or e.get("estimated_usd") or 0
            spent += c
            items.append({"tool": e.get("tool", ""), "prov": e.get("operation", ""),
                          "qty": "1", "cost": f"${c:.2f}"})
        spent = cl.get("budget_spent_usd", spent)
        btot = cl.get("budget_total_usd") or _budget_total()
    else:
        btot = _budget_total()
    return spent, items, btot, cl


def _decisions(name):
    dl = _art(name, "decision_log") or _read_json(PIPELINES_DIR / name / "decision_log.json")
    out = []
    if dl:
        for d in dl.get("decisions", []):
            opts = " · ".join(o.get("label", "") for o in d.get("options_considered", []))
            out.append({"id": d.get("category") or d.get("decision_id"), "when": d.get("stage", ""),
                        "why": d.get("reason") or d.get("selected", ""), "options": "options: " + opts})
    return out


def _budget_obj(spent, btot):
    pct = int(round(100 * spent / btot)) if btot else 0
    return {"used": f"${spent:.2f}", "total": f"${btot:.2f}", "pct": min(100, max(0, pct))}


def _facts(name):
    f = {}
    ed, pp, sp, sb = _art(name, "edit_decisions"), _art(name, "proposal_packet"), _art(name, "scene_plan"), _art(name, "story_bible")
    rt = (ed or {}).get("render_runtime") or ((pp or {}).get("production_plan") or {}).get("render_runtime")
    if isinstance(rt, str):
        f["Render runtime"] = rt.capitalize()
    play = (sp or {}).get("style_playbook") or ((sb or {}).get("world") or {}).get("style_playbook")
    if play:
        f["Style playbook"] = play
    fmt = _format(name)
    if fmt:
        f["Format"] = fmt
    return f or None


def _format(name):
    sb = _art(name, "story_bible")
    if sb and sb.get("format"):
        fo = sb["format"]
        parts = [str(fo.get("kind", "")).replace("_", " ")]
        if fo.get("aspect_ratio"):
            parts.append(fo["aspect_ratio"])
        if fo.get("target_duration_seconds"):
            parts.append(_fmtdur(fo["target_duration_seconds"]))
        return " · ".join(p for p in parts if p)
    br = _art(name, "brief")
    if br:
        parts = [br.get("target_platform", "")]
        if br.get("target_duration_seconds"):
            parts.append(_fmtdur(br["target_duration_seconds"]))
        return " · ".join(p for p in parts if p)
    return ""


def _artifacts_list(order, cps, awaiting):
    SA = _stage_artifacts()
    out, seen = [], set()
    for s in order:
        canon = SA.get(s)
        if not canon or canon in seen:
            continue
        seen.add(canon)
        st = ("done" if cps.get(s, {}).get("status") == "completed" else
              "needs" if s == awaiting else "pending")
        out.append({"name": canon, "status": st})
    return out


def _activity(cps):
    items = sorted(cps.values(), key=lambda c: c.get("timestamp", ""))
    evs = [{"time": (c.get("timestamp", "") or "")[11:16] or "·", "type": "cp",
            "main": f"wrote checkpoint_{c.get('stage')}.json",
            "sub": f"status: {c.get('status')}"} for c in items]
    return evs[-12:][::-1] or None


def _build_project(name):
    cps = _checkpoints(name)
    if not cps:
        return None
    pipeline = next((cp.get("pipeline_type") for cp in cps.values() if cp.get("pipeline_type")), "unknown")
    order = _stage_order(pipeline)
    awaiting = next((s for s in order if cps.get(s, {}).get("status") == "awaiting_human"), None)
    failed = next((s for s in order if cps.get(s, {}).get("status") == "failed"), None)
    done = {s for s in order if cps.get(s, {}).get("status") == "completed"}
    status = ("awaiting" if awaiting else "failed" if failed else "done" if done == set(order) else "running")
    nxt = next((s for s in order if s not in done), None)
    stages = [{"name": s, "status": ("done" if s in done else "needs" if s == awaiting
               else "failed" if s == failed else "running" if (s == nxt and status == "running") else "pending")}
              for s in order]
    latest_ts = max((c.get("timestamp", "") for c in cps.values()), default="")

    spent, items, btot, cl = _cost_data(name)
    shotlist = _shotlist(name)
    decisions = _decisions(name)
    current = awaiting or failed or nxt or order[-1]
    proj = {
        "name": name, "title": _title(name), "pipeline": pipeline, "status": status,
        "cost": f"${spent:.2f}", "updated": _ago(latest_ts),
        "stageLabel": (awaiting + " — failed" if failed and failed == awaiting else (failed + " — failed" if failed else current)),
        "dur": _format(name).split("·")[-1].strip() if _format(name) else "",
        "thumb": _PIPE_THUMB.get(pipeline, ["#1b2230", "#0a0b0d"]), "stages": stages,
    }
    detail = {
        "format": _format(name) or None,
        "stageCaption": f"Stage {order.index(current) + 1} of {len(order)} · {current}",
        "budget": _budget_obj(spent, btot),
        "artifacts": _artifacts_list(order, cps, awaiting),
        "facts": _facts(name),
        "decision": decisions[0] if decisions else None,
        "activity": _activity(cps),
        "shotList": shotlist,
        "shots": [s["thumb"] for s in shotlist[:6]] if shotlist else None,
        "assets": _assets(name),
        "render": _render(name),
        "cost": ({"budget": _budget_obj(spent, btot), "items": items,
                  "total": f"${spent:.2f}", "decisions": decisions} if (items or decisions) else None),
    }
    proj["detail"] = {k: v for k, v in detail.items() if v is not None}

    if awaiting:
        msg = (f"Shot list awaiting your approval — {len(shotlist)} shots"
               if awaiting == "scene_plan" and shotlist else f"{awaiting} awaiting your approval")
        review = cps[awaiting].get("review") or {}
        findings = [f.get("message", f) if isinstance(f, dict) else f
                    for f in (review.get("findings") or [])][:3]
        gate = {"stage": awaiting, "title": msg, "message": msg}
        if shotlist and awaiting == "scene_plan":
            gate["meta"] = f"{len(shotlist)} shots · {len({s['seq'] for s in shotlist})} sequences"
        if findings:
            gate["findings"] = findings
        proj["gate"] = gate
    return proj


def _inbox(projects):
    needs, recent = [], []
    for p in projects:
        base = {"name": p["name"], "title": p["title"], "pipeline": p["pipeline"], "time": p.get("updated", "")}
        st = p["status"]
        if st == "awaiting":
            needs.append({**base, "state": "needs", "message": (p.get("gate") or {}).get("message", f"{p.get('stageLabel')} awaiting approval")})
        elif st == "failed":
            recent.append({**base, "state": "failed", "message": f"{p.get('stageLabel')}"})
        elif st == "done":
            recent.append({**base, "state": "done", "message": "Render complete"})
        else:
            recent.append({**base, "state": "running", "message": f"{p.get('stageLabel')} in progress"})
    return {"needs": needs, "recent": recent}


_CAP_CACHE = "unset"


def _capabilities():
    global _CAP_CACHE
    if _CAP_CACHE != "unset":
        return _CAP_CACHE
    # runtimes via filesystem (cheap, dependency-free, always works)
    rt = []
    rt.append({"name": "FFmpeg", "warn": not shutil.which("ffmpeg"),
               "note": "available" if shutil.which("ffmpeg") else "not on PATH"})
    rem_ok = (ROOT / "remotion-composer" / "node_modules").is_dir() and bool(shutil.which("npx"))
    rt.append({"name": "Remotion", "warn": not rem_ok,
               "note": "npx + node_modules ready" if rem_ok else "node_modules not installed"})
    npx = bool(shutil.which("npx"))
    rt.append({"name": "HyperFrames", "warn": not npx, "note": "via npx" if npx else "npx not found"})
    rows, setup = [], []
    try:  # rich provider rows via the registry (may be heavy / unavailable)
        from tools.tool_registry import registry
        registry.discover()
        s = registry.provider_menu_summary()
        for cap in s.get("capabilities", []):
            rows.append({"name": str(cap.get("family") or cap.get("capability") or cap.get("name", "")).replace("_", " ").capitalize(),
                         "conf": cap.get("configured", 0), "total": cap.get("total", 0),
                         "provs": cap.get("providers") or cap.get("configured_providers") or ["—"]})
        for o in s.get("setup_offers", []):
            setup.append({"env": o.get("env_var") or o.get("env") or o.get("name", ""),
                          "unlocks": o.get("description") or o.get("unlocks", "")})
    except Exception:
        pass
    _CAP_CACHE = {"runtimes": rt, "rows": rows, "setup": setup}
    return _CAP_CACHE


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
        except Exception as exc:
            projects.append({"name": d.name, "title": d.name.replace("-", " ").title(),
                             "pipeline": "unknown", "status": "failed", "cost": "$0.00",
                             "updated": "", "stages": [], "error": str(exc)})
    if not projects:
        return {"projects": [], "generated_at": "no checkpoints"}
    return {"projects": projects, "inbox": _inbox(projects),
            "capabilities": _capabilities(), "generated_at": "live"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
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
        if (APP_DIR not in fpath.parents) or not fpath.is_file():
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
