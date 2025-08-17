# navi/modules/speech/wake_word.py

import os
import time
import queue
import json
import re

import sounddevice as sd
import vosk
from fuzzywuzzy import fuzz

from navi.modules.speech.tts import play_file, speak
from navi.modules.speech.command_listener import listen_for_command
from navi.modules.ai.ai_brain import ask_openai
from navi.core.paths import model_path

# -----------------------
# Config / constants
# -----------------------

# Wake variants + common mishears (quick win for Vosk)
WAKE_PHRASES = [
    "hey navi", "hi navi", "okay navi",
    "hey naughty", "hi naughty", "okay naughty",
    "hey navy", "hi navy", "okay navy",
    "hey neighbor", "hi neighbor", "okay neighbor",
]
FUZZ_THRESHOLD = 75  # a bit looser than 80; adjust if false positives appear

MODEL_PATH = model_path("vosk-model-small-en-us-0.15")

# Session behavior (can override via env)
MAX_TURNS = int(os.getenv("NAVI_MAX_TURNS", "5"))
SILENT_PROMPT_ON_EMPTY = os.getenv("NAVI_EMPTY_PROMPT", "I didn't catch that. Please repeat the command.")

# Optional input device override (NAVI_MIC_DEVICE=13)
DEV_ENV = os.getenv("NAVI_MIC_DEVICE")
DEVICE_INDEX = int(DEV_ENV) if DEV_ENV and DEV_ENV.isdigit() else None

# Shared audio queue
q = queue.Queue()

# Global mic mute flag so we don't re-transcribe Navi's own voice
MIC_MUTED = False

# Common "end session" phrases
STOP_RE = re.compile(
    r"\b(stop|cancel|nevermind|that's all|thanks navi|thank you navi|goodbye)\b",
    re.IGNORECASE
)

# -----------------------
# Audio callback
# -----------------------

def _callback(indata, frames, time_info, status):
    if status:
        print("[!] Audio status:", status)
    # Drop frames while we're speaking/playing audio
    if MIC_MUTED:
        return
    q.put(bytes(indata))

# -----------------------
# Wake logic helpers
# -----------------------

def is_wake_word(text: str) -> bool:
    t = (text or "").lower().strip()
    if not t:
        return False # Function returns False because there is no text
    if any(re.search(rf"\b{re.escape(p)}\b", t) for p in WAKE_PHRASES):
        return True # Return True, we matched text to a wake word
    for phrase in WAKE_PHRASES:
        if fuzz.ratio(phrase, t) >= FUZZ_THRESHOLD:
            print(f"[MATCH] '{t}' ≈ '{phrase}'")
            return True
    return False

def _safe_play_sir():
    """
    Play the 'Sir?' prompt without allowing playback to get re-captured by Vosk.
    """
    global MIC_MUTED
    try:
        MIC_MUTED = True
        # Relative to assets; play_file resolves: assets/voice_db/Joanna/sir.mp3
        play_file("voice_db/Joanna/sir.mp3")
    except Exception as e:
        print(f"[Audio] play_file error: {e}")
    finally:
        # small settle time avoids capturing the tail end as we unmute
        time.sleep(0.15)
        MIC_MUTED = False

def _safe_speak(text: str):
    """
    Speak TTS safely. Mic is muted during TTS so we don't re-transcribe our own voice.
    If Polly fails inside speak(), errors are printed but we don't crash.
    """
    global MIC_MUTED
    try:
        MIC_MUTED = True
        speak(text)
    except Exception as e:
        print(f"[TTS] speak error: {e}\n[NÄVÎ] {text}")
    finally:
        time.sleep(0.15)
        MIC_MUTED = False

# -----------------------
# Main listen loop
# -----------------------

def listen_for_wake_word():
    """
    Continuously listens for the wake word using Vosk.
    On detection, plays the prompt and runs a short multi-turn session,
    then returns to wake listening. Mic is muted during TTS so Navi
    doesn't hear herself.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Vosk model not found at {MODEL_PATH}")

    # Init model & recognizer (wake mode)
    model = vosk.Model(str(MODEL_PATH))
    recognizer = vosk.KaldiRecognizer(model, 16000)

    print(f"[Audio] Using device index: {DEVICE_INDEX}")

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=16000,   # ~1s chunks help short phrases
        dtype='int16',
        channels=1,
        callback=_callback,
        device=DEVICE_INDEX
    ):
        print("[NÄVÎ] Listening for wake word...")

        while True:
            data = q.get()
            if not recognizer.AcceptWaveform(data):
                continue

            # Parse recognizer output safely
            try:
                result = json.loads(recognizer.Result())
            except Exception as e:
                print(f"[VOSK] JSON parse error: {e}")
                result = {}

            text = (result.get("text") or "").lower().strip()
            if text:
                print(f"[DEBUG] Heard: {text}")

            # ---- Wake detection ----
            if is_wake_word(text):
                print("🔊 Wake word detected!")
                _safe_play_sir()

                # --- Multi-turn session ---
                turns = 0
                while turns < MAX_TURNS:
                    # Capture one command. If your implementation supports timeouts/silence,
                    # you can pass them here, e.g., listen_for_command(timeout=8, silence_timeout=1.5)
                    user_command = listen_for_command()
                    print(f"[NÄVÎ] Interpreted command: {user_command or '[empty]'}")

                    if not user_command:
                        # No usable speech — optionally prompt once and end session
                        if SILENT_PROMPT_ON_EMPTY:
                            _safe_speak(SILENT_PROMPT_ON_EMPTY)
                        break

                    if STOP_RE.search(user_command):
                        _safe_speak("Okay.")
                        break

                    # Ask AI and speak reply (mic muted during TTS)
                    reply = ask_openai(user_command, uid="josh")
                    _safe_speak(reply)

                    turns += 1

                print("[NÄVÎ] Session ended. Returning to wake listening…")
                # do NOT return; stay in outer loop
