# navi/core/memory.py
from __future__ import annotations
import os, json, time, threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Config
MEM_DIR  = Path(os.getenv("NAVI_MEMORY_DIR", "data/memory"))
MEM_FILE = MEM_DIR / "navi_memory.json"
MEM_DIR.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()

def _load() -> Dict[str, Any]:
    if not MEM_FILE.exists():
        return {"people": {}, "global_facts": [], "interactions": []}
    try:
        return json.loads(MEM_FILE.read_text(encoding="utf-8"))
    except Exception:
        # corrupt file fallback (don't crash service)
        ts = int(time.time())
        MEM_FILE.rename(MEM_FILE.with_suffix(f".corrupt.{ts}.json"))
        return {"people": {}, "global_facts": [], "interactions": []}

def _save(data: Dict[str, Any]) -> None:
    tmp = MEM_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(MEM_FILE)

def now() -> float:
    return time.time()

# --------------------------#
#         Public API        #
# --------------------------#

def remember_person(uid: str, name: Optional[str] = None, **traits) -> None:
    """
    Upsert a person record (by uid). You can pass any traits:
    e.g., nickname="Josh", likes=["dad jokes"], room="office"
    """
    with _lock:
        db = _load()
        people = db.setdefault("people", {})
        p = people.get(uid, {"facts": [], "recent_summary": "", "meta": {}})
        if name:
            p["name"] = name
        # merge traits into meta
        p["meta"].update({k: v for k, v in traits.items() if v is not None})
        p["updated_at"] = now()
        people[uid] = p
        _save(db)

def remember_fact(uid: Optional[str], fact: str, source: str = "voice", weight: float = 1.0) -> None:
    """
    Store a free-form fact either scoped to a person (uid) or globally.
    """
    if not fact:
        return
    rec = {"text": fact.strip(), "source": source, "weight": float(weight), "t": now()}
    with _lock:
        db = _load()
        if uid:
            p = db.setdefault("people", {}).setdefault(uid, {"facts": [], "recent_summary": "", "meta": {}})
            p["facts"].append(rec)
            p["updated_at"] = now()
        else:
            db.setdefault("global_facts", []).append(rec)
        _save(db)

def save_interaction(uid: Optional[str], user_text: str, navi_reply: str) -> None:
    """
    Append raw interaction (simple log). Later we'll auto-summarize.
    """
    with _lock:
        db = _load()
        it = db.setdefault("interactions", [])
        it.append({
            "uid": uid, "user": (user_text or "").strip(), "navi": (navi_reply or "").strip(), "t": now()
        })
        # keep it bounded
        if len(it) > 500:
            del it[: len(it) - 500]
        _save(db)

def set_recent_summary(uid: str, summary: str) -> None:
    with _lock:
        db = _load()
        p = db.setdefault("people", {}).setdefault(uid, {"facts": [], "recent_summary": "", "meta": {}})
        p["recent_summary"] = (summary or "").strip()
        p["updated_at"] = now()
        _save(db)

def get_person_context(uid: Optional[str]) -> str:
    """
    Return a short, human-readable context block that we can prepend to the system prompt.
    """
    db = _load()
    lines: List[str] = []

    if uid:
        p = db.get("people", {}).get(uid)
        if p:
            nm = p.get("name") or uid
            lines.append(f"User: {nm}")
            if p.get("meta"):
                # flatten small meta dict
                meta_pairs = []
                for k, v in p["meta"].items():
                    txt = ", ".join(v) if isinstance(v, list) else str(v)
                    meta_pairs.append(f"{k}: {txt}")
                if meta_pairs:
                    lines.append("Traits: " + "; ".join(meta_pairs))
            # include last ~3 facts
            facts = p.get("facts", [])[-3:]
            if facts:
                lines.append("Recent facts:")
                for f in facts:
                    lines.append(f"- {f['text']}")
            if p.get("recent_summary"):
                lines.append("Recent summary: " + p["recent_summary"])

    # include a couple of global facts
    gf = db.get("global_facts", [])[-2:]
    if gf:
        lines.append("Global:")
        for f in gf:
            lines.append(f"- " + f["text"])

    return "\n".join(lines).strip()

def export_all() -> Dict[str, Any]:
    """Read-only export for debugging/backups."""
    return _load()
