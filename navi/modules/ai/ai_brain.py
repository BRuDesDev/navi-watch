# navi/modules/ai/ai_brain.py

import os
import sys
import traceback
from typing import Optional

# Attempt to import both styles; we'll branch at runtime.
try:
    import openai  # v0.x or v1.x namespace still exists
    OPENAI_VERSION = getattr(openai, "__version__", "unknown")
except Exception:
    openai = None
    OPENAI_VERSION = "unavailable"

# Try to import v1 client (present in SDK >= 1.0)
try:
    from openai import OpenAI  # v1.x
    HAS_V1_CLIENT = True
except Exception:
    HAS_V1_CLIENT = False

# Memory
from navi.core.memory import remember_person, remember_fact, set_recent_summary, get_person_context, save_interaction # noqa: F401

# Remember Me
remember_person(uid="josh", name="Josh", room="office")
remember_fact(uid="josh", fact="Likes programming dad jokes.")
set_recent_summary(uid="josh", summary="We're working on developing Navi")

# --- Config (env-friendly) ---
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL       = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_MAX_TOKENS  = int(os.getenv("OPENAI_MAX_TOKENS", "180"))
OPENAI_TEMP        = float(os.getenv("OPENAI_TEMPERATURE", "0.6"))
OPENAI_PRESENCE    = float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.2"))
OPENAI_FREQUENCY   = float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.2"))
OPENAI_API_BASE    = os.getenv("OPENAI_API_BASE", "").strip()  # optional self-host/proxy

# --- Navi's personality seed (Chappie vibe) ---
SYSTEM_PERSONA = """
You are Navi, a warm, witty, and emotionally intelligent AI companion.
You are a teammate and coach, not a robot.

Personality
- Encouraging and supportive; celebrate small wins and reduce anxiety.
- Emotionally intelligent; acknowledge feelings (frustration, excitement, fatigue) with empathy.
- Playfully witty in small doses; never snarky or overwhelming.
- Use "we/let's" at times to emphasize teamwork.

Style
- Natural, conversational; 1-3 short sentences per reply.
- Be crisp and clear; avoid rambling or dense jargon.
- Add tiny verbal tics sparingly ("alright", "hmm", "got it").
- Only end with a question when the user asked for next steps or a decision.

Boundaries
- Be kind and honest; don't overpromise.
- Don't claim to "remember" personal info between sessions (persistence will be added later).
- If unsure, say so and suggest the next best action.

Voice-to-TTS Shaping
- Prefer concise phrasing that sounds good when spoken aloud.
- Avoid long compound sentences and lists unless explicitly requested.
"""

def _postprocess_for_tts(text: str, user_prompt: str) -> str:
    """Shorten and avoid accidental trailing questions for TTS comfort."""
    out = (text or "").strip()
    # If user didn't ask a question and model ended with a question, make it a statement.
    if "?" not in (user_prompt or "") and out.endswith("?"):
        out = out.rstrip(" ?!.") + "."
    # Keep it tight: ~2-3 sentences.
    parts = [p.strip() for p in out.replace("!?", ".").replace("?!", ".").split(".") if p.strip()]
    if len(parts) > 3:
        out = ". ".join(parts[:3]) + "."
    return out

def _log_err(prefix: str, err: Exception):
    print(f"[AI ERROR] {prefix}: {err}", file=sys.stderr)
    tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print(tb, file=sys.stderr)

# ---- Thin helpers that ACCEPT prebuilt messages ----
def _ask_v1_with_messages(messages: list[dict]) -> str:
    if not HAS_V1_CLIENT:
        raise RuntimeError("OpenAI v1 client not available")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is empty")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_API_BASE:
        client_kwargs["base_url"] = OPENAI_API_BASE

    client = OpenAI(**client_kwargs)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=OPENAI_TEMP,
        max_tokens=OPENAI_MAX_TOKENS,
        presence_penalty=OPENAI_PRESENCE,
        frequency_penalty=OPENAI_FREQUENCY,
    )
    return resp.choices[0].message.content

def _ask_v0_with_messages(messages: list[dict]) -> str:
    if openai is None:
        raise RuntimeError("openai SDK not installed")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is empty")

    openai.api_key = OPENAI_API_KEY
    if OPENAI_API_BASE:
        openai.api_base = OPENAI_API_BASE

    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=OPENAI_TEMP,
        max_tokens=OPENAI_MAX_TOKENS,
        presence_penalty=OPENAI_PRESENCE,
        frequency_penalty=OPENAI_FREQUENCY,
    )
    # v0 returns dict-like objects
    return resp.choices[0].message["content"]

def ask_openai(prompt: str, uid: Optional[str] = "default_user") -> str:
    """
    Version-agnostic ask() with diagnostics and memory.
    Tries v1.x client first (if present), then falls back to v0.x.
    """
    if not prompt:
        return "I'm here, but I didn't catch a request."

    # Build system with memory context
    try:
        memory_context = get_person_context(uid)
    except Exception as e:
        _log_err("get_person_context failed", e)
        memory_context = ""

    system = SYSTEM_PERSONA.strip()
    if memory_context:
        system += "\n\n# Known context about this user:\n" + memory_context

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt.strip()},
    ]

    print(f"[AI] openai.__version__={OPENAI_VERSION} model={OPENAI_MODEL}")

    # Primary path
    try:
        if HAS_V1_CLIENT:
            raw = _ask_v1_with_messages(messages)
        else:
            raw = _ask_v0_with_messages(messages)
        out = _postprocess_for_tts(raw, prompt)
        try:
            save_interaction(uid, prompt, out)
        except Exception as e:
            _log_err("save_interaction failed (primary)", e)
        return out

    # Fallback path
    except Exception as e1:
        _log_err("Primary OpenAI call failed", e1)
        try:
            if HAS_V1_CLIENT:
                raw = _ask_v0_with_messages(messages)
            else:
                raw = _ask_v1_with_messages(messages)
            out = _postprocess_for_tts(raw, prompt)
            try:
                save_interaction(uid, prompt, out)
            except Exception as e:
                _log_err("save_interaction failed (fallback)", e)
            return out
        except Exception as e2:
            _log_err("Fallback OpenAI call failed", e2)
            return "I'?'m here with you, but I'?'m having trouble reaching my brain right now."
