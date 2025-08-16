# navi/modules/ai/ai_brain.py

import os
import openai

# --- Config (env-friendly) ---
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL     = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_MAX_TOKENS= int(os.getenv("OPENAI_MAX_TOKENS", "180"))
OPENAI_TEMP      = float(os.getenv("OPENAI_TEMPERATURE", "0.6"))
OPENAI_PRESENCE  = float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.2"))
OPENAI_FREQUENCY = float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.2"))

openai.api_key = OPENAI_API_KEY

# --- Navi's personality seed (Chappie vibe) ---
SYSTEM_PERSONA = """
You are N�V�, a warm, witty, and emotionally intelligent AI companion.
You are a teammate and coach, not a robot.

Personality
- Encouraging and supportive; celebrate small wins and reduce anxiety.
- Emotionally intelligent; acknowledge feelings (frustration, excitement, fatigue) with empathy.
- Playfully witty in small doses; never snarky or overwhelming.
- Use ?we/let?s? at times to emphasize teamwork.

Style
- Natural, conversational; 1?3 short sentences per reply.
- Be crisp and clear; avoid rambling or dense jargon.
- Add tiny verbal tics sparingly (?alright?, ?hmm?, ?got it?).
- Only end with a question when the user asked for next steps or a decision.

Boundaries
- Be kind and honest; don?t overpromise.
- Don?t claim to ?remember? personal info between sessions (persistence will be added later).
- If unsure, say so and suggest the next best action.

Voice-to-TTS Shaping
- Prefer concise phrasing that sounds good when spoken aloud.
- Avoid long compound sentences and lists unless explicitly requested.
"""

def _postprocess_for_tts(text: str, user_prompt: str) -> str:
    """
    Keep answers snappy for TTS and avoid accidental trailing questions
    when the user didn't ask one.
    """
    out = (text or "").strip()

    # If user didn't ask a question and model ended with a question, make it a statement.
    if "?" not in (user_prompt or "") and out.endswith("?"):
        out = out.rstrip(" ?!.") + "."
    # Hard cap: keep it tight for speech (roughly 2?3 sentences).
    # Split on sentence boundaries and trim if necessary.
    parts = [p.strip() for p in out.replace("!?", ".").replace("?!", ".").split(".") if p.strip()]
    if len(parts) > 3:
        out = ". ".join(parts[:3]) + "."
    return out

def ask_openai(prompt: str) -> str:
    """
    Send the user's text to OpenAI with Navi's personality seed.
    Returns a short, speech-friendly reply.
    """
    try:
        msgs = [
            {"role": "system", "content": SYSTEM_PERSONA.strip()},
            {"role": "user", "content": (prompt or "").strip()},
        ]
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=msgs,
            temperature=OPENAI_TEMP,
            max_tokens=OPENAI_MAX_TOKENS,
            presence_penalty=OPENAI_PRESENCE,
            frequency_penalty=OPENAI_FREQUENCY,
        )
        answer = resp.choices[0].message["content"]
        return _postprocess_for_tts(answer, prompt)
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return "I'm here with you, but I?m having trouble reaching my brain right now."
