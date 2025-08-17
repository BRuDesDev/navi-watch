# navi/modules/speech/command_memory_hooks.py
import re
from navi.core.memory import remember_person, remember_fact

NAME_RE = re.compile(r"\bmy name is\s+([a-z][a-z\s'-]{1,40})\b", re.I)
REMEMBER_RE = re.compile(r"\bremember (that\s+)?(.+)", re.I)

def handle_memory_phrases(text: str, uid: str = "default_user") -> str | None:
    if not text:
        return None

    m = NAME_RE.search(text)
    if m:
        name = m.group(1).strip().title()
        remember_person(uid, name=name)
        return f"Nice to meet you, {name}. I?ll remember that."

    m = REMEMBER_RE.search(text)
    if m:
        fact = m.group(2).strip().rstrip(".")
        remember_fact(uid, fact)
        return "Got it. I?ll remember that."

    return None
