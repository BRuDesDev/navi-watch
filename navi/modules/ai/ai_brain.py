# navi/modules/ai/ai_brain.py

import os

from dotenv import load_dotenv

load_dotenv()

# OpenAI SDK v1+ style (if you installed openai>=1.0)
USE_NEW_SDK = False
try:
    import openai  # v0.x
    _legacy = True
except Exception:
    _legacy = False

try:
    from openai import OpenAI  # v1.x
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    USE_NEW_SDK = True
except Exception:
    pass

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # pick what you have access to

def ask_openai(prompt: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        print("[AI] Missing OPENAI_API_KEY; returning fallback.")
        return "My brain link is down, sir. I can't reach the network."

    if not prompt or not prompt.strip():
        return "I didn't hear a command. Please repeat that."

    try:
        if USE_NEW_SDK:
            resp = _client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are NÄVÎ, a concise, helpful voice assistant."},
                    {"role": "user", "content": prompt.strip()},
                ],
                max_tokens=180,
            )
            return (resp.choices[0].message.content or "").strip() or \
                   "I'm having trouble forming a response right now."
        else:
            # legacy path for openai<1.0
            openai.api_key = os.getenv("OPENAI_API_KEY")
            resp = openai.ChatCompletion.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are NÄVÎ, a concise, helpful voice assistant."},
                    {"role": "user", "content": prompt.strip()},
                ],
                max_tokens=180,
            )
            return (resp.choices[0].message.content or "").strip() or \
                   "I'm having trouble forming a response right now."
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return "My brain link is acting up. Please try again in a moment."
