# navi/core/memory.py

from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from datetime import datetime

# --- Paths (override if you want via env) ---
# <project_root>/data/memory/navi_memory.json
def _default_memory_dir() -> Path:
    # memory.py is expected at navi/core/memory.py
    # parents: [memory.py]=0 -> core=1 -> navi=2 -> project_root=3
    here = Path(__file__).resolve()
    project_root = here.parents[3] if len(here.parents) >= 4 else here.parent
    return project_root / "data" / "memory"

MEM_DIR = Path(os.getenv("NAVI_DATA_DIR", _default_memory_dir()))
MEM_FILE = Path(os.getenv("NAVI_MEMORY_FILE", str(MEM_DIR / "navi_memory.json")))

# --- Bootstrapping ---
def _ensure_store() -> None:
    MEM_DIR.mkdir(parents=True, exist_ok=True)
    if not MEM_FILE.exists():
        MEM_FILE.write_text("{}", encoding="utf-8")

def _safe_load() -> dict:
    _ensure_store()
    try:
        raw = MEM_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        return json.loads(raw)
    except json.JSONDecodeError:
        # keep a backup of the broken file and start fresh
        backup = MEM_FILE.with_suffix(".corrupt.json")
        try:
            MEM_FILE.replace(backup)
        except Exception:
            pass
        MEM_FILE.write_text("{}", encoding="utf-8")
        return {}

def _atomic_save(obj: dict) -> None:
    _ensure_store()
    tmp = tempfile.NamedTemporaryFile("w", delete=False, dir=str(MEM_DIR), encoding="utf-8")
    try:
        json.dump(obj, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        Path(tmp.name).replace(MEM_FILE)  # atomic on same filesystem
    finally:
        try:
            if Path(tmp.name).exists():
                Path(tmp.name).unlink(missing_ok=True)
        except Exception:
            pass

# --- Public helpers you already use elsewhere ---
def get_person_context() -> str:
    """
    Returns a short, rolling 'who/what matters' string Navi can use as context.
    """
    data = _safe_load()
    facts = data.get("facts", [])
    if not facts:
        return ""
    # keep it compact; adjust to taste
    return "; ".join(facts[-12:])

def remember_fact(text: str) -> None:
    """
    Persist a concise fact (e.g., 'User likes peppermint tea')
    """
    if not text or not text.strip():
        return
    data = _safe_load()
    data.setdefault("facts", [])
    if text not in data["facts"]:
        data["facts"].append(text.strip())
    _atomic_save(data)

def save_interaction(role: str, content: str) -> None:
    """
    Append to an interactions log for later summarization/distillation.
    role ? {'user','assistant','system'}
    """
    if not content:
        return
    data = _safe_load()
    data.setdefault("interactions", [])
    data["interactions"].append({
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "role": role,
        "content": content,
    })
    # Optional: cap size so file doesn't grow forever
    MAX_INTERACTIONS = 2000
    if len(data["interactions"]) > MAX_INTERACTIONS:
        data["interactions"] = data["interactions"][-MAX_INTERACTIONS:]
    _atomic_save(data)

# Ensure store exists the moment the module loads
_ensure_store()
